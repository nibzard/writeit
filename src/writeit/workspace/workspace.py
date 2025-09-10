# ABOUTME: Core Workspace class for managing centralized ~/.writeit directory
# ABOUTME: Handles workspace creation, configuration, and file operations
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import yaml

class WorkspaceConfig(BaseModel):
    """Configuration for a WriteIt workspace."""
    name: str = Field(description="Workspace name")
    created_at: str = Field(description="Workspace creation timestamp")
    default_pipeline: Optional[str] = Field(None, description="Default pipeline template")
    llm_providers: Dict[str, str] = Field(default_factory=dict, description="LLM provider configurations")

class GlobalConfig(BaseModel):
    """Global WriteIt configuration stored in ~/.writeit/config.yaml"""
    active_workspace: str = Field(default="default", description="Currently active workspace")
    workspaces: List[str] = Field(default_factory=list, description="List of available workspaces") 
    writeit_version: str = Field(default="0.1.0", description="WriteIt version that created this config")

class Workspace:
    """Manages WriteIt's centralized home directory structure."""
    
    def __init__(self, home_dir: Optional[Path] = None):
        """Initialize workspace manager.
        
        Args:
            home_dir: Override for WriteIt home directory (defaults to ~/.writeit)
        """
        self.home_dir = home_dir or Path.home() / ".writeit"
        self._global_config: Optional[GlobalConfig] = None
    
    @property
    def config_file(self) -> Path:
        """Path to global config file."""
        return self.home_dir / "config.yaml"
    
    @property  
    def templates_dir(self) -> Path:
        """Path to global pipeline templates directory."""
        return self.home_dir / "templates"
    
    @property
    def styles_dir(self) -> Path:
        """Path to global style primers directory."""
        return self.home_dir / "styles"
    
    @property
    def workspaces_dir(self) -> Path:
        """Path to workspaces directory."""
        return self.home_dir / "workspaces"
    
    @property
    def cache_dir(self) -> Path:
        """Path to cache directory."""
        return self.home_dir / "cache"
    
    def initialize(self) -> None:
        """Initialize the ~/.writeit directory structure."""
        # Create main directories
        self.home_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
        self.styles_dir.mkdir(exist_ok=True)
        self.workspaces_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Create default workspace if it doesn't exist
        if not self.workspace_exists("default"):
            self.create_workspace("default")
        
        # Initialize global config
        if not self.config_file.exists():
            config = GlobalConfig()
            self._save_global_config(config)
    
    def create_workspace(self, name: str) -> Path:
        """Create a new workspace.
        
        Args:
            name: Workspace name
            
        Returns:
            Path to the created workspace directory
            
        Raises:
            ValueError: If workspace already exists
        """
        if self.workspace_exists(name):
            raise ValueError(f"Workspace '{name}' already exists")
        
        workspace_dir = self.workspaces_dir / name
        workspace_dir.mkdir(parents=True)
        
        # Create workspace subdirectories
        (workspace_dir / "pipelines").mkdir()
        (workspace_dir / "articles").mkdir()
        (workspace_dir / "templates").mkdir()
        (workspace_dir / "styles").mkdir()
        
        # Create workspace config
        import datetime
        config = WorkspaceConfig(
            name=name,
            created_at=datetime.datetime.now().isoformat()
        )
        config_file = workspace_dir / "workspace.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False)
        
        # Update global config to include new workspace
        global_config = self.load_global_config()
        if name not in global_config.workspaces:
            global_config.workspaces.append(name)
            self._save_global_config(global_config)
        
        return workspace_dir
    
    def workspace_exists(self, name: str) -> bool:
        """Check if a workspace exists.
        
        Args:
            name: Workspace name
            
        Returns:
            True if workspace exists
        """
        return (self.workspaces_dir / name).exists()
    
    def get_workspace_path(self, name: Optional[str] = None) -> Path:
        """Get path to a workspace.
        
        Args:
            name: Workspace name (defaults to active workspace)
            
        Returns:
            Path to workspace directory
            
        Raises:
            ValueError: If workspace doesn't exist
        """
        if name is None:
            name = self.get_active_workspace()
        
        if not self.workspace_exists(name):
            raise ValueError(f"Workspace '{name}' does not exist")
        
        return self.workspaces_dir / name
    
    def list_workspaces(self) -> List[str]:
        """List all available workspaces.
        
        Returns:
            List of workspace names
        """
        if not self.workspaces_dir.exists():
            return []
        
        return [d.name for d in self.workspaces_dir.iterdir() if d.is_dir()]
    
    def get_active_workspace(self) -> str:
        """Get the name of the active workspace.
        
        Returns:
            Active workspace name
        """
        config = self.load_global_config()
        return config.active_workspace
    
    def set_active_workspace(self, name: str) -> None:
        """Set the active workspace.
        
        Args:
            name: Workspace name
            
        Raises:
            ValueError: If workspace doesn't exist
        """
        if not self.workspace_exists(name):
            raise ValueError(f"Workspace '{name}' does not exist")
        
        config = self.load_global_config()
        config.active_workspace = name
        self._save_global_config(config)
    
    def remove_workspace(self, name: str) -> None:
        """Remove a workspace.
        
        Args:
            name: Workspace name
            
        Raises:
            ValueError: If workspace doesn't exist or is the active workspace
        """
        if not self.workspace_exists(name):
            raise ValueError(f"Workspace '{name}' does not exist")
        
        if name == self.get_active_workspace():
            raise ValueError("Cannot remove active workspace. Switch to another workspace first.")
        
        # Remove directory
        import shutil
        workspace_dir = self.workspaces_dir / name
        shutil.rmtree(workspace_dir)
        
        # Update global config
        config = self.load_global_config()
        if name in config.workspaces:
            config.workspaces.remove(name)
            self._save_global_config(config)
    
    def load_global_config(self) -> GlobalConfig:
        """Load the global configuration.
        
        Returns:
            Global configuration object
        """
        if self._global_config is not None:
            return self._global_config
        
        if not self.config_file.exists():
            self._global_config = GlobalConfig()
            return self._global_config
        
        with open(self.config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        self._global_config = GlobalConfig(**data)
        return self._global_config
    
    def _save_global_config(self, config: GlobalConfig) -> None:
        """Save global configuration to disk.
        
        Args:
            config: Configuration to save
        """
        self._global_config = config
        with open(self.config_file, 'w') as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False)
    
    def load_workspace_config(self, name: Optional[str] = None) -> WorkspaceConfig:
        """Load workspace configuration.
        
        Args:
            name: Workspace name (defaults to active workspace)
            
        Returns:
            Workspace configuration
        """
        workspace_dir = self.get_workspace_path(name)
        config_file = workspace_dir / "workspace.yaml"
        
        if not config_file.exists():
            raise ValueError(f"Workspace config not found: {config_file}")
        
        with open(config_file, 'r') as f:
            data = yaml.safe_load(f)
        
        return WorkspaceConfig(**data)
    
    def get_workspace_templates_dir(self, name: Optional[str] = None) -> Path:
        """Get path to workspace-specific templates directory.
        
        Args:
            name: Workspace name (defaults to active workspace)
            
        Returns:
            Path to workspace templates directory
        """
        workspace_path = self.get_workspace_path(name)
        return workspace_path / "templates"
    
    def get_workspace_styles_dir(self, name: Optional[str] = None) -> Path:
        """Get path to workspace-specific styles directory.
        
        Args:
            name: Workspace name (defaults to active workspace)
            
        Returns:
            Path to workspace styles directory
        """
        workspace_path = self.get_workspace_path(name)
        return workspace_path / "styles"