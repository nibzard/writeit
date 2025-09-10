# ABOUTME: Hierarchical configuration loader for WriteIt
# ABOUTME: Supports global → workspace → local config loading with environment overrides
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class ConfigLoader:
    """Hierarchical configuration loader for WriteIt settings."""
    
    def __init__(self, workspace_manager=None):
        """Initialize config loader.
        
        Args:
            workspace_manager: Workspace instance for accessing paths
        """
        self.workspace_manager = workspace_manager
        self._cache: Dict[str, Any] = {}
    
    def load_config(self, workspace: Optional[str] = None, local_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Load hierarchical configuration.
        
        Loads configuration in this order (later overrides earlier):
        1. Global config (~/.writeit/config.yaml)
        2. Workspace config (~/.writeit/workspaces/{workspace}/workspace.yaml)
        3. Local config (.writeit/config.yaml in current directory or local_dir)
        4. Environment variables (WRITEIT_*)
        
        Args:
            workspace: Workspace name (defaults to active workspace)
            local_dir: Directory to look for local config (defaults to current dir)
            
        Returns:
            Merged configuration dictionary
        """
        cache_key = f"{workspace}:{local_dir}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        config = {}
        
        # 1. Load global config
        if self.workspace_manager:
            global_config = self.workspace_manager.load_global_config()
            config.update(global_config.model_dump())
        
        # 2. Load workspace config
        if self.workspace_manager and workspace:
            try:
                workspace_config = self.workspace_manager.load_workspace_config(workspace)
                config.update(workspace_config.model_dump())
            except ValueError:
                pass  # Workspace doesn't exist or no config
        
        # 3. Load local config
        local_config = self._load_local_config(local_dir)
        if local_config:
            config.update(local_config)
        
        # 4. Apply environment variable overrides
        env_config = self._load_env_config()
        config.update(env_config)
        
        self._cache[cache_key] = config
        return config
    
    def get_setting(self, key: str, default: Any = None, workspace: Optional[str] = None, local_dir: Optional[Path] = None) -> Any:
        """Get a specific configuration setting.
        
        Args:
            key: Configuration key (supports dot notation like 'llm.providers.openai')
            default: Default value if key not found
            workspace: Workspace name (defaults to active workspace)
            local_dir: Directory to look for local config
            
        Returns:
            Configuration value or default
        """
        config = self.load_config(workspace, local_dir)
        return self._get_nested_value(config, key, default)
    
    def _load_local_config(self, local_dir: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """Load local .writeit/config.yaml file.
        
        Args:
            local_dir: Directory to look in (defaults to current directory)
            
        Returns:
            Local configuration or None if not found
        """
        if local_dir is None:
            local_dir = Path.cwd()
        
        config_file = local_dir / ".writeit" / "config.yaml"
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except yaml.YAMLError:
            return None
    
    def _load_env_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables.
        
        Reads all WRITEIT_* environment variables and converts them to config.
        For example:
        - WRITEIT_HOME -> {"home": "/path/to/home"}  
        - WRITEIT_WORKSPACE -> {"workspace": "name"}
        - WRITEIT_LLM_PROVIDER -> {"llm": {"provider": "openai"}}
        
        Returns:
            Environment configuration dictionary
        """
        config = {}
        
        for key, value in os.environ.items():
            if not key.startswith("WRITEIT_"):
                continue
            
            # Remove WRITEIT_ prefix and convert to lowercase
            config_key = key[8:].lower()
            
            # Handle nested keys (WRITEIT_LLM_PROVIDER -> llm.provider)
            if "_" in config_key:
                self._set_nested_value(config, config_key.replace("_", "."), value)
            else:
                config[config_key] = value
        
        return config
    
    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get value from nested dictionary using dot notation.
        
        Args:
            data: Dictionary to search
            key: Dot-separated key (e.g., 'llm.providers.openai')
            default: Default value if not found
            
        Returns:
            Value or default
        """
        keys = key.split(".")
        current = data
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any) -> None:
        """Set value in nested dictionary using dot notation.
        
        Args:
            data: Dictionary to modify
            key: Dot-separated key (e.g., 'llm.providers.openai')
            value: Value to set
        """
        keys = key.split(".")
        current = data
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def clear_cache(self) -> None:
        """Clear the configuration cache."""
        self._cache.clear()


def get_writeit_home() -> Path:
    """Get WriteIt home directory from environment or default.
    
    Returns:
        Path to WriteIt home directory
    """
    home_env = os.environ.get("WRITEIT_HOME")
    if home_env:
        return Path(home_env)
    return Path.home() / ".writeit"


def get_active_workspace() -> str:
    """Get active workspace name from environment or config.
    
    Returns:
        Active workspace name
    """
    # Check environment first
    workspace_env = os.environ.get("WRITEIT_WORKSPACE")
    if workspace_env:
        return workspace_env
    
    # Fall back to global config
    from .workspace import Workspace
    workspace_manager = Workspace()
    if workspace_manager.config_file.exists():
        return workspace_manager.get_active_workspace()
    
    return "default"