"""Template name value object.

Provides strong typing and validation for template names."""

import re
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class TemplateName:
    """Strongly-typed template name with validation.
    
    A template name must be:
    - Non-empty string
    - Alphanumeric with hyphens and underscores
    - Between 3-64 characters
    - Not start or end with special characters
    - Follow kebab-case or snake_case conventions
    
    Examples:
        quick-article
        tech-documentation
        blog_post_template
        meeting-notes
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate template name format."""
        if not self.value:
            raise ValueError("Template name cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Template name must be string, got {type(self.value)}")
            
        if len(self.value) < 3:
            raise ValueError("Template name must be at least 3 characters long")
            
        if len(self.value) > 64:
            raise ValueError("Template name must be at most 64 characters long")
            
        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', self.value):
            raise ValueError(
                "Template name must contain only alphanumeric characters, hyphens, "
                "and underscores, and cannot start or end with special characters"
            )
    
    @classmethod
    def from_user_input(cls, name: str) -> Self:
        """Create template name from user input with normalization."""
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
            raise ValueError(f"Template name '{name}' too short after normalization")
            
        # Ensure maximum length
        if len(normalized) > 64:
            normalized = normalized[:64].rstrip('-')
            
        return cls(normalized)
    
    @classmethod
    def from_file_name(cls, filename: str) -> Self:
        """Create template name from filename (removes .yaml extension)."""
        # Remove common template extensions
        for ext in ['.yaml', '.yml', '.json']:
            if filename.lower().endswith(ext):
                filename = filename[:-len(ext)]
                break
        
        return cls.from_user_input(filename)
    
    def to_filename(self, extension: str = 'yaml') -> str:
        """Convert to filename with extension."""
        return f"{self.value}.{extension.lstrip('.')}"
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)
