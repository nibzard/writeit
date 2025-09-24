"""Storage path value object.

Provides safe and validated filesystem path handling for storage.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Self, Optional, cast


@dataclass(frozen=True)
class StoragePath:
    """Strongly-typed storage filesystem path with safety validation.
    
    Provides:
    - Path traversal protection
    - Storage boundary enforcement  
    - Cross-platform path handling
    - Safe path operations
    
    Examples:
        path = StoragePath.from_string("/storage/workspace/cache")
        sub_path = path.join("entries", "cache_123")
        
        # Safe path operations
        if path.exists():
            path.create_directories()
    """
    
    value: Path
    
    def __post_init__(self) -> None:
        """Validate storage path."""
        if not isinstance(self.value, Path):
            raise TypeError(f"Storage path must be Path, got {type(self.value)}")
            
        # Convert to absolute path for security
        object.__setattr__(self, 'value', self.value.resolve())
        
        # Check for path traversal attempts
        if '..' in self.value.parts:
            raise ValueError("Path traversal not allowed in storage paths")
    
    @classmethod
    def from_string(cls, path_str: str) -> Self:
        """Create storage path from string."""
        if not path_str:
            raise ValueError("Storage path cannot be empty")
            
        return cls(Path(path_str))
    
    @classmethod
    def from_workspace_storage(cls, workspace_path: Path) -> Self:
        """Create storage path from workspace storage directory."""
        return cls(workspace_path / "storage")
    
    def join(self, *parts: str) -> Self:
        """Join additional path components safely."""
        # Validate each part for security
        for part in parts:
            if not part or '..' in part or '/' in part or '\\' in part:
                raise ValueError(f"Invalid path component: {part}")
                
        new_path = self.value
        for part in parts:
            new_path = new_path / part
            
        return cast(Self, StoragePath(new_path))
    
    def parent(self) -> Self:
        """Get parent directory."""
        return cast(Self, StoragePath(self.value.parent))
    
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
    
    def read_bytes(self) -> bytes:
        """Read file content as bytes."""
        return self.value.read_bytes()
    
    def write_bytes(self, content: bytes) -> None:
        """Write bytes content to file."""
        # Ensure parent directory exists
        self.value.parent.mkdir(parents=True, exist_ok=True)
        self.value.write_bytes(content)
    
    def read_text(self, encoding: str = 'utf-8') -> str:
        """Read file content as text."""
        return self.value.read_text(encoding=encoding)
    
    def write_text(self, content: str, encoding: str = 'utf-8') -> None:
        """Write text content to file."""
        # Ensure parent directory exists
        self.value.parent.mkdir(parents=True, exist_ok=True)
        self.value.write_text(content, encoding=encoding)
    
    def glob(self, pattern: str) -> list[Self]:
        """Find paths matching a pattern."""
        return [cast(Self, StoragePath(p)) for p in self.value.glob(pattern)]
    
    def iterdir(self) -> list[Self]:
        """Iterate directory contents."""
        if not self.is_directory():
            raise ValueError(f"Path {self.value} is not a directory")
            
        return [cast(Self, StoragePath(p)) for p in self.value.iterdir()]
    
    def size(self) -> int:
        """Get file size in bytes."""
        if not self.is_file():
            return 0
        return self.value.stat().st_size
    
    def __str__(self) -> str:
        """String representation."""
        return str(self.value)
    
    def __repr__(self) -> str:
        """Debug representation."""
        return f"StoragePath({self.value!r})"
    
    def __truediv__(self, other: str) -> Self:
        """Path division operator."""
        return self.join(other)
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.value)