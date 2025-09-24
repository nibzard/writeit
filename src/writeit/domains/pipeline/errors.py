"""Pipeline domain errors."""

from ...shared.errors import DomainError


class PipelineError(DomainError):
    """Base exception for pipeline domain errors."""
    pass


class PipelineNotFoundError(PipelineError):
    """Raised when a pipeline is not found."""
    
    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        super().__init__(f"Pipeline '{pipeline_id}' not found")


class PipelineTemplateError(PipelineError):
    """Raised when pipeline template is invalid."""
    pass


class PipelineExecutionError(PipelineError):
    """Raised when pipeline execution fails."""
    
    def __init__(self, pipeline_id: str, step_name: str = None, reason: str = None):
        self.pipeline_id = pipeline_id
        self.step_name = step_name
        self.reason = reason
        message = f"Pipeline execution failed for '{pipeline_id}'"
        if step_name:
            message += f" at step '{step_name}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class PipelineAlreadyRunningError(PipelineError):
    """Raised when trying to execute a pipeline that is already running."""
    
    def __init__(self, pipeline_id: str):
        self.pipeline_id = pipeline_id
        super().__init__(f"Pipeline '{pipeline_id}' is already running")


class PipelineValidationError(PipelineError):
    """Raised when pipeline validation fails."""
    pass


class StepExecutionError(PipelineError):
    """Raised when step execution fails."""
    
    def __init__(self, step_name: str, pipeline_id: str = None, reason: str = None):
        self.step_name = step_name
        self.pipeline_id = pipeline_id
        self.reason = reason
        message = f"Step execution failed for '{step_name}'"
        if pipeline_id:
            message += f" in pipeline '{pipeline_id}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class StepDependencyError(PipelineError):
    """Raised when step dependencies cannot be resolved."""
    
    def __init__(self, step_name: str, dependency_name: str):
        self.step_name = step_name
        self.dependency_name = dependency_name
        super().__init__(f"Step '{step_name}' depends on unresolved step '{dependency_name}'")


class PipelineTimeoutError(PipelineError):
    """Raised when pipeline execution times out."""
    
    def __init__(self, pipeline_id: str, timeout_seconds: int):
        self.pipeline_id = pipeline_id
        self.timeout_seconds = timeout_seconds
        super().__init__(f"Pipeline '{pipeline_id}' execution timed out after {timeout_seconds} seconds")


__all__ = [
    "PipelineError",
    "PipelineNotFoundError",
    "PipelineTemplateError", 
    "PipelineExecutionError",
    "PipelineAlreadyRunningError",
    "PipelineValidationError",
    "StepExecutionError",
    "StepDependencyError",
    "PipelineTimeoutError",
]