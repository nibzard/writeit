"""Dependency injection configuration for WriteIt application.

This module provides centralized registration of all application services,
repositories, and command handlers.
"""

import logging
from typing import Dict, Type, Any
from pathlib import Path

from ...shared.dependencies.container import Container, ServiceLifetime
from ...shared.events.event_bus import EventBus

# Domain Services
from ...domains.pipeline.services import (
    PipelineValidationService,
    PipelineExecutionService,
    StepDependencyService
)
from ...domains.workspace.services import (
    WorkspaceIsolationService,
    WorkspaceTemplateService
)
from ...domains.content.services import (
    TemplateRenderingService,
    ContentValidationService
)
from ...domains.execution.services import (
    LLMOrchestrationService,
    CacheManagementService,
    TokenAnalyticsService
)

# Repository Interfaces
from ...domains.pipeline.repositories import (
    PipelineTemplateRepository,
    PipelineRunRepository,
    StepExecutionRepository
)
from ...domains.workspace.repositories import (
    WorkspaceRepository,
    WorkspaceConfigRepository
)
from ...domains.content.repositories import (
    ContentTemplateRepository,
    StylePrimerRepository,
    GeneratedContentRepository
)
from ...domains.execution.repositories import (
    LLMCacheRepository,
    TokenUsageRepository
)

# Infrastructure Repository Implementations
from ...infrastructure.persistence.lmdb_repositories import (
    LMDBPipelineTemplateRepository,
    LMDBPipelineRunRepository,
    LMDBStepExecutionRepository,
    LMDBWorkspaceRepository,
    LMDBWorkspaceConfigRepository,
    LMDBContentTemplateRepository,
    LMDBStylePrimerRepository,
    LMDBGeneratedContentRepository,
    LMDBLLMCacheRepository,
    LMDBTokenUsageRepository
)

# Command Handlers
from ...application.commands.handlers.pipeline_template_handlers import (
    ConcreteCreatePipelineTemplateCommandHandler,
    ConcreteUpdatePipelineTemplateCommandHandler,
    ConcreteDeletePipelineTemplateCommandHandler,
    ConcretePublishPipelineTemplateCommandHandler,
    ConcreteValidatePipelineTemplateCommandHandler
)
from ...application.commands.handlers.pipeline_execution_handlers import (
    ConcreteExecutePipelineCommandHandler,
    ConcreteCancelPipelineExecutionCommandHandler,
    ConcreteRetryPipelineExecutionCommandHandler,
    ConcreteStreamingPipelineExecutionCommandHandler
)
from ...application.commands.handlers.workspace_handlers import (
    ConcreteCreateWorkspaceCommandHandler,
    ConcreteSwitchWorkspaceCommandHandler,
    ConcreteDeleteWorkspaceCommandHandler,
    ConcreteConfigureWorkspaceCommandHandler,
    ConcreteInitializeWorkspaceCommandHandler,
    ConcreteArchiveWorkspaceCommandHandler,
    ConcreteRestoreWorkspaceCommandHandler,
    ConcreteCreateWorkspaceTemplateCommandHandler,
    ConcreteApplyWorkspaceTemplateCommandHandler
)
from ...application.commands.handlers.content_handlers import (
    ConcreteCreateTemplateCommandHandler,
    ConcreteUpdateTemplateCommandHandler,
    ConcreteDeleteTemplateCommandHandler,
    ConcreteValidateTemplateCommandHandler,
    ConcreteCreateStylePrimerCommandHandler,
    ConcreteCreateGeneratedContentCommandHandler
)

# Command Handler Interfaces
from ...application.commands.pipeline_commands import (
    CreatePipelineTemplateCommandHandler,
    UpdatePipelineTemplateCommandHandler,
    DeletePipelineTemplateCommandHandler,
    PublishPipelineTemplateCommandHandler,
    ValidatePipelineTemplateCommandHandler,
    ExecutePipelineCommandHandler,
    CancelPipelineExecutionCommandHandler,
    RetryPipelineExecutionCommandHandler,
    StreamingPipelineExecutionCommandHandler
)
from ...application.commands.workspace_commands import (
    CreateWorkspaceCommandHandler,
    SwitchWorkspaceCommandHandler,
    DeleteWorkspaceCommandHandler,
    ConfigureWorkspaceCommandHandler,
    InitializeWorkspaceCommandHandler,
    ArchiveWorkspaceCommandHandler,
    RestoreWorkspaceCommandHandler,
    CreateWorkspaceTemplateCommandHandler,
    ApplyWorkspaceTemplateCommandHandler
)
from ...application.commands.content_commands import (
    CreateTemplateCommandHandler,
    UpdateTemplateCommandHandler,
    DeleteTemplateCommandHandler,
    ValidateTemplateCommandHandler,
    CreateStylePrimerCommandHandler,
    CreateGeneratedContentCommandHandler
)

logger = logging.getLogger(__name__)


class DIConfiguration:
    """Centralized dependency injection configuration."""
    
    @staticmethod
    def configure_services(
        container: Container, 
        base_path: Path = None,
        workspace_name: str = None
    ) -> Container:
        """Configure all services in the dependency injection container.
        
        Args:
            container: DI container to configure
            base_path: Base path for file operations
            workspace_name: Current workspace name
            
        Returns:
            Configured container
        """
        logger.info("Configuring dependency injection services")
        
        # Configure shared infrastructure
        container = DIConfiguration._configure_infrastructure(container, base_path, workspace_name)
        
        # Configure domain services
        container = DIConfiguration._configure_domain_services(container)
        
        # Configure repositories
        container = DIConfiguration._configure_repositories(container)
        
        # Configure command handlers
        container = DIConfiguration._configure_command_handlers(container)
        
        logger.info("Dependency injection configuration completed")
        return container
    
    @staticmethod
    def _configure_infrastructure(
        container: Container, 
        base_path: Path = None,
        workspace_name: str = None
    ) -> Container:
        """Configure infrastructure services."""
        
        # Event Bus (singleton)
        container.register_singleton(EventBus, lambda: EventBus())
        
        return container
    
    @staticmethod
    def _configure_domain_services(container: Container) -> Container:
        """Configure domain services."""
        
        # Pipeline Domain Services
        container.register(
            PipelineValidationService,
            PipelineValidationService,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            PipelineExecutionService,
            PipelineExecutionService,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            StepDependencyService,
            StepDependencyService,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Workspace Domain Services
        container.register(
            WorkspaceIsolationService,
            WorkspaceIsolationService,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            WorkspaceTemplateService,
            WorkspaceTemplateService,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Content Domain Services
        container.register(
            TemplateRenderingService,
            TemplateRenderingService,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ContentValidationService,
            ContentValidationService,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Execution Domain Services
        container.register(
            LLMOrchestrationService,
            LLMOrchestrationService,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            CacheManagementService,
            CacheManagementService,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            TokenAnalyticsService,
            TokenAnalyticsService,
            lifetime=ServiceLifetime.SCOPED
        )
        
        return container
    
    @staticmethod
    def _configure_repositories(container: Container) -> Container:
        """Configure repository implementations."""
        
        # Pipeline Repositories
        container.register(
            PipelineTemplateRepository,
            LMDBPipelineTemplateRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            PipelineRunRepository,
            LMDBPipelineRunRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            StepExecutionRepository,
            LMDBStepExecutionRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Workspace Repositories
        container.register(
            WorkspaceRepository,
            LMDBWorkspaceRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            WorkspaceConfigRepository,
            LMDBWorkspaceConfigRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Content Repositories
        container.register(
            ContentTemplateRepository,
            LMDBContentTemplateRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            StylePrimerRepository,
            LMDBStylePrimerRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GeneratedContentRepository,
            LMDBGeneratedContentRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Execution Repositories
        container.register(
            LLMCacheRepository,
            LMDBLLMCacheRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            TokenUsageRepository,
            LMDBTokenUsageRepository,
            lifetime=ServiceLifetime.SCOPED
        )
        
        return container
    
    @staticmethod
    def _configure_command_handlers(container: Container) -> Container:
        """Configure command handlers with their interfaces."""
        
        # Pipeline Template Command Handlers
        container.register(
            CreatePipelineTemplateCommandHandler,
            ConcreteCreatePipelineTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            UpdatePipelineTemplateCommandHandler,
            ConcreteUpdatePipelineTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            DeletePipelineTemplateCommandHandler,
            ConcreteDeletePipelineTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            PublishPipelineTemplateCommandHandler,
            ConcretePublishPipelineTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ValidatePipelineTemplateCommandHandler,
            ConcreteValidatePipelineTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Pipeline Execution Command Handlers
        container.register(
            ExecutePipelineCommandHandler,
            ConcreteExecutePipelineCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            CancelPipelineExecutionCommandHandler,
            ConcreteCancelPipelineExecutionCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            RetryPipelineExecutionCommandHandler,
            ConcreteRetryPipelineExecutionCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            StreamingPipelineExecutionCommandHandler,
            ConcreteStreamingPipelineExecutionCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Workspace Command Handlers
        container.register(
            CreateWorkspaceCommandHandler,
            ConcreteCreateWorkspaceCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            SwitchWorkspaceCommandHandler,
            ConcreteSwitchWorkspaceCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            DeleteWorkspaceCommandHandler,
            ConcreteDeleteWorkspaceCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ConfigureWorkspaceCommandHandler,
            ConcreteConfigureWorkspaceCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            InitializeWorkspaceCommandHandler,
            ConcreteInitializeWorkspaceCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ArchiveWorkspaceCommandHandler,
            ConcreteArchiveWorkspaceCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            RestoreWorkspaceCommandHandler,
            ConcreteRestoreWorkspaceCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            CreateWorkspaceTemplateCommandHandler,
            ConcreteCreateWorkspaceTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ApplyWorkspaceTemplateCommandHandler,
            ConcreteApplyWorkspaceTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Content Command Handlers
        container.register(
            CreateTemplateCommandHandler,
            ConcreteCreateTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            UpdateTemplateCommandHandler,
            ConcreteUpdateTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            DeleteTemplateCommandHandler,
            ConcreteDeleteTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ValidateTemplateCommandHandler,
            ConcreteValidateTemplateCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            CreateStylePrimerCommandHandler,
            ConcreteCreateStylePrimerCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            CreateGeneratedContentCommandHandler,
            ConcreteCreateGeneratedContentCommandHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        
        return container
    
    @staticmethod
    def create_container(
        base_path: Path = None,
        workspace_name: str = None
    ) -> Container:
        """Create and configure a new DI container.
        
        Args:
            base_path: Base path for file operations
            workspace_name: Current workspace name
            
        Returns:
            Configured container
        """
        container = Container()
        return DIConfiguration.configure_services(container, base_path, workspace_name)
    
    @staticmethod
    def get_service_types() -> Dict[str, Type[Any]]:
        """Get mapping of service names to their types for discovery.
        
        Returns:
            Dictionary mapping service names to types
        """
        return {
            # Event Bus
            "event_bus": EventBus,
            
            # Domain Services
            "pipeline_validation_service": PipelineValidationService,
            "pipeline_execution_service": PipelineExecutionService,
            "step_dependency_service": StepDependencyService,
            "workspace_isolation_service": WorkspaceIsolationService,
            "workspace_template_service": WorkspaceTemplateService,
            "template_rendering_service": TemplateRenderingService,
            "content_validation_service": ContentValidationService,
            "llm_orchestration_service": LLMOrchestrationService,
            "cache_management_service": CacheManagementService,
            "token_analytics_service": TokenAnalyticsService,
            
            # Repository Interfaces
            "pipeline_template_repository": PipelineTemplateRepository,
            "pipeline_run_repository": PipelineRunRepository,
            "step_execution_repository": StepExecutionRepository,
            "workspace_repository": WorkspaceRepository,
            "workspace_config_repository": WorkspaceConfigRepository,
            "content_template_repository": ContentTemplateRepository,
            "style_primer_repository": StylePrimerRepository,
            "generated_content_repository": GeneratedContentRepository,
            "llm_cache_repository": LLMCacheRepository,
            "token_usage_repository": TokenUsageRepository,
            
            # Command Handlers
            "create_pipeline_template_handler": CreatePipelineTemplateCommandHandler,
            "update_pipeline_template_handler": UpdatePipelineTemplateCommandHandler,
            "delete_pipeline_template_handler": DeletePipelineTemplateCommandHandler,
            "publish_pipeline_template_handler": PublishPipelineTemplateCommandHandler,
            "validate_pipeline_template_handler": ValidatePipelineTemplateCommandHandler,
            "execute_pipeline_handler": ExecutePipelineCommandHandler,
            "cancel_pipeline_execution_handler": CancelPipelineExecutionCommandHandler,
            "retry_pipeline_execution_handler": RetryPipelineExecutionCommandHandler,
            "streaming_pipeline_execution_handler": StreamingPipelineExecutionCommandHandler,
            "create_workspace_handler": CreateWorkspaceCommandHandler,
            "switch_workspace_handler": SwitchWorkspaceCommandHandler,
            "delete_workspace_handler": DeleteWorkspaceCommandHandler,
            "configure_workspace_handler": ConfigureWorkspaceCommandHandler,
            "initialize_workspace_handler": InitializeWorkspaceCommandHandler,
            "archive_workspace_handler": ArchiveWorkspaceCommandHandler,
            "restore_workspace_handler": RestoreWorkspaceCommandHandler,
            "create_workspace_template_handler": CreateWorkspaceTemplateCommandHandler,
            "apply_workspace_template_handler": ApplyWorkspaceTemplateCommandHandler,
            "create_template_handler": CreateTemplateCommandHandler,
            "update_template_handler": UpdateTemplateCommandHandler,
            "delete_template_handler": DeleteTemplateCommandHandler,
            "validate_template_handler": ValidateTemplateCommandHandler,
            "create_style_primer_handler": CreateStylePrimerCommandHandler,
            "create_generated_content_handler": CreateGeneratedContentCommandHandler,
        }