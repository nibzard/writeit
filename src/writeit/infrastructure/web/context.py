"""API Context for request management and workspace awareness.

Provides request-scoped context management with workspace isolation,
user authentication, and dependency injection integration.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TYPE_CHECKING
from contextvars import ContextVar
import uuid
from datetime import datetime

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from ...domains.workspace.value_objects import WorkspaceName
from ...shared.dependencies.container import Container

if TYPE_CHECKING:
    from ...domains.workspace.entities import Workspace


@dataclass
class APIRequestContext:
    """Request context with workspace and user information."""
    
    # Request identification
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    # User and authentication
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    auth_token: Optional[str] = None
    
    # Workspace context
    workspace_name: str = "default"
    workspace: Optional[Workspace] = None
    
    # Request details
    method: str = ""
    path: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, Any] = field(default_factory=dict)
    
    # Dependency injection
    container: Optional[Container] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_workspace_name(self) -> WorkspaceName:
        """Get workspace name as value object."""
        return WorkspaceName(self.workspace_name)
    
    def is_authenticated(self) -> bool:
        """Check if request is authenticated."""
        return self.user_id is not None and self.auth_token is not None
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value safely."""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value


# Context variables for request-scoped access
_request_context: ContextVar[Optional[APIRequestContext]] = ContextVar(
    'request_context', default=None
)


class APIContextManager:
    """Manages API request context throughout the request lifecycle."""
    
    @staticmethod
    def set_context(context: APIRequestContext) -> None:
        """Set the current request context."""
        _request_context.set(context)
    
    @staticmethod
    def get_context() -> Optional[APIRequestContext]:
        """Get the current request context."""
        return _request_context.get()
    
    @staticmethod
    def get_context_or_raise() -> APIRequestContext:
        """Get the current request context or raise error."""
        context = _request_context.get()
        if context is None:
            raise RuntimeError("No API request context available")
        return context
    
    @staticmethod
    def clear_context() -> None:
        """Clear the current request context."""
        _request_context.set(None)
    
    @staticmethod
    def get_workspace_name() -> str:
        """Get current workspace name from context."""
        context = APIContextManager.get_context()
        return context.workspace_name if context else "default"
    
    @staticmethod
    def get_user_id() -> Optional[str]:
        """Get current user ID from context."""
        context = APIContextManager.get_context()
        return context.user_id if context else None
    
    @staticmethod
    def get_container() -> Optional[Container]:
        """Get dependency injection container from context."""
        context = APIContextManager.get_context()
        return context.container if context else None


class APIContextMiddleware(BaseHTTPMiddleware):
    """Middleware to set up API request context for each request."""
    
    def __init__(self, app, container: Optional[Container] = None):
        super().__init__(app)
        self.container = container
    
    async def dispatch(self, request: Request, call_next):
        """Process request and set up context."""
        # Extract workspace name from query params, headers, or path
        workspace_name = self._extract_workspace_name(request)
        
        # Extract user information (basic implementation)
        user_id, user_name, auth_token = self._extract_user_info(request)
        
        # Create request context
        context = APIRequestContext(
            user_id=user_id,
            user_name=user_name,
            auth_token=auth_token,
            workspace_name=workspace_name,
            method=request.method,
            path=str(request.url.path),
            headers=dict(request.headers),
            query_params=dict(request.query_params),
            container=self.container
        )
        
        # Set context for the request
        APIContextManager.set_context(context)
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = context.request_id
            
            return response
        
        finally:
            # Clean up context
            APIContextManager.clear_context()
    
    def _extract_workspace_name(self, request: Request) -> str:
        """Extract workspace name from request."""
        # Check query parameters first
        workspace = request.query_params.get("workspace_name")
        if workspace:
            return workspace
        
        # Check headers
        workspace = request.headers.get("X-Workspace-Name")
        if workspace:
            return workspace
        
        # Check path parameters (for /api/workspaces/{workspace_name}/... routes)
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) >= 3 and path_parts[1] == "workspaces":
            return path_parts[2]
        
        # Default workspace
        return "default"
    
    def _extract_user_info(self, request: Request) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract user information from request."""
        # Basic implementation - can be extended for actual authentication
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # In a real implementation, you would validate the token
            # and extract user information
            user_id = request.headers.get("X-User-ID")
            user_name = request.headers.get("X-User-Name")
            
            return user_id, user_name, token
        
        # Check for API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            # In a real implementation, validate API key and get user info
            user_id = request.headers.get("X-User-ID", "api-user")
            user_name = request.headers.get("X-User-Name", "API User")
            return user_id, user_name, api_key
        
        # No authentication found
        return None, None, None


# Utility functions for easy access
def get_current_context() -> Optional[APIRequestContext]:
    """Get the current API request context."""
    return APIContextManager.get_context()


def get_current_workspace_name() -> str:
    """Get the current workspace name."""
    return APIContextManager.get_workspace_name()


def get_current_user_id() -> Optional[str]:
    """Get the current user ID."""
    return APIContextManager.get_user_id()


def get_current_container() -> Optional[Container]:
    """Get the current dependency injection container."""
    return APIContextManager.get_container()


def require_authentication() -> APIRequestContext:
    """Require authentication and return context."""
    context = APIContextManager.get_context_or_raise()
    if not context.is_authenticated():
        raise RuntimeError("Authentication required")
    return context