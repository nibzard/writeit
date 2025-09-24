# ABOUTME: Rollback system for WriteIt migrations
# ABOUTME: Provides rollback capabilities for migration operations

import shutil
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
import yaml

from .data_migrator import MigrationResult


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    
    success: bool
    message: str
    rolled_back_items: int = 0
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    backup_path: Optional[Path] = None
    restored_path: Optional[Path] = None


@dataclass
class MigrationBackup:
    """Represents a migration backup."""
    
    backup_id: str
    migration_id: str
    workspace_name: str
    created_at: datetime
    backup_path: Path
    backup_type: str  # "full", "config", "cache", "workspace"
    metadata: Dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0


class MigrationRollbackManager:
    """Manages rollback operations for migrations."""
    
    def __init__(self, backup_root: Optional[Path] = None):
        """Initialize rollback manager.
        
        Args:
            backup_root: Root directory for storing backups
        """
        if backup_root is None:
            backup_root = Path.home() / ".writeit" / "migration_backups"
        
        self.backup_root = backup_root
        self.backup_root.mkdir(parents=True, exist_ok=True)
    
    def create_migration_backup(
        self,
        migration_id: str,
        workspace_name: str,
        source_path: Path,
        backup_type: str = "full"
    ) -> MigrationBackup:
        """Create a backup before migration.
        
        Args:
            migration_id: Unique identifier for the migration
            workspace_name: Name of the workspace being migrated
            source_path: Path to the source data to backup
            backup_type: Type of backup ("full", "config", "cache", "workspace")
            
        Returns:
            MigrationBackup object
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{migration_id}_{timestamp}"
        
        # Create backup directory
        backup_dir = self.backup_root / backup_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup metadata
        backup = MigrationBackup(
            backup_id=backup_id,
            migration_id=migration_id,
            workspace_name=workspace_name,
            created_at=datetime.now(),
            backup_path=backup_dir,
            backup_type=backup_type,
            metadata={
                "source_path": str(source_path),
                "backup_type": backup_type,
                "created_by": "writeit_migration"
            }
        )
        
        try:
            if backup_type == "full":
                self._create_full_backup(source_path, backup_dir)
            elif backup_type == "workspace":
                self._create_workspace_backup(source_path, backup_dir)
            elif backup_type == "config":
                self._create_config_backup(source_path, backup_dir)
            elif backup_type == "cache":
                self._create_cache_backup(source_path, backup_dir)
            else:
                raise ValueError(f"Unknown backup type: {backup_type}")
            
            # Calculate backup size
            backup.size_bytes = self._calculate_directory_size(backup_dir)
            
            # Save backup metadata
            self._save_backup_metadata(backup)
            
            return backup
            
        except Exception as e:
            # Clean up failed backup
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            raise RuntimeError(f"Failed to create backup: {str(e)}")
    
    def rollback_migration(
        self,
        migration_id: str,
        workspace_name: Optional[str] = None,
        target_path: Optional[Path] = None,
        backup_id: Optional[str] = None
    ) -> RollbackResult:
        """Rollback a migration using backup.
        
        Args:
            migration_id: ID of the migration to rollback
            workspace_name: Name of the workspace (for verification)
            target_path: Where to restore the backup (defaults to original location)
            backup_id: Specific backup ID to use (auto-detected if None)
            
        Returns:
            RollbackResult object
        """
        result = RollbackResult()
        
        try:
            # Find the backup
            backup = self._find_backup(migration_id, workspace_name, backup_id)
            if backup is None:
                result.success = False
                result.message = f"No backup found for migration {migration_id}"
                return result
            
            result.backup_path = backup.backup_path
            
            # Determine target path
            if target_path is None:
                target_path = Path(backup.metadata.get("source_path", "."))
            result.restored_path = target_path
            
            # Verify workspace name if provided
            if workspace_name and backup.workspace_name != workspace_name:
                result.success = False
                result.message = f"Workspace name mismatch: expected {workspace_name}, got {backup.workspace_name}"
                return result
            
            # Perform rollback
            if backup.backup_type == "full":
                result = self._rollback_full_backup(backup, target_path, result)
            elif backup.backup_type == "workspace":
                result = self._rollback_workspace_backup(backup, target_path, result)
            elif backup.backup_type == "config":
                result = self._rollback_config_backup(backup, target_path, result)
            elif backup.backup_type == "cache":
                result = self._rollback_cache_backup(backup, target_path, result)
            else:
                result.success = False
                result.message = f"Unknown backup type: {backup.backup_type}"
                return result
            
            result.success = len(result.errors) == 0
            result.message = f"Successfully rolled back migration {migration_id}" if result.success else \
                           f"Rollback completed with {len(result.errors)} errors"
            
            return result
            
        except Exception as e:
            result.success = False
            result.message = f"Rollback failed: {str(e)}"
            result.errors.append(str(e))
            return result
    
    def list_backups(
        self,
        workspace_name: Optional[str] = None,
        migration_id: Optional[str] = None,
        backup_type: Optional[str] = None
    ) -> List[MigrationBackup]:
        """List available backups.
        
        Args:
            workspace_name: Filter by workspace name
            migration_id: Filter by migration ID
            backup_type: Filter by backup type
            
        Returns:
            List of matching backups
        """
        backups = []
        
        for backup_dir in self.backup_root.iterdir():
            if not backup_dir.is_dir():
                continue
            
            metadata_file = backup_dir / "backup_metadata.json"
            if not metadata_file.exists():
                continue
            
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                backup = MigrationBackup(
                    backup_id=metadata["backup_id"],
                    migration_id=metadata["migration_id"],
                    workspace_name=metadata["workspace_name"],
                    created_at=datetime.fromisoformat(metadata["created_at"]),
                    backup_path=backup_dir,
                    backup_type=metadata["backup_type"],
                    metadata=metadata.get("metadata", {}),
                    size_bytes=metadata.get("size_bytes", 0)
                )
                
                # Apply filters
                if workspace_name and backup.workspace_name != workspace_name:
                    continue
                
                if migration_id and backup.migration_id != migration_id:
                    continue
                
                if backup_type and backup.backup_type != backup_type:
                    continue
                
                backups.append(backup)
                
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda b: b.created_at, reverse=True)
        return backups
    
    def cleanup_old_backups(self, days_to_keep: int = 30) -> int:
        """Clean up old backup files.
        
        Args:
            days_to_keep: Number of days to keep backups
            
        Returns:
            Number of backups cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        for backup in self.list_backups():
            if backup.created_at < cutoff_date:
                try:
                    if backup.backup_path.exists():
                        shutil.rmtree(backup.backup_path)
                        cleaned_count += 1
                except OSError:
                    continue
        
        return cleaned_count
    
    def _create_full_backup(self, source_path: Path, backup_dir: Path) -> None:
        """Create a full backup of the source."""
        if source_path.is_file():
            shutil.copy2(source_path, backup_dir / source_path.name)
        else:
            shutil.copytree(source_path, backup_dir / "data")
    
    def _create_workspace_backup(self, source_path: Path, backup_dir: Path) -> None:
        """Create a workspace-specific backup."""
        writeit_dir = source_path / ".writeit"
        if writeit_dir.exists():
            shutil.copytree(writeit_dir, backup_dir / ".writeit")
        
        # Also backup workspace.yaml if it exists
        workspace_config = source_path / "workspace.yaml"
        if workspace_config.exists():
            shutil.copy2(workspace_config, backup_dir / "workspace.yaml")
    
    def _create_config_backup(self, source_path: Path, backup_dir: Path) -> None:
        """Create a configuration backup."""
        # Look for config files in various locations
        config_files = [
            source_path / ".writeit" / "config.yaml",
            source_path / ".writeit" / "config.yml",
            source_path / "config.yaml",
            source_path / "workspace.yaml",
        ]
        
        for config_file in config_files:
            if config_file.exists():
                shutil.copy2(config_file, backup_dir / config_file.name)
    
    def _create_cache_backup(self, source_path: Path, backup_dir: Path) -> None:
        """Create a cache backup."""
        # Look for cache directories and files
        cache_locations = [
            source_path / ".writeit" / "cache",
            source_path / "cache",
            source_path / ".cache",
            source_path / ".writeit" / "cache.mdb",
            source_path / ".writeit" / "cache.lmdb",
        ]
        
        for cache_location in cache_locations:
            if cache_location.exists():
                if cache_location.is_file():
                    shutil.copy2(cache_location, backup_dir / cache_location.name)
                else:
                    shutil.copytree(cache_location, backup_dir / cache_location.name)
    
    def _rollback_full_backup(self, backup: MigrationBackup, target_path: Path, result: RollbackResult) -> RollbackResult:
        """Rollback a full backup."""
        backup_data = backup.backup_path / "data"
        
        if not backup_data.exists():
            result.errors.append("Backup data not found")
            return result
        
        # Remove existing target if it exists
        if target_path.exists():
            if target_path.is_file():
                target_path.unlink()
            else:
                shutil.rmtree(target_path)
        
        # Restore backup
        if backup_data.is_file():
            shutil.copy2(backup_data, target_path)
            result.rolled_back_items = 1
        else:
            shutil.copytree(backup_data, target_path)
            result.rolled_back_items = len(list(target_path.rglob('*')))
        
        return result
    
    def _rollback_workspace_backup(self, backup: MigrationBackup, target_path: Path, result: RollbackResult) -> RollbackResult:
        """Rollback a workspace backup."""
        writeit_backup = backup.backup_path / ".writeit"
        workspace_config_backup = backup.backup_path / "workspace.yaml"
        
        rolled_back_items = 0
        
        # Restore .writeit directory
        if writeit_backup.exists():
            target_writeit = target_path / ".writeit"
            if target_writeit.exists():
                shutil.rmtree(target_writeit)
            shutil.copytree(writeit_backup, target_writeit)
            rolled_back_items += len(list(target_writeit.rglob('*')))
        
        # Restore workspace.yaml
        if workspace_config_backup.exists():
            target_config = target_path / "workspace.yaml"
            shutil.copy2(workspace_config_backup, target_config)
            rolled_back_items += 1
        
        result.rolled_back_items = rolled_back_items
        return result
    
    def _rollback_config_backup(self, backup: MigrationBackup, target_path: Path, result: RollbackResult) -> RollbackResult:
        """Rollback a configuration backup."""
        config_files = list(backup.backup_path.glob("*.yaml")) + list(backup.backup_path.glob("*.yml"))
        
        for config_file in config_files:
            target_config = target_path / config_file.name
            target_config.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(config_file, target_config)
            result.rolled_back_items += 1
        
        return result
    
    def _rollback_cache_backup(self, backup: MigrationBackup, target_path: Path, result: RollbackResult) -> RollbackResult:
        """Rollback a cache backup."""
        cache_items = list(backup.backup_path.iterdir())
        
        for cache_item in cache_items:
            if cache_item.is_file():
                target_cache = target_path / cache_item.name
                target_cache.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(cache_item, target_cache)
                result.rolled_back_items += 1
            else:
                target_cache = target_path / cache_item.name
                if target_cache.exists():
                    shutil.rmtree(target_cache)
                shutil.copytree(cache_item, target_cache)
                result.rolled_back_items += len(list(target_cache.rglob('*')))
        
        return result
    
    def _find_backup(
        self,
        migration_id: str,
        workspace_name: Optional[str] = None,
        backup_id: Optional[str] = None
    ) -> Optional[MigrationBackup]:
        """Find a specific backup."""
        if backup_id:
            # Look for specific backup ID
            for backup in self.list_backups():
                if backup.backup_id == backup_id:
                    return backup
        else:
            # Find most recent backup for migration
            backups = self.list_backups(migration_id=migration_id, workspace_name=workspace_name)
            if backups:
                return backups[0]  # Most recent first
        
        return None
    
    def _save_backup_metadata(self, backup: MigrationBackup) -> None:
        """Save backup metadata to file."""
        metadata = {
            "backup_id": backup.backup_id,
            "migration_id": backup.migration_id,
            "workspace_name": backup.workspace_name,
            "created_at": backup.created_at.isoformat(),
            "backup_type": backup.backup_type,
            "metadata": backup.metadata,
            "size_bytes": backup.size_bytes
        }
        
        metadata_file = backup.backup_path / "backup_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _calculate_directory_size(self, directory: Path) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        try:
            for file_path in directory.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            pass
        return total_size


def create_rollback_manager(backup_root: Optional[Path] = None) -> MigrationRollbackManager:
    """Create rollback manager instance."""
    return MigrationRollbackManager(backup_root)