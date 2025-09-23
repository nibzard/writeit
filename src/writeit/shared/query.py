"""Base CQRS Query infrastructure.

Provides base classes and interfaces for implementing Query side
of Command Query Responsibility Segregation (CQRS) pattern.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TypeVar, Generic, Any, Dict, List, Optional, Union
from uuid import uuid4


@dataclass(frozen=True)
class Query(ABC):
    """Base class for all queries.
    
    Queries represent read operations that retrieve data without
    modifying system state. They should be immutable.
    """
    
    query_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    workspace_name: Optional[str] = None
    pagination: Optional[Dict[str, Any]] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    sorting: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize query with defaults."""
        # Field default factories handle the initialization now
        pass


@dataclass(frozen=True)
class QueryResult(ABC):
    """Base class for query execution results.
    
    Contains the data returned from query execution along with
    metadata about the query execution.
    """
    
    success: bool = True
    message: str = ""
    data: Optional[Any] = None
    total_count: Optional[int] = None
    page_info: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    cache_hit: bool = False
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        """Initialize result with defaults."""
        if self.errors is None:
            object.__setattr__(self, 'errors', [])
        if self.warnings is None:
            object.__setattr__(self, 'warnings', [])
    
    @property
    def has_errors(self) -> bool:
        """Check if result has errors."""
        return bool(self.errors)
    
    @property
    def has_warnings(self) -> bool:
        """Check if result has warnings.""" 
        return bool(self.warnings)
    
    @property
    def has_data(self) -> bool:
        """Check if result has data."""
        return self.data is not None


@dataclass(frozen=True)
class PaginationInfo:
    """Pagination information for query results."""
    
    page: int = 1
    page_size: int = 20
    total_pages: Optional[int] = None
    total_count: Optional[int] = None
    has_next: bool = False
    has_previous: bool = False
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries."""
        return (self.page - 1) * self.page_size


@dataclass(frozen=True)
class SortInfo:
    """Sorting information for queries."""
    
    field: str
    direction: str = "asc"  # asc or desc
    
    def __post_init__(self):
        """Validate sort direction."""
        if self.direction not in ("asc", "desc"):
            raise ValueError(f"Invalid sort direction: {self.direction}")


TQuery = TypeVar('TQuery', bound=Query)
TResult = TypeVar('TResult', bound=QueryResult)


class QueryHandler(Generic[TResult], ABC):
    """Base interface for query handlers.
    
    Query handlers contain the logic for executing read operations
    and retrieving data from the system.
    """
    
    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """Execute the query and return result.
        
        Args:
            query: The query to execute
            
        Returns:
            Result of query execution
            
        Raises:
            QueryExecutionError: If query execution fails
        """
        pass
    
    async def validate(self, query: TQuery) -> List[str]:
        """Validate query before execution.
        
        Args:
            query: The query to validate
            
        Returns:
            List of validation errors, empty if valid
        """
        return []
    
    async def can_handle(self, query: TQuery) -> bool:
        """Check if this handler can execute the query.
        
        Args:
            query: The query to check
            
        Returns:
            True if handler can execute the query
        """
        return True


class QueryBus(ABC):
    """Interface for query bus that routes queries to handlers."""
    
    @abstractmethod
    async def send(self, query: TQuery) -> TResult:
        """Send query for execution.
        
        Args:
            query: Query to execute
            
        Returns:
            Query execution result
            
        Raises:
            QueryHandlerNotFoundError: If no handler found for query
            QueryExecutionError: If query execution fails
        """
        pass
    
    @abstractmethod
    def register_handler(
        self, 
        query_type: type, 
        handler: QueryHandler[TResult]
    ) -> None:
        """Register query handler for query type.
        
        Args:
            query_type: Type of query to handle
            handler: Handler instance
        """
        pass


# Query Exceptions

class QueryError(Exception):
    """Base exception for query-related errors."""
    
    def __init__(self, message: str, query: Optional[Query] = None):
        super().__init__(message)
        self.query = query


class QueryValidationError(QueryError):
    """Exception raised when query validation fails."""
    
    def __init__(
        self, 
        message: str, 
        validation_errors: List[str], 
        query: Optional[Query] = None
    ):
        super().__init__(message, query)
        self.validation_errors = validation_errors


class QueryHandlerNotFoundError(QueryError):
    """Exception raised when no handler found for query."""
    pass


class QueryExecutionError(QueryError):
    """Exception raised when query execution fails."""
    
    def __init__(
        self, 
        message: str, 
        inner_exception: Optional[Exception] = None,
        query: Optional[Query] = None
    ):
        super().__init__(message, query)
        self.inner_exception = inner_exception


# Simple Query Bus Implementation

class SimpleQueryBus(QueryBus):
    """Simple in-memory query bus implementation."""
    
    def __init__(self):
        self._handlers: Dict[type, QueryHandler] = {}
    
    async def send(self, query: TQuery) -> TResult:
        """Send query for execution."""
        query_type = type(query)
        
        if query_type not in self._handlers:
            raise QueryHandlerNotFoundError(
                f"No handler registered for query type: {query_type.__name__}",
                query
            )
        
        handler = self._handlers[query_type]
        
        # Validate query
        validation_errors = await handler.validate(query)
        if validation_errors:
            raise QueryValidationError(
                f"Query validation failed: {', '.join(validation_errors)}",
                validation_errors,
                query
            )
        
        # Check if handler can execute
        if not await handler.can_handle(query):
            raise QueryExecutionError(
                f"Handler cannot execute query: {query_type.__name__}",
                query
            )
        
        try:
            # Execute query
            return await handler.handle(query)
        except Exception as e:
            raise QueryExecutionError(
                f"Query execution failed: {str(e)}",
                e,
                query
            )
    
    def register_handler(
        self, 
        query_type: type, 
        handler: QueryHandler[TResult]
    ) -> None:
        """Register query handler."""
        self._handlers[query_type] = handler
    
    def get_registered_queries(self) -> List[type]:
        """Get list of registered query types."""
        return list(self._handlers.keys())
    
    def has_handler(self, query_type: type) -> bool:
        """Check if handler is registered for query type."""
        return query_type in self._handlers


# Common Query Types

@dataclass(frozen=True)
class ListQuery(Query):
    """Base query for listing entities with pagination and filtering."""
    
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_direction: str = "asc"
    search_term: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        
        # Validate pagination
        if self.page < 1:
            raise ValueError("Page must be >= 1")
        if self.page_size < 1 or self.page_size > 1000:
            raise ValueError("Page size must be between 1 and 1000")
        
        # Validate sort direction
        if self.sort_direction not in ("asc", "desc"):
            raise ValueError(f"Invalid sort direction: {self.sort_direction}")


@dataclass(frozen=True)
class GetByIdQuery(Query):
    """Base query for retrieving entity by ID."""
    
    entity_id: str = ""
    include_related: bool = False


@dataclass(frozen=True)
class SearchQuery(Query):
    """Base query for full-text search operations."""
    
    search_term: str = ""
    page: int = 1
    page_size: int = 20
    filters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        super().__post_init__()
        
        if not self.search_term or not self.search_term.strip():
            raise ValueError("Search term cannot be empty")
        
        if self.page < 1:
            raise ValueError("Page must be >= 1")
        if self.page_size < 1 or self.page_size > 1000:
            raise ValueError("Page size must be between 1 and 1000")