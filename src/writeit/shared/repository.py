"""Base repository interfaces and patterns for domain-driven design.

Provides common repository patterns including:
- Generic repository interface with CRUD operations
- Specification pattern for composable queries
- Unit of Work pattern for transaction management
- Workspace-aware repository base class
"""

from abc import ABC, abstractmethod
from typing import Any, Generic, List, Optional, Protocol, TypeVar
from uuid import UUID

from ..domains.workspace.value_objects.workspace_name import WorkspaceName


T = TypeVar('T')
SpecType = TypeVar('SpecType')


class Specification(Generic[SpecType], ABC):
    """Base specification pattern for composable query building.
    
    Allows building complex queries through composition:
    spec = ByWorkspace(workspace) & ByStatus("active") | ByName("test")
    """
    
    @abstractmethod
    def is_satisfied_by(self, entity: SpecType) -> bool:
        """Check if entity satisfies this specification."""
        pass
    
    def __and__(self, other: 'Specification[SpecType]') -> 'Specification[SpecType]':
        """Logical AND composition."""
        return AndSpecification(self, other)
    
    def __or__(self, other: 'Specification[SpecType]') -> 'Specification[SpecType]':
        """Logical OR composition."""
        return OrSpecification(self, other)
    
    def __invert__(self) -> 'Specification[SpecType]':
        """Logical NOT composition."""
        return NotSpecification(self)


class AndSpecification(Specification[SpecType]):
    """Logical AND of two specifications."""
    
    def __init__(self, left: Specification[SpecType], right: Specification[SpecType]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: SpecType) -> bool:
        return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)


class OrSpecification(Specification[SpecType]):
    """Logical OR of two specifications."""
    
    def __init__(self, left: Specification[SpecType], right: Specification[SpecType]):
        self.left = left
        self.right = right
    
    def is_satisfied_by(self, entity: SpecType) -> bool:
        return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)


class NotSpecification(Specification[SpecType]):
    """Logical NOT of a specification."""
    
    def __init__(self, spec: Specification[SpecType]):
        self.spec = spec
    
    def is_satisfied_by(self, entity: SpecType) -> bool:
        return not self.spec.is_satisfied_by(entity)


class Repository(Protocol, Generic[T]):
    """Base repository interface with common CRUD operations.
    
    All repositories should implement this interface to provide
    consistent data access patterns across domains.
    """
    
    async def save(self, entity: T) -> None:
        """Save or update an entity.
        
        Args:
            entity: The entity to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        ...
    
    async def find_by_id(self, entity_id: Any) -> Optional[T]:
        """Find entity by its unique identifier.
        
        Args:
            entity_id: The unique identifier
            
        Returns:
            The entity if found, None otherwise
            
        Raises:
            RepositoryError: If lookup operation fails
        """
        ...
    
    async def find_all(self) -> List[T]:
        """Find all entities.
        
        Returns:
            List of all entities, empty list if none found
            
        Raises:
            RepositoryError: If query operation fails
        """
        ...
    
    async def find_by_specification(self, spec: Specification[T]) -> List[T]:
        """Find entities matching a specification.
        
        Args:
            spec: The specification to match against
            
        Returns:
            List of matching entities, empty list if none found
            
        Raises:
            RepositoryError: If query operation fails
        """
        ...
    
    async def exists(self, entity_id: Any) -> bool:
        """Check if entity exists by ID.
        
        Args:
            entity_id: The unique identifier
            
        Returns:
            True if entity exists, False otherwise
            
        Raises:
            RepositoryError: If existence check fails
        """
        ...
    
    async def delete(self, entity: T) -> None:
        """Delete an entity.
        
        Args:
            entity: The entity to delete
            
        Raises:
            RepositoryError: If delete operation fails
        """
        ...
    
    async def delete_by_id(self, entity_id: Any) -> bool:
        """Delete entity by ID.
        
        Args:
            entity_id: The unique identifier
            
        Returns:
            True if entity was deleted, False if not found
            
        Raises:
            RepositoryError: If delete operation fails
        """
        ...
    
    async def count(self) -> int:
        """Count total number of entities.
        
        Returns:
            Total count of entities
            
        Raises:
            RepositoryError: If count operation fails
        """
        ...


class WorkspaceAwareRepository(Repository[T], ABC):
    """Base class for repositories that need workspace isolation.
    
    Provides common workspace-aware functionality while maintaining
    the repository interface contract.
    """
    
    def __init__(self, workspace_name: WorkspaceName):
        """Initialize with workspace context.
        
        Args:
            workspace_name: The workspace this repository operates in
        """
        self._workspace_name = workspace_name
    
    @property
    def workspace_name(self) -> WorkspaceName:
        """Get the current workspace name."""
        return self._workspace_name
    
    async def find_by_workspace(self, workspace: Optional[WorkspaceName] = None) -> List[T]:
        """Find all entities in a specific workspace.
        
        Args:
            workspace: Workspace to search in, defaults to current workspace
            
        Returns:
            List of entities in the workspace
            
        Raises:
            RepositoryError: If query operation fails
        """
        target_workspace = workspace or self._workspace_name
        return await self._find_by_workspace_impl(target_workspace)
    
    @abstractmethod
    async def _find_by_workspace_impl(self, workspace: WorkspaceName) -> List[T]:
        """Implementation-specific workspace query."""
        pass


class UnitOfWork(ABC):
    """Unit of Work pattern for managing transactions across repositories.
    
    Ensures consistency when operations span multiple repositories
    or require atomic transactions.
    """
    
    @abstractmethod
    async def __aenter__(self) -> 'UnitOfWork':
        """Enter async context manager."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager with automatic rollback on exceptions."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit all changes in this unit of work.
        
        Raises:
            UnitOfWorkError: If commit fails
        """
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback all changes in this unit of work.
        
        Raises:
            UnitOfWorkError: If rollback fails
        """
        pass


# Repository-specific exceptions
class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class EntityNotFoundError(RepositoryError):
    """Raised when an entity cannot be found."""
    
    def __init__(self, entity_type: str, entity_id: Any):
        super().__init__(f"{entity_type} with id '{entity_id}' not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class EntityAlreadyExistsError(RepositoryError):
    """Raised when trying to create an entity that already exists."""
    
    def __init__(self, entity_type: str, entity_id: Any):
        super().__init__(f"{entity_type} with id '{entity_id}' already exists")
        self.entity_type = entity_type
        self.entity_id = entity_id


class ConcurrencyError(RepositoryError):
    """Raised when concurrent modifications conflict."""
    pass


class UnitOfWorkError(Exception):
    """Base exception for unit of work operations."""
    pass
