"""LMDB implementation of WorkspaceConfigRepository.

Provides concrete LMDB-backed storage for workspace configurations with
settings validation, defaults management, and inheritance.
"""

from typing import List, Optional, Dict, Any
import json

from ...domains.workspace.repositories.workspace_config_repository import (
    WorkspaceConfigRepository,
    ByWorkspaceSpecification,
    ByWorkspaceNameSpecification,
    HasConfigKeySpecification,
    HasConfigValueSpecification,
    CustomConfigSpecification
)
from ...domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from ...domains.workspace.entities.workspace import Workspace
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...domains.workspace.value_objects.configuration_value import ConfigurationValue
from ...shared.repository import RepositoryError, EntityNotFoundError
from ..base.repository_base import LMDBRepositoryBase
from ..base.storage_manager import LMDBStorageManager
from ..base.serialization import DomainEntitySerializer


class LMDBWorkspaceConfigRepository(LMDBRepositoryBase[WorkspaceConfiguration], WorkspaceConfigRepository):
    """LMDB implementation of WorkspaceConfigRepository.
    
    Stores workspace configurations with global storage and provides
    comprehensive configuration management with validation and inheritance.
    """
    
    def __init__(self, storage_manager: LMDBStorageManager):
        """Initialize repository.
        
        Args:
            storage_manager: LMDB storage manager
        """
        # Use global workspace for configuration metadata
        global_workspace = WorkspaceName.from_string("__global__")
        super().__init__(
            storage_manager=storage_manager,
            workspace_name=global_workspace,
            entity_type=WorkspaceConfiguration,
            db_name="configurations",
            db_key="workspace_configs"
        )
        
        # Configuration schema definition
        self._schema = self._get_default_schema()
    
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with configuration-specific types.
        
        Args:
            serializer: Serializer to configure
        """
        # Register value objects
        serializer.register_value_object(WorkspaceName)
        serializer.register_value_object(ConfigurationValue)
        
        # Register entity types
        serializer.register_type("WorkspaceConfiguration", WorkspaceConfiguration)
        serializer.register_type("Workspace", Workspace)
    
    def _get_entity_id(self, entity: WorkspaceConfiguration) -> Any:
        """Extract entity ID for storage key.
        
        Args:
            entity: Workspace configuration entity
            
        Returns:
            Entity identifier
        """
        # Use workspace name as identifier
        return entity.workspace_name if hasattr(entity, 'workspace_name') else "global"
    
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID.
        
        Args:
            entity_id: Entity identifier (workspace name)
            
        Returns:
            Storage key string
        """
        # Don't use workspace prefix for configuration metadata
        return f"config:{str(entity_id)}"
    
    def _get_default_schema(self) -> Dict[str, Any]:
        """Get default configuration schema.
        
        Returns:
            Default schema definition
        """
        return {
            "default_model": {
                "type": "string",
                "default": "gpt-4o-mini",
                "description": "Default LLM model for pipeline execution",
                "enum": ["gpt-4o-mini", "gpt-4o", "claude-3-haiku", "claude-3-sonnet"]
            },
            "cache_enabled": {
                "type": "boolean",
                "default": True,
                "description": "Enable LLM response caching"
            },
            "cache_ttl_hours": {
                "type": "integer",
                "default": 24,
                "minimum": 1,
                "maximum": 168,
                "description": "Cache time-to-live in hours"
            },
            "max_concurrent_steps": {
                "type": "integer",
                "default": 3,
                "minimum": 1,
                "maximum": 10,
                "description": "Maximum concurrent pipeline steps"
            },
            "timeout_seconds": {
                "type": "integer",
                "default": 300,
                "minimum": 30,
                "maximum": 3600,
                "description": "Default timeout for pipeline operations"
            },
            "retry_count": {
                "type": "integer",
                "default": 3,
                "minimum": 0,
                "maximum": 10,
                "description": "Default retry count for failed operations"
            },
            "log_level": {
                "type": "string",
                "default": "INFO",
                "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                "description": "Logging level"
            },
            "auto_save": {
                "type": "boolean",
                "default": True,
                "description": "Automatically save pipeline progress"
            },
            "templates_path": {
                "type": "string",
                "default": "templates",
                "description": "Relative path to templates directory"
            },
            "output_format": {
                "type": "string",
                "default": "markdown",
                "enum": ["markdown", "json", "yaml", "text"],
                "description": "Default output format for generated content"
            }
        }
    
    async def find_by_workspace(self, workspace: Workspace) -> Optional[WorkspaceConfiguration]:
        """Find configuration for a specific workspace.
        
        Args:
            workspace: Workspace to get configuration for
            
        Returns:
            Configuration if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        return await self.find_by_id(workspace.name.value)
    
    async def find_by_workspace_name(self, name: WorkspaceName) -> Optional[WorkspaceConfiguration]:
        """Find configuration by workspace name.
        
        Args:
            name: Workspace name to get configuration for
            
        Returns:
            Configuration if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        return await self.find_by_id(name.value)
    
    async def get_global_config(self) -> WorkspaceConfiguration:
        """Get global (default) configuration.
        
        Returns:
            Global configuration object
            
        Raises:
            RepositoryError: If query operation fails
        """
        global_config = await self.find_by_id("global")
        if global_config is None:
            # Create default global configuration
            global_config = WorkspaceConfiguration.default()
            await self.save(global_config)
        
        return global_config
    
    async def get_effective_config(self, workspace: Workspace) -> WorkspaceConfiguration:
        """Get effective configuration for workspace (with global fallbacks).
        
        Args:
            workspace: Workspace to get effective configuration for
            
        Returns:
            Effective configuration with global defaults applied
            
        Raises:
            RepositoryError: If query operation fails
        """
        # Get workspace-specific config
        workspace_config = await self.find_by_workspace(workspace)
        
        # Get global config for defaults
        global_config = await self.get_global_config()
        
        if workspace_config is None:
            return global_config
        
        # Merge configurations (workspace overrides global)
        effective_settings = global_config.settings.copy()
        effective_settings.update(workspace_config.settings)
        
        return WorkspaceConfiguration(
            workspace_name=workspace.name.value,
            settings=effective_settings,
            created_at=workspace_config.created_at,
            updated_at=workspace_config.updated_at
        )
    
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
        effective_config = await self.get_effective_config(workspace)
        
        if key in effective_config.settings:
            config_value = effective_config.settings[key]
            if isinstance(config_value, ConfigurationValue):
                return config_value.value
            return config_value
        
        # Check schema for default
        if key in self._schema:
            return self._schema[key].get("default", default)
        
        return default
    
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
        # Validate value against schema
        validation_errors = self._validate_config_value(key, value)
        if validation_errors:
            raise RepositoryError(f"Invalid configuration value: {validation_errors[0]}")
        
        # Get or create workspace configuration
        config = await self.find_by_workspace(workspace)
        if config is None:
            config = WorkspaceConfiguration.create_for_workspace(workspace.name.value)
        
        # Update configuration
        updated_config = config.set_value(key, value)
        await self.save(updated_config)
    
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
        config = await self.find_by_workspace(workspace)
        if config is None or key not in config.settings:
            return False
        
        updated_config = config.remove_value(key)
        await self.save(updated_config)
        return True
    
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
        # Validate all values first
        for key, value in updates.items():
            validation_errors = self._validate_config_value(key, value)
            if validation_errors:
                raise RepositoryError(f"Invalid value for {key}: {validation_errors[0]}")
        
        # Get or create workspace configuration
        config = await self.find_by_workspace(workspace)
        if config is None:
            config = WorkspaceConfiguration.create_for_workspace(workspace.name.value)
        
        # Apply all updates
        updated_config = config
        for key, value in updates.items():
            updated_config = updated_config.set_value(key, value)
        
        await self.save(updated_config)
        return updated_config
    
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
        config = await self.find_by_workspace(workspace)
        if config is None:
            return WorkspaceConfiguration.create_for_workspace(workspace.name.value)
        
        updated_config = config
        
        if keys is None:
            # Reset all to defaults
            default_settings = {
                key: schema_def.get("default")
                for key, schema_def in self._schema.items()
                if "default" in schema_def
            }
            updated_config = WorkspaceConfiguration.create_for_workspace(
                workspace.name.value,
                settings=default_settings
            )
        else:
            # Reset specific keys
            for key in keys:
                if key in self._schema and "default" in self._schema[key]:
                    default_value = self._schema[key]["default"]
                    updated_config = updated_config.set_value(key, default_value)
                else:
                    updated_config = updated_config.remove_value(key)
        
        await self.save(updated_config)
        return updated_config
    
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
        if include_defaults:
            config = await self.get_effective_config(workspace)
        else:
            config = await self.find_by_workspace(workspace)
            if config is None:
                return {}
        
        return config.to_dict()
    
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
        # Validate imported data
        validation_errors = []
        for key, value in config_data.items():
            errors = self._validate_config_value(key, value)
            validation_errors.extend(errors)
        
        if validation_errors:
            raise RepositoryError(f"Invalid configuration data: {validation_errors}")
        
        if merge:
            # Merge with existing configuration
            existing_config = await self.find_by_workspace(workspace)
            if existing_config is None:
                existing_config = WorkspaceConfiguration.create_for_workspace(workspace.name.value)
            
            updated_config = existing_config
            for key, value in config_data.items():
                updated_config = updated_config.set_value(key, value)
        else:
            # Replace configuration
            updated_config = WorkspaceConfiguration.create_for_workspace(
                workspace.name.value,
                settings=config_data
            )
        
        await self.save(updated_config)
        return updated_config
    
    async def validate_config(self, config: WorkspaceConfiguration) -> List[str]:
        """Validate configuration object.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors, empty if valid
            
        Raises:
            RepositoryError: If validation operation fails
        """
        errors = []
        
        for key, value in config.settings.items():
            value_errors = self._validate_config_value(key, value)
            errors.extend(value_errors)
        
        return errors
    
    async def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema definition.
        
        Returns:
            Schema definition with keys, types, and validation rules
            
        Raises:
            RepositoryError: If schema retrieval fails
        """
        return self._schema.copy()
    
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
        spec = HasConfigValueSpecification(key, value)
        return await self.find_by_specification(spec)
    
    async def get_config_usage_stats(self) -> Dict[str, Any]:
        """Get configuration usage statistics.
        
        Returns:
            Dictionary with usage statistics
            
        Raises:
            RepositoryError: If stats calculation fails
        """
        all_configs = await self.find_all()
        
        if not all_configs:
            return {
                "total_configs": 0,
                "most_common_values": {},
                "custom_configs": 0,
                "unused_keys": list(self._schema.keys())
            }
        
        # Count value usage
        value_counts = {}
        custom_configs = 0
        used_keys = set()
        
        for config in all_configs:
            if config.settings:  # Has custom settings
                custom_configs += 1
            
            for key, value in config.settings.items():
                used_keys.add(key)
                
                if key not in value_counts:
                    value_counts[key] = {}
                
                value_str = str(value)
                if value_str not in value_counts[key]:
                    value_counts[key][value_str] = 0
                value_counts[key][value_str] += 1
        
        # Find most common values
        most_common_values = {}
        for key, values in value_counts.items():
            if values:
                most_common = max(values.items(), key=lambda x: x[1])
                most_common_values[key] = {
                    "value": most_common[0],
                    "count": most_common[1]
                }
        
        # Find unused keys
        unused_keys = [key for key in self._schema.keys() if key not in used_keys]
        
        return {
            "total_configs": len(all_configs),
            "most_common_values": most_common_values,
            "custom_configs": custom_configs,
            "unused_keys": unused_keys
        }
    
    def _validate_config_value(self, key: str, value: Any) -> List[str]:
        """Validate a configuration value against schema.
        
        Args:
            key: Configuration key
            value: Value to validate
            
        Returns:
            List of validation errors
        """
        if key not in self._schema:
            return [f"Unknown configuration key: {key}"]
        
        schema_def = self._schema[key]
        errors = []
        
        # Type validation
        expected_type = schema_def.get("type")
        if expected_type == "string" and not isinstance(value, str):
            errors.append(f"Expected string for {key}, got {type(value).__name__}")
        elif expected_type == "integer" and not isinstance(value, int):
            errors.append(f"Expected integer for {key}, got {type(value).__name__}")
        elif expected_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Expected boolean for {key}, got {type(value).__name__}")
        
        # Enum validation
        if "enum" in schema_def and value not in schema_def["enum"]:
            errors.append(f"Invalid value for {key}: {value}. Must be one of {schema_def['enum']}")
        
        # Range validation for integers
        if expected_type == "integer" and isinstance(value, int):
            if "minimum" in schema_def and value < schema_def["minimum"]:
                errors.append(f"Value for {key} must be at least {schema_def['minimum']}")
            if "maximum" in schema_def and value > schema_def["maximum"]:
                errors.append(f"Value for {key} must be at most {schema_def['maximum']}")
        
        return errors