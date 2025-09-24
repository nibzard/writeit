Independent LMDB Storage Manager for Infrastructure Layer.

Self-contained storage manager that provides LMDB functionality
specifically for the infrastructure layer without dependencies on legacy storage.
"""

import lmdb
from pathlib import Path
from typing import Optional, Dict, Any, List, AsyncContextManager, Type, TypeVar
from contextlib import asynccontextmanager, contextmanager
from uuid import UUID
import json
import warnings
from datetime import datetime

from ...shared.repository import RepositoryError, EntityNotFoundError, EntityAlreadyExistsError
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from .safe_serialization import SafeDomainEntitySerializer, SerializationFormat

T = TypeVar('T')


class LMDBStorageManager:
    """Independent LMDB storage manager for infrastructure layer.
    
    Self-contained storage manager with:
    - Domain entity serialization/deserialization 
    - Async transaction management
    - Repository-specific error handling
    - Workspace isolation for multi-tenancy
    - Independent LMDB implementation
    """
    
    def __init__(
        self,
        workspace_manager=None,
        workspace_name: Optional[str] = None,
        map_size_mb: int = 500,  # Increased default for domain entities
        max_dbs: int = 20,  # More databases for domain separation
    ):
        """Initialize independent storage manager.
        
        Args:
            workspace_manager: Workspace instance for path resolution
            workspace_name: Specific workspace name (defaults to active workspace)
            map_size_mb: Initial LMDB map size in megabytes (default: 500)
            max_dbs: Maximum number of named databases (default: 20)
        """
        self.workspace_manager = workspace_manager
        self.workspace_name = workspace_name
        self.map_size = map_size_mb * 1024 * 1024  # Convert to bytes
        self.max_dbs = max_dbs
        self._connections: Dict[str, lmdb.Environment] = {}
        self._serializer = None

    def set_serializer(self, serializer: 'DomainEntitySerializer') -> None:
        """Set the domain entity serializer."""
        self._serializer = serializer

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
    ):
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

    def close(self) -> None:
        """Close all connections."""
        for env in self._connections.values():
            env.close()
        self._connections.clear()

    def __del__(self):
        """Cleanup connections on deletion."""
        self.close()

    @asynccontextmanager
    async def transaction(
        self, 
        db_name: str = "main", 
        write: bool = True, 
        db_key: Optional[str] = None
    ) -> AsyncContextManager[tuple[lmdb.Transaction, lmdb._Database]]:
        """Async transaction context manager.
        
        Args:
            db_name: Database name
            write: Whether this is a write transaction
            db_key: Specific sub-database key
            
        Yields:
            Tuple of (transaction, database)
            
        Raises:
            RepositoryError: If transaction fails
        """
        try:
            with self.get_transaction(db_name, write, db_key) as (txn, db):
                yield txn, db
        except lmdb.Error as e:
            raise RepositoryError(f"LMDB transaction failed: {e}") from e
        except Exception as e:
            raise RepositoryError(f"Transaction error: {e}") from e

    async def save_entity(
        self, 
        entity: T, 
        entity_id: Any,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> None:
        """Save a domain entity with proper serialization.
        
        Args:
            entity: Domain entity to save
            entity_id: Unique identifier for the entity
            db_name: Database name
            db_key: Sub-database key
            
        Raises:
            RepositoryError: If save operation fails
        """
        if not self._serializer:
            raise RepositoryError("No serializer configured")
            
        try:
            serialized = self._serializer.serialize(entity)
            async with self.transaction(db_name, write=True, db_key=db_key) as (txn, db):
                key_bytes = self._make_key(entity_id).encode('utf-8')
                txn.put(key_bytes, serialized, db=db)
        except Exception as e:
            raise RepositoryError(f"Failed to save entity {entity_id}: {e}") from e

    async def load_entity(
        self, 
        entity_id: Any,
        entity_type: Type[T],
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> Optional[T]:
        """Load a domain entity with proper deserialization.
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity to deserialize to
            db_name: Database name
            db_key: Sub-database key
            
        Returns:
            Deserialized entity or None if not found
            
        Raises:
            RepositoryError: If load operation fails
        """
        if not self._serializer:
            raise RepositoryError("No serializer configured")
            
        try:
            async with self.transaction(db_name, write=False, db_key=db_key) as (txn, db):
                key_bytes = self._make_key(entity_id).encode('utf-8')
                data = txn.get(key_bytes, db=db)
                
                if data is None:
                    return None
                    
                return self._serializer.deserialize(data, entity_type)
        except Exception as e:
            raise RepositoryError(f"Failed to load entity {entity_id}: {e}") from e

    async def entity_exists(
        self, 
        entity_id: Any,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> bool:
        """Check if an entity exists.
        
        Args:
            entity_id: Unique identifier for the entity
            db_name: Database name
            db_key: Sub-database key
            
        Returns:
            True if entity exists, False otherwise
            
        Raises:
            RepositoryError: If existence check fails
        """
        try:
            async with self.transaction(db_name, write=False, db_key=db_key) as (txn, db):
                key_bytes = self._make_key(entity_id).encode('utf-8')
                return txn.get(key_bytes, db=db) is not None
        except Exception as e:
            raise RepositoryError(f"Failed to check entity existence {entity_id}: {e}") from e

    async def delete_entity(
        self, 
        entity_id: Any,
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> bool:
        """Delete an entity by ID.
        
        Args:
            entity_id: Unique identifier for the entity
            db_name: Database name
            db_key: Sub-database key
            
        Returns:
            True if entity was deleted, False if not found
            
        Raises:
            RepositoryError: If delete operation fails
        """
        try:
            async with self.transaction(db_name, write=True, db_key=db_key) as (txn, db):
                key_bytes = self._make_key(entity_id).encode('utf-8')
                return txn.delete(key_bytes, db=db)
        except Exception as e:
            raise RepositoryError(f"Failed to delete entity {entity_id}: {e}") from e

    async def find_entities_by_prefix(
        self, 
        prefix: str,
        entity_type: Type[T],
        db_name: str = "main",
        db_key: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[T]:
        """Find entities by key prefix.
        
        Args:
            prefix: Key prefix to search for
            entity_type: Type of entity to deserialize to
            db_name: Database name
            db_key: Sub-database key
            limit: Maximum number of entities to return
            
        Returns:
            List of matching entities
            
        Raises:
            RepositoryError: If query operation fails
        """
        if not self._serializer:
            raise RepositoryError("No serializer configured")
            
        try:
            entities = []
            async with self.transaction(db_name, write=False, db_key=db_key) as (txn, db):
                cursor = txn.cursor(db=db)
                prefix_bytes = prefix.encode('utf-8')
                
                if cursor.set_range(prefix_bytes):
                    count = 0
                    for key, value in cursor:
                        if not key.startswith(prefix_bytes):
                            break
                            
                        try:
                            entity = self._serializer.deserialize(value, entity_type)
                            entities.append(entity)
                            count += 1
                            
                            if limit and count >= limit:
                                break
                        except Exception as e:
                            # Log deserialization error but continue
                            print(f"Warning: Failed to deserialize entity {key}: {e}")
                            
            return entities
        except Exception as e:
            raise RepositoryError(f"Failed to find entities by prefix {prefix}: {e}") from e

    async def count_entities(
        self, 
        prefix: str = "",
        db_name: str = "main",
        db_key: Optional[str] = None
    ) -> int:
        """Count entities with optional prefix filter.
        
        Args:
            prefix: Key prefix to filter by
            db_name: Database name
            db_key: Sub-database key
            
        Returns:
            Number of matching entities
            
        Raises:
            RepositoryError: If count operation fails
        """
        try:
            count = 0
            async with self.transaction(db_name, write=False, db_key=db_key) as (txn, db):
                cursor = txn.cursor(db=db)
                prefix_bytes = prefix.encode('utf-8') if prefix else b""
                
                if prefix_bytes:
                    if cursor.set_range(prefix_bytes):
                        for key, _ in cursor:
                            if key.startswith(prefix_bytes):
                                count += 1
                            else:
                                break
                else:
                    count = txn.stat(db)['entries']
                    
            return count
        except Exception as e:
            raise RepositoryError(f"Failed to count entities: {e}") from e


    def _make_key(self, entity_id: Any) -> str:
        if isinstance(entity_id, UUID):
            return str(entity_id)
        elif hasattr(entity_id, 'value'):
            return str(entity_id.value)
        else:
            return str(entity_id)

    def get_workspace_storage_path(self, workspace: WorkspaceName) -> Path:
        if self.workspace_manager is None:
            return Path.cwd() / ".writeit" / "workspaces" / workspace.value
        return self.workspace_manager.get_workspace_path(workspace.value)
