# ABOUTME: Legacy FastAPI server compatibility layer
# ABOUTME: Provides backward compatibility while transitioning to modern infrastructure

import warnings
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, UTC

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Modern infrastructure imports
from ..infrastructure.web.app import create_app
from ..shared.dependencies.container import Container
from ..shared.events.bus import EventBus

# Legacy imports for compatibility
from writeit.pipeline import PipelineExecutor
from writeit.models import Pipeline, PipelineRun, PipelineStatus, StepStatus
from writeit.workspace.workspace import Workspace
from writeit.storage.adapter import create_storage_adapter
from writeit.shared.errors import ValidationError


# Request/Response Models
class CreatePipelineRequest(BaseModel):
    pipeline_path: str
    workspace_name: str = "default"


class RunPipelineRequest(BaseModel):
    pipeline_id: str
    inputs: Dict[str, Any]
    workspace_name: str = "default"


class PipelineResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    metadata: Dict[str, Any]
    inputs: Dict[str, Dict[str, Any]]
    steps: List[Dict[str, Any]]


class PipelineRunResponse(BaseModel):
    id: str
    pipeline_id: str
    status: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    error: Optional[str]
    steps: List[Dict[str, Any]]


class WebSocketManager:
    """Manages WebSocket connections for real-time pipeline updates."""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.run_connections: Dict[str, List[str]] = {}  # run_id -> [connection_ids]

    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept and store a WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]

        # Remove from run connections
        for run_id, connections in self.run_connections.items():
            if connection_id in connections:
                connections.remove(connection_id)

    def subscribe_to_run(self, connection_id: str, run_id: str):
        """Subscribe a connection to pipeline run updates."""
        if run_id not in self.run_connections:
            self.run_connections[run_id] = []
        if connection_id not in self.run_connections[run_id]:
            self.run_connections[run_id].append(connection_id)

    async def broadcast_to_run(self, run_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections subscribed to a run."""
        if run_id not in self.run_connections:
            return

        disconnected = []
        for connection_id in self.run_connections[run_id]:
            if connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.append(connection_id)

        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)


# Deprecation warning for legacy server
warnings.warn(
    "The legacy server (writeit.server.app) is deprecated. "
    "Use the modern infrastructure (writeit.infrastructure.web.app) instead.",
    DeprecationWarning,
    stacklevel=2
)

# Create modern app instance
_modern_app = None

def get_modern_app() -> FastAPI:
    """Get or create the modern FastAPI application."""
    global _modern_app
    if _modern_app is None:
        container = Container()
        event_bus = EventBus()
        _modern_app = create_app(
            container=container,
            event_bus=event_bus,
            debug=True,
            cors_origins=["*"]
        )
    return _modern_app

# For backward compatibility, expose the modern app as 'app'
app = get_modern_app()

# Legacy compatibility layer - these endpoints are deprecated
# All functionality has been migrated to the modern infrastructure

# Global state for legacy compatibility
legacy_executors: Dict[str, PipelineExecutor] = {}  # workspace_name -> executor
legacy_pipelines: Dict[str, Pipeline] = {}  # pipeline_id -> pipeline


def get_legacy_executor(workspace_name: str = "default") -> PipelineExecutor:
    """Get or create a pipeline executor for the workspace (legacy)."""
    warnings.warn(
        "get_legacy_executor is deprecated. Use the modern infrastructure instead.",
        DeprecationWarning,
        stacklevel=2
    )
    if workspace_name not in legacy_executors:
        workspace = Workspace()
        storage = StorageManager(workspace, workspace_name)
        legacy_executors[workspace_name] = PipelineExecutor(workspace, storage, workspace_name)
    return legacy_executors[workspace_name]


# Legacy REST API Endpoints (deprecated)
# These endpoints are maintained for backward compatibility
# New development should use the modern API at /api/v1/*

@app.post("/api/legacy/pipelines", response_model=PipelineResponse, deprecated=True)
async def legacy_create_pipeline(request: CreatePipelineRequest):
    """Load and register a pipeline from a file."""
    """Create pipeline (legacy endpoint - deprecated).
    
    This endpoint is deprecated. Use POST /api/v1/pipelines/templates instead.
    """
    warnings.warn(
        "Legacy pipeline creation endpoint is deprecated. Use /api/v1/pipelines/templates",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        executor = get_legacy_executor(request.workspace_name)
        pipeline = await executor.load_pipeline(Path(request.pipeline_path))

        # Store pipeline
        legacy_pipelines[pipeline.id] = pipeline

        return PipelineResponse(
            id=pipeline.id,
            name=pipeline.name,
            description=pipeline.description,
            version=pipeline.version,
            metadata=pipeline.metadata,
            inputs=pipeline.inputs,
            steps=[
                {
                    "key": step.key,
                    "name": step.name,
                    "description": step.description,
                    "type": step.type,
                    "model_preference": step.model_preference,
                    "validation": step.validation,
                    "ui": step.ui,
                }
                for step in pipeline.steps
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/legacy/pipelines/{pipeline_id}", response_model=PipelineResponse, deprecated=True)
async def legacy_get_pipeline(pipeline_id: str):
    """Get pipeline configuration (legacy endpoint - deprecated).
    
    This endpoint is deprecated. Use GET /api/v1/pipelines/templates instead.
    """
    warnings.warn(
        "Legacy get pipeline endpoint is deprecated. Use /api/v1/pipelines/templates",
        DeprecationWarning,
        stacklevel=2
    )
    if pipeline_id not in legacy_pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline = legacy_pipelines[pipeline_id]
    return PipelineResponse(
        id=pipeline.id,
        name=pipeline.name,
        description=pipeline.description,
        version=pipeline.version,
        metadata=pipeline.metadata,
        inputs=pipeline.inputs,
        steps=[
            {
                "key": step.key,
                "name": step.name,
                "description": step.description,
                "type": step.type,
                "model_preference": step.model_preference,
                "validation": step.validation,
                "ui": step.ui,
            }
            for step in pipeline.steps
        ],
    )


@app.post("/api/legacy/runs", response_model=PipelineRunResponse, deprecated=True)
async def legacy_create_run(request: RunPipelineRequest):
    """Create a new pipeline run (legacy endpoint - deprecated).
    
    This endpoint is deprecated. Use POST /api/v1/pipelines/execute instead.
    """
    warnings.warn(
        "Legacy create run endpoint is deprecated. Use /api/v1/pipelines/execute",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        if request.pipeline_id not in legacy_pipelines:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        pipeline = legacy_pipelines[request.pipeline_id]
        executor = get_legacy_executor(request.workspace_name)

        run_id = await executor.create_run(
            pipeline, request.inputs, request.workspace_name
        )

        run = await executor.get_run(run_id)
        if not run:
            raise HTTPException(status_code=500, detail="Failed to create run")

        return _run_to_response(run)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/legacy/runs/{run_id}/execute", deprecated=True)
async def legacy_execute_run(run_id: str, workspace_name: str = "default"):
    """Execute a pipeline run (legacy endpoint - deprecated).
    
    This endpoint is deprecated. Use POST /api/v1/pipelines/execute instead.
    """
    warnings.warn(
        "Legacy execute run endpoint is deprecated. Use /api/v1/pipelines/execute",
        DeprecationWarning,
        stacklevel=2
    )
    try:
        executor = get_legacy_executor(workspace_name)
        run = await executor.get_run(run_id)

        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        if run.pipeline_id not in legacy_pipelines:
            raise HTTPException(status_code=404, detail="Pipeline not found")

        pipeline = legacy_pipelines[run.pipeline_id]

        # Legacy WebSocket callbacks (simplified for compatibility)
        async def progress_callback(event_type: str, data: Dict[str, Any]):
            # Legacy callback - no WebSocket support in compatibility mode
            pass

        async def response_callback(response_type: str, content: str):
            # Legacy callback - no WebSocket support in compatibility mode
            pass

        # Execute the run
        completed_run = await executor.execute_run(
            run_id, pipeline, progress_callback, response_callback
        )

        # Legacy completion notification (no-op in compatibility mode)
        pass

        return _run_to_response(completed_run)

    except Exception as e:
        # Legacy error notification (no-op in compatibility mode)
        pass
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/legacy/runs/{run_id}", response_model=PipelineRunResponse, deprecated=True)
async def legacy_get_run(run_id: str, workspace_name: str = "default"):
    """Get pipeline run status (legacy endpoint - deprecated).
    
    This endpoint is deprecated. Use GET /api/v1/pipelines/runs/{run_id} instead.
    """
    warnings.warn(
        "Legacy get run endpoint is deprecated. Use /api/v1/pipelines/runs/{run_id}",
        DeprecationWarning,
        stacklevel=2
    )
    executor = get_legacy_executor(workspace_name)
    run = await executor.get_run(run_id)

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return _run_to_response(run)


@app.get(
    "/api/legacy/workspaces/{workspace_name}/runs", response_model=List[PipelineRunResponse], deprecated=True
)
async def legacy_list_runs(workspace_name: str = "default", limit: int = 50):
    """List pipeline runs for a workspace (legacy endpoint - deprecated).
    
    This endpoint is deprecated. Use GET /api/v1/pipelines/runs instead.
    """
    warnings.warn(
        "Legacy list runs endpoint is deprecated. Use /api/v1/pipelines/runs",
        DeprecationWarning,
        stacklevel=2
    )
    get_legacy_executor(workspace_name)
    # Legacy implementation - returns empty list
    return []


# Legacy WebSocket endpoint (deprecated)
@app.websocket("/ws/legacy/{run_id}")
async def legacy_websocket_endpoint(websocket: WebSocket, run_id: str):
    """Legacy WebSocket endpoint (deprecated).
    
    This endpoint is deprecated. Use /ws/{workspace_name} or /ws/run/{run_id} instead.
    """
    try:
        await websocket.accept()
        
        # Send deprecation warning
        await websocket.send_json({
            "type": "deprecated",
            "message": "This WebSocket endpoint is deprecated. Use /ws/{workspace_name} or /ws/run/{run_id} instead.",
            "timestamp": datetime.now(UTC).isoformat(),
        })
        
        # Keep connection open briefly then close
        await websocket.close(code=1000, reason="Endpoint deprecated")
        
    except WebSocketDisconnect:
        pass
    except Exception:
        pass


async def _handle_legacy_websocket_message(run_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages (legacy - deprecated)."""
    # Legacy handler - no-op for compatibility
    pass


def _run_to_response(run: PipelineRun) -> PipelineRunResponse:
    """Convert PipelineRun to response model."""
    return PipelineRunResponse(
        id=run.id,
        pipeline_id=run.pipeline_id,
        status=run.status.value
        if isinstance(run.status, PipelineStatus)
        else run.status,
        inputs=run.inputs,
        outputs=run.outputs,
        created_at=run.created_at.isoformat() if run.created_at else None,
        started_at=run.started_at.isoformat() if run.started_at else None,
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        error=run.error,
        steps=[
            {
                "step_key": step.step_key,
                "status": step.status.value
                if isinstance(step.status, StepStatus)
                else step.status,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat()
                if step.completed_at
                else None,
                "responses": step.responses,
                "selected_response": step.selected_response,
                "user_feedback": step.user_feedback,
                "tokens_used": step.tokens_used,
                "execution_time": step.execution_time,
                "error": step.error,
            }
            for step in run.steps
        ],
    )


def _run_to_dict(run: PipelineRun) -> Dict[str, Any]:
    """Convert PipelineRun to dictionary for JSON serialization."""
    return {
        "id": run.id,
        "pipeline_id": run.pipeline_id,
        "status": run.status.value
        if isinstance(run.status, PipelineStatus)
        else run.status,
        "inputs": run.inputs,
        "outputs": run.outputs,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error": run.error,
        "steps": [
            {
                "step_key": step.step_key,
                "status": step.status.value
                if isinstance(step.status, StepStatus)
                else step.status,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat()
                if step.completed_at
                else None,
                "responses": step.responses,
                "selected_response": step.selected_response,
                "user_feedback": step.user_feedback,
                "tokens_used": step.tokens_used,
                "execution_time": step.execution_time,
                "error": step.error,
            }
            for step in run.steps
        ],
    }


# Legacy health check endpoint (superseded by modern health endpoints)
@app.get("/legacy/health", deprecated=True)
async def legacy_health_check():
    """Legacy health check endpoint (deprecated).
    
    This endpoint is deprecated. Use /health or /api/v1/health instead.
    """
    warnings.warn(
        "Legacy health endpoint is deprecated. Use /health or /api/v1/health",
        DeprecationWarning,
        stacklevel=2
    )
    return {
        "status": "healthy", 
        "timestamp": datetime.now(UTC).isoformat(),
        "deprecated": True,
        "use_instead": "/health or /api/v1/health"
    }

# Redirect root health check to modern implementation
@app.get("/health")
async def health_check():
    """Health check endpoint (redirects to modern implementation)."""
    # This will be handled by the modern app's health endpoint
    from ..infrastructure.web.handlers import HealthHandlers
    return await HealthHandlers.health_check()


# Legacy compatibility notice
def print_migration_notice():
    """Print migration notice for legacy server usage."""
    print("\n" + "=" * 80)
    print("NOTICE: Legacy Server Compatibility Mode")
    print("=" * 80)
    print("You are using the legacy server compatibility layer.")
    print("Consider migrating to the modern infrastructure:")
    print("")
    print("  Modern server: python -m writeit.infrastructure.web.app")
    print("  Modern API:    /api/v1/* endpoints")
    print("  Legacy API:    /api/legacy/* endpoints (deprecated)")
    print("")
    print("The legacy endpoints will be removed in a future version.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    print_migration_notice()
    
    # Use the modern app for execution
    modern_app = get_modern_app()
    
    uvicorn.run(
        modern_app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
