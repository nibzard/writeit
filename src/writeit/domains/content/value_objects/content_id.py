"""Content ID value object.

Provides strong typing and validation for content identifiers."""

import uuid
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class ContentId:
    """Strongly-typed content identifier.
    
    A content ID uniquely identifies generated content within the system.
    It's used to track content across different stages (generation, validation,
    formatting, storage) and provides correlation for content lifecycle events.
    
    Examples:
        content_id = ContentId.generate()
        content_id = ContentId.from_string("123e4567-e89b-12d3-a456-426614174000")
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate content ID format."""
        if not self.value:
            raise ValueError("Content ID cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Content ID must be string, got {type(self.value)}")
            
        # Validate UUID format
        try:
            uuid.UUID(self.value)
        except ValueError as e:
            raise ValueError(f"Content ID must be a valid UUID: {e}")
    
    @classmethod
    def generate(cls) -> Self:
        """Generate a new unique content ID."""
        return cls(str(uuid.uuid4()))
    
    @classmethod
    def from_string(cls, content_id: str) -> Self:
        """Create content ID from string with validation."""
        return cls(content_id.strip())
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)
