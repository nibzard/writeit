"""Service registry for managing service registrations."""

from typing import Type, Any, Dict, List, Optional
from dataclasses import dataclass
import importlib
import inspect
from pathlib import Path

from .container import Container, ServiceLifetime
from .exceptions import InvalidServiceRegistrationError


@dataclass
class ServiceRegistration:
    """Service registration configuration."""
    service_type: str  # Fully qualified type name
    implementation_type: Optional[str] = None  # Fully qualified implementation name
    factory: Optional[str] = None  # Factory function path
    lifetime: str = "transient"  # ServiceLifetime value
    workspace_specific: bool = False  # Whether service is workspace-specific
    dependencies: List[str] = None  # Explicit dependency list
    
    def __post_init__(self) -> None:
        if self.dependencies is None:
            self.dependencies = []


class ServiceRegistry:
    """Registry for managing service registrations.
    
    Provides configuration-based service registration with support for:
    - Type name resolution from strings
    - Workspace-specific service registration
    - Automatic dependency discovery
    - Environment-specific configurations
    
    Examples:
        registry = ServiceRegistry()
        
        # Register from configuration
        registry.register_from_config({
            "services": [
                {
                    "service_type": "writeit.domains.pipeline.repositories.PipelineTemplateRepository",
                    "implementation_type": "writeit.infrastructure.persistence.LMDBPipelineTemplateRepository",
                    "lifetime": "singleton"
                }
            ]
        })
        
        # Apply registrations to container
        container = Container()
        registry.apply_to_container(container)
    """
    
    def __init__(self) -> None:
        self._registrations: List[ServiceRegistration] = []
        self._type_cache: Dict[str, Type[Any]] = {}
    
    def register(
        self,
        service_type: str,
        implementation_type: Optional[str] = None,
        factory: Optional[str] = None,
        lifetime: str = "transient",
        workspace_specific: bool = False,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """Register a service.
        
        Args:
            service_type: Fully qualified service type name
            implementation_type: Fully qualified implementation type name
            factory: Factory function path (module.function)
            lifetime: Service lifetime (singleton, transient, scoped)
            workspace_specific: Whether service is workspace-specific
            dependencies: Explicit dependency list
        """
        registration = ServiceRegistration(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=lifetime,
            workspace_specific=workspace_specific,
            dependencies=dependencies or []
        )
        
        self._registrations.append(registration)
    
    def register_from_config(self, config: Dict[str, Any]) -> None:
        """Register services from configuration.
        
        Args:
            config: Configuration dictionary with 'services' key
        """
        services = config.get("services", [])
        
        for service_config in services:
            self.register(
                service_type=service_config["service_type"],
                implementation_type=service_config.get("implementation_type"),
                factory=service_config.get("factory"),
                lifetime=service_config.get("lifetime", "transient"),
                workspace_specific=service_config.get("workspace_specific", False),
                dependencies=service_config.get("dependencies")
            )
    
    def apply_to_container(
        self,
        container: Container,
        workspace_name: Optional[str] = None
    ) -> None:
        """Apply registrations to container.
        
        Args:
            container: Container to apply registrations to
            workspace_name: Current workspace name (for workspace-specific services)
        """
        for registration in self._registrations:
            # Skip workspace-specific services if no workspace provided
            if registration.workspace_specific and not workspace_name:
                continue
            
            try:
                self._apply_registration(container, registration, workspace_name)
            except Exception as e:
                raise InvalidServiceRegistrationError(
                    f"Failed to register {registration.service_type}: {e}"
                )
    
    def _apply_registration(
        self,
        container: Container,
        registration: ServiceRegistration,
        workspace_name: Optional[str]
    ) -> None:
        """Apply single registration to container."""
        # Resolve service type
        service_type = self._resolve_type(registration.service_type)
        
        # Parse lifetime
        lifetime = ServiceLifetime(registration.lifetime)
        
        if registration.factory:
            # Factory registration
            factory_func = self._resolve_factory(registration.factory)
            container.register_factory(
                service_type=service_type,
                factory=factory_func,
                lifetime=lifetime
            )
        
        elif registration.implementation_type:
            # Implementation type registration
            impl_type = self._resolve_type(registration.implementation_type)
            
            if lifetime == ServiceLifetime.SINGLETON:
                container.register_singleton(service_type, impl_type)
            elif lifetime == ServiceLifetime.SCOPED:
                container.register_scoped(service_type, impl_type)
            else:
                container.register_transient(service_type, impl_type)
        
        else:
            # Self-registration
            if lifetime == ServiceLifetime.SINGLETON:
                container.register_singleton(service_type)
            elif lifetime == ServiceLifetime.SCOPED:
                container.register_scoped(service_type)
            else:
                container.register_transient(service_type)
    
    def _resolve_type(self, type_name: str) -> Type[Any]:
        """Resolve type from string name."""
        if type_name in self._type_cache:
            return self._type_cache[type_name]
        
        try:
            # Split module and class name
            parts = type_name.split('.')
            if len(parts) < 2:
                raise ValueError(f"Invalid type name: {type_name}")
            
            class_name = parts[-1]
            module_name = '.'.join(parts[:-1])
            
            # Import module and get class
            module = importlib.import_module(module_name)
            type_obj = getattr(module, class_name)
            
            # Cache for future use
            self._type_cache[type_name] = type_obj
            return type_obj
        
        except (ImportError, AttributeError) as e:
            raise InvalidServiceRegistrationError(
                f"Could not resolve type '{type_name}': {e}"
            )
    
    def _resolve_factory(self, factory_path: str) -> Any:
        """Resolve factory function from string path."""
        try:
            # Split module and function name
            parts = factory_path.split('.')
            if len(parts) < 2:
                raise ValueError(f"Invalid factory path: {factory_path}")
            
            func_name = parts[-1]
            module_name = '.'.join(parts[:-1])
            
            # Import module and get function
            module = importlib.import_module(module_name)
            factory_func = getattr(module, func_name)
            
            if not callable(factory_func):
                raise ValueError(f"Factory '{factory_path}' is not callable")
            
            return factory_func
        
        except (ImportError, AttributeError) as e:
            raise InvalidServiceRegistrationError(
                f"Could not resolve factory '{factory_path}': {e}"
            )
    
    def get_registrations(self) -> List[ServiceRegistration]:
        """Get all registrations."""
        return self._registrations.copy()
    
    def clear(self) -> None:
        """Clear all registrations."""
        self._registrations.clear()
        self._type_cache.clear()