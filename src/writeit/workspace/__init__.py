# ABOUTME: WriteIt workspace management library
# ABOUTME: Handles centralized ~/.writeit directory structure and workspace operations
# DEPRECATED: This module is deprecated. Use writeit.domains.workspace and writeit.application.services instead.

import warnings
from typing import Optional, List
from pathlib import Path

# Import from DDD structure
from writeit.domains.workspace.entities import Workspace as DDDWorkspace, WorkspaceConfiguration as DDDWorkspaceConfig
from writeit.domains.workspace.value_objects import WorkspaceName, WorkspacePath
from writeit.application.services.workspace_application_service import WorkspaceApplicationService
from writeit.infrastructure.factory import InfrastructureFactory

# Issue deprecation warning
warnings.warn(
    "writeit.workspace is deprecated. Use writeit.domains.workspace and writeit.application.services instead.",
    DeprecationWarning,
    stacklevel=2
)

# Create backward compatibility classes
class WorkspaceConfig(DDDWorkspaceConfig):
    """Backward compatibility wrapper for WorkspaceConfig."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class GlobalConfig:
    """Backward compatibility wrapper for global configuration."""
    
    def __init__(self, active_workspace: str = "default", workspaces: Optional[list] = None, writeit_version: str = "0.1.0"):
        self.active_workspace = active_workspace
        self.workspaces = workspaces or []
        self.writeit_version = writeit_version
    
    def model_dump(self) -> dict:
        return {
            "active_workspace": self.active_workspace,
            "workspaces": self.workspaces,
            "writeit_version": self.writeit_version
        }

class Workspace:
    """Backward compatibility wrapper for Workspace."""
    
    def __init__(self, home_dir: Optional[Path] = None):
        self.home_dir = home_dir or Path.home() / ".writeit"
        # Create a simple service instance for backward compatibility
        self._service = self._create_simple_service()
        
    @property
    def config_file(self) -> Path:
        return self.home_dir / "config.yaml"
    
    @property
    def templates_dir(self) -> Path:
        return self.home_dir / "templates"
    
    @property
    def styles_dir(self) -> Path:
        return self.home_dir / "styles"
    
    @property
    def workspaces_dir(self) -> Path:
        return self.home_dir / "workspaces"
    
    @property
    def cache_dir(self) -> Path:
        return self.home_dir / "cache"
    
    def initialize(self) -> None:
        """Initialize the ~/.writeit directory structure."""
        self._service.initialize_writeit_home()
    
    def create_workspace(self, name: str) -> Path:
        """Create a new workspace."""
        workspace_name = WorkspaceName.from_user_input(name)
        workspace = self._service.create_workspace(workspace_name)
        return Path(str(workspace.root_path))
    
    def workspace_exists(self, name: str) -> bool:
        """Check if a workspace exists."""
        try:
            workspace_name = WorkspaceName.from_user_input(name)
            return self._service.get_workspace(workspace_name) is not None
        except:
            return False
    
    def get_workspace_path(self, name: Optional[str] = None) -> Path:
        """Get path to a workspace."""
        if name is None:
            name = self.get_active_workspace()
        
        workspace_name = WorkspaceName.from_user_input(name)
        workspace = self._service.get_workspace(workspace_name)
        if workspace is None:
            raise ValueError(f"Workspace '{name}' does not exist")
        
        return Path(str(workspace.root_path))
    
    def list_workspaces(self) -> List[str]:
        """List all available workspaces."""
        workspaces = self._service.list_workspaces()
        return [str(workspace.name) for workspace in workspaces]
    
    def get_active_workspace(self) -> str:
        """Get the name of the active workspace."""
        active = self._service.get_active_workspace()
        return str(active.name) if active else "default"
    
    def set_active_workspace(self, name: str) -> None:
        """Set the active workspace."""
        workspace_name = WorkspaceName.from_user_input(name)
        self._service.set_active_workspace(workspace_name)
    
    def remove_workspace(self, name: str) -> None:
        """Remove a workspace."""
        workspace_name = WorkspaceName.from_user_input(name)
        self._service.remove_workspace(workspace_name)
    
    def load_global_config(self) -> GlobalConfig:
        """Load the global configuration."""
        config = self._service.get_global_configuration()
        return GlobalConfig(
            active_workspace=config.get("active_workspace", "default"),
            workspaces=config.get("workspaces", []),
            writeit_version=config.get("writeit_version", "0.1.0")
        )
    
    def load_workspace_config(self, name: Optional[str] = None) -> WorkspaceConfig:
        """Load workspace configuration."""
        if name is None:
            name = self.get_active_workspace()
        
        workspace_name = WorkspaceName.from_user_input(name)
        workspace = self._service.get_workspace(workspace_name)
        if workspace is None:
            raise ValueError(f"Workspace '{name}' does not exist")
        
        return WorkspaceConfig(**workspace.configuration.model_dump())
    
    def get_workspace_templates_dir(self, name: Optional[str] = None) -> Path:
        """Get path to workspace-specific templates directory."""
        workspace_path = self.get_workspace_path(name)
        return workspace_path / "templates"
    
    def get_workspace_styles_dir(self, name: Optional[str] = None) -> Path:
        """Get path to workspace-specific styles directory."""
        workspace_path = self.get_workspace_path(name)
        return workspace_path / "styles"
    
    def _create_simple_service(self):
        """Create a simple service instance for backward compatibility."""
        class SimpleWorkspaceService:
            def __init__(self, home_dir):
                self.home_dir = home_dir
                
            def initialize_writeit_home(self):
                """Initialize writeit home directory."""
                self.home_dir.mkdir(exist_ok=True)
                (self.home_dir / "templates").mkdir(exist_ok=True)
                (self.home_dir / "styles").mkdir(exist_ok=True)
                (self.home_dir / "workspaces").mkdir(exist_ok=True)
                (self.home_dir / "cache").mkdir(exist_ok=True)
                
                # Create default workspace
                default_workspace = self.home_dir / "workspaces" / "default"
                default_workspace.mkdir(exist_ok=True, parents=True)
                (default_workspace / "pipelines").mkdir(exist_ok=True)
                (default_workspace / "articles").mkdir(exist_ok=True)
                (default_workspace / "templates").mkdir(exist_ok=True)
                (default_workspace / "styles").mkdir(exist_ok=True)
                
            def create_workspace(self, workspace_name):
                """Create a workspace using legacy implementation."""
                workspace_dir = self.home_dir / "workspaces" / str(workspace_name)
                workspace_dir.mkdir(parents=True, exist_ok=True)
                
                # Create subdirectories
                (workspace_dir / "pipelines").mkdir(exist_ok=True)
                (workspace_dir / "articles").mkdir(exist_ok=True)
                (workspace_dir / "templates").mkdir(exist_ok=True)
                (workspace_dir / "styles").mkdir(exist_ok=True)
                
                # Create workspace config
                import datetime
                config_data = {
                    "name": str(workspace_name),
                    "created_at": datetime.datetime.now().isoformat()
                }
                
                import yaml
                with open(workspace_dir / "workspace.yaml", "w") as f:
                    yaml.dump(config_data, f, default_flow_style=False)
                
                # Create a simple workspace entity
                from writeit.domains.workspace.entities import Workspace
                from writeit.domains.workspace.value_objects import WorkspacePath, WorkspaceName
                from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
                
                return Workspace(
                    name=workspace_name,
                    root_path=WorkspacePath(str(workspace_dir)),
                    configuration=WorkspaceConfiguration()
                )
            
            def get_workspace(self, workspace_name):
                """Get workspace if it exists."""
                workspace_dir = self.home_dir / "workspaces" / str(workspace_name)
                if not workspace_dir.exists():
                    return None
                    
                # Load workspace config
                config_file = workspace_dir / "workspace.yaml"
                if config_file.exists():
                    import yaml
                    with open(config_file, "r") as f:
                        config_data = yaml.safe_load(f) or {}
                else:
                    config_data = {"name": str(workspace_name)}
                
                # Create workspace entity
                from writeit.domains.workspace.entities import Workspace
                from writeit.domains.workspace.value_objects import WorkspacePath, WorkspaceName
                from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
                
                return Workspace(
                    name=workspace_name,
                    root_path=WorkspacePath(str(workspace_dir)),
                    configuration=WorkspaceConfiguration(**config_data)
                )
            
            def list_workspaces(self):
                """List all workspaces."""
                workspaces_dir = self.home_dir / "workspaces"
                if not workspaces_dir.exists():
                    return []
                    
                workspaces = []
                for workspace_dir in workspaces_dir.iterdir():
                    if workspace_dir.is_dir():
                        workspace_name = WorkspaceName.from_user_input(workspace_dir.name)
                        workspace = self.get_workspace(workspace_name)
                        if workspace:
                            workspaces.append(workspace)
                
                return workspaces
            
            def get_active_workspace(self):
                """Get active workspace."""
                # For now, return default workspace
                return self.get_workspace(WorkspaceName.from_user_input("default"))
            
            def set_active_workspace(self, workspace_name):
                """Set active workspace."""
                # Simple implementation - just ensure workspace exists
                if self.get_workspace(workspace_name) is None:
                    raise ValueError(f"Workspace {workspace_name} does not exist")
            
            def remove_workspace(self, workspace_name):
                """Remove workspace."""
                workspace_dir = self.home_dir / "workspaces" / str(workspace_name)
                if workspace_dir.exists():
                    import shutil
                    shutil.rmtree(workspace_dir)
            
            def get_global_configuration(self):
                """Get global configuration."""
                config_file = self.home_dir / "config.yaml"
                if config_file.exists():
                    import yaml
                    with open(config_file, "r") as f:
                        return yaml.safe_load(f) or {}
                return {"active_workspace": "default", "workspaces": ["default"]}
        
        return SimpleWorkspaceService(self.home_dir)

# Import remaining legacy components
from .config import ConfigLoader, get_writeit_home, get_active_workspace
from .migration import WorkspaceMigrator, find_and_migrate_workspaces

__all__ = [
    "Workspace",
    "WorkspaceConfig",
    "GlobalConfig",
    "ConfigLoader",
    "get_writeit_home",
    "get_active_workspace",
    "WorkspaceMigrator",
    "find_and_migrate_workspaces",
]
