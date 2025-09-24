"""Storage management service for WriteIt.

Provides centralized storage operations across all domains, including
file system operations, LMDB management, and workspace-aware storage.
"""

import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
from enum import Enum
import logging
from datetime import datetime
import asyncio

from ...workspace.value_objects import WorkspaceName
from ...content.value_objects import TemplateName, StyleName
from ...pipeline.value_objects import PipelineId, StepId


class StorageOperation(str, Enum):
    """Types of storage operations."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    LIST = "list"
    CREATE_DIR = "create_dir"
    REMOVE_DIR = "remove_dir"


class StorageError(Exception):
    """Base class for storage errors."""
    pass


class StoragePermissionError(StorageError):
    """Error when storage permissions are insufficient."""
    pass


class StorageSpaceError(StorageError):
    """Error when storage space is insufficient."""
    pass


class StorageConcurrencyError(StorageError):
    """Error when concurrent access conflicts occur."""
    pass


@dataclass
class StorageOperationResult:
    """Result of a storage operation."""
    success: bool
    operation: StorageOperation
    path: Path
    message: str
    bytes_processed: int = 0
    items_processed: int = 0
    execution_time: float = 0.0
    error_details: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class StorageInfo:
    """Information about storage usage."""
    total_space: int
    used_space: int
    free_space: int
    file_count: int
    directory_count: int
    last_modified: datetime
    can_read: bool
    can_write: bool
    can_execute: bool


class StorageManagerInterface(ABC):
    """Abstract interface for storage management."""
    
    @abstractmethod
    async def read_file(self, file_path: Path, encoding: str = "utf-8") -> str:
        """Read file contents."""
        pass
    
    @abstractmethod
    async def write_file(self, file_path: Path, content: str, encoding: str = "utf-8") -> StorageOperationResult:
        """Write content to file."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: Path) -> StorageOperationResult:
        """Delete a file."""
        pass
    
    @abstractmethod
    async def copy_file(self, source_path: Path, target_path: Path) -> StorageOperationResult:
        """Copy a file."""
        pass
    
    @abstractmethod
    async def move_file(self, source_path: Path, target_path: Path) -> StorageOperationResult:
        """Move a file."""
        pass
    
    @abstractmethod
    async def list_directory(self, directory_path: Path, recursive: bool = False) -> List[Path]:
        """List directory contents."""
        pass
    
    @abstractmethod
    async def create_directory(self, directory_path: Path, parents: bool = True) -> StorageOperationResult:
        """Create a directory."""
        pass
    
    @abstractmethod
    async def remove_directory(self, directory_path: Path, recursive: bool = False) -> StorageOperationResult:
        """Remove a directory."""
        pass
    
    @abstractmethod
    async def get_storage_info(self, path: Path) -> StorageInfo:
        """Get storage information for a path."""
        pass
    
    @abstractmethod
    async def check_permissions(self, path: Path) -> Dict[str, bool]:
        """Check permissions for a path."""
        pass


class StorageManagementService(StorageManagerInterface):
    """Implementation of storage management service."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.home()
        self.logger = logging.getLogger(__name__)
        self._lock = asyncio.Lock()
    
    async def read_file(self, file_path: Path, encoding: str = "utf-8") -> str:
        """Read file contents."""
        try:
            # Check if file exists and is readable
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not os.access(file_path, os.R_OK):
                raise StoragePermissionError(f"No read permission for: {file_path}")
            
            # Read file
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            self.logger.debug(f"Read file: {file_path} ({len(content)} bytes)")
            return content
            
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    async def write_file(self, file_path: Path, content: str, encoding: str = "utf-8") -> StorageOperationResult:
        """Write content to file."""
        start_time = datetime.now()
        
        async with self._lock:
            try:
                # Ensure parent directory exists
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Check if we can write to the location
                if file_path.exists() and not os.access(file_path, os.W_OK):
                    raise StoragePermissionError(f"No write permission for: {file_path}")
                
                if not os.access(file_path.parent, os.W_OK):
                    raise StoragePermissionError(f"No write permission for directory: {file_path.parent}")
                
                # Check disk space
                content_size = len(content.encode(encoding))
                if not await self._check_disk_space(file_path.parent, content_size):
                    raise StorageSpaceError(f"Insufficient disk space for: {file_path}")
                
                # Write file to temporary location first
                temp_path = file_path.with_suffix(f'.tmp_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
                with open(temp_path, 'w', encoding=encoding) as f:
                    f.write(content)
                
                # Atomic move to final location
                shutil.move(str(temp_path), str(file_path))
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=True,
                    operation=StorageOperation.WRITE,
                    path=file_path,
                    message="File written successfully",
                    bytes_processed=content_size,
                    items_processed=1,
                    execution_time=execution_time,
                    metadata={"encoding": encoding}
                )
                
                self.logger.debug(f"Wrote file: {file_path} ({content_size} bytes)")
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=False,
                    operation=StorageOperation.WRITE,
                    path=file_path,
                    message=f"Failed to write file: {str(e)}",
                    execution_time=execution_time,
                    error_details=str(e)
                )
                
                self.logger.error(f"Error writing file {file_path}: {e}")
                return result
    
    async def delete_file(self, file_path: Path) -> StorageOperationResult:
        """Delete a file."""
        start_time = datetime.now()
        
        async with self._lock:
            try:
                if not file_path.exists():
                    raise FileNotFoundError(f"File not found: {file_path}")
                
                if not os.access(file_path, os.W_OK):
                    raise StoragePermissionError(f"No write permission for: {file_path}")
                
                # Get file size before deletion
                file_size = file_path.stat().st_size
                
                # Delete file
                file_path.unlink()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=True,
                    operation=StorageOperation.DELETE,
                    path=file_path,
                    message="File deleted successfully",
                    bytes_processed=file_size,
                    items_processed=1,
                    execution_time=execution_time
                )
                
                self.logger.debug(f"Deleted file: {file_path}")
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=False,
                    operation=StorageOperation.DELETE,
                    path=file_path,
                    message=f"Failed to delete file: {str(e)}",
                    execution_time=execution_time,
                    error_details=str(e)
                )
                
                self.logger.error(f"Error deleting file {file_path}: {e}")
                return result
    
    async def copy_file(self, source_path: Path, target_path: Path) -> StorageOperationResult:
        """Copy a file."""
        start_time = datetime.now()
        
        async with self._lock:
            try:
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file not found: {source_path}")
                
                if not os.access(source_path, os.R_OK):
                    raise StoragePermissionError(f"No read permission for: {source_path}")
                
                # Ensure target directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not os.access(target_path.parent, os.W_OK):
                    raise StoragePermissionError(f"No write permission for: {target_path.parent}")
                
                # Check disk space
                file_size = source_path.stat().st_size
                if not await self._check_disk_space(target_path.parent, file_size):
                    raise StorageSpaceError(f"Insufficient disk space for: {target_path}")
                
                # Copy file
                shutil.copy2(str(source_path), str(target_path))
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=True,
                    operation=StorageOperation.COPY,
                    path=target_path,
                    message="File copied successfully",
                    bytes_processed=file_size,
                    items_processed=1,
                    execution_time=execution_time,
                    metadata={"source_path": str(source_path)}
                )
                
                self.logger.debug(f"Copied file: {source_path} -> {target_path}")
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=False,
                    operation=StorageOperation.COPY,
                    path=target_path,
                    message=f"Failed to copy file: {str(e)}",
                    execution_time=execution_time,
                    error_details=str(e),
                    metadata={"source_path": str(source_path)}
                )
                
                self.logger.error(f"Error copying file {source_path} -> {target_path}: {e}")
                return result
    
    async def move_file(self, source_path: Path, target_path: Path) -> StorageOperationResult:
        """Move a file."""
        start_time = datetime.now()
        
        async with self._lock:
            try:
                if not source_path.exists():
                    raise FileNotFoundError(f"Source file not found: {source_path}")
                
                if not os.access(source_path, os.W_OK):
                    raise StoragePermissionError(f"No write permission for: {source_path}")
                
                # Ensure target directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                if not os.access(target_path.parent, os.W_OK):
                    raise StoragePermissionError(f"No write permission for: {target_path.parent}")
                
                # Get file size
                file_size = source_path.stat().st_size
                
                # Move file
                shutil.move(str(source_path), str(target_path))
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=True,
                    operation=StorageOperation.MOVE,
                    path=target_path,
                    message="File moved successfully",
                    bytes_processed=file_size,
                    items_processed=1,
                    execution_time=execution_time,
                    metadata={"source_path": str(source_path)}
                )
                
                self.logger.debug(f"Moved file: {source_path} -> {target_path}")
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=False,
                    operation=StorageOperation.MOVE,
                    path=target_path,
                    message=f"Failed to move file: {str(e)}",
                    execution_time=execution_time,
                    error_details=str(e),
                    metadata={"source_path": str(source_path)}
                )
                
                self.logger.error(f"Error moving file {source_path} -> {target_path}: {e}")
                return result
    
    async def list_directory(self, directory_path: Path, recursive: bool = False) -> List[Path]:
        """List directory contents."""
        try:
            if not directory_path.exists():
                raise FileNotFoundError(f"Directory not found: {directory_path}")
            
            if not os.access(directory_path, os.R_OK):
                raise StoragePermissionError(f"No read permission for: {directory_path}")
            
            if recursive:
                files = list(directory_path.rglob("*"))
            else:
                files = list(directory_path.iterdir())
            
            self.logger.debug(f"Listed directory: {directory_path} ({len(files)} items)")
            return files
            
        except Exception as e:
            self.logger.error(f"Error listing directory {directory_path}: {e}")
            raise
    
    async def create_directory(self, directory_path: Path, parents: bool = True) -> StorageOperationResult:
        """Create a directory."""
        start_time = datetime.now()
        
        async with self._lock:
            try:
                # Check if we can create the directory
                if directory_path.exists():
                    result = StorageOperationResult(
                        success=True,
                        operation=StorageOperation.CREATE_DIR,
                        path=directory_path,
                        message="Directory already exists",
                        execution_time=(datetime.now() - start_time).total_seconds()
                    )
                    return result
                
                # Check parent permissions
                if parents and directory_path.parent.exists():
                    if not os.access(directory_path.parent, os.W_OK):
                        raise StoragePermissionError(f"No write permission for: {directory_path.parent}")
                
                # Create directory
                directory_path.mkdir(parents=parents, exist_ok=True)
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=True,
                    operation=StorageOperation.CREATE_DIR,
                    path=directory_path,
                    message="Directory created successfully",
                    items_processed=1,
                    execution_time=execution_time
                )
                
                self.logger.debug(f"Created directory: {directory_path}")
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=False,
                    operation=StorageOperation.CREATE_DIR,
                    path=directory_path,
                    message=f"Failed to create directory: {str(e)}",
                    execution_time=execution_time,
                    error_details=str(e)
                )
                
                self.logger.error(f"Error creating directory {directory_path}: {e}")
                return result
    
    async def remove_directory(self, directory_path: Path, recursive: bool = False) -> StorageOperationResult:
        """Remove a directory."""
        start_time = datetime.now()
        
        async with self._lock:
            try:
                if not directory_path.exists():
                    raise FileNotFoundError(f"Directory not found: {directory_path}")
                
                if not os.access(directory_path, os.W_OK):
                    raise StoragePermissionError(f"No write permission for: {directory_path}")
                
                # Count items before deletion
                if recursive:
                    items = list(directory_path.rglob("*"))
                    item_count = len(items)
                else:
                    item_count = len(list(directory_path.iterdir()))
                
                # Remove directory
                if recursive:
                    shutil.rmtree(str(directory_path))
                else:
                    directory_path.rmdir()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=True,
                    operation=StorageOperation.REMOVE_DIR,
                    path=directory_path,
                    message="Directory removed successfully",
                    items_processed=item_count,
                    execution_time=execution_time,
                    metadata={"recursive": recursive}
                )
                
                self.logger.debug(f"Removed directory: {directory_path} (recursive={recursive})")
                return result
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = StorageOperationResult(
                    success=False,
                    operation=StorageOperation.REMOVE_DIR,
                    path=directory_path,
                    message=f"Failed to remove directory: {str(e)}",
                    execution_time=execution_time,
                    error_details=str(e),
                    metadata={"recursive": recursive}
                )
                
                self.logger.error(f"Error removing directory {directory_path}: {e}")
                return result
    
    async def get_storage_info(self, path: Path) -> StorageInfo:
        """Get storage information for a path."""
        try:
            if not path.exists():
                raise FileNotFoundError(f"Path not found: {path}")
            
            stat = path.stat()
            
            # Count files and directories
            if path.is_dir():
                files = list(path.rglob("*"))
                file_count = len([f for f in files if f.is_file()])
                directory_count = len([d for d in files if d.is_dir()])
            else:
                file_count = 1
                directory_count = 0
            
            # Get disk usage
            total_space = shutil.disk_usage(path).total
            used_space = shutil.disk_usage(path).used
            free_space = shutil.disk_usage(path).free
            
            # Check permissions
            permissions = await self.check_permissions(path)
            
            return StorageInfo(
                total_space=total_space,
                used_space=used_space,
                free_space=free_space,
                file_count=file_count,
                directory_count=directory_count,
                last_modified=datetime.fromtimestamp(stat.st_mtime),
                can_read=permissions.get("read", False),
                can_write=permissions.get("write", False),
                can_execute=permissions.get("execute", False),
            )
            
        except Exception as e:
            self.logger.error(f"Error getting storage info for {path}: {e}")
            raise
    
    async def check_permissions(self, path: Path) -> Dict[str, bool]:
        """Check permissions for a path."""
        try:
            if not path.exists():
                return {"read": False, "write": False, "execute": False}
            
            return {
                "read": os.access(path, os.R_OK),
                "write": os.access(path, os.W_OK),
                "execute": os.access(path, os.X_OK),
            }
            
        except Exception as e:
            self.logger.error(f"Error checking permissions for {path}: {e}")
            return {"read": False, "write": False, "execute": False}
    
    async def _check_disk_space(self, path: Path, required_bytes: int) -> bool:
        """Check if there's enough disk space."""
        try:
            free_space = shutil.disk_usage(path).free
            return free_space >= required_bytes
            
        except Exception as e:
            self.logger.error(f"Error checking disk space for {path}: {e}")
            return False
    
    async def workspace_path(self, workspace_name: WorkspaceName) -> Path:
        """Get the path for a workspace."""
        return self.base_path / ".writeit" / "workspaces" / workspace_name.value
    
    async def ensure_workspace_directory(self, workspace_name: WorkspaceName) -> Path:
        """Ensure workspace directory exists."""
        workspace_path = await self.workspace_path(workspace_name)
        await self.create_directory(workspace_path)
        return workspace_path
    
    async def cleanup_temp_files(self, directory: Path, older_than_days: int = 7) -> int:
        """Clean up temporary files older than specified days."""
        try:
            if not directory.exists():
                return 0
            
            cutoff_time = datetime.now().timestamp() - (older_than_days * 24 * 60 * 60)
            cleaned_count = 0
            
            for file_path in directory.rglob("*"):
                if (file_path.is_file() and 
                    "tmp_" in file_path.name and 
                    file_path.stat().st_mtime < cutoff_time):
                    file_path.unlink()
                    cleaned_count += 1
            
            self.logger.info(f"Cleaned up {cleaned_count} temporary files from {directory}")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up temporary files from {directory}: {e}")
            return 0