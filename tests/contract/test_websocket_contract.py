"""
Contract tests for WebSocket message flows.

Ensures that WebSocket endpoints properly handle real-time communication,
including connection management, message formats, and error handling.
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from pathlib import Path
import tempfile
import shutil
from datetime import datetime, UTC

from writeit.infrastructure.web.app import create_app
from writeit.shared.dependencies.container import Container
from writeit.shared.events.bus import EventBus
from writeit.workspace.workspace import Workspace


@pytest.fixture
def temp_home() -> Path:
    """Create temporary home directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
async def test_app(temp_home: Path):
    """Create test FastAPI application with temporary workspace."""
    # Initialize workspace
    workspace = Workspace(temp_home / ".writeit")
    workspace.initialize()
    
    # Create app with test container
    container = Container()
    event_bus = EventBus()
    app = create_app(container=container, event_bus=event_bus, debug=True)
    
    # Set workspace for testing
    app.state.workspace = temp_home / ".writeit"
    
    yield app


class MockWebSocket:
    """Mock WebSocket for testing."""
    
    def __init__(self):
        self.messages = []
        self.closed = False
        self.close_code = None
        self.close_reason = None
    
    async def send_json(self, data: Dict[str, Any]):
        """Send JSON message."""
        self.messages.append(data)
    
    async def send_text(self, data: str):
        """Send text message."""
        self.messages.append(json.loads(data))
    
    async def close(self, code: int = 1000, reason: str = None):
        """Close WebSocket connection."""
        self.closed = True
        self.close_code = code
        self.close_reason = reason


class TestWorkspaceWebSocketContract:
    """Contract tests for workspace WebSocket endpoints."""

    @pytest.mark.asyncio
    async def test_workspace_connection_contract(self, test_app):
        """Test workspace WebSocket connection contract."""
        mock_websocket = MockWebSocket()
        
        # Simulate workspace WebSocket connection
        from writeit.infrastructure.web.websocket_handlers import WorkspaceWebSocketHandler
        
        handler = WorkspaceWebSocketHandler()
        
        # Test connection acceptance
        await handler.connect(mock_websocket, "test-workspace")
        
        # Contract: Connection should be accepted
        assert not mock_websocket.closed
        
        # Contract: Welcome message should be sent
        assert len(mock_websocket.messages) > 0
        welcome_message = mock_websocket.messages[0]
        assert welcome_message["type"] == "connection_established"
        assert welcome_message["workspace"] == "test-workspace"
        assert "timestamp" in welcome_message

    @pytest.mark.asyncio
    async def test_workspace_subscription_contract(self, test_app):
        """Test workspace event subscription contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import WorkspaceWebSocketHandler
        
        handler = WorkspaceWebSocketHandler()
        await handler.connect(mock_websocket, "test-workspace")
        
        # Clear welcome message
        mock_websocket.messages.clear()
        
        # Test event subscription
        await handler.subscribe_to_events(mock_websocket, "test-workspace", ["pipeline_execution"])
        
        # Simulate event
        event_data = {
            "type": "pipeline_execution_started",
            "pipeline_id": "test-pipeline",
            "workspace": "test-workspace",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {"run_id": "test-run"}
        }
        
        await handler.broadcast_to_workspace("test-workspace", event_data)
        
        # Contract: Event should be received
        assert len(mock_websocket.messages) == 1
        received_event = mock_websocket.messages[0]
        assert received_event["type"] == "pipeline_execution_started"
        assert received_event["workspace"] == "test-workspace"
        assert received_event["data"]["run_id"] == "test-run"

    @pytest.mark.asyncio
    async def test_workspace_unsubscription_contract(self, test_app):
        """Test workspace event unsubscription contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import WorkspaceWebSocketHandler
        
        handler = WorkspaceWebSocketHandler()
        await handler.connect(mock_websocket, "test-workspace")
        
        # Subscribe to events
        await handler.subscribe_to_events(mock_websocket, "test-workspace", ["pipeline_execution"])
        
        # Unsubscribe
        await handler.unsubscribe_from_events(mock_websocket, "test-workspace", ["pipeline_execution"])
        
        # Clear messages
        mock_websocket.messages.clear()
        
        # Simulate event
        event_data = {
            "type": "pipeline_execution_started",
            "workspace": "test-workspace",
            "timestamp": datetime.now(UTC).isoformat(),
            "data": {"run_id": "test-run"}
        }
        
        await handler.broadcast_to_workspace("test-workspace", event_data)
        
        # Contract: Event should not be received after unsubscription
        assert len(mock_websocket.messages) == 0

    @pytest.mark.asyncio
    async def test_workspace_disconnection_contract(self, test_app):
        """Test workspace WebSocket disconnection contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import WorkspaceWebSocketHandler
        
        handler = WorkspaceWebSocketHandler()
        await handler.connect(mock_websocket, "test-workspace")
        
        # Test disconnection
        await handler.disconnect(mock_websocket, "test-workspace")
        
        # Contract: WebSocket should be closed
        assert mock_websocket.closed


class TestRunWebSocketContract:
    """Contract tests for pipeline run WebSocket endpoints."""

    @pytest.mark.asyncio
    async def test_run_connection_contract(self, test_app):
        """Test pipeline run WebSocket connection contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        
        # Test run connection
        await handler.connect(mock_websocket, "test-run-123")
        
        # Contract: Connection should be accepted
        assert not mock_websocket.closed
        
        # Contract: Welcome message should be sent
        assert len(mock_websocket.messages) > 0
        welcome_message = mock_websocket.messages[0]
        assert welcome_message["type"] == "run_connection_established"
        assert welcome_message["run_id"] == "test-run-123"
        assert "timestamp" in welcome_message

    @pytest.mark.asyncio
    async def test_run_progress_updates_contract(self, test_app):
        """Test run progress update contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        await handler.connect(mock_websocket, "test-run-123")
        
        # Clear welcome message
        mock_websocket.messages.clear()
        
        # Test progress update
        progress_data = {
            "type": "step_progress",
            "run_id": "test-run-123",
            "step_key": "outline",
            "progress": {
                "current_step": 1,
                "total_steps": 3,
                "percent_complete": 33.3,
                "status": "executing"
            },
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        await handler.send_progress_update(mock_websocket, progress_data)
        
        # Contract: Progress update should be received
        assert len(mock_websocket.messages) == 1
        received_update = mock_websocket.messages[0]
        assert received_update["type"] == "step_progress"
        assert received_update["run_id"] == "test-run-123"
        assert received_update["step_key"] == "outline"
        assert "progress" in received_update

    @pytest.mark.asyncio
    async def test_run_execution_events_contract(self, test_app):
        """Test run execution event contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        await handler.connect(mock_websocket, "test-run-123")
        
        # Clear welcome message
        mock_websocket.messages.clear()
        
        # Test execution events
        events = [
            {
                "type": "step_started",
                "run_id": "test-run-123",
                "step_key": "outline",
                "timestamp": datetime.now(UTC).isoformat(),
                "data": {"model": "gpt-4o-mini"}
            },
            {
                "type": "llm_response_received",
                "run_id": "test-run-123",
                "step_key": "outline",
                "timestamp": datetime.now(UTC).isoformat(),
                "data": {"tokens_used": 150, "response_length": 500}
            },
            {
                "type": "step_completed",
                "run_id": "test-run-123",
                "step_key": "outline",
                "timestamp": datetime.now(UTC).isoformat(),
                "data": {"execution_time": 2.5, "success": True}
            }
        ]
        
        for event in events:
            await handler.send_execution_event(mock_websocket, event)
        
        # Contract: All events should be received
        assert len(mock_websocket.messages) == 3
        
        # Verify each event type
        event_types = [msg["type"] for msg in mock_websocket.messages]
        assert "step_started" in event_types
        assert "llm_response_received" in event_types
        assert "step_completed" in event_types

    @pytest.mark.asyncio
    async def test_run_streaming_responses_contract(self, test_app):
        """Test run streaming response contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        await handler.connect(mock_websocket, "test-run-123")
        
        # Clear welcome message
        mock_websocket.messages.clear()
        
        # Test streaming response
        chunks = [
            {"type": "token", "content": "Hello", "index": 0},
            {"type": "token", "content": " World", "index": 1},
            {"type": "token", "content": "!", "index": 2},
            {"type": "done", "content": "", "index": 3}
        ]
        
        for chunk in chunks:
            await handler.send_streaming_chunk(mock_websocket, chunk)
        
        # Contract: All chunks should be received
        assert len(mock_websocket.messages) == 4
        
        # Verify streaming format
        for i, message in enumerate(mock_websocket.messages):
            assert message["type"] in ["token", "done"]
            assert "content" in message
            assert "index" in message

    @pytest.mark.asyncio
    async def test_run_error_handling_contract(self, test_app):
        """Test run error handling contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        await handler.connect(mock_websocket, "test-run-123")
        
        # Clear welcome message
        mock_websocket.messages.clear()
        
        # Test error message
        error_data = {
            "type": "execution_error",
            "run_id": "test-run-123",
            "error": {
                "code": "LLM_PROVIDER_ERROR",
                "message": "Failed to connect to LLM provider",
                "details": {"provider": "openai", "retry_count": 3}
            },
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        await handler.send_error_message(mock_websocket, error_data)
        
        # Contract: Error message should be received
        assert len(mock_websocket.messages) == 1
        error_message = mock_websocket.messages[0]
        assert error_message["type"] == "execution_error"
        assert error_message["run_id"] == "test-run-123"
        assert "error" in error_message
        assert error_message["error"]["code"] == "LLM_PROVIDER_ERROR"


class TestWebSocketMessageFormatContract:
    """Contract tests for WebSocket message format consistency."""

    @pytest.mark.asyncio
    async def test_message_structure_contract(self, test_app):
        """Test consistent message structure contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        await handler.connect(mock_websocket, "test-run-123")
        
        # Test message structure
        message_types = [
            "connection_established",
            "step_started", 
            "step_progress",
            "llm_response_received",
            "step_completed",
            "execution_error",
            "run_completed"
        ]
        
        for msg_type in message_types:
            mock_websocket.messages.clear()
            
            message_data = {
                "type": msg_type,
                "run_id": "test-run-123",
                "timestamp": datetime.now(UTC).isoformat()
            }
            
            if msg_type == "connection_established":
                await handler.connect(mock_websocket, "test-run-123")
            else:
                await handler.send_execution_event(mock_websocket, message_data)
            
            if mock_websocket.messages:
                message = mock_websocket.messages[0]
                
                # Contract: All messages must have required fields
                assert "type" in message
                assert "timestamp" in message
                assert isinstance(message["type"], str)
                assert isinstance(message["timestamp"], str)
                
                # Contract: Timestamp should be valid ISO format
                try:
                    datetime.fromisoformat(message["timestamp"].replace('Z', '+00:00'))
                except ValueError:
                    pytest.fail(f"Invalid timestamp format: {message['timestamp']}")

    @pytest.mark.asyncio
    async def test_message_serialization_contract(self, test_app):
        """Test message serialization contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        
        # Test with complex data structures
        complex_message = {
            "type": "step_progress",
            "run_id": "test-run-123",
            "step_key": "complex_step",
            "progress": {
                "current_step": 2,
                "total_steps": 5,
                "percent_complete": 40.0,
                "status": "executing",
                "substeps": [
                    {"name": "preprocessing", "status": "completed"},
                    {"name": "processing", "status": "executing"},
                    {"name": "postprocessing", "status": "pending"}
                ]
            },
            "metadata": {
                "model": "gpt-4o-mini",
                "tokens_used": {"input": 100, "output": 200},
                "execution_time": 1.5
            },
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        await handler.send_execution_event(mock_websocket, complex_message)
        
        # Contract: Complex message should be serializable
        assert len(mock_websocket.messages) == 1
        received_message = mock_websocket.messages[0]
        
        # Verify complex structure is preserved
        assert received_message["progress"]["substeps"][0]["name"] == "preprocessing"
        assert received_message["metadata"]["tokens_used"]["input"] == 100


class TestWebSocketConnectionManagementContract:
    """Contract tests for WebSocket connection management."""

    @pytest.mark.asyncio
    async def test_connection_timeout_contract(self, test_app):
        """Test connection timeout handling contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        
        # Test connection with timeout
        try:
            await asyncio.wait_for(
                handler.connect(mock_websocket, "test-run-123"),
                timeout=5.0
            )
        except asyncio.TimeoutError:
            pytest.fail("WebSocket connection should not timeout")

    @pytest.mark.asyncio
    async def test_connection_limit_contract(self, test_app):
        """Test connection limit enforcement contract."""
        from writeit.infrastructure.web.websocket_handlers import ConnectionManager
        
        manager = ConnectionManager(max_connections=2)
        
        # Test connection limit
        mock_websocket1 = MockWebSocket()
        mock_websocket2 = MockWebSocket()
        mock_websocket3 = MockWebSocket()
        
        # Should accept first two connections
        assert await manager.add_connection(mock_websocket1, "conn1") == True
        assert await manager.add_connection(mock_websocket2, "conn2") == True
        
        # Should reject third connection
        assert await manager.add_connection(mock_websocket3, "conn3") == False

    @pytest.mark.asyncio
    async def test_connection_cleanup_contract(self, test_app):
        """Test connection cleanup contract."""
        from writeit.infrastructure.web.websocket_handlers import ConnectionManager
        
        manager = ConnectionManager()
        
        # Add connection
        mock_websocket = MockWebSocket()
        await manager.add_connection(mock_websocket, "test-conn")
        
        # Simulate disconnection
        mock_websocket.closed = True
        
        # Clean up closed connections
        await manager.cleanup_closed_connections()
        
        # Contract: Closed connection should be removed
        assert len(manager.connections) == 0


class TestWebSocketErrorHandlingContract:
    """Contract tests for WebSocket error handling."""

    @pytest.mark.asyncio
    async def test_invalid_message_handling_contract(self, test_app):
        """Test invalid message handling contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        await handler.connect(mock_websocket, "test-run-123")
        
        # Clear welcome message
        mock_websocket.messages.clear()
        
        # Test with invalid message (missing required fields)
        invalid_message = {"type": "invalid"}  # Missing run_id and timestamp
        
        try:
            await handler.send_execution_event(mock_websocket, invalid_message)
        except Exception:
            # Contract: Should handle invalid messages gracefully
            pass
        
        # Contract: WebSocket should not be closed due to invalid message
        assert not mock_websocket.closed

    @pytest.mark.asyncio
    async def test_connection_error_recovery_contract(self, test_app):
        """Test connection error recovery contract."""
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        
        # Test with WebSocket that raises exceptions
        class ErrorWebSocket:
            def __init__(self):
                self.send_error = False
            
            async def send_json(self, data):
                if self.send_error:
                    raise Exception("Network error")
                pass
        
        error_websocket = ErrorWebSocket()
        
        # First send should succeed
        await handler.connect(error_websocket, "test-run-123")
        
        # Trigger error
        error_websocket.send_error = True
        
        try:
            await handler.send_execution_event(
                error_websocket, 
                {"type": "test", "run_id": "test-run-123", "timestamp": datetime.now(UTC).isoformat()}
            )
        except Exception:
            # Contract: Should handle send errors gracefully
            pass


class TestWebSocketPerformanceContract:
    """Contract tests for WebSocket performance characteristics."""

    @pytest.mark.asyncio
    async def test_message_throughput_contract(self, test_app):
        """Test message throughput contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        await handler.connect(mock_websocket, "test-run-123")
        
        # Clear welcome message
        mock_websocket.messages.clear()
        
        # Test sending multiple messages
        num_messages = 100
        start_time = asyncio.get_event_loop().time()
        
        for i in range(num_messages):
            message = {
                "type": "progress_update",
                "run_id": "test-run-123",
                "progress": i / num_messages * 100,
                "timestamp": datetime.now(UTC).isoformat()
            }
            await handler.send_execution_event(mock_websocket, message)
        
        end_time = asyncio.get_event_loop().time()
        elapsed_time = end_time - start_time
        
        # Contract: Should handle reasonable throughput
        assert len(mock_websocket.messages) == num_messages
        assert elapsed_time < 5.0  # Should complete within 5 seconds
        
        # Contract: Messages per second should be reasonable
        messages_per_second = num_messages / elapsed_time
        assert messages_per_second > 10  # At least 10 messages per second

    @pytest.mark.asyncio
    async def test_message_size_limit_contract(self, test_app):
        """Test message size limit contract."""
        mock_websocket = MockWebSocket()
        
        from writeit.infrastructure.web.websocket_handlers import RunWebSocketHandler
        
        handler = RunWebSocketHandler()
        await handler.connect(mock_websocket, "test-run-123")
        
        # Clear welcome message
        mock_websocket.messages.clear()
        
        # Test with large message (within reasonable limits)
        large_content = "x" * 10000  # 10KB message
        large_message = {
            "type": "llm_response",
            "run_id": "test-run-123",
            "content": large_content,
            "timestamp": datetime.now(UTC).isoformat()
        }
        
        await handler.send_execution_event(mock_websocket, large_message)
        
        # Contract: Large message should be handled
        assert len(mock_websocket.messages) == 1
        assert len(mock_websocket.messages[0]["content"]) == 10000