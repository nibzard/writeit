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

- **Pipeline**: The template definition with metadata and steps
- **PipelineRun**: A specific execution instance with runtime state
- **PipelineStep**: Individual step definition with dependencies
- **StepExecution**: Runtime state and results for a specific step

## Key Value Objects

- **PipelineId**: Strongly-typed pipeline identifier
- **StepId**: Strongly-typed step identifier  
- **PromptTemplate**: Template string with validation
- **ExecutionStatus**: State enumeration with valid transitions

## Domain Services

- **PipelineValidationService**: Template validation logic
- **PipelineExecutionService**: Core execution orchestration
- **StepDependencyService**: Step dependency resolution

## Domain Events

- **PipelineStarted**: Pipeline execution began
- **StepCompleted**: Individual step finished
- **PipelineCompleted**: Full pipeline finished
- **PipelineFailure**: Pipeline execution failed

## Boundaries

This domain owns:
- Pipeline configuration and metadata
- Execution state and progress tracking
- Step orchestration and dependency management
- Pipeline-level validation and error handling

This domain does NOT own:
- LLM integration (Execution Domain)
- Data persistence (Storage Domain)
- Workspace isolation (Workspace Domain)
- Template rendering (Content Domain)
"""