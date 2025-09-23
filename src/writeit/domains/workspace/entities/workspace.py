"""Workspace entity.

Domain entity representing a workspace that provides isolation for WriteIt operations.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Dict, Any, Optional, Self

from ..value_objects.workspace_name import WorkspaceName
from ..value_objects.workspace_path import WorkspacePath
from .workspace_configuration import WorkspaceConfiguration


@dataclass
class Workspace:
    """Domain entity representing a workspace.
    
    A workspace is an isolated environment for WriteIt operations,
    providing:
    - Configuration isolation
    - Template isolation
    - Pipeline execution isolation
    - Storage isolation
    
    Examples:
        workspace = Workspace.create(
            name=WorkspaceName.from_user_input("my-project"),
            root_path=WorkspacePath.home_directory() / "workspaces" / "my-project"
        )
        
        workspace.activate()
        workspace.configure("default_model", "gpt-4o-mini")
    """
    
    name: WorkspaceName
    root_path: WorkspacePath
    configuration: WorkspaceConfiguration
    is_active: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_accessed: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate workspace entity."""
        if not isinstance(self.name, WorkspaceName):
            raise TypeError("Workspace name must be a WorkspaceName")
            
        if not isinstance(self.root_path, WorkspacePath):
            raise TypeError("Workspace root path must be a WorkspacePath")
            
        if not isinstance(self.configuration, WorkspaceConfiguration):
            raise TypeError("Workspace configuration must be a WorkspaceConfiguration")
    
    def activate(self) -> Self:
        """Activate this workspace.
        
        Returns:
            Updated workspace with activation timestamp
        """
        return replace(
            self,
            is_active=True,
            last_accessed=datetime.now(),
            updated_at=datetime.now()
        )
    
    def deactivate(self) -> Self:
        """Deactivate this workspace.
        
        Returns:
            Updated workspace
        """
        return replace(
            self,
            is_active=False,
            updated_at=datetime.now()
        )
    
    def update_configuration(self, configuration: WorkspaceConfiguration) -> Self:
        """Update workspace configuration.
        
        Args:
            configuration: New configuration
            
        Returns:
            Updated workspace
        """
        return replace(
            self,
            configuration=configuration,
            updated_at=datetime.now()
        )
    
    def set_metadata(self, key: str, value: Any) -> Self:
        """Set metadata value.
        
        Args:
            key: Metadata key
            value: Metadata value
            
        Returns:
            Updated workspace
        """
        new_metadata = self.metadata.copy()
        new_metadata[key] = value
        
        return replace(
            self,
            metadata=new_metadata,
            updated_at=datetime.now()
        )
    
    def remove_metadata(self, key: str) -> Self:
        """Remove metadata value.
        
        Args:
            key: Metadata key to remove
            
        Returns:
            Updated workspace
        """
        if key not in self.metadata:
            return self
            
        new_metadata = self.metadata.copy()
        del new_metadata[key]
        
        return replace(
            self,
            metadata=new_metadata,
            updated_at=datetime.now()
        )
    
    def get_templates_path(self) -> WorkspacePath:
        """Get the templates directory path."""
        return self.root_path.join("templates")
    
    def get_pipelines_path(self) -> WorkspacePath:
        """Get the pipelines directory path."""
        return self.root_path.join("pipelines")
    
    def get_cache_path(self) -> WorkspacePath:
        """Get the cache directory path."""
        return self.root_path.join("cache")
    
    def get_config_path(self) -> WorkspacePath:
        """Get the configuration file path."""
        return self.root_path.join("config.yaml")
    
    def get_storage_path(self) -> WorkspacePath:
        """Get the storage directory path."""
        return self.root_path.join("storage")
    
    def ensure_directory_structure(self) -> None:
        """Ensure workspace directory structure exists."""
        directories = [
            self.root_path,
            self.get_templates_path(),
            self.get_pipelines_path(),
            self.get_cache_path(),
            self.get_storage_path()
        ]
        
        for directory in directories:
            directory.create_directories(exist_ok=True)
    
    def is_initialized(self) -> bool:
        """Check if workspace is properly initialized."""
        required_paths = [
            self.root_path,
            self.get_templates_path(),
            self.get_storage_path()
        ]
        
        return all(path.exists() and path.is_directory() for path in required_paths)
    
    def get_size_on_disk(self) -> int:
        """Get approximate workspace size in bytes."""
        if not self.root_path.exists():
            return 0
            
        total_size = 0
        try:
            for file_path in self.root_path.value.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except (OSError, PermissionError):
            # Return partial size if we can't access some files
            pass
            
        return total_size
    
    @classmethod
    def create(
        cls,
        name: WorkspaceName,
        root_path: WorkspacePath,
        configuration: Optional[WorkspaceConfiguration] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Self:
        """Create a new workspace.
        
        Args:
            name: Workspace name
            root_path: Root directory path
            configuration: Initial configuration (uses default if None)
            metadata: Initial metadata
            
        Returns:
            New workspace instance
        """
        if configuration is None:
            configuration = WorkspaceConfiguration.default()
            
        workspace = cls(
            name=name,
            root_path=root_path,
            configuration=configuration,
            is_active=False,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            last_accessed=None,
            metadata=metadata or {}
        )
        
        # Ensure directory structure exists
        workspace.ensure_directory_structure()
        
        return workspace
    
    def __str__(self) -> str:
        """String representation."""
        status = "active" if self.is_active else "inactive"
        return f"Workspace({self.name}, {status})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"Workspace(name={self.name}, path={self.root_path}, "
                f"active={self.is_active}, created={self.created_at})")
