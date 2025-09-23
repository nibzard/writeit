"""WebSocket Handlers with domain events integration.

Provides real-time WebSocket communication for pipeline execution,
progress updates, and user interaction using domain events.
"""

from __future__ import annotations
import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Callable, AsyncGenerator
from enum import Enum
from contextlib import asynccontextmanager

from fastapi import WebSocket, WebSocketDisconnect, status
from websockets.exceptions import ConnectionClosed

from ...shared.events.bus import EventBus, DomainEvent
from ...domains.execution.events import (
    PipelineExecutionStarted, PipelineExecutionCompleted, PipelineExecutionFailed,
    StepExecutionStarted, StepExecutionCompleted, StepExecutionFailed,
    PipelineExecutionProgress
)
from ...domains.pipeline.events import (
    PipelineTemplateCreated, PipelineTemplateUpdated, PipelineTemplateDeleted
)
from ...domains.workspace.events import (
    WorkspaceCreated, WorkspaceUpdated, WorkspaceDeleted
)
from .context import APIContextManager, get_current_context


class WebSocketMessageType(str, Enum):
    """WebSocket message types."""
    # Connection management
    CONNECTION_ACK = "connection_ack"
    PING = "ping"
    PONG = "pong"
    
    # Subscription management
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SUBSCRIPTION_ACK = "subscription_ack"
    
    # Pipeline execution
    EXECUTION_STARTED = "execution_started"
    EXECUTION_PROGRESS = "execution_progress"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    
    # Step execution
    STEP_STARTED = "step_started"
    STEP_PROGRESS = "step_progress"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_USER_INPUT_REQUIRED = "step_user_input_required"
    
    # User interactions
    USER_SELECTION = "user_selection"
    USER_FEEDBACK = "user_feedback"
    USER_INPUT = "user_input"
    
    # Template/workspace events
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DELETED = "template_deleted"
    WORKSPACE_UPDATED = "workspace_updated"
    
    # Errors
    ERROR = "error"
    VALIDATION_ERROR = "validation_error"


@dataclass
class WebSocketMessage:
    """WebSocket message structure."""
    type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type,
            "payload": self.payload,
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WebSocketMessage:
        """Create from dictionary."""
        return cls(
            type=data.get("type", ""),
            payload=data.get("payload", {}),
            id=data.get("id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None
        )


@dataclass
class WebSocketConnection:
    """WebSocket connection wrapper."""
    websocket: WebSocket
    connection_id: str
    workspace_name: str
    user_id: Optional[str] = None
    subscriptions: Set[str] = field(default_factory=set)
    last_ping: Optional[datetime] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    async def send_message(self, message: WebSocketMessage) -> None:
        """Send message to WebSocket."""
        try:
            await self.websocket.send_text(json.dumps(message.to_dict()))
        except (ConnectionClosed, WebSocketDisconnect):
            # Connection is closed, handle gracefully
            pass
    
    async def send_error(self, error_type: str, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Send error message."""
        error_message = WebSocketMessage(
            type=WebSocketMessageType.ERROR,
            payload={
                "error_type": error_type,
                "message": message,
                "details": details or {}
            }
        )
        await self.send_message(error_message)
    
    def subscribe(self, topic: str) -> None:
        """Subscribe to topic."""
        self.subscriptions.add(topic)
    
    def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from topic."""
        self.subscriptions.discard(topic)
    
    def is_subscribed(self, topic: str) -> bool:
        """Check if subscribed to topic."""
        return topic in self.subscriptions


class WebSocketManager:
    """Manages WebSocket connections and message routing."""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.connections: Dict[str, WebSocketConnection] = {}
        self.topic_subscribers: Dict[str, Set[str]] = {}
        self.ping_interval = 30  # seconds
        self._ping_task: Optional[asyncio.Task] = None
        
        # Set up event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self) -> None:
        """Set up domain event handlers."""
        # Pipeline execution events
        self.event_bus.subscribe(PipelineExecutionStarted, self._handle_pipeline_execution_started)
        self.event_bus.subscribe(PipelineExecutionCompleted, self._handle_pipeline_execution_completed)
        self.event_bus.subscribe(PipelineExecutionFailed, self._handle_pipeline_execution_failed)
        self.event_bus.subscribe(PipelineExecutionProgress, self._handle_pipeline_execution_progress)
        
        # Step execution events
        self.event_bus.subscribe(StepExecutionStarted, self._handle_step_execution_started)
        self.event_bus.subscribe(StepExecutionCompleted, self._handle_step_execution_completed)
        self.event_bus.subscribe(StepExecutionFailed, self._handle_step_execution_failed)
        
        # Template events
        self.event_bus.subscribe(PipelineTemplateCreated, self._handle_template_created)
        self.event_bus.subscribe(PipelineTemplateUpdated, self._handle_template_updated)
        self.event_bus.subscribe(PipelineTemplateDeleted, self._handle_template_deleted)
        
        # Workspace events
        self.event_bus.subscribe(WorkspaceUpdated, self._handle_workspace_updated)
    
    async def connect(self, websocket: WebSocket, workspace_name: str = "default") -> str:
        """Accept WebSocket connection and return connection ID."""
        await websocket.accept()
        
        connection_id = str(uuid.uuid4())
        context = get_current_context()
        user_id = context.user_id if context else None
        
        connection = WebSocketConnection(
            websocket=websocket,
            connection_id=connection_id,
            workspace_name=workspace_name,
            user_id=user_id
        )
        
        self.connections[connection_id] = connection
        
        # Send connection acknowledgment
        ack_message = WebSocketMessage(
            type=WebSocketMessageType.CONNECTION_ACK,
            payload={
                "connection_id": connection_id,
                "workspace_name": workspace_name,
                "server_time": datetime.utcnow().isoformat()
            }
        )
        await connection.send_message(ack_message)
        
        # Start ping task if not already running
        if self._ping_task is None or self._ping_task.done():
            self._ping_task = asyncio.create_task(self._ping_loop())
        
        return connection_id
    
    def disconnect(self, connection_id: str) -> None:
        """Remove WebSocket connection."""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            
            # Remove from topic subscriptions
            for topic in list(connection.subscriptions):
                self._unsubscribe_from_topic(connection_id, topic)
            
            del self.connections[connection_id]
    
    async def handle_message(self, connection_id: str, message_data: Dict[str, Any]) -> None:
        """Handle incoming WebSocket message."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        try:
            message = WebSocketMessage.from_dict(message_data)
            
            if message.type == WebSocketMessageType.PING:
                await self._handle_ping(connection, message)
            
            elif message.type == WebSocketMessageType.SUBSCRIBE:
                await self._handle_subscribe(connection, message)
            
            elif message.type == WebSocketMessageType.UNSUBSCRIBE:
                await self._handle_unsubscribe(connection, message)
            
            elif message.type == WebSocketMessageType.USER_SELECTION:
                await self._handle_user_selection(connection, message)
            
            elif message.type == WebSocketMessageType.USER_FEEDBACK:
                await self._handle_user_feedback(connection, message)
            
            elif message.type == WebSocketMessageType.USER_INPUT:
                await self._handle_user_input(connection, message)
            
            else:
                await connection.send_error(
                    "unknown_message_type",
                    f"Unknown message type: {message.type}"
                )
        
        except Exception as e:
            await connection.send_error(
                "message_handling_error",
                f"Error handling message: {str(e)}"
            )
    
    async def broadcast_to_topic(self, topic: str, message: WebSocketMessage) -> None:
        """Broadcast message to all subscribers of a topic."""
        if topic not in self.topic_subscribers:
            return
        
        subscriber_ids = list(self.topic_subscribers[topic])
        
        # Send to all subscribers
        tasks = []
        for connection_id in subscriber_ids:
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                tasks.append(connection.send_message(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_workspace(self, workspace_name: str, message: WebSocketMessage) -> None:
        """Broadcast message to all connections in a workspace."""
        tasks = []
        for connection in self.connections.values():
            if connection.workspace_name == workspace_name:
                tasks.append(connection.send_message(message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _subscribe_to_topic(self, connection_id: str, topic: str) -> None:
        """Subscribe connection to topic."""
        if topic not in self.topic_subscribers:
            self.topic_subscribers[topic] = set()
        
        self.topic_subscribers[topic].add(connection_id)
        
        if connection_id in self.connections:
            self.connections[connection_id].subscribe(topic)
    
    def _unsubscribe_from_topic(self, connection_id: str, topic: str) -> None:
        """Unsubscribe connection from topic."""
        if topic in self.topic_subscribers:
            self.topic_subscribers[topic].discard(connection_id)
            
            # Clean up empty topic
            if not self.topic_subscribers[topic]:
                del self.topic_subscribers[topic]
        
        if connection_id in self.connections:
            self.connections[connection_id].unsubscribe(topic)
    
    async def _ping_loop(self) -> None:
        """Periodic ping to keep connections alive."""
        while True:
            try:
                await asyncio.sleep(self.ping_interval)
                
                if not self.connections:
                    continue
                
                ping_message = WebSocketMessage(
                    type=WebSocketMessageType.PING,
                    payload={"server_time": datetime.utcnow().isoformat()}
                )
                
                # Send ping to all connections
                tasks = []
                for connection in list(self.connections.values()):
                    tasks.append(connection.send_message(ping_message))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            
            except asyncio.CancelledError:
                break
            except Exception:
                # Continue ping loop even if some pings fail
                continue
    
    # Message handlers
    
    async def _handle_ping(self, connection: WebSocketConnection, message: WebSocketMessage) -> None:
        """Handle ping message."""
        connection.last_ping = datetime.utcnow()
        
        pong_message = WebSocketMessage(
            type=WebSocketMessageType.PONG,
            payload={"server_time": datetime.utcnow().isoformat()}
        )
        await connection.send_message(pong_message)
    
    async def _handle_subscribe(self, connection: WebSocketConnection, message: WebSocketMessage) -> None:
        """Handle subscription request."""
        topic = message.payload.get("topic")
        if not topic:
            await connection.send_error(
                "invalid_subscription",
                "Topic is required for subscription"
            )
            return
        
        self._subscribe_to_topic(connection.connection_id, topic)
        
        ack_message = WebSocketMessage(
            type=WebSocketMessageType.SUBSCRIPTION_ACK,
            payload={"topic": topic, "subscribed": True}
        )
        await connection.send_message(ack_message)
    
    async def _handle_unsubscribe(self, connection: WebSocketConnection, message: WebSocketMessage) -> None:
        """Handle unsubscription request."""
        topic = message.payload.get("topic")
        if not topic:
            await connection.send_error(
                "invalid_unsubscription",
                "Topic is required for unsubscription"
            )
            return
        
        self._unsubscribe_from_topic(connection.connection_id, topic)
        
        ack_message = WebSocketMessage(
            type=WebSocketMessageType.SUBSCRIPTION_ACK,
            payload={"topic": topic, "subscribed": False}
        )
        await connection.send_message(ack_message)
    
    async def _handle_user_selection(self, connection: WebSocketConnection, message: WebSocketMessage) -> None:
        """Handle user selection for step responses."""
        run_id = message.payload.get("run_id")
        step_id = message.payload.get("step_id")
        selected_response = message.payload.get("selected_response")
        
        if not all([run_id, step_id, selected_response is not None]):
            await connection.send_error(
                "invalid_user_selection",
                "run_id, step_id, and selected_response are required"
            )
            return
        
        # TODO: Send user selection to execution engine
        # This would typically involve calling a command handler
        pass
    
    async def _handle_user_feedback(self, connection: WebSocketConnection, message: WebSocketMessage) -> None:
        """Handle user feedback."""
        run_id = message.payload.get("run_id")
        step_id = message.payload.get("step_id")
        feedback = message.payload.get("feedback", "")
        
        if not all([run_id, step_id]):
            await connection.send_error(
                "invalid_user_feedback",
                "run_id and step_id are required"
            )
            return
        
        # TODO: Send user feedback to execution engine
        pass
    
    async def _handle_user_input(self, connection: WebSocketConnection, message: WebSocketMessage) -> None:
        """Handle user input for interactive steps."""
        run_id = message.payload.get("run_id")
        step_id = message.payload.get("step_id")
        user_input = message.payload.get("input")
        
        if not all([run_id, step_id, user_input is not None]):
            await connection.send_error(
                "invalid_user_input",
                "run_id, step_id, and input are required"
            )
            return
        
        # TODO: Send user input to execution engine
        pass
    
    # Domain event handlers
    
    async def _handle_pipeline_execution_started(self, event: PipelineExecutionStarted) -> None:
        """Handle pipeline execution started event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.EXECUTION_STARTED,
            payload={
                "run_id": event.run_id,
                "pipeline_id": event.pipeline_id,
                "pipeline_name": event.pipeline_name,
                "workspace_name": event.workspace_name,
                "started_at": event.timestamp.isoformat()
            }
        )
        
        # Broadcast to workspace and specific run topic
        await self.broadcast_to_workspace(event.workspace_name, message)
        await self.broadcast_to_topic(f"run:{event.run_id}", message)
    
    async def _handle_pipeline_execution_completed(self, event: PipelineExecutionCompleted) -> None:
        """Handle pipeline execution completed event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.EXECUTION_COMPLETED,
            payload={
                "run_id": event.run_id,
                "pipeline_id": event.pipeline_id,
                "workspace_name": event.workspace_name,
                "completed_at": event.timestamp.isoformat(),
                "execution_time": event.execution_time,
                "outputs": event.outputs
            }
        )
        
        await self.broadcast_to_workspace(event.workspace_name, message)
        await self.broadcast_to_topic(f"run:{event.run_id}", message)
    
    async def _handle_pipeline_execution_failed(self, event: PipelineExecutionFailed) -> None:
        """Handle pipeline execution failed event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.EXECUTION_FAILED,
            payload={
                "run_id": event.run_id,
                "pipeline_id": event.pipeline_id,
                "workspace_name": event.workspace_name,
                "failed_at": event.timestamp.isoformat(),
                "error": event.error,
                "error_details": event.error_details
            }
        )
        
        await self.broadcast_to_workspace(event.workspace_name, message)
        await self.broadcast_to_topic(f"run:{event.run_id}", message)
    
    async def _handle_pipeline_execution_progress(self, event: PipelineExecutionProgress) -> None:
        """Handle pipeline execution progress event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.EXECUTION_PROGRESS,
            payload={
                "run_id": event.run_id,
                "current_step": event.current_step,
                "step_progress": event.step_progress,
                "overall_progress": event.overall_progress,
                "status_message": event.status_message,
                "timestamp": event.timestamp.isoformat()
            }
        )
        
        await self.broadcast_to_topic(f"run:{event.run_id}", message)
    
    async def _handle_step_execution_started(self, event: StepExecutionStarted) -> None:
        """Handle step execution started event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.STEP_STARTED,
            payload={
                "run_id": event.run_id,
                "step_id": event.step_id,
                "step_name": event.step_name,
                "step_type": event.step_type,
                "started_at": event.timestamp.isoformat()
            }
        )
        
        await self.broadcast_to_topic(f"run:{event.run_id}", message)
    
    async def _handle_step_execution_completed(self, event: StepExecutionCompleted) -> None:
        """Handle step execution completed event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.STEP_COMPLETED,
            payload={
                "run_id": event.run_id,
                "step_id": event.step_id,
                "step_name": event.step_name,
                "completed_at": event.timestamp.isoformat(),
                "execution_time": event.execution_time,
                "outputs": event.outputs,
                "responses": event.responses
            }
        )
        
        await self.broadcast_to_topic(f"run:{event.run_id}", message)
    
    async def _handle_step_execution_failed(self, event: StepExecutionFailed) -> None:
        """Handle step execution failed event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.STEP_FAILED,
            payload={
                "run_id": event.run_id,
                "step_id": event.step_id,
                "step_name": event.step_name,
                "failed_at": event.timestamp.isoformat(),
                "error": event.error,
                "error_details": event.error_details
            }
        )
        
        await self.broadcast_to_topic(f"run:{event.run_id}", message)
    
    async def _handle_template_created(self, event: PipelineTemplateCreated) -> None:
        """Handle template created event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.TEMPLATE_CREATED,
            payload={
                "template_id": event.template_id,
                "template_name": event.template_name,
                "workspace_name": event.workspace_name,
                "created_at": event.timestamp.isoformat()
            }
        )
        
        await self.broadcast_to_workspace(event.workspace_name, message)
        await self.broadcast_to_topic("templates", message)
    
    async def _handle_template_updated(self, event: PipelineTemplateUpdated) -> None:
        """Handle template updated event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.TEMPLATE_UPDATED,
            payload={
                "template_id": event.template_id,
                "template_name": event.template_name,
                "workspace_name": event.workspace_name,
                "updated_at": event.timestamp.isoformat()
            }
        )
        
        await self.broadcast_to_workspace(event.workspace_name, message)
        await self.broadcast_to_topic("templates", message)
    
    async def _handle_template_deleted(self, event: PipelineTemplateDeleted) -> None:
        """Handle template deleted event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.TEMPLATE_DELETED,
            payload={
                "template_id": event.template_id,
                "template_name": event.template_name,
                "workspace_name": event.workspace_name,
                "deleted_at": event.timestamp.isoformat()
            }
        )
        
        await self.broadcast_to_workspace(event.workspace_name, message)
        await self.broadcast_to_topic("templates", message)
    
    async def _handle_workspace_updated(self, event: WorkspaceUpdated) -> None:
        """Handle workspace updated event."""
        message = WebSocketMessage(
            type=WebSocketMessageType.WORKSPACE_UPDATED,
            payload={
                "workspace_name": event.workspace_name,
                "updated_at": event.timestamp.isoformat()
            }
        )
        
        await self.broadcast_to_workspace(event.workspace_name, message)
        await self.broadcast_to_topic("workspaces", message)


# WebSocket endpoint handler

class WebSocketHandler:
    """Main WebSocket endpoint handler."""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
    
    async def handle_connection(self, websocket: WebSocket, workspace_name: str = "default") -> None:
        """Handle WebSocket connection lifecycle."""
        connection_id = await self.websocket_manager.connect(websocket, workspace_name)
        
        try:
            while True:
                try:
                    # Receive message
                    data = await websocket.receive_text()
                    message_data = json.loads(data)
                    
                    # Handle message
                    await self.websocket_manager.handle_message(connection_id, message_data)
                
                except json.JSONDecodeError:
                    # Send error for invalid JSON
                    if connection_id in self.websocket_manager.connections:
                        connection = self.websocket_manager.connections[connection_id]
                        await connection.send_error(
                            "invalid_json",
                            "Invalid JSON message format"
                        )
                
                except WebSocketDisconnect:
                    break
                
                except ConnectionClosed:
                    break
                
                except Exception as e:
                    # Handle other errors
                    if connection_id in self.websocket_manager.connections:
                        connection = self.websocket_manager.connections[connection_id]
                        await connection.send_error(
                            "internal_error",
                            f"Internal server error: {str(e)}"
                        )
        
        finally:
            # Clean up connection
            self.websocket_manager.disconnect(connection_id)


# Utility context manager for WebSocket testing

@asynccontextmanager
async def websocket_client(websocket_manager: WebSocketManager, workspace_name: str = "default"):
    """Context manager for WebSocket client testing."""
    # This would be used in tests to simulate WebSocket clients
    pass