"""Pipeline identifier value object.

Provides strong typing and validation for pipeline identifiers.
"""

import re
import uuid
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class PipelineId:
    """Strongly-typed pipeline identifier with validation.
    
    A pipeline ID must be:
    - Non-empty string
    - Alphanumeric with hyphens and underscores
    - Between 3-64 characters
    - Not start or end with special characters
    
    Examples:
        pipeline-123
        user_content_generator
        quick-article-v2
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate pipeline ID format."""
        if not self.value:
            raise ValueError("Pipeline ID cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Pipeline ID must be string, got {type(self.value)}")
            
        if len(self.value) < 3:
            raise ValueError("Pipeline ID must be at least 3 characters long")
            
        if len(self.value) > 64:
            raise ValueError("Pipeline ID must be at most 64 characters long")
            
        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', self.value):
            raise ValueError(
                "Pipeline ID must contain only alphanumeric characters, hyphens, "
                "and underscores, and cannot start or end with special characters"
            )
    
    @classmethod
    def generate(cls) -> Self:
        """Generate a new random pipeline ID."""
        return cls(f"pipeline-{uuid.uuid4().hex[:8]}")
    
    @classmethod
    def from_name(cls, name: str) -> Self:
        """Create pipeline ID from a human-readable name."""
        # Convert name to valid ID format
        normalized = re.sub(r'[^a-zA-Z0-9]+', '-', name.strip())
        normalized = normalized.strip('-').lower()
        
        if len(normalized) < 3:
            normalized = f"pipeline-{normalized}"
        elif len(normalized) > 64:
            normalized = normalized[:64].rstrip('-')
            
        return cls(normalized)
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)