"""Workspace configuration service.

Provides comprehensive configuration management including validation,
merging, schema management, and environment-specific overrides.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Set, Tuple
from datetime import datetime
from enum import Enum
import asyncio
import os
import re

from ....shared.repository import RepositoryError
from ..entities.workspace import Workspace
from ..entities.workspace_configuration import WorkspaceConfiguration
from ..value_objects.configuration_value import (
    ConfigurationValue,
    StringConfigValue,
    IntConfigValue,
    BoolConfigValue,
    ListConfigValue,
    string_config,
    int_config,
    bool_config,
    list_config
)
from ..repositories.workspace_config_repository import WorkspaceConfigRepository


class ConfigurationValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigurationMergeError(Exception):
    """Raised when configuration merge fails."""
    pass


class ConfigurationSchemaError(Exception):
    """Raised when configuration schema is invalid."""
    pass


class ConfigurationScope(str, Enum):
    """Configuration scopes for value inheritance."""
    GLOBAL = "global"          # System-wide defaults
    WORKSPACE = "workspace"    # Workspace-specific
    ENVIRONMENT = "environment"  # Environment variables
    RUNTIME = "runtime"        # Runtime overrides


@dataclass
class ConfigurationValidationIssue:
    """Individual configuration validation issue."""
    key: str
    severity: str  # "error", "warning", "info"
    message: str
    suggestion: Optional[str] = None
    current_value: Optional[Any] = None
    expected_type: Optional[str] = None


@dataclass
class ConfigurationMergeConflict:
    """Configuration merge conflict."""
    key: str
    source_value: Any
    target_value: Any
    source_scope: ConfigurationScope
    target_scope: ConfigurationScope
    resolution_strategy: Optional[str] = None


@dataclass
class ConfigurationSchema:
    """Configuration schema definition."""
    keys: Dict[str, Dict[str, Any]]
    version: str
    created_at: datetime
    description: str
    
    def validate_key(self, key: str, value: Any) -> List[str]:
        """Validate a configuration key-value pair."""
        issues = []
        
        if key not in self.keys:
            issues.append(f"Unknown configuration key: {key}")
            return issues
        
        key_schema = self.keys[key]
        
        # Type validation
        expected_type = key_schema.get("type")
        if expected_type and not self._validate_type(value, expected_type):
            issues.append(f"Invalid type for {key}: expected {expected_type}, got {type(value).__name__}")
        
        # Value validation
        if "allowed_values" in key_schema:
            if value not in key_schema["allowed_values"]:
                issues.append(f"Invalid value for {key}: {value} not in {key_schema['allowed_values']}")
        
        # Range validation
        if "min_value" in key_schema and isinstance(value, (int, float)):
            if value < key_schema["min_value"]:
                issues.append(f"Value for {key} below minimum: {value} < {key_schema['min_value']}")
        
        if "max_value" in key_schema and isinstance(value, (int, float)):
            if value > key_schema["max_value"]:
                issues.append(f"Value for {key} above maximum: {value} > {key_schema['max_value']}")
        
        # Pattern validation
        if "pattern" in key_schema and isinstance(value, str):
            pattern = key_schema["pattern"]
            if not re.match(pattern, value):
                issues.append(f"Value for {key} doesn't match pattern: {value} !~ {pattern}")
        
        return issues
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type."""
        type_map = {
            "string": str,
            "int": int,
            "bool": bool,
            "list": list,
            "dict": dict
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown types pass validation


class WorkspaceConfigurationService:
    """Service for managing workspace configuration.
    
    Provides comprehensive configuration management including validation,
    merging, schema management, and environment-specific overrides.
    
    Examples:
        service = WorkspaceConfigurationService(config_repo)
        
        # Validate configuration
        issues = await service.validate_configuration(workspace, config)
        
        # Merge configurations
        merged = await service.merge_configurations([global_config, workspace_config])
        
        # Apply environment overrides
        final_config = await service.apply_environment_overrides(config, env_vars)
        
        # Get effective configuration
        effective = await service.get_effective_configuration(workspace)
    """
    
    def __init__(self, config_repository: WorkspaceConfigRepository) -> None:
        """Initialize configuration service.
        
        Args:
            config_repository: Repository for configuration persistence
        """
        self._config_repo = config_repository
        self._schema_cache = {}
        self._validation_cache = {}
        self._environment_prefix = "WRITEIT_"
        
        # Configuration merge strategies
        self._merge_strategies = {
            "override": self._merge_override,
            "merge": self._merge_deep,
            "append": self._merge_append,
            "preserve": self._merge_preserve
        }
    
    async def validate_configuration(
        self,
        workspace: Workspace,
        config: WorkspaceConfiguration,
        strict: bool = False
    ) -> List[ConfigurationValidationIssue]:
        """Validate workspace configuration.
        
        Args:
            workspace: Workspace context
            config: Configuration to validate
            strict: If True, treat warnings as errors
            
        Returns:
            List of validation issues
            
        Raises:
            ConfigurationSchemaError: If schema is invalid
            RepositoryError: If validation operation fails
        """
        issues = []
        
        # Get configuration schema
        schema = await self._get_configuration_schema()
        
        # Validate each configuration value
        for key, config_value in config.values.items():
            value = config_value.get_effective_value()
            key_issues = schema.validate_key(key, value)
            
            for issue_msg in key_issues:
                severity = "error" if strict else self._determine_issue_severity(key, issue_msg)
                issues.append(ConfigurationValidationIssue(
                    key=key,
                    severity=severity,
                    message=issue_msg,
                    current_value=value,
                    expected_type=schema.keys.get(key, {}).get("type")
                ))
        
        # Validate configuration consistency
        consistency_issues = await self._validate_configuration_consistency(config)
        issues.extend(consistency_issues)
        
        # Validate against workspace context
        context_issues = await self._validate_workspace_context(workspace, config)
        issues.extend(context_issues)
        
        return issues
    
    async def merge_configurations(
        self,
        configs: List[Tuple[WorkspaceConfiguration, ConfigurationScope]],
        strategy: str = "override"
    ) -> WorkspaceConfiguration:
        """Merge multiple configurations with precedence rules.
        
        Args:
            configs: List of (configuration, scope) tuples in precedence order
            strategy: Merge strategy ("override", "merge", "append", "preserve")
            
        Returns:
            Merged configuration
            
        Raises:
            ConfigurationMergeError: If merge operation fails
            ConfigurationValidationError: If merged config is invalid
        """
        if not configs:
            return WorkspaceConfiguration.default()
        
        if len(configs) == 1:
            return configs[0][0]
        
        # Start with first configuration
        result_config, _ = configs[0]
        merge_conflicts = []
        
        # Merge each subsequent configuration
        for config, scope in configs[1:]:
            try:
                result_config, conflicts = await self._merge_single_configuration(
                    result_config, config, scope, strategy
                )
                merge_conflicts.extend(conflicts)
            except Exception as e:
                raise ConfigurationMergeError(f"Failed to merge configuration: {e}") from e
        
        # Validate merged configuration
        validation_issues = await self.validate_configuration(
            workspace=None,  # Context-free validation
            config=result_config,
            strict=False
        )
        
        error_issues = [issue for issue in validation_issues if issue.severity == "error"]
        if error_issues:
            raise ConfigurationValidationError(f"Merged configuration is invalid: {error_issues}")
        
        return result_config
    
    async def apply_environment_overrides(
        self,
        config: WorkspaceConfiguration,
        environment: Optional[Dict[str, str]] = None
    ) -> WorkspaceConfiguration:
        """Apply environment variable overrides to configuration.
        
        Args:
            config: Base configuration
            environment: Environment variables (uses os.environ if None)
            
        Returns:
            Configuration with environment overrides applied
            
        Raises:
            ConfigurationValidationError: If environment overrides are invalid
        """
        if environment is None:
            environment = dict(os.environ)
        
        # Find environment variables with our prefix
        env_overrides = {}
        for env_key, env_value in environment.items():
            if env_key.startswith(self._environment_prefix):
                config_key = env_key[len(self._environment_prefix):].lower()
                
                # Convert environment variable to appropriate type
                try:
                    parsed_value = await self._parse_environment_value(config, config_key, env_value)
                    env_overrides[config_key] = parsed_value
                except Exception as e:
                    raise ConfigurationValidationError(
                        f"Invalid environment override {env_key}={env_value}: {e}"
                    )
        
        # Apply overrides
        result_config = config
        for key, value in env_overrides.items():
            if config.has_key(key):
                result_config = result_config.set_value(key, value)
        
        return result_config
    
    async def get_effective_configuration(
        self,
        workspace: Workspace,
        include_environment: bool = True
    ) -> WorkspaceConfiguration:
        """Get effective configuration for workspace with all overrides applied.
        
        Args:
            workspace: Workspace to get configuration for
            include_environment: Whether to include environment overrides
            
        Returns:
            Effective configuration with all overrides
            
        Raises:
            RepositoryError: If configuration retrieval fails
            ConfigurationMergeError: If configuration merge fails
        """
        # Build configuration hierarchy
        configs = []
        
        # 1. Global configuration (lowest precedence)
        global_config = await self._config_repo.get_global_config()
        configs.append((global_config, ConfigurationScope.GLOBAL))
        
        # 2. Workspace configuration
        workspace_config = await self._config_repo.find_by_workspace(workspace)
        if workspace_config:
            configs.append((workspace_config, ConfigurationScope.WORKSPACE))
        
        # Merge configurations
        effective_config = await self.merge_configurations(configs, strategy="override")
        
        # 3. Apply environment overrides (highest precedence)
        if include_environment:
            effective_config = await self.apply_environment_overrides(effective_config)
        
        return effective_config
    
    async def update_configuration_schema(
        self,
        schema_updates: Dict[str, Dict[str, Any]]
    ) -> ConfigurationSchema:
        """Update configuration schema with new keys or modifications.
        
        Args:
            schema_updates: Schema updates to apply
            
        Returns:
            Updated schema
            
        Raises:
            ConfigurationSchemaError: If schema update is invalid
        """
        current_schema = await self._get_configuration_schema()
        
        # Validate schema updates
        for key, key_schema in schema_updates.items():
            await self._validate_schema_definition(key, key_schema)
        
        # Apply updates
        updated_keys = current_schema.keys.copy()
        updated_keys.update(schema_updates)
        
        updated_schema = ConfigurationSchema(
            keys=updated_keys,
            version=self._increment_schema_version(current_schema.version),
            created_at=datetime.now(),
            description=f"Updated schema with {len(schema_updates)} changes"
        )
        
        # Cache updated schema
        self._schema_cache["current"] = updated_schema
        
        return updated_schema
    
    async def export_configuration(
        self,
        workspace: Workspace,
        scope: ConfigurationScope = ConfigurationScope.WORKSPACE,
        include_defaults: bool = False,
        format_type: str = "yaml"
    ) -> str:
        """Export workspace configuration to string format.
        
        Args:
            workspace: Workspace to export
            scope: Configuration scope to export
            include_defaults: Whether to include default values
            format_type: Export format ("yaml", "json", "env")
            
        Returns:
            Configuration as formatted string
            
        Raises:
            RepositoryError: If export operation fails
        """
        if scope == ConfigurationScope.WORKSPACE:
            config = await self._config_repo.find_by_workspace(workspace)
        elif scope == ConfigurationScope.GLOBAL:
            config = await self._config_repo.get_global_config()
        else:
            config = await self.get_effective_configuration(workspace)
        
        if not config:
            config = WorkspaceConfiguration.default()
        
        # Get configuration data
        if include_defaults:
            config_data = config.to_dict()
        else:
            config_data = config.get_non_default_values()
        
        # Format output
        if format_type == "yaml":
            return await self._export_as_yaml(config_data)
        elif format_type == "json":
            return await self._export_as_json(config_data)
        elif format_type == "env":
            return await self._export_as_env(config_data)
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
        """Import configuration from string format.
        
        Args:
            workspace: Target workspace
            config_data: Configuration data as string
            format_type: Input format ("yaml", "json", "env")
            merge_strategy: How to merge with existing config
            validate: Whether to validate imported configuration
            
        Returns:
            Imported and merged configuration
            
        Raises:
            ConfigurationValidationError: If imported config is invalid
            ConfigurationMergeError: If merge operation fails
        """
        # Parse configuration data
        if format_type == "yaml":
            parsed_data = await self._import_from_yaml(config_data)
        elif format_type == "json":
            parsed_data = await self._import_from_json(config_data)
        elif format_type == "env":
            parsed_data = await self._import_from_env(config_data)
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
        
        # Merge with existing configuration
        existing_config = await self._config_repo.find_by_workspace(workspace)
        if existing_config and merge_strategy != "replace":
            merged_config = await self.merge_configurations([
                (existing_config, ConfigurationScope.WORKSPACE),
                (imported_config, ConfigurationScope.WORKSPACE)
            ], strategy=merge_strategy)
        else:
            merged_config = imported_config
        
        # Update repository
        updated_config = await self._config_repo.update_config(workspace, merged_config.to_dict())
        
        return updated_config
    
    async def reset_configuration(
        self,
        workspace: Workspace,
        keys: Optional[List[str]] = None,
        scope: ConfigurationScope = ConfigurationScope.WORKSPACE
    ) -> WorkspaceConfiguration:
        """Reset configuration to defaults.
        
        Args:
            workspace: Target workspace
            keys: Specific keys to reset (None for all)
            scope: Configuration scope to reset
            
        Returns:
            Reset configuration
            
        Raises:
            RepositoryError: If reset operation fails
        """
        if scope == ConfigurationScope.WORKSPACE:
            return await self._config_repo.reset_to_defaults(workspace, keys)
        elif scope == ConfigurationScope.GLOBAL:
            # Reset global configuration
            default_config = WorkspaceConfiguration.default()
            global_config = await self._config_repo.get_global_config()
            
            if keys:
                # Reset specific keys
                reset_config = global_config
                for key in keys:
                    if default_config.has_key(key):
                        default_value = default_config.get_value(key)
                        reset_config = reset_config.set_value(key, default_value)
            else:
                # Reset all keys
                reset_config = default_config
            
            # This would need to be implemented in the repository
            # For now, return the default configuration
            return reset_config
        else:
            raise ValueError(f"Cannot reset configuration for scope: {scope}")
    
    async def get_configuration_diff(
        self,
        config1: WorkspaceConfiguration,
        config2: WorkspaceConfiguration
    ) -> Dict[str, Dict[str, Any]]:
        """Get differences between two configurations.
        
        Args:
            config1: First configuration
            config2: Second configuration
            
        Returns:
            Dictionary with differences
        """
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
    
    # Private helper methods
    
    async def _get_configuration_schema(self) -> ConfigurationSchema:
        """Get current configuration schema."""
        if "current" in self._schema_cache:
            return self._schema_cache["current"]
        
        # Build default schema
        schema = await self._build_default_schema()
        self._schema_cache["current"] = schema
        return schema
    
    async def _build_default_schema(self) -> ConfigurationSchema:
        """Build default configuration schema."""
        keys = {
            "default_model": {
                "type": "string",
                "description": "Default LLM model for pipeline execution",
                "allowed_values": ["gpt-4o-mini", "gpt-4o", "claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
                "default": "gpt-4o-mini"
            },
            "max_tokens": {
                "type": "int",
                "description": "Maximum tokens per LLM request",
                "min_value": 100,
                "max_value": 10000,
                "default": 2000
            },
            "temperature": {
                "type": "string",
                "description": "LLM temperature (0.0-1.0)",
                "pattern": r'^(0(\.[0-9]+)?|1(\.0+)?)$',
                "default": "0.7"
            },
            "enable_cache": {
                "type": "bool",
                "description": "Enable LLM response caching",
                "default": True
            },
            "cache_ttl_hours": {
                "type": "int",
                "description": "Cache time-to-live in hours",
                "min_value": 1,
                "max_value": 168,
                "default": 24
            },
            "template_search_paths": {
                "type": "list",
                "description": "Paths to search for templates",
                "default": ["templates", "global/templates"]
            },
            "auto_validate_templates": {
                "type": "bool",
                "description": "Automatically validate templates on load",
                "default": True
            },
            "parallel_execution": {
                "type": "bool",
                "description": "Enable parallel step execution",
                "default": True
            },
            "max_parallel_steps": {
                "type": "int",
                "description": "Maximum number of parallel steps",
                "min_value": 1,
                "max_value": 10,
                "default": 3
            },
            "retry_attempts": {
                "type": "int",
                "description": "Number of retry attempts for failed steps",
                "min_value": 0,
                "max_value": 10,
                "default": 3
            },
            "output_format": {
                "type": "string",
                "description": "Default output format",
                "allowed_values": ["rich", "plain", "json"],
                "default": "rich"
            },
            "log_level": {
                "type": "string",
                "description": "Logging level",
                "allowed_values": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                "default": "INFO"
            }
        }
        
        return ConfigurationSchema(
            keys=keys,
            version="1.0.0",
            created_at=datetime.now(),
            description="Default workspace configuration schema"
        )
    
    def _determine_issue_severity(self, key: str, message: str) -> str:
        """Determine severity of validation issue."""
        if "unknown" in message.lower() or "invalid type" in message.lower():
            return "error"
        elif "below minimum" in message.lower() or "above maximum" in message.lower():
            return "error"
        elif "doesn't match pattern" in message.lower():
            return "error"
        elif "not in" in message.lower():
            return "warning"
        else:
            return "info"
    
    async def _validate_configuration_consistency(
        self,
        config: WorkspaceConfiguration
    ) -> List[ConfigurationValidationIssue]:
        """Validate configuration consistency."""
        issues = []
        
        # Check for conflicting settings
        if config.has_key("parallel_execution") and config.has_key("max_parallel_steps"):
            parallel_enabled = config.get_bool("parallel_execution")
            max_parallel = config.get_int("max_parallel_steps")
            
            if not parallel_enabled and max_parallel > 1:
                issues.append(ConfigurationValidationIssue(
                    key="max_parallel_steps",
                    severity="warning",
                    message="max_parallel_steps > 1 but parallel_execution is disabled",
                    suggestion="Enable parallel_execution or set max_parallel_steps to 1"
                ))
        
        # Check cache settings
        if config.has_key("enable_cache") and config.has_key("cache_ttl_hours"):
            cache_enabled = config.get_bool("enable_cache")
            cache_ttl = config.get_int("cache_ttl_hours")
            
            if not cache_enabled and cache_ttl > 0:
                issues.append(ConfigurationValidationIssue(
                    key="cache_ttl_hours",
                    severity="info",
                    message="cache_ttl_hours set but caching is disabled",
                    suggestion="Enable caching or set cache_ttl_hours to 0"
                ))
        
        return issues
    
    async def _validate_workspace_context(
        self,
        workspace: Optional[Workspace],
        config: WorkspaceConfiguration
    ) -> List[ConfigurationValidationIssue]:
        """Validate configuration against workspace context."""
        issues = []
        
        if workspace is None:
            return issues
        
        # Check template search paths exist
        if config.has_key("template_search_paths"):
            search_paths = config.get_list("template_search_paths")
            for path in search_paths:
                if path.startswith("/"):
                    # Absolute path
                    if not os.path.exists(path):
                        issues.append(ConfigurationValidationIssue(
                            key="template_search_paths",
                            severity="warning",
                            message=f"Template search path does not exist: {path}",
                            suggestion="Create the directory or remove from search paths"
                        ))
                else:
                    # Relative to workspace
                    full_path = workspace.root_path.value / path
                    if not full_path.exists():
                        issues.append(ConfigurationValidationIssue(
                            key="template_search_paths",
                            severity="info",
                            message=f"Template search path does not exist: {path}",
                            suggestion="Create the directory or it will be ignored"
                        ))
        
        return issues
    
    async def _merge_single_configuration(
        self,
        base_config: WorkspaceConfiguration,
        override_config: WorkspaceConfiguration,
        scope: ConfigurationScope,
        strategy: str
    ) -> Tuple[WorkspaceConfiguration, List[ConfigurationMergeConflict]]:
        """Merge a single configuration with conflict detection."""
        merge_func = self._merge_strategies.get(strategy, self._merge_override)
        conflicts = []
        
        result_config = base_config
        override_data = override_config.get_non_default_values()
        
        for key, override_value in override_data.items():
            if base_config.has_key(key):
                base_value = base_config.get_value(key)
                
                if base_value != override_value:
                    conflicts.append(ConfigurationMergeConflict(
                        key=key,
                        source_value=base_value,
                        target_value=override_value,
                        source_scope=ConfigurationScope.WORKSPACE,  # Assuming base is workspace
                        target_scope=scope,
                        resolution_strategy=strategy
                    ))
                
                # Apply merge strategy
                merged_value = await merge_func(base_value, override_value)
                result_config = result_config.set_value(key, merged_value)
            else:
                # New key, just add it
                result_config = result_config.set_value(key, override_value)
        
        return result_config, conflicts
    
    async def _merge_override(self, base_value: Any, override_value: Any) -> Any:
        """Override merge strategy - override value wins."""
        return override_value
    
    async def _merge_deep(self, base_value: Any, override_value: Any) -> Any:
        """Deep merge strategy - merge nested structures."""
        if isinstance(base_value, dict) and isinstance(override_value, dict):
            result = base_value.copy()
            result.update(override_value)
            return result
        elif isinstance(base_value, list) and isinstance(override_value, list):
            return base_value + override_value
        else:
            return override_value
    
    async def _merge_append(self, base_value: Any, override_value: Any) -> Any:
        """Append merge strategy - append to lists, override others."""
        if isinstance(base_value, list) and isinstance(override_value, list):
            return base_value + override_value
        else:
            return override_value
    
    async def _merge_preserve(self, base_value: Any, override_value: Any) -> Any:
        """Preserve merge strategy - keep base value."""
        return base_value
    
    async def _parse_environment_value(
        self,
        config: WorkspaceConfiguration,
        key: str,
        env_value: str
    ) -> Any:
        """Parse environment variable value to appropriate type."""
        if not config.has_key(key):
            return env_value
        
        config_value = config.values[key]
        
        if isinstance(config_value, BoolConfigValue):
            return env_value.lower() in ("true", "1", "yes", "on")
        elif isinstance(config_value, IntConfigValue):
            return int(env_value)
        elif isinstance(config_value, ListConfigValue):
            # Parse comma-separated values
            return [item.strip() for item in env_value.split(",") if item.strip()]
        else:
            return env_value
    
    async def _validate_schema_definition(self, key: str, schema_def: Dict[str, Any]) -> None:
        """Validate schema definition."""
        required_fields = ["type", "description"]
        for field in required_fields:
            if field not in schema_def:
                raise ConfigurationSchemaError(f"Schema definition for '{key}' missing required field: {field}")
        
        valid_types = ["string", "int", "bool", "list", "dict"]
        if schema_def["type"] not in valid_types:
            raise ConfigurationSchemaError(f"Invalid type for '{key}': {schema_def['type']}")
    
    def _increment_schema_version(self, current_version: str) -> str:
        """Increment schema version."""
        try:
            parts = current_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            return ".".join(parts)
        except (ValueError, IndexError):
            return "1.0.1"
    
    async def _export_as_yaml(self, config_data: Dict[str, Any]) -> str:
        """Export configuration as YAML."""
        import yaml
        return yaml.dump(config_data, default_flow_style=False, sort_keys=True)
    
    async def _export_as_json(self, config_data: Dict[str, Any]) -> str:
        """Export configuration as JSON."""
        import json
        return json.dumps(config_data, indent=2, sort_keys=True)
    
    async def _export_as_env(self, config_data: Dict[str, Any]) -> str:
        """Export configuration as environment variables."""
        lines = []
        for key, value in sorted(config_data.items()):
            env_key = f"{self._environment_prefix}{key.upper()}"
            if isinstance(value, list):
                env_value = ",".join(str(item) for item in value)
            else:
                env_value = str(value)
            lines.append(f"{env_key}={env_value}")
        return "\n".join(lines)
    
    async def _import_from_yaml(self, yaml_data: str) -> Dict[str, Any]:
        """Import configuration from YAML."""
        import yaml
        return yaml.safe_load(yaml_data) or {}
    
    async def _import_from_json(self, json_data: str) -> Dict[str, Any]:
        """Import configuration from JSON."""
        import json
        return json.loads(json_data)
    
    async def _import_from_env(self, env_data: str) -> Dict[str, Any]:
        """Import configuration from environment format."""
        config_data = {}
        for line in env_data.strip().split("\n"):
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                if key.startswith(self._environment_prefix):
                    config_key = key[len(self._environment_prefix):].lower()
                    config_data[config_key] = value
        return config_data