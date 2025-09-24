"""Migration backup and rollback infrastructure.

Provides comprehensive backup and rollback capabilities for migration operations,
ensuring data safety and recovery options during migration processes.
"""

import shutil
import json
import yaml
import hashlib
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple, Set
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta
import logging
import asyncio
import zipfile
import tarfile

from ...domains.workspace.value_objects import WorkspaceName
from ...domains.content.value_objects import TemplateName, StyleName
from ...domains.pipeline.value_objects import PipelineId, StepId


class BackupType(str, Enum):
    """Types of backup operations."""
    FULL = "full"                    # Complete backup of all data
    INCREMENTAL = "incremental"      # Incremental backup since last full
    DIFFERENTIAL = "differential"    # Differential backup since last full
    SNAPSHOT = "snapshot"            # Point-in-time snapshot
    WORKSPACE = "workspace"          # Workspace-specific backup
    CONFIGURATION = "configuration"  # Configuration-only backup
    CACHE = "cache"                  # Cache data backup
    LEGACY = "legacy"                # Legacy format backup


class BackupStatus(str, Enum):
    """Backup operation status."""
    PENDING = "pending"          # Backup scheduled but not started
    IN_PROGRESS = "in_progress"  # Backup in progress
    COMPLETED = "completed"     # Backup completed successfully
    FAILED = "failed"          # Backup failed
    EXPIRED = "expired"        # Backup has expired
    DELETED = "deleted"        # Backup has been deleted


class CompressionType(str, Enum):
    """Compression types for backups."""
    NONE = "none"           # No compression
    ZIP = "zip"           # ZIP compression
    TAR_GZ = "tar.gz"     # Tar with gzip
    TAR_BZ2 = "tar.bz2"   # Tar with bzip2
    TAR_XZ = "tar.xz"     # Tar with xz


class RollbackStrategy(str, Enum):
    """Rollback strategies."""
    FULL_RESTORE = "full_restore"        # Full restore from backup
    PARTIAL_RESTORE = "partial_restore"  # Restore specific components
    FILE_LEVEL = "file_level"           # File-level rollback
    TRANSACTIONAL = "transactional"     # Transactional rollback


@dataclass
class BackupMetadata:
    """Metadata for backup operations."""
    backup_id: str
    backup_type: BackupType
    created_at: datetime
    source_path: Path
    backup_path: Path
    size_bytes: int
    file_count: int
    checksum: str
    compression: CompressionType
    migration_id: Optional[str] = None
    workspace_name: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    expiration_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "backup_id": self.backup_id,
            "backup_type": self.backup_type.value,
            "created_at": self.created_at.isoformat(),
            "source_path": str(self.source_path),
            "backup_path": str(self.backup_path),
            "size_bytes": self.size_bytes,
            "file_count": self.file_count,
            "checksum": self.checksum,
            "compression": self.compression.value,
            "migration_id": self.migration_id,
            "workspace_name": self.workspace_name,
            "description": self.description,
            "tags": self.tags,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BackupMetadata":
        """Create from dictionary."""
        return cls(
            backup_id=data["backup_id"],
            backup_type=BackupType(data["backup_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            source_path=Path(data["source_path"]),
            backup_path=Path(data["backup_path"]),
            size_bytes=data["size_bytes"],
            file_count=data["file_count"],
            checksum=data["checksum"],
            compression=CompressionType(data["compression"]),
            migration_id=data.get("migration_id"),
            workspace_name=data.get("workspace_name"),
            description=data.get("description"),
            tags=data.get("tags", []),
            expiration_date=datetime.fromisoformat(data["expiration_date"]) if data.get("expiration_date") else None,
        )


@dataclass
class BackupResult:
    """Result of backup operation."""
    success: bool
    backup_id: str
    metadata: BackupMetadata
    backup_path: Path
    execution_time: timedelta
    warnings: List[str] = field(default_factory=list)
    error_details: Optional[str] = None


@dataclass
class RollbackResult:
    """Result of rollback operation."""
    success: bool
    rollback_id: str
    backup_id: str
    restored_items: List[str]
    failed_items: List[str]
    execution_time: timedelta
    warnings: List[str] = field(default_factory=list)
    error_details: Optional[str] = None


@dataclass
class BackupConfig:
    """Configuration for backup operations."""
    backup_root_path: Path
    compression: CompressionType = CompressionType.TAR_GZ
    retention_days: int = 30
    max_backups: int = 10
    checksum_algorithm: str = "sha256"
    temp_dir: Optional[Path] = None
    exclude_patterns: List[str] = field(default_factory=list)
    include_patterns: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.temp_dir is None:
            self.temp_dir = Path(tempfile.gettempdir()) / "writeit_backups"


class BackupStrategy(ABC):
    """Abstract base class for backup strategies."""
    
    @abstractmethod
    def can_handle(self, backup_type: BackupType) -> bool:
        """Check if this strategy can handle the backup type."""
        pass
    
    @abstractmethod
    async def create_backup(
        self, 
        source_path: Path, 
        backup_path: Path, 
        config: BackupConfig,
        metadata: BackupMetadata
    ) -> BackupResult:
        """Create backup."""
        pass
    
    @abstractmethod
    async def restore_backup(
        self, 
        backup_path: Path, 
        target_path: Path, 
        config: BackupConfig,
        strategy: RollbackStrategy = RollbackStrategy.FULL_RESTORE
    ) -> RollbackResult:
        """Restore from backup."""
        pass
    
    @abstractmethod
    def validate_backup(self, backup_path: Path, metadata: BackupMetadata) -> bool:
        """Validate backup integrity."""
        pass


class FileSystemBackupStrategy(BackupStrategy):
    """File system backup strategy using standard file operations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def can_handle(self, backup_type: BackupType) -> bool:
        """Handle all backup types."""
        return True
    
    async def create_backup(
        self, 
        source_path: Path, 
        backup_path: Path, 
        config: BackupConfig,
        metadata: BackupMetadata
    ) -> BackupResult:
        """Create backup using file system operations."""
        start_time = datetime.now()
        
        try:
            # Create backup directory
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create temporary backup file
            temp_backup_path = config.temp_dir / f"temp_{metadata.backup_id}"
            
            # Perform backup based on compression type
            if config.compression == CompressionType.NONE:
                await self._copy_directory(source_path, temp_backup_path, config)
            elif config.compression == CompressionType.ZIP:
                await self._create_zip_backup(source_path, temp_backup_path, config)
            else:
                await self._create_tar_backup(source_path, temp_backup_path, config, metadata.compression)
            
            # Calculate checksum
            checksum = await self._calculate_checksum(temp_backup_path, config.checksum_algorithm)
            
            # Move to final location
            shutil.move(str(temp_backup_path), str(backup_path))
            
            # Get file info
            size_bytes = backup_path.stat().st_size if backup_path.exists() else 0
            
            execution_time = datetime.now() - start_time
            
            return BackupResult(
                success=True,
                backup_id=metadata.backup_id,
                metadata=metadata,
                backup_path=backup_path,
                execution_time=execution_time,
                warnings=[],
                error_details=None,
            )
            
        except Exception as e:
            execution_time = datetime.now() - start_time
            self.logger.error(f"Error creating backup: {e}")
            return BackupResult(
                success=False,
                backup_id=metadata.backup_id,
                metadata=metadata,
                backup_path=backup_path,
                execution_time=execution_time,
                error_details=str(e),
            )
    
    async def restore_backup(
        self, 
        backup_path: Path, 
        target_path: Path, 
        config: BackupConfig,
        strategy: RollbackStrategy = RollbackStrategy.FULL_RESTORE
    ) -> RollbackResult:
        """Restore from backup."""
        start_time = datetime.now()
        restored_items = []
        failed_items = []
        
        try:
            # Ensure target directory exists
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create temporary restore directory
            temp_restore_path = config.temp_dir / f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Extract backup based on compression type
            if backup_path.suffix == '.zip':
                await self._extract_zip_backup(backup_path, temp_restore_path)
            elif backup_path.suffix in ['.tar', '.tar.gz', '.tar.bz2', '.tar.xz']:
                await self._extract_tar_backup(backup_path, temp_restore_path)
            else:
                # Direct copy for uncompressed backups
                shutil.copytree(str(backup_path), str(temp_restore_path))
            
            # Restore based on strategy
            if strategy == RollbackStrategy.FULL_RESTORE:
                # Remove existing target if it exists
                if target_path.exists():
                    if target_path.is_dir():
                        shutil.rmtree(str(target_path))
                    else:
                        target_path.unlink()
                
                # Move restored files to target
                shutil.move(str(temp_restore_path), str(target_path))
                restored_items.append(str(target_path))
            
            elif strategy == RollbackStrategy.PARTIAL_RESTORE:
                # For partial restore, we would need a manifest of what to restore
                # For now, restore everything
                if target_path.exists():
                    if target_path.is_dir():
                        shutil.rmtree(str(target_path))
                    else:
                        target_path.unlink()
                
                shutil.move(str(temp_restore_path), str(target_path))
                restored_items.append(str(target_path))
            
            execution_time = datetime.now() - start_time
            
            return RollbackResult(
                success=True,
                rollback_id=f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                backup_id=backup_path.stem,
                restored_items=restored_items,
                failed_items=failed_items,
                execution_time=execution_time,
                warnings=[],
                error_details=None,
            )
            
        except Exception as e:
            execution_time = datetime.now() - start_time
            self.logger.error(f"Error restoring backup: {e}")
            return RollbackResult(
                success=False,
                rollback_id=f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                backup_id=backup_path.stem,
                restored_items=restored_items,
                failed_items=failed_items + [str(target_path)],
                execution_time=execution_time,
                error_details=str(e),
            )
    
    def validate_backup(self, backup_path: Path, metadata: BackupMetadata) -> bool:
        """Validate backup integrity."""
        try:
            if not backup_path.exists():
                return False
            
            # Check file size
            actual_size = backup_path.stat().st_size
            if actual_size != metadata.size_bytes:
                self.logger.warning(f"Backup size mismatch: expected {metadata.size_bytes}, got {actual_size}")
                return False
            
            # Check checksum if available
            if metadata.checksum:
                actual_checksum = self._calculate_file_checksum(backup_path, metadata.checksum.split(':')[0])
                if actual_checksum != metadata.checksum:
                    self.logger.warning(f"Backup checksum mismatch: expected {metadata.checksum}, got {actual_checksum}")
                    return False
            
            # Try to read the backup file
            if backup_path.suffix == '.zip':
                with zipfile.ZipFile(backup_path, 'r') as zf:
                    zf.testzip()
            elif backup_path.suffix in ['.tar', '.tar.gz', '.tar.bz2', '.tar.xz']:
                with tarfile.open(backup_path, 'r:*') as tf:
                    # Just try to get members to validate
                    tf.getmembers()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating backup: {e}")
            return False
    
    async def _copy_directory(self, source: Path, target: Path, config: BackupConfig) -> None:
        """Copy directory with filtering."""
        target.mkdir(parents=True, exist_ok=True)
        
        for item in source.iterdir():
            # Skip excluded patterns
            if any(pattern in str(item) for pattern in config.exclude_patterns):
                continue
            
            # Only include specified patterns
            if config.include_patterns and not any(pattern in str(item) for pattern in config.include_patterns):
                continue
            
            if item.is_dir():
                await self._copy_directory(item, target / item.name, config)
            else:
                shutil.copy2(str(item), str(target / item.name))
    
    async def _create_zip_backup(self, source: Path, target: Path, config: BackupConfig) -> None:
        """Create ZIP backup."""
        with zipfile.ZipFile(str(target), 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in source.rglob('*'):
                # Skip excluded patterns
                if any(pattern in str(file_path) for pattern in config.exclude_patterns):
                    continue
                
                # Only include specified patterns
                if config.include_patterns and not any(pattern in str(file_path) for pattern in config.include_patterns):
                    continue
                
                arcname = file_path.relative_to(source)
                zf.write(str(file_path), str(arcname))
    
    async def _create_tar_backup(self, source: Path, target: Path, config: BackupConfig, compression: CompressionType) -> None:
        """Create TAR backup."""
        mode_map = {
            CompressionType.TAR_GZ: 'w:gz',
            CompressionType.TAR_BZ2: 'w:bz2',
            CompressionType.TAR_XZ: 'w:xz',
        }
        
        mode = mode_map.get(compression, 'w')
        
        with tarfile.open(str(target), mode) as tf:
            for file_path in source.rglob('*'):
                # Skip excluded patterns
                if any(pattern in str(file_path) for pattern in config.exclude_patterns):
                    continue
                
                # Only include specified patterns
                if config.include_patterns and not any(pattern in str(file_path) for pattern in config.include_patterns):
                    continue
                
                arcname = file_path.relative_to(source)
                tf.add(str(file_path), str(arcname))
    
    async def _extract_zip_backup(self, backup_path: Path, target_path: Path) -> None:
        """Extract ZIP backup."""
        with zipfile.ZipFile(str(backup_path), 'r') as zf:
            zf.extractall(str(target_path))
    
    async def _extract_tar_backup(self, backup_path: Path, target_path: Path) -> None:
        """Extract TAR backup."""
        with tarfile.open(str(backup_path), 'r:*') as tf:
            tf.extractall(str(target_path))
    
    async def _calculate_checksum(self, file_path: Path, algorithm: str) -> str:
        """Calculate checksum for file."""
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return f"{algorithm}:{hash_func.hexdigest()}"
    
    def _calculate_file_checksum(self, file_path: Path, algorithm: str) -> str:
        """Calculate checksum for file (synchronous version)."""
        hash_func = getattr(hashlib, algorithm)()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        
        return f"{algorithm}:{hash_func.hexdigest()}"


class BackupManager:
    """Manager for backup and rollback operations."""
    
    def __init__(self, config: BackupConfig):
        self.config = config
        self.strategies: List[BackupStrategy] = []
        self.logger = logging.getLogger(__name__)
        
        # Ensure backup directory exists
        self.config.backup_root_path.mkdir(parents=True, exist_ok=True)
        
        # Register default strategies
        self._register_default_strategies()
    
    def register_strategy(self, strategy: BackupStrategy) -> None:
        """Register a backup strategy."""
        self.strategies.append(strategy)
    
    async def create_backup(
        self,
        source_path: Path,
        backup_type: BackupType,
        migration_id: Optional[str] = None,
        workspace_name: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        compression: Optional[CompressionType] = None,
    ) -> BackupResult:
        """Create a backup."""
        start_time = datetime.now()
        
        try:
            # Generate backup ID
            backup_id = f"{backup_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Determine compression
            actual_compression = compression or self.config.compression
            
            # Create backup path
            backup_filename = f"{backup_id}.{actual_compression.value if actual_compression != CompressionType.NONE else 'bak'}"
            backup_path = self.config.backup_root_path / backup_filename
            
            # Create metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=backup_type,
                created_at=start_time,
                source_path=source_path,
                backup_path=backup_path,
                size_bytes=0,  # Will be updated after creation
                file_count=0,  # Will be updated after creation
                checksum="",
                compression=actual_compression,
                migration_id=migration_id,
                workspace_name=workspace_name,
                description=description,
                tags=tags or [],
                expiration_date=start_time + timedelta(days=self.config.retention_days),
            )
            
            # Find appropriate strategy
            strategy = self._find_strategy(backup_type)
            if not strategy:
                raise ValueError(f"No strategy found for backup type: {backup_type}")
            
            # Create backup
            result = await strategy.create_backup(source_path, backup_path, self.config, metadata)
            
            # Update metadata with actual size and checksum
            if result.success and backup_path.exists():
                metadata.size_bytes = backup_path.stat().st_size
                metadata.checksum = await strategy._calculate_checksum(backup_path, self.config.checksum_algorithm) if hasattr(strategy, '_calculate_checksum') else ""
                
                # Count files
                if backup_path.suffix == '.zip':
                    with zipfile.ZipFile(backup_path, 'r') as zf:
                        metadata.file_count = len(zf.namelist())
                elif backup_path.suffix in ['.tar', '.tar.gz', '.tar.bz2', '.tar.xz']:
                    with tarfile.open(backup_path, 'r:*') as tf:
                        metadata.file_count = len(tf.getnames())
                else:
                    metadata.file_count = len(list(backup_path.rglob('*'))) if backup_path.is_dir() else 1
            
            # Save metadata
            metadata_path = backup_path.with_suffix('.meta')
            with open(metadata_path, 'w') as f:
                json.dump(metadata.to_dict(), f, indent=2)
            
            # Clean up old backups
            await self._cleanup_old_backups(backup_type, workspace_name)
            
            self.logger.info(f"Backup created successfully: {backup_id}")
            return result
            
        except Exception as e:
            execution_time = datetime.now() - start_time
            self.logger.error(f"Error creating backup: {e}")
            return BackupResult(
                success=False,
                backup_id=backup_id if 'backup_id' in locals() else "unknown",
                metadata=None,
                backup_path=None,
                execution_time=execution_time,
                error_details=str(e),
            )
    
    async def restore_backup(
        self,
        backup_id: str,
        target_path: Path,
        strategy: RollbackStrategy = RollbackStrategy.FULL_RESTORE,
    ) -> RollbackResult:
        """Restore from backup."""
        try:
            # Find backup
            backup_info = await self._find_backup(backup_id)
            if not backup_info:
                raise ValueError(f"Backup not found: {backup_id}")
            
            backup_path, metadata = backup_info
            
            # Find appropriate strategy
            backup_strategy = self._find_strategy(metadata.backup_type)
            if not backup_strategy:
                raise ValueError(f"No strategy found for backup type: {metadata.backup_type}")
            
            # Validate backup before restore
            if not backup_strategy.validate_backup(backup_path, metadata):
                raise ValueError(f"Backup validation failed: {backup_id}")
            
            # Perform restore
            result = await backup_strategy.restore_backup(backup_path, target_path, self.config, strategy)
            
            self.logger.info(f"Backup restored successfully: {backup_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error restoring backup: {e}")
            raise
    
    async def list_backups(
        self,
        backup_type: Optional[BackupType] = None,
        workspace_name: Optional[str] = None,
        migration_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[BackupMetadata]:
        """List available backups."""
        backups = []
        
        # Scan for backup files
        for backup_file in self.config.backup_root_path.glob("*"):
            if backup_file.suffix == '.meta':
                try:
                    with open(backup_file, 'r') as f:
                        metadata_dict = json.load(f)
                        metadata = BackupMetadata.from_dict(metadata_dict)
                        
                        # Apply filters
                        if backup_type and metadata.backup_type != backup_type:
                            continue
                        
                        if workspace_name and metadata.workspace_name != workspace_name:
                            continue
                        
                        if migration_id and metadata.migration_id != migration_id:
                            continue
                        
                        # Check if backup file exists
                        backup_file_path = backup_file.with_suffix('')
                        compressed_extensions = ['.zip', '.tar', '.gz', '.bz2', '.xz']
                        for ext in compressed_extensions:
                            if backup_file.with_suffix(ext).exists():
                                backup_file_path = backup_file.with_suffix(ext)
                                break
                        
                        if not backup_file_path.exists():
                            continue
                        
                        backups.append(metadata)
                        
                except Exception as e:
                    self.logger.warning(f"Error reading backup metadata {backup_file}: {e}")
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit
        if limit:
            backups = backups[:limit]
        
        return backups
    
    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup."""
        try:
            # Find backup
            backup_info = await self._find_backup(backup_id)
            if not backup_info:
                return False
            
            backup_path, metadata = backup_info
            
            # Delete backup file
            if backup_path.exists():
                if backup_path.is_dir():
                    shutil.rmtree(str(backup_path))
                else:
                    backup_path.unlink()
            
            # Delete metadata file
            metadata_path = backup_path.with_suffix('.meta')
            if metadata_path.exists():
                metadata_path.unlink()
            
            self.logger.info(f"Backup deleted: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting backup {backup_id}: {e}")
            return False
    
    async def validate_backup(self, backup_id: str) -> bool:
        """Validate backup integrity."""
        try:
            # Find backup
            backup_info = await self._find_backup(backup_id)
            if not backup_info:
                return False
            
            backup_path, metadata = backup_info
            
            # Find appropriate strategy
            strategy = self._find_strategy(metadata.backup_type)
            if not strategy:
                return False
            
            return strategy.validate_backup(backup_path, metadata)
            
        except Exception as e:
            self.logger.error(f"Error validating backup {backup_id}: {e}")
            return False
    
    def _register_default_strategies(self) -> None:
        """Register default backup strategies."""
        self.register_strategy(FileSystemBackupStrategy())
    
    def _find_strategy(self, backup_type: BackupType) -> Optional[BackupStrategy]:
        """Find strategy for backup type."""
        for strategy in self.strategies:
            if strategy.can_handle(backup_type):
                return strategy
        return None
    
    async def _find_backup(self, backup_id: str) -> Optional[Tuple[Path, BackupMetadata]]:
        """Find backup by ID."""
        # Look for metadata file
        metadata_pattern = f"{backup_id}.meta"
        metadata_files = list(self.config.backup_root_path.glob(metadata_pattern))
        
        if not metadata_files:
            return None
        
        metadata_file = metadata_files[0]
        
        try:
            with open(metadata_file, 'r') as f:
                metadata_dict = json.load(f)
                metadata = BackupMetadata.from_dict(metadata_dict)
            
            # Find backup file
            backup_path = metadata_file.with_suffix('')
            compressed_extensions = ['.zip', '.tar', '.gz', '.bz2', '.xz']
            for ext in compressed_extensions:
                if metadata_file.with_suffix(ext).exists():
                    backup_path = metadata_file.with_suffix(ext)
                    break
            
            return backup_path, metadata
            
        except Exception as e:
            self.logger.error(f"Error reading backup metadata for {backup_id}: {e}")
            return None
    
    async def _cleanup_old_backups(self, backup_type: BackupType, workspace_name: Optional[str] = None) -> None:
        """Clean up old backups based on retention policy."""
        try:
            # Get all backups of this type
            backups = await self.list_backups(backup_type=backup_type, workspace_name=workspace_name)
            
            # Remove expired backups
            current_time = datetime.now()
            expired_backups = [b for b in backups if b.expiration_date and b.expiration_date < current_time]
            
            for backup in expired_backups:
                await self.delete_backup(backup.backup_id)
            
            # If we have too many backups, remove oldest ones
            if len(backups) > self.config.max_backups:
                backups_to_remove = backups[self.config.max_backups:]
                for backup in backups_to_remove:
                    await self.delete_backup(backup.backup_id)
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old backups: {e}")


# Factory function for creating backup manager
def create_backup_manager(backup_root_path: Path) -> BackupManager:
    """Create backup manager with default configuration."""
    config = BackupConfig(
        backup_root_path=backup_root_path,
        compression=CompressionType.TAR_GZ,
        retention_days=30,
        max_backups=10,
    )
    
    return BackupManager(config)