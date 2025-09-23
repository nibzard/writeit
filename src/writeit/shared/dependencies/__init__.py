"""Dependency injection container for WriteIt.

Provides a comprehensive dependency injection framework supporting:
- Service registration with different lifetimes
- Auto-wiring based on type hints
- Configuration-based registration
- Interface/implementation mapping
- Async service support
"""

from .container import Container, ServiceLifetime, ServiceDescriptor, ServiceScope
from .registry import ServiceRegistry
from .resolver import ServiceResolver, IServiceResolver, LazyServiceResolver
from .configuration import DIConfiguration, Environment, DIConfigurationBuilder
from .factory import ContainerFactory, WorkspaceContainerManager, workspace_containers
from .exceptions import (
    DIError,
    ServiceNotFoundError,
    CircularDependencyError,
    InvalidServiceRegistrationError,
    ServiceLifetimeError,
    AsyncServiceError
)

__all__ = [
    # Core container
    "Container",
    "ServiceLifetime", 
    "ServiceDescriptor",
    "ServiceScope",
    
    # Registry and resolution
    "ServiceRegistry",
    "ServiceResolver",
    "IServiceResolver",
    "LazyServiceResolver",
    
    # Configuration
    "DIConfiguration",
    "Environment",
    "DIConfigurationBuilder",
    
    # Factory and management
    "ContainerFactory",
    "WorkspaceContainerManager",
    "workspace_containers",
    
    # Exceptions
    "DIError",
    "ServiceNotFoundError",
    "CircularDependencyError",
    "InvalidServiceRegistrationError",
    "ServiceLifetimeError",
    "AsyncServiceError"
]