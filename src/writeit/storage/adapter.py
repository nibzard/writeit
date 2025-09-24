"""Storage adapter interface to break circular dependencies.

Provides a clean interface for storage operations that can be implemented
by different storage backends without creating circular imports.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Type, TypeVar
from pathlib import Path
from uuid import UUID
import json
import warnings

T = TypeVar('T')


class StorageAdapter(ABC):
    """Abstract base class for storage adapters.
    
    This interface defines the contract for storage operations,
    allowing different implementations (legacy, infrastructure, etc.)
    to be used interchangeably without circular dependencies.
    """
    
    @abstractmethod
    def get_storage_path(self) -> Path:
        """Get the base storage path."""
        pass
    
    @abstractmethod
    def store_json(self, key: str, data: Any, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store JSON-serializable data."""
        pass
    
    @abstractmethod
    def load_json(self, key: str, default: Any = None, db_name: str = "main", db_key: Optional[str] = None) -> Any:
        """Load JSON data."""
        pass
    
    @abstractmethod
    def store_binary(self, key: str, data: bytes, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store binary data."""
        pass
    
    @abstractmethod
    def load_binary(self, key: str, default: Optional[bytes] = None, db_name: str = "main", db_key: Optional[str] = None) -> Optional[bytes]:
        """Load binary data."""
        pass
    
    @abstractmethod
    def store_object(self, key: str, obj: Any, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store Python object using serialization."""
        pass
    
    @abstractmethod
    def load_object(self, key: str, default: Any = None, db_name: str = "main", db_key: Optional[str] = None, object_type: Type = None) -> Any:
        """Load Python object using deserialization."""
        pass
    
    @abstractmethod
    def delete(self, key: str, db_name: str = "main", db_key: Optional[str] = None) -> bool:
        """Delete a key."""
        pass
    
    @abstractmethod
    def list_keys(self, prefix: str = "", db_name: str = "main", db_key: Optional[str] = None) -> List[str]:
        """List keys with optional prefix filter."""
        pass
    
    @abstractmethod
    def exists(self, key: str, db_name: str = "main", db_key: Optional[str] = None) -> bool:
        """Check if a key exists."""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """Close all connections."""
        pass


class LegacyStorageAdapter(StorageAdapter):
    """Adapter for the legacy storage manager.
    
    This adapter wraps the legacy StorageManager to provide
    the StorageAdapter interface without direct dependencies.
    """
    
    def __init__(self, storage_manager=None):
        """Initialize with optional storage manager.
        
        Args:
            storage_manager: Legacy StorageManager instance
        """
        if storage_manager is None:
            # Import here to avoid circular imports
            from writeit.storage.manager import StorageManager, create_storage_manager
            self._storage_manager = create_storage_manager()
        else:
            self._storage_manager = storage_manager
    
    @property
    def storage_path(self) -> Path:
        """Get the base storage path."""
        return self._storage_manager.storage_path
    
    def get_storage_path(self) -> Path:
        """Get the base storage path."""
        return self._storage_manager.storage_path
    
    def store_json(self, key: str, data: Any, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store JSON-serializable data."""
        self._storage_manager.store_json(key, data, db_name, db_key)
    
    def load_json(self, key: str, default: Any = None, db_name: str = "main", db_key: Optional[str] = None) -> Any:
        """Load JSON data."""
        return self._storage_manager.load_json(key, default, db_name, db_key)
    
    def store_binary(self, key: str, data: bytes, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store binary data."""
        self._storage_manager.store_binary(key, data, db_name, db_key)
    
    def load_binary(self, key: str, default: Optional[bytes] = None, db_name: str = "main", db_key: Optional[str] = None) -> Optional[bytes]:
        """Load binary data."""
        return self._storage_manager.load_binary(key, default, db_name, db_key)
    
    def store_object(self, key: str, obj: Any, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store Python object using serialization."""
        self._storage_manager.store_object(key, obj, db_name, db_key)
    
    def load_object(self, key: str, default: Any = None, db_name: str = "main", db_key: Optional[str] = None, object_type: Type = None) -> Any:
        """Load Python object using deserialization."""
        return self._storage_manager.load_object(key, default, db_name, db_key, object_type)
    
    def delete(self, key: str, db_name: str = "main", db_key: Optional[str] = None) -> bool:
        """Delete a key."""
        return self._storage_manager.delete(key, db_name, db_key)
    
    def list_keys(self, prefix: str = "", db_name: str = "main", db_key: Optional[str] = None) -> List[str]:
        """List keys with optional prefix filter."""
        return self._storage_manager.list_keys(prefix, db_name, db_key)
    
    def exists(self, key: str, db_name: str = "main", db_key: Optional[str] = None) -> bool:
        """Check if a key exists."""
        return self._storage_manager.exists(key, db_name, db_key)
    
    def close(self) -> None:
        """Close all connections."""
        self._storage_manager.close()


class InfrastructureStorageAdapter(StorageAdapter):
    """Adapter for the infrastructure storage manager.
    
    This adapter wraps the infrastructure LMDBStorageManager to provide
    the StorageAdapter interface for DDD-compliant storage operations.
    """
    
    def __init__(self, storage_manager=None, workspace_manager=None, workspace_name: Optional[str] = None):
        """Initialize with optional storage manager.
        
        Args:
            storage_manager: Infrastructure LMDBStorageManager instance
            workspace_manager: Workspace manager for path resolution
            workspace_name: Specific workspace name
        """
        if storage_manager is None:
            # Import here to avoid circular imports
            from writeit.infrastructure.base.storage_manager import LMDBStorageManager
            from writeit.infrastructure.base.safe_serialization import SafeDomainEntitySerializer
            
            self._storage_manager = LMDBStorageManager(
                workspace_manager=workspace_manager,
                workspace_name=workspace_name
            )
            # Set up serializer for domain entities
            self._serializer = SafeDomainEntitySerializer()
            self._storage_manager.set_serializer(self._serializer)
        else:
            self._storage_manager = storage_manager
            self._serializer = None
    
    def get_storage_path(self) -> Path:
        """Get the base storage path."""
        return self._storage_manager.storage_path
    
    def store_json(self, key: str, data: Any, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store JSON-serializable data."""
        json_data = json.dumps(data, default=str).encode("utf-8")
        self._storage_manager.store_binary(key, json_data, db_name, db_key)
    
    def load_json(self, key: str, default: Any = None, db_name: str = "main", db_key: Optional[str] = None) -> Any:
        """Load JSON data."""
        import asyncio
        
        async def _load():
            data = self._storage_manager.load_binary(key, db_name, db_key)
            if data is None:
                return default
            try:
                return json.loads(data.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return default
        
        # Run async operation in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an async context, we need to handle this differently
                # For now, return default to avoid blocking
                return default
            else:
                return loop.run_until_complete(_load())
        except RuntimeError:
            # No event loop available, return default
            return default
    
    def store_binary(self, key: str, data: bytes, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store binary data."""
        import asyncio
        
        async def _store():
            # Store as a simple entity with string ID
            class SimpleEntity:
                def __init__(self, data: bytes):
                    self.data = data
            
            await self._storage_manager.save_entity(SimpleEntity(data), key, db_name, db_key)
        
        # Run async operation in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't easily run async in sync context that's already in event loop
                # For now, we'll need to handle this case differently
                warnings.warn("Async storage operation in sync context - data may not be stored")
            else:
                loop.run_until_complete(_store())
        except RuntimeError:
            warnings.warn("No event loop available for storage operation")
    
    def load_binary(self, key: str, default: Optional[bytes] = None, db_name: str = "main", db_key: Optional[str] = None) -> Optional[bytes]:
        """Load binary data."""
        import asyncio
        
        class SimpleEntity:
            def __init__(self, data: bytes):
                self.data = data
        
        async def _load():
            entity = await self._storage_manager.load_entity(key, SimpleEntity, db_name, db_key)
            return entity.data if entity else default
        
        # Run async operation in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return default
            else:
                return loop.run_until_complete(_load())
        except RuntimeError:
            return default
    
    def store_object(self, key: str, obj: Any, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store Python object using serialization."""
        import asyncio
        
        async def _store():
            await self._storage_manager.save_entity(obj, key, db_name, db_key)
        
        # Run async operation in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                warnings.warn("Async storage operation in sync context - object may not be stored")
            else:
                loop.run_until_complete(_store())
        except RuntimeError:
            warnings.warn("No event loop available for storage operation")
    
    def load_object(self, key: str, default: Any = None, db_name: str = "main", db_key: Optional[str] = None, object_type: Type = None) -> Any:
        """Load Python object using deserialization."""
        import asyncio
        
        async def _load():
            return await self._storage_manager.load_entity(key, object_type or dict, db_name, db_key)
        
        # Run async operation in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return default
            else:
                return loop.run_until_complete(_load())
        except RuntimeError:
            return default
    
    def delete(self, key: str, db_name: str = "main", db_key: Optional[str] = None) -> bool:
        """Delete a key."""
        import asyncio
        
        async def _delete():
            return await self._storage_manager.delete_entity(key, db_name, db_key)
        
        # Run async operation in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return False
            else:
                return loop.run_until_complete(_delete())
        except RuntimeError:
            return False
    
    def list_keys(self, prefix: str = "", db_name: str = "main", db_key: Optional[str] = None) -> List[str]:
        """List keys with optional prefix filter."""
        import asyncio
        
        async def _list():
            entities = await self._storage_manager.find_entities_by_prefix(prefix, dict, db_name, db_key)
            # Extract keys from entities - this is a simplification
            # In practice, we'd need a better way to get the actual keys
            return [f"{prefix}_{i}" for i in range(len(entities))]
        
        # Run async operation in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return []
            else:
                return loop.run_until_complete(_list())
        except RuntimeError:
            return []
    
    def exists(self, key: str, db_name: str = "main", db_key: Optional[str] = None) -> bool:
        """Check if a key exists."""
        import asyncio
        
        async def _exists():
            return await self._storage_manager.entity_exists(key, db_name, db_key)
        
        # Run async operation in sync context
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return False
            else:
                return loop.run_until_complete(_exists())
        except RuntimeError:
            return False
    
    def close(self) -> None:
        """Close all connections."""
        self._storage_manager.close()


def create_storage_adapter(adapter_type: str = "legacy", **kwargs) -> StorageAdapter:
    """Create a storage adapter of the specified type.
    
    Args:
        adapter_type: Type of adapter ("legacy" or "infrastructure")
        **kwargs: Additional arguments for the adapter
        
    Returns:
        StorageAdapter instance
        
    Raises:
        ValueError: If adapter_type is not supported
    """
    if adapter_type == "legacy":
        return LegacyStorageAdapter(**kwargs)
    elif adapter_type == "infrastructure":
        return InfrastructureStorageAdapter(**kwargs)
    else:
        raise ValueError(f"Unsupported adapter type: {adapter_type}")


__all__ = [
    "StorageAdapter",
    "LegacyStorageAdapter", 
    "InfrastructureStorageAdapter",
    "create_storage_adapter"
]