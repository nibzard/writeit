"""Storage key value object.

Provides safe and validated storage key handling.
"""

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class StorageKey:
    """Strongly-typed storage key with validation.
    
    Provides:
    - Key validation
    - Safe key operations
    - Type safety
    
    Examples:
        key = StorageKey.from_string("pipeline_run_123")
        key = StorageKey.from_components("pipeline", "run", "123")
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate storage key."""
        if not isinstance(self.value, str):
            raise TypeError(f"Storage key must be string, got {type(self.value)}")
            
        if not self.value:
            raise ValueError("Storage key cannot be empty")
            
        # Check for invalid characters
        invalid_chars = ['\x00', '\n', '\r']
        for char in invalid_chars:
            if char in self.value:
                raise ValueError(f"Invalid character in storage key: {repr(char)}")
    
    @classmethod
    def from_string(cls, key_str: str) -> Self:
        """Create storage key from string."""
        return cls(key_str)
    
    @classmethod
    def from_components(cls, *components: str) -> Self:
        """Create storage key from components."""
        if not components:
            raise ValueError("At least one component is required")
            
        # Join components with separator
        key_str = ":".join(str(comp) for comp in components)
        return cls(key_str)
    
    def starts_with(self, prefix: str) -> bool:
        """Check if key starts with prefix."""
        return self.value.startswith(prefix)
    
    def ends_with(self, suffix: str) -> bool:
        """Check if key ends with suffix."""
        return self.value.endswith(suffix)
    
    def contains(self, substring: str) -> bool:
        """Check if key contains substring."""
        return substring in self.value
    
    def split(self, separator: str = ":") -> list[str]:
        """Split key into components."""
        return self.value.split(separator)
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"StorageKey({self.value!r})"
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)
    
    def __eq__(self, other: object) -> bool:
        """Equality comparison."""
        if isinstance(other, StorageKey):
            return self.value == other.value
        return False


class StorageKeyBuilder:
    """Builder for creating storage keys with consistent patterns."""
    
    @staticmethod
    def pipeline_run(pipeline_id: str, run_id: str) -> StorageKey:
        """Create pipeline run key."""
        return StorageKey.from_components("pipeline", pipeline_id, "run", run_id)
    
    @staticmethod
    def pipeline_template(pipeline_id: str) -> StorageKey:
        """Create pipeline template key."""
        return StorageKey.from_components("pipeline", pipeline_id, "template")
    
    @staticmethod
    def execution_context(execution_id: str) -> StorageKey:
        """Create execution context key."""
        return StorageKey.from_components("execution", execution_id, "context")
    
    @staticmethod
    def cache_entry(cache_key: str) -> StorageKey:
        """Create cache entry key."""
        return StorageKey.from_components("cache", cache_key)
    
    @staticmethod
    def token_usage(workspace_name: str, timestamp: str) -> StorageKey:
        """Create token usage key."""
        return StorageKey.from_components("tokens", workspace_name, timestamp)
    
    @staticmethod
    def artifact(artifact_id: str) -> StorageKey:
        """Create artifact key."""
        return StorageKey.from_components("artifact", artifact_id)
    
    @staticmethod
    def workspace_config(workspace_name: str) -> StorageKey:
        """Create workspace configuration key."""
        return StorageKey.from_components("workspace", workspace_name, "config")