"""Workspace path value object.

Provides safe and validated filesystem path handling for workspaces.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self, Optional, cast


@dataclass(frozen=True)
class WorkspacePath:
    """Strongly-typed workspace filesystem path with safety validation.
    
    Provides:
    - Path traversal protection
    - Workspace boundary enforcement  
    - Cross-platform path handling
    - Safe path operations
    
    Examples:
        path = WorkspacePath.from_workspace_root("/home/user/.writeit/workspaces/my-project")
        sub_path = path.join("templates", "article.yaml")
        
        # Safe path operations
        if path.exists():
            path.create_directories()
    """
    
    value: Path
    
    def __post_init__(self) -> None:
        """Validate workspace path."""
        if not isinstance(self.value, Path):
            raise TypeError(f"Workspace path must be Path, got {type(self.value)}")
            
        # Convert to absolute path for security
        object.__setattr__(self, 'value', self.value.resolve())
        
        # Check for path traversal attempts
        if '..' in self.value.parts:
            raise ValueError("Path traversal not allowed in workspace paths")
    
    @classmethod
    def from_string(cls, path_str: str) -> Self:
        """Create workspace path from string."""
        if not path_str:
            raise ValueError("Workspace path cannot be empty")
            
        return cls(Path(path_str))
    
    @classmethod
    def from_workspace_root(cls, workspace_root: str) -> Self:
        """Create workspace path from workspace root directory."""
        return cls(Path(workspace_root))
    
    @classmethod
    def home_directory(cls) -> Self:
        """Get the user's home directory workspace path."""
        return cls(Path.home() / ".writeit")
    
    def join(self, *parts: str) -> Self:
        """Join additional path components safely."""
        # Validate each part for security
        for part in parts:
            if not part or '..' in part or '/' in part or '\\' in part:
                raise ValueError(f"Invalid path component: {part}")
                
        new_path = self.value
        for part in parts:
            new_path = new_path / part
            
        return cast(Self, WorkspacePath(new_path))
    
    def parent(self) -> Self:
        """Get parent directory."""
        return cast(Self, WorkspacePath(self.value.parent))
    
    def name(self) -> str:
        """Get the final path component name."""
        return self.value.name
    
    def stem(self) -> str:
        """Get the final path component without suffix."""
        return self.value.stem
    
    def suffix(self) -> str:
        """Get the file suffix."""
        return self.value.suffix
    
    def exists(self) -> bool:
        """Check if path exists."""
        return self.value.exists()
    
    def is_file(self) -> bool:
        """Check if path is a file."""
        return self.value.is_file()
    
    def is_directory(self) -> bool:
        """Check if path is a directory."""
        return self.value.is_dir()
    
    def create_directories(self, mode: int = 0o755, exist_ok: bool = True) -> None:
        """Create directories safely."""
        self.value.mkdir(parents=True, exist_ok=exist_ok, mode=mode)
    
    def read_text(self, encoding: str = 'utf-8') -> str:
        """Read file content as text."""
        return self.value.read_text(encoding=encoding)
    
    def write_text(self, content: str, encoding: str = 'utf-8') -> None:
        """Write text content to file."""
        # Ensure parent directory exists
        self.value.parent.mkdir(parents=True, exist_ok=True)
        self.value.write_text(content, encoding=encoding)
    
    def relative_to(self, other: Self) -> Optional[Path]:
        """Get relative path from another workspace path."""
        try:
            return self.value.relative_to(other.value)
        except ValueError:
            return None
    
    def is_within(self, workspace_root: Self) -> bool:
        """Check if this path is within the workspace root."""
        try:
            self.value.relative_to(workspace_root.value)
            return True
        except ValueError:
            return False
    
    def glob(self, pattern: str) -> list[Self]:
        """Find paths matching a pattern."""
        return [cast(Self, WorkspacePath(p)) for p in self.value.glob(pattern)]
    
    def iterdir(self) -> list[Self]:
        """Iterate directory contents."""
        if not self.is_directory():
            raise ValueError(f"Path {self.value} is not a directory")
            
        return [cast(Self, WorkspacePath(p)) for p in self.value.iterdir()]
    
    def __str__(self) -> str:
        """String representation."""
        return str(self.value)
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"WorkspacePath({self.value!r})"
    
    def __truediv__(self, other: str) -> Self:
        """Path division operator."""
        return self.join(other)
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)
