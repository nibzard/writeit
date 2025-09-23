"""File System Storage for WriteIt Infrastructure.

Provides file system operations for templates, workspaces, and content
with atomic operations, backup support, and change detection.
"""

import asyncio
import shutil
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
import logging
from contextlib import asynccontextmanager
from tempfile import NamedTemporaryFile
import hashlib
from concurrent.futures import ThreadPoolExecutor
import os

from ..base.exceptions import StorageError, ValidationError, ConfigurationError

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Metadata for tracked files."""
    
    path: Path
    size: int
    modified_time: datetime
    content_hash: str
    is_directory: bool = False
    
    @classmethod
    def from_path(cls, path: Path) -> 'FileMetadata':
        """Create metadata from file path.
        
        Args:
            path: File path to analyze
            
        Returns:
            FileMetadata instance
        """
        stat = path.stat()
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        
        if path.is_file():
            content_hash = cls._calculate_hash(path)
            return cls(
                path=path,
                size=stat.st_size,
                modified_time=modified_time,
                content_hash=content_hash,
                is_directory=False
            )
        else:
            return cls(
                path=path,
                size=0,
                modified_time=modified_time,
                content_hash="",
                is_directory=True
            )
    
    @staticmethod
    def _calculate_hash(path: Path) -> str:
        """Calculate SHA256 hash of file content.
        
        Args:
            path: File path
            
        Returns:
            Hex digest of file hash
        """
        hash_sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()


class FileChangeHandler(FileSystemEventHandler):
    """File system event handler for change detection."""
    
    def __init__(self, storage: 'FileSystemStorage'):
        """Initialize handler.
        
        Args:
            storage: File storage instance to notify
        """
        self.storage = storage
        super().__init__()
    
    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory:
            asyncio.create_task(self.storage._on_file_changed(Path(event.src_path), 'modified'))
    
    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory:
            asyncio.create_task(self.storage._on_file_changed(Path(event.src_path), 'created'))
    
    def on_deleted(self, event: FileDeletedEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory:
            asyncio.create_task(self.storage._on_file_changed(Path(event.src_path), 'deleted'))


class FileSystemStorage:
    """File system storage abstraction for WriteIt.
    
    Provides high-level file operations with atomic writes, backup support,
    change detection, and workspace isolation.
    """
    
    def __init__(
        self,
        base_path: Path,
        enable_watching: bool = True,
        backup_enabled: bool = True,
        max_backups: int = 5
    ):
        """Initialize file system storage.
        
        Args:
            base_path: Base directory for file operations
            enable_watching: Whether to enable file change detection
            backup_enabled: Whether to create backups on overwrites
            max_backups: Maximum number of backup files to keep
        """
        self.base_path = base_path
        self.enable_watching = enable_watching
        self.backup_enabled = backup_enabled
        self.max_backups = max_backups
        
        self._file_metadata: Dict[Path, FileMetadata] = {}
        self._change_callbacks: List[callable] = []
        self._observer: Optional[Observer] = None
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="file_storage")
        self._lock = asyncio.Lock()
        
        logger.info(f"Initialized file system storage at {base_path}")
    
    async def initialize(self) -> None:
        """Initialize storage and start file watching if enabled.
        
        Raises:
            StorageError: If initialization fails
        """
        try:
            # Ensure base directory exists
            self.base_path.mkdir(parents=True, exist_ok=True)
            
            # Scan existing files
            await self._scan_directory(self.base_path)
            
            # Start file watching
            if self.enable_watching:
                await self._start_watching()
            
            logger.info(f"File system storage initialized with {len(self._file_metadata)} files")
            
        except Exception as e:
            raise StorageError(
                f"Failed to initialize file system storage: {e}",
                operation="initialize",
                cause=e
            )
    
    async def _scan_directory(self, directory: Path) -> None:
        """Recursively scan directory for files.
        
        Args:
            directory: Directory to scan
        """
        try:
            for item in directory.rglob('*'):
                if item.is_file():
                    metadata = await asyncio.get_event_loop().run_in_executor(
                        self._executor, FileMetadata.from_path, item
                    )
                    self._file_metadata[item] = metadata
                    
        except Exception as e:
            logger.warning(f"Failed to scan directory {directory}: {e}")
    
    async def _start_watching(self) -> None:
        """Start file system watching."""
        try:
            self._observer = Observer()
            handler = FileChangeHandler(self)
            self._observer.schedule(handler, str(self.base_path), recursive=True)
            self._observer.start()
            logger.info(f"Started file watching on {self.base_path}")
            
        except Exception as e:
            logger.warning(f"Failed to start file watching: {e}")
            self._observer = None
    
    async def _on_file_changed(self, path: Path, event_type: str) -> None:
        """Handle file change events.
        
        Args:
            path: Path of changed file
            event_type: Type of change (created, modified, deleted)
        """
        async with self._lock:
            if event_type == 'deleted':
                self._file_metadata.pop(path, None)
            else:
                try:
                    metadata = await asyncio.get_event_loop().run_in_executor(
                        self._executor, FileMetadata.from_path, path
                    )
                    self._file_metadata[path] = metadata
                except Exception as e:
                    logger.warning(f"Failed to update metadata for {path}: {e}")
            
            # Notify callbacks
            for callback in self._change_callbacks:
                try:
                    await callback(path, event_type)
                except Exception as e:
                    logger.error(f"File change callback failed: {e}")
    
    def add_change_callback(self, callback: callable) -> None:
        """Add a callback for file change notifications.
        
        Args:
            callback: Async function to call on file changes
        """
        self._change_callbacks.append(callback)
    
    async def write_file(
        self,
        file_path: Path,
        content: str,
        create_backup: Optional[bool] = None,
        encoding: str = 'utf-8'
    ) -> None:
        """Write content to file atomically.
        
        Args:
            file_path: Target file path
            content: Content to write
            create_backup: Whether to create backup (uses instance default if None)
            encoding: Text encoding
            
        Raises:
            StorageError: If write operation fails
        """
        absolute_path = self._resolve_path(file_path)
        
        try:
            # Create parent directories
            absolute_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if file exists and backup is enabled
            if create_backup is None:
                create_backup = self.backup_enabled
                
            if create_backup and absolute_path.exists():
                await self._create_backup(absolute_path)
            
            # Atomic write using temporary file
            temp_file = None
            try:
                with NamedTemporaryFile(
                    mode='w',
                    encoding=encoding,
                    dir=absolute_path.parent,
                    delete=False
                ) as f:
                    f.write(content)
                    temp_file = Path(f.name)
                
                # Atomic move
                await asyncio.get_event_loop().run_in_executor(
                    self._executor, 
                    lambda: shutil.move(str(temp_file), str(absolute_path))
                )
                
                logger.debug(f"Wrote file: {absolute_path}")
                
            except Exception as e:
                # Clean up temp file on error
                if temp_file and temp_file.exists():
                    temp_file.unlink()
                raise
                
        except Exception as e:
            raise StorageError(
                f"Failed to write file {file_path}: {e}",
                operation="write",
                cause=e
            )
    
    async def read_file(
        self,
        file_path: Path,
        encoding: str = 'utf-8'
    ) -> str:
        """Read content from file.
        
        Args:
            file_path: File path to read
            encoding: Text encoding
            
        Returns:
            File content as string
            
        Raises:
            StorageError: If read operation fails
        """
        absolute_path = self._resolve_path(file_path)
        
        try:
            content = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: absolute_path.read_text(encoding=encoding)
            )
            
            logger.debug(f"Read file: {absolute_path}")
            return content
            
        except FileNotFoundError:
            raise StorageError(
                f"File not found: {file_path}",
                operation="read"
            )
        except Exception as e:
            raise StorageError(
                f"Failed to read file {file_path}: {e}",
                operation="read",
                cause=e
            )
    
    async def delete_file(self, file_path: Path) -> bool:
        """Delete a file.
        
        Args:
            file_path: File path to delete
            
        Returns:
            True if file was deleted, False if it didn't exist
            
        Raises:
            StorageError: If delete operation fails
        """
        absolute_path = self._resolve_path(file_path)
        
        try:
            if not absolute_path.exists():
                return False
            
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                absolute_path.unlink
            )
            
            logger.debug(f"Deleted file: {absolute_path}")
            return True
            
        except Exception as e:
            raise StorageError(
                f"Failed to delete file {file_path}: {e}",
                operation="delete",
                cause=e
            )
    
    async def file_exists(self, file_path: Path) -> bool:
        """Check if file exists.
        
        Args:
            file_path: File path to check
            
        Returns:
            True if file exists, False otherwise
        """
        absolute_path = self._resolve_path(file_path)
        return await asyncio.get_event_loop().run_in_executor(
            self._executor,
            absolute_path.exists
        )
    
    async def list_files(
        self,
        directory_path: Path = Path("."),
        pattern: str = "*",
        recursive: bool = False
    ) -> List[Path]:
        """List files in directory.
        
        Args:
            directory_path: Directory to search in
            pattern: Glob pattern to match
            recursive: Whether to search recursively
            
        Returns:
            List of matching file paths
        """
        absolute_dir = self._resolve_path(directory_path)
        
        try:
            if recursive:
                matches = list(absolute_dir.rglob(pattern))
            else:
                matches = list(absolute_dir.glob(pattern))
            
            # Filter to files only and make relative to base path
            files = [
                path.relative_to(self.base_path)
                for path in matches
                if path.is_file()
            ]
            
            return files
            
        except Exception as e:
            raise StorageError(
                f"Failed to list files in {directory_path}: {e}",
                operation="list",
                cause=e
            )
    
    async def create_directory(self, directory_path: Path) -> None:
        """Create directory and all parent directories.
        
        Args:
            directory_path: Directory path to create
            
        Raises:
            StorageError: If directory creation fails
        """
        absolute_path = self._resolve_path(directory_path)
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: absolute_path.mkdir(parents=True, exist_ok=True)
            )
            
            logger.debug(f"Created directory: {absolute_path}")
            
        except Exception as e:
            raise StorageError(
                f"Failed to create directory {directory_path}: {e}",
                operation="create_directory",
                cause=e
            )
    
    async def copy_file(
        self,
        source_path: Path,
        destination_path: Path,
        create_backup: bool = False
    ) -> None:
        """Copy file from source to destination.
        
        Args:
            source_path: Source file path
            destination_path: Destination file path
            create_backup: Whether to backup destination if it exists
            
        Raises:
            StorageError: If copy operation fails
        """
        abs_source = self._resolve_path(source_path)
        abs_dest = self._resolve_path(destination_path)
        
        try:
            # Create destination parent directory
            abs_dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if requested and destination exists
            if create_backup and abs_dest.exists():
                await self._create_backup(abs_dest)
            
            # Copy file
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: shutil.copy2(str(abs_source), str(abs_dest))
            )
            
            logger.debug(f"Copied file: {abs_source} -> {abs_dest}")
            
        except Exception as e:
            raise StorageError(
                f"Failed to copy file {source_path} to {destination_path}: {e}",
                operation="copy",
                cause=e
            )
    
    async def write_yaml(self, file_path: Path, data: Dict[str, Any]) -> None:
        """Write data to YAML file.
        
        Args:
            file_path: Target file path
            data: Data to serialize to YAML
            
        Raises:
            StorageError: If write operation fails
        """
        try:
            yaml_content = yaml.dump(
                data,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )
            await self.write_file(file_path, yaml_content)
            
        except Exception as e:
            raise StorageError(
                f"Failed to write YAML file {file_path}: {e}",
                operation="write_yaml",
                cause=e
            )
    
    async def read_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Read data from YAML file.
        
        Args:
            file_path: File path to read
            
        Returns:
            Parsed YAML data
            
        Raises:
            StorageError: If read operation fails
        """
        try:
            content = await self.read_file(file_path)
            data = yaml.safe_load(content)
            return data or {}  # Handle empty files
            
        except yaml.YAMLError as e:
            raise ValidationError(
                f"Invalid YAML in file {file_path}: {e}",
                field="yaml_content",
                cause=e
            )
        except Exception as e:
            raise StorageError(
                f"Failed to read YAML file {file_path}: {e}",
                operation="read_yaml",
                cause=e
            )
    
    async def write_json(self, file_path: Path, data: Any, indent: int = 2) -> None:
        """Write data to JSON file.
        
        Args:
            file_path: Target file path
            data: Data to serialize to JSON
            indent: Indentation for pretty printing
            
        Raises:
            StorageError: If write operation fails
        """
        try:
            json_content = json.dumps(data, indent=indent, ensure_ascii=False)
            await self.write_file(file_path, json_content)
            
        except Exception as e:
            raise StorageError(
                f"Failed to write JSON file {file_path}: {e}",
                operation="write_json",
                cause=e
            )
    
    async def read_json(self, file_path: Path) -> Any:
        """Read data from JSON file.
        
        Args:
            file_path: File path to read
            
        Returns:
            Parsed JSON data
            
        Raises:
            StorageError: If read operation fails
        """
        try:
            content = await self.read_file(file_path)
            return json.loads(content)
            
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON in file {file_path}: {e}",
                field="json_content",
                cause=e
            )
        except Exception as e:
            raise StorageError(
                f"Failed to read JSON file {file_path}: {e}",
                operation="read_json",
                cause=e
            )
    
    async def _create_backup(self, file_path: Path) -> None:
        """Create backup of existing file.
        
        Args:
            file_path: File to backup
        """
        if not file_path.exists():
            return
        
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.with_suffix(f".{timestamp}.backup{file_path.suffix}")
            
            # Copy to backup
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: shutil.copy2(str(file_path), str(backup_path))
            )
            
            # Clean up old backups
            await self._cleanup_backups(file_path)
            
            logger.debug(f"Created backup: {backup_path}")
            
        except Exception as e:
            logger.warning(f"Failed to create backup for {file_path}: {e}")
    
    async def _cleanup_backups(self, original_path: Path) -> None:
        """Clean up old backup files.
        
        Args:
            original_path: Original file path
        """
        try:
            # Find all backup files for this file
            backup_pattern = f"{original_path.stem}.*.backup{original_path.suffix}"
            backup_files = list(original_path.parent.glob(backup_pattern))
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            
            # Remove excess backups
            for backup_file in backup_files[self.max_backups:]:
                await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    backup_file.unlink
                )
                logger.debug(f"Removed old backup: {backup_file}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup backups for {original_path}: {e}")
    
    def _resolve_path(self, path: Path) -> Path:
        """Resolve path relative to base path.
        
        Args:
            path: Path to resolve
            
        Returns:
            Absolute path
        """
        if path.is_absolute():
            # Ensure path is within base path for security
            try:
                path.relative_to(self.base_path)
                return path
            except ValueError:
                raise StorageError(
                    f"Path {path} is outside base directory {self.base_path}",
                    operation="resolve_path"
                )
        else:
            return self.base_path / path
    
    def get_file_metadata(self, file_path: Path) -> Optional[FileMetadata]:
        """Get metadata for a file.
        
        Args:
            file_path: File path
            
        Returns:
            File metadata or None if not tracked
        """
        absolute_path = self._resolve_path(file_path)
        return self._file_metadata.get(absolute_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        total_size = sum(metadata.size for metadata in self._file_metadata.values())
        
        return {
            'base_path': str(self.base_path),
            'tracked_files': len(self._file_metadata),
            'total_size_bytes': total_size,
            'watching_enabled': self.enable_watching and self._observer is not None,
            'backup_enabled': self.backup_enabled,
            'max_backups': self.max_backups,
            'change_callbacks': len(self._change_callbacks),
        }
    
    async def close(self) -> None:
        """Close storage and clean up resources."""
        logger.info("Closing file system storage")
        
        # Stop file watching
        if self._observer:
            self._observer.stop()
            self._observer.join(timeout=5)
            self._observer = None
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        # Clear callbacks and metadata
        self._change_callbacks.clear()
        self._file_metadata.clear()
    
    def __str__(self) -> str:
        """String representation."""
        return f"FileSystemStorage(path={self.base_path}, files={len(self._file_metadata)})"
