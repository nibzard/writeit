"""Base repository implementation using LMDB storage.

Provides common functionality for all domain repositories including
CRUD operations, specification queries, and workspace isolation.
"""

from typing import List, Optional, Type, TypeVar, Any, cast
from abc import ABC, abstractmethod

from ...shared.repository import Repository, WorkspaceAwareRepository, Specification, RepositoryError, EntityNotFoundError
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from .storage_manager import LMDBStorageManager
from .serialization import DomainEntitySerializer

T = TypeVar('T')


class LMDBRepositoryBase(WorkspaceAwareRepository[T], ABC):
    """Base implementation for LMDB-backed repositories.
    
    Provides common CRUD operations with workspace isolation,
    specification-based queries, and proper error handling.
    """
    
    def __init__(
        self, 
        storage_manager: LMDBStorageManager,
        workspace_name: WorkspaceName,
        entity_type: Type[T],
        db_name: str = "main",
        db_key: Optional[str] = None
    ):
        """Initialize repository with storage configuration.
        
        Args:
            storage_manager: LMDB storage manager instance
            workspace_name: Workspace for data isolation
            entity_type: Type of entities this repository handles
            db_name: LMDB database name
            db_key: Sub-database key for organization
        """
        super().__init__(workspace_name)
        self._storage = storage_manager
        self._entity_type = entity_type
        self._db_name = db_name
        self._db_key = db_key
        
        # Ensure serializer is configured
        if not self._storage._serializer:
            serializer = DomainEntitySerializer()
            self._setup_serializer(serializer)
            self._storage.set_serializer(serializer)
    
    @abstractmethod
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with domain-specific types.
        
        Args:
            serializer: Serializer to configure
        """
        pass
    
    @abstractmethod
    def _get_entity_id(self, entity: T) -> Any:
        """Extract entity ID for storage key.
        
        Args:
            entity: Entity to get ID from
            
        Returns:
            Entity identifier
        """
        pass
    
    @abstractmethod
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID.
        
        Args:
            entity_id: Entity identifier
            
        Returns:
            Storage key string
        """
        pass
    
    async def save(self, entity: T) -> None:
        """Save or update an entity.
        
        Args:
            entity: The entity to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        entity_id = self._get_entity_id(entity)
        await self._storage.save_entity(
            entity, 
            entity_id, 
            self._db_name, 
            self._db_key
        )
    
    async def find_by_id(self, entity_id: Any) -> Optional[T]:
        """Find entity by its unique identifier.
        
        Args:
            entity_id: The unique identifier
            
        Returns:
            The entity if found, None otherwise
            
        Raises:
            RepositoryError: If lookup operation fails
        """
        return await self._storage.load_entity(
            entity_id,
            self._entity_type,
            self._db_name,
            self._db_key
        )
    
    async def find_all(self) -> List[T]:
        """Find all entities in current workspace.
        
        Returns:
            List of all entities, empty list if none found
            
        Raises:
            RepositoryError: If query operation fails
        """
        prefix = self._get_workspace_prefix()
        return await self._storage.find_entities_by_prefix(
            prefix,
            self._entity_type,
            self._db_name,
            self._db_key
        )
    
    async def find_by_specification(self, spec: Specification[T]) -> List[T]:
        """Find entities matching a specification.
        
        Args:
            spec: The specification to match against
            
        Returns:
            List of matching entities, empty list if none found
            
        Raises:
            RepositoryError: If query operation fails
        """
        # Load all entities and filter in memory
        # For large datasets, consider implementing database-level filtering
        all_entities = await self.find_all()
        return [entity for entity in all_entities if spec.is_satisfied_by(entity)]
    
    async def exists(self, entity_id: Any) -> bool:
        """Check if entity exists by ID.
        
        Args:
            entity_id: The unique identifier
            
        Returns:
            True if entity exists, False otherwise
            
        Raises:
            RepositoryError: If existence check fails
        """
        return await self._storage.entity_exists(
            entity_id,
            self._db_name,
            self._db_key
        )
    
    async def delete(self, entity: T) -> None:
        """Delete an entity.
        
        Args:
            entity: The entity to delete
            
        Raises:
            RepositoryError: If delete operation fails
        """
        entity_id = self._get_entity_id(entity)
        success = await self.delete_by_id(entity_id)
        if not success:
            raise EntityNotFoundError(self._entity_type.__name__, entity_id)
    
    async def delete_by_id(self, entity_id: Any) -> bool:
        """Delete entity by ID.
        
        Args:
            entity_id: The unique identifier
            
        Returns:
            True if entity was deleted, False if not found
            
        Raises:
            RepositoryError: If delete operation fails
        """
        return await self._storage.delete_entity(
            entity_id,
            self._db_name,
            self._db_key
        )
    
    async def count(self) -> int:
        """Count total number of entities in current workspace.
        
        Returns:
            Total count of entities
            
        Raises:
            RepositoryError: If count operation fails
        """
        prefix = self._get_workspace_prefix()
        return await self._storage.count_entities(
            prefix,
            self._db_name,
            self._db_key
        )
    
    async def _find_by_workspace_impl(self, workspace: WorkspaceName) -> List[T]:
        """Implementation-specific workspace query.
        
        Args:
            workspace: Workspace to search in
            
        Returns:
            List of entities in the workspace
        """
        prefix = self._make_workspace_prefix(workspace)
        return await self._storage.find_entities_by_prefix(
            prefix,
            self._entity_type,
            self._db_name,
            self._db_key
        )
    
    def _get_workspace_prefix(self) -> str:
        """Get key prefix for current workspace.
        
        Returns:
            Workspace key prefix
        """
        return self._make_workspace_prefix(self.workspace_name)
    
    def _make_workspace_prefix(self, workspace: WorkspaceName) -> str:
        """Create key prefix for workspace isolation.
        
        Args:
            workspace: Workspace name
            
        Returns:
            Key prefix for workspace
        """
        return f"ws:{workspace.value}:"
    
    async def find_with_limit(self, limit: int, offset: int = 0) -> List[T]:
        """Find entities with pagination.
        
        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            
        Returns:
            List of entities
            
        Raises:
            RepositoryError: If query operation fails
        """
        prefix = self._get_workspace_prefix()
        entities = await self._storage.find_entities_by_prefix(
            prefix,
            self._entity_type,
            self._db_name,
            self._db_key,
            limit + offset  # Load more than needed to handle offset
        )
        return entities[offset:offset + limit]
    
    async def find_by_field_value(self, field_name: str, value: Any) -> List[T]:
        """Find entities by field value.
        
        Note: This performs an in-memory scan. For large datasets,
        consider adding field-specific indexes.
        
        Args:
            field_name: Name of field to search
            value: Value to match
            
        Returns:
            List of matching entities
        """
        all_entities = await self.find_all()
        return [
            entity for entity in all_entities 
            if hasattr(entity, field_name) and getattr(entity, field_name) == value
        ]
    
    async def batch_save(self, entities: List[T]) -> None:
        """Save multiple entities in batch.
        
        Args:
            entities: List of entities to save
            
        Raises:
            RepositoryError: If batch save fails
        """
        for entity in entities:
            await self.save(entity)
    
    async def batch_delete(self, entity_ids: List[Any]) -> int:
        """Delete multiple entities by ID.
        
        Args:
            entity_ids: List of entity IDs to delete
            
        Returns:
            Number of entities actually deleted
            
        Raises:
            RepositoryError: If batch delete fails
        """
        deleted_count = 0
        for entity_id in entity_ids:
            if await self.delete_by_id(entity_id):
                deleted_count += 1
        return deleted_count


class LMDBSpecificationRepository(LMDBRepositoryBase[T]):
    """Enhanced repository with advanced specification support.
    
    Provides optimized specification queries for common patterns.
    """
    
    async def find_by_and_specification(self, *specs: Specification[T]) -> List[T]:
        """Find entities matching all specifications (AND).
        
        Args:
            specs: Specifications to combine with AND
            
        Returns:
            List of matching entities
        """
        if not specs:
            return await self.find_all()
            
        combined_spec = specs[0]
        for spec in specs[1:]:
            combined_spec = combined_spec & spec
            
        return await self.find_by_specification(combined_spec)
    
    async def find_by_or_specification(self, *specs: Specification[T]) -> List[T]:
        """Find entities matching any specification (OR).
        
        Args:
            specs: Specifications to combine with OR
            
        Returns:
            List of matching entities
        """
        if not specs:
            return []
            
        combined_spec = specs[0]
        for spec in specs[1:]:
            combined_spec = combined_spec | spec
            
        return await self.find_by_specification(combined_spec)
    
    async def count_by_specification(self, spec: Specification[T]) -> int:
        """Count entities matching a specification.
        
        Args:
            spec: The specification to count against
            
        Returns:
            Number of matching entities
        """
        matching_entities = await self.find_by_specification(spec)
        return len(matching_entities)