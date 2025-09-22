"""Workspace name value object.

Provides strong typing and validation for workspace names.
"""

import re
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class WorkspaceName:
    """Strongly-typed workspace name with validation.
    
    A workspace name must be:
    - Non-empty string
    - Alphanumeric with hyphens and underscores
    - Between 3-32 characters
    - Not start or end with special characters
    - Not be reserved names
    
    Examples:
        default
        my-project
        team_workspace
        client-site-v2
    """
    
    value: str
    
    # Reserved workspace names that cannot be used
    RESERVED_NAMES = {
        'admin', 'api', 'app', 'cache', 'config', 'data', 'default',
        'global', 'internal', 'local', 'root', 'system', 'temp', 'test',
        'user', 'workspace', 'writeit'
    }
    
    def __post_init__(self) -> None:
        """Validate workspace name format."""
        if not self.value:
            raise ValueError("Workspace name cannot be empty")
            
        if not isinstance(self.value, str):
            raise TypeError(f"Workspace name must be string, got {type(self.value)}")
            
        if len(self.value) < 3:
            raise ValueError("Workspace name must be at least 3 characters long")
            
        if len(self.value) > 32:
            raise ValueError("Workspace name must be at most 32 characters long")
            
        # Allow alphanumeric, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*[a-zA-Z0-9]$', self.value):
            raise ValueError(
                "Workspace name must contain only alphanumeric characters, hyphens, "
                "and underscores, and cannot start or end with special characters"
            )
            
        # Check reserved names
        if self.value.lower() in self.RESERVED_NAMES:
            raise ValueError(f"Workspace name '{self.value}' is reserved")
    
    @classmethod
    def from_user_input(cls, name: str) -> Self:
        """Create workspace name from user input with normalization."""
        # Normalize input
        normalized = name.strip().lower()
        
        # Replace invalid characters with hyphens
        normalized = re.sub(r'[^a-zA-Z0-9_-]+', '-', normalized)
        
        # Remove multiple consecutive hyphens
        normalized = re.sub(r'-+', '-', normalized)
        
        # Remove leading/trailing hyphens
        normalized = normalized.strip('-')
        
        # Ensure minimum length
        if len(normalized) < 3:
            raise ValueError(f"Workspace name '{name}' too short after normalization")
            
        # Ensure maximum length
        if len(normalized) > 32:
            normalized = normalized[:32].rstrip('-')
            
        return cls(normalized)
    
    @classmethod
    def default(cls) -> Self:
        """Get the default workspace name."""
        return cls("user-default")
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)
