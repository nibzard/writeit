"""Dependency injection configuration for WriteIt application.

This module provides centralized registration of all application services,
repositories, and command handlers.
"""

import logging
from typing import Dict, Type, Any
from pathlib import Path

from ..shared.dependencies.container import Container, ServiceLifetime
from ..shared.events.event_bus import EventBus

# Domain Services
from ..domains.pipeline.services import (
    PipelineValidationService,
    PipelineExecutionService,
    StepDependencyService
)
from ..domains.workspace.services import (
    WorkspaceIsolationService,
    WorkspaceTemplateService
)
from ..domains.content.services import (
    TemplateRenderingService,
    ContentValidationService
)
from ..domains.execution.services import (
    LLMOrchestrationService,
    CacheManagementService,
    TokenAnalyticsService
)

# Repository Interfaces
from ..domains.pipeline.repositories import (
    PipelineTemplateRepository,
    PipelineRunRepository,
    StepExecutionRepository
)
from ..domains.workspace.repositories import (
    WorkspaceRepository,
    WorkspaceConfigRepository
)
from ..domains.content.repositories import (
    ContentTemplateRepository,
    StylePrimerRepository,
    GeneratedContentRepository
)
from ..domains.execution.repositories import (
    LLMCacheRepository,
    TokenUsageRepository
)

# Infrastructure Repository Implementations
from ..infrastructure.persistence.lmdb_repositories import (
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
from ..application.commands.handlers.pipeline_template_handlers import (
    ConcreteCreatePipelineTemplateCommandHandler,
    ConcreteUpdatePipelineTemplateCommandHandler,
    ConcreteDeletePipelineTemplateCommandHandler,
    ConcretePublishPipelineTemplateCommandHandler,
    ConcreteValidatePipelineTemplateCommandHandler
)
from ..application.commands.handlers.pipeline_execution_handlers import (
    ConcreteExecutePipelineCommandHandler,
    ConcreteCancelPipelineExecutionCommandHandler,
    ConcreteRetryPipelineExecutionCommandHandler,
    ConcreteStreamingPipelineExecutionCommandHandler
)
from ..application.commands.handlers.workspace_handlers import (
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
from ..application.commands.handlers.content_handlers import (
    ConcreteCreateTemplateCommandHandler,
    ConcreteUpdateTemplateCommandHandler,
    ConcreteDeleteTemplateCommandHandler,
    ConcreteValidateTemplateCommandHandler,
    ConcreteCreateStylePrimerCommandHandler,
    ConcreteCreateGeneratedContentCommandHandler
)

# Command Handler Interfaces
from ..application.commands.pipeline_commands import (
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
from ..application.commands.workspace_commands import (
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
from ..application.commands.content_commands import (
    CreateTemplateCommandHandler,
    UpdateTemplateCommandHandler,
    DeleteTemplateCommandHandler,
    ValidateTemplateCommandHandler,
    CreateStylePrimerCommandHandler,
    CreateGeneratedContentCommandHandler
)

# Query Handlers
from ..application.queries.handlers.pipeline_handlers import (
    ConcreteGetPipelineTemplateQueryHandler,
    ConcreteListPipelineTemplatesQueryHandler,
    ConcreteSearchPipelineTemplatesQueryHandler,
    ConcreteGetPipelineRunQueryHandler,
    ConcreteListPipelineRunsQueryHandler,
    ConcreteGetPipelineAnalyticsQueryHandler,
)
from ..application.queries.handlers.workspace_handlers import (
    ConcreteGetWorkspacesQueryHandler,
    ConcreteGetWorkspaceQueryHandler,
    ConcreteGetActiveWorkspaceQueryHandler,
    ConcreteGetWorkspaceConfigQueryHandler,
    ConcreteGetWorkspaceStatsQueryHandler,
    ConcreteSearchWorkspacesQueryHandler,
    ConcreteValidateWorkspaceNameQueryHandler,
    ConcreteCheckWorkspaceExistsQueryHandler,
    ConcreteGetWorkspaceHealthQueryHandler,
    ConcreteGetWorkspaceTemplatesQueryHandler,
    ConcreteGetWorkspaceTemplateQueryHandler,
)
from ..application.queries.handlers.content_handlers import (
    ConcreteGetTemplatesQueryHandler,
    ConcreteGetTemplateQueryHandler,
    ConcreteGetTemplateByNameQueryHandler,
    ConcreteSearchTemplatesQueryHandler,
    ConcreteGetGeneratedContentQueryHandler,
    ConcreteListGeneratedContentQueryHandler,
    ConcreteSearchGeneratedContentQueryHandler,
    ConcreteGetStylePrimersQueryHandler,
    ConcreteGetStylePrimerQueryHandler,
    ConcreteGetContentAnalyticsQueryHandler,
    ConcreteGetPopularTemplatesQueryHandler,
    ConcreteValidateTemplateQueryHandler,
    ConcreteCheckTemplateExistsQueryHandler,
)

# Query Handler Interfaces
from ..application.queries.pipeline_queries import (
    GetPipelineTemplateQueryHandler,
    ListPipelineTemplatesQueryHandler,
    SearchPipelineTemplatesQueryHandler,
    GetPipelineRunQueryHandler,
    ListPipelineRunsQueryHandler,
    GetPipelineAnalyticsQueryHandler,
)
from ..application.queries.workspace_queries import (
    GetWorkspacesQueryHandler,
    GetWorkspaceQueryHandler,
    GetActiveWorkspaceQueryHandler,
    GetWorkspaceConfigQueryHandler,
    GetWorkspaceStatsQueryHandler,
    SearchWorkspacesQueryHandler,
    ValidateWorkspaceNameQueryHandler,
    CheckWorkspaceExistsQueryHandler,
    GetWorkspaceHealthQueryHandler,
    GetWorkspaceTemplatesQueryHandler,
    GetWorkspaceTemplateQueryHandler,
)
from ..application.queries.content_queries import (
    GetTemplatesQueryHandler,
    GetTemplateQueryHandler,
    GetTemplateByNameQueryHandler,
    SearchTemplatesQueryHandler,
    GetGeneratedContentQueryHandler,
    ListGeneratedContentQueryHandler,
    SearchGeneratedContentQueryHandler,
    GetStylePrimersQueryHandler,
    GetStylePrimerQueryHandler,
    GetContentAnalyticsQueryHandler,
    GetPopularTemplatesQueryHandler,
    ValidateTemplateQueryHandler,
    CheckTemplateExistsQueryHandler,
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
        
        # Configure query handlers
        container = DIConfiguration._configure_query_handlers(container)
        
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
    def _configure_query_handlers(container: Container) -> Container:
        """Configure query handlers with their interfaces."""
        
        # Pipeline Query Handlers
        container.register(
            GetPipelineTemplateQueryHandler,
            ConcreteGetPipelineTemplateQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ListPipelineTemplatesQueryHandler,
            ConcreteListPipelineTemplatesQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            SearchPipelineTemplatesQueryHandler,
            ConcreteSearchPipelineTemplatesQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetPipelineRunQueryHandler,
            ConcreteGetPipelineRunQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ListPipelineRunsQueryHandler,
            ConcreteListPipelineRunsQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetPipelineAnalyticsQueryHandler,
            ConcreteGetPipelineAnalyticsQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Workspace Query Handlers
        container.register(
            GetWorkspacesQueryHandler,
            ConcreteGetWorkspacesQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetWorkspaceQueryHandler,
            ConcreteGetWorkspaceQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetActiveWorkspaceQueryHandler,
            ConcreteGetActiveWorkspaceQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetWorkspaceConfigQueryHandler,
            ConcreteGetWorkspaceConfigQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetWorkspaceStatsQueryHandler,
            ConcreteGetWorkspaceStatsQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            SearchWorkspacesQueryHandler,
            ConcreteSearchWorkspacesQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ValidateWorkspaceNameQueryHandler,
            ConcreteValidateWorkspaceNameQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            CheckWorkspaceExistsQueryHandler,
            ConcreteCheckWorkspaceExistsQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetWorkspaceHealthQueryHandler,
            ConcreteGetWorkspaceHealthQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetWorkspaceTemplatesQueryHandler,
            ConcreteGetWorkspaceTemplatesQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetWorkspaceTemplateQueryHandler,
            ConcreteGetWorkspaceTemplateQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        
        # Content Query Handlers
        container.register(
            GetTemplatesQueryHandler,
            ConcreteGetTemplatesQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetTemplateQueryHandler,
            ConcreteGetTemplateQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetTemplateByNameQueryHandler,
            ConcreteGetTemplateByNameQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            SearchTemplatesQueryHandler,
            ConcreteSearchTemplatesQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetGeneratedContentQueryHandler,
            ConcreteGetGeneratedContentQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ListGeneratedContentQueryHandler,
            ConcreteListGeneratedContentQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            SearchGeneratedContentQueryHandler,
            ConcreteSearchGeneratedContentQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetStylePrimersQueryHandler,
            ConcreteGetStylePrimersQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetStylePrimerQueryHandler,
            ConcreteGetStylePrimerQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetContentAnalyticsQueryHandler,
            ConcreteGetContentAnalyticsQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            GetPopularTemplatesQueryHandler,
            ConcreteGetPopularTemplatesQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            ValidateTemplateQueryHandler,
            ConcreteValidateTemplateQueryHandler,
            lifetime=ServiceLifetime.SCOPED
        )
        container.register(
            CheckTemplateExistsQueryHandler,
            ConcreteCheckTemplateExistsQueryHandler,
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
            
            # Pipeline Query Handlers
            "get_pipeline_template_handler": GetPipelineTemplateQueryHandler,
            "list_pipeline_templates_handler": ListPipelineTemplatesQueryHandler,
            "search_pipeline_templates_handler": SearchPipelineTemplatesQueryHandler,
            "get_pipeline_run_handler": GetPipelineRunQueryHandler,
            "list_pipeline_runs_handler": ListPipelineRunsQueryHandler,
            "get_pipeline_analytics_handler": GetPipelineAnalyticsQueryHandler,
            
            # Workspace Query Handlers
            "get_workspaces_handler": GetWorkspacesQueryHandler,
            "get_workspace_handler": GetWorkspaceQueryHandler,
            "get_active_workspace_handler": GetActiveWorkspaceQueryHandler,
            "get_workspace_config_handler": GetWorkspaceConfigQueryHandler,
            "get_workspace_stats_handler": GetWorkspaceStatsQueryHandler,
            "search_workspaces_handler": SearchWorkspacesQueryHandler,
            "validate_workspace_name_handler": ValidateWorkspaceNameQueryHandler,
            "check_workspace_exists_handler": CheckWorkspaceExistsQueryHandler,
            "get_workspace_health_handler": GetWorkspaceHealthQueryHandler,
            "get_workspace_templates_handler": GetWorkspaceTemplatesQueryHandler,
            "get_workspace_template_handler": GetWorkspaceTemplateQueryHandler,
            
            # Content Query Handlers
            "get_templates_handler": GetTemplatesQueryHandler,
            "get_template_handler": GetTemplateQueryHandler,
            "get_template_by_name_handler": GetTemplateByNameQueryHandler,
            "search_templates_handler": SearchTemplatesQueryHandler,
            "get_generated_content_handler": GetGeneratedContentQueryHandler,
            "list_generated_content_handler": ListGeneratedContentQueryHandler,
            "search_generated_content_handler": SearchGeneratedContentQueryHandler,
            "get_style_primers_handler": GetStylePrimersQueryHandler,
            "get_style_primer_handler": GetStylePrimerQueryHandler,
            "get_content_analytics_handler": GetContentAnalyticsQueryHandler,
            "get_popular_templates_handler": GetPopularTemplatesQueryHandler,
            "validate_template_handler": ValidateTemplateQueryHandler,
            "check_template_exists_handler": CheckTemplateExistsQueryHandler,
        }