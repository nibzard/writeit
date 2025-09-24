"""Mock implementation of WorkspaceConfigRepository for testing."""

from typing import List, Optional, Dict, Any
from datetime import datetime

from writeit.domains.workspace.repositories.workspace_config_repository import WorkspaceConfigRepository
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
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