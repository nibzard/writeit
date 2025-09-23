"""LMDB Storage Abstraction for WriteIt Infrastructure.

Provides high-level LMDB storage operations with transaction management,
connection pooling, schema versioning, and performance optimization.
"""

import lmdb
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, AsyncContextManager, TypeVar, Type
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from threading import RLock
from weakref import WeakValueDictionary

from ..base.exceptions import StorageError, ConnectionError, TransactionError, ValidationError
from ..base.serialization import DomainEntitySerializer

logger = logging.getLogger(__name__)
T = TypeVar('T')


@dataclass
class StorageConfig:
    """Configuration for LMDB storage."""
    
    map_size_mb: int = 500  # Initial map size in MB
    max_dbs: int = 20  # Maximum number of named databases
    max_connections: int = 10  # Connection pool size
    sync: bool = True  # Sync writes to disk
    metasync: bool = True  # Sync metadata to disk
    readonly: bool = False  # Read-only mode
    
    @property
    def map_size_bytes(self) -> int:
        """Get map size in bytes."""
        return self.map_size_mb * 1024 * 1024


@dataclass
class TransactionStats:
    """Statistics for transaction monitoring."""
    
    total_transactions: int = 0
    active_transactions: int = 0
    committed_transactions: int = 0
    aborted_transactions: int = 0
    avg_duration_ms: float = 0.0
    

class ConnectionPool:
    """Connection pool for LMDB environments."""
    
    def __init__(self, storage_path: Path, config: StorageConfig):
        """Initialize connection pool.
        
        Args:
            storage_path: Path to LMDB database directory
            config: Storage configuration
        """
        self.storage_path = storage_path
        self.config = config
        self._pool: List[lmdb.Environment] = []
        self._in_use: WeakValueDictionary = WeakValueDictionary()
        self._lock = RLock()
        self._created_count = 0
        
    def get_environment(self) -> lmdb.Environment:
        """Get an LMDB environment from the pool.
        
        Returns:
            LMDB environment instance
            
        Raises:
            ConnectionError: If environment creation fails
        """
        with self._lock:
            # Try to reuse existing environment
            if self._pool:
                env = self._pool.pop()
                self._in_use[id(env)] = env
                return env
            
            # Create new environment if under limit
            if self._created_count < self.config.max_connections:
                try:
                    env = self._create_environment()
                    self._created_count += 1
                    self._in_use[id(env)] = env
                    return env
                except Exception as e:
                    raise ConnectionError(
                        f"Failed to create LMDB environment at {self.storage_path}",
                        database=str(self.storage_path),
                        cause=e
                    )
            
            # Pool exhausted - create temporary environment
            logger.warning(f"Connection pool exhausted, creating temporary environment")
            try:
                return self._create_environment()
            except Exception as e:
                raise ConnectionError(
                    f"Failed to create temporary LMDB environment",
                    database=str(self.storage_path),
                    cause=e
                )
    
    def return_environment(self, env: lmdb.Environment) -> None:
        """Return an environment to the pool.
        
        Args:
            env: Environment to return
        """
        with self._lock:
            env_id = id(env)
            if env_id in self._in_use:
                del self._in_use[env_id]
                if len(self._pool) < self.config.max_connections:
                    self._pool.append(env)
                else:
                    env.close()
                    self._created_count -= 1
    
    def _create_environment(self) -> lmdb.Environment:
        """Create a new LMDB environment.
        
        Returns:
            New LMDB environment
        """
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        return lmdb.open(
            str(self.storage_path),
            map_size=self.config.map_size_bytes,
            max_dbs=self.config.max_dbs,
            sync=self.config.sync,
            metasync=self.config.metasync,
            readonly=self.config.readonly
        )
    
    def close_all(self) -> None:
        """Close all environments in the pool."""
        with self._lock:
            for env in self._pool:
                env.close()
            self._pool.clear()
            
            for env in self._in_use.values():
                env.close()
            self._in_use.clear()
            
            self._created_count = 0
    
    def get_stats(self) -> Dict[str, int]:
        """Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        with self._lock:
            return {
                'pool_size': len(self._pool),
                'in_use': len(self._in_use),
                'created_total': self._created_count,
                'max_connections': self.config.max_connections
            }


class LMDBStorage:
    """High-level LMDB storage abstraction.
    
    Provides transaction management, connection pooling, and performance monitoring
    for domain entity persistence.
    """
    
    def __init__(
        self,
        storage_path: Path,
        config: Optional[StorageConfig] = None,
        serializer: Optional[DomainEntitySerializer] = None
    ):
        """Initialize LMDB storage.
        
        Args:
            storage_path: Path to storage directory
            config: Storage configuration (uses defaults if None)
            serializer: Entity serializer (creates default if None)
        """
        self.storage_path = storage_path
        self.config = config or StorageConfig()
        self.serializer = serializer or DomainEntitySerializer(prefer_json=True)
        
        self._connection_pool = ConnectionPool(storage_path, self.config)
        self._databases: Dict[str, lmdb._Database] = {}
        self._lock = asyncio.Lock()
        self._stats = TransactionStats()
        self._schema_version = 1
        
        logger.info(f"Initialized LMDB storage at {storage_path}")
    
    async def initialize(self) -> None:
        """Initialize storage and perform any necessary setup.
        
        Raises:
            StorageError: If initialization fails
        """
        try:
            # Ensure storage directory exists
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # Test connection
            async with self.transaction("main", write=False) as (txn, db):
                # Check schema version
                version_key = b"__schema_version__"
                stored_version = txn.get(version_key, db=db)
                
                if stored_version is None:
                    # First initialization - store schema version
                    async with self.transaction("main", write=True) as (write_txn, write_db):
                        write_txn.put(version_key, str(self._schema_version).encode(), db=write_db)
                        logger.info(f"Initialized schema version {self._schema_version}")
                else:
                    stored_version_int = int(stored_version.decode())
                    if stored_version_int != self._schema_version:
                        logger.warning(
                            f"Schema version mismatch: expected {self._schema_version}, "
                            f"found {stored_version_int}"
                        )
                        # TODO: Implement schema migration
            
            logger.info("LMDB storage initialized successfully")
            
        except Exception as e:
            raise StorageError(
                f"Failed to initialize LMDB storage: {e}",
                operation="initialize",
                cause=e
            )
    
    @asynccontextmanager
    async def transaction(
        self,
        db_name: str = "main",
        write: bool = False
    ) -> AsyncContextManager[tuple[lmdb.Transaction, lmdb._Database]]:
        """Create a transaction context manager.
        
        Args:
            db_name: Database name
            write: Whether this is a write transaction
            
        Yields:
            Tuple of (transaction, database)
            
        Raises:
            TransactionError: If transaction fails
        """
        env = None
        txn = None
        start_time = datetime.now()
        
        try:
            # Get environment from pool
            env = self._connection_pool.get_environment()
            
            # Get or create database
            db = await self._get_database(env, db_name)
            
            # Start transaction
            txn = env.begin(write=write)
            self._stats.total_transactions += 1
            self._stats.active_transactions += 1
            
            logger.debug(f"Started {'write' if write else 'read'} transaction on {db_name}")
            
            yield txn, db
            
            # Commit transaction
            if write:
                txn.commit()
                self._stats.committed_transactions += 1
                logger.debug(f"Committed transaction on {db_name}")
            
        except Exception as e:
            # Abort transaction on error
            if txn:
                try:
                    txn.abort()
                    self._stats.aborted_transactions += 1
                    logger.debug(f"Aborted transaction on {db_name} due to error: {e}")
                except:
                    pass
            
            raise TransactionError(
                f"Transaction failed on database {db_name}: {e}",
                cause=e
            )
        
        finally:
            # Update stats
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self._stats.active_transactions -= 1
            
            # Update average duration
            total_completed = self._stats.committed_transactions + self._stats.aborted_transactions
            if total_completed > 0:
                self._stats.avg_duration_ms = (
                    (self._stats.avg_duration_ms * (total_completed - 1) + duration) / total_completed
                )
            
            # Return environment to pool
            if env:
                self._connection_pool.return_environment(env)
    
    async def _get_database(self, env: lmdb.Environment, db_name: str) -> lmdb._Database:
        """Get or create a named database.
        
        Args:
            env: LMDB environment
            db_name: Database name
            
        Returns:
            Database instance
        """
        if db_name not in self._databases:
            async with self._lock:
                if db_name not in self._databases:
                    # Create database
                    self._databases[db_name] = env.open_db(db_name.encode())
                    logger.debug(f"Created database: {db_name}")
        
        return self._databases[db_name]
    
    async def store_entity(
        self,
        entity: T,
        entity_id: str,
        db_name: str = "main"
    ) -> None:
        """Store a domain entity.
        
        Args:
            entity: Entity to store
            entity_id: Unique identifier
            db_name: Database name
            
        Raises:
            StorageError: If storage operation fails
        """
        try:
            # Serialize entity
            serialized_data = self.serializer.serialize(entity)
            
            # Store in database
            async with self.transaction(db_name, write=True) as (txn, db):
                key_bytes = entity_id.encode('utf-8')
                txn.put(key_bytes, serialized_data, db=db)
                
            logger.debug(f"Stored entity {entity_id} in {db_name}")
            
        except Exception as e:
            raise StorageError(
                f"Failed to store entity {entity_id}: {e}",
                operation="store",
                entity_type=type(entity).__name__,
                cause=e
            )
    
    async def load_entity(
        self,
        entity_id: str,
        entity_type: Type[T],
        db_name: str = "main"
    ) -> Optional[T]:
        """Load a domain entity.
        
        Args:
            entity_id: Entity identifier
            entity_type: Expected entity type
            db_name: Database name
            
        Returns:
            Entity instance or None if not found
            
        Raises:
            StorageError: If load operation fails
        """
        try:
            async with self.transaction(db_name, write=False) as (txn, db):
                key_bytes = entity_id.encode('utf-8')
                data = txn.get(key_bytes, db=db)
                
                if data is None:
                    return None
                
                # Deserialize entity
                entity = self.serializer.deserialize(data, entity_type)
                logger.debug(f"Loaded entity {entity_id} from {db_name}")
                return entity
                
        except Exception as e:
            raise StorageError(
                f"Failed to load entity {entity_id}: {e}",
                operation="load",
                entity_type=entity_type.__name__,
                cause=e
            )
    
    async def delete_entity(
        self,
        entity_id: str,
        db_name: str = "main"
    ) -> bool:
        """Delete a domain entity.
        
        Args:
            entity_id: Entity identifier
            db_name: Database name
            
        Returns:
            True if entity was deleted, False if not found
            
        Raises:
            StorageError: If delete operation fails
        """
        try:
            async with self.transaction(db_name, write=True) as (txn, db):
                key_bytes = entity_id.encode('utf-8')
                deleted = txn.delete(key_bytes, db=db)
                
                if deleted:
                    logger.debug(f"Deleted entity {entity_id} from {db_name}")
                
                return deleted
                
        except Exception as e:
            raise StorageError(
                f"Failed to delete entity {entity_id}: {e}",
                operation="delete",
                cause=e
            )
    
    async def entity_exists(
        self,
        entity_id: str,
        db_name: str = "main"
    ) -> bool:
        """Check if an entity exists.
        
        Args:
            entity_id: Entity identifier
            db_name: Database name
            
        Returns:
            True if entity exists, False otherwise
        """
        try:
            async with self.transaction(db_name, write=False) as (txn, db):
                key_bytes = entity_id.encode('utf-8')
                return txn.get(key_bytes, db=db) is not None
                
        except Exception as e:
            raise StorageError(
                f"Failed to check entity existence {entity_id}: {e}",
                operation="exists",
                cause=e
            )
    
    async def find_entities_by_prefix(
        self,
        prefix: str,
        entity_type: Type[T],
        db_name: str = "main",
        limit: Optional[int] = None
    ) -> List[T]:
        """Find entities by key prefix.
        
        Args:
            prefix: Key prefix to search for
            entity_type: Expected entity type
            db_name: Database name
            limit: Maximum number of entities to return
            
        Returns:
            List of matching entities
        """
        try:
            entities = []
            
            async with self.transaction(db_name, write=False) as (txn, db):
                cursor = txn.cursor(db=db)
                prefix_bytes = prefix.encode('utf-8')
                
                if cursor.set_range(prefix_bytes):
                    count = 0
                    for key, value in cursor:
                        if not key.startswith(prefix_bytes):
                            break
                        
                        try:
                            entity = self.serializer.deserialize(value, entity_type)
                            entities.append(entity)
                            count += 1
                            
                            if limit and count >= limit:
                                break
                        except Exception as e:
                            logger.warning(f"Failed to deserialize entity {key}: {e}")
            
            logger.debug(f"Found {len(entities)} entities with prefix '{prefix}' in {db_name}")
            return entities
            
        except Exception as e:
            raise StorageError(
                f"Failed to find entities by prefix {prefix}: {e}",
                operation="find_by_prefix",
                entity_type=entity_type.__name__,
                cause=e
            )
    
    async def count_entities(
        self,
        prefix: str = "",
        db_name: str = "main"
    ) -> int:
        """Count entities with optional prefix filter.
        
        Args:
            prefix: Key prefix to filter by
            db_name: Database name
            
        Returns:
            Number of matching entities
        """
        try:
            count = 0
            
            async with self.transaction(db_name, write=False) as (txn, db):
                if prefix:
                    cursor = txn.cursor(db=db)
                    prefix_bytes = prefix.encode('utf-8')
                    
                    if cursor.set_range(prefix_bytes):
                        for key, _ in cursor:
                            if key.startswith(prefix_bytes):
                                count += 1
                            else:
                                break
                else:
                    # Count all entries
                    count = txn.stat(db)['entries']
            
            return count
            
        except Exception as e:
            raise StorageError(
                f"Failed to count entities: {e}",
                operation="count",
                cause=e
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics.
        
        Returns:
            Dictionary with storage statistics
        """
        pool_stats = self._connection_pool.get_stats()
        
        return {
            'storage_path': str(self.storage_path),
            'schema_version': self._schema_version,
            'config': {
                'map_size_mb': self.config.map_size_mb,
                'max_dbs': self.config.max_dbs,
                'max_connections': self.config.max_connections,
            },
            'transactions': {
                'total': self._stats.total_transactions,
                'active': self._stats.active_transactions,
                'committed': self._stats.committed_transactions,
                'aborted': self._stats.aborted_transactions,
                'avg_duration_ms': self._stats.avg_duration_ms,
            },
            'connections': pool_stats,
            'databases': list(self._databases.keys()),
        }
    
    async def close(self) -> None:
        """Close storage and clean up resources."""
        logger.info("Closing LMDB storage")
        self._connection_pool.close_all()
        self._databases.clear()
    
    def __str__(self) -> str:
        """String representation."""
        return f"LMDBStorage(path={self.storage_path}, databases={len(self._databases)})"
