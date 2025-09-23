"""Main dependency injection container."""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any, Type, TypeVar, Generic, Optional, Dict, List, Callable, 
    Union, get_type_hints, get_origin, get_args, cast
)
import inspect
import asyncio
from contextlib import asynccontextmanager, contextmanager
from threading import Lock
from weakref import WeakSet

from .exceptions import (
    ServiceNotFoundError,
    CircularDependencyError,
    InvalidServiceRegistrationError,
    ServiceLifetimeError,
    AsyncServiceError
)

T = TypeVar('T')
ServiceType = TypeVar('ServiceType')
ImplementationType = TypeVar('ImplementationType')


class ServiceLifetime(Enum):
    """Service lifetime enumeration."""
    SINGLETON = "singleton"      # One instance per container
    TRANSIENT = "transient"      # New instance every time
    SCOPED = "scoped"            # One instance per scope


@dataclass
class ServiceDescriptor:
    """Service registration descriptor."""
    service_type: Type[Any]
    implementation_type: Optional[Type[Any]] = None
    factory: Optional[Callable[..., Any]] = None
    instance: Optional[Any] = None
    lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT
    dependencies: List[Type[Any]] = field(default_factory=list)
    async_factory: bool = False
    
    def __post_init__(self) -> None:
        """Validate service descriptor."""
        # Ensure exactly one of implementation_type, factory, or instance is provided
        provided = sum([
            self.implementation_type is not None,
            self.factory is not None,
            self.instance is not None
        ])
        
        if provided != 1:
            raise InvalidServiceRegistrationError(
                "Exactly one of implementation_type, factory, or instance must be provided"
            )
        
        # Singleton instances must have singleton lifetime
        if self.instance is not None and self.lifetime != ServiceLifetime.SINGLETON:
            raise InvalidServiceRegistrationError(
                "Instance registration must use SINGLETON lifetime"
            )
        
        # Auto-discover dependencies if not explicitly provided
        if not self.dependencies:
            if self.implementation_type:
                self.dependencies = self._discover_dependencies(self.implementation_type)
            elif self.factory:
                self.dependencies = self._discover_dependencies(self.factory)
    
    def _discover_dependencies(self, target: Union[Type[Any], Callable]) -> List[Type[Any]]:
        """Auto-discover dependencies from type hints."""
        try:
            if inspect.isclass(target):
                # Get constructor dependencies
                init_method = target.__init__
                type_hints = get_type_hints(init_method)
                # Remove 'self' and 'return' from dependencies
                dependencies = [
                    hint for name, hint in type_hints.items() 
                    if name not in ('self', 'return')
                ]
            else:
                # Get function dependencies
                type_hints = get_type_hints(target)
                dependencies = [
                    hint for name, hint in type_hints.items()
                    if name != 'return'
                ]
            
            return dependencies
        except Exception:
            # If type hint discovery fails, return empty list
            return []


class ServiceScope:
    """Service scope for scoped lifetime management."""
    
    def __init__(self, container: Container) -> None:
        self._container = container
        self._scoped_instances: Dict[Type[Any], Any] = {}
        self._is_disposed = False
        self._disposables: WeakSet[Any] = WeakSet()
    
    def get_scoped_instance(self, service_type: Type[T]) -> Optional[T]:
        """Get scoped instance if it exists."""
        if self._is_disposed:
            raise ServiceLifetimeError("Cannot access disposed scope")
        return self._scoped_instances.get(service_type)
    
    def set_scoped_instance(self, service_type: Type[T], instance: T) -> None:
        """Set scoped instance."""
        if self._is_disposed:
            raise ServiceLifetimeError("Cannot set instance in disposed scope")
        
        self._scoped_instances[service_type] = instance
        
        # Track disposable instances
        if hasattr(instance, 'dispose') or hasattr(instance, '__aenter__'):
            self._disposables.add(instance)
    
    def dispose(self) -> None:
        """Dispose of all scoped instances."""
        if self._is_disposed:
            return
        
        self._is_disposed = True
        
        # Dispose all disposable instances
        for instance in self._disposables:
            try:
                if hasattr(instance, 'dispose'):
                    result = instance.dispose()
                    if asyncio.iscoroutine(result):
                        # Schedule async disposal
                        asyncio.create_task(result)
                elif hasattr(instance, '__aexit__'):
                    # Async context manager
                    result = instance.__aexit__(None, None, None)
                    if asyncio.iscoroutine(result):
                        asyncio.create_task(result)
            except Exception:
                # Log disposal errors but don't raise
                pass
        
        self._scoped_instances.clear()
        self._disposables.clear()
    
    async def adispose(self) -> None:
        """Async dispose of all scoped instances."""
        if self._is_disposed:
            return
        
        self._is_disposed = True
        
        # Dispose all disposable instances
        disposal_tasks = []
        for instance in self._disposables:
            try:
                if hasattr(instance, 'adispose'):
                    disposal_tasks.append(instance.adispose())
                elif hasattr(instance, '__aexit__'):
                    disposal_tasks.append(instance.__aexit__(None, None, None))
                elif hasattr(instance, 'dispose'):
                    result = instance.dispose()
                    if asyncio.iscoroutine(result):
                        disposal_tasks.append(result)
            except Exception:
                pass
        
        # Wait for all disposals to complete
        if disposal_tasks:
            await asyncio.gather(*disposal_tasks, return_exceptions=True)
        
        self._scoped_instances.clear()
        self._disposables.clear()


class Container:
    """Dependency injection container.
    
    Provides comprehensive service registration and resolution with support for:
    - Multiple service lifetimes (singleton, transient, scoped)
    - Auto-wiring based on type hints
    - Interface/implementation mapping
    - Async service factories
    - Circular dependency detection
    - Service scoping and disposal
    
    Examples:
        # Basic registration
        container = Container()
        container.register_singleton(DatabaseConnection, SqliteConnection)
        container.register_transient(UserService)
        
        # Factory registration
        container.register_factory(
            LLMProvider,
            lambda: OpenAIProvider(api_key="..."),
            ServiceLifetime.SINGLETON
        )
        
        # Instance registration
        config = Configuration()
        container.register_instance(Configuration, config)
        
        # Service resolution
        user_service = container.resolve(UserService)
        
        # Scoped services
        with container.create_scope() as scope:
            scoped_service = scope.resolve(ScopedService)
    """
    
    def __init__(self, parent: Optional[Container] = None) -> None:
        """Initialize container.
        
        Args:
            parent: Parent container for hierarchical resolution
        """
        self._parent = parent
        self._services: Dict[Type[Any], ServiceDescriptor] = {}
        self._singletons: Dict[Type[Any], Any] = {}
        self._resolution_stack: List[Type[Any]] = []
        self._lock = Lock()
        self._current_scope: Optional[ServiceScope] = None
    
    def register_singleton(
        self,
        service_type: Type[ServiceType],
        implementation_type: Optional[Type[ImplementationType]] = None
    ) -> Container:
        """Register service with singleton lifetime.
        
        Args:
            service_type: Service interface or base type
            implementation_type: Implementation type (defaults to service_type)
            
        Returns:
            Self for method chaining
        """
        impl_type = implementation_type or service_type
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.SINGLETON
        )
        return self._register_service(service_type, descriptor)
    
    def register_transient(
        self,
        service_type: Type[ServiceType],
        implementation_type: Optional[Type[ImplementationType]] = None
    ) -> Container:
        """Register service with transient lifetime.
        
        Args:
            service_type: Service interface or base type
            implementation_type: Implementation type (defaults to service_type)
            
        Returns:
            Self for method chaining
        """
        impl_type = implementation_type or service_type
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.TRANSIENT
        )
        return self._register_service(service_type, descriptor)
    
    def register_scoped(
        self,
        service_type: Type[ServiceType],
        implementation_type: Optional[Type[ImplementationType]] = None
    ) -> Container:
        """Register service with scoped lifetime.
        
        Args:
            service_type: Service interface or base type
            implementation_type: Implementation type (defaults to service_type)
            
        Returns:
            Self for method chaining
        """
        impl_type = implementation_type or service_type
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation_type=impl_type,
            lifetime=ServiceLifetime.SCOPED
        )
        return self._register_service(service_type, descriptor)
    
    def register_factory(
        self,
        service_type: Type[ServiceType],
        factory: Callable[..., ServiceType],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
        async_factory: bool = False
    ) -> Container:
        """Register service with factory function.
        
        Args:
            service_type: Service type
            factory: Factory function to create service instances
            lifetime: Service lifetime
            async_factory: Whether factory is async
            
        Returns:
            Self for method chaining
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime,
            async_factory=async_factory
        )
        return self._register_service(service_type, descriptor)
    
    def register_instance(
        self,
        service_type: Type[ServiceType],
        instance: ServiceType
    ) -> Container:
        """Register service instance.
        
        Args:
            service_type: Service type
            instance: Service instance
            
        Returns:
            Self for method chaining
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # Store instance immediately
        with self._lock:
            self._singletons[service_type] = instance
        
        return self._register_service(service_type, descriptor)
    
    def is_registered(self, service_type: Type[Any]) -> bool:
        """Check if service type is registered.
        
        Args:
            service_type: Service type to check
            
        Returns:
            True if service is registered
        """
        with self._lock:
            if service_type in self._services:
                return True
            if self._parent:
                return self._parent.is_registered(service_type)
            return False
    
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve service instance.
        
        Args:
            service_type: Type of service to resolve
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependency detected
        """
        with self._lock:
            return self._resolve_internal(service_type)
    
    async def aresolve(self, service_type: Type[T]) -> T:
        """Async resolve service instance.
        
        Args:
            service_type: Type of service to resolve
            
        Returns:
            Service instance
            
        Raises:
            ServiceNotFoundError: If service is not registered
            CircularDependencyError: If circular dependency detected
            AsyncServiceError: If async resolution fails
        """
        # Note: We can't use lock in async context, so we need different approach
        return await self._aresolve_internal(service_type)
    
    @contextmanager
    def create_scope(self):
        """Create service scope for scoped lifetime management.
        
        Returns:
            Context manager that provides scoped service resolution
        """
        scope = ServiceScope(self)
        old_scope = self._current_scope
        self._current_scope = scope
        
        try:
            yield scope
        finally:
            self._current_scope = old_scope
            scope.dispose()
    
    @asynccontextmanager
    async def acreate_scope(self):
        """Create async service scope for scoped lifetime management.
        
        Returns:
            Async context manager that provides scoped service resolution
        """
        scope = ServiceScope(self)
        old_scope = self._current_scope
        self._current_scope = scope
        
        try:
            yield scope
        finally:
            self._current_scope = old_scope
            await scope.adispose()
    
    def create_child_container(self) -> Container:
        """Create child container with this container as parent.
        
        Returns:
            New child container
        """
        return Container(parent=self)
    
    def _register_service(self, service_type: Type[Any], descriptor: ServiceDescriptor) -> Container:
        """Internal service registration."""
        with self._lock:
            self._services[service_type] = descriptor
        return self
    
    def _resolve_internal(self, service_type: Type[T]) -> T:
        """Internal synchronous service resolution."""
        # Check for circular dependencies
        if service_type in self._resolution_stack:
            raise CircularDependencyError(self._resolution_stack + [service_type])
        
        # Check if service is registered
        descriptor = self._get_service_descriptor(service_type)
        if not descriptor:
            raise ServiceNotFoundError(service_type)
        
        # Handle different lifetimes
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            return self._resolve_singleton(service_type, descriptor)
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return self._resolve_scoped(service_type, descriptor)
        else:  # TRANSIENT
            return self._resolve_transient(service_type, descriptor)
    
    async def _aresolve_internal(self, service_type: Type[T]) -> T:
        """Internal async service resolution."""
        # For async resolution, we need to handle the resolution stack differently
        # to avoid race conditions. For now, implement basic async resolution.
        
        # Check if service is registered
        descriptor = self._get_service_descriptor(service_type)
        if not descriptor:
            raise ServiceNotFoundError(service_type)
        
        # Handle different lifetimes (simplified for async)
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            # Check existing singleton
            if service_type in self._singletons:
                return self._singletons[service_type]
            
            # Create new singleton
            instance = await self._create_instance_async(descriptor)
            self._singletons[service_type] = instance
            return instance
        
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if not self._current_scope:
                raise ServiceLifetimeError("No active scope for scoped service")
            
            existing = self._current_scope.get_scoped_instance(service_type)
            if existing is not None:
                return existing
            
            instance = await self._create_instance_async(descriptor)
            self._current_scope.set_scoped_instance(service_type, instance)
            return instance
        
        else:  # TRANSIENT
            return await self._create_instance_async(descriptor)
    
    def _get_service_descriptor(self, service_type: Type[Any]) -> Optional[ServiceDescriptor]:
        """Get service descriptor, checking parent if not found."""
        if service_type in self._services:
            return self._services[service_type]
        
        if self._parent:
            return self._parent._get_service_descriptor(service_type)
        
        return None
    
    def _resolve_singleton(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Resolve singleton service."""
        # Check if instance already exists
        if service_type in self._singletons:
            return self._singletons[service_type]
        
        # Create new instance
        instance = self._create_instance(service_type, descriptor)
        self._singletons[service_type] = instance
        return instance
    
    def _resolve_scoped(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Resolve scoped service."""
        if not self._current_scope:
            raise ServiceLifetimeError("No active scope for scoped service")
        
        # Check if instance exists in current scope
        existing = self._current_scope.get_scoped_instance(service_type)
        if existing is not None:
            return existing
        
        # Create new scoped instance
        instance = self._create_instance(service_type, descriptor)
        self._current_scope.set_scoped_instance(service_type, instance)
        return instance
    
    def _resolve_transient(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Resolve transient service."""
        return self._create_instance(service_type, descriptor)
    
    def _create_instance(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Create service instance."""
        self._resolution_stack.append(service_type)
        
        try:
            if descriptor.instance is not None:
                return descriptor.instance
            
            elif descriptor.factory is not None:
                if descriptor.async_factory:
                    raise AsyncServiceError(
                        f"Cannot resolve async factory for {service_type.__name__} in sync context"
                    )
                
                # Resolve factory dependencies
                factory_args = self._resolve_dependencies(descriptor.dependencies)
                return descriptor.factory(*factory_args)
            
            elif descriptor.implementation_type is not None:
                # Resolve constructor dependencies
                constructor_args = self._resolve_dependencies(descriptor.dependencies)
                return descriptor.implementation_type(*constructor_args)
            
            else:
                raise InvalidServiceRegistrationError(
                    f"Invalid service descriptor for {service_type.__name__}"
                )
        
        finally:
            self._resolution_stack.pop()
    
    async def _create_instance_async(self, descriptor: ServiceDescriptor) -> Any:
        """Create service instance asynchronously."""
        if descriptor.instance is not None:
            return descriptor.instance
        
        elif descriptor.factory is not None:
            if descriptor.async_factory:
                # Async factory - resolve dependencies first
                factory_args = []
                for dep_type in descriptor.dependencies:
                    dep_instance = await self._aresolve_internal(dep_type)
                    factory_args.append(dep_instance)
                return await descriptor.factory(*factory_args)
            else:
                # Sync factory
                factory_args = []
                for dep_type in descriptor.dependencies:
                    dep_instance = await self._aresolve_internal(dep_type)
                    factory_args.append(dep_instance)
                return descriptor.factory(*factory_args)
        
        elif descriptor.implementation_type is not None:
            # Resolve constructor dependencies
            constructor_args = []
            for dep_type in descriptor.dependencies:
                dep_instance = await self._aresolve_internal(dep_type)
                constructor_args.append(dep_instance)
            return descriptor.implementation_type(*constructor_args)
        
        else:
            raise InvalidServiceRegistrationError(
                f"Invalid service descriptor"
            )
    
    def _resolve_dependencies(self, dependencies: List[Type[Any]]) -> List[Any]:
        """Resolve list of dependencies."""
        resolved = []
        for dep_type in dependencies:
            resolved.append(self._resolve_internal(dep_type))
        return resolved