"""Mock workspace configuration service for testing."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from unittest.mock import AsyncMock

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.configuration_value import (
    ConfigurationValue,
    StringConfigValue,
    IntConfigValue,
    BoolConfigValue,
    ListConfigValue
)
from writeit.domains.workspace.services.workspace_configuration_service import (
    WorkspaceConfigurationService,
    ConfigurationValidationIssue,
    ConfigurationMergeConflict,
    ConfigurationSchema,
    ConfigurationScope,
    ConfigurationValidationError,
    ConfigurationMergeError,
    ConfigurationSchemaError
)


class MockWorkspaceConfigurationService(WorkspaceConfigurationService):
    """Mock implementation of WorkspaceConfigurationService for testing."""
    
    def __init__(self):
        """Initialize mock service with test data."""
        # Don't call super().__init__ to avoid dependency injection
        self._configurations: Dict[str, WorkspaceConfiguration] = {}
        self._global_config = WorkspaceConfiguration.default()
        self._schemas: Dict[str, ConfigurationSchema] = {}
        
        # Mock state for testing
        self._validation_issues: Dict[str, List[ConfigurationValidationIssue]] = {}
        self._merge_conflicts: List[ConfigurationMergeConflict] = []
        self._should_fail_validation = False
        self._should_fail_merge = False
        self._should_fail_import = False
        
        # Setup default test data
        self._setup_test_data()
    
    def _setup_test_data(self):
        """Setup default test data."""
        # Create default schema
        schema = ConfigurationSchema(
            keys={
                "default_model": {
                    "type": "string",
                    "description": "Default LLM model",
                    "allowed_values": ["gpt-4o-mini", "gpt-4o", "claude-3-haiku"],
                    "default": "gpt-4o-mini"
                },
                "max_tokens": {
                    "type": "int",
                    "description": "Maximum tokens per request",
                    "min_value": 100,
                    "max_value": 10000,
                    "default": 2000
                },
                "enable_cache": {
                    "type": "bool",
                    "description": "Enable response caching",
                    "default": True
                }
            },
            version="1.0.0",
            created_at=datetime.now(),
            description="Test configuration schema"
        )
        self._schemas["current"] = schema
        
        # Create test configurations
        test_config = WorkspaceConfiguration.default()
        test_config = test_config.set_value("default_model", "gpt-4o")
        test_config = test_config.set_value("max_tokens", 4000)
        test_config = test_config.set_value("enable_cache", True)
        self._configurations["test_workspace"] = test_config
    
    # Mock control methods for testing
    
    def set_should_fail_validation(self, should_fail: bool):
        """Control whether validation should fail."""
        self._should_fail_validation = should_fail
    
    def set_should_fail_merge(self, should_fail: bool):
        """Control whether merge should fail."""
        self._should_fail_merge = should_fail
    
    def set_should_fail_import(self, should_fail: bool):
        """Control whether import should fail."""
        self._should_fail_import = should_fail
    
    def add_validation_issue(
        self,
        workspace_key: str,
        issue: ConfigurationValidationIssue
    ):
        """Add validation issue for testing."""
        if workspace_key not in self._validation_issues:
            self._validation_issues[workspace_key] = []
        self._validation_issues[workspace_key].append(issue)
    
    def add_merge_conflict(self, conflict: ConfigurationMergeConflict):
        """Add merge conflict for testing."""
        self._merge_conflicts.append(conflict)
    
    def get_configuration(self, workspace_key: str) -> Optional[WorkspaceConfiguration]:
        """Get configuration for testing."""
        return self._configurations.get(workspace_key)
    
    def set_configuration(self, workspace_key: str, config: WorkspaceConfiguration):
        """Set configuration for testing."""
        self._configurations[workspace_key] = config
    
    def get_global_configuration(self) -> WorkspaceConfiguration:
        """Get global configuration for testing."""
        return self._global_config
    
    def set_global_configuration(self, config: WorkspaceConfiguration):
        """Set global configuration for testing."""
        self._global_config = config
    
    # Implementation of WorkspaceConfigurationService interface
    
    async def validate_configuration(
        self,
        workspace: Workspace,
        config: WorkspaceConfiguration,
        strict: bool = False
    ) -> List[ConfigurationValidationIssue]:
        """Validate workspace configuration."""
        if self._should_fail_validation:
            raise ConfigurationValidationError("Forced validation failure for testing")
        
        issues = []
        
        # Return predefined issues for testing
        workspace_key = str(workspace.name) if workspace else "global"
        predefined_issues = self._validation_issues.get(workspace_key, [])
        issues.extend(predefined_issues)
        
        # Add some basic validation
        for key, config_value in config.values.items():
            value = config_value.get_effective_value()
            
            # Check for test-specific validation issues
            if key == "max_tokens" and isinstance(value, int):
                if value < 100:
                    issues.append(ConfigurationValidationIssue(
                        key=key,
                        severity="error",
                        message="max_tokens must be at least 100",
                        current_value=value,
                        expected_type="int"
                    ))
                elif value > 10000:
                    issues.append(ConfigurationValidationIssue(
                        key=key,
                        severity="warning",
                        message="max_tokens is very high",
                        current_value=value,
                        expected_type="int"
                    ))
            
            if key == "default_model" and isinstance(value, str):
                valid_models = ["gpt-4o-mini", "gpt-4o", "claude-3-haiku", "claude-3-sonnet"]
                if value not in valid_models:
                    issues.append(ConfigurationValidationIssue(
                        key=key,
                        severity="error",
                        message=f"Invalid model: {value}",
                        current_value=value,
                        expected_type="string"
                    ))
        
        return issues
    
    async def merge_configurations(
        self,
        configs: List[Tuple[WorkspaceConfiguration, ConfigurationScope]],
        strategy: str = "override"
    ) -> WorkspaceConfiguration:
        """Merge multiple configurations with precedence rules."""
        if self._should_fail_merge:
            raise ConfigurationMergeError("Forced merge failure for testing")
        
        if not configs:
            return WorkspaceConfiguration.default()
        
        if len(configs) == 1:
            return configs[0][0]
        
        # Simple merge implementation for testing
        result_config = configs[0][0]
        
        for config, scope in configs[1:]:
            # Override strategy: later configs override earlier ones
            if strategy == "override":
                for key, value in config.get_non_default_values().items():
                    result_config = result_config.set_value(key, value)
            
            # Track conflicts for testing
            if hasattr(result_config, 'values') and hasattr(config, 'values'):
                for key in config.values.keys():
                    if key in result_config.values:
                        if result_config.values[key] != config.values[key]:
                            conflict = ConfigurationMergeConflict(
                                key=key,
                                source_value=result_config.values[key].get_effective_value(),
                                target_value=config.values[key].get_effective_value(),
                                source_scope=ConfigurationScope.WORKSPACE,
                                target_scope=scope,
                                resolution_strategy=strategy
                            )
                            self._merge_conflicts.append(conflict)
        
        return result_config
    
    async def apply_environment_overrides(
        self,
        config: WorkspaceConfiguration,
        environment: Optional[Dict[str, str]] = None
    ) -> WorkspaceConfiguration:
        """Apply environment variable overrides to configuration."""
        if environment is None:
            environment = {
                "WRITEIT_DEFAULT_MODEL": "claude-3-haiku",
                "WRITEIT_MAX_TOKENS": "3000",
                "WRITEIT_ENABLE_CACHE": "true"
            }
        
        result_config = config
        
        # Apply environment overrides
        for env_key, env_value in environment.items():
            if env_key.startswith("WRITEIT_"):
                config_key = env_key[9:].lower()  # Remove "WRITEIT_" prefix
                
                # Convert value to appropriate type
                if config_key == "max_tokens":
                    try:
                        parsed_value = int(env_value)
                        result_config = result_config.set_value(config_key, parsed_value)
                    except ValueError:
                        pass
                elif config_key == "enable_cache":
                    parsed_value = env_value.lower() in ("true", "1", "yes", "on")
                    result_config = result_config.set_value(config_key, parsed_value)
                else:
                    result_config = result_config.set_value(config_key, env_value)
        
        return result_config
    
    async def get_effective_configuration(
        self,
        workspace: Workspace,
        include_environment: bool = True
    ) -> WorkspaceConfiguration:
        """Get effective configuration for workspace with all overrides applied."""
        # Build configuration hierarchy
        configs = [(self._global_config, ConfigurationScope.GLOBAL)]
        
        # Add workspace configuration if it exists
        workspace_key = str(workspace.name)
        if workspace_key in self._configurations:
            workspace_config = self._configurations[workspace_key]
            configs.append((workspace_config, ConfigurationScope.WORKSPACE))
        
        # Merge configurations
        effective_config = await self.merge_configurations(configs, strategy="override")
        
        # Apply environment overrides if requested
        if include_environment:
            effective_config = await self.apply_environment_overrides(effective_config)
        
        return effective_config
    
    async def update_configuration_schema(
        self,
        schema_updates: Dict[str, Dict[str, Any]]
    ) -> ConfigurationSchema:
        """Update configuration schema with new keys or modifications."""
        current_schema = self._schemas.get("current")
        if not current_schema:
            current_schema = ConfigurationSchema(
                keys={},
                version="1.0.0",
                created_at=datetime.now(),
                description="Default schema"
            )
        
        # Apply updates
        updated_keys = current_schema.keys.copy()
        updated_keys.update(schema_updates)
        
        # Increment version
        version_parts = current_schema.version.split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        new_version = ".".join(version_parts)
        
        updated_schema = ConfigurationSchema(
            keys=updated_keys,
            version=new_version,
            created_at=datetime.now(),
            description=f"Updated schema with {len(schema_updates)} changes"
        )
        
        self._schemas["current"] = updated_schema
        return updated_schema
    
    async def export_configuration(
        self,
        workspace: Workspace,
        scope: ConfigurationScope = ConfigurationScope.WORKSPACE,
        include_defaults: bool = False,
        format_type: str = "yaml"
    ) -> str:
        """Export workspace configuration to string format."""
        # Get configuration based on scope
        if scope == ConfigurationScope.WORKSPACE:
            workspace_key = str(workspace.name)
            config = self._configurations.get(workspace_key, WorkspaceConfiguration.default())
        elif scope == ConfigurationScope.GLOBAL:
            config = self._global_config
        else:
            config = await self.get_effective_configuration(workspace)
        
        # Get configuration data
        if include_defaults:
            config_data = config.to_dict()
        else:
            config_data = config.get_non_default_values()
        
        # Format output
        if format_type == "yaml":
            import yaml
            return yaml.dump(config_data, default_flow_style=False, sort_keys=True)
        elif format_type == "json":
            import json
            return json.dumps(config_data, indent=2, sort_keys=True)
        elif format_type == "env":
            lines = []
            for key, value in sorted(config_data.items()):
                env_key = f"WRITEIT_{key.upper()}"
                if isinstance(value, list):
                    env_value = ",".join(str(item) for item in value)
                else:
                    env_value = str(value)
                lines.append(f"{env_key}={env_value}")
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    async def import_configuration(
        self,
        workspace: Workspace,
        config_data: str,
        format_type: str = "yaml",
        merge_strategy: str = "override",
        validate: bool = True
    ) -> WorkspaceConfiguration:
        """Import configuration from string format."""
        if self._should_fail_import:
            raise ConfigurationValidationError("Forced import failure for testing")
        
        # Parse configuration data
        if format_type == "yaml":
            import yaml
            parsed_data = yaml.safe_load(config_data) or {}
        elif format_type == "json":
            import json
            parsed_data = json.loads(config_data)
        elif format_type == "env":
            parsed_data = {}
            for line in config_data.strip().split("\n"):
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    if key.startswith("WRITEIT_"):
                        config_key = key[9:].lower()  # Remove "WRITEIT_" prefix
                        parsed_data[config_key] = value
        else:
            raise ValueError(f"Unsupported import format: {format_type}")
        
        # Create configuration from parsed data
        imported_config = WorkspaceConfiguration.from_dict(parsed_data)
        
        # Validate if requested
        if validate:
            issues = await self.validate_configuration(workspace, imported_config, strict=False)
            error_issues = [issue for issue in issues if issue.severity == "error"]
            if error_issues:
                raise ConfigurationValidationError(f"Imported configuration is invalid: {error_issues}")
        
        # Store configuration
        workspace_key = str(workspace.name)
        self._configurations[workspace_key] = imported_config
        
        return imported_config
    
    async def reset_configuration(
        self,
        workspace: Workspace,
        keys: Optional[List[str]] = None,
        scope: ConfigurationScope = ConfigurationScope.WORKSPACE
    ) -> WorkspaceConfiguration:
        """Reset configuration to defaults."""
        default_config = WorkspaceConfiguration.default()
        
        if scope == ConfigurationScope.WORKSPACE:
            workspace_key = str(workspace.name)
            
            if keys:
                # Reset specific keys
                current_config = self._configurations.get(workspace_key, default_config)
                reset_config = current_config
                for key in keys:
                    if default_config.has_key(key):
                        default_value = default_config.get_value(key)
                        reset_config = reset_config.set_value(key, default_value)
                self._configurations[workspace_key] = reset_config
                return reset_config
            else:
                # Reset all keys
                self._configurations[workspace_key] = default_config
                return default_config
        
        elif scope == ConfigurationScope.GLOBAL:
            if keys:
                # Reset specific keys in global config
                reset_config = self._global_config
                for key in keys:
                    if default_config.has_key(key):
                        default_value = default_config.get_value(key)
                        reset_config = reset_config.set_value(key, default_value)
                self._global_config = reset_config
                return reset_config
            else:
                # Reset all global config
                self._global_config = default_config
                return default_config
        
        else:
            raise ValueError(f"Cannot reset configuration for scope: {scope}")
    
    async def get_configuration_diff(
        self,
        config1: WorkspaceConfiguration,
        config2: WorkspaceConfiguration
    ) -> Dict[str, Dict[str, Any]]:
        """Get differences between two configurations."""
        diff = {
            "added": {},
            "removed": {},
            "changed": {},
            "unchanged": {}
        }
        
        config1_data = config1.to_dict()
        config2_data = config2.to_dict()
        
        all_keys = set(config1_data.keys()) | set(config2_data.keys())
        
        for key in all_keys:
            if key in config1_data and key in config2_data:
                if config1_data[key] != config2_data[key]:
                    diff["changed"][key] = {
                        "old": config1_data[key],
                        "new": config2_data[key]
                    }
                else:
                    diff["unchanged"][key] = config1_data[key]
            elif key in config1_data:
                diff["removed"][key] = config1_data[key]
            else:
                diff["added"][key] = config2_data[key]
        
        return diff
    
    # Additional helper methods for testing
    
    def clear_all_configurations(self):
        """Clear all configurations for testing."""
        self._configurations.clear()
        self._global_config = WorkspaceConfiguration.default()
        self._validation_issues.clear()
        self._merge_conflicts.clear()
    
    def get_merge_conflicts(self) -> List[ConfigurationMergeConflict]:
        """Get merge conflicts for testing."""
        return self._merge_conflicts.copy()
    
    def get_schema(self, schema_name: str = "current") -> Optional[ConfigurationSchema]:
        """Get schema for testing."""
        return self._schemas.get(schema_name)
    
    def reset_mock_state(self):
        """Reset mock state for testing."""
        self._should_fail_validation = False
        self._should_fail_merge = False
        self._should_fail_import = False
        self.clear_all_configurations()
        self._setup_test_data()