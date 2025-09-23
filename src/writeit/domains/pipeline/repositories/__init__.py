"""Pipeline domain repositories.

Repository interfaces for pipeline domain entities providing
data access operations with workspace isolation and advanced querying.
"""

from .pipeline_template_repository import (
    PipelineTemplateRepository,
    ByWorkspaceSpecification,
    ByNameSpecification,
    ByTagSpecification,
    GlobalTemplateSpecification,
    ByVersionSpecification,
)

from .pipeline_run_repository import (
    PipelineRunRepository,
    ByTemplateIdSpecification,
    ByStatusSpecification,
    ActiveRunsSpecification,
    CompletedRunsSpecification,
    FailedRunsSpecification,
    DateRangeSpecification,
)

from .step_execution_repository import (
    StepExecutionRepository,
    StepExecution,
    ByRunIdSpecification,
    ByStepIdSpecification,
    FailedExecutionsSpecification,
    RetryExecutionsSpecification,
    SuccessfulExecutionsSpecification,
)

__all__ = [
    # Repository interfaces
    "PipelineTemplateRepository",
    "PipelineRunRepository", 
    "StepExecutionRepository",
    
    # Value objects
    "StepExecution",
    
    # Template specifications
    "ByWorkspaceSpecification",
    "ByNameSpecification", 
    "ByTagSpecification",
    "GlobalTemplateSpecification",
    "ByVersionSpecification",
    
    # Run specifications
    "ByTemplateIdSpecification",
    "ByStatusSpecification",
    "ActiveRunsSpecification",
    "CompletedRunsSpecification", 
    "FailedRunsSpecification",
    "DateRangeSpecification",
    
    # Step execution specifications
    "ByRunIdSpecification",
    "ByStepIdSpecification",
    "FailedExecutionsSpecification",
    "RetryExecutionsSpecification",
    "SuccessfulExecutionsSpecification",
]