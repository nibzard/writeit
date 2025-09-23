"""API Routes organization for WriteIt REST endpoints.

Provides clean route organization and dependency injection for
API endpoints using FastAPI router patterns.
"""

from typing import Type, List, Optional
from fastapi import APIRouter, Depends, Query, Path, Body, status
from fastapi.responses import JSONResponse

from .handlers import WorkspaceHandlers, PipelineHandlers, ContentHandlers, HealthHandlers
from .validation import (
    CreateWorkspaceRequest, UpdateWorkspaceRequest,
    CreatePipelineTemplateRequest, UpdatePipelineTemplateRequest,
    ExecutePipelineRequest, CreateContentRequest
)


def create_workspace_router(handlers: Type[WorkspaceHandlers]) -> APIRouter:
    """Create workspace-related routes."""
    router = APIRouter(prefix="/workspaces", tags=["Workspaces"])
    
    @router.post("", response_model=None, status_code=status.HTTP_201_CREATED)
    async def create_workspace(request: CreateWorkspaceRequest) -> JSONResponse:
        """Create a new workspace.
        
        Creates a new workspace with the specified configuration.
        Workspace names must be unique and follow naming conventions.
        """
        return await handlers.create_workspace(request)
    
    @router.get("", response_model=None)
    async def list_workspaces(
        scope: Optional[str] = Query(
            None, 
            description="Filter by workspace scope (user, global, system)"
        ),
        status_filter: Optional[str] = Query(
            None, 
            alias="status",
            description="Filter by workspace status (active, inactive, archived)"
        ),
        include_stats: bool = Query(
            True, 
            description="Include workspace statistics"
        ),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Page size")
    ) -> JSONResponse:
        """List workspaces with filtering and pagination.
        
        Returns a paginated list of workspaces with optional filtering
        by scope and status. Includes workspace statistics by default.
        """
        return await handlers.get_workspaces(scope, status_filter, include_stats, page, page_size)
    
    @router.get("/{workspace_name}", response_model=None)
    async def get_workspace(
        workspace_name: str = Path(..., description="Workspace name")
    ) -> JSONResponse:
        """Get workspace details.
        
        Returns detailed information about a specific workspace
        including configuration and statistics.
        """
        return await handlers.get_workspace(workspace_name)
    
    @router.put("/{workspace_name}", response_model=None)
    async def update_workspace(
        workspace_name: str = Path(..., description="Workspace name"),
        request: UpdateWorkspaceRequest = Body(...)
    ) -> JSONResponse:
        """Update workspace configuration.
        
        Updates workspace settings, display name, description,
        or configuration. Partial updates are supported.
        """
        return await handlers.update_workspace(workspace_name, request)
    
    @router.delete("/{workspace_name}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_workspace(
        workspace_name: str = Path(..., description="Workspace name"),
        force: bool = Query(
            False, 
            description="Force deletion even if workspace contains data"
        )
    ) -> JSONResponse:
        """Delete workspace.
        
        Deletes a workspace and all its associated data.
        Use force=true to delete workspaces with existing content.
        """
        return await handlers.delete_workspace(workspace_name, force)
    
    return router


def create_pipeline_router(handlers: Type[PipelineHandlers]) -> APIRouter:
    """Create pipeline-related routes."""
    router = APIRouter(prefix="/pipelines", tags=["Pipelines"])
    
    @router.post("/templates", response_model=None, status_code=status.HTTP_201_CREATED)
    async def create_pipeline_template(request: CreatePipelineTemplateRequest) -> JSONResponse:
        """Create a new pipeline template.
        
        Creates a pipeline template from YAML content.
        Template content is validated before creation.
        """
        return await handlers.create_pipeline_template(request)
    
    @router.get("/templates", response_model=None)
    async def list_pipeline_templates(
        workspace_name: str = Query("default", description="Workspace name"),
        tags: Optional[List[str]] = Query(None, description="Filter by tags"),
        author: Optional[str] = Query(None, description="Filter by author"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Page size")
    ) -> JSONResponse:
        """List pipeline templates with filtering.
        
        Returns a paginated list of pipeline templates with optional
        filtering by tags and author.
        """
        return await handlers.get_pipeline_templates(workspace_name, tags, author, page, page_size)
    
    @router.post("/execute", response_model=None, status_code=status.HTTP_202_ACCEPTED)
    async def execute_pipeline(request: ExecutePipelineRequest) -> JSONResponse:
        """Execute a pipeline.
        
        Starts execution of a pipeline with the provided inputs.
        Returns immediately with run information. Use WebSocket
        for real-time progress updates.
        """
        return await handlers.execute_pipeline(request)
    
    @router.get("/runs", response_model=None)
    async def list_pipeline_runs(
        workspace_name: str = Query("default", description="Workspace name"),
        pipeline_name: Optional[str] = Query(None, description="Filter by pipeline name"),
        status_filter: Optional[str] = Query(
            None, 
            alias="status",
            description="Filter by run status (running, completed, failed)"
        ),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Page size")
    ) -> JSONResponse:
        """List pipeline runs with filtering.
        
        Returns a paginated list of pipeline execution runs
        with optional filtering by pipeline name and status.
        """
        return await handlers.get_pipeline_runs(workspace_name, pipeline_name, status_filter, page, page_size)
    
    @router.get("/runs/{run_id}", response_model=None)
    async def get_pipeline_run(
        run_id: str = Path(..., description="Pipeline run ID"),
        workspace_name: str = Query("default", description="Workspace name")
    ) -> JSONResponse:
        """Get pipeline run details.
        
        Returns detailed information about a specific pipeline run
        including step execution details and outputs.
        """
        return await handlers.get_pipeline_run(run_id, workspace_name)
    
    return router


def create_content_router(handlers: Type[ContentHandlers]) -> APIRouter:
    """Create content-related routes."""
    router = APIRouter(prefix="/content", tags=["Content"])
    
    @router.post("", response_model=None, status_code=status.HTTP_201_CREATED)
    async def create_content(request: CreateContentRequest) -> JSONResponse:
        """Create new content.
        
        Creates content (templates, styles, documents, snippets)
        in the specified workspace.
        """
        return await handlers.create_content(request)
    
    @router.get("", response_model=None)
    async def list_content(
        workspace_name: str = Query("default", description="Workspace name"),
        content_type: Optional[str] = Query(
            None, 
            description="Filter by content type (template, style, document, snippet)"
        ),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Page size")
    ) -> JSONResponse:
        """List content with filtering.
        
        Returns a paginated list of content items with optional
        filtering by content type.
        """
        return await handlers.get_contents(workspace_name, content_type, page, page_size)
    
    return router


def create_health_router(handlers: Type[HealthHandlers]) -> APIRouter:
    """Create health check routes."""
    router = APIRouter(prefix="/health", tags=["Health"])
    
    @router.get("", response_model=None)
    async def health_check() -> JSONResponse:
        """Basic health check.
        
        Returns basic health status and timestamp.
        """
        return await handlers.health_check()
    
    @router.get("/detailed", response_model=None)
    async def detailed_health_check() -> JSONResponse:
        """Detailed health check.
        
        Returns detailed health status including dependency
        availability and system metrics.
        """
        return await handlers.detailed_health_check()
    
    return router


def create_api_router(
    workspace_handlers: Type[WorkspaceHandlers],
    pipeline_handlers: Type[PipelineHandlers],
    content_handlers: Type[ContentHandlers],
    health_handlers: Type[HealthHandlers]
) -> APIRouter:
    """Create main API router with all sub-routers.
    
    Args:
        workspace_handlers: Workspace handler class
        pipeline_handlers: Pipeline handler class
        content_handlers: Content handler class
        health_handlers: Health handler class
    
    Returns:
        Configured API router
    """
    # Create main API router
    api_router = APIRouter()
    
    # Include sub-routers
    api_router.include_router(create_workspace_router(workspace_handlers))
    api_router.include_router(create_pipeline_router(pipeline_handlers))
    api_router.include_router(create_content_router(content_handlers))
    api_router.include_router(create_health_router(health_handlers))
    
    return api_router


# Additional utility routes

def create_utility_router() -> APIRouter:
    """Create utility routes for system operations."""
    router = APIRouter(prefix="/utils", tags=["Utilities"])
    
    @router.get("/version")
    async def get_version():
        """Get API version information."""
        return {
            "api_version": "1.0.0",
            "writeIt_version": "1.0.0",
            "python_version": "3.12+",
            "build_date": "2025-01-15"
        }
    
    @router.get("/config")
    async def get_config():
        """Get public configuration information."""
        return {
            "max_page_size": 100,
            "default_page_size": 50,
            "supported_content_types": ["template", "style", "document", "snippet"],
            "supported_pipeline_types": ["llm_generate", "llm_edit", "user_input", "transformation"],
            "websocket_endpoints": ["/ws/{workspace_name}", "/ws/run/{run_id}"]
        }
    
    return router


# Route tags for documentation organization
ROUTE_TAGS = [
    {
        "name": "Workspaces",
        "description": "Workspace management operations including creation, configuration, and deletion."
    },
    {
        "name": "Pipelines", 
        "description": "Pipeline template management and execution operations."
    },
    {
        "name": "Content",
        "description": "Content management for templates, styles, and documents."
    },
    {
        "name": "Health",
        "description": "Health check and monitoring endpoints."
    },
    {
        "name": "Utilities",
        "description": "Utility endpoints for version and configuration information."
    }
]