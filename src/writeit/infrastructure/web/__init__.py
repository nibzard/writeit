"""Web infrastructure module for WriteIt API.

Provides FastAPI-based web infrastructure with domain-driven design integration,
including context management, error handling, validation, and WebSocket support.
"""

from .app import WriteItAPIApplication, create_app, get_application
from .context import (
    APIRequestContext, APIContextManager, APIContextMiddleware,
    get_current_context, get_current_workspace_name, get_current_user_id,
    get_current_container, require_authentication
)
from .error_handler import (
    APIErrorResponse, APIErrorHandler, ErrorSeverity,
    error_handler, domain_exception_handler, generic_exception_handler,
    http_exception_handler_with_context
)
from .validation import (
    APIValidator, ValidationResult, ValidationRule, ValidationType,
    CreateWorkspaceRequest, UpdateWorkspaceRequest,
    CreatePipelineTemplateRequest, UpdatePipelineTemplateRequest,
    ExecutePipelineRequest, CreateContentRequest,
    api_validator, validate_workspace_request, validate_pipeline_request,
    validate_content_request, handle_pydantic_validation_error
)
from .response_mapper import (
    WorkspaceDTO, WorkspaceConfigurationDTO, PipelineTemplateDTO,
    PipelineRunDTO, StepExecutionDTO, ContentDTO, TemplateDTO, StyleDTO,
    ExecutionContextDTO, ExecutionResultDTO, APIResponseMapper, response_mapper
)
from .handlers import (
    WorkspaceHandlers, PipelineHandlers, ContentHandlers, HealthHandlers
)
from .websocket_handlers import (
    WebSocketMessageType, WebSocketMessage, WebSocketConnection,
    WebSocketManager, WebSocketHandler
)
from .routes import (
    create_workspace_router, create_pipeline_router, create_content_router,
    create_health_router, create_api_router, create_utility_router, ROUTE_TAGS
)

__all__ = [
    # Application
    "WriteItAPIApplication",
    "create_app", 
    "get_application",
    
    # Context
    "APIRequestContext",
    "APIContextManager",
    "APIContextMiddleware",
    "get_current_context",
    "get_current_workspace_name",
    "get_current_user_id",
    "get_current_container",
    "require_authentication",
    
    # Error handling
    "APIErrorResponse",
    "APIErrorHandler",
    "ErrorSeverity",
    "error_handler",
    "domain_exception_handler",
    "generic_exception_handler",
    "http_exception_handler_with_context",
    
    # Validation
    "APIValidator",
    "ValidationResult",
    "ValidationRule",
    "ValidationType",
    "CreateWorkspaceRequest",
    "UpdateWorkspaceRequest",
    "CreatePipelineTemplateRequest",
    "UpdatePipelineTemplateRequest",
    "ExecutePipelineRequest",
    "CreateContentRequest",
    "api_validator",
    "validate_workspace_request",
    "validate_pipeline_request",
    "validate_content_request",
    "handle_pydantic_validation_error",
    
    # Response mapping
    "WorkspaceDTO",
    "WorkspaceConfigurationDTO",
    "PipelineTemplateDTO",
    "PipelineRunDTO",
    "StepExecutionDTO",
    "ContentDTO",
    "TemplateDTO",
    "StyleDTO",
    "ExecutionContextDTO",
    "ExecutionResultDTO",
    "APIResponseMapper",
    "response_mapper",
    
    # Handlers
    "WorkspaceHandlers",
    "PipelineHandlers",
    "ContentHandlers",
    "HealthHandlers",
    
    # WebSocket
    "WebSocketMessageType",
    "WebSocketMessage",
    "WebSocketConnection",
    "WebSocketManager",
    "WebSocketHandler",
    
    # Routes
    "create_workspace_router",
    "create_pipeline_router",
    "create_content_router",
    "create_health_router",
    "create_api_router",
    "create_utility_router",
    "ROUTE_TAGS",
]