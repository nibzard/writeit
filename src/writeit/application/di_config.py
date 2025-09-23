"""Dependency injection configuration for WriteIt application.

This module provides centralized registration of all application services,
repositories, and command handlers.
"""

import logging
from typing import Dict, Type, Any
from pathlib import Path

from ..shared.dependencies.container import Container, ServiceLifetime
from ..shared.events.event_bus import EventBus, AsyncEventBus

# Domain Services
from ..domains.pipeline.services import (
    PipelineValidationService,
    PipelineExecutionService,
    StepDependencyService
)
from ..domains.workspace.services import (
    WorkspaceManagementService,
    WorkspaceConfigurationService,
    WorkspaceAnalyticsService,
    WorkspaceIsolationService,
    WorkspaceTemplateService
)
from ..domains.content.services import (
    TemplateManagementService,
    StyleManagementService,
    ContentGenerationService,
    TemplateRenderingService,
    ContentValidationService
)
from ..domains.execution.services import (
    LLMOrchestrationService,
    CacheManagementService,
    TokenAnalyticsService
)

# Application Services
from .services import (
    PipelineApplicationService,
    WorkspaceApplicationService,
    ContentApplicationService,
    ExecutionApplicationService
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
from ..application.queries.handlers.execution_handlers import (
    ConcreteGetLLMProvidersQueryHandler,
    ConcreteGetLLMProviderQueryHandler,
    ConcreteGetLLMProviderHealthQueryHandler,
    ConcreteSearchLLMProvidersQueryHandler,
    ConcreteGetTokenUsageQueryHandler,
    ConcreteListTokenUsageQueryHandler,
    ConcreteGetTokenAnalyticsQueryHandler,
    ConcreteGetTopTokenConsumersQueryHandler,
    ConcreteGetCacheStatsQueryHandler,
    ConcreteGetCacheEntryQueryHandler,
    ConcreteSearchCacheEntriesQueryHandler,
    ConcreteGetExecutionContextQueryHandler,
    ConcreteListExecutionContextsQueryHandler,
    ConcreteGetActiveExecutionContextsQueryHandler,
    ConcreteGetLLMRequestHistoryQueryHandler,
    ConcreteGetLLMRequestPerformanceQueryHandler,
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
from ..application.queries.execution_queries import (
    GetLLMProvidersQueryHandler,
    GetLLMProviderQueryHandler,
    GetLLMProviderHealthQueryHandler,
    SearchLLMProvidersQueryHandler,
    GetTokenUsageQueryHandler,
    ListTokenUsageQueryHandler,
    GetTokenAnalyticsQueryHandler,
    GetTopTokenConsumersQueryHandler,
    GetCacheStatsQueryHandler,
    GetCacheEntryQueryHandler,
    SearchCacheEntriesQueryHandler,
    GetExecutionContextQueryHandler,
    ListExecutionContextsQueryHandler,
    GetActiveExecutionContextsQueryHandler,
    GetLLMRequestHistoryQueryHandler,
    GetLLMRequestPerformanceQueryHandler,
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
        
        # Configure application services
        container = DIConfiguration._configure_application_services(container)
        
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
        container.register_singleton(EventBus, AsyncEventBus)
        
        return container
    
    @staticmethod
    def _configure_domain_services(container: Container) -> Container:
        """Configure domain services."""
        
        # Pipeline Domain Services
        container.register_scoped(
            PipelineValidationService,
            PipelineValidationService
        )
        container.register_scoped(
            PipelineExecutionService,
            PipelineExecutionService
        )
        container.register_scoped(
            StepDependencyService,
            StepDependencyService
        )
        
        # Workspace Domain Services
        container.register_scoped(
            WorkspaceManagementService,
            WorkspaceManagementService
        )
        container.register_scoped(
            WorkspaceConfigurationService,
            WorkspaceConfigurationService
        )
        container.register_scoped(
            WorkspaceAnalyticsService,
            WorkspaceAnalyticsService
        )
        container.register_scoped(
            WorkspaceIsolationService,
            WorkspaceIsolationService
        )
        container.register_scoped(
            WorkspaceTemplateService,
            WorkspaceTemplateService
        )
        
        # Content Domain Services
        container.register_scoped(
            TemplateManagementService,
            TemplateManagementService
        )
        container.register_scoped(
            StyleManagementService,
            StyleManagementService
        )
        container.register_scoped(
            ContentGenerationService,
            ContentGenerationService
        )
        container.register_scoped(
            TemplateRenderingService,
            TemplateRenderingService
        )
        container.register_scoped(
            ContentValidationService,
            ContentValidationService
        )
        
        # Execution Domain Services
        container.register_scoped(
            LLMOrchestrationService,
            LLMOrchestrationService
        )
        container.register_scoped(
            CacheManagementService,
            CacheManagementService
        )
        container.register_scoped(
            TokenAnalyticsService,
            TokenAnalyticsService
        )
        
        return container
    
    @staticmethod
    def _configure_application_services(container: Container) -> Container:
        """Configure application services."""
        
        # Pipeline Application Service
        container.register_scoped(
            PipelineApplicationService,
            PipelineApplicationService
        )
        
        # Workspace Application Service
        container.register_scoped(
            WorkspaceApplicationService,
            WorkspaceApplicationService
        )
        
        # Content Application Service
        container.register_scoped(
            ContentApplicationService,
            ContentApplicationService
        )
        
        # Execution Application Service
        container.register_scoped(
            ExecutionApplicationService,
            ExecutionApplicationService
        )
        
        return container
    
    @staticmethod
    def _configure_repositories(container: Container) -> Container:
        """Configure repository implementations."""
        
        # Pipeline Repositories
        container.register_scoped(
            PipelineTemplateRepository,
            LMDBPipelineTemplateRepository
        )
        container.register_scoped(
            PipelineRunRepository,
            LMDBPipelineRunRepository
        )
        container.register_scoped(
            StepExecutionRepository,
            LMDBStepExecutionRepository
        )
        
        # Workspace Repositories
        container.register_scoped(
            WorkspaceRepository,
            LMDBWorkspaceRepository
        )
        container.register_scoped(
            WorkspaceConfigRepository,
            LMDBWorkspaceConfigRepository
        )
        
        # Content Repositories
        container.register_scoped(
            ContentTemplateRepository,
            LMDBContentTemplateRepository
        )
        container.register_scoped(
            StylePrimerRepository,
            LMDBStylePrimerRepository
        )
        container.register_scoped(
            GeneratedContentRepository,
            LMDBGeneratedContentRepository
        )
        
        # Execution Repositories
        container.register_scoped(
            LLMCacheRepository,
            LMDBLLMCacheRepository
        )
        container.register_scoped(
            TokenUsageRepository,
            LMDBTokenUsageRepository
        )
        
        return container
    
    @staticmethod
    def _configure_command_handlers(container: Container) -> Container:
        """Configure command handlers with their interfaces."""
        
        # Pipeline Template Command Handlers
        container.register_transient(
            CreatePipelineTemplateCommandHandler,
            ConcreteCreatePipelineTemplateCommandHandler
        )
        container.register_transient(
            UpdatePipelineTemplateCommandHandler,
            ConcreteUpdatePipelineTemplateCommandHandler
        )
        container.register_transient(
            DeletePipelineTemplateCommandHandler,
            ConcreteDeletePipelineTemplateCommandHandler
        )
        container.register_transient(
            PublishPipelineTemplateCommandHandler,
            ConcretePublishPipelineTemplateCommandHandler
        )
        container.register_transient(
            ValidatePipelineTemplateCommandHandler,
            ConcreteValidatePipelineTemplateCommandHandler
        )
        
        # Pipeline Execution Command Handlers
        container.register_transient(
            ExecutePipelineCommandHandler,
            ConcreteExecutePipelineCommandHandler
        )
        container.register_transient(
            CancelPipelineExecutionCommandHandler,
            ConcreteCancelPipelineExecutionCommandHandler
        )
        container.register_transient(
            RetryPipelineExecutionCommandHandler,
            ConcreteRetryPipelineExecutionCommandHandler
        )
        container.register_transient(
            StreamingPipelineExecutionCommandHandler,
            ConcreteStreamingPipelineExecutionCommandHandler
        )
        
        # Workspace Command Handlers
        container.register_transient(
            CreateWorkspaceCommandHandler,
            ConcreteCreateWorkspaceCommandHandler
        )
        container.register_transient(
            SwitchWorkspaceCommandHandler,
            ConcreteSwitchWorkspaceCommandHandler
        )
        container.register_transient(
            DeleteWorkspaceCommandHandler,
            ConcreteDeleteWorkspaceCommandHandler
        )
        container.register_transient(
            ConfigureWorkspaceCommandHandler,
            ConcreteConfigureWorkspaceCommandHandler
        )
        container.register_transient(
            InitializeWorkspaceCommandHandler,
            ConcreteInitializeWorkspaceCommandHandler
        )
        container.register_transient(
            ArchiveWorkspaceCommandHandler,
            ConcreteArchiveWorkspaceCommandHandler
        )
        container.register_transient(
            RestoreWorkspaceCommandHandler,
            ConcreteRestoreWorkspaceCommandHandler
        )
        container.register_transient(
            CreateWorkspaceTemplateCommandHandler,
            ConcreteCreateWorkspaceTemplateCommandHandler
        )
        container.register_transient(
            ApplyWorkspaceTemplateCommandHandler,
            ConcreteApplyWorkspaceTemplateCommandHandler
        )
        
        # Content Command Handlers
        container.register_transient(
            CreateTemplateCommandHandler,
            ConcreteCreateTemplateCommandHandler
        )
        container.register_transient(
            UpdateTemplateCommandHandler,
            ConcreteUpdateTemplateCommandHandler
        )
        container.register_transient(
            DeleteTemplateCommandHandler,
            ConcreteDeleteTemplateCommandHandler
        )
        container.register_transient(
            ValidateTemplateCommandHandler,
            ConcreteValidateTemplateCommandHandler
        )
        container.register_transient(
            CreateStylePrimerCommandHandler,
            ConcreteCreateStylePrimerCommandHandler
        )
        container.register_transient(
            CreateGeneratedContentCommandHandler,
            ConcreteCreateGeneratedContentCommandHandler
        )
        
        return container
    
    @staticmethod
    def _configure_query_handlers(container: Container) -> Container:
        """Configure query handlers with their interfaces."""
        
        # Pipeline Query Handlers
        container.register_transient(
            GetPipelineTemplateQueryHandler,
            ConcreteGetPipelineTemplateQueryHandler
        )
        container.register_transient(
            ListPipelineTemplatesQueryHandler,
            ConcreteListPipelineTemplatesQueryHandler
        )
        container.register_transient(
            SearchPipelineTemplatesQueryHandler,
            ConcreteSearchPipelineTemplatesQueryHandler
        )
        container.register_transient(
            GetPipelineRunQueryHandler,
            ConcreteGetPipelineRunQueryHandler
        )
        container.register_transient(
            ListPipelineRunsQueryHandler,
            ConcreteListPipelineRunsQueryHandler
        )
        container.register_transient(
            GetPipelineAnalyticsQueryHandler,
            ConcreteGetPipelineAnalyticsQueryHandler
        )
        
        # Workspace Query Handlers
        container.register_transient(
            GetWorkspacesQueryHandler,
            ConcreteGetWorkspacesQueryHandler
        )
        container.register_transient(
            GetWorkspaceQueryHandler,
            ConcreteGetWorkspaceQueryHandler
        )
        container.register_transient(
            GetActiveWorkspaceQueryHandler,
            ConcreteGetActiveWorkspaceQueryHandler
        )
        container.register_transient(
            GetWorkspaceConfigQueryHandler,
            ConcreteGetWorkspaceConfigQueryHandler
        )
        container.register_transient(
            GetWorkspaceStatsQueryHandler,
            ConcreteGetWorkspaceStatsQueryHandler
        )
        container.register_transient(
            SearchWorkspacesQueryHandler,
            ConcreteSearchWorkspacesQueryHandler
        )
        container.register_transient(
            ValidateWorkspaceNameQueryHandler,
            ConcreteValidateWorkspaceNameQueryHandler
        )
        container.register_transient(
            CheckWorkspaceExistsQueryHandler,
            ConcreteCheckWorkspaceExistsQueryHandler
        )
        container.register_transient(
            GetWorkspaceHealthQueryHandler,
            ConcreteGetWorkspaceHealthQueryHandler
        )
        container.register_transient(
            GetWorkspaceTemplatesQueryHandler,
            ConcreteGetWorkspaceTemplatesQueryHandler
        )
        container.register_transient(
            GetWorkspaceTemplateQueryHandler,
            ConcreteGetWorkspaceTemplateQueryHandler
        )
        
        # Content Query Handlers
        container.register_transient(
            GetTemplatesQueryHandler,
            ConcreteGetTemplatesQueryHandler
        )
        container.register_transient(
            GetTemplateQueryHandler,
            ConcreteGetTemplateQueryHandler
        )
        container.register_transient(
            GetTemplateByNameQueryHandler,
            ConcreteGetTemplateByNameQueryHandler
        )
        container.register_transient(
            SearchTemplatesQueryHandler,
            ConcreteSearchTemplatesQueryHandler
        )
        container.register_transient(
            GetGeneratedContentQueryHandler,
            ConcreteGetGeneratedContentQueryHandler
        )
        container.register_transient(
            ListGeneratedContentQueryHandler,
            ConcreteListGeneratedContentQueryHandler
        )
        container.register_transient(
            SearchGeneratedContentQueryHandler,
            ConcreteSearchGeneratedContentQueryHandler
        )
        container.register_transient(
            GetStylePrimersQueryHandler,
            ConcreteGetStylePrimersQueryHandler
        )
        container.register_transient(
            GetStylePrimerQueryHandler,
            ConcreteGetStylePrimerQueryHandler
        )
        container.register_transient(
            GetContentAnalyticsQueryHandler,
            ConcreteGetContentAnalyticsQueryHandler
        )
        container.register_transient(
            GetPopularTemplatesQueryHandler,
            ConcreteGetPopularTemplatesQueryHandler
        )
        container.register_transient(
            ValidateTemplateQueryHandler,
            ConcreteValidateTemplateQueryHandler
        )
        container.register_transient(
            CheckTemplateExistsQueryHandler,
            ConcreteCheckTemplateExistsQueryHandler
        )
        
        # Execution Query Handlers
        container.register_transient(
            GetLLMProvidersQueryHandler,
            ConcreteGetLLMProvidersQueryHandler
        )
        container.register_transient(
            GetLLMProviderQueryHandler,
            ConcreteGetLLMProviderQueryHandler
        )
        container.register_transient(
            GetLLMProviderHealthQueryHandler,
            ConcreteGetLLMProviderHealthQueryHandler
        )
        container.register_transient(
            SearchLLMProvidersQueryHandler,
            ConcreteSearchLLMProvidersQueryHandler
        )
        container.register_transient(
            GetTokenUsageQueryHandler,
            ConcreteGetTokenUsageQueryHandler
        )
        container.register_transient(
            ListTokenUsageQueryHandler,
            ConcreteListTokenUsageQueryHandler
        )
        container.register_transient(
            GetTokenAnalyticsQueryHandler,
            ConcreteGetTokenAnalyticsQueryHandler
        )
        container.register_transient(
            GetTopTokenConsumersQueryHandler,
            ConcreteGetTopTokenConsumersQueryHandler
        )
        container.register_transient(
            GetCacheStatsQueryHandler,
            ConcreteGetCacheStatsQueryHandler
        )
        container.register_transient(
            GetCacheEntryQueryHandler,
            ConcreteGetCacheEntryQueryHandler
        )
        container.register_transient(
            SearchCacheEntriesQueryHandler,
            ConcreteSearchCacheEntriesQueryHandler
        )
        container.register_transient(
            GetExecutionContextQueryHandler,
            ConcreteGetExecutionContextQueryHandler
        )
        container.register_transient(
            ListExecutionContextsQueryHandler,
            ConcreteListExecutionContextsQueryHandler
        )
        container.register_transient(
            GetActiveExecutionContextsQueryHandler,
            ConcreteGetActiveExecutionContextsQueryHandler
        )
        container.register_transient(
            GetLLMRequestHistoryQueryHandler,
            ConcreteGetLLMRequestHistoryQueryHandler
        )
        container.register_transient(
            GetLLMRequestPerformanceQueryHandler,
            ConcreteGetLLMRequestPerformanceQueryHandler
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
            "workspace_management_service": WorkspaceManagementService,
            "workspace_configuration_service": WorkspaceConfigurationService,
            "workspace_analytics_service": WorkspaceAnalyticsService,
            "workspace_isolation_service": WorkspaceIsolationService,
            "workspace_template_service": WorkspaceTemplateService,
            "template_management_service": TemplateManagementService,
            "style_management_service": StyleManagementService,
            "content_generation_service": ContentGenerationService,
            "template_rendering_service": TemplateRenderingService,
            "content_validation_service": ContentValidationService,
            "llm_orchestration_service": LLMOrchestrationService,
            "cache_management_service": CacheManagementService,
            "token_analytics_service": TokenAnalyticsService,
            
            # Application Services
            "pipeline_application_service": PipelineApplicationService,
            "workspace_application_service": WorkspaceApplicationService,
            "content_application_service": ContentApplicationService,
            "execution_application_service": ExecutionApplicationService,
            
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
            
            # Execution Query Handlers
            "get_llm_providers_handler": GetLLMProvidersQueryHandler,
            "get_llm_provider_handler": GetLLMProviderQueryHandler,
            "get_llm_provider_health_handler": GetLLMProviderHealthQueryHandler,
            "search_llm_providers_handler": SearchLLMProvidersQueryHandler,
            "get_token_usage_handler": GetTokenUsageQueryHandler,
            "list_token_usage_handler": ListTokenUsageQueryHandler,
            "get_token_analytics_handler": GetTokenAnalyticsQueryHandler,
            "get_top_token_consumers_handler": GetTopTokenConsumersQueryHandler,
            "get_cache_stats_handler": GetCacheStatsQueryHandler,
            "get_cache_entry_handler": GetCacheEntryQueryHandler,
            "search_cache_entries_handler": SearchCacheEntriesQueryHandler,
            "get_execution_context_handler": GetExecutionContextQueryHandler,
            "list_execution_contexts_handler": ListExecutionContextsQueryHandler,
            "get_active_execution_contexts_handler": GetActiveExecutionContextsQueryHandler,
            "get_llm_request_history_handler": GetLLMRequestHistoryQueryHandler,
            "get_llm_request_performance_handler": GetLLMRequestPerformanceQueryHandler,
        }