"""Workspace configuration repository interface.

Provides data access operations for workspace configuration management
including settings persistence, defaults, and validation.
"""

from abc import abstractmethod
from typing import List, Optional, Dict, Any, Union

from ....shared.repository import Repository, Specification
from ..entities.workspace_configuration import WorkspaceConfiguration
from ..entities.workspace import Workspace
from ..value_objects.workspace_name import WorkspaceName
from ..value_objects.configuration_value import ConfigurationValue


class WorkspaceConfigRepository(Repository[WorkspaceConfiguration]):
    """Repository for workspace configuration persistence and retrieval.
    
    Handles CRUD operations for workspace configurations with
    settings validation, defaults management, and inheritance.
    """
    
    @abstractmethod
    async def find_by_workspace(self, workspace: Workspace) -> Optional[WorkspaceConfiguration]:
        """Find configuration for a specific workspace.
        
        Args:
            workspace: Workspace to get configuration for
            
        Returns:
            Configuration if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_workspace_name(self, name: WorkspaceName) -> Optional[WorkspaceConfiguration]:
        """Find configuration by workspace name.
        
        Args:
            name: Workspace name to get configuration for
            
        Returns:
            Configuration if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def get_global_config(self) -> WorkspaceConfiguration:
        """Get global (default) configuration.
        
        Returns:
            Global configuration object
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def get_effective_config(self, workspace: Workspace) -> WorkspaceConfiguration:
        """Get effective configuration for workspace (with global fallbacks).
        
        Args:
            workspace: Workspace to get effective configuration for
            
        Returns:
            Effective configuration with global defaults applied
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def get_config_value(
        self, 
        workspace: Workspace, 
        key: str, 
        default: Optional[Any] = None
    ) -> Any:
        """Get specific configuration value for workspace.
        
        Args:
            workspace: Workspace to get value for
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def set_config_value(
        self, 
        workspace: Workspace, 
        key: str, 
        value: Any
    ) -> None:
        """Set specific configuration value for workspace.
        
        Args:
            workspace: Workspace to set value for
            key: Configuration key
            value: Configuration value to set
            
        Raises:
            RepositoryError: If update operation fails
            ValidationError: If value is invalid for key
        """
        pass
    
    @abstractmethod
    async def remove_config_value(
        self, 
        workspace: Workspace, 
        key: str
    ) -> bool:
        """Remove specific configuration value for workspace.
        
        Args:
            workspace: Workspace to remove value from
            key: Configuration key to remove
            
        Returns:
            True if value was removed, False if key didn't exist
            
        Raises:
            RepositoryError: If removal operation fails
        """
        pass
    
    @abstractmethod
    async def update_config(
        self, 
        workspace: Workspace, 
        updates: Dict[str, Any]
    ) -> WorkspaceConfiguration:
        """Update multiple configuration values atomically.
        
        Args:
            workspace: Workspace to update
            updates: Dictionary of key-value pairs to update
            
        Returns:
            Updated configuration
            
        Raises:
            RepositoryError: If update operation fails
            ValidationError: If any value is invalid
        """
        pass
    
    @abstractmethod
    async def reset_to_defaults(
        self, 
        workspace: Workspace, 
        keys: Optional[List[str]] = None
    ) -> WorkspaceConfiguration:
        """Reset configuration values to defaults.
        
        Args:
            workspace: Workspace to reset
            keys: Specific keys to reset, or None for all
            
        Returns:
            Reset configuration
            
        Raises:
            RepositoryError: If reset operation fails
        """
        pass
    
    @abstractmethod
    async def export_config(
        self, 
        workspace: Workspace, 
        include_defaults: bool = False
    ) -> Dict[str, Any]:
        """Export workspace configuration to dictionary.
        
        Args:
            workspace: Workspace to export
            include_defaults: Whether to include default values
            
        Returns:
            Configuration as dictionary
            
        Raises:
            RepositoryError: If export operation fails
        """
        pass
    
    @abstractmethod
    async def import_config(
        self, 
        workspace: Workspace, 
        config_data: Dict[str, Any], 
        merge: bool = True
    ) -> WorkspaceConfiguration:
        """Import configuration from dictionary.
        
        Args:
            workspace: Workspace to import to
            config_data: Configuration data to import
            merge: Whether to merge with existing config or replace
            
        Returns:
            Imported configuration
            
        Raises:
            RepositoryError: If import operation fails
            ValidationError: If configuration data is invalid
        """
        pass
    
    @abstractmethod
    async def validate_config(
        self, 
        config: WorkspaceConfiguration
    ) -> List[str]:
        """Validate configuration object.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors, empty if valid
            
        Raises:
            RepositoryError: If validation operation fails
        """
        pass
    
    @abstractmethod
    async def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema definition.
        
        Returns:
            Schema definition with keys, types, and validation rules
            
        Raises:
            RepositoryError: If schema retrieval fails
        """
        pass
    
    @abstractmethod
    async def find_configs_with_value(
        self, 
        key: str, 
        value: Any
    ) -> List[WorkspaceConfiguration]:
        """Find all configurations with specific key-value pair.
        
        Args:
            key: Configuration key to search for
            value: Value to match
            
        Returns:
            List of configurations with matching key-value
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def get_config_usage_stats(self) -> Dict[str, Any]:
        """Get configuration usage statistics.
        
        Returns:
            Dictionary with usage statistics:
            - total_configs: Total number of configurations
            - most_common_values: Most common configuration values
            - custom_configs: Configurations with non-default values
            - unused_keys: Available but unused configuration keys
            
        Raises:
            RepositoryError: If stats calculation fails
        """
        pass


# Specifications for workspace configuration queries

class ByWorkspaceSpecification(Specification[WorkspaceConfiguration]):
    """Specification for filtering configurations by workspace."""
    
    def __init__(self, workspace: Workspace):
        self.workspace = workspace
    
    def is_satisfied_by(self, config: WorkspaceConfiguration) -> bool:
        return config.workspace == self.workspace


class ByWorkspaceNameSpecification(Specification[WorkspaceConfiguration]):
    """Specification for filtering configurations by workspace name."""
    
    def __init__(self, workspace_name: WorkspaceName):
        self.workspace_name = workspace_name
    
    def is_satisfied_by(self, config: WorkspaceConfiguration) -> bool:
        return config.workspace.name == self.workspace_name


class HasConfigKeySpecification(Specification[WorkspaceConfiguration]):
    """Specification for filtering configurations with specific key."""
    
    def __init__(self, key: str):
        self.key = key
    
    def is_satisfied_by(self, config: WorkspaceConfiguration) -> bool:
        return self.key in config.settings


class HasConfigValueSpecification(Specification[WorkspaceConfiguration]):
    """Specification for filtering configurations with specific key-value."""
    
    def __init__(self, key: str, value: Any):
        self.key = key
        self.value = value
    
    def is_satisfied_by(self, config: WorkspaceConfiguration) -> bool:
        return config.settings.get(self.key) == self.value


class CustomConfigSpecification(Specification[WorkspaceConfiguration]):
    """Specification for filtering configurations with custom (non-default) values."""
    
    def is_satisfied_by(self, config: WorkspaceConfiguration) -> bool:
        # Implementation would check if config has non-default values
        return len(config.settings) > 0
