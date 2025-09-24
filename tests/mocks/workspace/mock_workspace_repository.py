"""Mock implementation of WorkspaceRepository for testing."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from writeit.domains.workspace.repositories.workspace_repository import WorkspaceRepository
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError, MockEntityAlreadyExistsError


class MockWorkspaceRepository(BaseMockRepository[Workspace], WorkspaceRepository):
    """Mock implementation of WorkspaceRepository.
    
    Provides in-memory storage for workspaces with lifecycle management
    and metadata tracking.
    """
    
    def __init__(self):
        # Workspace repository doesn't have workspace isolation since it manages workspaces
        super().__init__(None)
        self._active_workspace: Optional[str] = None
        
    def _get_entity_id(self, entity: Workspace) -> Any:
        """Extract entity ID from workspace."""
        return str(entity.name.value)
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "Workspace"
        
    # Repository interface implementation
    
    async def save(self, entity: Workspace) -> None:
        """Save or update a workspace."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id, workspace="global")
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: WorkspaceName) -> Optional[Workspace]:
        """Find workspace by name (ID)."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        workspace = self._get_entity(str(entity_id.value), workspace="global")
        self._log_event("find_by_id", self._get_entity_type_name(), 
                       str(entity_id.value), found=workspace is not None)
        return workspace
        
    async def find_all(self) -> List[Workspace]:
        """Find all workspaces."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        workspaces = self._get_all_entities(workspace="global")
        self._log_event("find_all", self._get_entity_type_name(), count=len(workspaces))
        return workspaces
        
    async def find_by_specification(self, spec: Specification[Workspace]) -> List[Workspace]:
        """Find workspaces matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        workspaces = self._find_entities_by_specification(spec, workspace="global")
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(workspaces))
        return workspaces
        
    async def exists(self, entity_id: WorkspaceName) -> bool:
        """Check if workspace exists."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        exists = self._entity_exists(str(entity_id.value), workspace="global")
        self._log_event("exists", self._get_entity_type_name(), str(entity_id.value), exists=exists)
        return exists
        
    async def delete(self, entity: Workspace) -> None:
        """Delete a workspace."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id, workspace="global"):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
            
        # Clear active workspace if this was it
        if self._active_workspace == entity_id:
            self._active_workspace = None
            
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: WorkspaceName) -> bool:
        """Delete workspace by name."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(str(entity_id.value), workspace="global")
        
        # Clear active workspace if this was it
        if deleted and self._active_workspace == str(entity_id.value):
            self._active_workspace = None
            
        self._log_event("delete_by_id", self._get_entity_type_name(), 
                       str(entity_id.value), deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total workspaces."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        total = self._count_entities(workspace="global")
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    # WorkspaceRepository-specific methods
    
    async def find_by_name(self, name: WorkspaceName) -> Optional[Workspace]:
        """Find workspace by name."""
        return await self.find_by_id(name)
        
    async def find_by_path(self, path: WorkspacePath) -> Optional[Workspace]:
        """Find workspace by filesystem path."""
        await self._check_error_condition("find_by_path")
        self._increment_call_count("find_by_path")
        await self._apply_call_delay("find_by_path")
        
        workspaces = self._get_all_entities(workspace="global")
        for workspace in workspaces:
            if workspace.path == path:
                self._log_event("find_by_path", self._get_entity_type_name(), 
                              str(workspace.name.value), found=True, path=str(path.value))
                return workspace
                
        self._log_event("find_by_path", self._get_entity_type_name(), 
                       found=False, path=str(path.value))
        return None
        
    async def find_active_workspace(self) -> Optional[Workspace]:
        """Find the currently active workspace."""
        await self._check_error_condition("find_active_workspace")
        self._increment_call_count("find_active_workspace")
        await self._apply_call_delay("find_active_workspace")
        
        if not self._active_workspace:
            self._log_event("find_active_workspace", self._get_entity_type_name(), found=False)
            return None
            
        workspace = self._get_entity(self._active_workspace, workspace="global")
        self._log_event("find_active_workspace", self._get_entity_type_name(), 
                       self._active_workspace, found=workspace is not None)
        return workspace
        
    async def find_recent_workspaces(self, limit: int = 5) -> List[Workspace]:
        """Find recently used workspaces."""
        await self._check_error_condition("find_recent_workspaces")
        self._increment_call_count("find_recent_workspaces")
        await self._apply_call_delay("find_recent_workspaces")
        
        workspaces = self._get_all_entities(workspace="global")
        
        # Sort by last access time desc
        workspaces.sort(key=lambda w: w.last_accessed_at or datetime.min, reverse=True)
        recent_workspaces = workspaces[:limit]
        
        self._log_event("find_recent_workspaces", self._get_entity_type_name(), 
                       count=len(recent_workspaces), limit=limit)
        return recent_workspaces
        
    async def find_workspaces_by_tag(self, tag: str) -> List[Workspace]:
        """Find workspaces with a specific tag."""
        await self._check_error_condition("find_workspaces_by_tag")
        self._increment_call_count("find_workspaces_by_tag")
        await self._apply_call_delay("find_workspaces_by_tag")
        
        workspaces = self._get_all_entities(workspace="global")
        matching_workspaces = [w for w in workspaces if tag in w.tags]
        
        self._log_event("find_workspaces_by_tag", self._get_entity_type_name(), 
                       count=len(matching_workspaces), tag=tag)
        return matching_workspaces
        
    async def is_name_available(self, name: WorkspaceName) -> bool:
        """Check if workspace name is available."""
        await self._check_error_condition("is_name_available")
        self._increment_call_count("is_name_available")
        await self._apply_call_delay("is_name_available")
        
        exists = await self.exists(name)
        available = not exists
        self._log_event("is_name_available", self._get_entity_type_name(), 
                       str(name.value), available=available)
        return available
        
    async def is_path_available(self, path: WorkspacePath) -> bool:
        """Check if workspace path is available."""
        await self._check_error_condition("is_path_available")
        self._increment_call_count("is_path_available")
        await self._apply_call_delay("is_path_available")
        
        workspace = await self.find_by_path(path)
        available = workspace is None
        self._log_event("is_path_available", self._get_entity_type_name(), 
                       path=str(path.value), available=available)
        return available
        
    async def set_active_workspace(self, workspace: Workspace) -> None:
        """Set the active workspace."""
        await self._check_error_condition("set_active_workspace")
        self._increment_call_count("set_active_workspace")
        await self._apply_call_delay("set_active_workspace")
        
        # Verify workspace exists
        if not await self.exists(workspace.name):
            raise MockEntityNotFoundError(self._get_entity_type_name(), str(workspace.name.value))
            
        self._active_workspace = str(workspace.name.value)
        self._log_event("set_active_workspace", self._get_entity_type_name(), 
                       self._active_workspace)
        
    async def update_last_accessed(self, workspace: Workspace) -> None:
        """Update workspace last access time."""
        await self._check_error_condition("update_last_accessed")
        self._increment_call_count("update_last_accessed")
        await self._apply_call_delay("update_last_accessed")
        
        existing_workspace = await self.find_by_name(workspace.name)
        if not existing_workspace:
            raise MockEntityNotFoundError(self._get_entity_type_name(), str(workspace.name.value))
            
        # Create updated workspace with new last access time
        updated_workspace = existing_workspace.with_last_accessed(datetime.now())
        await self.save(updated_workspace)
        
        self._log_event("update_last_accessed", self._get_entity_type_name(), 
                       str(workspace.name.value))
        
    async def get_workspace_stats(self, workspace: Workspace) -> Dict[str, Any]:
        """Get workspace usage statistics."""
        await self._check_error_condition("get_workspace_stats")
        self._increment_call_count("get_workspace_stats")
        await self._apply_call_delay("get_workspace_stats")
        
        # Mock statistics - would normally query related repositories
        stats = {
            "created_at": workspace.created_at,
            "last_accessed_at": workspace.last_accessed_at,
            "total_pipelines": self._behavior.return_values.get("total_pipelines", 0),
            "total_runs": self._behavior.return_values.get("total_runs", 0),
            "total_templates": self._behavior.return_values.get("total_templates", 0),
            "storage_size_bytes": self._behavior.return_values.get("storage_size_bytes", 1024000)
        }
        
        self._log_event("get_workspace_stats", self._get_entity_type_name(), 
                       str(workspace.name.value), **stats)
        return stats
        
    async def validate_workspace_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace integrity and consistency."""
        await self._check_error_condition("validate_workspace_integrity")
        self._increment_call_count("validate_workspace_integrity")
        await self._apply_call_delay("validate_workspace_integrity")
        
        # Mock validation - return configured errors or empty list
        errors = self._behavior.return_values.get("validate_workspace_integrity", [])
        self._log_event("validate_workspace_integrity", self._get_entity_type_name(), 
                       str(workspace.name.value), error_count=len(errors))
        return errors
        
    async def backup_workspace(
        self, 
        workspace: Workspace, 
        backup_path: WorkspacePath
    ) -> bool:
        """Create a backup of workspace data."""
        await self._check_error_condition("backup_workspace")
        self._increment_call_count("backup_workspace")
        await self._apply_call_delay("backup_workspace")
        
        # Mock backup operation
        success = self._behavior.return_values.get("backup_workspace", True)
        self._log_event("backup_workspace", self._get_entity_type_name(), 
                       str(workspace.name.value), backup_path=str(backup_path.value), success=success)
        return success
        
    async def restore_workspace(
        self, 
        backup_path: WorkspacePath, 
        target_name: WorkspaceName
    ) -> Workspace:
        """Restore workspace from backup."""
        await self._check_error_condition("restore_workspace")
        self._increment_call_count("restore_workspace")
        await self._apply_call_delay("restore_workspace")
        
        # Check if target name already exists
        if await self.exists(target_name):
            raise MockEntityAlreadyExistsError(self._get_entity_type_name(), str(target_name.value))
            
        # Create restored workspace (mock implementation)
        from writeit.domains.workspace.entities.workspace import Workspace
        restored_workspace = Workspace(
            name=target_name,
            path=WorkspacePath(f"/mock/restored/{target_name.value}"),
            created_at=datetime.now(),
            description=f"Restored from {backup_path.value}",
            tags=["restored"]
        )
        
        await self.save(restored_workspace)
        
        self._log_event("restore_workspace", self._get_entity_type_name(), 
                       str(target_name.value), backup_path=str(backup_path.value))
        return restored_workspace
        
    async def cleanup_inactive_workspaces(
        self, 
        inactive_since: datetime
    ) -> List[WorkspaceName]:
        """Clean up workspaces inactive since a given date."""
        await self._check_error_condition("cleanup_inactive_workspaces")
        self._increment_call_count("cleanup_inactive_workspaces")
        await self._apply_call_delay("cleanup_inactive_workspaces")
        
        workspaces = self._get_all_entities(workspace="global")
        inactive_workspaces = [
            w for w in workspaces 
            if w.last_accessed_at and w.last_accessed_at < inactive_since
        ]
        
        deleted_names = []
        for workspace in inactive_workspaces:
            await self.delete(workspace)
            deleted_names.append(workspace.name)
            
        self._log_event("cleanup_inactive_workspaces", self._get_entity_type_name(), 
                       deleted_count=len(deleted_names), inactive_since=inactive_since)
        return deleted_names