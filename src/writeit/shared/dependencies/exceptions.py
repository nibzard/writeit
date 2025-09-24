"""Dependency injection exceptions."""

from typing import Any, Type, List, Optional


class DIError(Exception):
    """Base exception for dependency injection errors."""
    pass


class ServiceNotFoundError(DIError):
    """Raised when a requested service is not registered."""
    
    def __init__(self, service_type: Type[Any], message: Optional[str] = None) -> None:
        self.service_type = service_type
        if message is None:
            message = f"Service of type '{service_type.__name__}' is not registered"
        super().__init__(message)


class CircularDependencyError(DIError):
    """Raised when a circular dependency is detected."""
    
    def __init__(self, dependency_chain: List[Type[Any]]) -> None:
        self.dependency_chain = dependency_chain
        chain_str = " -> ".join(t.__name__ for t in dependency_chain)
        message = f"Circular dependency detected: {chain_str}"
        super().__init__(message)


class InvalidServiceRegistrationError(DIError):
    """Raised when service registration is invalid."""
    pass


class ServiceLifetimeError(DIError):
    """Raised when there's an issue with service lifetime management."""
    pass


class AsyncServiceError(DIError):
    """Raised when there's an issue with async service resolution."""
    pass