# ABOUTME: Comprehensive error handling for WriteIt
# ABOUTME: Defines custom exceptions with helpful error messages and recovery suggestions

from typing import Optional, Dict, Any
import sys


class WriteItError(Exception):
    """Base exception for all WriteIt errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
        suggestion: Optional[str] = None,
        error_code: Optional[str] = None
    ):
        self.message = message
        self.details = details
        self.suggestion = suggestion
        self.error_code = error_code
        super().__init__(message)
    
    def format_error(self) -> str:
        """Format error with details and suggestions."""
        output = [f"❌ {self.message}"]
        
        if self.details:
            output.append(f"   Details: {self.details}")
        
        if self.suggestion:
            output.append(f"   💡 Suggestion: {self.suggestion}")
        
        if self.error_code:
            output.append(f"   Error Code: {self.error_code}")
        
        return "\n".join(output)


class WorkspaceError(WriteItError):
    """Errors related to workspace operations."""
    pass


class PipelineError(WriteItError):
    """Errors related to pipeline operations."""
    pass


class LLMError(WriteItError):
    """Errors related to LLM operations."""
    pass


class StorageError(WriteItError):
    """Errors related to storage operations."""
    pass


class ValidationError(WriteItError):
    """Errors related to validation operations."""
    pass


class ConfigurationError(WriteItError):
    """Errors related to configuration."""
    pass


# Specific error instances with helpful messages
class WorkspaceNotFoundError(WorkspaceError):
    def __init__(self, workspace_name: str):
        super().__init__(
            message=f"Workspace '{workspace_name}' not found",
            details=f"The workspace '{workspace_name}' does not exist in your WriteIt installation",
            suggestion="Use 'writeit workspace list' to see available workspaces or 'writeit workspace create <name>' to create a new one",
            error_code="WS001"
        )


class WorkspaceAlreadyExistsError(WorkspaceError):
    def __init__(self, workspace_name: str):
        super().__init__(
            message=f"Workspace '{workspace_name}' already exists",
            details=f"A workspace with the name '{workspace_name}' already exists",
            suggestion="Choose a different name or use 'writeit workspace use <name>' to switch to the existing workspace",
            error_code="WS002"
        )


class PipelineNotFoundError(PipelineError):
    def __init__(self, pipeline_name: str, workspace: Optional[str] = None):
        workspace_info = f" in workspace '{workspace}'" if workspace else ""
        super().__init__(
            message=f"Pipeline '{pipeline_name}' not found{workspace_info}",
            details=f"The pipeline template '{pipeline_name}' does not exist",
            suggestion="Use 'writeit list-pipelines' to see available pipelines or check the pipeline name spelling",
            error_code="PL001"
        )


class InvalidPipelineError(PipelineError):
    def __init__(self, pipeline_name: str, validation_errors: list):
        errors_text = "\n".join(f"    - {error}" for error in validation_errors)
        super().__init__(
            message=f"Pipeline '{pipeline_name}' is invalid",
            details=f"Validation errors:\n{errors_text}",
            suggestion="Fix the validation errors in your pipeline template or use 'writeit validate <pipeline>' for detailed information",
            error_code="PL002"
        )


class LLMConnectionError(LLMError):
    def __init__(self, model_name: str, original_error: Exception):
        super().__init__(
            message=f"Failed to connect to LLM model '{model_name}'",
            details=f"Connection error: {original_error}",
            suggestion="Check your API keys, network connection, and model availability. See documentation for setup instructions",
            error_code="LLM001"
        )


class LLMQuotaExceededError(LLMError):
    def __init__(self, model_name: str):
        super().__init__(
            message=f"Quota exceeded for model '{model_name}'",
            details="You have exceeded your API usage quota for this model",
            suggestion="Check your API usage limits, upgrade your plan, or try a different model",
            error_code="LLM002"
        )


class StoragePermissionError(StorageError):
    def __init__(self, path: str):
        super().__init__(
            message=f"Permission denied accessing storage at '{path}'",
            details="WriteIt does not have permission to read/write to the storage location",
            suggestion="Check file permissions or run 'writeit init' to reinitialize workspace",
            error_code="ST001"
        )


class StorageCorruptedError(StorageError):
    def __init__(self, db_name: str):
        super().__init__(
            message=f"Storage database '{db_name}' is corrupted",
            details="The storage database appears to be corrupted or incompatible",
            suggestion="Try backing up your data and running 'writeit init --migrate' to recreate the storage",
            error_code="ST002"
        )


class InvalidTemplateError(ValidationError):
    def __init__(self, template_name: str, errors: list):
        errors_text = "\n".join(f"    - {error}" for error in errors)
        super().__init__(
            message=f"Template '{template_name}' is invalid",
            details=f"Validation errors:\n{errors_text}",
            suggestion="Fix the validation errors in your template or check the template format documentation",
            error_code="VAL001"
        )


class MissingDependencyError(ConfigurationError):
    def __init__(self, dependency: str, feature: str):
        super().__init__(
            message=f"Missing dependency '{dependency}' for {feature}",
            details=f"The required dependency '{dependency}' is not installed",
            suggestion=f"Install the dependency with 'pip install {dependency}' or 'uv add {dependency}'",
            error_code="CFG001"
        )


def handle_error(error: Exception, exit_on_error: bool = True) -> None:
    """Handle and display errors in a user-friendly way.
    
    Args:
        error: The exception to handle
        exit_on_error: Whether to exit the application after handling the error
    """
    if isinstance(error, WriteItError):
        print(error.format_error(), file=sys.stderr)
    else:
        # Handle unexpected errors
        print(f"❌ Unexpected error: {error}", file=sys.stderr)
        print("   💡 Suggestion: Please report this issue to the WriteIt team", file=sys.stderr)
    
    if exit_on_error:
        sys.exit(1)


def wrap_error(func):
    """Decorator to wrap functions with error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except WriteItError:
            # Re-raise WriteIt errors as-is
            raise
        except Exception as e:
            # Convert unexpected errors to WriteItError
            raise WriteItError(
                message=f"Unexpected error in {func.__name__}",
                details=str(e),
                suggestion="Please report this issue if it persists",
                error_code="UNK001"
            ) from e
    
    return wrapper