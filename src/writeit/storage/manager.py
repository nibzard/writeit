# ABOUTME: Storage manager for WriteIt with workspace-aware LMDB connections
# ABOUTME: Handles persistent storage of pipelines, artifacts, and state data
import lmdb  # type: ignore
from pathlib import Path
from typing import Optional, Dict, Any, List, Type
from contextlib import contextmanager
import json
import warnings

# Safe serialization - inline implementation to avoid circular imports
from dataclasses import is_dataclass, fields
from datetime import datetime
from uuid import UUID

try:
    import msgpack  # type: ignore
    HAS_MSGPACK = True
except ImportError:
    HAS_MSGPACK = False
    msgpack = None


class SerializationFormat:
    """Supported serialization formats."""
    JSON = "json"
    MSGPACK = "msgpack"


class SimpleSafeSerializer:
    """Simple safe serializer for legacy storage."""
    
    def serialize(self, obj: Any) -> bytes:
        """Serialize object to bytes safely."""
        if isinstance(obj, (str, int, float, bool, type(None))):
            return json.dumps({"__simple__": True, "data": obj}).encode('utf-8')
        elif isinstance(obj, UUID):
            return json.dumps({"__uuid__": str(obj)}).encode('utf-8')
        elif isinstance(obj, datetime):
            return json.dumps({"__datetime__": obj.isoformat()}).encode('utf-8')
        elif is_dataclass(obj):
            data = {}
            for field in fields(obj):
                value = getattr(obj, field.name)
                data[field.name] = self._serialize_value(value)
            return json.dumps({"__dataclass__": type(obj).__name__, "data": data}).encode('utf-8')
        else:
            # Fallback to dict representation
            try:
                data = {}
                for attr in dir(obj):
                    if not attr.startswith('_') and not callable(getattr(obj, attr, None)):
                        try:
                            value = getattr(obj, attr)
                            data[attr] = self._serialize_value(value)
                        except (AttributeError, TypeError):
                            continue
                return json.dumps({"__dict__": data}).encode('utf-8')
            except Exception:
                # Ultimate fallback
                return json.dumps({"__str__": str(obj)}).encode('utf-8')
    
    def deserialize(self, data: bytes, object_type: Optional[Type[Any]] = None) -> Any:
        """Deserialize bytes to object."""
        try:
            json_data = json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        
        if not isinstance(json_data, dict):
            return json_data
        
        if "__simple__" in json_data:
            return json_data["data"]
        elif "__uuid__" in json_data:
            return UUID(json_data["__uuid__"])
        elif "__datetime__" in json_data:
            return datetime.fromisoformat(json_data["__datetime__"])
        elif "__str__" in json_data:
            return json_data["__str__"]
        else:
            # For backward compatibility, return dict
            return json_data
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a single value."""
        if isinstance(value, (str, int, float, bool, type(None))):
            return value
        elif isinstance(value, UUID):
            return {"__uuid__": str(value)}
        elif isinstance(value, datetime):
            return {"__datetime__": value.isoformat()}
        elif is_dataclass(value):
            data = {}
            for field in fields(value):
                data[field.name] = self._serialize_value(getattr(value, field.name))
            return {"__dataclass__": type(value).__name__, "data": data}
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return {"__str__": str(value)}


def create_safe_serializer(format_preference: str = SerializationFormat.JSON, 
                          enable_schema_validation: bool = True, 
                          migration_strategy: Optional[Any] = None) -> SimpleSafeSerializer:
    """Create a safe serializer - simplified version for legacy storage."""
    return SimpleSafeSerializer()


class StorageManager:
    """Workspace-aware storage manager for WriteIt data persistence."""

    def __init__(
        self,
        workspace_manager: Optional[Any] = None,
        workspace_name: Optional[str] = None,
        map_size_mb: int = 100,
        max_dbs: int = 10,
    ) -> None:
        """Initialize storage manager.

        Args:
            workspace_manager: Workspace instance for path resolution
            workspace_name: Specific workspace name (defaults to active workspace)
            map_size_mb: Initial LMDB map size in megabytes (default: 100MB)
            max_dbs: Maximum number of named databases (default: 10)
        """
        self.workspace_manager = workspace_manager
        self.workspace_name = workspace_name
        self.map_size = map_size_mb * 1024 * 1024  # Convert to bytes
        self.max_dbs = max_dbs
        self._connections: Dict[str, lmdb.Environment] = {}
        
        # Initialize safe serializer for binary data
        self._safe_serializer = create_safe_serializer(SerializationFormat.MSGPACK)

    @property
    def storage_path(self) -> Path:
        """Get storage path for the current workspace.

        Returns:
            Path to workspace storage directory
        """
        if self.workspace_manager is None:
            # Fallback to local storage for testing
            return Path.cwd() / ".writeit"

        workspace_path = self.workspace_manager.get_workspace_path(self.workspace_name)
        return workspace_path

    def get_db_path(self, db_name: str) -> Path:
        """Get path for a specific database file.

        Args:
            db_name: Name of the database (e.g., 'artifacts', 'pipelines')

        Returns:
            Path to database file
        """
        return self.storage_path / f"{db_name}.lmdb"

    @contextmanager
    def get_connection(self, db_name: str = "main", readonly: bool = False) -> Any:
        """Get LMDB connection context manager.

        Args:
            db_name: Database name
            readonly: Whether to open in read-only mode

        Yields:
            LMDB environment
        """
        connection_key = f"{self.workspace_name or 'default'}:{db_name}:{readonly}"

        if connection_key not in self._connections:
            db_path = self.get_db_path(db_name)
            db_path.parent.mkdir(parents=True, exist_ok=True)

            # LMDB can't open non-existent databases in readonly mode
            # If database doesn't exist and we need readonly access, create it first
            if readonly and not db_path.exists():
                # Create the database first
                temp_env = lmdb.open(
                    str(db_path),
                    map_size=self.map_size,
                    max_dbs=self.max_dbs,
                    readonly=False,
                )
                temp_env.close()

            env = lmdb.open(
                str(db_path),
                map_size=self.map_size,
                max_dbs=self.max_dbs,
                readonly=readonly,
            )
            self._connections[connection_key] = env

        yield self._connections[connection_key]

    @contextmanager
    def get_transaction(
        self, db_name: str = "main", write: bool = True, db_key: Optional[str] = None
    ) -> Any:
        """Get LMDB transaction context manager.

        Args:
            db_name: Database name
            write: Whether this is a write transaction
            db_key: Specific sub-database key

        Yields:
            Tuple of (transaction, database)
        """
        with self.get_connection(db_name, readonly=not write) as env:
            with env.begin(write=write) as txn:
                if db_key:
                    db = env.open_db(db_key.encode(), txn=txn, create=write)
                else:
                    db = env.open_db(txn=txn, create=write)
                yield txn, db

    def store_json(
        self, key: str, data: Any, db_name: str = "main", db_key: Optional[str] = None
    ) -> None:
        """Store JSON-serializable data.

        Args:
            key: Storage key
            data: Data to store (must be JSON serializable)
            db_name: Database name
            db_key: Sub-database key for organization
        """
        with self.get_transaction(db_name, write=True, db_key=db_key) as (txn, db):
            json_data = json.dumps(data, default=str).encode("utf-8")
            txn.put(key.encode("utf-8"), json_data, db=db)

    def load_json(
        self,
        key: str,
        default: Any = None,
        db_name: str = "main",
        db_key: Optional[str] = None,
    ) -> Any:
        """Load JSON data.

        Args:
            key: Storage key
            default: Default value if key not found
            db_name: Database name
            db_key: Sub-database key

        Returns:
            Deserialized data or default
        """
        try:
            with self.get_transaction(db_name, write=False, db_key=db_key) as (txn, db):
                data = txn.get(key.encode("utf-8"), db=db)
                if data is None:
                    return default
                return json.loads(data.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError, lmdb.Error, OSError):
            return default

    def store_binary(
        self, key: str, data: bytes, db_name: str = "main", db_key: Optional[str] = None
    ) -> None:
        """Store binary data.

        Args:
            key: Storage key
            data: Binary data to store
            db_name: Database name
            db_key: Sub-database key
        """
        with self.get_transaction(db_name, write=True, db_key=db_key) as (txn, db):
            txn.put(key.encode("utf-8"), data, db=db)

    def load_binary(
        self,
        key: str,
        default: Optional[bytes] = None,
        db_name: str = "main",
        db_key: Optional[str] = None,
    ) -> Optional[bytes]:
        """Load binary data.

        Args:
            key: Storage key
            default: Default value if key not found
            db_name: Database name
            db_key: Sub-database key

        Returns:
            Binary data or default
        """
        try:
            with self.get_transaction(db_name, write=False, db_key=db_key) as (txn, db):
                return txn.get(key.encode("utf-8"), default, db=db)
        except (lmdb.Error, OSError):
            return default

    def store_object(
        self, key: str, obj: Any, db_name: str = "main", db_key: Optional[str] = None
    ) -> None:
        """Store Python object using safe serialization.

        Args:
            key: Storage key
            obj: Object to store
            db_name: Database name
            db_key: Sub-database key
        """
        try:
            data = self._safe_serializer.serialize(obj)
            self.store_binary(key, data, db_name, db_key)
        except Exception as e:
            # Log warning and try to use a fallback method
            warnings.warn(
                f"Failed to serialize object {type(obj).__name__} with safe serializer: {e}. "
                "This may indicate the object is not compatible with safe serialization.",
                RuntimeWarning
            )
            raise

    def load_object(
        self,
        key: str,
        default: Any = None,
        db_name: str = "main",
        db_key: Optional[str] = None,
        object_type: Optional[type] = None,
    ) -> Any:
        """Load Python object using safe deserialization.

        Args:
            key: Storage key
            default: Default value if key not found
            db_name: Database name
            db_key: Sub-database key
            object_type: Expected object type for validation

        Returns:
            Deserialized object or default
        """
        try:
            data = self.load_binary(key, db_name=db_name, db_key=db_key)
            if data is None:
                return default

            # Check for legacy pickle format and reject it
            if data.startswith(b'\x80\x03') or data.startswith(b'\x80\x04') or data.startswith(b'PICKLE:'):
                warnings.warn(
                    f"Legacy pickle data detected for key '{key}'. "
                    "This data cannot be loaded for security reasons. "
                    "Please regenerate or migrate the data.",
                    RuntimeWarning
                )
                return default

            # Use safe deserializer
            if object_type:
                return self._safe_serializer.deserialize(data, object_type)
            else:
                # For backward compatibility, try to deserialize as dict
                return self._safe_serializer.deserialize(data, dict)
        except Exception as e:
            warnings.warn(
                f"Failed to deserialize object for key '{key}': {e}. "
                "Returning default value.",
                RuntimeWarning
            )
            return default

    def delete(
        self, key: str, db_name: str = "main", db_key: Optional[str] = None
    ) -> bool:
        """Delete a key.

        Args:
            key: Storage key to delete
            db_name: Database name
            db_key: Sub-database key

        Returns:
            True if key was deleted, False if not found
        """
        with self.get_transaction(db_name, write=True, db_key=db_key) as (txn, db):
            return txn.delete(key.encode("utf-8"), db=db)

    def list_keys(
        self, prefix: str = "", db_name: str = "main", db_key: Optional[str] = None
    ) -> List[str]:
        """List keys with optional prefix filter.

        Args:
            prefix: Key prefix to filter by
            db_name: Database name
            db_key: Sub-database key

        Returns:
            List of matching keys
        """
        keys = []
        with self.get_transaction(db_name, write=False, db_key=db_key) as (txn, db):
            cursor = txn.cursor(db=db)
            prefix_bytes = prefix.encode("utf-8") if prefix else b""

            if prefix_bytes:
                cursor.set_range(prefix_bytes)
            else:
                cursor.first()

            for key, _ in cursor:
                key_str = key.decode("utf-8")
                if not prefix or key_str.startswith(prefix):
                    keys.append(key_str)
                elif prefix and not key_str.startswith(prefix):
                    break  # Keys are sorted, so we can stop early

        return keys

    def exists(
        self, key: str, db_name: str = "main", db_key: Optional[str] = None
    ) -> bool:
        """Check if a key exists.

        Args:
            key: Storage key to check
            db_name: Database name
            db_key: Sub-database key

        Returns:
            True if key exists
        """
        with self.get_transaction(db_name, write=False, db_key=db_key) as (txn, db):
            return txn.get(key.encode("utf-8"), db=db) is not None

    def get_stats(self, db_name: str = "main") -> Dict[str, Any]:
        """Get database statistics.

        Args:
            db_name: Database name

        Returns:
            Dictionary with database statistics
        """
        with self.get_connection(db_name) as env:
            with env.begin() as txn:
                stats = txn.stat()
                return {
                    "entries": stats.get("entries", 0),
                    "page_size": stats.get("psize", 0),
                    "depth": stats.get("depth", 0),
                    "branch_pages": stats.get("branch_pages", 0),
                    "leaf_pages": stats.get("leaf_pages", 0),
                    "overflow_pages": stats.get("overflow_pages", 0),
                }

    def close(self) -> None:
        """Close all connections."""
        for env in self._connections.values():
            env.close()
        self._connections.clear()

    def __del__(self) -> None:
        """Cleanup connections on deletion."""
        self.close()


def create_storage_manager(
    workspace_manager: Optional[Any] = None, workspace_name: Optional[str] = None
) -> StorageManager:
    """Create a storage manager instance.

    Args:
        workspace_manager: Workspace manager instance
        workspace_name: Specific workspace name

    Returns:
        Configured storage manager
    """
    return StorageManager(workspace_manager, workspace_name)
