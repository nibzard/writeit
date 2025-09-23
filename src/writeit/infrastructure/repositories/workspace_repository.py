"""File system implementation of WorkspaceRepository.

Provides workspace management using file system operations
with directory structure and metadata tracking.
"""

import asyncio
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from ...domains.workspace.repositories.workspace_repository import WorkspaceRepository
from ...domains.workspace.entities.workspace import Workspace
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...domains.workspace.value_objects.workspace_path import WorkspacePath
from ...shared.repository import RepositoryError
from ..persistence.file_storage import FileSystemStorage
from ..base.exceptions import StorageError, ValidationError


class FileSystemWorkspaceRepository(WorkspaceRepository):
    """File system-based implementation of WorkspaceRepository.
    
    Manages workspaces as directory structures with metadata files
    and provides lifecycle management and isolation verification.
    """
    
    def __init__(self, storage: FileSystemStorage, base_path: Path):
        """Initialize repository.
        
        Args:
            storage: File system storage instance
            base_path: Base path for workspace directories
        """
        super().__init__()
        self.storage = storage
        self.base_path = base_path
        self._metadata_file = ".workspace.json"
    
    async def save(self, workspace: Workspace) -> None:
        """Save a workspace.
        
        Args:
            workspace: Workspace to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        try:
            # Create workspace directory
            workspace_path = self.base_path / workspace.name.value
            await self.storage.create_directory(workspace_path)
            
            # Create metadata file
            metadata = self._workspace_to_metadata(workspace)
            metadata_path = workspace_path / self._metadata_file
            
            await self.storage.write_json(metadata_path, metadata)
            
            # Create standard subdirectories
            await self._create_workspace_structure(workspace_path)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to save workspace {workspace.name}: {e}") from e
    
    async def find_by_id(self, workspace_id: str) -> Optional[Workspace]:
        """Find workspace by ID.
        
        Args:
            workspace_id: Workspace ID to search for
            
        Returns:
            Workspace if found, None otherwise
        """
        try:
            # List all workspaces and find by ID
            all_workspaces = await self.find_all()
            
            for workspace in all_workspaces:
                if str(workspace.id) == workspace_id:
                    return workspace
            
            return None
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find workspace by ID {workspace_id}: {e}") from e
    
    async def find_by_name(self, name: WorkspaceName) -> Optional[Workspace]:
        """Find workspace by name.
        
        Args:
            name: Workspace name to search for
            
        Returns:
            Workspace if found, None otherwise
        """
        try:
            workspace_path = self.base_path / name.value
            metadata_path = workspace_path / self._metadata_file
            
            if not await self.storage.file_exists(metadata_path):
                return None
            
            metadata = await self.storage.read_json(metadata_path)
            return self._metadata_to_workspace(metadata, workspace_path)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find workspace by name {name}: {e}") from e
    
    async def find_by_path(self, path: WorkspacePath) -> Optional[Workspace]:
        """Find workspace by filesystem path.
        
        Args:
            path: Workspace path to search for
            
        Returns:
            Workspace if found, None otherwise
        """
        try:
            metadata_path = path.path / self._metadata_file
            
            if not await self.storage.file_exists(metadata_path):
                return None
            
            metadata = await self.storage.read_json(metadata_path)
            return self._metadata_to_workspace(metadata, path.path)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find workspace by path {path}: {e}") from e
    
    async def find_active_workspace(self) -> Optional[Workspace]:
        """Find the currently active workspace.
        
        Returns:
            Active workspace if found, None otherwise
        """
        try:
            # Look for active workspace marker file
            active_marker_path = self.base_path / ".active_workspace"
            
            if not await self.storage.file_exists(active_marker_path):
                return None
            
            active_name = (await self.storage.read_file(active_marker_path)).strip()
            
            if not active_name:
                return None
            
            return await self.find_by_name(WorkspaceName(active_name))
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find active workspace: {e}") from e
    
    async def set_active_workspace(self, workspace: Workspace) -> None:
        """Set the active workspace.
        
        Args:
            workspace: Workspace to set as active
        """
        try:
            active_marker_path = self.base_path / ".active_workspace"
            await self.storage.write_file(active_marker_path, workspace.name.value)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to set active workspace {workspace.name}: {e}") from e
    
    async def is_name_available(self, name: WorkspaceName) -> bool:
        """Check if workspace name is available.
        
        Args:
            name: Workspace name to check
            
        Returns:
            True if name is available, False if taken
        """
        try:
            existing = await self.find_by_name(name)
            return existing is None
        except StorageError as e:
            raise RepositoryError(f"Failed to check name availability for {name}: {e}") from e
    
    async def get_workspace_size(self, workspace: Workspace) -> int:
        """Get total size of workspace in bytes.
        
        Args:
            workspace: Workspace to analyze
            
        Returns:
            Total size in bytes
        """
        try:
            workspace_path = self.base_path / workspace.name.value
            
            # Calculate directory size (simplified approach)
            total_size = 0
            files = await self.storage.list_files(workspace_path, "**/*", recursive=True)
            
            for file_path in files:
                metadata = self.storage.get_file_metadata(file_path)
                if metadata:
                    total_size += metadata.size
            
            return total_size
            
        except StorageError as e:
            raise RepositoryError(f"Failed to get workspace size for {workspace.name}: {e}") from e
    
    async def validate_workspace_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace integrity and structure.
        
        Args:
            workspace: Workspace to validate
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        try:
            workspace_path = self.base_path / workspace.name.value
            
            # Check if workspace directory exists
            if not await self.storage.file_exists(workspace_path):
                errors.append(f"Workspace directory does not exist: {workspace_path}")
                return errors
            
            # Check metadata file
            metadata_path = workspace_path / self._metadata_file
            if not await self.storage.file_exists(metadata_path):
                errors.append("Workspace metadata file is missing")
            else:
                try:
                    await self.storage.read_json(metadata_path)
                except ValidationError:
                    errors.append("Workspace metadata file is corrupted")
            
            # Check standard directories
            expected_dirs = ["templates", "pipelines", "content", "cache"]
            for dir_name in expected_dirs:
                dir_path = workspace_path / dir_name
                if not await self.storage.file_exists(dir_path):
                    errors.append(f"Missing standard directory: {dir_name}")
            
            return errors
            
        except StorageError as e:
            errors.append(f"Validation error: {e}")
            return errors
    
    async def archive_workspace(self, workspace: Workspace) -> Path:
        """Archive a workspace for backup.
        
        Args:
            workspace: Workspace to archive
            
        Returns:
            Path to archive file
        """
        try:
            # Create archive directory if it doesn't exist
            archive_dir = self.base_path.parent / "archives"
            await self.storage.create_directory(archive_dir)
            
            # Generate archive filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"{workspace.name.value}_{timestamp}.tar.gz"
            archive_path = archive_dir / archive_name
            
            # For now, we'll just copy the directory
            # In production, you'd want to create a proper archive
            workspace_path = self.base_path / workspace.name.value
            
            # Simple copy approach (in production, use tar/zip)
            archive_workspace_path = archive_dir / f"{workspace.name.value}_{timestamp}"
            await self.storage.create_directory(archive_workspace_path)
            
            # Copy all files (simplified)
            files = await self.storage.list_files(workspace_path, "**/*", recursive=True)
            for file_path in files:
                relative_path = file_path
                dest_path = archive_workspace_path / relative_path
                await self.storage.copy_file(workspace_path / file_path, dest_path)
            
            return archive_workspace_path
            
        except StorageError as e:
            raise RepositoryError(f"Failed to archive workspace {workspace.name}: {e}") from e
    
    async def find_all(self) -> List[Workspace]:
        """Find all workspaces.
        
        Returns:
            List of all workspaces
        """
        try:
            workspaces = []
            
            # List all directories in base path
            directories = await self.storage.list_files(self.base_path, "*/", recursive=False)
            
            for dir_path in directories:
                metadata_path = dir_path / self._metadata_file
                
                if await self.storage.file_exists(metadata_path):
                    try:
                        metadata = await self.storage.read_json(metadata_path)
                        workspace = self._metadata_to_workspace(metadata, dir_path)
                        workspaces.append(workspace)
                    except Exception:
                        # Skip corrupted workspaces
                        continue
            
            return workspaces
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find all workspaces: {e}") from e
    
    async def delete(self, workspace_id: str) -> bool:
        """Delete a workspace.
        
        Args:
            workspace_id: ID of workspace to delete
            
        Returns:
            True if workspace was deleted, False if not found
        """
        try:
            workspace = await self.find_by_id(workspace_id)
            if not workspace:
                return False
            
            # Remove workspace directory and all contents
            workspace_path = self.base_path / workspace.name.value
            
            # In a real implementation, you'd use recursive directory deletion
            # For now, we'll just delete the metadata file as a marker
            metadata_path = workspace_path / self._metadata_file
            return await self.storage.delete_file(metadata_path)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to delete workspace {workspace_id}: {e}") from e
    
    async def count(self) -> int:
        """Count workspaces.
        
        Returns:
            Number of workspaces
        """
        try:
            workspaces = await self.find_all()
            return len(workspaces)
        except StorageError as e:
            raise RepositoryError(f"Failed to count workspaces: {e}") from e
    
    def _workspace_to_metadata(self, workspace: Workspace) -> Dict[str, Any]:
        """Convert workspace to metadata dictionary.
        
        Args:
            workspace: Workspace to convert
            
        Returns:
            Metadata dictionary
        """
        return {
            "id": str(workspace.id),
            "name": workspace.name.value,
            "description": workspace.description,
            "created_at": workspace.created_at.isoformat() if workspace.created_at else None,
            "updated_at": workspace.updated_at.isoformat() if workspace.updated_at else None,
            "is_active": workspace.is_active,
            "metadata_version": "1.0"
        }
    
    def _metadata_to_workspace(self, metadata: Dict[str, Any], path: Path) -> Workspace:
        """Convert metadata dictionary to workspace.
        
        Args:
            metadata: Metadata dictionary
            path: Workspace path
            
        Returns:
            Workspace instance
        """
        from uuid import UUID
        
        created_at = None
        if metadata.get("created_at"):
            created_at = datetime.fromisoformat(metadata["created_at"])
        
        updated_at = None
        if metadata.get("updated_at"):
            updated_at = datetime.fromisoformat(metadata["updated_at"])
        
        return Workspace(
            id=UUID(metadata["id"]),
            name=WorkspaceName(metadata["name"]),
            path=WorkspacePath(path),
            description=metadata.get("description", ""),
            created_at=created_at,
            updated_at=updated_at,
            is_active=metadata.get("is_active", False)
        )
    
    async def _create_workspace_structure(self, workspace_path: Path) -> None:
        """Create standard workspace directory structure.
        
        Args:
            workspace_path: Path to workspace directory
        """
        standard_dirs = [
            "templates",      # Pipeline templates
            "pipelines",      # Pipeline definitions
            "content",        # Generated content
            "cache",          # LLM cache
            "config",         # Configuration files
            "logs"            # Log files
        ]
        
        for dir_name in standard_dirs:
            dir_path = workspace_path / dir_name
            await self.storage.create_directory(dir_path)
