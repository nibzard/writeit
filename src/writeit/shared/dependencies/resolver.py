"""Service resolver with advanced resolution capabilities."""

from typing import Type, TypeVar, Any, Optional, List, Dict, Union, get_type_hints, get_origin, get_args
import inspect
from abc import ABC, abstractmethod

from .container import Container
from .exceptions import ServiceNotFoundError, InvalidServiceRegistrationError

T = TypeVar('T')


class IServiceResolver(ABC):
    """Interface for service resolution."""
    
    @abstractmethod
    def resolve(self, service_type: Type[T], **kwargs) -> T:
        """Resolve service instance."""
        pass
    
    @abstractmethod
    async def aresolve(self, service_type: Type[T], **kwargs) -> T:
        """Async resolve service instance."""
        pass
    
    @abstractmethod
    def resolve_all(self, service_type: Type[T]) -> List[T]:
        """Resolve all instances of service type."""
        pass
    
    @abstractmethod
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """Try to resolve service, return None if not found."""
        pass


class ServiceResolver(IServiceResolver):
    """Advanced service resolver.
    
    Provides enhanced service resolution capabilities including:
    - Generic type resolution
    - Optional dependency resolution
    - Multiple instance resolution
    - Conditional resolution
    - Context-aware resolution
    
    Examples:
        resolver = ServiceResolver(container)
        
        # Basic resolution
        service = resolver.resolve(UserService)
        
        # Optional resolution (doesn't throw if not found)
        service = resolver.try_resolve(OptionalService)
        
        # Resolve with context
        service = resolver.resolve(ContextualService, workspace="test")
        
        # Resolve all implementations
        handlers = resolver.resolve_all(IMessageHandler)
    """
    
    def __init__(self, container: Container) -> None:
        """Initialize resolver.
        
        Args:
            container: DI container to use for resolution
        """
        self._container = container
        self._resolution_context: Dict[str, Any] = {}
    
    def resolve(self, service_type: Type[T], **kwargs) -> T:
        """Resolve service instance.
        
        Args:
            service_type: Type of service to resolve
            **kwargs: Additional context for resolution
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not registered
        """
        # Set resolution context
        old_context = self._resolution_context
        self._resolution_context = {**old_context, **kwargs}
        
        try:
            return self._resolve_with_context(service_type)
        finally:
            self._resolution_context = old_context
    
    async def aresolve(self, service_type: Type[T], **kwargs) -> T:
        """Async resolve service instance.
        
        Args:
            service_type: Type of service to resolve
            **kwargs: Additional context for resolution
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not registered
        """
        # Set resolution context
        old_context = self._resolution_context
        self._resolution_context = {**old_context, **kwargs}
        
        try:
            return await self._aresolve_with_context(service_type)
        finally:
            self._resolution_context = old_context
    
    def resolve_all(self, service_type: Type[T]) -> List[T]:
        """Resolve all instances of service type.
        
        Args:
            service_type: Type of service to resolve
            
        Returns:
            List of all registered instances
        """
        # For now, return single instance if available
        # In future, could support multiple registrations
        try:
            instance = self.resolve(service_type)
            return [instance]
        except ServiceNotFoundError:
            return []
    
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """Try to resolve service, return None if not found.
        
        Args:
            service_type: Type of service to resolve
            
        Returns:
            Service instance or None
        """
        try:
            return self.resolve(service_type)
        except ServiceNotFoundError:
            return None
    
    def with_context(self, **kwargs) -> 'ServiceResolver':
        """Create resolver with additional context.
        
        Args:
            **kwargs: Context to add
            
        Returns:
            New resolver with added context
        """
        new_resolver = ServiceResolver(self._container)
        new_resolver._resolution_context = {**self._resolution_context, **kwargs}
        return new_resolver
    
    def _resolve_with_context(self, service_type: Type[T]) -> T:
        """Resolve service with current context."""
        # Check if service type is generic
        origin = get_origin(service_type)
        if origin is not None:
            return self._resolve_generic(service_type)
        
        # Check for contextual resolution
        if self._has_contextual_registration(service_type):
            return self._resolve_contextual(service_type)
        
        # Standard resolution
        return self._container.resolve(service_type)
    
    async def _aresolve_with_context(self, service_type: Type[T]) -> T:
        """Async resolve service with current context."""
        # Check if service type is generic
        origin = get_origin(service_type)
        if origin is not None:
            return await self._aresolve_generic(service_type)
        
        # Check for contextual resolution
        if self._has_contextual_registration(service_type):
            return await self._aresolve_contextual(service_type)
        
        # Standard resolution
        return await self._container.aresolve(service_type)
    
    def _resolve_generic(self, service_type: Type[T]) -> T:
        """Resolve generic service type."""
        origin = get_origin(service_type)
        args = get_args(service_type)
        
        # Handle common generic types
        if origin is list or origin is List:
            if args:
                element_type = args[0]
                return self.resolve_all(element_type)  # type: ignore
        
        elif origin is dict or origin is Dict:
            # Could implement dict-based service resolution
            pass
        
        # Fall back to origin type
        if origin:
            return self._container.resolve(origin)  # type: ignore
        
        raise ServiceNotFoundError(service_type)
    
    async def _aresolve_generic(self, service_type: Type[T]) -> T:
        """Async resolve generic service type."""
        origin = get_origin(service_type)
        args = get_args(service_type)
        
        # Handle common generic types
        if origin is list or origin is List:
            if args:
                element_type = args[0]
                # For async, we need to resolve each item
                instances = []
                try:
                    instance = await self.aresolve(element_type)
                    instances.append(instance)
                except ServiceNotFoundError:
                    pass
                return instances  # type: ignore
        
        # Fall back to origin type
        if origin:
            return await self._container.aresolve(origin)  # type: ignore
        
        raise ServiceNotFoundError(service_type)
    
    def _has_contextual_registration(self, service_type: Type[Any]) -> bool:
        """Check if service has contextual registration."""
        # For now, simple implementation
        # Could be extended to support more complex contextual logic
        return False
    
    def _resolve_contextual(self, service_type: Type[T]) -> T:
        """Resolve service with context."""
        # Placeholder for contextual resolution
        # Could implement workspace-specific, environment-specific, etc.
        return self._container.resolve(service_type)
    
    async def _aresolve_contextual(self, service_type: Type[T]) -> T:
        """Async resolve service with context."""
        # Placeholder for contextual resolution
        return await self._container.aresolve(service_type)


class LazyServiceResolver:
    """Lazy service resolver that defers resolution until needed.
    
    Useful for breaking circular dependencies or improving startup performance.
    
    Examples:
        lazy_service = LazyServiceResolver(container, UserService)
        
        # Service is resolved when accessed
        user = lazy_service.value
    """
    
    def __init__(self, container: Container, service_type: Type[T]) -> None:
        """Initialize lazy resolver.
        
        Args:
            container: DI container
            service_type: Service type to resolve lazily
        """
        self._container = container
        self._service_type = service_type
        self._instance: Optional[T] = None
        self._resolved = False
    
    @property
    def value(self) -> T:
        """Get resolved service instance."""
        if not self._resolved:
            self._instance = self._container.resolve(self._service_type)
            self._resolved = True
        
        return self._instance  # type: ignore
    
    async def avalue(self) -> T:
        """Get resolved service instance asynchronously."""
        if not self._resolved:
            self._instance = await self._container.aresolve(self._service_type)
            self._resolved = True
        
        return self._instance  # type: ignore
    
    def is_resolved(self) -> bool:
        """Check if service has been resolved."""
        return self._resolved
    
    def reset(self) -> None:
        """Reset lazy resolver to unresolved state."""
        self._instance = None
        self._resolved = False