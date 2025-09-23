"""Workspace configuration entity.

Domain entity for managing workspace-specific settings and preferences.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Dict, Any, Optional, List, Self

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


@dataclass
class WorkspaceConfiguration:
    """Domain entity representing workspace configuration.
    
    Manages workspace-specific settings with type safety and validation.
    
    Examples:
        config = WorkspaceConfiguration.default()
        config = config.set_value("default_model", "gpt-4o-mini")
        config = config.set_value("max_tokens", 2000)
        
        # Get validated values
        model = config.get_string("default_model")
        tokens = config.get_int("max_tokens")
    """
    
    values: Dict[str, ConfigurationValue] = field(default_factory=dict)
    schema_version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Validate configuration."""
        # Validate all configuration values
        for key, value in self.values.items():
            if not isinstance(value, ConfigurationValue):
                raise TypeError(f"Configuration value for '{key}' must be a ConfigurationValue")
    
    def set_value(self, key: str, value: Any) -> Self:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            
        Returns:
            Updated configuration
            
        Raises:
            KeyError: If configuration key is not defined
            ValueError: If value is invalid for the configuration type
        """
        if key not in self.values:
            raise KeyError(f"Configuration key '{key}' is not defined")
            
        config_def = self.values[key]
        
        # Create new configuration value with the updated value
        if isinstance(config_def, StringConfigValue):
            new_config = replace(config_def, value=value)
        elif isinstance(config_def, IntConfigValue):
            new_config = replace(config_def, value=value)
        elif isinstance(config_def, BoolConfigValue):
            new_config = replace(config_def, value=value)
        elif isinstance(config_def, ListConfigValue):
            new_config = replace(config_def, value=value)
        else:
            raise TypeError(f"Unsupported configuration type for '{key}'")
        
        # Validation happens in __post_init__ of the configuration value
        new_values = self.values.copy()
        new_values[key] = new_config
        
        return replace(
            self,
            values=new_values,
            updated_at=datetime.now()
        )
    
    def get_value(self, key: str) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            Configuration value or default if not set
            
        Raises:
            KeyError: If configuration key is not defined
        """
        if key not in self.values:
            raise KeyError(f"Configuration key '{key}' is not defined")
            
        return self.values[key].get_effective_value()
    
    def get_string(self, key: str) -> str:
        """Get a string configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            String value
            
        Raises:
            KeyError: If key not found
            TypeError: If value is not a string configuration
        """
        config_value = self.values.get(key)
        if config_value is None:
            raise KeyError(f"Configuration key '{key}' not found")
            
        if not isinstance(config_value, StringConfigValue):
            raise TypeError(f"Configuration '{key}' is not a string value")
            
        return config_value.get_effective_value() or ""
    
    def get_int(self, key: str) -> int:
        """Get an integer configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            Integer value
            
        Raises:
            KeyError: If key not found
            TypeError: If value is not an integer configuration
        """
        config_value = self.values.get(key)
        if config_value is None:
            raise KeyError(f"Configuration key '{key}' not found")
            
        if not isinstance(config_value, IntConfigValue):
            raise TypeError(f"Configuration '{key}' is not an integer value")
            
        return config_value.get_effective_value() or 0
    
    def get_bool(self, key: str) -> bool:
        """Get a boolean configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            Boolean value
            
        Raises:
            KeyError: If key not found
            TypeError: If value is not a boolean configuration
        """
        config_value = self.values.get(key)
        if config_value is None:
            raise KeyError(f"Configuration key '{key}' not found")
            
        if not isinstance(config_value, BoolConfigValue):
            raise TypeError(f"Configuration '{key}' is not a boolean value")
            
        return config_value.get_effective_value() or False
    
    def get_list(self, key: str) -> List[str]:
        """Get a list configuration value.
        
        Args:
            key: Configuration key
            
        Returns:
            List value
            
        Raises:
            KeyError: If key not found
            TypeError: If value is not a list configuration
        """
        config_value = self.values.get(key)
        if config_value is None:
            raise KeyError(f"Configuration key '{key}' not found")
            
        if not isinstance(config_value, ListConfigValue):
            raise TypeError(f"Configuration '{key}' is not a list value")
            
        return config_value.get_effective_value() or []
    
    def has_key(self, key: str) -> bool:
        """Check if configuration has a key.
        
        Args:
            key: Configuration key
            
        Returns:
            True if key exists
        """
        return key in self.values
    
    def is_default(self, key: str) -> bool:
        """Check if a configuration value is using its default.
        
        Args:
            key: Configuration key
            
        Returns:
            True if value is default
            
        Raises:
            KeyError: If key not found
        """
        if key not in self.values:
            raise KeyError(f"Configuration key '{key}' not found")
            
        return self.values[key].is_default()
    
    def get_all_keys(self) -> List[str]:
        """Get all configuration keys.
        
        Returns:
            List of configuration keys
        """
        return list(self.values.keys())
    
    def get_non_default_values(self) -> Dict[str, Any]:
        """Get all non-default configuration values.
        
        Returns:
            Dictionary of non-default values
        """
        result = {}
        for key, config_value in self.values.items():
            if not config_value.is_default():
                result[key] = config_value.get_effective_value()
        return result
    
    def merge_with(self, other: Self) -> Self:
        """Merge with another configuration.
        
        Args:
            other: Configuration to merge with
            
        Returns:
            New configuration with merged values
        """
        merged_values = self.values.copy()
        
        for key, other_value in other.values.items():
            if key in merged_values:
                # Use the other value if it's not default
                if not other_value.is_default():
                    merged_values[key] = other_value
            else:
                # Add new configuration from other
                merged_values[key] = other_value
        
        return replace(
            self,
            values=merged_values,
            updated_at=datetime.now()
        )
    
    @classmethod
    def default(cls) -> Self:
        """Create default workspace configuration.
        
        Returns:
            Default configuration with common settings
        """
        default_values = {
            # LLM Settings
            "default_model": string_config(
                key="default_model",
                default="gpt-4o-mini",
                description="Default LLM model for pipeline execution",
                allowed_values=["gpt-4o-mini", "gpt-4o", "claude-3-haiku", "claude-3-sonnet", "claude-3-opus"]
            ),
            "max_tokens": int_config(
                key="max_tokens",
                default=2000,
                description="Maximum tokens per LLM request",
                min_value=100,
                max_value=10000
            ),
            "temperature": string_config(
                key="temperature",
                default="0.7",
                description="LLM temperature (0.0-1.0)",
                pattern=r'^(0(\.[0-9]+)?|1(\.0+)?)$'
            ),
            
            # Cache Settings
            "enable_cache": bool_config(
                key="enable_cache",
                default=True,
                description="Enable LLM response caching"
            ),
            "cache_ttl_hours": int_config(
                key="cache_ttl_hours",
                default=24,
                description="Cache time-to-live in hours",
                min_value=1,
                max_value=168  # 1 week
            ),
            
            # Template Settings
            "template_search_paths": list_config(
                key="template_search_paths",
                default=["templates", "global/templates"],
                description="Paths to search for templates"
            ),
            "auto_validate_templates": bool_config(
                key="auto_validate_templates",
                default=True,
                description="Automatically validate templates on load"
            ),
            
            # Execution Settings
            "parallel_execution": bool_config(
                key="parallel_execution",
                default=True,
                description="Enable parallel step execution"
            ),
            "max_parallel_steps": int_config(
                key="max_parallel_steps",
                default=3,
                description="Maximum number of parallel steps",
                min_value=1,
                max_value=10
            ),
            "retry_attempts": int_config(
                key="retry_attempts",
                default=3,
                description="Number of retry attempts for failed steps",
                min_value=0,
                max_value=10
            ),
            
            # Output Settings
            "output_format": string_config(
                key="output_format",
                default="rich",
                description="Default output format",
                allowed_values=["rich", "plain", "json"]
            ),
            "log_level": string_config(
                key="log_level",
                default="INFO",
                description="Logging level",
                allowed_values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            )
        }
        
        return cls(
            values=default_values,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """Create configuration from dictionary.
        
        Args:
            data: Configuration data
            
        Returns:
            New configuration instance
        """
        config = cls.default()
        
        # Set values from data
        for key, value in data.items():
            if config.has_key(key):
                config = config.set_value(key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        result = {}
        for key, config_value in self.values.items():
            result[key] = config_value.get_effective_value()
        return result
    
    def __str__(self) -> str:
        """String representation."""
        non_default = len(self.get_non_default_values())
        total = len(self.values)
        return f"WorkspaceConfiguration({non_default}/{total} customized)"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"WorkspaceConfiguration(values={len(self.values)}, updated={self.updated_at})"
