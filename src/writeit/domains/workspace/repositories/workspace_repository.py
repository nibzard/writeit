"""Workspace repository interface.

Provides data access operations for workspace management including
CRUD operations, workspace lifecycle, and metadata management.
"""

from abc import abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any

from ....shared.repository import Repository, Specification
from ..entities.workspace import Workspace
from ..value_objects.workspace_name import WorkspaceName
from ..value_objects.workspace_path import WorkspacePath


class WorkspaceRepository(Repository[Workspace]):
    """Repository for workspace persistence and retrieval.
    
    Handles CRUD operations for workspaces with lifecycle management,
    metadata tracking, and isolation verification.
    """
    
    @abstractmethod
    async def find_by_name(self, name: WorkspaceName) -> Optional[Workspace]:
        """Find workspace by name.
        
        Args:
            name: Workspace name to search for
            
        Returns:
            Workspace if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_path(self, path: WorkspacePath) -> Optional[Workspace]:
        """Find workspace by filesystem path.
        
        Args:
            path: Workspace path to search for
            
        Returns:
            Workspace if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_active_workspace(self) -> Optional[Workspace]:
        """Find the currently active workspace.
        
        Returns:
            Active workspace if set, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_recent_workspaces(self, limit: int = 5) -> List[Workspace]:
        """Find recently used workspaces.
        
        Args:
            limit: Maximum number of workspaces to return
            
        Returns:
            List of recent workspaces, ordered by last access time desc
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_workspaces_by_tag(self, tag: str) -> List[Workspace]:
        """Find workspaces with a specific tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of workspaces with the tag
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def is_name_available(self, name: WorkspaceName) -> bool:
        """Check if workspace name is available.
        
        Args:
            name: Workspace name to check
            
        Returns:
            True if name is available, False if taken
            
        Raises:
            RepositoryError: If check operation fails
        """
        pass
    
    @abstractmethod
    async def is_path_available(self, path: WorkspacePath) -> bool:
        """Check if workspace path is available.
        
        Args:
            path: Workspace path to check
            
        Returns:
            True if path is available, False if taken
            
        Raises:
            RepositoryError: If check operation fails
        """
        pass
    
    @abstractmethod
    async def set_active_workspace(self, workspace: Workspace) -> None:
        """Set the active workspace.
        
        Args:
            workspace: Workspace to activate
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If activation fails
        """
        pass
    
    @abstractmethod
    async def update_last_accessed(self, workspace: Workspace) -> None:
        """Update workspace last access time.
        
        Args:
            workspace: Workspace to update
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If update operation fails
        """
        pass
    
    @abstractmethod
    async def get_workspace_stats(self, workspace: Workspace) -> Dict[str, Any]:
        """Get workspace usage statistics.
        
        Args:
            workspace: Workspace to get stats for
            
        Returns:
            Dictionary with workspace statistics:
            - created_at: Workspace creation time
            - last_accessed_at: Last access time
            - total_pipelines: Number of pipelines
            - total_runs: Number of pipeline runs
            - total_templates: Number of templates
            - storage_size_bytes: Storage usage in bytes
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If stats calculation fails
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass


# Specifications for workspace queries

class ByNameSpecification(Specification[Workspace]):
    """Specification for filtering workspaces by name."""
    
    def __init__(self, name: WorkspaceName):
        self.name = name
    
    def is_satisfied_by(self, workspace: Workspace) -> bool:
        return workspace.name == self.name


class ByTagSpecification(Specification[Workspace]):
    """Specification for filtering workspaces by tag."""
    
    def __init__(self, tag: str):
        self.tag = tag
    
    def is_satisfied_by(self, workspace: Workspace) -> bool:
        return self.tag in workspace.tags


class ActiveWorkspaceSpecification(Specification[Workspace]):
    """Specification for filtering active workspace."""
    
    def is_satisfied_by(self, workspace: Workspace) -> bool:
        return workspace.is_active


class RecentlyAccessedSpecification(Specification[Workspace]):
    """Specification for filtering recently accessed workspaces."""
    
    def __init__(self, since: datetime):
        self.since = since
    
    def is_satisfied_by(self, workspace: Workspace) -> bool:
        return (
            workspace.last_accessed_at is not None and
            workspace.last_accessed_at >= self.since
        )
