"""Modern FastAPI application with DDD infrastructure integration.

Provides a clean, production-ready FastAPI application that integrates
with the domain-driven design architecture and CQRS pattern.
"""

from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, Request, WebSocket, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uvicorn

from ...shared.dependencies.container import Container
from ...shared.events.event_bus import EventBus
from ...shared.errors.base import DomainError
from .context import APIContextMiddleware, APIContextManager
from .error_handler import (
    error_handler, domain_exception_handler, generic_exception_handler,
    http_exception_handler_with_context
)
from .validation import handle_pydantic_validation_error
from .handlers import WorkspaceHandlers, PipelineHandlers, ContentHandlers, HealthHandlers, MigrationEndpoints
from .websocket_handlers import WebSocketManager, WebSocketHandler
from .routes import create_api_router

logger = logging.getLogger(__name__)


class WriteItAPIApplication:
    """WriteIt API Application with DDD integration."""
    
    def __init__(
        self,
        container: Container,
        event_bus: EventBus,
        debug: bool = False,
        cors_origins: list[str] = None,
        trusted_hosts: list[str] = None
    ):
        self.container = container
        self.event_bus = event_bus
        self.debug = debug
        self.cors_origins = cors_origins or ["*"]
        self.trusted_hosts = trusted_hosts or ["*"]
        
        # Create WebSocket manager
        self.websocket_manager = WebSocketManager(event_bus)
        self.websocket_handler = WebSocketHandler(self.websocket_manager)
        
        # Create FastAPI app with lifespan
        self.app = FastAPI(
            title="WriteIt API",
            description="Modern API for WriteIt pipeline execution and management",
            version="1.0.0",
            debug=debug,
            lifespan=self._lifespan
        )
        
        # Set up middleware, routes, and error handlers
        self._setup_middleware()
        self._setup_routes()
        self._setup_error_handlers()
    
    @asynccontextmanager
    async def _lifespan(self, app: FastAPI):
        """Application lifespan manager."""
        # Startup
        logger.info("Starting WriteIt API application")
        
        # Register dependencies in container
        await self._register_dependencies()
        
        # Start background tasks
        await self._start_background_tasks()
        
        yield
        
        # Shutdown
        logger.info("Shutting down WriteIt API application")
        
        # Clean up resources
        await self._cleanup_resources()
    
    def _setup_middleware(self) -> None:
        """Set up middleware stack."""
        # Trusted host middleware (should be first)
        if self.trusted_hosts != ["*"]:
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=self.trusted_hosts
            )
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID"]
        )
        
        # GZip compression
        self.app.add_middleware(GZipMiddleware, minimum_size=500)
        
        # API context middleware (should be last to set context first)
        self.app.add_middleware(
            APIContextMiddleware,
            container=self.container
        )
    
    def _setup_routes(self) -> None:
        """Set up API routes."""
        # Create API router with handlers
        api_router = create_api_router(
            workspace_handlers=WorkspaceHandlers,
            pipeline_handlers=PipelineHandlers,
            content_handlers=ContentHandlers,
            health_handlers=HealthHandlers
        )
        
        # Include API router
        self.app.include_router(api_router, prefix="/api/v1")
        
        # Set up migration endpoints
        self._setup_migration_routes()
        
        # WebSocket endpoints
        self._setup_websocket_routes()
        
        # Root endpoints
        self._setup_root_routes()
    
    def _setup_migration_routes(self) -> None:
        """Set up migration routes."""
        # Create migration endpoints
        migration_endpoints = MigrationEndpoints(self.container)
        
        # Include migration router
        self.app.include_router(migration_endpoints.router)
    
    def _setup_websocket_routes(self) -> None:
        """Set up WebSocket routes."""
        @self.app.websocket("/ws/{workspace_name}")
        async def websocket_endpoint(websocket: WebSocket, workspace_name: str = "default"):
            """WebSocket endpoint for real-time updates."""
            await self.websocket_handler.handle_connection(websocket, workspace_name)
        
        @self.app.websocket("/ws/run/{run_id}")
        async def websocket_run_endpoint(websocket: WebSocket, run_id: str):
            """WebSocket endpoint for specific pipeline run updates."""
            # Connect to default workspace but auto-subscribe to run topic
            connection_id = await self.websocket_manager.connect(websocket, "default")
            
            try:
                # Auto-subscribe to run topic
                self.websocket_manager._subscribe_to_topic(connection_id, f"run:{run_id}")
                
                # Handle connection
                await self.websocket_handler.handle_connection(websocket, "default")
            finally:
                self.websocket_manager.disconnect(connection_id)
    
    def _setup_root_routes(self) -> None:
        """Set up root-level routes."""
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "name": "WriteIt API",
                "version": "1.0.0",
                "description": "Modern API for WriteIt pipeline execution and management",
                "docs": "/docs",
                "health": "/health"
            }
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint."""
            return await HealthHandlers.health_check()
        
        @self.app.get("/health/detailed")
        async def detailed_health():
            """Detailed health check endpoint."""
            return await HealthHandlers.detailed_health_check()
    
    def _setup_error_handlers(self) -> None:
        """Set up error handlers."""
        # Domain errors
        self.app.add_exception_handler(DomainError, domain_exception_handler)
        
        # HTTP errors with context
        self.app.add_exception_handler(StarletteHTTPException, http_exception_handler_with_context)
        
        # Validation errors
        @self.app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            return JSONResponse(
                status_code=422,
                content=handle_pydantic_validation_error(exc).detail
            )
        
        # Generic errors
        self.app.add_exception_handler(Exception, generic_exception_handler)
    
    async def _register_dependencies(self) -> None:
        """Register dependencies in container."""
        # Register core services if not already registered
        if not self.container.is_registered(EventBus):
            self.container.register_instance(EventBus, self.event_bus)
        
        if not self.container.is_registered(WebSocketManager):
            self.container.register_instance(WebSocketManager, self.websocket_manager)
        
        # Register handlers would happen here if using DI for handlers
        # For now, handlers are static methods
    
    async def _start_background_tasks(self) -> None:
        """Start background tasks."""
        # Check for migration requirements on startup
        await self._check_migration_requirements()
        
        # Background tasks would be started here
        # For example: periodic cleanup, health checks, etc.
        pass
    
    async def _check_migration_requirements(self) -> None:
        """Check for migration requirements on server startup."""
        try:
            from ...application.services.migration_application_service import DefaultMigrationApplicationService
            from ...application.commands.migration_commands import AnalyzeMigrationRequirementsCommand
            
            # Get migration service
            migration_service = self.container.get(DefaultMigrationApplicationService)
            
            # Check for migration requirements
            command = AnalyzeMigrationRequirementsCommand(
                workspace_name=None,  # Check active workspace
                include_all_workspaces=False,
                check_data_formats=True,
                check_configurations=True,
                check_cache=True,
            )
            
            required_migrations = await migration_service.analyze_migration_requirements(command)
            
            if required_migrations:
                logger.info(f"Server startup detected {len(required_migrations)} required migrations")
                for migration_type in required_migrations:
                    logger.warning(f"Migration required: {migration_type.value}")
                
                # Log detailed migration info
                logger.info("Use the migration CLI commands to perform required migrations:")
                logger.info("  writeit migration detect     - Detect legacy workspaces")
                logger.info("  writeit migration analyze    - Analyze migration requirements")
                logger.info("  writeit migration migrate    - Start migration operations")
                logger.info("  writeit migration status     - Check migration status")
            else:
                logger.info("No migrations required on server startup")
                
        except Exception as e:
            logger.warning(f"Error checking migration requirements on startup: {e}")
            # Don't fail startup for migration check errors
    
    async def _cleanup_resources(self) -> None:
        """Clean up resources on shutdown."""
        # Cancel WebSocket ping tasks
        if hasattr(self.websocket_manager, '_ping_task') and self.websocket_manager._ping_task:
            self.websocket_manager._ping_task.cancel()
        
        # Close any remaining WebSocket connections
        for connection in list(self.websocket_manager.connections.values()):
            try:
                await connection.websocket.close()
            except Exception:
                pass
        
        self.websocket_manager.connections.clear()
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.app
    
    def run(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        reload: bool = False,
        workers: int = 1,
        **kwargs
    ) -> None:
        """Run the application with uvicorn."""
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            reload=reload,
            workers=workers,
            **kwargs
        )


# Factory function for creating application

def create_app(
    container: Container = None,
    event_bus: EventBus = None,
    debug: bool = False,
    cors_origins: list[str] = None,
    trusted_hosts: list[str] = None
) -> FastAPI:
    """Factory function to create WriteIt API application.
    
    Args:
        container: Dependency injection container
        event_bus: Domain event bus
        debug: Enable debug mode
        cors_origins: Allowed CORS origins
        trusted_hosts: Trusted host names
    
    Returns:
        Configured FastAPI application
    """
    # Create default dependencies if not provided
    if container is None:
        container = Container()
    
    if event_bus is None:
        event_bus = EventBus()
    
    # Create application
    api_app = WriteItAPIApplication(
        container=container,
        event_bus=event_bus,
        debug=debug,
        cors_origins=cors_origins,
        trusted_hosts=trusted_hosts
    )
    
    return api_app.get_app()


# Default application instance (for use with uvicorn command line)
def get_application() -> FastAPI:
    """Get default application instance."""
    return create_app(debug=True)


# For uvicorn command line usage
app = get_application()


if __name__ == "__main__":
    # Create and run application
    container = Container()
    event_bus = EventBus()
    
    api_app = WriteItAPIApplication(
        container=container,
        event_bus=event_bus,
        debug=True
    )
    
    api_app.run(host="127.0.0.1", port=8000, reload=True)