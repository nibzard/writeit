"""Shared kernel for WriteIt domain-driven design implementation.

Provides common patterns, interfaces, and utilities shared across
all domain boundaries including repository patterns, specifications,
and error handling.

## Repository Patterns

The shared kernel provides repository abstractions that all domains implement:
- Repository[T]: Base repository interface with CRUD operations
- WorkspaceAwareRepository[T]: Repository with workspace isolation
- Specification[T]: Composable query specification pattern
- UnitOfWork: Transaction boundary management across repositories

## Design Principles

1. **Minimal Dependencies**: Shared kernel should have minimal external dependencies
2. **Stability**: Changes should be rare and well-coordinated
3. **Generic**: Should be useful across multiple domains
4. **Well-Tested**: Comprehensive test coverage for shared components
5. **Documented**: Clear contracts and usage examples

## Usage Guidelines

- Only add to shared kernel when truly needed by multiple domains
- Prefer composition over inheritance for shared behavior
- Use interfaces to define contracts between domains
- Keep shared value objects immutable and side-effect free
"""

from .repository import (
    Repository,
    WorkspaceAwareRepository,
    Specification,
    UnitOfWork,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    RepositoryError,
    EntityNotFoundError,
    EntityAlreadyExistsError,
    ConcurrencyError,
    UnitOfWorkError,
)

__all__ = [
    # Repository patterns
    "Repository",
    "WorkspaceAwareRepository",
    "UnitOfWork",
    
    # Specification pattern
    "Specification",
    "AndSpecification",
    "OrSpecification", 
    "NotSpecification",
    
    # Exceptions
    "RepositoryError",
    "EntityNotFoundError",
    "EntityAlreadyExistsError",
    "ConcurrencyError",
    "UnitOfWorkError",
]