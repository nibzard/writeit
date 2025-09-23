"""File system access control for WriteIt.

Provides secure file system operations with workspace isolation,
path validation, and access controls.
"""

import os
import stat
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from contextlib import contextmanager

from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.errors import SecurityError


class FileAccessError(SecurityError):
    """File access security error."""
    pass


class PathTraversalError(FileAccessError):
    """Path traversal attack detected."""
    pass


class FilePermissionError(FileAccessError):
    """File permission error."""
    pass


class FileSizeError(FileAccessError):
    """File size limit exceeded."""
    pass


class FileAccessController:
    """Controls secure file system access within workspace boundaries."""
    
    # Dangerous file extensions that should not be executed or written
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js', '.jar',
        '.msi', '.dll', '.so', '.dylib', '.app', '.deb', '.rpm', '.dmg'
    }
    
    # Safe file extensions for templates and content
    SAFE_EXTENSIONS = {
        '.yaml', '.yml', '.json', '.txt', '.md', '.html', '.css', '.xml',
        '.csv', '.tsv', '.log', '.cfg', '.ini', '.conf', '.py', '.js', '.ts'
    }
    
    # Maximum file sizes by type (in bytes)
    MAX_FILE_SIZES = {
        'template': 1024 * 1024,      # 1MB for templates
        'content': 10 * 1024 * 1024,  # 10MB for generated content
        'config': 100 * 1024,         # 100KB for config files
        'log': 50 * 1024 * 1024,      # 50MB for log files
        'default': 5 * 1024 * 1024,   # 5MB default
    }
    
    def __init__(self, workspace_name: WorkspaceName, workspace_root: Path):
        """Initialize file access controller.
        
        Args:
            workspace_name: Name of the workspace
            workspace_root: Root directory of the workspace
        """
        self.workspace_name = workspace_name
        self.workspace_root = workspace_root.resolve()
        self._ensure_workspace_directory()
    
    def _ensure_workspace_directory(self) -> None:
        """Ensure workspace directory exists and has proper permissions."""
        try:
            self.workspace_root.mkdir(parents=True, exist_ok=True)
            
            # Set secure permissions (owner read/write/execute only)
            if hasattr(os, 'chmod'):
                os.chmod(self.workspace_root, stat.S_IRWXU)
                
        except (OSError, PermissionError) as e:
            raise FileAccessError(f"Cannot create workspace directory '{self.workspace_root}': {e}")
    
    def validate_path(self, file_path: Union[str, Path], operation: str = "access") -> Path:
        """Validate that a file path is safe and within workspace boundaries.
        
        Args:
            file_path: Path to validate
            operation: Type of operation (access, read, write, create, delete)
            
        Returns:
            Validated absolute path
            
        Raises:
            PathTraversalError: If path attempts to escape workspace
            FileAccessError: If path is invalid or unsafe
        """
        try:
            # Convert to Path object and resolve
            path = Path(file_path).resolve()
            
            # Check for path traversal attacks
            try:
                path.relative_to(self.workspace_root)
            except ValueError:
                raise PathTraversalError(
                    f"Path '{file_path}' attempts to access outside workspace '{self.workspace_root}'"
                )
            
            # Check for dangerous path components
            self._check_dangerous_path_components(path)
            
            # Check file extension safety
            if operation in ('write', 'create'):
                self._validate_file_extension(path)
            
            return path
            
        except (OSError, ValueError) as e:
            raise FileAccessError(f"Invalid file path '{file_path}': {e}")
    
    def _check_dangerous_path_components(self, path: Path) -> None:
        """Check for dangerous path components."""
        dangerous_components = {
            '.ssh', '.gnupg', '.aws', '.config', '.local', '.cache',
            'bin', 'sbin', 'usr', 'etc', 'var', 'proc', 'sys', 'dev'
        }
        
        for part in path.parts:
            if part in dangerous_components:
                raise FileAccessError(f"Access to dangerous directory '{part}' not allowed")
            
            # Check for hidden files that might be sensitive
            if part.startswith('.') and len(part) > 1:
                if part not in {'.writeit', '.git', '.gitignore', '.gitattributes'}:
                    # Allow common development files but block others
                    pass
    
    def _validate_file_extension(self, path: Path) -> None:
        """Validate file extension is safe for writing."""
        suffix = path.suffix.lower()
        
        if suffix in self.DANGEROUS_EXTENSIONS:
            raise FileAccessError(f"Cannot write file with dangerous extension: {suffix}")
    
    def check_file_size_limit(self, file_path: Path, file_type: str = 'default') -> None:
        """Check if file size is within limits.
        
        Args:
            file_path: Path to check
            file_type: Type of file (template, content, config, log, default)
            
        Raises:
            FileSizeError: If file exceeds size limit
        """
        if not file_path.exists():
            return
        
        try:
            file_size = file_path.stat().st_size
            max_size = self.MAX_FILE_SIZES.get(file_type, self.MAX_FILE_SIZES['default'])
            
            if file_size > max_size:
                raise FileSizeError(
                    f"File '{file_path}' size {file_size} bytes exceeds limit {max_size} bytes for type '{file_type}'"
                )
                
        except OSError as e:
            raise FileAccessError(f"Cannot check file size for '{file_path}': {e}")
    
    @contextmanager
    def secure_open(
        self,
        file_path: Union[str, Path],
        mode: str = 'r',
        file_type: str = 'default',
        encoding: Optional[str] = None,
        **kwargs
    ):
        """Secure file opening with access control.
        
        Args:
            file_path: Path to file
            mode: File mode ('r', 'w', 'a', etc.)
            file_type: Type of file for size limits
            encoding: Text encoding (defaults to utf-8 for text files)
            **kwargs: Additional arguments for open()
            
        Yields:
            File object
            
        Raises:
            FileAccessError: If access is denied
            FileSizeError: If file size limits are exceeded
            PathTraversalError: If path is outside workspace
        """
        # Determine operation type from mode
        if 'w' in mode or 'a' in mode or '+' in mode:
            operation = 'write'
        else:
            operation = 'read'
        
        # Validate path
        safe_path = self.validate_path(file_path, operation)
        
        # Check size limits for existing files
        if safe_path.exists():
            self.check_file_size_limit(safe_path, file_type)
        
        # Set default encoding for text modes
        if 'b' not in mode and encoding is None:
            encoding = 'utf-8'
        
        try:
            # Open file with validated path
            with open(safe_path, mode, encoding=encoding, **kwargs) as f:
                yield f
                
                # Check size limits after writing
                if operation == 'write':
                    self.check_file_size_limit(safe_path, file_type)
                    
        except (OSError, PermissionError) as e:
            raise FilePermissionError(f"Cannot {operation} file '{safe_path}': {e}")
    
    def secure_read_text(
        self,
        file_path: Union[str, Path],
        encoding: str = 'utf-8',
        file_type: str = 'default'
    ) -> str:
        """Securely read text file content.
        
        Args:
            file_path: Path to file
            encoding: Text encoding
            file_type: Type of file for size limits
            
        Returns:
            File content as string
        """
        with self.secure_open(file_path, 'r', file_type, encoding) as f:
            return f.read()
    
    def secure_write_text(
        self,
        file_path: Union[str, Path],
        content: str,
        encoding: str = 'utf-8',
        file_type: str = 'default'
    ) -> None:
        """Securely write text file content.
        
        Args:
            file_path: Path to file
            content: Content to write
            encoding: Text encoding
            file_type: Type of file for size limits
        """
        # Check content size before writing
        content_bytes = content.encode(encoding)
        max_size = self.MAX_FILE_SIZES.get(file_type, self.MAX_FILE_SIZES['default'])
        
        if len(content_bytes) > max_size:
            raise FileSizeError(
                f"Content size {len(content_bytes)} bytes exceeds limit {max_size} bytes for type '{file_type}'"
            )
        
        with self.secure_open(file_path, 'w', file_type, encoding) as f:
            f.write(content)
    
    def secure_read_binary(
        self,
        file_path: Union[str, Path],
        file_type: str = 'default'
    ) -> bytes:
        """Securely read binary file content.
        
        Args:
            file_path: Path to file
            file_type: Type of file for size limits
            
        Returns:
            File content as bytes
        """
        with self.secure_open(file_path, 'rb', file_type) as f:
            return f.read()
    
    def secure_write_binary(
        self,
        file_path: Union[str, Path],
        content: bytes,
        file_type: str = 'default'
    ) -> None:
        """Securely write binary file content.
        
        Args:
            file_path: Path to file
            content: Content to write
            file_type: Type of file for size limits
        """
        max_size = self.MAX_FILE_SIZES.get(file_type, self.MAX_FILE_SIZES['default'])
        
        if len(content) > max_size:
            raise FileSizeError(
                f"Content size {len(content)} bytes exceeds limit {max_size} bytes for type '{file_type}'"
            )
        
        with self.secure_open(file_path, 'wb', file_type) as f:
            f.write(content)
    
    def secure_list_directory(
        self,
        directory_path: Union[str, Path] = None,
        include_hidden: bool = False,
        file_types: Optional[Set[str]] = None
    ) -> List[Path]:
        """Securely list directory contents.
        
        Args:
            directory_path: Directory to list (defaults to workspace root)
            include_hidden: Whether to include hidden files
            file_types: Set of file extensions to include (e.g., {'.yaml', '.json'})
            
        Returns:
            List of file paths
        """
        if directory_path is None:
            directory_path = self.workspace_root
        
        safe_path = self.validate_path(directory_path, 'read')
        
        if not safe_path.is_dir():
            raise FileAccessError(f"Path '{safe_path}' is not a directory")
        
        try:
            files = []
            for item in safe_path.iterdir():
                # Skip hidden files unless requested
                if not include_hidden and item.name.startswith('.'):
                    continue
                
                # Filter by file types if specified
                if file_types and item.is_file():
                    if item.suffix.lower() not in file_types:
                        continue
                
                files.append(item)
            
            return sorted(files)
            
        except (OSError, PermissionError) as e:
            raise FilePermissionError(f"Cannot list directory '{safe_path}': {e}")
    
    def secure_create_directory(
        self,
        directory_path: Union[str, Path],
        parents: bool = True,
        exist_ok: bool = True
    ) -> Path:
        """Securely create directory.
        
        Args:
            directory_path: Directory to create
            parents: Whether to create parent directories
            exist_ok: Whether to ignore if directory already exists
            
        Returns:
            Created directory path
        """
        safe_path = self.validate_path(directory_path, 'create')
        
        try:
            safe_path.mkdir(parents=parents, exist_ok=exist_ok)
            
            # Set secure permissions
            if hasattr(os, 'chmod'):
                os.chmod(safe_path, stat.S_IRWXU)
            
            return safe_path
            
        except (OSError, PermissionError) as e:
            raise FilePermissionError(f"Cannot create directory '{safe_path}': {e}")
    
    def secure_delete_file(self, file_path: Union[str, Path]) -> None:
        """Securely delete file.
        
        Args:
            file_path: File to delete
        """
        safe_path = self.validate_path(file_path, 'delete')
        
        if not safe_path.exists():
            return  # Already deleted
        
        if safe_path.is_dir():
            raise FileAccessError(f"Cannot delete directory '{safe_path}' with delete_file. Use delete_directory.")
        
        try:
            safe_path.unlink()
        except (OSError, PermissionError) as e:
            raise FilePermissionError(f"Cannot delete file '{safe_path}': {e}")
    
    def secure_delete_directory(
        self,
        directory_path: Union[str, Path],
        recursive: bool = False
    ) -> None:
        """Securely delete directory.
        
        Args:
            directory_path: Directory to delete
            recursive: Whether to delete recursively
        """
        safe_path = self.validate_path(directory_path, 'delete')
        
        if not safe_path.exists():
            return  # Already deleted
        
        if not safe_path.is_dir():
            raise FileAccessError(f"Path '{safe_path}' is not a directory")
        
        # Prevent deletion of workspace root
        if safe_path == self.workspace_root:
            raise FileAccessError("Cannot delete workspace root directory")
        
        try:
            if recursive:
                import shutil
                shutil.rmtree(safe_path)
            else:
                safe_path.rmdir()
        except (OSError, PermissionError) as e:
            raise FilePermissionError(f"Cannot delete directory '{safe_path}': {e}")
    
    def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if file exists within workspace.
        
        Args:
            file_path: File path to check
            
        Returns:
            True if file exists
        """
        try:
            safe_path = self.validate_path(file_path, 'access')
            return safe_path.exists()
        except (FileAccessError, PathTraversalError):
            return False
    
    def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get file information.
        
        Args:
            file_path: File path
            
        Returns:
            Dictionary with file information
        """
        safe_path = self.validate_path(file_path, 'read')
        
        if not safe_path.exists():
            raise FileAccessError(f"File '{safe_path}' does not exist")
        
        try:
            stat_info = safe_path.stat()
            
            return {
                'path': str(safe_path),
                'name': safe_path.name,
                'size': stat_info.st_size,
                'is_file': safe_path.is_file(),
                'is_directory': safe_path.is_dir(),
                'modified_time': stat_info.st_mtime,
                'created_time': getattr(stat_info, 'st_birthtime', stat_info.st_ctime),
                'permissions': oct(stat_info.st_mode)[-3:],
                'extension': safe_path.suffix.lower(),
                'workspace_relative': str(safe_path.relative_to(self.workspace_root))
            }
            
        except (OSError, ValueError) as e:
            raise FileAccessError(f"Cannot get file info for '{safe_path}': {e}")
    
    def get_workspace_root(self) -> Path:
        """Get workspace root directory."""
        return self.workspace_root
    
    def get_workspace_name(self) -> WorkspaceName:
        """Get workspace name."""
        return self.workspace_name


def create_file_access_controller(
    workspace_name: Union[WorkspaceName, str],
    workspace_root: Union[str, Path]
) -> FileAccessController:
    """Create a file access controller.
    
    Args:
        workspace_name: Name of the workspace
        workspace_root: Root directory of the workspace
        
    Returns:
        Configured file access controller
    """
    if isinstance(workspace_name, str):
        workspace_name = WorkspaceName(workspace_name)
    
    if isinstance(workspace_root, str):
        workspace_root = Path(workspace_root)
    
    return FileAccessController(workspace_name, workspace_root)