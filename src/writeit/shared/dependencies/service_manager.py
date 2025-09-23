"""Service registration manager for WriteIt application.

Provides centralized service registration and dependency injection container
management with environment-specific configurations and workspace support.
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging
import os

from .container import Container
from .configuration import DIConfiguration, Environment
from .registry import ServiceRegistry
from .exceptions import (
    ServiceNotFoundError,
    InvalidServiceRegistrationError,
    ServiceLifetimeError,
    CircularDependencyError
)

logger = logging.getLogger(__name__)


class ServiceManager:
    """Service registration manager for WriteIt.
    
    Provides a high-level interface for managing service registration,
    container configuration, and dependency injection across different
    environments and workspaces.
    
    Features:
    - Environment-specific service configuration
    - Workspace-aware service registration
    - Configuration validation and diagnostics
    - Service health checking and diagnostics
    - Container lifecycle management
    
    Examples:
        # Create manager with default configuration
        manager = ServiceManager()
        container = manager.create_container()
        
        # Environment-specific setup
        manager = ServiceManager.for_environment(Environment.TESTING)
        container = manager.create_container(workspace="test-workspace")
        
        # Custom configuration
        config = DIConfiguration.from_file("services.yaml")
        manager = ServiceManager(config)
        container = manager.create_container()
    """
    
    def __init__(
        self, 
        configuration: Optional[DIConfiguration] = None,
        validate_on_init: bool = True
    ) -> None:
        """Initialize service manager.
        
        Args:
            configuration: DI configuration (uses default if None)
            validate_on_init: Whether to validate configuration on initialization
        """
        self._configuration = configuration or DIConfiguration.create_default()
        self._containers: Dict[str, Container] = {}
        self._registry = ServiceRegistry()
        
        if validate_on_init:
            self._validate_configuration()
    
    @classmethod
    def for_environment(
        cls, 
        environment: Environment,
        config_path: Optional[Path] = None
    ) -> ServiceManager:
        """Create service manager for specific environment.
        
        Args:
            environment: Target environment
            config_path: Optional path to environment-specific config
            
        Returns:
            Configured service manager
        """
        if config_path and config_path.exists():
            config = DIConfiguration.from_file(config_path)
        else:
            config = DIConfiguration.create_default()
        
        config.set_environment(environment)
        return cls(config)
    
    @classmethod
    def from_config_file(cls, config_path: Path) -> ServiceManager:
        """Create service manager from configuration file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Service manager with loaded configuration
        """
        config = DIConfiguration.from_file(config_path)
        return cls(config)
    
    def create_container(
        self, 
        workspace_name: Optional[str] = None,
        parent_container: Optional[Container] = None
    ) -> Container:
        """Create and configure dependency injection container.
        
        Args:
            workspace_name: Workspace name for workspace-specific services
            parent_container: Parent container for hierarchical DI
            
        Returns:
            Configured container with all services registered
        """
        container_key = f"{workspace_name or 'default'}_{id(parent_container)}"
        
        if container_key in self._containers:
            logger.debug(f"Reusing existing container for {container_key}")
            return self._containers[container_key]
        
        logger.info(f"Creating new container for workspace: {workspace_name}")
        
        # Create container
        container = Container(parent=parent_container)
        
        # Apply configuration
        try:
            self._configuration.apply_to_container(container, workspace_name)
            logger.info(f"Successfully registered {len(self._configuration.services)} services")
        except Exception as e:
            logger.error(f"Failed to apply configuration to container: {e}")
            raise InvalidServiceRegistrationError(f"Container configuration failed: {e}")
        
        # Cache container
        self._containers[container_key] = container
        
        return container
    
    def create_child_container(
        self, 
        parent_container: Container,
        workspace_name: Optional[str] = None
    ) -> Container:
        """Create child container with workspace-specific services.
        
        Args:
            parent_container: Parent container
            workspace_name: Workspace name for additional services
            
        Returns:
            Child container with additional workspace services
        """
        child = parent_container.create_child_container()
        
        if workspace_name and workspace_name in self._configuration.workspace_services:
            # Register workspace-specific services
            workspace_registry = ServiceRegistry()
            for service_config in self._configuration.workspace_services[workspace_name]:
                workspace_registry.register(
                    service_type=service_config["service_type"],
                    implementation_type=service_config.get("implementation_type"),
                    factory=service_config.get("factory"),
                    lifetime=service_config.get("lifetime", "transient"),
                    workspace_specific=True
                )
            
            workspace_registry.apply_to_container(child, workspace_name)
        
        return child
    
    def validate_configuration(self) -> List[str]:
        """Validate service configuration.
        
        Returns:
            List of validation issues (empty if valid)
        """
        return self._validate_configuration()
    
    def get_registered_services(self) -> List[str]:
        """Get list of all registered service types.
        
        Returns:
            List of service type names
        """
        return [service["service_type"] for service in self._configuration.services]
    
    def get_workspace_services(self, workspace_name: str) -> List[str]:
        """Get workspace-specific services.
        
        Args:
            workspace_name: Workspace name
            
        Returns:
            List of workspace-specific service type names
        """
        if workspace_name not in self._configuration.workspace_services:
            return []
        
        return [
            service["service_type"] 
            for service in self._configuration.workspace_services[workspace_name]
        ]
    
    def diagnose_container(self, container: Container) -> Dict[str, Any]:
        """Diagnose container configuration and health.
        
        Args:
            container: Container to diagnose
            
        Returns:
            Diagnostic information
        """
        diagnostics = {
            "registered_services": [],
            "failed_resolutions": [],
            "circular_dependencies": [],
            "missing_dependencies": [],
            "environment": self._configuration.environment.value,
            "total_services": len(self._configuration.services)
        }
        
        # Test service resolution
        for service_config in self._configuration.services:
            service_type_name = service_config["service_type"]
            
            try:
                # Try to resolve the service type
                service_type = self._registry._resolve_type(service_type_name)
                
                if container.is_registered(service_type):
                    diagnostics["registered_services"].append(service_type_name)
                    
                    # Try to resolve instance (only for singletons to avoid side effects)
                    if service_config.get("lifetime") == "singleton":
                        try:
                            container.resolve(service_type)
                        except CircularDependencyError:
                            diagnostics["circular_dependencies"].append(service_type_name)
                        except ServiceNotFoundError as e:
                            diagnostics["missing_dependencies"].append({
                                "service": service_type_name,
                                "missing": str(e)
                            })
                        except Exception as e:
                            diagnostics["failed_resolutions"].append({
                                "service": service_type_name,
                                "error": str(e)
                            })
                
            except Exception as e:
                diagnostics["failed_resolutions"].append({
                    "service": service_type_name,
                    "error": f"Type resolution failed: {e}"
                })
        
        return diagnostics
    
    def add_service(
        self,
        service_type: str,
        implementation_type: Optional[str] = None,
        factory: Optional[str] = None,
        lifetime: str = "transient",
        workspace_specific: bool = False
    ) -> None:
        """Add service to configuration.
        
        Args:
            service_type: Service type name
            implementation_type: Implementation type name
            factory: Factory function path
            lifetime: Service lifetime
            workspace_specific: Whether service is workspace-specific
        """
        self._configuration.add_service(
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=lifetime,
            workspace_specific=workspace_specific
        )
    
    def add_workspace_service(
        self,
        workspace_name: str,
        service_type: str,
        implementation_type: Optional[str] = None,
        factory: Optional[str] = None,
        lifetime: str = "transient"
    ) -> None:
        """Add workspace-specific service.
        
        Args:
            workspace_name: Workspace name
            service_type: Service type name
            implementation_type: Implementation type name
            factory: Factory function path
            lifetime: Service lifetime
        """
        self._configuration.add_workspace_service(
            workspace_name=workspace_name,
            service_type=service_type,
            implementation_type=implementation_type,
            factory=factory,
            lifetime=lifetime
        )
    
    def clear_containers(self) -> None:
        """Clear all cached containers."""
        self._containers.clear()
        logger.info("Cleared all cached containers")
    
    def _validate_configuration(self) -> List[str]:
        """Internal configuration validation.
        
        Returns:
            List of validation issues
        """
        issues = []
        
        # Check for duplicate service registrations
        service_types = [s["service_type"] for s in self._configuration.services]
        duplicates = [st for st in service_types if service_types.count(st) > 1]
        if duplicates:
            issues.append(f"Duplicate service registrations: {set(duplicates)}")
        
        # Validate service type names
        for service_config in self._configuration.services:
            service_type = service_config["service_type"]
            
            if not service_type:
                issues.append("Empty service type name found")
                continue
            
            # Check if type can be resolved
            try:
                self._registry._resolve_type(service_type)
            except Exception as e:
                issues.append(f"Cannot resolve service type '{service_type}': {e}")
            
            # Validate implementation type if provided
            impl_type = service_config.get("implementation_type")
            if impl_type:
                try:
                    self._registry._resolve_type(impl_type)
                except Exception as e:
                    issues.append(f"Cannot resolve implementation type '{impl_type}': {e}")
        
        if issues:
            logger.warning(f"Configuration validation found {len(issues)} issues")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("Configuration validation passed")
        
        return issues
    
    @property
    def configuration(self) -> DIConfiguration:
        """Get current configuration."""
        return self._configuration
    
    @property
    def environment(self) -> Environment:
        """Get current environment."""
        return self._configuration.environment


# Global service manager instance for convenience
_global_service_manager: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """Get global service manager instance.
    
    Returns:
        Global service manager (creates with defaults if none exists)
    """
    global _global_service_manager
    
    if _global_service_manager is None:
        # Create default service manager
        _global_service_manager = ServiceManager()
        logger.info("Created global service manager with default configuration")
    
    return _global_service_manager


def set_service_manager(manager: ServiceManager) -> None:
    """Set global service manager instance.
    
    Args:
        manager: Service manager to set as global
    """
    global _global_service_manager
    _global_service_manager = manager
    logger.info("Set new global service manager")


def configure_for_environment(
    environment: Environment,
    config_path: Optional[Path] = None
) -> ServiceManager:
    """Configure global service manager for environment.
    
    Args:
        environment: Target environment
        config_path: Optional path to environment-specific config
        
    Returns:
        Configured service manager
    """
    manager = ServiceManager.for_environment(environment, config_path)
    set_service_manager(manager)
    return manager


def create_default_container(workspace_name: Optional[str] = None) -> Container:
    """Create default container using global service manager.
    
    Args:
        workspace_name: Workspace name for workspace-specific services
        
    Returns:
        Configured container
    """
    return get_service_manager().create_container(workspace_name)
