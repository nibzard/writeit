"""Secure storage wrapper with access control integration.

Provides a secure layer over the storage manager that enforces workspace isolation,
access controls, and security policies.
"""

import asyncio
import warnings
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...storage.manager import StorageManager
from ..base.access_control import (
    AccessLevel, 
    ResourceType, 
    enforce_workspace_access,
    get_access_control_manager,
    AccessRequest,
    WorkspaceAccessDeniedError
)
from ...shared.errors import SecurityError


class SecureStorageError(SecurityError):
    """Secure storage operation error."""
    pass


class SecureStorageManager:
    """Security-enhanced storage manager with access control integration.
    
    This wrapper provides secure access to storage operations while enforcing
    workspace isolation, access controls, and security policies.
    """
    
    def __init__(
        self,
        storage_manager: StorageManager,
        workspace_name: WorkspaceName,
        user_id: Optional[str] = None,
        enforce_isolation: bool = True
    ):
        """Initialize secure storage manager.
        
        Args:
            storage_manager: Underlying storage manager
            workspace_name: Current workspace name
            user_id: User identifier for access tracking
            enforce_isolation: Whether to enforce strict workspace isolation
        """
        self._storage_manager = storage_manager
        self._workspace_name = workspace_name
        self._user_id = user_id
        self._enforce_isolation = enforce_isolation
        self._access_manager = get_access_control_manager()
        
        # Validate workspace name matches storage manager
        if (hasattr(storage_manager, 'workspace_name') and 
            storage_manager.workspace_name and 
            storage_manager.workspace_name != str(workspace_name)):
            raise SecureStorageError(
                f"Workspace name mismatch: secure manager expects '{workspace_name}', "
                f"storage manager has '{storage_manager.workspace_name}'"
            )
    
    async def _check_access(
        self,
        resource_id: str,
        access_level: AccessLevel,
        resource_type: ResourceType = ResourceType.DATABASE
    ) -> None:
        """Check access permissions for a storage operation."""
        if not self._enforce_isolation:
            return
        
        try:
            await enforce_workspace_access(
                workspace_name=self._workspace_name,
                resource_id=resource_id,
                resource_type=resource_type,
                access_level=access_level,
                user_id=self._user_id
            )
        except WorkspaceAccessDeniedError as e:
            raise SecureStorageError(f"Storage access denied: {e}") from e
    
    def _sanitize_key(self, key: str) -> str:
        """Sanitize storage key to prevent path traversal and injection attacks."""
        # Remove dangerous characters and sequences
        sanitized = key.replace("..", "").replace("/", "_").replace("\\", "_")
        
        # Ensure key doesn't start with special characters
        if sanitized.startswith((".", "-", "_")):
            sanitized = "safe" + sanitized
        
        # Limit key length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        # Add workspace prefix for isolation
        return f"{self._workspace_name}_{sanitized}"
    
    def _validate_db_name(self, db_name: str) -> str:
        """Validate and sanitize database name."""
        # Only allow alphanumeric characters and underscores
        if not all(c.isalnum() or c == '_' for c in db_name):
            raise SecureStorageError(f"Invalid database name: '{db_name}'. Only alphanumeric and underscore allowed.")
        
        # Limit length
        if len(db_name) > 50:
            raise SecureStorageError(f"Database name too long: '{db_name}'. Maximum 50 characters.")
        
        return db_name
    
    @asynccontextmanager
    async def _secure_operation(
        self,
        operation_name: str,
        resource_id: str,
        access_level: AccessLevel
    ) -> AsyncGenerator[None, None]:
        """Context manager for secure storage operations."""
        await self._check_access(resource_id, access_level)
        
        try:
            yield
        except Exception as e:
            # Log security-relevant errors
            if "permission" in str(e).lower() or "access" in str(e).lower():
                raise SecureStorageError(f"Security error in {operation_name}: {e}") from e
            raise
    
    async def store_json(
        self,
        key: str,
        data: Any,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> None:
        """Securely store JSON-serializable data."""
        safe_key = self._sanitize_key(key)
        safe_db_name = self._validate_db_name(db_name)
        safe_db_key = self._sanitize_key(db_key) if db_key else None
        
        async with self._secure_operation("store_json", safe_key, AccessLevel.WRITE):
            # Validate data doesn't contain sensitive information
            if await self._contains_sensitive_data(data):
                warnings.warn(
                    f"Potentially sensitive data detected in key '{key}'. "
                    "Consider using encrypted storage for sensitive information.",
                    UserWarning
                )
            
            self._storage_manager.store_json(safe_key, data, safe_db_name, safe_db_key)
    
    async def load_json(
        self,
        key: str,
        default: Any = None,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> Any:
        """Securely load JSON data."""
        safe_key = self._sanitize_key(key)
        safe_db_name = self._validate_db_name(db_name)
        safe_db_key = self._sanitize_key(db_key) if db_key else None
        
        async with self._secure_operation("load_json", safe_key, AccessLevel.READ):
            return self._storage_manager.load_json(safe_key, default, safe_db_name, safe_db_key)
    
    async def store_binary(
        self,
        key: str,
        data: bytes,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> None:
        """Securely store binary data."""
        safe_key = self._sanitize_key(key)
        safe_db_name = self._validate_db_name(db_name)
        safe_db_key = self._sanitize_key(db_key) if db_key else None
        
        # Check binary data size limits
        max_size = 10 * 1024 * 1024  # 10MB limit
        if len(data) > max_size:
            raise SecureStorageError(f"Binary data too large: {len(data)} bytes > {max_size} bytes")
        
        async with self._secure_operation("store_binary", safe_key, AccessLevel.WRITE):
            self._storage_manager.store_binary(safe_key, data, safe_db_name, safe_db_key)
    
    async def load_binary(
        self,
        key: str,
        default: Optional[bytes] = None,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> Optional[bytes]:
        """Securely load binary data."""
        safe_key = self._sanitize_key(key)
        safe_db_name = self._validate_db_name(db_name)
        safe_db_key = self._sanitize_key(db_key) if db_key else None
        
        async with self._secure_operation("load_binary", safe_key, AccessLevel.READ):
            return self._storage_manager.load_binary(safe_key, default, safe_db_name, safe_db_key)
    
    async def store_object(
        self,
        key: str,
        obj: Any,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> None:
        """Securely store Python object using safe serialization."""
        safe_key = self._sanitize_key(key)
        safe_db_name = self._validate_db_name(db_name)
        safe_db_key = self._sanitize_key(db_key) if db_key else None
        
        # Validate object is safe to serialize
        await self._validate_serializable_object(obj)
        
        async with self._secure_operation("store_object", safe_key, AccessLevel.WRITE):
            self._storage_manager.store_object(safe_key, obj, safe_db_name, safe_db_key)
    
    async def load_object(
        self,
        key: str,
        default: Any = None,
        db_name: str = "main",
        db_key: Optional[str] = None,
        object_type: type = None
    ) -> Any:
        """Securely load Python object using safe deserialization."""
        safe_key = self._sanitize_key(key)
        safe_db_name = self._validate_db_name(db_name)
        safe_db_key = self._sanitize_key(db_key) if db_key else None
        
        async with self._secure_operation("load_object", safe_key, AccessLevel.READ):
            return self._storage_manager.load_object(safe_key, default, safe_db_name, safe_db_key, object_type)
    
    async def delete(
        self,
        key: str,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> bool:
        """Securely delete a key."""
        safe_key = self._sanitize_key(key)
        safe_db_name = self._validate_db_name(db_name)
        safe_db_key = self._sanitize_key(db_key) if db_key else None
        
        async with self._secure_operation("delete", safe_key, AccessLevel.WRITE):
            return self._storage_manager.delete(safe_key, safe_db_name, safe_db_key)
    
    async def list_keys(
        self,
        prefix: str = "",
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> List[str]:
        """Securely list keys with optional prefix filter."""
        safe_prefix = self._sanitize_key(prefix) if prefix else f"{self._workspace_name}_"
        safe_db_name = self._validate_db_name(db_name)
        safe_db_key = self._sanitize_key(db_key) if db_key else None
        
        async with self._secure_operation("list_keys", safe_prefix, AccessLevel.READ):
            # Get all keys and filter to only workspace-scoped ones
            all_keys = self._storage_manager.list_keys(safe_prefix, safe_db_name, safe_db_key)
            workspace_prefix = f"{self._workspace_name}_"
            
            # Return keys with workspace prefix removed for cleaner interface
            filtered_keys = []
            for key in all_keys:
                if key.startswith(workspace_prefix):
                    clean_key = key[len(workspace_prefix):]
                    filtered_keys.append(clean_key)
            
            return filtered_keys
    
    async def exists(
        self,
        key: str,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> bool:
        """Securely check if a key exists."""
        safe_key = self._sanitize_key(key)
        safe_db_name = self._validate_db_name(db_name)
        safe_db_key = self._sanitize_key(db_key) if db_key else None
        
        async with self._secure_operation("exists", safe_key, AccessLevel.READ):
            return self._storage_manager.exists(safe_key, safe_db_name, safe_db_key)
    
    async def get_stats(self, db_name: str = "main") -> Dict[str, Any]:
        """Securely get database statistics."""
        safe_db_name = self._validate_db_name(db_name)
        
        async with self._secure_operation("get_stats", safe_db_name, AccessLevel.READ):
            stats = self._storage_manager.get_stats(safe_db_name)
            
            # Add security-relevant statistics
            stats["workspace_name"] = str(self._workspace_name)
            stats["isolation_enforced"] = self._enforce_isolation
            
            return stats
    
    async def _contains_sensitive_data(self, data: Any) -> bool:
        """Check if data potentially contains sensitive information."""
        if isinstance(data, dict):
            # Check for common sensitive field names
            sensitive_keys = {
                'password', 'pass', 'pwd', 'secret', 'token', 'key', 'credential',
                'auth', 'oauth', 'api_key', 'access_token', 'private_key', 'cert'
            }
            
            for key in data.keys():
                if isinstance(key, str) and any(sensitive in key.lower() for sensitive in sensitive_keys):
                    return True
            
            # Recursively check nested data
            for value in data.values():
                if await self._contains_sensitive_data(value):
                    return True
        
        elif isinstance(data, list):
            for item in data:
                if await self._contains_sensitive_data(item):
                    return True
        
        elif isinstance(data, str):
            # Check for patterns that might indicate sensitive data
            if (len(data) > 20 and 
                any(c.isdigit() for c in data) and 
                any(c.isalpha() for c in data) and
                not data.isspace()):
                # Could be a token or key
                return True
        
        return False
    
    async def _validate_serializable_object(self, obj: Any) -> None:
        """Validate object is safe to serialize."""
        # Check for dangerous object types
        dangerous_types = {
            'function', 'method', 'builtin_function_or_method',
            'code', 'frame', 'traceback', 'module'
        }
        
        obj_type = type(obj).__name__
        if obj_type in dangerous_types:
            raise SecureStorageError(f"Cannot serialize dangerous object type: {obj_type}")
        
        # Check for objects with __reduce__ or __getstate__ methods
        if hasattr(obj, '__reduce__') or hasattr(obj, '__getstate__'):
            # These could be used for code execution during deserialization
            warnings.warn(
                f"Object of type {obj_type} has custom serialization methods. "
                "Ensure it's safe for serialization.",
                UserWarning
            )
    
    def get_workspace_name(self) -> WorkspaceName:
        """Get the current workspace name."""
        return self._workspace_name
    
    def get_storage_path(self) -> Path:
        """Get the storage path for the current workspace."""
        return self._storage_manager.storage_path
    
    def is_isolation_enforced(self) -> bool:
        """Check if workspace isolation is enforced."""
        return self._enforce_isolation
    
    async def close(self) -> None:
        """Close the storage manager."""
        self._storage_manager.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


async def create_secure_storage_manager(
    workspace_name: Union[WorkspaceName, str],
    workspace_manager=None,
    user_id: Optional[str] = None,
    enforce_isolation: bool = True,
    map_size_mb: int = 100,
    max_dbs: int = 10
) -> SecureStorageManager:
    """Create a secure storage manager instance.
    
    Args:
        workspace_name: Workspace name
        workspace_manager: Workspace manager instance
        user_id: User identifier for access tracking
        enforce_isolation: Whether to enforce strict workspace isolation
        map_size_mb: Initial LMDB map size in megabytes
        max_dbs: Maximum number of named databases
    
    Returns:
        Configured secure storage manager
    """
    if isinstance(workspace_name, str):
        workspace_name = WorkspaceName(workspace_name)
    
    # Create underlying storage manager
    storage_manager = StorageManager(
        workspace_manager=workspace_manager,
        workspace_name=str(workspace_name),
        map_size_mb=map_size_mb,
        max_dbs=max_dbs
    )
    
    return SecureStorageManager(
        storage_manager=storage_manager,
        workspace_name=workspace_name,
        user_id=user_id,
        enforce_isolation=enforce_isolation
    )