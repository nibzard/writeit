"""Pipeline Application Service.

Orchestrates pipeline operations across domains, providing user-facing
use cases for pipeline creation, execution, and lifecycle management.
Coordinates workspace, content, and execution domains.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from enum import Enum
import asyncio
from datetime import datetime
from pathlib import Path

from ...domains.pipeline.services import (
    PipelineValidationService,
    PipelineExecutionService,
    StepDependencyService,
)
from ...domains.workspace.services import (
    WorkspaceManagementService,
    WorkspaceConfigurationService,
    WorkspaceAnalyticsService,
)
from ...domains.content.services import (
    TemplateManagementService,
    StyleManagementService,
    ContentGenerationService,
)
from ...domains.execution.services import (
    LLMOrchestrationService,
    CacheManagementService,
    TokenAnalyticsService,
)

from ...domains.pipeline.entities import PipelineTemplate, PipelineRun, PipelineStep
from ...domains.pipeline.value_objects import (
    PipelineId,
    StepId,
    ExecutionStatus,
)
from ...domains.workspace.entities import Workspace
from ...domains.workspace.value_objects import WorkspaceName

# Query infrastructure
from ...shared.query import QueryBus, SimpleQueryBus
from ...domains.pipeline.queries import (
    GetPipelineTemplatesQuery,
    GetPipelineTemplatesResult,
    GetPipelineTemplateQuery,
    GetPipelineTemplateResult,
    GetPipelineRunQuery,
    GetPipelineRunResult,
    GetPipelineRunsQuery,
    GetPipelineRunsResult,
    SearchPipelineTemplatesQuery,
    SearchPipelineTemplatesResult,
    GetPipelineHistoryQuery,
    GetPipelineHistoryResult,
    GetPipelineMetricsQuery,
    GetPipelineMetricsResult,
    GetStepExecutionsQuery,
    GetStepExecutionsResult,
    GetPipelineTemplatesHandler,
    GetPipelineTemplateHandler,
    GetPipelineRunHandler,
    GetPipelineRunsHandler,
    SearchPipelineTemplatesHandler,
    GetPipelineHistoryHandler,
    GetPipelineMetricsHandler,
    GetStepExecutionsHandler,
)

# Repository interfaces
from ...domains.pipeline.repositories import (
    PipelineTemplateRepository,
    PipelineRunRepository,
    StepExecutionRepository,
)


class PipelineExecutionMode(str, Enum):
    """Pipeline execution modes for application layer."""
    CLI = "cli"          # Command-line execution
    TUI = "tui"          # Terminal UI execution  
    API = "api"          # REST API execution
    BACKGROUND = "background"  # Background execution


class PipelineSource(str, Enum):
    """Source of pipeline templates."""
    LOCAL = "local"      # Local file system
    WORKSPACE = "workspace"  # Workspace templates
    GLOBAL = "global"    # Global templates
    REMOTE = "remote"    # Remote template repository


@dataclass
class PipelineExecutionRequest:
    """Request for pipeline execution."""
    pipeline_name: str
    workspace_name: Optional[str] = None
    source: PipelineSource = PipelineSource.WORKSPACE
    mode: PipelineExecutionMode = PipelineExecutionMode.CLI
    inputs: Optional[Dict[str, Any]] = None
    execution_options: Optional[Dict[str, Any]] = None
    template_path: Optional[Path] = None


@dataclass
class PipelineExecutionResult:
    """Result of pipeline execution."""
    pipeline_run: PipelineRun
    execution_status: ExecutionStatus
    step_results: Dict[str, Any]
    execution_metrics: Dict[str, Any]
    errors: List[str]
    warnings: List[str]


@dataclass
class PipelineCreationRequest:
    """Request for pipeline creation."""
    name: str
    description: str
    workspace_name: Optional[str] = None
    template_content: Optional[str] = None
    template_path: Optional[Path] = None
    validation_level: str = "strict"


@dataclass
class PipelineListingOptions:
    """Options for listing pipelines."""
    workspace_name: Optional[str] = None
    source: Optional[PipelineSource] = None
    include_global: bool = True
    include_local: bool = True
    filter_pattern: Optional[str] = None


class PipelineApplicationError(Exception):
    """Base exception for pipeline application service errors."""
    pass


class PipelineValidationError(PipelineApplicationError):
    """Pipeline validation failed."""
    pass


class PipelineExecutionError(PipelineApplicationError):
    """Pipeline execution failed."""
    pass


class PipelineNotFoundError(PipelineApplicationError):
    """Pipeline template not found."""
    pass


class WorkspaceNotAvailableError(PipelineApplicationError):
    """Workspace is not available for pipeline operations."""
    pass


class PipelineApplicationService:
    """
    Application service for pipeline operations.
    
    Orchestrates pipeline creation, validation, execution, and management
    across workspace, content, and execution domains. Provides high-level
    use cases for CLI, TUI, and API interfaces.
    """
    
    def __init__(
        self,
        # Domain services
        pipeline_validation_service: PipelineValidationService,
        pipeline_execution_service: PipelineExecutionService,
        step_dependency_service: StepDependencyService,
        workspace_management_service: WorkspaceManagementService,
        workspace_configuration_service: WorkspaceConfigurationService,
        workspace_analytics_service: WorkspaceAnalyticsService,
        template_management_service: TemplateManagementService,
        style_management_service: StyleManagementService,
        content_generation_service: ContentGenerationService,
        llm_orchestration_service: LLMOrchestrationService,
        cache_management_service: CacheManagementService,
        token_analytics_service: TokenAnalyticsService,
        # Query infrastructure
        query_bus: Optional[QueryBus] = None,
        # Repositories (optional - will be provided by DI container)
        template_repository: Optional[PipelineTemplateRepository] = None,
        run_repository: Optional[PipelineRunRepository] = None,
        step_repository: Optional[StepExecutionRepository] = None,
    ):
        """Initialize the pipeline application service."""
        # Pipeline domain services
        self._pipeline_validation = pipeline_validation_service
        self._pipeline_execution = pipeline_execution_service
        self._step_dependency = step_dependency_service
        
        # Workspace domain services
        self._workspace_management = workspace_management_service
        self._workspace_configuration = workspace_configuration_service
        self._workspace_analytics = workspace_analytics_service
        
        # Content domain services
        self._template_management = template_management_service
        self._style_management = style_management_service
        self._content_generation = content_generation_service
        
        # Execution domain services
        self._llm_orchestration = llm_orchestration_service
        self._cache_management = cache_management_service
        self._token_analytics = token_analytics_service
        
        # Query infrastructure
        self._query_bus = query_bus or SimpleQueryBus()
        
        # Repositories (will be injected by DI container)
        self._template_repository = template_repository
        self._run_repository = run_repository
        self._step_repository = step_repository
        
        # Register query handlers if repositories are available
        if self._template_repository and self._run_repository and self._step_repository:
            self._register_query_handlers()

    async def create_pipeline(
        self, 
        request: PipelineCreationRequest
    ) -> PipelineTemplate:
        """
        Create a new pipeline template.
        
        Coordinates workspace validation, template creation, and storage
        across multiple domains.
        
        Args:
            request: Pipeline creation request
            
        Returns:
            Created pipeline template
            
        Raises:
            PipelineValidationError: If template validation fails
            WorkspaceNotAvailableError: If workspace is not available
        """
        try:
            # Resolve workspace
            workspace = await self._resolve_workspace(request.workspace_name)
            
            # Load template content
            template_content = await self._load_template_content(
                request.template_content,
                request.template_path
            )
            
            # Validate template content
            validation_result = await self._pipeline_validation.validate_template_content(
                template_content,
                workspace_context=workspace
            )
            
            if not validation_result.is_valid:
                raise PipelineValidationError(
                    f"Template validation failed: {validation_result.errors}"
                )
            
            # Create pipeline template
            template = await self._template_management.create_template(
                name=request.name,
                description=request.description,
                content=template_content,
                workspace=workspace,
                validation_level=request.validation_level
            )
            
            # Register template in workspace
            await self._workspace_management.register_pipeline_template(
                workspace.name,
                template
            )
            
            return template
            
        except Exception as e:
            raise PipelineApplicationError(f"Failed to create pipeline: {e}") from e

    async def execute_pipeline(
        self, 
        request: PipelineExecutionRequest
    ) -> AsyncGenerator[PipelineExecutionResult, None]:
        """
        Execute a pipeline with streaming results.
        
        Orchestrates pipeline loading, validation, execution coordination,
        and real-time progress reporting.
        
        Args:
            request: Pipeline execution request
            
        Yields:
            Pipeline execution results as they become available
            
        Raises:
            PipelineNotFoundError: If pipeline template is not found
            PipelineExecutionError: If execution fails
        """
        try:
            # Resolve workspace and pipeline
            workspace = await self._resolve_workspace(request.workspace_name)
            template = await self._load_pipeline_template(request, workspace)
            
            # Validate execution context
            await self._validate_execution_context(template, request, workspace)
            
            # Create pipeline run
            pipeline_run = await self._pipeline_execution.create_run(
                template=template,
                inputs=request.inputs or {},
                workspace=workspace,
                execution_mode=request.mode.value
            )
            
            # Configure execution services
            await self._configure_execution_services(request, workspace)
            
            # Execute pipeline with streaming
            async for execution_state in self._pipeline_execution.execute_stream(
                pipeline_run=pipeline_run,
                template=template
            ):
                # Convert domain state to application result
                result = PipelineExecutionResult(
                    pipeline_run=execution_state.pipeline_run,
                    execution_status=execution_state.status,
                    step_results=execution_state.step_results,
                    execution_metrics=await self._collect_execution_metrics(
                        execution_state, workspace
                    ),
                    errors=execution_state.errors,
                    warnings=execution_state.warnings
                )
                
                yield result
                
                # Update workspace analytics
                await self._workspace_analytics.record_pipeline_execution(
                    workspace.name,
                    execution_state
                )
                
        except Exception as e:
            raise PipelineExecutionError(f"Pipeline execution failed: {e}") from e

    async def list_pipelines(
        self, 
        options: PipelineListingOptions
    ) -> List[Dict[str, Any]]:
        """
        List available pipeline templates.
        
        Aggregates pipeline templates from workspace, global, and local sources
        with filtering and metadata enrichment.
        
        Args:
            options: Listing options
            
        Returns:
            List of pipeline information dictionaries
        """
        try:
            pipelines = []
            
            # Get workspace pipelines
            if options.include_local or options.workspace_name:
                workspace = await self._resolve_workspace(options.workspace_name)
                workspace_pipelines = await self._template_management.list_templates(
                    workspace=workspace,
                    filter_pattern=options.filter_pattern
                )
                pipelines.extend([
                    {
                        "name": p.name,
                        "description": p.description,
                        "source": PipelineSource.WORKSPACE,
                        "workspace": workspace.name.value,
                        "template": p,
                        "metadata": await self._enrich_pipeline_metadata(p, workspace)
                    }
                    for p in workspace_pipelines
                ])
            
            # Get global pipelines
            if options.include_global:
                global_pipelines = await self._template_management.list_global_templates(
                    filter_pattern=options.filter_pattern
                )
                pipelines.extend([
                    {
                        "name": p.name,
                        "description": p.description,
                        "source": PipelineSource.GLOBAL,
                        "workspace": None,
                        "template": p,
                        "metadata": await self._enrich_pipeline_metadata(p, None)
                    }
                    for p in global_pipelines
                ])
            
            return pipelines
            
        except Exception as e:
            raise PipelineApplicationError(f"Failed to list pipelines: {e}") from e

    async def validate_pipeline(
        self, 
        pipeline_name: str, 
        workspace_name: Optional[str] = None,
        detailed: bool = False
    ) -> Dict[str, Any]:
        """
        Validate a pipeline template.
        
        Performs comprehensive validation including syntax, dependencies,
        workspace compatibility, and execution feasibility.
        
        Args:
            pipeline_name: Name of pipeline to validate
            workspace_name: Optional workspace context
            detailed: Whether to include detailed validation information
            
        Returns:
            Validation result with errors, warnings, and recommendations
        """
        try:
            workspace = await self._resolve_workspace(workspace_name)
            
            # Load pipeline template
            template = await self._template_management.get_template(
                pipeline_name, workspace
            )
            
            if not template:
                raise PipelineNotFoundError(f"Pipeline '{pipeline_name}' not found")
            
            # Validate template
            validation_result = await self._pipeline_validation.validate_comprehensive(
                template=template,
                workspace_context=workspace,
                include_performance_analysis=detailed
            )
            
            # Validate dependencies
            dependency_result = await self._step_dependency.validate_dependencies(
                template.steps
            )
            
            # Validate execution requirements
            execution_validation = await self._validate_execution_requirements(
                template, workspace
            )
            
            return {
                "is_valid": validation_result.is_valid and dependency_result.is_valid,
                "template_validation": validation_result,
                "dependency_validation": dependency_result,
                "execution_validation": execution_validation,
                "recommendations": await self._generate_optimization_recommendations(
                    template, workspace
                ) if detailed else []
            }
            
        except Exception as e:
            raise PipelineApplicationError(f"Pipeline validation failed: {e}") from e

    async def get_pipeline_analytics(
        self, 
        pipeline_name: str, 
        workspace_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get analytics for a pipeline.
        
        Aggregates execution history, performance metrics, and usage patterns
        from workspace and token analytics.
        
        Args:
            pipeline_name: Name of pipeline
            workspace_name: Optional workspace context
            
        Returns:
            Pipeline analytics data
        """
        try:
            workspace = await self._resolve_workspace(workspace_name)
            
            # Get workspace analytics
            workspace_analytics = await self._workspace_analytics.get_pipeline_analytics(
                workspace.name,
                pipeline_name
            )
            
            # Get token analytics
            token_analytics = await self._token_analytics.get_pipeline_usage(
                workspace.name,
                pipeline_name
            )
            
            # Get cache analytics
            cache_analytics = await self._cache_management.get_pipeline_cache_stats(
                workspace.name,
                pipeline_name
            )
            
            return {
                "execution_history": workspace_analytics.execution_history,
                "performance_metrics": workspace_analytics.performance_metrics,
                "token_usage": token_analytics,
                "cache_performance": cache_analytics,
                "recommendations": await self._generate_performance_recommendations(
                    workspace_analytics, token_analytics, cache_analytics
                )
            }
            
        except Exception as e:
            raise PipelineApplicationError(f"Failed to get pipeline analytics: {e}") from e

    # Private helper methods
    
    async def _resolve_workspace(self, workspace_name: Optional[str]) -> Workspace:
        """Resolve workspace, using active workspace if none specified."""
        if workspace_name:
            workspace = await self._workspace_management.get_workspace(
                WorkspaceName(workspace_name)
            )
        else:
            workspace = await self._workspace_management.get_active_workspace()
        
        if not workspace:
            raise WorkspaceNotAvailableError("No workspace available")
        
        return workspace

    async def _load_template_content(
        self, 
        content: Optional[str], 
        path: Optional[Path]
    ) -> str:
        """Load template content from string or file."""
        if content:
            return content
        elif path:
            return path.read_text(encoding='utf-8')
        else:
            raise PipelineValidationError("No template content or path provided")

    async def _load_pipeline_template(
        self, 
        request: PipelineExecutionRequest, 
        workspace: Workspace
    ) -> PipelineTemplate:
        """Load pipeline template based on request source."""
        if request.source == PipelineSource.LOCAL and request.template_path:
            content = await self._load_template_content(None, request.template_path)
            return await self._template_management.parse_template(content)
        elif request.source == PipelineSource.GLOBAL:
            return await self._template_management.get_global_template(
                request.pipeline_name
            )
        else:
            template = await self._template_management.get_template(
                request.pipeline_name, workspace
            )
            if not template:
                raise PipelineNotFoundError(
                    f"Pipeline '{request.pipeline_name}' not found"
                )
            return template

    async def _validate_execution_context(
        self, 
        template: PipelineTemplate, 
        request: PipelineExecutionRequest,
        workspace: Workspace
    ) -> None:
        """Validate that execution context is valid."""
        # Validate inputs
        if template.inputs:
            required_inputs = {
                name for name, input_def in template.inputs.items() 
                if input_def.required
            }
            provided_inputs = set(request.inputs.keys()) if request.inputs else set()
            missing_inputs = required_inputs - provided_inputs
            
            if missing_inputs:
                raise PipelineExecutionError(
                    f"Missing required inputs: {missing_inputs}"
                )
        
        # Validate LLM availability
        for step in template.steps.values():
            if hasattr(step, 'model_preference') and step.model_preference:
                available = await self._llm_orchestration.check_model_availability(
                    step.model_preference[0]  # Check first preference
                )
                if not available:
                    raise PipelineExecutionError(
                        f"Required model not available: {step.model_preference[0]}"
                    )

    async def _configure_execution_services(
        self, 
        request: PipelineExecutionRequest, 
        workspace: Workspace
    ) -> None:
        """Configure execution services for the pipeline run."""
        # Configure cache strategy
        await self._cache_management.configure_workspace_cache(
            workspace.name,
            strategy="adaptive"  # Could be configurable
        )
        
        # Configure token tracking
        await self._token_analytics.start_pipeline_tracking(
            workspace.name,
            request.pipeline_name
        )

    async def _collect_execution_metrics(
        self, 
        execution_state: Any, 
        workspace: Workspace
    ) -> Dict[str, Any]:
        """Collect comprehensive execution metrics."""
        return {
            "execution_time": execution_state.execution_time,
            "steps_completed": len(execution_state.completed_steps),
            "steps_failed": len(execution_state.failed_steps),
            "token_usage": await self._token_analytics.get_current_usage(workspace.name),
            "cache_hits": await self._cache_management.get_cache_hits(workspace.name),
            "memory_usage": execution_state.memory_usage if hasattr(execution_state, 'memory_usage') else None
        }

    async def _enrich_pipeline_metadata(
        self, 
        template: PipelineTemplate, 
        workspace: Optional[Workspace]
    ) -> Dict[str, Any]:
        """Enrich pipeline with additional metadata."""
        metadata = {
            "steps_count": len(template.steps),
            "has_dependencies": bool(template.dependencies) if hasattr(template, 'dependencies') else False,
        }
        
        if workspace:
            analytics = await self._workspace_analytics.get_pipeline_summary(
                workspace.name,
                template.name
            )
            metadata.update({
                "last_executed": analytics.last_execution_time,
                "execution_count": analytics.execution_count,
                "average_duration": analytics.average_duration,
                "success_rate": analytics.success_rate
            })
        
        return metadata

    async def _validate_execution_requirements(
        self, 
        template: PipelineTemplate, 
        workspace: Workspace
    ) -> Dict[str, Any]:
        """Validate execution requirements."""
        return {
            "models_available": await self._check_model_availability(template),
            "dependencies_satisfied": await self._step_dependency.validate_dependencies(
                template.steps
            ).is_valid,
            "workspace_compatible": True,  # Could add more checks
            "estimated_cost": await self._estimate_execution_cost(template, workspace)
        }

    async def _check_model_availability(self, template: PipelineTemplate) -> bool:
        """Check if all required models are available."""
        for step in template.steps.values():
            if hasattr(step, 'model_preference') and step.model_preference:
                available = await self._llm_orchestration.check_model_availability(
                    step.model_preference[0]
                )
                if not available:
                    return False
        return True

    async def _estimate_execution_cost(
        self, 
        template: PipelineTemplate, 
        workspace: Workspace
    ) -> Optional[float]:
        """Estimate the cost of executing the pipeline."""
        try:
            return await self._token_analytics.estimate_pipeline_cost(
                workspace.name,
                template
            )
        except Exception:
            return None

    async def _generate_optimization_recommendations(
        self, 
        template: PipelineTemplate, 
        workspace: Workspace
    ) -> List[str]:
        """Generate optimization recommendations for the pipeline."""
        recommendations = []
        
        # Check for caching opportunities
        cache_recommendations = await self._cache_management.analyze_caching_potential(
            template
        )
        recommendations.extend(cache_recommendations)
        
        # Check for model optimization
        model_recommendations = await self._llm_orchestration.analyze_model_usage(
            template
        )
        recommendations.extend(model_recommendations)
        
        return recommendations

    async def _generate_performance_recommendations(
        self, 
        workspace_analytics: Any, 
        token_analytics: Any, 
        cache_analytics: Any
    ) -> List[str]:
        """Generate performance recommendations based on analytics."""
        recommendations = []
        
        # Token usage recommendations
        if token_analytics.average_cost_per_execution > 0.10:  # Example threshold
            recommendations.append(
                "Consider using a smaller model or optimizing prompts to reduce costs"
            )
        
        # Cache recommendations
        if cache_analytics.hit_rate < 0.3:  # Low cache hit rate
            recommendations.append(
                "Consider enabling more aggressive caching to improve performance"
            )
        
        # Performance recommendations
        if workspace_analytics.average_duration > 60:  # Slow execution
            recommendations.append(
                "Consider parallelizing independent steps to improve execution time"
            )
        
        return recommendations

    # Query handler registration
    
    def _register_query_handlers(self) -> None:
        """Register all query handlers with the query bus."""
        if not (self._template_repository and self._run_repository and self._step_repository):
            return
        
        # Template query handlers
        self._query_bus.register_handler(
            GetPipelineTemplatesQuery,
            GetPipelineTemplatesHandler(
                self._template_repository,
                self._pipeline_validation
            )
        )
        
        self._query_bus.register_handler(
            GetPipelineTemplateQuery,
            GetPipelineTemplateHandler(
                self._template_repository,
                self._run_repository
            )
        )
        
        self._query_bus.register_handler(
            SearchPipelineTemplatesQuery,
            SearchPipelineTemplatesHandler(self._template_repository)
        )
        
        # Run query handlers
        self._query_bus.register_handler(
            GetPipelineRunQuery,
            GetPipelineRunHandler(
                self._run_repository,
                self._step_repository,
                self._template_repository
            )
        )
        
        self._query_bus.register_handler(
            GetPipelineRunsQuery,
            GetPipelineRunsHandler(self._run_repository)
        )
        
        # Analytics query handlers
        self._query_bus.register_handler(
            GetPipelineHistoryQuery,
            GetPipelineHistoryHandler(
                self._run_repository,
                self._step_repository
            )
        )
        
        self._query_bus.register_handler(
            GetPipelineMetricsQuery,
            GetPipelineMetricsHandler(
                self._run_repository,
                self._template_repository
            )
        )
        
        # Step execution query handlers
        self._query_bus.register_handler(
            GetStepExecutionsQuery,
            GetStepExecutionsHandler(self._step_repository)
        )

    # Query methods for application layer
    
    async def query_pipeline_templates(
        self,
        workspace_name: Optional[str] = None,
        include_global: bool = True,
        tags: Optional[List[str]] = None,
        category: Optional[str] = None,
        author: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "name",
        sort_direction: str = "asc"
    ) -> GetPipelineTemplatesResult:
        """
        Query pipeline templates with filtering and pagination.
        
        Args:
            workspace_name: Optional workspace filter
            include_global: Whether to include global templates
            tags: Optional tag filters
            category: Optional category filter
            author: Optional author filter
            page: Page number for pagination
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_direction: Sort direction (asc/desc)
            
        Returns:
            Query result with templates and pagination info
        """
        query = GetPipelineTemplatesQuery(
            workspace_name=workspace_name,
            include_global=include_global,
            tags=tags or [],
            category=category,
            author=author,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction
        )
        
        return await self._query_bus.send(query)
    
    async def query_pipeline_template(
        self,
        template_id: Union[str, PipelineId],
        workspace_name: Optional[str] = None,
        include_global: bool = True,
        include_usage_stats: bool = False
    ) -> GetPipelineTemplateResult:
        """
        Query a specific pipeline template.
        
        Args:
            template_id: Template identifier
            workspace_name: Optional workspace context
            include_global: Whether to search global templates
            include_usage_stats: Whether to include usage statistics
            
        Returns:
            Query result with template details
        """
        query = GetPipelineTemplateQuery(
            template_id=template_id,
            workspace_name=workspace_name,
            include_global=include_global,
            include_usage_stats=include_usage_stats
        )
        
        return await self._query_bus.send(query)
    
    async def search_pipeline_templates(
        self,
        search_term: str,
        workspace_name: Optional[str] = None,
        include_global: bool = True,
        search_fields: Optional[List[str]] = None,
        category_filter: Optional[str] = None,
        tag_filter: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 20
    ) -> SearchPipelineTemplatesResult:
        """
        Search pipeline templates by text content.
        
        Args:
            search_term: Text to search for
            workspace_name: Optional workspace filter
            include_global: Whether to include global templates
            search_fields: Fields to search in
            category_filter: Optional category filter
            tag_filter: Optional tag filters
            page: Page number for pagination
            page_size: Number of items per page
            
        Returns:
            Search results with relevance scores
        """
        query = SearchPipelineTemplatesQuery(
            search_term=search_term,
            workspace_name=workspace_name,
            include_global=include_global,
            search_fields=search_fields or ["name", "description", "tags"],
            category_filter=category_filter,
            tag_filter=tag_filter or [],
            page=page,
            page_size=page_size
        )
        
        return await self._query_bus.send(query)
    
    async def query_pipeline_run(
        self,
        run_id: str,
        workspace_name: Optional[str] = None,
        include_step_executions: bool = True,
        include_outputs: bool = True,
        include_metrics: bool = False
    ) -> GetPipelineRunResult:
        """
        Query a specific pipeline run.
        
        Args:
            run_id: Run identifier
            workspace_name: Optional workspace filter
            include_step_executions: Whether to include step execution details
            include_outputs: Whether to include run outputs
            include_metrics: Whether to include execution metrics
            
        Returns:
            Query result with run details
        """
        query = GetPipelineRunQuery(
            run_id=run_id,
            workspace_name=workspace_name,
            include_step_executions=include_step_executions,
            include_outputs=include_outputs,
            include_metrics=include_metrics
        )
        
        return await self._query_bus.send(query)
    
    async def query_pipeline_runs(
        self,
        workspace_name: Optional[str] = None,
        template_id: Optional[Union[str, PipelineId]] = None,
        status_filter: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_direction: str = "desc"
    ) -> GetPipelineRunsResult:
        """
        Query pipeline runs with filtering and pagination.
        
        Args:
            workspace_name: Optional workspace filter
            template_id: Optional template filter
            status_filter: Optional status filters
            start_date: Optional start date filter
            end_date: Optional end date filter
            page: Page number for pagination
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_direction: Sort direction (asc/desc)
            
        Returns:
            Query result with runs and statistics
        """
        query = GetPipelineRunsQuery(
            workspace_name=workspace_name,
            template_id=template_id,
            status_filter=status_filter or [],
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction
        )
        
        return await self._query_bus.send(query)
    
    async def query_pipeline_history(
        self,
        workspace_name: Optional[str] = None,
        template_id: Optional[Union[str, PipelineId]] = None,
        date_range_days: int = 30,
        include_step_breakdown: bool = False,
        include_token_usage: bool = True,
        include_performance_metrics: bool = True,
        group_by_period: str = "day"
    ) -> GetPipelineHistoryResult:
        """
        Query pipeline execution history and analytics.
        
        Args:
            workspace_name: Optional workspace filter
            template_id: Optional template filter
            date_range_days: Number of days to include
            include_step_breakdown: Whether to include step-level analytics
            include_token_usage: Whether to include token usage trends
            include_performance_metrics: Whether to include performance metrics
            group_by_period: Period for grouping data
            
        Returns:
            Historical analytics and trend data
        """
        query = GetPipelineHistoryQuery(
            workspace_name=workspace_name,
            template_id=template_id,
            date_range_days=date_range_days,
            include_step_breakdown=include_step_breakdown,
            include_token_usage=include_token_usage,
            include_performance_metrics=include_performance_metrics,
            group_by_period=group_by_period
        )
        
        return await self._query_bus.send(query)
    
    async def query_pipeline_metrics(
        self,
        workspace_name: Optional[str] = None,
        template_ids: Optional[List[Union[str, PipelineId]]] = None,
        date_range_days: int = 7,
        include_cost_analysis: bool = True,
        include_performance_breakdown: bool = True,
        include_error_analysis: bool = True,
        compare_previous_period: bool = False
    ) -> GetPipelineMetricsResult:
        """
        Query pipeline performance metrics and KPIs.
        
        Args:
            workspace_name: Optional workspace filter
            template_ids: Optional template filters
            date_range_days: Number of days to analyze
            include_cost_analysis: Whether to include cost analysis
            include_performance_breakdown: Whether to include performance breakdown
            include_error_analysis: Whether to include error analysis
            compare_previous_period: Whether to compare with previous period
            
        Returns:
            Performance metrics and recommendations
        """
        query = GetPipelineMetricsQuery(
            workspace_name=workspace_name,
            template_ids=template_ids or [],
            date_range_days=date_range_days,
            include_cost_analysis=include_cost_analysis,
            include_performance_breakdown=include_performance_breakdown,
            include_error_analysis=include_error_analysis,
            compare_previous_period=compare_previous_period
        )
        
        return await self._query_bus.send(query)
    
    async def query_step_executions(
        self,
        run_id: Optional[str] = None,
        step_id: Optional[Union[str, StepId]] = None,
        workspace_name: Optional[str] = None,
        status_filter: Optional[List[str]] = None,
        date_range_days: int = 7,
        include_outputs: bool = False,
        include_llm_details: bool = False,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "started_at",
        sort_direction: str = "desc"
    ) -> GetStepExecutionsResult:
        """
        Query step executions with filtering and pagination.
        
        Args:
            run_id: Optional run filter
            step_id: Optional step filter
            workspace_name: Optional workspace filter
            status_filter: Optional status filters
            date_range_days: Number of days to include
            include_outputs: Whether to include step outputs
            include_llm_details: Whether to include LLM details
            page: Page number for pagination
            page_size: Number of items per page
            sort_by: Field to sort by
            sort_direction: Sort direction (asc/desc)
            
        Returns:
            Query result with step executions and analytics
        """
        query = GetStepExecutionsQuery(
            run_id=run_id,
            step_id=step_id,
            workspace_name=workspace_name,
            status_filter=status_filter or [],
            date_range_days=date_range_days,
            include_outputs=include_outputs,
            include_llm_details=include_llm_details,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction
        )
        
        return await self._query_bus.send(query)