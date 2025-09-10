# ABOUTME: Storage manager for WriteIt with workspace-aware LMDB connections
# ABOUTME: Handles persistent storage of pipelines, artifacts, and state data
import lmdb
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import json
import pickle

class StorageManager:
    """Workspace-aware storage manager for WriteIt data persistence."""
    
    def __init__(self, workspace_manager=None, workspace_name: Optional[str] = None):
        """Initialize storage manager.
        
        Args:
            workspace_manager: Workspace instance for path resolution
            workspace_name: Specific workspace name (defaults to active workspace)
        """
        self.workspace_manager = workspace_manager
        self.workspace_name = workspace_name
        self._connections: Dict[str, lmdb.Environment] = {}
    
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
    def get_connection(self, db_name: str = "main", readonly: bool = False):
        """Get LMDB connection context manager.
        
        Args:
            db_name: Database name
            readonly: Whether to open in read-only mode
            
        Yields:
            LMDB environment
        """
        connection_key = f"{self.workspace_name or 'default'}:{db_name}"
        
        if connection_key not in self._connections:
            db_path = self.get_db_path(db_name)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # LMDB requires the database file to not exist initially
            env = lmdb.open(
                str(db_path),
                map_size=100 * 1024 * 1024,  # 100MB initial size
                max_dbs=10,  # Support multiple named databases
                readonly=readonly
            )
            self._connections[connection_key] = env
        
        yield self._connections[connection_key]
    
    @contextmanager
    def get_transaction(self, db_name: str = "main", write: bool = True, db_key: Optional[str] = None):
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
    
    def store_json(self, key: str, data: Any, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store JSON-serializable data.
        
        Args:
            key: Storage key
            data: Data to store (must be JSON serializable)
            db_name: Database name
            db_key: Sub-database key for organization
        """
        with self.get_transaction(db_name, write=True, db_key=db_key) as (txn, db):
            json_data = json.dumps(data, default=str).encode('utf-8')
            txn.put(key.encode('utf-8'), json_data, db=db)
    
    def load_json(self, key: str, default: Any = None, db_name: str = "main", db_key: Optional[str] = None) -> Any:
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
                data = txn.get(key.encode('utf-8'), db=db)
                if data is None:
                    return default
                return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return default
    
    def store_binary(self, key: str, data: bytes, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store binary data.
        
        Args:
            key: Storage key
            data: Binary data to store
            db_name: Database name
            db_key: Sub-database key
        """
        with self.get_transaction(db_name, write=True, db_key=db_key) as (txn, db):
            txn.put(key.encode('utf-8'), data, db=db)
    
    def load_binary(self, key: str, default: Optional[bytes] = None, db_name: str = "main", db_key: Optional[str] = None) -> Optional[bytes]:
        """Load binary data.
        
        Args:
            key: Storage key
            default: Default value if key not found
            db_name: Database name
            db_key: Sub-database key
            
        Returns:
            Binary data or default
        """
        with self.get_transaction(db_name, write=False, db_key=db_key) as (txn, db):
            return txn.get(key.encode('utf-8'), default, db=db)
    
    def store_object(self, key: str, obj: Any, db_name: str = "main", db_key: Optional[str] = None) -> None:
        """Store Python object using pickle.
        
        Args:
            key: Storage key
            obj: Object to store
            db_name: Database name
            db_key: Sub-database key
        """
        data = pickle.dumps(obj)
        self.store_binary(key, data, db_name, db_key)
    
    def load_object(self, key: str, default: Any = None, db_name: str = "main", db_key: Optional[str] = None) -> Any:
        """Load Python object using pickle.
        
        Args:
            key: Storage key
            default: Default value if key not found
            db_name: Database name
            db_key: Sub-database key
            
        Returns:
            Deserialized object or default
        """
        data = self.load_binary(key, db_name=db_name, db_key=db_key)
        if data is None:
            return default
        
        try:
            return pickle.loads(data)
        except (pickle.PickleError, EOFError):
            return default
    
    def delete(self, key: str, db_name: str = "main", db_key: Optional[str] = None) -> bool:
        """Delete a key.
        
        Args:
            key: Storage key to delete
            db_name: Database name
            db_key: Sub-database key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self.get_transaction(db_name, write=True, db_key=db_key) as (txn, db):
            return txn.delete(key.encode('utf-8'), db=db)
    
    def list_keys(self, prefix: str = "", db_name: str = "main", db_key: Optional[str] = None) -> List[str]:
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
            prefix_bytes = prefix.encode('utf-8') if prefix else b''
            
            if prefix_bytes:
                cursor.set_range(prefix_bytes)
            else:
                cursor.first()
            
            for key, _ in cursor:
                key_str = key.decode('utf-8')
                if not prefix or key_str.startswith(prefix):
                    keys.append(key_str)
                elif prefix and not key_str.startswith(prefix):
                    break  # Keys are sorted, so we can stop early
        
        return keys
    
    def exists(self, key: str, db_name: str = "main", db_key: Optional[str] = None) -> bool:
        """Check if a key exists.
        
        Args:
            key: Storage key to check
            db_name: Database name
            db_key: Sub-database key
            
        Returns:
            True if key exists
        """
        with self.get_transaction(db_name, write=False, db_key=db_key) as (txn, db):
            return txn.get(key.encode('utf-8'), db=db) is not None
    
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
    
    def __del__(self):
        """Cleanup connections on deletion."""
        self.close()


def create_storage_manager(workspace_manager=None, workspace_name: Optional[str] = None) -> StorageManager:
    """Create a storage manager instance.
    
    Args:
        workspace_manager: Workspace manager instance
        workspace_name: Specific workspace name
        
    Returns:
        Configured storage manager
    """
    return StorageManager(workspace_manager, workspace_name)