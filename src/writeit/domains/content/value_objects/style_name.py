"""Style name value object.

Provides strong typing and validation for style primer names."""

import re
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class StyleName:
    """Strongly-typed style primer name with validation.
    
    A style name must be:
    - Non-empty string
    - Alphanumeric with hyphens and underscores
    - Between 3-32 characters
    - Not start or end with special characters
    - Follow kebab-case or snake_case conventions
    
    Examples:
        formal
        casual-blog
        technical-docs
        marketing_copy
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate style name format."""
        if not self.value:
            raise ValueError("Style name cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Style name must be string, got {type(self.value)}")
            
        if len(self.value) < 3:
            raise ValueError("Style name must be at least 3 characters long")
            
        if len(self.value) > 32:
            raise ValueError("Style name must be at most 32 characters long")
            
        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', self.value):
            raise ValueError(
                "Style name must contain only alphanumeric characters, hyphens, "
                "and underscores, and cannot start or end with special characters"
            )
    
    @classmethod
    def from_user_input(cls, name: str) -> Self:
        """Create style name from user input with normalization."""
        # Normalize input
        normalized = name.strip().lower()
        
        # Replace invalid characters with hyphens
        normalized = re.sub(r'[^a-zA-Z0-9_-]+', '-', normalized)
        
        # Remove multiple consecutive hyphens/underscores
        normalized = re.sub(r'[-_]+', '-', normalized)
        
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')
        
        # Ensure minimum length
        if len(normalized) < 3:
            raise ValueError(f"Style name '{name}' too short after normalization")
            
        # Ensure maximum length
        if len(normalized) > 32:
            normalized = normalized[:32].rstrip('-')
            
        return cls(normalized)
    
    @classmethod
    def default(cls) -> Self:
        """Get the default style name."""
        return cls("default")
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)
