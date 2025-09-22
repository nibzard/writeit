"""Configuration value objects.

Provides type-safe configuration handling for workspace settings.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar, Union, Dict, List, Optional


T = TypeVar('T')


@dataclass(frozen=True)
class ConfigurationValue(Generic[T], ABC):
    """Base class for type-safe configuration values.
    
    Provides validation and type safety for configuration settings.
    """
    
    key: str
    value: T
    default: T
    description: str = ""
    required: bool = False
    
    def __post_init__(self) -> None:
        """Validate configuration value."""
        if not self.key:
            raise ValueError("Configuration key cannot be empty")
            
        if self.required and self.value is None:
            raise ValueError(f"Required configuration '{self.key}' cannot be None")
            
        self._validate_value()
    
    @abstractmethod
    def _validate_value(self) -> None:
        """Validate the configuration value."""
        pass
    
    def is_default(self) -> bool:
        """Check if value is the default."""
        return self.value == self.default
    
    def get_effective_value(self) -> T:
        """Get the effective value (value or default if None)."""
        return self.value if self.value is not None else self.default


@dataclass(frozen=True)
class StringConfigValue(ConfigurationValue[Optional[str]]):
    """String configuration value with validation."""
    
    min_length: int = 0
    max_length: int = 1000
    allowed_values: Optional[List[str]] = None
    pattern: Optional[str] = None
    
    def _validate_value(self) -> None:
        """Validate string value."""
        if self.value is None:
            return
            
        if not isinstance(self.value, str):
            raise TypeError(f"Configuration '{self.key}' must be string, got {type(self.value)}")
            
        if len(self.value) < self.min_length:
            raise ValueError(f"Configuration '{self.key}' must be at least {self.min_length} characters")
            
        if len(self.value) > self.max_length:
            raise ValueError(f"Configuration '{self.key}' must be at most {self.max_length} characters")
            
        if self.allowed_values and self.value not in self.allowed_values:
            raise ValueError(f"Configuration '{self.key}' must be one of {self.allowed_values}")
            
        if self.pattern:
            import re
            if not re.match(self.pattern, self.value):
                raise ValueError(f"Configuration '{self.key}' does not match pattern {self.pattern}")


@dataclass(frozen=True)
class IntConfigValue(ConfigurationValue[Optional[int]]):
    """Integer configuration value with validation."""
    
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    
    def _validate_value(self) -> None:
        """Validate integer value."""
        if self.value is None:
            return
            
        if not isinstance(self.value, int):
            raise TypeError(f"Configuration '{self.key}' must be integer, got {type(self.value)}")
            
        if self.min_value is not None and self.value < self.min_value:
            raise ValueError(f"Configuration '{self.key}' must be at least {self.min_value}")
            
        if self.max_value is not None and self.value > self.max_value:
            raise ValueError(f"Configuration '{self.key}' must be at most {self.max_value}")


@dataclass(frozen=True)
class BoolConfigValue(ConfigurationValue[Optional[bool]]):
    """Boolean configuration value."""
    
    def _validate_value(self) -> None:
        """Validate boolean value."""
        if self.value is None:
            return
            
        if not isinstance(self.value, bool):
            raise TypeError(f"Configuration '{self.key}' must be boolean, got {type(self.value)}")


@dataclass(frozen=True)
class ListConfigValue(ConfigurationValue[Optional[List[str]]]):
    """List configuration value with validation."""
    
    min_items: int = 0
    max_items: int = 100
    allowed_item_values: Optional[List[str]] = None
    
    def _validate_value(self) -> None:
        """Validate list value."""
        if self.value is None:
            return
            
        if not isinstance(self.value, list):
            raise TypeError(f"Configuration '{self.key}' must be list, got {type(self.value)}")
            
        if len(self.value) < self.min_items:
            raise ValueError(f"Configuration '{self.key}' must have at least {self.min_items} items")
            
        if len(self.value) > self.max_items:
            raise ValueError(f"Configuration '{self.key}' must have at most {self.max_items} items")
            
        # Validate each item
        for item in self.value:
            if not isinstance(item, str):
                raise TypeError(f"Configuration '{self.key}' items must be strings")
                
            if self.allowed_item_values and item not in self.allowed_item_values:
                raise ValueError(f"Configuration '{self.key}' item '{item}' not in allowed values")


@dataclass(frozen=True)
class DictConfigValue(ConfigurationValue[Optional[Dict[str, Any]]]):
    """Dictionary configuration value with validation."""
    
    required_keys: Optional[List[str]] = None
    allowed_keys: Optional[List[str]] = None
    
    def _validate_value(self) -> None:
        """Validate dictionary value."""
        if self.value is None:
            return
            
        if not isinstance(self.value, dict):
            raise TypeError(f"Configuration '{self.key}' must be dictionary, got {type(self.value)}")
            
        # Check required keys
        if self.required_keys:
            missing_keys = set(self.required_keys) - set(self.value.keys())
            if missing_keys:
                raise ValueError(f"Configuration '{self.key}' missing required keys: {missing_keys}")
                
        # Check allowed keys
        if self.allowed_keys:
            invalid_keys = set(self.value.keys()) - set(self.allowed_keys)
            if invalid_keys:
                raise ValueError(f"Configuration '{self.key}' has invalid keys: {invalid_keys}")


# Common configuration value factories
def string_config(
    key: str,
    default: str = "",
    description: str = "",
    required: bool = False,
    min_length: int = 0,
    max_length: int = 1000,
    allowed_values: Optional[List[str]] = None,
    pattern: Optional[str] = None
) -> StringConfigValue:
    """Create a string configuration value."""
    return StringConfigValue(
        key=key,
        value=None,
        default=default,
        description=description,
        required=required,
        min_length=min_length,
        max_length=max_length,
        allowed_values=allowed_values,
        pattern=pattern
    )


def int_config(
    key: str,
    default: int = 0,
    description: str = "",
    required: bool = False,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None
) -> IntConfigValue:
    """Create an integer configuration value."""
    return IntConfigValue(
        key=key,
        value=None,
        default=default,
        description=description,
        required=required,
        min_value=min_value,
        max_value=max_value
    )


def bool_config(
    key: str,
    default: bool = False,
    description: str = "",
    required: bool = False
) -> BoolConfigValue:
    """Create a boolean configuration value."""
    return BoolConfigValue(
        key=key,
        value=None,
        default=default,
        description=description,
        required=required
    )


def list_config(
    key: str,
    default: Optional[List[str]] = None,
    description: str = "",
    required: bool = False,
    min_items: int = 0,
    max_items: int = 100,
    allowed_item_values: Optional[List[str]] = None
) -> ListConfigValue:
    """Create a list configuration value."""
    return ListConfigValue(
        key=key,
        value=None,
        default=default or [],
        description=description,
        required=required,
        min_items=min_items,
        max_items=max_items,
        allowed_item_values=allowed_item_values
    )


def dict_config(
    key: str,
    default: Optional[Dict[str, Any]] = None,
    description: str = "",
    required: bool = False,
    required_keys: Optional[List[str]] = None,
    allowed_keys: Optional[List[str]] = None
) -> DictConfigValue:
    """Create a dictionary configuration value."""
    return DictConfigValue(
        key=key,
        value=None,
        default=default or {},
        description=description,
        required=required,
        required_keys=required_keys,
        allowed_keys=allowed_keys
    )
