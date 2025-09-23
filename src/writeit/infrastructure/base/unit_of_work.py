"""Unit of Work implementation for LMDB transactions.

Provides atomic transaction management across multiple repositories
ensuring data consistency and proper rollback on failures.
"""

import lmdb
from typing import Dict, Any, Optional, List, Type, TypeVar
from contextlib import asynccontextmanager
import logging

from ...shared.repository import UnitOfWork, UnitOfWorkError, RepositoryError
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from .storage_manager import LMDBStorageManager

logger = logging.getLogger(__name__)
T = TypeVar('T')


class LMDBUnitOfWork(UnitOfWork):
    """LMDB-based Unit of Work for managing transactions.
    
    Coordinates transactions across multiple repositories ensuring
    atomic commits and proper cleanup on failures.
    """
    
    def __init__(
        self, 
        storage_manager: LMDBStorageManager,
        workspace_name: WorkspaceName
    ):
        """Initialize unit of work.
        
        Args:
            storage_manager: LMDB storage manager
            workspace_name: Workspace for transaction isolation
        """
        self._storage = storage_manager
        self._workspace_name = workspace_name
        self._transactions: Dict[str, tuple[lmdb.Transaction, lmdb._Database]] = {}
        self._is_committed = False
        self._is_rolled_back = False
        self._pending_operations: List[dict] = []
        
    async def __aenter__(self) -> 'LMDBUnitOfWork':
        """Enter async context manager."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager with automatic rollback on exceptions."""
        if exc_type is not None:
            # Exception occurred, rollback
            await self.rollback()
        elif not self._is_committed and not self._is_rolled_back:
            # Auto-commit if not explicitly handled
            try:
                await self.commit()
            except Exception as e:
                logger.error(f"Auto-commit failed in UnitOfWork: {e}")
                await self.rollback()
                raise UnitOfWorkError(f"Auto-commit failed: {e}") from e
    
    async def commit(self) -> None:
        """Commit all changes in this unit of work.
        
        Raises:
            UnitOfWorkError: If commit fails
        """
        if self._is_committed:
            raise UnitOfWorkError("Unit of work already committed")
        if self._is_rolled_back:
            raise UnitOfWorkError("Unit of work was rolled back")
            
        try:
            # Execute pending operations
            for operation in self._pending_operations:
                await self._execute_operation(operation)
            
            # Commit all transactions
            for db_name, (txn, db) in self._transactions.items():
                try:
                    txn.commit()
                    logger.debug(f"Committed transaction for database: {db_name}")
                except Exception as e:
                    logger.error(f"Failed to commit transaction for {db_name}: {e}")
                    raise UnitOfWorkError(f"Commit failed for database {db_name}: {e}") from e
            
            self._is_committed = True
            logger.debug(f"Unit of work committed successfully for workspace: {self._workspace_name}")
            
        except Exception as e:
            # Attempt to rollback on commit failure
            await self.rollback()
            raise UnitOfWorkError(f"Commit failed: {e}") from e
        finally:
            self._cleanup()
    
    async def rollback(self) -> None:
        """Rollback all changes in this unit of work.
        
        Raises:
            UnitOfWorkError: If rollback fails
        """
        if self._is_committed:
            raise UnitOfWorkError("Cannot rollback committed unit of work")
        if self._is_rolled_back:
            return  # Already rolled back
            
        try:
            # Abort all transactions
            for db_name, (txn, db) in self._transactions.items():
                try:
                    txn.abort()
                    logger.debug(f"Rolled back transaction for database: {db_name}")
                except Exception as e:
                    logger.warning(f"Failed to rollback transaction for {db_name}: {e}")
                    # Continue with other transactions
            
            self._is_rolled_back = True
            logger.debug(f"Unit of work rolled back for workspace: {self._workspace_name}")
            
        except Exception as e:
            raise UnitOfWorkError(f"Rollback failed: {e}") from e
        finally:
            self._cleanup()
    
    def get_transaction(self, db_name: str = "main", db_key: Optional[str] = None) -> tuple[lmdb.Transaction, lmdb._Database]:
        """Get or create transaction for database.
        
        Args:
            db_name: Database name
            db_key: Sub-database key
            
        Returns:
            Tuple of (transaction, database)
            
        Raises:
            UnitOfWorkError: If transaction creation fails
        """
        if self._is_committed or self._is_rolled_back:
            raise UnitOfWorkError("Unit of work is no longer active")
            
        cache_key = f"{db_name}:{db_key or 'default'}"
        
        if cache_key not in self._transactions:
            try:
                # Create new write transaction
                with self._storage.get_connection(db_name, readonly=False) as env:
                    txn = env.begin(write=True)
                    if db_key:
                        db = env.open_db(db_key.encode(), txn=txn, create=True)
                    else:
                        db = env.open_db(txn=txn, create=True)
                    
                    self._transactions[cache_key] = (txn, db)
                    logger.debug(f"Created transaction for {cache_key}")
                    
            except Exception as e:
                raise UnitOfWorkError(f"Failed to create transaction for {cache_key}: {e}") from e
        
        return self._transactions[cache_key]
    
    async def save_entity(
        self, 
        entity: Any, 
        entity_id: Any, 
        db_name: str = "main", 
        db_key: Optional[str] = None
    ) -> None:
        """Queue entity save operation.
        
        Args:
            entity: Entity to save
            entity_id: Entity identifier
            db_name: Database name
            db_key: Sub-database key
        """
        operation = {
            'type': 'save',
            'entity': entity,
            'entity_id': entity_id,
            'db_name': db_name,
            'db_key': db_key
        }
        self._pending_operations.append(operation)
    
    async def delete_entity(
        self, 
        entity_id: Any, 
        db_name: str = "main", 
        db_key: Optional[str] = None
    ) -> None:
        """Queue entity delete operation.
        
        Args:
            entity_id: Entity identifier
            db_name: Database name
            db_key: Sub-database key
        """
        operation = {
            'type': 'delete',
            'entity_id': entity_id,
            'db_name': db_name,
            'db_key': db_key
        }
        self._pending_operations.append(operation)
    
    async def _execute_operation(self, operation: dict) -> None:
        """Execute a pending operation.
        
        Args:
            operation: Operation dictionary
            
        Raises:
            UnitOfWorkError: If operation execution fails
        """
        try:
            if operation['type'] == 'save':
                await self._execute_save(operation)
            elif operation['type'] == 'delete':
                await self._execute_delete(operation)
            else:
                raise UnitOfWorkError(f"Unknown operation type: {operation['type']}")
                
        except Exception as e:
            raise UnitOfWorkError(f"Failed to execute {operation['type']} operation: {e}") from e
    
    async def _execute_save(self, operation: dict) -> None:
        """Execute save operation.
        
        Args:
            operation: Save operation dictionary
        """
        txn, db = self.get_transaction(operation['db_name'], operation['db_key'])
        
        if not self._storage._serializer:
            raise UnitOfWorkError("No serializer configured")
            
        # Serialize entity
        serialized = self._storage._serializer.serialize(operation['entity'])
        
        # Create storage key
        key_str = self._storage._make_key(operation['entity_id'])
        key_bytes = key_str.encode('utf-8')
        
        # Store in transaction
        txn.put(key_bytes, serialized, db=db)
    
    async def _execute_delete(self, operation: dict) -> None:
        """Execute delete operation.
        
        Args:
            operation: Delete operation dictionary
        """
        txn, db = self.get_transaction(operation['db_name'], operation['db_key'])
        
        # Create storage key
        key_str = self._storage._make_key(operation['entity_id'])
        key_bytes = key_str.encode('utf-8')
        
        # Delete from transaction
        txn.delete(key_bytes, db=db)
    
    def _cleanup(self) -> None:
        """Clean up resources."""
        self._transactions.clear()
        self._pending_operations.clear()
    
    @property
    def is_active(self) -> bool:
        """Check if unit of work is still active."""
        return not (self._is_committed or self._is_rolled_back)
    
    @property
    def workspace_name(self) -> WorkspaceName:
        """Get workspace name for this unit of work."""
        return self._workspace_name
    
    def get_pending_operation_count(self) -> int:
        """Get number of pending operations."""
        return len(self._pending_operations)
    
    def clear_pending_operations(self) -> None:
        """Clear pending operations without executing them."""
        self._pending_operations.clear()


class UnitOfWorkManager:
    """Manager for creating and coordinating units of work."""
    
    def __init__(self, storage_manager: LMDBStorageManager):
        """Initialize manager.
        
        Args:
            storage_manager: LMDB storage manager
        """
        self._storage = storage_manager
        self._active_units: Dict[str, LMDBUnitOfWork] = {}
    
    @asynccontextmanager
    async def create_unit_of_work(self, workspace_name: WorkspaceName):
        """Create a new unit of work.
        
        Args:
            workspace_name: Workspace for transaction isolation
            
        Yields:
            Unit of work instance
        """
        unit_key = f"{workspace_name.value}:{id(self)}"
        
        if unit_key in self._active_units:
            raise UnitOfWorkError(f"Unit of work already active for workspace {workspace_name}")
        
        unit = LMDBUnitOfWork(self._storage, workspace_name)
        self._active_units[unit_key] = unit
        
        try:
            async with unit:
                yield unit
        finally:
            self._active_units.pop(unit_key, None)
    
    def get_active_units(self) -> List[LMDBUnitOfWork]:
        """Get list of active units of work."""
        return list(self._active_units.values())
    
    async def rollback_all(self) -> None:
        """Rollback all active units of work."""
        for unit in self._active_units.values():
            try:
                await unit.rollback()
            except Exception as e:
                logger.error(f"Failed to rollback unit of work: {e}")
        
        self._active_units.clear()
    
    def get_unit_count(self) -> int:
        """Get number of active units of work."""
        return len(self._active_units)