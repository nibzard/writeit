"""Container factory for creating configured DI containers."""

from typing import Optional, Dict, Any
from pathlib import Path

from .container import Container
from .configuration import DIConfiguration, Environment
from .resolver import ServiceResolver
from .exceptions import InvalidServiceRegistrationError


class ContainerFactory:
    """Factory for creating and configuring DI containers.
    
    Provides convenient methods for bootstrapping containers with
    WriteIt's default services and configurations.
    
    Examples:
        # Create container with defaults
        container = ContainerFactory.create_default()
        
        # Create workspace-specific container
        container = ContainerFactory.create_for_workspace("my-project")
        
        # Create from configuration file
        container = ContainerFactory.create_from_config("services.yaml")
        
        # Create testing container
        container = ContainerFactory.create_testing()
    """
    
    _default_config: Optional[DIConfiguration] = None
    
    @classmethod
    def create_default(cls, workspace_name: Optional[str] = None) -> Container:
        """Create container with default WriteIt services.
        
        Args:
            workspace_name: Optional workspace name for workspace-specific services
            
        Returns:
            Configured container
        """
        config = cls._get_default_config()
        container = Container()
        config.apply_to_container(container, workspace_name)
        return container
    
    @classmethod
    def create_for_workspace(cls, workspace_name: str) -> Container:
        """Create container configured for specific workspace.
        
        Args:
            workspace_name: Workspace name
            
        Returns:
            Workspace-configured container
        """
        return cls.create_default(workspace_name)
    
    @classmethod
    def create_from_config(
        cls,
        config_path: str,
        workspace_name: Optional[str] = None
    ) -> Container:
        """Create container from configuration file.
        
        Args:
            config_path: Path to configuration file
            workspace_name: Optional workspace name
            
        Returns:
            Configured container
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            InvalidServiceRegistrationError: If configuration is invalid
        """
        try:
            config = DIConfiguration.from_file(config_path)
            container = Container()
            config.apply_to_container(container, workspace_name)
            return container
        except Exception as e:
            raise InvalidServiceRegistrationError(
                f"Failed to create container from config '{config_path}': {e}"
            )
    
    @classmethod
    def create_testing(
        cls,
        workspace_name: str = "test",
        use_mocks: bool = True
    ) -> Container:
        """Create container for testing.
        
        Args:
            workspace_name: Test workspace name
            use_mocks: Whether to use mock implementations
            
        Returns:
            Testing container
        """
        config = cls._get_default_config()
        config.set_environment(Environment.TESTING)
        
        container = Container()
        config.apply_to_container(container, workspace_name)
        
        if use_mocks:
            cls._register_test_mocks(container)
        
        return container
    
    @classmethod
    def create_production(
        cls,
        workspace_name: Optional[str] = None,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> Container:
        """Create container for production.
        
        Args:
            workspace_name: Optional workspace name
            config_overrides: Configuration overrides
            
        Returns:
            Production container
        """
        config = cls._get_default_config()
        config.set_environment(Environment.PRODUCTION)
        
        # Apply overrides
        if config_overrides:
            config.defaults.update(config_overrides)
        
        container = Container()
        config.apply_to_container(container, workspace_name)
        return container
    
    @classmethod
    def create_with_resolver(
        cls,
        workspace_name: Optional[str] = None
    ) -> ServiceResolver:
        """Create service resolver with default container.
        
        Args:
            workspace_name: Optional workspace name
            
        Returns:
            Service resolver
        """
        container = cls.create_default(workspace_name)
        return ServiceResolver(container)
    
    @classmethod
    def create_child_container(
        cls,
        parent: Container,
        workspace_name: Optional[str] = None
    ) -> Container:
        """Create child container with parent.
        
        Args:
            parent: Parent container
            workspace_name: Optional workspace name for child-specific services
            
        Returns:
            Child container
        """
        child = parent.create_child_container()
        
        # Add workspace-specific services if needed
        if workspace_name:
            config = cls._get_default_config()
            if workspace_name in config.workspace_services:
                # Apply only workspace-specific services to child
                workspace_config = DIConfiguration(
                    services=[],
                    workspace_services={workspace_name: config.workspace_services[workspace_name]}
                )
                workspace_config.apply_to_container(child, workspace_name)
        
        return child
    
    @classmethod
    def _get_default_config(cls) -> DIConfiguration:
        """Get default configuration, loading if necessary."""
        if cls._default_config is None:
            # Try to load from default file
            default_path = Path(__file__).parent / "default_services.yaml"
            if default_path.exists():
                cls._default_config = DIConfiguration.from_file(default_path)
            else:
                # Create programmatic default
                cls._default_config = DIConfiguration.create_default()
        
        return cls._default_config
    
    @classmethod
    def _register_test_mocks(cls, container: Container) -> None:
        """Register mock implementations for testing."""
        # This would register mock implementations
        # For now, we'll use the same implementations but could switch to mocks
        pass
    
    @classmethod
    def reset_default_config(cls) -> None:
        """Reset cached default configuration."""
        cls._default_config = None


class WorkspaceContainerManager:
    """Manager for workspace-specific containers.
    
    Maintains containers per workspace to ensure proper isolation.
    
    Examples:
        manager = WorkspaceContainerManager()
        
        # Get container for workspace
        container = manager.get_container("my-project")
        
        # Containers are cached per workspace
        same_container = manager.get_container("my-project")
        assert container is same_container
    """
    
    def __init__(self) -> None:
        self._containers: Dict[str, Container] = {}
        self._global_container: Optional[Container] = None
    
    def get_container(self, workspace_name: str) -> Container:
        """Get container for workspace.
        
        Args:
            workspace_name: Workspace name
            
        Returns:
            Workspace container
        """
        if workspace_name not in self._containers:
            self._containers[workspace_name] = ContainerFactory.create_for_workspace(workspace_name)
        
        return self._containers[workspace_name]
    
    def get_global_container(self) -> Container:
        """Get global container (no workspace).
        
        Returns:
            Global container
        """
        if self._global_container is None:
            self._global_container = ContainerFactory.create_default()
        
        return self._global_container
    
    def create_scoped_container(self, workspace_name: str) -> Container:
        """Create new scoped container for workspace.
        
        Args:
            workspace_name: Workspace name
            
        Returns:
            New container instance
        """
        parent = self.get_container(workspace_name)
        return parent.create_child_container()
    
    def invalidate_workspace(self, workspace_name: str) -> None:
        """Invalidate cached container for workspace.
        
        Args:
            workspace_name: Workspace to invalidate
        """
        self._containers.pop(workspace_name, None)
    
    def clear_all(self) -> None:
        """Clear all cached containers."""
        self._containers.clear()
        self._global_container = None


# Global instance for convenience
workspace_containers = WorkspaceContainerManager()