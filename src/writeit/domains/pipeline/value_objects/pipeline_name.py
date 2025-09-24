"""Pipeline name value object.

Provides strong typing and validation for pipeline names."""

import re
from dataclasses import dataclass
from typing import Self, Any


@dataclass(frozen=True)
class PipelineName:
    """Strongly-typed pipeline name with validation and normalization.
    
    A pipeline name must be:
    - Non-empty string
    - Between 3-100 characters
    - Human-readable and descriptive
    - No leading/trailing whitespace
    
    Examples:
        "Article Generator"
        "Code Documentation Pipeline"
        "Quick Content Creator"
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate pipeline name format."""
        if not self.value:
            raise ValueError("Pipeline name cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Pipeline name must be string, got {type(self.value)}")
            
        # Normalize whitespace
        normalized = self.value.strip()
        if normalized != self.value:
            object.__setattr__(self, 'value', normalized)
            
        if len(self.value) < 3:
            raise ValueError("Pipeline name must be at least 3 characters long")
            
        if len(self.value) > 100:
            raise ValueError("Pipeline name must be at most 100 characters long")
            
        # Allow letters, numbers, spaces, and common punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_.,()&!?:;]+$', self.value):
            raise ValueError(
                "Pipeline name must contain only letters, numbers, spaces, "
                "and common punctuation (- _ . , ( ) & ! ? : ;)"
            )
            
        # Must start and end with alphanumeric
        if not re.match(r'^[a-zA-Z0-9].*[a-zA-Z0-9]$', self.value):
            if len(self.value) == 1 and self.value.isalnum():
                pass  # Single character alphanumeric is OK
            else:
                raise ValueError(
                    "Pipeline name must start and end with letters or numbers"
                )
    
    @classmethod
    def from_string(cls, name: str) -> Self:
        """Create pipeline name from string with normalization."""
        # Basic normalization
        normalized = ' '.join(name.strip().split())
        return cls(normalized)
    
    @classmethod
    def from_template(cls, template: str, **kwargs: Any) -> Self:
        """Create pipeline name from template with substitution.
        
        Args:
            template: String template (e.g., "{type} Pipeline")
            **kwargs: Variables for substitution
            
        Returns:
            New pipeline name
        """
        try:
            name = template.format(**kwargs)
            return cls.from_string(name)
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def to_id_format(self) -> str:
        """Convert to pipeline ID format (lowercase, hyphens)."""
        # Convert to lowercase and replace spaces/punctuation with hyphens
        id_format = re.sub(r'[^a-zA-Z0-9]+', '-', self.value.lower())
        id_format = id_format.strip('-')
        return id_format
    
    def is_descriptive(self) -> bool:
        """Check if name is descriptive (has multiple words)."""
        words = self.value.split()
        return len(words) >= 2
    
    def get_word_count(self) -> int:
        """Get number of words in the name."""
        return len(self.value.split())
    
    def starts_with(self, prefix: str) -> bool:
        """Check if name starts with given prefix (case-insensitive)."""
        return self.value.lower().startswith(prefix.lower())
    
    def contains(self, text: str) -> bool:
        """Check if name contains given text (case-insensitive)."""
        return text.lower() in self.value.lower()
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __len__(self) -> int:
        """Name length."""
        return len(self.value)
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)