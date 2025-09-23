"""REST Endpoint Handlers using CQRS pattern.

Provides HTTP endpoint handlers that integrate with CQRS commands/queries
while maintaining proper separation between web layer and application layer.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, AsyncGenerator
import uuid
import asyncio
from datetime import datetime

from fastapi import HTTPException, status, Depends, Query, Path, Body
from fastapi.responses import JSONResponse

from ...application.commands.workspace_commands import (
    CreateWorkspaceCommand, UpdateWorkspaceCommand, DeleteWorkspaceCommand
)
from ...application.commands.pipeline_commands import (
    CreatePipelineTemplateCommand, UpdatePipelineTemplateCommand, 
    DeletePipelineTemplateCommand, ExecutePipelineCommand,
    ValidatePipelineTemplateCommand, PublishPipelineTemplateCommand
)
from ...application.commands.content_commands import (
    CreateContentCommand, UpdateContentCommand, DeleteContentCommand
)
from ...application.queries.workspace_queries import (
    GetWorkspacesQuery, GetWorkspaceQuery, GetWorkspaceConfigurationQuery
)
from ...application.queries.pipeline_queries import (
    GetPipelineTemplatesQuery, GetPipelineTemplateQuery, GetPipelineRunsQuery,
    GetPipelineRunQuery, SearchPipelineTemplatesQuery
)
from ...application.queries.content_queries import (
    GetContentQuery, GetContentsQuery, SearchContentQuery
)
from ...shared.dependencies.container import Container
from ...shared.command import CommandResult
from ...shared.query import QueryResult
from .context import APIContextManager, get_current_context, get_current_container
from .validation import (
    CreateWorkspaceRequest, UpdateWorkspaceRequest,
    CreatePipelineTemplateRequest, UpdatePipelineTemplateRequest,
    ExecutePipelineRequest, CreateContentRequest,
    api_validator
)
from .response_mapper import response_mapper
from .error_handler import error_handler


class WorkspaceHandlers:
    """HTTP handlers for workspace operations."""
    
    @staticmethod
    async def create_workspace(request: CreateWorkspaceRequest) -> JSONResponse:
        """Create a new workspace."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Validate request
        api_validator.validate_and_raise('workspace', request.dict())
        
        # Create command
        command = CreateWorkspaceCommand(
            name=request.name,
            display_name=request.display_name,
            description=request.description,
            configuration=request.configuration or {}
        )
        
        try:
            # Get command handler and execute
            handler = await container.aresolve(CreateWorkspaceCommand.__class__)
            result = await handler.handle(command)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_type": "workspace_creation_failed",
                        "message": "Failed to create workspace",
                        "errors": result.errors,
                        "warnings": result.warnings
                    }
                )
            
            # Map result to DTO
            workspace_dto = response_mapper.to_dto(result.workspace)
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response_mapper.create_success_response(
                    workspace_dto,
                    "Workspace created successfully"
                )
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc
    
    @staticmethod
    async def get_workspaces(
        scope: Optional[str] = Query(None),
        status_filter: Optional[str] = Query(None, alias="status"),
        include_stats: bool = Query(True),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100)
    ) -> JSONResponse:
        """Get list of workspaces."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Create query
        query = GetWorkspacesQuery(
            scope=scope,
            status=status_filter,
            include_stats=include_stats,
            page=page,
            page_size=page_size
        )
        
        try:
            # Get query handler and execute
            handler = await container.aresolve(GetWorkspacesQuery.__class__)
            result = await handler.handle(query)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to retrieve workspaces"
                )
            
            # Map results to DTOs
            workspace_dtos = response_mapper.to_dto_list(result.workspaces)
            
            # Create paginated response
            paginated_response = response_mapper.create_pagination_response(
                items=workspace_dtos,
                total=result.total_count,
                page=page,
                page_size=page_size
            )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=paginated_response
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc
    
    @staticmethod
    async def get_workspace(workspace_name: str = Path(...)) -> JSONResponse:
        """Get specific workspace."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Create query
        query = GetWorkspaceQuery(workspace_name=workspace_name)
        
        try:
            # Get query handler and execute
            handler = await container.aresolve(GetWorkspaceQuery.__class__)
            result = await handler.handle(query)
            
            if not result.success or not result.workspace:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Workspace '{workspace_name}' not found"
                )
            
            # Map result to DTO
            workspace_dto = response_mapper.to_dto(result.workspace)
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_mapper.create_success_response(workspace_dto)
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc
    
    @staticmethod
    async def update_workspace(
        workspace_name: str = Path(...),
        request: UpdateWorkspaceRequest = Body(...)
    ) -> JSONResponse:
        """Update workspace."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Create command
        command = UpdateWorkspaceCommand(
            workspace_name=workspace_name,
            display_name=request.display_name,
            description=request.description,
            configuration=request.configuration
        )
        
        try:
            # Get command handler and execute
            handler = await container.aresolve(UpdateWorkspaceCommand.__class__)
            result = await handler.handle(command)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_type": "workspace_update_failed",
                        "message": "Failed to update workspace",
                        "errors": result.errors
                    }
                )
            
            # Map result to DTO
            workspace_dto = response_mapper.to_dto(result.workspace)
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_mapper.create_success_response(
                    workspace_dto,
                    "Workspace updated successfully"
                )
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc
    
    @staticmethod
    async def delete_workspace(
        workspace_name: str = Path(...),
        force: bool = Query(False)
    ) -> JSONResponse:
        """Delete workspace."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Create command
        command = DeleteWorkspaceCommand(
            workspace_name=workspace_name,
            force=force
        )
        
        try:
            # Get command handler and execute
            handler = await container.aresolve(DeleteWorkspaceCommand.__class__)
            result = await handler.handle(command)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_type": "workspace_deletion_failed",
                        "message": "Failed to delete workspace",
                        "errors": result.errors
                    }
                )
            
            return JSONResponse(
                status_code=status.HTTP_204_NO_CONTENT,
                content=None
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc


class PipelineHandlers:
    """HTTP handlers for pipeline operations."""
    
    @staticmethod
    async def create_pipeline_template(request: CreatePipelineTemplateRequest) -> JSONResponse:
        """Create a new pipeline template."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Validate request
        api_validator.validate_and_raise('pipeline', request.dict())
        
        # Create command
        command = CreatePipelineTemplateCommand(
            name=request.name,
            description=request.description,
            content=request.content,
            version=request.version,
            author=request.author,
            tags=request.tags or [],
            workspace_name=request.workspace_name
        )
        
        try:
            # Get command handler and execute
            handler = await container.aresolve(CreatePipelineTemplateCommand.__class__)
            result = await handler.handle(command)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_type": "pipeline_creation_failed",
                        "message": "Failed to create pipeline template",
                        "errors": result.errors,
                        "validation_errors": result.validation_errors
                    }
                )
            
            # Map result to DTO
            pipeline_dto = response_mapper.to_dto(result.template)
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response_mapper.create_success_response(
                    pipeline_dto,
                    "Pipeline template created successfully"
                )
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc
    
    @staticmethod
    async def get_pipeline_templates(
        workspace_name: str = Query("default"),
        tags: Optional[List[str]] = Query(None),
        author: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100)
    ) -> JSONResponse:
        """Get list of pipeline templates."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Create query
        query = GetPipelineTemplatesQuery(
            workspace_name=workspace_name,
            tags=tags,
            author=author,
            page=page,
            page_size=page_size
        )
        
        try:
            # Get query handler and execute
            handler = await container.aresolve(GetPipelineTemplatesQuery.__class__)
            result = await handler.handle(query)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to retrieve pipeline templates"
                )
            
            # Map results to DTOs
            template_dtos = response_mapper.to_dto_list(result.templates)
            
            # Create paginated response
            paginated_response = response_mapper.create_pagination_response(
                items=template_dtos,
                total=result.total_count,
                page=page,
                page_size=page_size
            )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=paginated_response
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc
    
    @staticmethod
    async def execute_pipeline(request: ExecutePipelineRequest) -> JSONResponse:
        """Execute a pipeline."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Create command
        command = ExecutePipelineCommand(
            pipeline_name=request.pipeline_name,
            workspace_name=request.workspace_name or "default",
            inputs=request.inputs or {},
            execution_options=request.execution_options or {}
        )
        
        try:
            # Get command handler and execute
            handler = await container.aresolve(ExecutePipelineCommand.__class__)
            result = await handler.handle(command)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_type": "pipeline_execution_failed",
                        "message": "Failed to execute pipeline",
                        "errors": result.errors
                    }
                )
            
            # Map result to DTO
            run_dto = response_mapper.to_dto(result.pipeline_run)
            
            return JSONResponse(
                status_code=status.HTTP_202_ACCEPTED,
                content=response_mapper.create_success_response(
                    run_dto,
                    "Pipeline execution started"
                )
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc
    
    @staticmethod
    async def get_pipeline_runs(
        workspace_name: str = Query("default"),
        pipeline_name: Optional[str] = Query(None),
        status_filter: Optional[str] = Query(None, alias="status"),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100)
    ) -> JSONResponse:
        """Get list of pipeline runs."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Create query
        query = GetPipelineRunsQuery(
            workspace_name=workspace_name,
            pipeline_name=pipeline_name,
            status=status_filter,
            page=page,
            page_size=page_size
        )
        
        try:
            # Get query handler and execute
            handler = await container.aresolve(GetPipelineRunsQuery.__class__)
            result = await handler.handle(query)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to retrieve pipeline runs"
                )
            
            # Map results to DTOs
            run_dtos = response_mapper.to_dto_list(result.runs)
            
            # Create paginated response
            paginated_response = response_mapper.create_pagination_response(
                items=run_dtos,
                total=result.total_count,
                page=page,
                page_size=page_size
            )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=paginated_response
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc
    
    @staticmethod
    async def get_pipeline_run(
        run_id: str = Path(...),
        workspace_name: str = Query("default")
    ) -> JSONResponse:
        """Get specific pipeline run."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Create query
        query = GetPipelineRunQuery(
            run_id=run_id,
            workspace_name=workspace_name
        )
        
        try:
            # Get query handler and execute
            handler = await container.aresolve(GetPipelineRunQuery.__class__)
            result = await handler.handle(query)
            
            if not result.success or not result.run:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Pipeline run '{run_id}' not found"
                )
            
            # Map result to DTO
            run_dto = response_mapper.to_dto(result.run)
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=response_mapper.create_success_response(run_dto)
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc


class ContentHandlers:
    """HTTP handlers for content operations."""
    
    @staticmethod
    async def create_content(request: CreateContentRequest) -> JSONResponse:
        """Create new content."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Validate request
        api_validator.validate_and_raise('content', request.dict())
        
        # Create command
        command = CreateContentCommand(
            name=request.name,
            content_type=request.content_type,
            content=request.content,
            metadata=request.metadata or {},
            workspace_name=request.workspace_name
        )
        
        try:
            # Get command handler and execute
            handler = await container.aresolve(CreateContentCommand.__class__)
            result = await handler.handle(command)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_type": "content_creation_failed",
                        "message": "Failed to create content",
                        "errors": result.errors
                    }
                )
            
            # Map result to DTO
            content_dto = response_mapper.to_dto(result.content)
            
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=response_mapper.create_success_response(
                    content_dto,
                    "Content created successfully"
                )
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc
    
    @staticmethod
    async def get_contents(
        workspace_name: str = Query("default"),
        content_type: Optional[str] = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(50, ge=1, le=100)
    ) -> JSONResponse:
        """Get list of contents."""
        container = get_current_container()
        if not container:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Dependency injection container not available"
            )
        
        # Create query
        query = GetContentsQuery(
            workspace_name=workspace_name,
            content_type=content_type,
            page=page,
            page_size=page_size
        )
        
        try:
            # Get query handler and execute
            handler = await container.aresolve(GetContentsQuery.__class__)
            result = await handler.handle(query)
            
            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to retrieve contents"
                )
            
            # Map results to DTOs
            content_dtos = response_mapper.to_dto_list(result.contents)
            
            # Create paginated response
            paginated_response = response_mapper.create_pagination_response(
                items=content_dtos,
                total=result.total_count,
                page=page,
                page_size=page_size
            )
            
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=paginated_response
            )
        
        except Exception as exc:
            error_response = error_handler.create_error_response(exc)
            http_exc = error_handler.to_http_exception(error_response)
            raise http_exc


class HealthHandlers:
    """HTTP handlers for health and monitoring."""
    
    @staticmethod
    async def health_check() -> JSONResponse:
        """Basic health check endpoint."""
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
        )
    
    @staticmethod
    async def detailed_health_check() -> JSONResponse:
        """Detailed health check with dependency status."""
        container = get_current_container()
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "dependencies": {
                "container": container is not None,
                "database": True,  # Would check actual database connectivity
                "llm_services": True  # Would check LLM service availability
            }
        }
        
        # Determine overall status
        if not all(health_status["dependencies"].values()):
            health_status["status"] = "degraded"
        
        status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE
        
        return JSONResponse(
            status_code=status_code,
            content=health_status
        )