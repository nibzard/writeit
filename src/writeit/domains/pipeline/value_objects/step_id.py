"""Step identifier value object.

Provides strong typing and validation for pipeline step identifiers.
"""

import re
from dataclasses import dataclass
from typing import Self, Optional


@dataclass(frozen=True)
class StepId:
    """Strongly-typed step identifier with validation and hierarchy support.
    
    A step ID must be:
    - Non-empty string
    - Alphanumeric with hyphens and underscores
    - Between 2-32 characters
    - Support hierarchical notation with dots (e.g., "outline.introduction")
    
    Examples:
        outline
        content
        review.grammar
        finalize.export
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate step ID format."""
        if not self.value:
            raise ValueError("Step ID cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Step ID must be string, got {type(self.value)}")
            
        if len(self.value) < 2:
            raise ValueError("Step ID must be at least 2 characters long")
            
        if len(self.value) > 32:
            raise ValueError("Step ID must be at most 32 characters long")
            
        # Allow alphanumeric, hyphens, underscores, and dots for hierarchy
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*[a-zA-Z0-9]$', self.value):
            raise ValueError(
                "Step ID must contain only alphanumeric characters, hyphens, "
                "underscores, and dots, and cannot start or end with special characters"
            )
            
        # Validate no consecutive dots
        if '..' in self.value:
            raise ValueError("Step ID cannot contain consecutive dots")
    
    @classmethod
    def from_name(cls, name: str) -> Self:
        """Create step ID from a human-readable name."""
        # Convert name to valid ID format
        normalized = re.sub(r'[^a-zA-Z0-9.]+', '_', name.strip())
        normalized = normalized.strip('_').lower()
        
        if len(normalized) < 2:
            normalized = f"step_{normalized}"
        elif len(normalized) > 32:
            normalized = normalized[:32].rstrip('_')
            
        return cls(normalized)
    
    @property
    def parent(self) -> Optional[Self]:
        """Get parent step ID if this is hierarchical."""
        if '.' not in self.value:
            return None
        parent_value = '.'.join(self.value.split('.')[:-1])
        return StepId(parent_value)
    
    @property
    def name(self) -> str:
        """Get the name part of hierarchical ID."""
        return self.value.split('.')[-1]
    
    @property
    def is_hierarchical(self) -> bool:
        """Check if this is a hierarchical step ID."""
        return '.' in self.value
    
    @property
    def depth(self) -> int:
        """Get the hierarchy depth (0 for root level)."""
        return self.value.count('.')
    
    def create_child(self, child_name: str) -> Self:
        """Create a child step ID."""
        child_id = f"{self.value}.{child_name}"
        return StepId(child_id)
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)