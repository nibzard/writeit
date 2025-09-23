"""LMDB implementation of WorkspaceConfigRepository.

Provides persistent storage for workspace configuration using LMDB
with defaults management and inheritance.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from ...domains.workspace.repositories.workspace_config_repository import WorkspaceConfigRepository
from ...domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...domains.workspace.value_objects.configuration_value import ConfigurationValue
from ...shared.repository import RepositoryError
from ..persistence.lmdb_storage import LMDBStorage
from ..base.exceptions import StorageError


class LMDBWorkspaceConfigRepository(WorkspaceConfigRepository):
    """LMDB-based implementation of WorkspaceConfigRepository.
    
    Stores workspace configurations with defaults management,
    inheritance, and validation.
    """
    
    def __init__(self, storage: LMDBStorage, workspace: Optional[WorkspaceName] = None):
        """Initialize repository.
        
        Args:
            storage: LMDB storage instance
            workspace: Current workspace (if None, uses global scope)
        """
        super().__init__(workspace)
        self.storage = storage
        self._db_name = "workspace_configs"
    
    async def save(self, config: WorkspaceConfiguration) -> None:
        """Save a workspace configuration.
        
        Args:
            config: Configuration to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        try:
            key = self._make_key(config.workspace_name)
            
            await self.storage.store_entity(
                config,
                key,
                self._db_name
            )
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to save workspace config for {config.workspace_name}: {e}"
            ) from e
    
    async def find_by_id(self, config_id: str) -> Optional[WorkspaceConfiguration]:
        """Find configuration by ID.
        
        Args:
            config_id: Configuration ID to search for
            
        Returns:
            Configuration if found, None otherwise
        """
        try:
            # For workspace configs, ID is typically the workspace name
            workspace_name = WorkspaceName(config_id)
            return await self.find_by_workspace(workspace_name)
        except (StorageError, ValueError) as e:
            raise RepositoryError(f"Failed to find config by ID {config_id}: {e}") from e
    
    async def find_by_workspace(self, workspace: WorkspaceName) -> Optional[WorkspaceConfiguration]:
        """Find configuration for specific workspace.
        
        Args:
            workspace: Workspace name
            
        Returns:
            Configuration if found, None otherwise
        """
        try:
            key = self._make_key(workspace)
            return await self.storage.load_entity(
                key,
                WorkspaceConfiguration,
                self._db_name
            )
        except StorageError as e:
            raise RepositoryError(
                f"Failed to find config for workspace {workspace}: {e}"
            ) from e
    
    async def get_global_config(self) -> Optional[WorkspaceConfiguration]:
        """Get global (default) configuration.
        
        Returns:
            Global configuration if found, None otherwise
        """
        try:
            key = "config:global"
            return await self.storage.load_entity(
                key,
                WorkspaceConfiguration,
                self._db_name
            )
        except StorageError as e:
            raise RepositoryError(f"Failed to get global config: {e}") from e
    
    async def get_effective_config(self, workspace: WorkspaceName) -> WorkspaceConfiguration:
        """Get effective configuration with inheritance.
        
        Args:
            workspace: Workspace name
            
        Returns:
            Effective configuration (workspace config merged with global defaults)
        """
        try:
            # Get workspace-specific config
            workspace_config = await self.find_by_workspace(workspace)
            
            # Get global config as defaults
            global_config = await self.get_global_config()
            
            if workspace_config and global_config:
                # Merge workspace config with global defaults
                return self._merge_configurations(workspace_config, global_config)
            elif workspace_config:
                return workspace_config
            elif global_config:
                # Create workspace config based on global defaults
                return WorkspaceConfiguration(
                    workspace_name=workspace,
                    values=global_config.values.copy(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            else:
                # Create minimal default config
                return self._create_default_config(workspace)
                
        except StorageError as e:
            raise RepositoryError(
                f"Failed to get effective config for workspace {workspace}: {e}"
            ) from e
    
    async def get_configuration_value(
        self,
        workspace: WorkspaceName,
        key: str
    ) -> Optional[ConfigurationValue]:
        """Get specific configuration value.
        
        Args:
            workspace: Workspace name
            key: Configuration key
            
        Returns:
            Configuration value if found, None otherwise
        """
        try:
            effective_config = await self.get_effective_config(workspace)
            return effective_config.values.get(key)
        except StorageError as e:
            raise RepositoryError(
                f"Failed to get config value {key} for workspace {workspace}: {e}"
            ) from e
    
    async def set_configuration_value(
        self,
        workspace: WorkspaceName,
        key: str,
        value: ConfigurationValue
    ) -> None:
        """Set specific configuration value.
        
        Args:
            workspace: Workspace name
            key: Configuration key
            value: Configuration value
        """
        try:
            # Get or create workspace config
            config = await self.find_by_workspace(workspace)
            
            if not config:
                config = self._create_default_config(workspace)
            
            # Update value
            config.values[key] = value
            config.updated_at = datetime.now()
            
            # Save updated config
            await self.save(config)
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to set config value {key} for workspace {workspace}: {e}"
            ) from e
    
    async def remove_configuration_value(
        self,
        workspace: WorkspaceName,
        key: str
    ) -> bool:
        """Remove specific configuration value.
        
        Args:
            workspace: Workspace name
            key: Configuration key
            
        Returns:
            True if value was removed, False if not found
        """
        try:
            config = await self.find_by_workspace(workspace)
            
            if not config or key not in config.values:
                return False
            
            # Remove value
            del config.values[key]
            config.updated_at = datetime.now()
            
            # Save updated config
            await self.save(config)
            return True
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to remove config value {key} for workspace {workspace}: {e}"
            ) from e
    
    async def get_all_configurations(self) -> List[WorkspaceConfiguration]:
        """Get all workspace configurations.
        
        Returns:
            List of all configurations
        """
        try:
            prefix = "config:"
            return await self.storage.find_entities_by_prefix(
                prefix,
                WorkspaceConfiguration,
                self._db_name
            )
        except StorageError as e:
            raise RepositoryError(f"Failed to get all configurations: {e}") from e
    
    async def validate_configuration(
        self,
        config: WorkspaceConfiguration
    ) -> List[str]:
        """Validate configuration structure and values.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors, empty if valid
        """
        errors = []
        
        try:
            # Basic structure validation
            if not config.workspace_name:
                errors.append("Workspace name is required")
            
            # Validate configuration values
            for key, value in config.values.items():
                if not key:
                    errors.append("Configuration key cannot be empty")
                
                if not isinstance(value, ConfigurationValue):
                    errors.append(f"Invalid value type for key '{key}'")
                
                # Additional value-specific validation could go here
                # e.g., validate specific config keys like model names, paths, etc.
            
            return errors
            
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return errors
    
    async def reset_to_defaults(self, workspace: WorkspaceName) -> None:
        """Reset workspace configuration to global defaults.
        
        Args:
            workspace: Workspace name
        """
        try:
            global_config = await self.get_global_config()
            
            if global_config:
                # Create new config based on global defaults
                default_config = WorkspaceConfiguration(
                    workspace_name=workspace,
                    values=global_config.values.copy(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            else:
                # Create minimal default config
                default_config = self._create_default_config(workspace)
            
            await self.save(default_config)
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to reset config to defaults for workspace {workspace}: {e}"
            ) from e
    
    async def find_all(self) -> List[WorkspaceConfiguration]:
        """Find all configurations.
        
        Returns:
            List of all configurations
        """
        return await self.get_all_configurations()
    
    async def delete(self, config_id: str) -> bool:
        """Delete a configuration.
        
        Args:
            config_id: ID of configuration to delete (workspace name)
            
        Returns:
            True if configuration was deleted, False if not found
        """
        try:
            workspace_name = WorkspaceName(config_id)
            key = self._make_key(workspace_name)
            return await self.storage.delete_entity(key, self._db_name)
            
        except (StorageError, ValueError) as e:
            raise RepositoryError(f"Failed to delete config {config_id}: {e}") from e
    
    async def count(self) -> int:
        """Count configurations.
        
        Returns:
            Number of configurations
        """
        try:
            prefix = "config:"
            return await self.storage.count_entities(prefix, self._db_name)
        except StorageError as e:
            raise RepositoryError(f"Failed to count configurations: {e}") from e
    
    def _make_key(self, workspace: WorkspaceName) -> str:
        """Create storage key for configuration.
        
        Args:
            workspace: Workspace name
            
        Returns:
            Storage key
        """
        return f"config:{workspace.value}"
    
    def _merge_configurations(
        self,
        workspace_config: WorkspaceConfiguration,
        global_config: WorkspaceConfiguration
    ) -> WorkspaceConfiguration:
        """Merge workspace config with global defaults.
        
        Args:
            workspace_config: Workspace-specific configuration
            global_config: Global default configuration
            
        Returns:
            Merged configuration
        """
        # Start with global defaults
        merged_values = global_config.values.copy()
        
        # Override with workspace-specific values
        merged_values.update(workspace_config.values)
        
        return WorkspaceConfiguration(
            workspace_name=workspace_config.workspace_name,
            values=merged_values,
            created_at=workspace_config.created_at,
            updated_at=workspace_config.updated_at
        )
    
    def _create_default_config(self, workspace: WorkspaceName) -> WorkspaceConfiguration:
        """Create a minimal default configuration.
        
        Args:
            workspace: Workspace name
            
        Returns:
            Default configuration
        """
        default_values = {
            "default_model": ConfigurationValue("gpt-4o-mini", "string"),
            "max_tokens": ConfigurationValue(2000, "integer"),
            "temperature": ConfigurationValue(0.7, "float"),
            "cache_enabled": ConfigurationValue(True, "boolean"),
            "cache_ttl_hours": ConfigurationValue(24, "integer"),
        }
        
        return WorkspaceConfiguration(
            workspace_name=workspace,
            values=default_values,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
