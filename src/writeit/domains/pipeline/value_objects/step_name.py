"""Step name value object.

Provides strong typing and validation for pipeline step names."""

import re
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class StepName:
    """Strongly-typed step name with validation and normalization.
    
    A step name must be:
    - Non-empty string
    - Between 2-50 characters
    - Human-readable and descriptive
    - No leading/trailing whitespace
    
    Examples:
        "Create Outline"
        "Generate Content"
        "Review & Edit"
        "Finalize"
    """
    
    value: str
    
    def __post_init__(self) -> None:
        """Validate step name format."""
        if not self.value:
            raise ValueError("Step name cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Step name must be string, got {type(self.value)}")
            
        # Normalize whitespace
        normalized = self.value.strip()
        if normalized != self.value:
            object.__setattr__(self, 'value', normalized)
            
        if len(self.value) < 2:
            raise ValueError("Step name must be at least 2 characters long")
            
        if len(self.value) > 50:
            raise ValueError("Step name must be at most 50 characters long")
            
        # Allow letters, numbers, spaces, and common punctuation
        if not re.match(r'^[a-zA-Z0-9\s\-_.,()&!?:;]+$', self.value):
            raise ValueError(
                "Step name must contain only letters, numbers, spaces, "
                "and common punctuation (- _ . , ( ) & ! ? : ;)"
            )
            
        # Must start and end with alphanumeric
        if not re.match(r'^[a-zA-Z0-9].*[a-zA-Z0-9]$', self.value):
            if len(self.value) == 1 and self.value.isalnum():
                pass  # Single character alphanumeric is OK
            else:
                raise ValueError(
                    "Step name must start and end with letters or numbers"
                )
    
    @classmethod
    def from_string(cls, name: str) -> Self:
        """Create step name from string with normalization."""
        # Basic normalization
        normalized = ' '.join(name.strip().split())
        return cls(normalized)
    
    @classmethod
    def from_action(cls, action: str, object_name: str = "") -> Self:
        """Create step name from action and optional object.
        
        Args:
            action: Action verb (e.g., "Create", "Generate", "Review")
            object_name: Optional object name (e.g., "Outline", "Content")
            
        Returns:
            New step name
        """
        if object_name:
            name = f"{action} {object_name}"
        else:
            name = action
        return cls.from_string(name)
    
    def to_id_format(self) -> str:
        """Convert to step ID format (lowercase, underscores)."""
        # Convert to lowercase and replace spaces/punctuation with underscores
        id_format = re.sub(r'[^a-zA-Z0-9]+', '_', self.value.lower())
        id_format = id_format.strip('_')
        return id_format
    
    def is_descriptive(self) -> bool:
        """Check if name is descriptive (has multiple words)."""
        words = self.value.split()
        return len(words) >= 2
    
    def get_word_count(self) -> int:
        """Get number of words in the name."""
        return len(self.value.split())
    
    def starts_with_verb(self) -> bool:
        """Check if name starts with an action verb."""
        common_verbs = {
            'create', 'generate', 'build', 'make', 'write', 'compose',
            'review', 'edit', 'revise', 'update', 'modify', 'improve',
            'analyze', 'check', 'validate', 'verify', 'test',
            'format', 'transform', 'convert', 'process',
            'finalize', 'complete', 'finish', 'export', 'save'
        }
        first_word = self.value.split()[0].lower()
        return first_word in common_verbs
    
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