"""API Error Handler for domain exception mapping.

Provides comprehensive error handling that maps domain exceptions
to appropriate HTTP responses while preserving error context.
"""

from __future__ import annotations
import traceback
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Type, Callable
from enum import Enum
import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

from ...shared.errors.base import DomainError, ValidationError, NotFoundError, ConflictError
from ...shared.errors.exceptions import (
    ServiceNotFoundError,
    CircularDependencyError,
    InvalidServiceRegistrationError,
    ServiceLifetimeError,
    AsyncServiceError
)
from ...domains.workspace.errors import (
    WorkspaceNotFoundError,
    WorkspaceAlreadyExistsError,
    WorkspaceConfigurationError,
    WorkspaceAccessDeniedError
)
from ...domains.pipeline.errors import (
    PipelineNotFoundError,
    PipelineValidationError,
    PipelineExecutionError,
    StepExecutionError
)
from ...domains.content.errors import (
    ContentNotFoundError,
    ContentValidationError,
    TemplateProcessingError
)
from .context import APIContextManager

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class APIErrorResponse:
    """Structured API error response."""
    
    error_type: str
    message: str
    details: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    context: Dict[str, Any] = None
    suggestions: List[str] = None
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.suggestions is None:
            self.suggestions = []


class APIErrorHandler:
    """Handles domain exceptions and converts them to HTTP responses."""
    
    def __init__(self):
        self._exception_mappings: Dict[Type[Exception], Callable[[Exception], APIErrorResponse]] = {}
        self._setup_default_mappings()
    
    def _setup_default_mappings(self) -> None:
        """Set up default exception to HTTP status mappings."""
        
        # Domain validation errors -> 400 Bad Request
        self.register_mapping(ValidationError, self._handle_validation_error)
        self.register_mapping(PipelineValidationError, self._handle_pipeline_validation_error)
        self.register_mapping(ContentValidationError, self._handle_content_validation_error)
        self.register_mapping(WorkspaceConfigurationError, self._handle_workspace_config_error)
        
        # Not found errors -> 404 Not Found
        self.register_mapping(NotFoundError, self._handle_not_found_error)
        self.register_mapping(WorkspaceNotFoundError, self._handle_workspace_not_found_error)
        self.register_mapping(PipelineNotFoundError, self._handle_pipeline_not_found_error)
        self.register_mapping(ContentNotFoundError, self._handle_content_not_found_error)
        
        # Conflict errors -> 409 Conflict
        self.register_mapping(ConflictError, self._handle_conflict_error)
        self.register_mapping(WorkspaceAlreadyExistsError, self._handle_workspace_conflict_error)
        
        # Access denied -> 403 Forbidden
        self.register_mapping(WorkspaceAccessDeniedError, self._handle_access_denied_error)
        
        # Execution errors -> 500 Internal Server Error
        self.register_mapping(PipelineExecutionError, self._handle_execution_error)
        self.register_mapping(StepExecutionError, self._handle_step_execution_error)
        self.register_mapping(TemplateProcessingError, self._handle_template_processing_error)
        
        # Dependency injection errors -> 500 Internal Server Error
        self.register_mapping(ServiceNotFoundError, self._handle_service_not_found_error)
        self.register_mapping(CircularDependencyError, self._handle_circular_dependency_error)
        self.register_mapping(InvalidServiceRegistrationError, self._handle_invalid_service_registration_error)
        self.register_mapping(ServiceLifetimeError, self._handle_service_lifetime_error)
        self.register_mapping(AsyncServiceError, self._handle_async_service_error)
    
    def register_mapping(
        self, 
        exception_type: Type[Exception], 
        handler: Callable[[Exception], APIErrorResponse]
    ) -> None:
        """Register custom exception mapping."""
        self._exception_mappings[exception_type] = handler
    
    def create_error_response(self, exception: Exception) -> APIErrorResponse:
        """Create structured error response from exception."""
        # Get request context for additional information
        context = APIContextManager.get_context()
        request_id = context.request_id if context else None
        
        # Find appropriate handler
        for exc_type, handler in self._exception_mappings.items():
            if isinstance(exception, exc_type):
                error_response = handler(exception)
                error_response.request_id = request_id
                if context:
                    error_response.timestamp = context.timestamp.isoformat()
                return error_response
        
        # Default handler for unhandled exceptions
        return self._handle_generic_error(exception, request_id)
    
    def to_http_exception(self, error_response: APIErrorResponse) -> HTTPException:
        """Convert error response to HTTPException."""
        # Determine HTTP status code based on error type
        status_code = self._get_status_code(error_response.error_type)
        
        # Create detail dictionary
        detail = {
            "error_type": error_response.error_type,
            "message": error_response.message,
            "request_id": error_response.request_id,
            "timestamp": error_response.timestamp,
            "severity": error_response.severity.value
        }
        
        if error_response.details:
            detail["details"] = error_response.details
        
        if error_response.context:
            detail["context"] = error_response.context
        
        if error_response.suggestions:
            detail["suggestions"] = error_response.suggestions
        
        return HTTPException(status_code=status_code, detail=detail)
    
    def _get_status_code(self, error_type: str) -> int:
        """Get HTTP status code for error type."""
        status_mappings = {
            "validation_error": status.HTTP_400_BAD_REQUEST,
            "pipeline_validation_error": status.HTTP_400_BAD_REQUEST,
            "content_validation_error": status.HTTP_400_BAD_REQUEST,
            "workspace_configuration_error": status.HTTP_400_BAD_REQUEST,
            "not_found_error": status.HTTP_404_NOT_FOUND,
            "workspace_not_found_error": status.HTTP_404_NOT_FOUND,
            "pipeline_not_found_error": status.HTTP_404_NOT_FOUND,
            "content_not_found_error": status.HTTP_404_NOT_FOUND,
            "conflict_error": status.HTTP_409_CONFLICT,
            "workspace_already_exists_error": status.HTTP_409_CONFLICT,
            "access_denied_error": status.HTTP_403_FORBIDDEN,
            "workspace_access_denied_error": status.HTTP_403_FORBIDDEN,
            "execution_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "step_execution_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "template_processing_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "service_error": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "generic_error": status.HTTP_500_INTERNAL_SERVER_ERROR
        }
        
        return status_mappings.get(error_type, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Specific error handlers
    
    def _handle_validation_error(self, exc: ValidationError) -> APIErrorResponse:
        """Handle validation errors."""
        return APIErrorResponse(
            error_type="validation_error",
            message=str(exc),
            details=getattr(exc, 'details', None),
            context={"validation_field": getattr(exc, 'field', None)},
            suggestions=[
                "Check the input data format and types",
                "Refer to the API documentation for valid values"
            ],
            severity=ErrorSeverity.LOW
        )
    
    def _handle_pipeline_validation_error(self, exc: PipelineValidationError) -> APIErrorResponse:
        """Handle pipeline validation errors."""
        return APIErrorResponse(
            error_type="pipeline_validation_error",
            message=f"Pipeline validation failed: {exc}",
            details=getattr(exc, 'validation_details', None),
            context={
                "pipeline_id": getattr(exc, 'pipeline_id', None),
                "step_id": getattr(exc, 'step_id', None)
            },
            suggestions=[
                "Check pipeline YAML syntax and structure",
                "Validate all required fields are present",
                "Use 'writeit validate' command to check locally"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    
    def _handle_content_validation_error(self, exc: ContentValidationError) -> APIErrorResponse:
        """Handle content validation errors."""
        return APIErrorResponse(
            error_type="content_validation_error", 
            message=f"Content validation failed: {exc}",
            details=getattr(exc, 'validation_details', None),
            context={"content_type": getattr(exc, 'content_type', None)},
            suggestions=[
                "Check content format and encoding",
                "Ensure all required content fields are present"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    
    def _handle_workspace_config_error(self, exc: WorkspaceConfigurationError) -> APIErrorResponse:
        """Handle workspace configuration errors."""
        return APIErrorResponse(
            error_type="workspace_configuration_error",
            message=f"Workspace configuration error: {exc}",
            details=getattr(exc, 'config_details', None),
            context={"workspace_name": getattr(exc, 'workspace_name', None)},
            suggestions=[
                "Check workspace configuration file",
                "Use 'writeit workspace info' to check current settings",
                "Initialize workspace with 'writeit init'"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    
    def _handle_not_found_error(self, exc: NotFoundError) -> APIErrorResponse:
        """Handle generic not found errors."""
        return APIErrorResponse(
            error_type="not_found_error",
            message=str(exc),
            suggestions=[
                "Check that the resource exists",
                "Verify you have access to the resource"
            ],
            severity=ErrorSeverity.LOW
        )
    
    def _handle_workspace_not_found_error(self, exc: WorkspaceNotFoundError) -> APIErrorResponse:
        """Handle workspace not found errors."""
        return APIErrorResponse(
            error_type="workspace_not_found_error",
            message=f"Workspace not found: {exc}",
            context={"workspace_name": getattr(exc, 'workspace_name', None)},
            suggestions=[
                "Create workspace with 'writeit workspace create'",
                "List available workspaces with 'writeit workspace list'",
                "Use 'default' workspace if unsure"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    
    def _handle_pipeline_not_found_error(self, exc: PipelineNotFoundError) -> APIErrorResponse:
        """Handle pipeline not found errors."""
        return APIErrorResponse(
            error_type="pipeline_not_found_error",
            message=f"Pipeline not found: {exc}",
            context={"pipeline_id": getattr(exc, 'pipeline_id', None)},
            suggestions=[
                "Check the pipeline ID or name",
                "List available pipelines",
                "Ensure pipeline is in the correct workspace"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    
    def _handle_content_not_found_error(self, exc: ContentNotFoundError) -> APIErrorResponse:
        """Handle content not found errors."""
        return APIErrorResponse(
            error_type="content_not_found_error",
            message=f"Content not found: {exc}",
            context={"content_id": getattr(exc, 'content_id', None)},
            suggestions=[
                "Verify the content path or ID",
                "Check content exists in workspace"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    
    def _handle_conflict_error(self, exc: ConflictError) -> APIErrorResponse:
        """Handle generic conflict errors."""
        return APIErrorResponse(
            error_type="conflict_error",
            message=str(exc),
            suggestions=[
                "Check for existing resources with the same identifier",
                "Use a different name or ID"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    
    def _handle_workspace_conflict_error(self, exc: WorkspaceAlreadyExistsError) -> APIErrorResponse:
        """Handle workspace already exists errors."""
        return APIErrorResponse(
            error_type="workspace_already_exists_error",
            message=f"Workspace already exists: {exc}",
            context={"workspace_name": getattr(exc, 'workspace_name', None)},
            suggestions=[
                "Use a different workspace name",
                "Switch to existing workspace with 'writeit workspace use'",
                "Remove existing workspace if no longer needed"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    
    def _handle_access_denied_error(self, exc: WorkspaceAccessDeniedError) -> APIErrorResponse:
        """Handle access denied errors."""
        return APIErrorResponse(
            error_type="workspace_access_denied_error",
            message=f"Access denied: {exc}",
            context={"workspace_name": getattr(exc, 'workspace_name', None)},
            suggestions=[
                "Check your permissions for this workspace",
                "Contact workspace administrator for access"
            ],
            severity=ErrorSeverity.HIGH
        )
    
    def _handle_execution_error(self, exc: PipelineExecutionError) -> APIErrorResponse:
        """Handle pipeline execution errors."""
        return APIErrorResponse(
            error_type="execution_error",
            message=f"Pipeline execution failed: {exc}",
            details=getattr(exc, 'execution_details', None),
            context={
                "pipeline_id": getattr(exc, 'pipeline_id', None),
                "run_id": getattr(exc, 'run_id', None)
            },
            suggestions=[
                "Check pipeline configuration and inputs",
                "Review execution logs for details",
                "Retry with different parameters if appropriate"
            ],
            severity=ErrorSeverity.HIGH
        )
    
    def _handle_step_execution_error(self, exc: StepExecutionError) -> APIErrorResponse:
        """Handle step execution errors."""
        return APIErrorResponse(
            error_type="step_execution_error",
            message=f"Step execution failed: {exc}",
            details=getattr(exc, 'step_details', None),
            context={
                "step_id": getattr(exc, 'step_id', None),
                "run_id": getattr(exc, 'run_id', None)
            },
            suggestions=[
                "Check step configuration and dependencies",
                "Review step inputs and LLM responses",
                "Consider retrying the step"
            ],
            severity=ErrorSeverity.HIGH
        )
    
    def _handle_template_processing_error(self, exc: TemplateProcessingError) -> APIErrorResponse:
        """Handle template processing errors."""
        return APIErrorResponse(
            error_type="template_processing_error",
            message=f"Template processing failed: {exc}",
            details=getattr(exc, 'template_details', None),
            context={"template_id": getattr(exc, 'template_id', None)},
            suggestions=[
                "Check template syntax and variables",
                "Ensure all required template variables are provided",
                "Validate template structure"
            ],
            severity=ErrorSeverity.MEDIUM
        )
    
    def _handle_service_not_found_error(self, exc: ServiceNotFoundError) -> APIErrorResponse:
        """Handle service not found errors."""
        return APIErrorResponse(
            error_type="service_error",
            message=f"Service dependency not available: {exc}",
            details="Required service is not registered in dependency container",
            context={"service_type": str(getattr(exc, 'service_type', None))},
            suggestions=[
                "Check service registration in container",
                "Ensure all required dependencies are configured"
            ],
            severity=ErrorSeverity.CRITICAL
        )
    
    def _handle_circular_dependency_error(self, exc: CircularDependencyError) -> APIErrorResponse:
        """Handle circular dependency errors."""
        return APIErrorResponse(
            error_type="service_error",
            message=f"Circular dependency detected: {exc}",
            details="Service dependency chain forms a circular reference",
            suggestions=[
                "Review service registrations for circular dependencies",
                "Consider using factory patterns to break cycles"
            ],
            severity=ErrorSeverity.CRITICAL
        )
    
    def _handle_invalid_service_registration_error(self, exc: InvalidServiceRegistrationError) -> APIErrorResponse:
        """Handle invalid service registration errors."""
        return APIErrorResponse(
            error_type="service_error",
            message=f"Invalid service registration: {exc}",
            suggestions=[
                "Check service registration parameters",
                "Ensure implementation matches interface"
            ],
            severity=ErrorSeverity.CRITICAL
        )
    
    def _handle_service_lifetime_error(self, exc: ServiceLifetimeError) -> APIErrorResponse:
        """Handle service lifetime errors."""
        return APIErrorResponse(
            error_type="service_error",
            message=f"Service lifetime error: {exc}",
            suggestions=[
                "Check service scope configuration",
                "Ensure services are accessed within appropriate scope"
            ],
            severity=ErrorSeverity.HIGH
        )
    
    def _handle_async_service_error(self, exc: AsyncServiceError) -> APIErrorResponse:
        """Handle async service errors."""
        return APIErrorResponse(
            error_type="service_error",
            message=f"Async service error: {exc}",
            suggestions=[
                "Use async service resolution methods",
                "Check async context and event loop"
            ],
            severity=ErrorSeverity.HIGH
        )
    
    def _handle_generic_error(self, exc: Exception, request_id: Optional[str]) -> APIErrorResponse:
        """Handle generic unhandled exceptions."""
        logger.error(f"Unhandled exception in API: {exc}", exc_info=True)
        
        return APIErrorResponse(
            error_type="generic_error",
            message="An unexpected error occurred",
            details=str(exc) if logger.isEnabledFor(logging.DEBUG) else None,
            request_id=request_id,
            suggestions=[
                "Try again later",
                "Contact support if the problem persists"
            ],
            severity=ErrorSeverity.CRITICAL
        )


# Global error handler instance
error_handler = APIErrorHandler()


async def domain_exception_handler(request: Request, exc: DomainError) -> JSONResponse:
    """FastAPI exception handler for domain exceptions."""
    error_response = error_handler.create_error_response(exc)
    status_code = error_handler._get_status_code(error_response.error_type)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error_type": error_response.error_type,
            "message": error_response.message,
            "details": error_response.details,
            "request_id": error_response.request_id,
            "timestamp": error_response.timestamp,
            "context": error_response.context,
            "suggestions": error_response.suggestions,
            "severity": error_response.severity.value
        }
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """FastAPI exception handler for generic exceptions."""
    error_response = error_handler.create_error_response(exc)
    status_code = error_handler._get_status_code(error_response.error_type)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error_type": error_response.error_type,
            "message": error_response.message,
            "details": error_response.details,
            "request_id": error_response.request_id,
            "timestamp": error_response.timestamp,
            "context": error_response.context,
            "suggestions": error_response.suggestions,
            "severity": error_response.severity.value
        }
    )


async def http_exception_handler_with_context(request: Request, exc: HTTPException) -> JSONResponse:
    """Enhanced HTTP exception handler with context."""
    context = APIContextManager.get_context()
    request_id = context.request_id if context else None
    
    # If detail is already a dict (from our error handling), use it directly
    if isinstance(exc.detail, dict):
        content = exc.detail
        if request_id and "request_id" not in content:
            content["request_id"] = request_id
    else:
        # Standard HTTP exception
        content = {
            "error_type": "http_error",
            "message": exc.detail,
            "request_id": request_id,
            "timestamp": context.timestamp.isoformat() if context else None
        }
    
    return JSONResponse(
        status_code=exc.status_code,
        content=content
    )