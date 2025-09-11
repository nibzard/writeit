# ABOUTME: FastAPI server for WriteIt pipeline execution
# ABOUTME: Provides REST API and WebSocket endpoints for TUI backend communication

import asyncio
import json
import uuid
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from writeit.pipeline import PipelineExecutor, ExecutionContext, StepResult
from writeit.models import Pipeline, PipelineRun, PipelineStatus, StepStatus
from writeit.workspace.workspace import Workspace
from writeit.storage.manager import StorageManager
from writeit.errors import PipelineError, StepExecutionError, ValidationError


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
                except:
                    disconnected.append(connection_id)
        
        # Clean up disconnected connections
        for connection_id in disconnected:
            self.disconnect(connection_id)


# Global instances
app = FastAPI(
    title="WriteIt Pipeline API",
    description="REST API and WebSocket endpoints for WriteIt pipeline execution",
    version="0.1.0"
)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
websocket_manager = WebSocketManager()
executors: Dict[str, PipelineExecutor] = {}  # workspace_name -> executor
pipelines: Dict[str, Pipeline] = {}  # pipeline_id -> pipeline


def get_executor(workspace_name: str = "default") -> PipelineExecutor:
    """Get or create a pipeline executor for the workspace."""
    if workspace_name not in executors:
        workspace = Workspace()
        storage = StorageManager(workspace, workspace_name)
        executors[workspace_name] = PipelineExecutor(workspace, storage, workspace_name)
    return executors[workspace_name]


# REST API Endpoints

@app.post("/api/pipelines", response_model=PipelineResponse)
async def create_pipeline(request: CreatePipelineRequest):
    """Load and register a pipeline from a file."""
    try:
        executor = get_executor(request.workspace_name)
        pipeline = await executor.load_pipeline(Path(request.pipeline_path))
        
        # Store pipeline
        pipelines[pipeline.id] = pipeline
        
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
                    "ui": step.ui
                }
                for step in pipeline.steps
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/pipelines/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: str):
    """Get pipeline configuration."""
    if pipeline_id not in pipelines:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    pipeline = pipelines[pipeline_id]
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
                "ui": step.ui
            }
            for step in pipeline.steps
        ]
    )


@app.post("/api/runs", response_model=PipelineRunResponse)
async def create_run(request: RunPipelineRequest):
    """Create a new pipeline run."""
    try:
        if request.pipeline_id not in pipelines:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        pipeline = pipelines[request.pipeline_id]
        executor = get_executor(request.workspace_name)
        
        run_id = await executor.create_run(
            pipeline, 
            request.inputs, 
            request.workspace_name
        )
        
        run = await executor.get_run(run_id)
        if not run:
            raise HTTPException(status_code=500, detail="Failed to create run")
        
        return _run_to_response(run)
        
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/runs/{run_id}/execute")
async def execute_run(run_id: str, workspace_name: str = "default"):
    """Execute a pipeline run."""
    try:
        executor = get_executor(workspace_name)
        run = await executor.get_run(run_id)
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        if run.pipeline_id not in pipelines:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        pipeline = pipelines[run.pipeline_id]
        
        # Define progress callback for WebSocket updates
        async def progress_callback(event_type: str, data: Dict[str, Any]):
            await websocket_manager.broadcast_to_run(run_id, {
                "type": "progress",
                "event": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Define response callback for streaming responses
        async def response_callback(response_type: str, content: str):
            await websocket_manager.broadcast_to_run(run_id, {
                "type": "response",
                "response_type": response_type,
                "content": content,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        # Execute the run
        completed_run = await executor.execute_run(
            run_id,
            pipeline,
            progress_callback,
            response_callback
        )
        
        # Send completion notification
        await websocket_manager.broadcast_to_run(run_id, {
            "type": "completed",
            "run": _run_to_dict(completed_run),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return _run_to_response(completed_run)
        
    except Exception as e:
        # Send error notification
        await websocket_manager.broadcast_to_run(run_id, {
            "type": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/runs/{run_id}", response_model=PipelineRunResponse)
async def get_run(run_id: str, workspace_name: str = "default"):
    """Get pipeline run status."""
    executor = get_executor(workspace_name)
    run = await executor.get_run(run_id)
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return _run_to_response(run)


@app.get("/api/workspaces/{workspace_name}/runs", response_model=List[PipelineRunResponse])
async def list_runs(workspace_name: str = "default", limit: int = 50):
    """List pipeline runs for a workspace."""
    executor = get_executor(workspace_name)
    # TODO: Implement run listing in executor
    return []


# WebSocket endpoint
@app.websocket("/ws/{run_id}")
async def websocket_endpoint(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for real-time pipeline execution updates."""
    connection_id = str(uuid.uuid4())
    
    try:
        await websocket_manager.connect(websocket, connection_id)
        websocket_manager.subscribe_to_run(connection_id, run_id)
        
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "connection_id": connection_id,
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                # Handle incoming messages (e.g., user selections, feedback)
                await _handle_websocket_message(run_id, data)
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(connection_id)
    except Exception as e:
        websocket_manager.disconnect(connection_id)


async def _handle_websocket_message(run_id: str, message: Dict[str, Any]):
    """Handle incoming WebSocket messages."""
    message_type = message.get("type")
    
    if message_type == "user_selection":
        # Handle user selection for step responses
        step_key = message.get("step_key")
        selected_response = message.get("selected_response")
        # TODO: Update step execution with user selection
        
    elif message_type == "user_feedback":
        # Handle user feedback
        step_key = message.get("step_key")
        feedback = message.get("feedback", "")
        # TODO: Update step execution with user feedback
        
    elif message_type == "pause_run":
        # Handle run pause request
        # TODO: Implement run pausing
        pass
        
    elif message_type == "resume_run":
        # Handle run resume request
        # TODO: Implement run resuming
        pass


def _run_to_response(run: PipelineRun) -> PipelineRunResponse:
    """Convert PipelineRun to response model."""
    return PipelineRunResponse(
        id=run.id,
        pipeline_id=run.pipeline_id,
        status=run.status.value if isinstance(run.status, PipelineStatus) else run.status,
        inputs=run.inputs,
        outputs=run.outputs,
        created_at=run.created_at.isoformat() if run.created_at else None,
        started_at=run.started_at.isoformat() if run.started_at else None,
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        error=run.error,
        steps=[
            {
                "step_key": step.step_key,
                "status": step.status.value if isinstance(step.status, StepStatus) else step.status,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                "responses": step.responses,
                "selected_response": step.selected_response,
                "user_feedback": step.user_feedback,
                "tokens_used": step.tokens_used,
                "execution_time": step.execution_time,
                "error": step.error
            }
            for step in run.steps
        ]
    )


def _run_to_dict(run: PipelineRun) -> Dict[str, Any]:
    """Convert PipelineRun to dictionary for JSON serialization."""
    return {
        "id": run.id,
        "pipeline_id": run.pipeline_id,
        "status": run.status.value if isinstance(run.status, PipelineStatus) else run.status,
        "inputs": run.inputs,
        "outputs": run.outputs,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "error": run.error,
        "steps": [
            {
                "step_key": step.step_key,
                "status": step.status.value if isinstance(step.status, StepStatus) else step.status,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                "responses": step.responses,
                "selected_response": step.selected_response,
                "user_feedback": step.user_feedback,
                "tokens_used": step.tokens_used,
                "execution_time": step.execution_time,
                "error": step.error
            }
            for step in run.steps
        ]
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


if __name__ == "__main__":
    uvicorn.run(
        "writeit.server.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )