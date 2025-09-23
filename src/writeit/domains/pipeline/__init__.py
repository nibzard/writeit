"""
Pipeline Domain - Core Pipeline Management

This domain handles the complete lifecycle of pipeline execution from
template definition to result generation.

## Responsibilities

- Pipeline template configuration and validation
- Pipeline execution orchestration and state management
- Step dependency resolution and execution ordering
- Execution results collection and aggregation
- Pipeline lifecycle events (started, completed, failed)

## Key Entities

- **PipelineTemplate**: The template definition with metadata and steps
- **PipelineRun**: A specific execution instance with runtime state
- **PipelineStep**: Individual step definition with dependencies
- **StepExecution**: Runtime state and results for a specific step
- **PipelineMetadata**: Pipeline metadata, versioning, and usage statistics

## Key Value Objects

- **PipelineId**: Strongly-typed pipeline identifier
- **PipelineName**: Validated pipeline name
- **StepId**: Strongly-typed step identifier
- **StepName**: Validated step name
- **PromptTemplate**: Template string with validation and variable substitution
- **ModelPreference**: LLM model selection criteria
- **ExecutionStatus**: State enumeration with valid transitions

## Domain Events

- **PipelineCreated**: Pipeline template created
- **PipelineUpdated**: Pipeline template updated
- **PipelineDeleted**: Pipeline template deleted
- **PipelinePublished**: Pipeline template published
- **PipelineDeprecated**: Pipeline template deprecated
- **PipelineExecutionStarted**: Pipeline execution began
- **PipelineExecutionCompleted**: Pipeline execution completed successfully
- **PipelineExecutionFailed**: Pipeline execution failed
- **PipelineExecutionCancelled**: Pipeline execution cancelled
- **StepExecutionStarted**: Step execution started
- **StepExecutionCompleted**: Step execution completed
- **StepExecutionFailed**: Step execution failed
- **StepExecutionSkipped**: Step execution skipped
- **StepExecutionRetried**: Step execution retried

## Boundaries

This domain owns:
- Pipeline configuration and metadata
- Execution state and progress tracking
- Step orchestration and dependency management
- Pipeline-level validation and error handling
- Pipeline lifecycle and versioning

This domain does NOT own:
- LLM integration (Execution Domain)
- Data persistence (Storage Domain)
- Workspace isolation (Workspace Domain)
- Template rendering (Content Domain)
"""

# Import main domain components for easy access
from .value_objects import (
    PipelineId,
    PipelineName,
    StepId,
    StepName,
    PromptTemplate,
    ModelPreference,
    ExecutionStatus
)

from .entities import (
    PipelineTemplate,
    PipelineInput,
    PipelineStepTemplate,
    PipelineRun,
    PipelineStep,
    StepExecution,
    PipelineMetadata,
    PipelineUsageStats,
    PipelineCategory,
    PipelineComplexity,
    PipelineStatus
)

# Temporarily disable events import due to dataclass field ordering issue
# from .events import (
#     PipelineCreated,
#     PipelineUpdated,
#     PipelineDeleted,
#     PipelinePublished,
#     PipelineDeprecated,
#     PipelineExecutionStarted,
#     PipelineExecutionCompleted,
#     PipelineExecutionFailed,
#     PipelineExecutionCancelled,
#     StepExecutionStarted,
#     StepExecutionCompleted,
#     StepExecutionFailed,
#     StepExecutionSkipped,
#     StepExecutionRetried
# )

__all__ = [
    # Value Objects
    "PipelineId",
    "PipelineName",
    "StepId",
    "StepName", 
    "PromptTemplate",
    "ModelPreference",
    "ExecutionStatus",
    
    # Entities
    "PipelineTemplate",
    "PipelineInput",
    "PipelineStepTemplate",
    "PipelineRun",
    "PipelineStep",
    "StepExecution",
    "PipelineMetadata",
    "PipelineUsageStats",
    
    # Enums
    "PipelineCategory",
    "PipelineComplexity", 
    "PipelineStatus",
    
    # Events (temporarily disabled due to dataclass field ordering issue)
    # "PipelineCreated",
    # "PipelineUpdated",
    # "PipelineDeleted",
    # "PipelinePublished",
    # "PipelineDeprecated",
    # "PipelineExecutionStarted",
    # "PipelineExecutionCompleted",
    # "PipelineExecutionFailed",
    # "PipelineExecutionCancelled",
    # "StepExecutionStarted",
    # "StepExecutionCompleted",
    # "StepExecutionFailed",
    # "StepExecutionSkipped",
    # "StepExecutionRetried",
]