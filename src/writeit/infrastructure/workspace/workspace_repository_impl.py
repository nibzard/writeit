"""LMDB implementation of WorkspaceRepository.

Provides concrete LMDB-backed storage for workspaces with
lifecycle management, metadata tracking, and integrity validation.
"""

import shutil
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ...domains.workspace.repositories.workspace_repository import (
    WorkspaceRepository,
    ByNameSpecification,
    ByTagSpecification,
    ActiveWorkspaceSpecification,
    RecentlyAccessedSpecification
)
from ...domains.workspace.entities.workspace import Workspace
from ...domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...domains.workspace.value_objects.workspace_path import WorkspacePath
from ...shared.repository import RepositoryError, EntityNotFoundError, EntityAlreadyExistsError
from ..base.repository_base import LMDBRepositoryBase
from ..base.storage_manager import LMDBStorageManager
from ..base.serialization import DomainEntitySerializer


class LMDBWorkspaceRepository(LMDBRepositoryBase[Workspace], WorkspaceRepository):
    """LMDB implementation of WorkspaceRepository.
    
    Stores workspaces with global storage (not workspace-isolated)
    and provides comprehensive workspace lifecycle management.
    """
    
    def __init__(self, storage_manager: LMDBStorageManager):
        """Initialize repository.
        
        Args:
            storage_manager: LMDB storage manager
        """
        # Use global workspace for workspace metadata
        global_workspace = WorkspaceName.from_string("__global__")
        super().__init__(
            storage_manager=storage_manager,
            workspace_name=global_workspace,
            entity_type=Workspace,
            db_name="workspaces",
            db_key="workspace_metadata"
        )
    
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with workspace-specific types.
        
        Args:
            serializer: Serializer to configure
        """
        # Register value objects
        serializer.register_value_object(WorkspaceName)
        serializer.register_value_object(WorkspacePath)
        
        # Register entity types
        serializer.register_type("Workspace", Workspace)
        serializer.register_type("WorkspaceConfiguration", WorkspaceConfiguration)
    
    def _get_entity_id(self, entity: Workspace) -> Any:
        """Extract entity ID for storage key.
        
        Args:
            entity: Workspace entity
            
        Returns:
            Entity identifier
        """
        return entity.name
    
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID.
        
        Args:
            entity_id: Entity identifier (WorkspaceName)
            
        Returns:
            Storage key string
        """
        # Don't use workspace prefix for workspace metadata
        if isinstance(entity_id, WorkspaceName):
            return f"workspace:{entity_id.value}"
        else:
            return f"workspace:{str(entity_id)}"
    
    async def find_by_name(self, name: WorkspaceName) -> Optional[Workspace]:
        """Find workspace by name.
        
        Args:
            name: Workspace name to search for
            
        Returns:
            Workspace if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        return await self.find_by_id(name)
    
    async def find_by_path(self, path: WorkspacePath) -> Optional[Workspace]:
        """Find workspace by filesystem path.
        
        Args:
            path: Workspace path to search for
            
        Returns:
            Workspace if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        all_workspaces = await self.find_all()
        for workspace in all_workspaces:
            if workspace.root_path.value == path.value:
                return workspace
        return None
    
    async def find_active_workspace(self) -> Optional[Workspace]:
        """Find the currently active workspace.
        
        Returns:
            Active workspace if set, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ActiveWorkspaceSpecification()
        active_workspaces = await self.find_by_specification(spec)
        return active_workspaces[0] if active_workspaces else None
    
    async def find_recent_workspaces(self, limit: int = 5) -> List[Workspace]:
        """Find recently used workspaces.
        
        Args:
            limit: Maximum number of workspaces to return
            
        Returns:
            List of recent workspaces, ordered by last access time desc
            
        Raises:
            RepositoryError: If query operation fails
        """
        all_workspaces = await self.find_all()
        
        # Filter workspaces with last_accessed time
        accessed_workspaces = [
            workspace for workspace in all_workspaces
            if workspace.last_accessed is not None
        ]
        
        # Sort by last access time (newest first)
        accessed_workspaces.sort(key=lambda w: w.last_accessed, reverse=True)
        
        return accessed_workspaces[:limit]
    
    async def find_workspaces_by_tag(self, tag: str) -> List[Workspace]:
        """Find workspaces with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of workspaces with the tag
            
        Raises:
            RepositoryError: If query operation fails
        """
        # Check metadata for tags
        all_workspaces = await self.find_all()
        return [
            workspace for workspace in all_workspaces
            if "tags" in workspace.metadata and tag in workspace.metadata["tags"]
        ]
    
    async def is_name_available(self, name: WorkspaceName) -> bool:
        """Check if workspace name is available.
        
        Args:
            name: Workspace name to check
            
        Returns:
            True if name is available, False if taken
            
        Raises:
            RepositoryError: If check operation fails
        """
        existing = await self.find_by_name(name)
        return existing is None
    
    async def is_path_available(self, path: WorkspacePath) -> bool:
        """Check if workspace path is available.
        
        Args:
            path: Workspace path to check
            
        Returns:
            True if path is available, False if taken
            
        Raises:
            RepositoryError: If check operation fails
        """
        existing = await self.find_by_path(path)
        return existing is None
    
    async def set_active_workspace(self, workspace: Workspace) -> None:
        """Set the active workspace.
        
        Args:
            workspace: Workspace to activate
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If activation fails
        """
        # First, deactivate all workspaces
        all_workspaces = await self.find_all()
        for ws in all_workspaces:
            if ws.is_active:
                deactivated = ws.deactivate()
                await self.save(deactivated)
        
        # Then activate the target workspace
        if not await self.exists(workspace.name):
            raise EntityNotFoundError("Workspace", workspace.name)
        
        activated = workspace.activate()
        await self.save(activated)
    
    async def update_last_accessed(self, workspace: Workspace) -> None:
        """Update workspace last access time.
        
        Args:
            workspace: Workspace to update
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If update operation fails
        """
        if not await self.exists(workspace.name):
            raise EntityNotFoundError("Workspace", workspace.name)
        
        updated = workspace.set_metadata("last_accessed", datetime.now().isoformat())
        await self.save(updated)
    
    async def get_workspace_stats(self, workspace: Workspace) -> Dict[str, Any]:
        """Get workspace usage statistics.
        
        Args:
            workspace: Workspace to get stats for
            
        Returns:
            Dictionary with workspace statistics
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If stats calculation fails
        """
        if not await self.exists(workspace.name):
            raise EntityNotFoundError("Workspace", workspace.name)
        
        try:
            # Calculate storage size
            storage_size = workspace.get_size_on_disk()
            
            # Basic statistics from workspace entity
            stats = {
                "created_at": workspace.created_at.isoformat(),
                "last_accessed_at": workspace.last_accessed.isoformat() if workspace.last_accessed else None,
                "storage_size_bytes": storage_size,
                "is_active": workspace.is_active,
                "is_initialized": workspace.is_initialized(),
                "configuration_count": len(workspace.configuration.settings) if workspace.configuration else 0,
                "metadata_count": len(workspace.metadata)
            }
            
            # TODO: Add pipeline and template counts when those repositories are available
            stats.update({
                "total_pipelines": 0,  # Placeholder
                "total_runs": 0,      # Placeholder
                "total_templates": 0   # Placeholder
            })
            
            return stats
            
        except Exception as e:
            raise RepositoryError(f"Failed to calculate workspace stats: {e}") from e
    
    async def validate_workspace_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace integrity and consistency.
        
        Args:
            workspace: Workspace to validate
            
        Returns:
            List of validation errors, empty if valid
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If validation operation fails
        """
        if not await self.exists(workspace.name):
            raise EntityNotFoundError("Workspace", workspace.name)
        
        errors = []
        
        try:
            # Check directory structure
            if not workspace.root_path.exists():
                errors.append(f"Workspace root directory does not exist: {workspace.root_path}")
            elif not workspace.root_path.is_directory():
                errors.append(f"Workspace root path is not a directory: {workspace.root_path}")
            
            # Check required subdirectories
            required_dirs = [
                ("templates", workspace.get_templates_path()),
                ("storage", workspace.get_storage_path()),
                ("cache", workspace.get_cache_path())
            ]
            
            for dir_name, dir_path in required_dirs:
                if not dir_path.exists():
                    errors.append(f"Missing {dir_name} directory: {dir_path}")
                elif not dir_path.is_directory():
                    errors.append(f"{dir_name} path is not a directory: {dir_path}")
            
            # Check configuration validity
            if workspace.configuration:
                config_errors = workspace.configuration.validate()
                errors.extend(f"Configuration error: {error}" for error in config_errors)
            else:
                errors.append("Workspace configuration is missing")
            
            # Check for common file system issues
            try:
                test_file = workspace.root_path.join(".write_test")
                test_file.value.write_text("test")
                test_file.value.unlink()
            except (OSError, PermissionError):
                errors.append("Workspace directory is not writable")
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
        
        return errors
    
    async def backup_workspace(
        self, 
        workspace: Workspace, 
        backup_path: WorkspacePath
    ) -> bool:
        """Create a backup of workspace data.
        
        Args:
            workspace: Workspace to backup
            backup_path: Path to store backup
            
        Returns:
            True if backup successful, False otherwise
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If backup operation fails
        """
        if not await self.exists(workspace.name):
            raise EntityNotFoundError("Workspace", workspace.name)
        
        try:
            # Ensure backup directory exists
            backup_path.create_directories(exist_ok=True)
            
            # Copy workspace directory
            source_path = workspace.root_path.value
            target_path = backup_path.value / workspace.name.value
            
            if source_path.exists():
                shutil.copytree(source_path, target_path, dirs_exist_ok=True)
            
            # Save workspace metadata
            metadata_file = backup_path.value / f"{workspace.name.value}_metadata.json"
            import json
            metadata = {
                "name": workspace.name.value,
                "created_at": workspace.created_at.isoformat(),
                "backup_created_at": datetime.now().isoformat(),
                "configuration": workspace.configuration.to_dict() if workspace.configuration else {},
                "metadata": workspace.metadata
            }
            metadata_file.write_text(json.dumps(metadata, indent=2))
            
            return True
            
        except Exception as e:
            raise RepositoryError(f"Backup failed: {e}") from e
    
    async def restore_workspace(
        self, 
        backup_path: WorkspacePath, 
        target_name: WorkspaceName
    ) -> Workspace:
        """Restore workspace from backup.
        
        Args:
            backup_path: Path to backup data
            target_name: Name for restored workspace
            
        Returns:
            Restored workspace
            
        Raises:
            EntityAlreadyExistsError: If target name already exists
            RepositoryError: If restore operation fails
        """
        if not await self.is_name_available(target_name):
            raise EntityAlreadyExistsError("Workspace", target_name)
        
        try:
            # Load metadata
            metadata_file = backup_path.value / f"{target_name.value}_metadata.json"
            if not metadata_file.exists():
                raise RepositoryError(f"Backup metadata not found: {metadata_file}")
            
            import json
            metadata = json.loads(metadata_file.read_text())
            
            # Create target workspace path
            # TODO: Get workspace root from configuration
            workspace_root = Path.home() / ".writeit" / "workspaces" / target_name.value
            target_path = WorkspacePath(workspace_root)
            
            # Copy backup data
            source_path = backup_path.value / target_name.value
            if source_path.exists():
                shutil.copytree(source_path, target_path.value, dirs_exist_ok=True)
            
            # Create workspace configuration
            config_data = metadata.get("configuration", {})
            configuration = WorkspaceConfiguration.from_dict(config_data)
            
            # Create workspace entity
            workspace = Workspace.create(
                name=target_name,
                root_path=target_path,
                configuration=configuration,
                metadata=metadata.get("metadata", {})
            )
            
            # Save workspace
            await self.save(workspace)
            
            return workspace
            
        except Exception as e:
            raise RepositoryError(f"Restore failed: {e}") from e
    
    async def cleanup_inactive_workspaces(
        self, 
        inactive_since: datetime
    ) -> List[WorkspaceName]:
        """Clean up workspaces inactive since a given date.
        
        Args:
            inactive_since: Delete workspaces not accessed since this date
            
        Returns:
            List of deleted workspace names
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        try:
            all_workspaces = await self.find_all()
            deleted_names = []
            
            for workspace in all_workspaces:
                # Check if workspace is inactive
                last_access = workspace.last_accessed or workspace.created_at
                if last_access < inactive_since and not workspace.is_active:
                    # Delete workspace directory
                    if workspace.root_path.exists():
                        shutil.rmtree(workspace.root_path.value)
                    
                    # Delete workspace metadata
                    await self.delete(workspace)
                    deleted_names.append(workspace.name)
            
            return deleted_names
            
        except Exception as e:
            raise RepositoryError(f"Cleanup failed: {e}") from e
    
    async def get_all_workspace_names(self) -> List[WorkspaceName]:
        """Get names of all workspaces.
        
        Returns:
            List of workspace names
        """
        all_workspaces = await self.find_all()
        return [workspace.name for workspace in all_workspaces]
    
    async def create_workspace_directories(self, workspace: Workspace) -> None:
        """Ensure workspace directory structure exists.
        
        Args:
            workspace: Workspace to create directories for
            
        Raises:
            RepositoryError: If directory creation fails
        """
        try:
            workspace.ensure_directory_structure()
        except Exception as e:
            raise RepositoryError(f"Failed to create workspace directories: {e}") from e
    
    async def export_workspace_metadata(self, workspace: Workspace) -> Dict[str, Any]:
        """Export workspace metadata for migration or backup.
        
        Args:
            workspace: Workspace to export
            
        Returns:
            Exportable metadata dictionary
        """
        return {
            "name": workspace.name.value,
            "root_path": str(workspace.root_path.value),
            "is_active": workspace.is_active,
            "created_at": workspace.created_at.isoformat(),
            "updated_at": workspace.updated_at.isoformat(),
            "last_accessed": workspace.last_accessed.isoformat() if workspace.last_accessed else None,
            "configuration": workspace.configuration.to_dict() if workspace.configuration else {},
            "metadata": workspace.metadata
        }