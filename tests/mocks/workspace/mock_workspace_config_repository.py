"""Mock implementation of WorkspaceConfigRepository for testing."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from writeit.domains.workspace.repositories.workspace_config_repository import WorkspaceConfigRepository
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError


class MockWorkspaceConfigRepository(BaseMockRepository[WorkspaceConfiguration], WorkspaceConfigRepository):
    """Mock implementation of WorkspaceConfigRepository.
    
    Provides in-memory storage for workspace configurations with
    settings management and validation.
    """
    
    def __init__(self):
        # Config repository doesn't have workspace isolation since it manages workspace configs
        super().__init__(None)
        
    def _get_entity_id(self, entity: WorkspaceConfiguration) -> Any:
        """Extract entity ID from workspace configuration."""
        return str(entity.workspace_name.value)
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "WorkspaceConfiguration"
        
    # Repository interface implementation
    
    async def save(self, entity: WorkspaceConfiguration) -> None:
        """Save or update a workspace configuration."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id, workspace="global")
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: WorkspaceName) -> Optional[WorkspaceConfiguration]:
        """Find configuration by workspace name."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        config = self._get_entity(str(entity_id.value), workspace="global")
        self._log_event("find_by_id", self._get_entity_type_name(), 
                       str(entity_id.value), found=config is not None)
        return config
        
    async def find_all(self) -> List[WorkspaceConfiguration]:
        """Find all workspace configurations."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        configs = self._get_all_entities(workspace="global")
        self._log_event("find_all", self._get_entity_type_name(), count=len(configs))
        return configs
        
    async def find_by_specification(self, spec: Specification[WorkspaceConfiguration]) -> List[WorkspaceConfiguration]:
        """Find configurations matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        configs = self._find_entities_by_specification(spec, workspace="global")
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(configs))
        return configs
        
    async def exists(self, entity_id: WorkspaceName) -> bool:
        """Check if configuration exists."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        exists = self._entity_exists(str(entity_id.value), workspace="global")
        self._log_event("exists", self._get_entity_type_name(), str(entity_id.value), exists=exists)
        return exists
        
    async def delete(self, entity: WorkspaceConfiguration) -> None:
        """Delete a workspace configuration."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id, workspace="global"):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: WorkspaceName) -> bool:
        """Delete configuration by workspace name."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(str(entity_id.value), workspace="global")
        self._log_event("delete_by_id", self._get_entity_type_name(), 
                       str(entity_id.value), deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total configurations."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        total = self._count_entities(workspace="global")
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    # WorkspaceConfigRepository-specific methods
    
    async def find_by_workspace_name(self, workspace_name: WorkspaceName) -> Optional[WorkspaceConfiguration]:
        """Find configuration by workspace name."""
        return await self.find_by_id(workspace_name)
        
    async def get_setting(
        self, 
        workspace_name: WorkspaceName, 
        setting_key: str
    ) -> Optional[Any]:
        """Get specific setting value for a workspace."""
        await self._check_error_condition("get_setting")
        self._increment_call_count("get_setting")
        await self._apply_call_delay("get_setting")
        
        config = await self.find_by_workspace_name(workspace_name)
        if not config:
            self._log_event("get_setting", self._get_entity_type_name(), 
                           str(workspace_name.value), setting_key=setting_key, found=False)
            return None
            
        setting_value = config.settings.get(setting_key)
        self._log_event("get_setting", self._get_entity_type_name(), 
                       str(workspace_name.value), setting_key=setting_key, 
                       found=setting_value is not None)
        return setting_value
        
    async def set_setting(
        self, 
        workspace_name: WorkspaceName, 
        setting_key: str, 
        setting_value: Any
    ) -> None:
        """Set specific setting value for a workspace."""
        await self._check_error_condition("set_setting")
        self._increment_call_count("set_setting")
        await self._apply_call_delay("set_setting")
        
        config = await self.find_by_workspace_name(workspace_name)
        if not config:
            # Create default configuration if it doesn't exist
            from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
            config = WorkspaceConfiguration(
                workspace_name=workspace_name,
                settings={setting_key: setting_value},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        else:
            # Update existing configuration
            new_settings = config.settings.copy()
            new_settings[setting_key] = setting_value
            config = config.with_settings(new_settings)
            
        await self.save(config)
        self._log_event("set_setting", self._get_entity_type_name(), 
                       str(workspace_name.value), setting_key=setting_key)
        
    async def remove_setting(
        self, 
        workspace_name: WorkspaceName, 
        setting_key: str
    ) -> bool:
        """Remove specific setting for a workspace."""
        await self._check_error_condition("remove_setting")
        self._increment_call_count("remove_setting")
        await self._apply_call_delay("remove_setting")
        
        config = await self.find_by_workspace_name(workspace_name)
        if not config or setting_key not in config.settings:
            self._log_event("remove_setting", self._get_entity_type_name(), 
                           str(workspace_name.value), setting_key=setting_key, removed=False)
            return False
            
        new_settings = config.settings.copy()
        del new_settings[setting_key]
        updated_config = config.with_settings(new_settings)
        await self.save(updated_config)
        
        self._log_event("remove_setting", self._get_entity_type_name(), 
                       str(workspace_name.value), setting_key=setting_key, removed=True)
        return True
        
    async def get_all_settings(self, workspace_name: WorkspaceName) -> Dict[str, Any]:
        """Get all settings for a workspace."""
        await self._check_error_condition("get_all_settings")
        self._increment_call_count("get_all_settings")
        await self._apply_call_delay("get_all_settings")
        
        config = await self.find_by_workspace_name(workspace_name)
        if not config:
            self._log_event("get_all_settings", self._get_entity_type_name(), 
                           str(workspace_name.value), found=False)
            return {}
            
        self._log_event("get_all_settings", self._get_entity_type_name(), 
                       str(workspace_name.value), settings_count=len(config.settings))
        return config.settings.copy()
        
    async def update_settings(
        self, 
        workspace_name: WorkspaceName, 
        settings: Dict[str, Any]
    ) -> None:
        """Update multiple settings for a workspace."""
        await self._check_error_condition("update_settings")
        self._increment_call_count("update_settings")
        await self._apply_call_delay("update_settings")
        
        config = await self.find_by_workspace_name(workspace_name)
        if not config:
            # Create new configuration
            from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
            config = WorkspaceConfiguration(
                workspace_name=workspace_name,
                settings=settings.copy(),
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        else:
            # Update existing configuration
            new_settings = config.settings.copy()
            new_settings.update(settings)
            config = config.with_settings(new_settings)
            
        await self.save(config)
        self._log_event("update_settings", self._get_entity_type_name(), 
                       str(workspace_name.value), updated_count=len(settings))
        
    async def validate_settings(
        self, 
        workspace_name: WorkspaceName, 
        settings: Dict[str, Any]
    ) -> List[str]:
        """Validate workspace settings."""
        await self._check_error_condition("validate_settings")
        self._increment_call_count("validate_settings")
        await self._apply_call_delay("validate_settings")
        
        # Mock validation - return configured errors or empty list
        errors = self._behavior.return_values.get("validate_settings", [])
        self._log_event("validate_settings", self._get_entity_type_name(), 
                       str(workspace_name.value), error_count=len(errors))
        return errors
        
    async def get_default_settings(self) -> Dict[str, Any]:
        """Get default workspace settings."""
        await self._check_error_condition("get_default_settings")
        self._increment_call_count("get_default_settings")
        await self._apply_call_delay("get_default_settings")
        
        defaults = self._behavior.return_values.get("get_default_settings", {
            "auto_save": True,
            "cache_enabled": True,
            "default_model": "gpt-4o-mini",
            "max_concurrent_steps": 3,
            "step_timeout_seconds": 300,
            "enable_streaming": True
        })
        
        self._log_event("get_default_settings", self._get_entity_type_name(), 
                       settings_count=len(defaults))
        return defaults
        
    async def reset_to_defaults(self, workspace_name: WorkspaceName) -> None:
        """Reset workspace settings to defaults."""
        await self._check_error_condition("reset_to_defaults")
        self._increment_call_count("reset_to_defaults")
        await self._apply_call_delay("reset_to_defaults")
        
        defaults = await self.get_default_settings()
        await self.update_settings(workspace_name, defaults)
        
        self._log_event("reset_to_defaults", self._get_entity_type_name(), 
                       str(workspace_name.value))
        
    async def export_settings(
        self, 
        workspace_name: WorkspaceName
    ) -> Dict[str, Any]:
        """Export workspace settings for backup."""
        await self._check_error_condition("export_settings")
        self._increment_call_count("export_settings")
        await self._apply_call_delay("export_settings")
        
        config = await self.find_by_workspace_name(workspace_name)
        if not config:
            return {}
            
        export_data = {
            "workspace_name": str(workspace_name.value),
            "settings": config.settings,
            "exported_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        
        self._log_event("export_settings", self._get_entity_type_name(), 
                       str(workspace_name.value))
        return export_data
        
    async def import_settings(
        self, 
        workspace_name: WorkspaceName, 
        exported_data: Dict[str, Any]
    ) -> None:
        """Import workspace settings from backup."""
        await self._check_error_condition("import_settings")
        self._increment_call_count("import_settings")
        await self._apply_call_delay("import_settings")
        
        if "settings" not in exported_data:
            raise ValueError("Invalid exported data: missing 'settings' key")
            
        await self.update_settings(workspace_name, exported_data["settings"])
        
        self._log_event("import_settings", self._get_entity_type_name(), 
                       str(workspace_name.value))

    # Missing abstract methods from WorkspaceConfigRepository
    
    async def find_by_workspace(self, workspace: Workspace) -> Optional[WorkspaceConfiguration]:
        """Find configuration for a specific workspace."""
        return await self.find_by_workspace_name(workspace.name)
    
    async def get_global_config(self) -> WorkspaceConfiguration:
        """Get global (default) configuration."""
        await self._check_error_condition("get_global_config")
        self._increment_call_count("get_global_config")
        await self._apply_call_delay("get_global_config")
        
        global_name = WorkspaceName("global")
        global_config = await self.find_by_workspace_name(global_name)
        if not global_config:
            # Create default global configuration
            from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
            defaults = await self.get_default_settings()
            global_config = WorkspaceConfiguration(
                workspace_name=global_name,
                settings=defaults,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            await self.save(global_config)
        
        return global_config
    
    async def get_effective_config(self, workspace: Workspace) -> WorkspaceConfiguration:
        """Get effective configuration for workspace (with global fallbacks)."""
        await self._check_error_condition("get_effective_config")
        self._increment_call_count("get_effective_config")
        await self._apply_call_delay("get_effective_config")
        
        # Get workspace-specific config
        workspace_config = await self.find_by_workspace(workspace)
        global_config = await self.get_global_config()
        
        # Merge with global defaults
        if not workspace_config:
            return global_config
        
        # Merge settings: workspace overrides global
        effective_settings = global_config.settings.copy()
        effective_settings.update(workspace_config.settings)
        
        from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
        return WorkspaceConfiguration(
            workspace_name=workspace.name,
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
        """Get specific configuration value for workspace."""
        effective_config = await self.get_effective_config(workspace)
        return effective_config.settings.get(key, default)
    
    async def set_config_value(
        self, 
        workspace: Workspace, 
        key: str, 
        value: Any
    ) -> None:
        """Set specific configuration value for workspace."""
        await self.set_setting(workspace.name, key, value)
    
    async def remove_config_value(
        self, 
        workspace: Workspace, 
        key: str
    ) -> bool:
        """Remove specific configuration value for workspace."""
        return await self.remove_setting(workspace.name, key)
    
    async def update_config(
        self, 
        workspace: Workspace, 
        updates: Dict[str, Any]
    ) -> WorkspaceConfiguration:
        """Update multiple configuration values atomically."""
        await self.update_settings(workspace.name, updates)
        return await self.get_effective_config(workspace)
    
    async def reset_to_defaults(
        self, 
        workspace: Workspace, 
        keys: Optional[List[str]] = None
    ) -> WorkspaceConfiguration:
        """Reset configuration values to defaults."""
        await self._check_error_condition("reset_to_defaults_workspace")
        self._increment_call_count("reset_to_defaults_workspace")
        await self._apply_call_delay("reset_to_defaults_workspace")
        
        if keys is None:
            # Reset all to defaults
            await self.reset_to_defaults(workspace.name)
        else:
            # Reset specific keys
            defaults = await self.get_default_settings()
            updates = {key: defaults.get(key) for key in keys if key in defaults}
            if updates:
                await self.update_settings(workspace.name, updates)
        
        return await self.get_effective_config(workspace)
    
    async def export_config(
        self, 
        workspace: Workspace, 
        include_defaults: bool = False
    ) -> Dict[str, Any]:
        """Export workspace configuration to dictionary."""
        if include_defaults:
            config = await self.get_effective_config(workspace)
        else:
            config = await self.find_by_workspace(workspace)
            if not config:
                return {}
        
        return {
            "workspace_name": str(workspace.name.value),
            "settings": config.settings,
            "exported_at": datetime.now().isoformat(),
            "version": "1.0.0"
        }
    
    async def import_config(
        self, 
        workspace: Workspace, 
        config_data: Dict[str, Any], 
        merge: bool = True
    ) -> WorkspaceConfiguration:
        """Import configuration from dictionary."""
        await self._check_error_condition("import_config")
        self._increment_call_count("import_config")
        await self._apply_call_delay("import_config")
        
        if "settings" not in config_data:
            raise ValueError("Invalid config data: missing 'settings' key")
        
        settings = config_data["settings"]
        if merge:
            current_config = await self.find_by_workspace(workspace)
            if current_config:
                current_settings = current_config.settings.copy()
                current_settings.update(settings)
                settings = current_settings
        
        await self.update_settings(workspace.name, settings)
        return await self.get_effective_config(workspace)
    
    async def validate_config(
        self, 
        config: WorkspaceConfiguration
    ) -> List[str]:
        """Validate configuration object."""
        await self._check_error_condition("validate_config")
        self._increment_call_count("validate_config")
        await self._apply_call_delay("validate_config")
        
        # Mock validation - return configured errors or empty list
        errors = self._behavior.return_values.get("validate_config", [])
        return errors
    
    async def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema definition."""
        await self._check_error_condition("get_config_schema")
        self._increment_call_count("get_config_schema")
        await self._apply_call_delay("get_config_schema")
        
        schema = self._behavior.return_values.get("get_config_schema", {
            "properties": {
                "auto_save": {"type": "boolean", "default": True},
                "cache_enabled": {"type": "boolean", "default": True},
                "default_model": {"type": "string", "default": "gpt-4o-mini"},
                "max_concurrent_steps": {"type": "integer", "default": 3, "minimum": 1},
                "step_timeout_seconds": {"type": "integer", "default": 300, "minimum": 30},
                "enable_streaming": {"type": "boolean", "default": True}
            },
            "required": [],
            "additionalProperties": True
        })
        
        return schema
    
    async def find_configs_with_value(
        self, 
        key: str, 
        value: Any
    ) -> List[WorkspaceConfiguration]:
        """Find all configurations with specific key-value pair."""
        await self._check_error_condition("find_configs_with_value")
        self._increment_call_count("find_configs_with_value")
        await self._apply_call_delay("find_configs_with_value")
        
        all_configs = await self.find_all()
        matching_configs = [
            config for config in all_configs 
            if config.settings.get(key) == value
        ]
        
        self._log_event("find_configs_with_value", self._get_entity_type_name(), 
                       key=key, matches_found=len(matching_configs))
        return matching_configs
    
    async def get_config_usage_stats(self) -> Dict[str, Any]:
        """Get configuration usage statistics."""
        await self._check_error_condition("get_config_usage_stats")
        self._increment_call_count("get_config_usage_stats")
        await self._apply_call_delay("get_config_usage_stats")
        
        all_configs = await self.find_all()
        defaults = await self.get_default_settings()
        
        # Calculate statistics
        total_configs = len(all_configs)
        all_keys = set()
        value_counts = {}
        custom_configs = []
        
        for config in all_configs:
            all_keys.update(config.settings.keys())
            for key, value in config.settings.items():
                if key not in value_counts:
                    value_counts[key] = {}
                if value not in value_counts[key]:
                    value_counts[key][value] = 0
                value_counts[key][value] += 1
                
                # Check if it's a custom (non-default) value
                if defaults.get(key) != value:
                    custom_configs.append(config)
        
        # Most common values
        most_common_values = {}
        for key, values in value_counts.items():
            most_common_values[key] = max(values.items(), key=lambda x: x[1])
        
        # Unused keys
        default_keys = set(defaults.keys())
        unused_keys = default_keys - all_keys
        
        stats = {
            "total_configs": total_configs,
            "most_common_values": most_common_values,
            "custom_configs": len(set(config.workspace_name.value for config in custom_configs)),
            "unused_keys": list(unused_keys),
            "all_keys_used": list(all_keys),
            "stats_generated_at": datetime.now().isoformat()
        }
        
        self._log_event("get_config_usage_stats", self._get_entity_type_name(), 
                       total_configs=total_configs)
        return stats