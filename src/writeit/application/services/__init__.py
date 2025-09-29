"""Application Services Layer.

This module provides high-level application services that orchestrate domain
services and coordinate cross-domain operations. These services provide the
main entry points for CLI, TUI, and API interfaces.

## Services

### PipelineApplicationService
Orchestrates pipeline operations across domains including:
- Pipeline creation and validation
- Cross-domain pipeline execution
- Pipeline lifecycle management
- Analytics and optimization

### WorkspaceApplicationService  
Manages workspace operations and configurations including:
- Workspace creation and management
- Configuration management across domains
- Analytics and reporting

### ContentApplicationService
Handles content creation and management workflows including:
- Template and style management
- Content generation coordination
- Quality assessment and optimization
- Content lifecycle operations

### ExecutionApplicationService
Coordinates LLM execution and performance including:
- Multi-provider LLM coordination
- Cache and token management
- Performance optimization and monitoring
- Analytics and alerting

## Design Principles

1. **Domain Orchestration**: Coordinate domain services without duplicating logic
2. **User-Facing Use Cases**: Provide complete workflows for user goals
3. **Cross-Domain Coordination**: Handle interactions between domains
4. **Transaction Management**: Ensure consistency across operations
5. **Error Handling**: Convert domain errors to application responses
6. **Async Support**: Full async/await support for all operations
"""

from .pipeline_application_service import (
    PipelineApplicationService,
    PipelineExecutionRequest,
    PipelineExecutionResult,
    PipelineCreationRequest,
    PipelineListingOptions,
    PipelineExecutionMode,
    PipelineSource,
    PipelineApplicationError,
    PipelineValidationError,
    PipelineExecutionError,
    PipelineNotFoundError,
    WorkspaceNotAvailableError,
)

from .workspace_application_service import (
    WorkspaceApplicationService,
    WorkspaceCreationRequest,
    WorkspaceListingOptions,
    WorkspaceBackupRequest,
    WorkspaceReportRequest,
    WorkspaceInitializationMode,
    WorkspaceBackupScope,
    WorkspaceReportType,
    WorkspaceApplicationError,
    WorkspaceCreationError,
    WorkspaceNotFoundError,
    WorkspaceBackupError,
)

from .content_application_service import (
    ContentApplicationService,
    TemplateCreationRequest,
    StyleCreationRequest,
    ContentGenerationRequest,
    ContentListingRequest,
    ContentValidationRequest,
    ContentOptimizationRequest,
    ContentAnalysisRequest,
    ContentCreationMode,
    ContentValidationLevel,
    ContentOptimizationGoal,
    ContentListingScope,
    ContentApplicationError,
    ContentCreationError,
    ContentValidationError,
    ContentNotFoundError,
    ContentOptimizationError,
)

from .execution_application_service import (
    ExecutionApplicationService,
    ExecutionRequest,
    ExecutionConfiguration,
    PerformanceAnalysisRequest,
    OptimizationRequest,
    MonitoringSetupRequest,
    ExecutionStrategy,
    MonitoringLevel,
    OptimizationGoal,
    AlertSeverity,
    ExecutionApplicationError,
    ExecutionConfigurationError,
    ExecutionFailedError,
    OptimizationError,
    MonitoringError,
)


__all__ = [
    # Pipeline Application Service
    "PipelineApplicationService",
    "PipelineExecutionRequest",
    "PipelineExecutionResult", 
    "PipelineCreationRequest",
    "PipelineListingOptions",
    "PipelineExecutionMode",
    "PipelineSource",
    "PipelineApplicationError",
    "PipelineValidationError",
    "PipelineExecutionError",
    "PipelineNotFoundError",
    "WorkspaceNotAvailableError",
    
    # Workspace Application Service
    "WorkspaceApplicationService",
    "WorkspaceCreationRequest",
    "WorkspaceListingOptions",
    "WorkspaceBackupRequest",
 
    "WorkspaceReportRequest",
    "WorkspaceInitializationMode",
    "WorkspaceBackupScope",
    "WorkspaceReportType",
    "WorkspaceApplicationError",
    "WorkspaceCreationError",
    "WorkspaceNotFoundError",
    "WorkspaceBackupError",
    
    # Content Application Service
    "ContentApplicationService",
    "TemplateCreationRequest",
    "StyleCreationRequest",
    "ContentGenerationRequest",
    "ContentListingRequest",
    "ContentValidationRequest",
    "ContentOptimizationRequest",
    "ContentAnalysisRequest",
    "ContentCreationMode",
    "ContentValidationLevel",
    "ContentOptimizationGoal",
    "ContentListingScope",
    "ContentApplicationError",
    "ContentCreationError",
    "ContentValidationError",
    "ContentNotFoundError",
    "ContentOptimizationError",
    
    # Execution Application Service
    "ExecutionApplicationService",
    "ExecutionRequest",
    "ExecutionConfiguration",
    "PerformanceAnalysisRequest",
    "OptimizationRequest", 
    "MonitoringSetupRequest",
    "ExecutionStrategy",
    "MonitoringLevel",
    "OptimizationGoal",
    "AlertSeverity",
    "ExecutionApplicationError",
    "ExecutionConfigurationError",
    "ExecutionFailedError",
    "OptimizationError",
    "MonitoringError",
    
]