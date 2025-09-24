"""Dependency injection configuration management."""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import yaml
import json
from enum import Enum

from .registry import ServiceRegistry
from .container import Container, ServiceLifetime
from .exceptions import InvalidServiceRegistrationError


class Environment(str, Enum):
    """Environment types for configuration."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class DIConfiguration:
    """Dependency injection configuration.
    
    Supports environment-specific configurations, workspace-aware services,
    and hierarchical configuration loading.
    
    Examples:
        # Load from file
        config = DIConfiguration.from_file("services.yaml")
        
        # Apply to container
        container = Container()
        config.apply_to_container(container, workspace="test")
        
        # Environment-specific configuration
        config.set_environment(Environment.TESTING)
    """
    
    services: List[Dict[str, Any]] = field(default_factory=list)
    environment: Environment = Environment.DEVELOPMENT
    workspace_services: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> 'DIConfiguration':
        """Load configuration from file.
        
        Args:
            file_path: Path to configuration file (YAML or JSON)
            
        Returns:
            Configuration instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                if path.suffix.lower() in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif path.suffix.lower() == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {path.suffix}")
            
            return cls.from_dict(data)
        
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ValueError(f"Invalid configuration file format: {e}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DIConfiguration':
        """Create configuration from dictionary.
        
        Args:
            data: Configuration data
            
        Returns:
            Configuration instance
        """
        return cls(
            services=data.get('services', []),
            environment=Environment(data.get('environment', 'development')),
            workspace_services=data.get('workspace_services', {}),
            defaults=data.get('defaults', {})
        )
    
    @classmethod
    def create_default(cls) -> 'DIConfiguration':
        """Create default configuration for WriteIt.
        
        Returns:
            Default configuration with all implemented WriteIt services
        """
        services = [
            # Repository interfaces (with infrastructure implementations)
            {
                "service_type": "writeit.domains.pipeline.repositories.PipelineTemplateRepository",
                "implementation_type": "writeit.infrastructure.persistence.LMDBPipelineTemplateRepository",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.pipeline.repositories.PipelineRunRepository",
                "implementation_type": "writeit.infrastructure.persistence.LMDBPipelineRunRepository",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.pipeline.repositories.StepExecutionRepository",
                "implementation_type": "writeit.infrastructure.persistence.LMDBStepExecutionRepository",
                "lifetime": "singleton"
            },
            
            # Workspace repositories
            {
                "service_type": "writeit.domains.workspace.repositories.WorkspaceRepository",
                "implementation_type": "writeit.infrastructure.persistence.FileSystemWorkspaceRepository",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.workspace.repositories.WorkspaceConfigRepository",
                "implementation_type": "writeit.infrastructure.persistence.LMDBWorkspaceConfigRepository",
                "lifetime": "singleton"
            },
            
            # Content repositories
            {
                "service_type": "writeit.domains.content.repositories.ContentTemplateRepository",
                "implementation_type": "writeit.infrastructure.persistence.FileSystemContentTemplateRepository",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.content.repositories.StylePrimerRepository",
                "implementation_type": "writeit.infrastructure.persistence.FileSystemStylePrimerRepository",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.content.repositories.GeneratedContentRepository",
                "implementation_type": "writeit.infrastructure.persistence.LMDBGeneratedContentRepository",
                "lifetime": "singleton"
            },
            
            # Execution repositories
            {
                "service_type": "writeit.domains.execution.repositories.LLMCacheRepository",
                "implementation_type": "writeit.infrastructure.persistence.MemoryLLMCacheRepository",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.execution.repositories.TokenUsageRepository",
                "implementation_type": "writeit.infrastructure.persistence.LMDBTokenUsageRepository",
                "lifetime": "singleton"
            },
            
            # Pipeline Domain Services
            {
                "service_type": "writeit.domains.pipeline.services.PipelineValidationService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.pipeline.services.PipelineExecutionService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.pipeline.services.StepDependencyService",
                "lifetime": "singleton"
            },
            
            # Storage Domain Services
            {
                "service_type": "writeit.domains.storage.services.StorageManagementService",
                "lifetime": "singleton"
            },
            
            # Workspace Domain Services
            {
                "service_type": "writeit.domains.workspace.services.WorkspaceManagementService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.workspace.services.WorkspaceConfigurationService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.workspace.services.WorkspaceAnalyticsService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.workspace.services.WorkspaceIsolationService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.workspace.services.WorkspaceTemplateService",
                "lifetime": "singleton"
            },
            
            # Content Domain Services
            {
                "service_type": "writeit.domains.content.services.TemplateManagementService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.content.services.StyleManagementService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.content.services.ContentGenerationService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.content.services.TemplateRenderingService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.content.services.ContentValidationService",
                "lifetime": "singleton"
            },
            
            # Execution Domain Services
            {
                "service_type": "writeit.domains.execution.services.LLMOrchestrationService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.execution.services.CacheManagementService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.domains.execution.services.TokenAnalyticsService",
                "lifetime": "singleton"
            },
            
            # Infrastructure Services
            {
                "service_type": "writeit.infrastructure.persistence.backup_manager.BackupManager",
                "implementation_type": "writeit.infrastructure.persistence.backup_manager.create_backup_manager",
                "factory": true,
                "lifetime": "singleton"
            },
            
            # Application Services
            {
                "service_type": "writeit.application.services.PipelineApplicationService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.application.services.WorkspaceApplicationService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.application.services.ContentApplicationService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.application.services.ExecutionApplicationService",
                "lifetime": "singleton"
            },
            {
                "service_type": "writeit.application.services.migration_application_service.DefaultMigrationApplicationService",
                "lifetime": "singleton"
            }
        ]
        
        return cls(
            services=services,
            environment=Environment.DEVELOPMENT,
            defaults={
                "storage_path": "~/.writeit",
                "cache_size": 1000,
                "enable_metrics": True
            }
        )
    
    def apply_to_container(
        self,
        container: Container,
        workspace_name: Optional[str] = None
    ) -> None:
        """Apply configuration to container.
        
        Args:
            container: Container to configure
            workspace_name: Current workspace name
        """
        registry = ServiceRegistry()
        
        # Register global services
        for service_config in self.services:
            self._register_service(registry, service_config)
        
        # Register workspace-specific services
        if workspace_name and workspace_name in self.workspace_services:
            for service_config in self.workspace_services[workspace_name]:
                self._register_service(registry, service_config, workspace_specific=True)
        
        # Apply all registrations
        registry.apply_to_container(container, workspace_name)
    
    def _register_service(
        self,
        registry: ServiceRegistry,
        config: Dict[str, Any],
        workspace_specific: bool = False
    ) -> None:
        """Register single service from configuration."""
        registry.register(
            service_type=config["service_type"],
            implementation_type=config.get("implementation_type"),
            factory=config.get("factory"),
            lifetime=config.get("lifetime", "transient"),
            workspace_specific=workspace_specific or config.get("workspace_specific", False),
            dependencies=config.get("dependencies")
        )
    
    def set_environment(self, environment: Environment) -> None:
        """Set current environment.
        
        Args:
            environment: Environment to set
        """
        self.environment = environment
    
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
        service_config = {
            "service_type": service_type,
            "lifetime": lifetime,
            "workspace_specific": workspace_specific
        }
        
        if implementation_type:
            service_config["implementation_type"] = implementation_type
        
        if factory:
            service_config["factory"] = factory
        
        self.services.append(service_config)
    
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
        if workspace_name not in self.workspace_services:
            self.workspace_services[workspace_name] = []
        
        service_config = {
            "service_type": service_type,
            "lifetime": lifetime
        }
        
        if implementation_type:
            service_config["implementation_type"] = implementation_type
        
        if factory:
            service_config["factory"] = factory
        
        self.workspace_services[workspace_name].append(service_config)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return {
            "services": self.services,
            "environment": self.environment.value,
            "workspace_services": self.workspace_services,
            "defaults": self.defaults
        }
    
    def save_to_file(self, file_path: Union[str, Path]) -> None:
        """Save configuration to file.
        
        Args:
            file_path: Path to save configuration
        """
        path = Path(file_path)
        data = self.to_dict()
        
        with open(path, 'w', encoding='utf-8') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                yaml.dump(data, f, default_flow_style=False)
            elif path.suffix.lower() == '.json':
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
    
    def merge(self, other: 'DIConfiguration') -> 'DIConfiguration':
        """Merge with another configuration.
        
        Args:
            other: Configuration to merge
            
        Returns:
            New merged configuration
        """
        merged_services = self.services + other.services
        merged_workspace_services = {**self.workspace_services}
        
        for workspace, services in other.workspace_services.items():
            if workspace in merged_workspace_services:
                merged_workspace_services[workspace].extend(services)
            else:
                merged_workspace_services[workspace] = services
        
        merged_defaults = {**self.defaults, **other.defaults}
        
        return DIConfiguration(
            services=merged_services,
            environment=other.environment,  # Use other's environment
            workspace_services=merged_workspace_services,
            defaults=merged_defaults
        )


class DIConfigurationBuilder:
    """Builder for creating DI configurations fluently.
    
    Examples:
        config = (DIConfigurationBuilder()
            .add_singleton("UserService", "UserServiceImpl")
            .add_transient("MessageHandler")
            .add_workspace_service("test", "TestService")
            .set_environment(Environment.TESTING)
            .build())
    """
    
    def __init__(self) -> None:
        self._services: List[Dict[str, Any]] = []
        self._workspace_services: Dict[str, List[Dict[str, Any]]] = {}
        self._environment = Environment.DEVELOPMENT
        self._defaults: Dict[str, Any] = {}
    
    def add_singleton(
        self,
        service_type: str,
        implementation_type: Optional[str] = None,
        factory: Optional[str] = None
    ) -> 'DIConfigurationBuilder':
        """Add singleton service."""
        return self._add_service(service_type, implementation_type, factory, "singleton")
    
    def add_transient(
        self,
        service_type: str,
        implementation_type: Optional[str] = None,
        factory: Optional[str] = None
    ) -> 'DIConfigurationBuilder':
        """Add transient service."""
        return self._add_service(service_type, implementation_type, factory, "transient")
    
    def add_scoped(
        self,
        service_type: str,
        implementation_type: Optional[str] = None,
        factory: Optional[str] = None
    ) -> 'DIConfigurationBuilder':
        """Add scoped service."""
        return self._add_service(service_type, implementation_type, factory, "scoped")
    
    def add_workspace_service(
        self,
        workspace_name: str,
        service_type: str,
        implementation_type: Optional[str] = None,
        lifetime: str = "transient"
    ) -> 'DIConfigurationBuilder':
        """Add workspace-specific service."""
        if workspace_name not in self._workspace_services:
            self._workspace_services[workspace_name] = []
        
        service_config = {
            "service_type": service_type,
            "lifetime": lifetime
        }
        
        if implementation_type:
            service_config["implementation_type"] = implementation_type
        
        self._workspace_services[workspace_name].append(service_config)
        return self
    
    def set_environment(self, environment: Environment) -> 'DIConfigurationBuilder':
        """Set environment."""
        self._environment = environment
        return self
    
    def add_default(self, key: str, value: Any) -> 'DIConfigurationBuilder':
        """Add default value."""
        self._defaults[key] = value
        return self
    
    def build(self) -> DIConfiguration:
        """Build configuration."""
        return DIConfiguration(
            services=self._services,
            environment=self._environment,
            workspace_services=self._workspace_services,
            defaults=self._defaults
        )
    
    def _add_service(
        self,
        service_type: str,
        implementation_type: Optional[str],
        factory: Optional[str],
        lifetime: str
    ) -> 'DIConfigurationBuilder':
        """Internal method to add service."""
        service_config = {
            "service_type": service_type,
            "lifetime": lifetime
        }
        
        if implementation_type:
            service_config["implementation_type"] = implementation_type
        
        if factory:
            service_config["factory"] = factory
        
        self._services.append(service_config)
        return self