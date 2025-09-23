"""Mock factories for testing.

Provides factory functions and classes for creating mock objects
for testing WriteIt's domain-driven architecture components.
"""

from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from unittest.mock import AsyncMock, Mock, MagicMock
import asyncio
from datetime import datetime
from uuid import uuid4

from writeit.shared.events import DomainEvent, EventHandler, AsyncEventBus, EventPublishResult
from writeit.pipeline.executor import PipelineExecutor
from writeit.domains.workspace.repositories.workspace_repository import WorkspaceRepository
from writeit.domains.workspace.entities.workspace import Workspace


class MockLLMProvider:
    """Mock LLM provider for deterministic testing."""
    
    def __init__(self):
        self.responses: Dict[str, str] = {}
        self.default_response = "Mock LLM response"
        self.call_count = 0
        self.last_prompt = ""
        self.streaming_enabled = False
        self.stream_delay = 0.01  # Small delay for realistic streaming
        self.should_fail = False
        self.failure_message = "Mock LLM failure"
    
    def set_response(self, prompt_key: str, response: str) -> None:
        """Set a specific response for a prompt pattern."""
        self.responses[prompt_key] = response
    
    def set_default_response(self, response: str) -> None:
        """Set the default response for unmatched prompts."""
        self.default_response = response
    
    async def generate_text(
        self, 
        prompt: str, 
        model: str = "mock-model",
        **kwargs
    ) -> str:
        """Generate text response (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.call_count += 1
        self.last_prompt = prompt
        
        # Check for specific response
        for key, response in self.responses.items():
            if key.lower() in prompt.lower():
                return response
        
        return self.default_response
    
    async def stream_text(
        self, 
        prompt: str, 
        model: str = "mock-model",
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream text response (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.call_count += 1
        self.last_prompt = prompt
        
        # Get response
        response = await self.generate_text(prompt, model, **kwargs)
        
        # Stream the response word by word
        words = response.split()
        for word in words:
            if self.stream_delay > 0:
                await asyncio.sleep(self.stream_delay)
            yield word + " "
    
    def get_model_info(self, model: str = "mock-model") -> Dict[str, Any]:
        """Get model information (mock)."""
        return {
            "name": model,
            "provider": "mock",
            "version": "1.0.0",
            "context_length": 4096,
            "supports_streaming": True,
            "supports_functions": False
        }
    
    def reset(self) -> None:
        """Reset mock state."""
        self.call_count = 0
        self.last_prompt = ""
        self.responses.clear()
        self.should_fail = False


class MockEventBus:
    """Mock event bus for testing."""
    
    def __init__(self):
        self.published_events: List[DomainEvent] = []
        self.registered_handlers: Dict[type, List[EventHandler]] = {}
        self.publish_results: List[EventPublishResult] = []
        self.should_fail = False
        self.failure_message = "Mock event bus failure"
        self.running = False
    
    async def publish(self, event: DomainEvent) -> EventPublishResult:
        """Publish an event (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.published_events.append(event)
        
        # Create mock result
        result = EventPublishResult(
            event=event,
            handlers_executed=len(self.registered_handlers.get(type(event), [])),
            handlers_failed=0,
            errors=[],
            stored_event=event
        )
        
        self.publish_results.append(result)
        return result
    
    async def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler (mock)."""
        event_type = handler.event_type
        if event_type not in self.registered_handlers:
            self.registered_handlers[event_type] = []
        self.registered_handlers[event_type].append(handler)
    
    async def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler (mock)."""
        event_type = handler.event_type
        if event_type in self.registered_handlers:
            self.registered_handlers[event_type].remove(handler)
    
    async def start(self) -> None:
        """Start the event bus (mock)."""
        self.running = True
    
    async def stop(self) -> None:
        """Stop the event bus (mock)."""
        self.running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics (mock)."""
        return {
            "running": self.running,
            "events_published": len(self.published_events),
            "handlers_registered": sum(len(handlers) for handlers in self.registered_handlers.values()),
            "failed_attempts": 0,
            "dead_letter_queue": 0
        }
    
    def get_published_events(self, event_type: Optional[type] = None) -> List[DomainEvent]:
        """Get published events, optionally filtered by type."""
        if event_type is None:
            return self.published_events.copy()
        return [event for event in self.published_events if isinstance(event, event_type)]
    
    def clear_events(self) -> None:
        """Clear all published events."""
        self.published_events.clear()
        self.publish_results.clear()
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.published_events.clear()
        self.registered_handlers.clear()
        self.publish_results.clear()
        self.should_fail = False
        self.running = False


class MockWorkspaceRepository:
    """Mock workspace repository for testing."""
    
    def __init__(self):
        self.workspaces: Dict[str, Workspace] = {}
        self.operation_log: List[tuple[str, str]] = []  # (operation, workspace_name)
        self.should_fail = False
        self.failure_message = "Mock repository failure"
        self.integrity_errors: Dict[str, List[str]] = {}
    
    async def find_by_name(self, name) -> Optional[Workspace]:
        """Find workspace by name (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("find_by_name", name.value))
        return self.workspaces.get(name.value)
    
    async def save(self, workspace: Workspace) -> None:
        """Save workspace (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("save", workspace.name.value))
        self.workspaces[workspace.name.value] = workspace
    
    async def delete(self, workspace: Workspace) -> None:
        """Delete workspace (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("delete", workspace.name.value))
        if workspace.name.value in self.workspaces:
            del self.workspaces[workspace.name.value]
    
    async def list_all(self) -> List[Workspace]:
        """List all workspaces (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("list_all", "*"))
        return list(self.workspaces.values())
    
    async def validate_workspace_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace integrity (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("validate_integrity", workspace.name.value))
        return self.integrity_errors.get(workspace.name.value, [])
    
    async def update_last_accessed(self, workspace: Workspace) -> None:
        """Update last accessed timestamp (mock)."""
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.operation_log.append(("update_last_accessed", workspace.name.value))
    
    # Test helper methods
    def add_workspace(self, workspace: Workspace) -> None:
        """Add a workspace to the mock repository."""
        self.workspaces[workspace.name.value] = workspace
    
    def set_integrity_errors(self, workspace_name: str, errors: List[str]) -> None:
        """Set integrity errors for a workspace."""
        self.integrity_errors[workspace_name] = errors
    
    def get_operation_count(self, operation: str, workspace_name: str = "") -> int:
        """Get count of specific operations."""
        return len([
            log for log in self.operation_log
            if log[0] == operation and (not workspace_name or log[1] == workspace_name)
        ])
    
    def clear_operation_log(self) -> None:
        """Clear operation log."""
        self.operation_log.clear()
    
    def reset(self) -> None:
        """Reset all mock state."""
        self.workspaces.clear()
        self.operation_log.clear()
        self.integrity_errors.clear()
        self.should_fail = False


def create_mock_pipeline_executor(
    llm_provider: Optional[MockLLMProvider] = None,
    event_bus: Optional[MockEventBus] = None
) -> Mock:
    """Create a mock pipeline executor for testing.
    
    Args:
        llm_provider: Optional mock LLM provider
        event_bus: Optional mock event bus
    
    Returns:
        Mock pipeline executor
    """
    if llm_provider is None:
        llm_provider = MockLLMProvider()
    
    if event_bus is None:
        event_bus = MockEventBus()
    
    executor = Mock(spec=PipelineExecutor)
    
    # Mock execution result
    mock_result = {
        "run_id": str(uuid4()),
        "status": "completed",
        "steps": {
            "outline": {
                "status": "completed",
                "result": "Mock outline result",
                "execution_time": 1.23
            },
            "content": {
                "status": "completed", 
                "result": "Mock content result",
                "execution_time": 2.45
            }
        },
        "total_execution_time": 3.68,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat()
    }
    
    # Configure mock methods
    executor.execute_pipeline = AsyncMock(return_value=mock_result)
    executor.execute_step = AsyncMock(return_value="Mock step result")
    executor.get_execution_status = Mock(return_value="completed")
    executor.cancel_execution = AsyncMock()
    
    # Attach mock dependencies
    executor.llm_provider = llm_provider
    executor.event_bus = event_bus
    
    return executor


class MockDIContainer:
    """Mock dependency injection container for testing."""
    
    def __init__(self):
        self.services: Dict[str, Any] = {}
        self.singletons: Dict[str, Any] = {}
        self.factories: Dict[str, Callable] = {}
    
    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton service."""
        self.singletons[name] = instance
    
    def register_factory(self, name: str, factory: Callable) -> None:
        """Register a factory function."""
        self.factories[name] = factory
    
    def register_service(self, name: str, service: Any) -> None:
        """Register a service instance."""
        self.services[name] = service
    
    def get(self, name: str) -> Any:
        """Get a service by name."""
        if name in self.singletons:
            return self.singletons[name]
        elif name in self.services:
            return self.services[name]
        elif name in self.factories:
            return self.factories[name]()
        else:
            raise KeyError(f"Service '{name}' not found")
    
    async def cleanup(self) -> None:
        """Cleanup all services (mock)."""
        pass
    
    def reset(self) -> None:
        """Reset all registered services."""
        self.services.clear()
        self.singletons.clear()
        self.factories.clear()


class TestDataFactory:
    """Factory for creating common test data structures."""
    
    @staticmethod
    def create_pipeline_yaml(name: str = "test-pipeline") -> Dict[str, Any]:
        """Create a test pipeline YAML structure."""
        return {
            "metadata": {
                "name": name,
                "description": f"Test pipeline: {name}",
                "version": "1.0.0"
            },
            "defaults": {
                "model": "mock-model"
            },
            "inputs": {
                "topic": {
                    "type": "text",
                    "label": "Topic",
                    "required": True,
                    "placeholder": "Enter topic..."
                },
                "style": {
                    "type": "choice",
                    "label": "Style",
                    "options": [
                        {"label": "Formal", "value": "formal"},
                        {"label": "Casual", "value": "casual"}
                    ],
                    "default": "formal"
                }
            },
            "steps": {
                "outline": {
                    "name": "Create Outline", 
                    "type": "llm_generate",
                    "prompt_template": "Create an outline for {{ inputs.topic }} in {{ inputs.style }} style.",
                    "model_preference": ["{{ defaults.model }}"]
                },
                "content": {
                    "name": "Write Content",
                    "type": "llm_generate", 
                    "prompt_template": "Based on this outline: {{ steps.outline }}\n\nWrite complete content about {{ inputs.topic }}.",
                    "depends_on": ["outline"],
                    "model_preference": ["{{ defaults.model }}"]
                }
            }
        }
    
    @staticmethod
    def create_pipeline_run_data(run_id: str = None) -> Dict[str, Any]:
        """Create test pipeline run data."""
        if run_id is None:
            run_id = str(uuid4())
        
        return {
            "run_id": run_id,
            "pipeline_id": "test-pipeline",
            "workspace_name": "test-workspace",
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "inputs": {
                "topic": "Test Topic",
                "style": "formal"
            },
            "steps": {
                "outline": {
                    "status": "completed",
                    "result": "1. Introduction\n2. Main Points\n3. Conclusion",
                    "execution_time": 1.5
                },
                "content": {
                    "status": "running",
                    "result": None,
                    "execution_time": None
                }
            },
            "metadata": {
                "version": "1.0.0",
                "model": "mock-model"
            }
        }
    
    @staticmethod
    def create_test_event(
        event_type: str = "TestEvent",
        aggregate_id: str = "test-aggregate",
        **data
    ) -> Dict[str, Any]:
        """Create test event data."""
        return {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "aggregate_id": aggregate_id,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "metadata": {
                "version": 1,
                "source": "test"
            }
        }


class MockAsyncContextManager:
    """Mock async context manager for testing."""
    
    def __init__(self, return_value: Any = None):
        self.return_value = return_value
        self.entered = False
        self.exited = False
        self.exception_info = None
    
    async def __aenter__(self):
        self.entered = True
        return self.return_value
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exited = True
        self.exception_info = (exc_type, exc_val, exc_tb)
        return False  # Don't suppress exceptions
    
    def was_entered(self) -> bool:
        """Check if context was entered."""
        return self.entered
    
    def was_exited(self) -> bool:
        """Check if context was exited."""
        return self.exited
    
    def had_exception(self) -> bool:
        """Check if an exception occurred in the context."""
        return self.exception_info[0] is not None


def create_mock_async_generator(items: List[Any], delay: float = 0.01):
    """Create a mock async generator for testing.
    
    Args:
        items: List of items to yield
        delay: Delay between yields (for realistic async behavior)
    
    Returns:
        Async generator function
    """
    async def mock_generator():
        for item in items:
            if delay > 0:
                await asyncio.sleep(delay)
            yield item
    
    return mock_generator()


class MockWebSocketConnection:
    """Mock WebSocket connection for testing."""
    
    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []
        self.received_messages: List[Dict[str, Any]] = []
        self.closed = False
        self.close_code = None
    
    async def send_json(self, data: Dict[str, Any]) -> None:
        """Send JSON message (mock)."""
        if self.closed:
            raise RuntimeError("WebSocket is closed")
        self.sent_messages.append(data)
    
    async def receive_json(self) -> Dict[str, Any]:
        """Receive JSON message (mock)."""
        if self.closed:
            raise RuntimeError("WebSocket is closed")
        if not self.received_messages:
            # Simulate waiting for message
            await asyncio.sleep(0.1)
            return {"type": "ping"}  # Default message
        return self.received_messages.pop(0)
    
    async def close(self, code: int = 1000) -> None:
        """Close connection (mock)."""
        self.closed = True
        self.close_code = code
    
    def add_received_message(self, message: Dict[str, Any]) -> None:
        """Add a message to the received queue."""
        self.received_messages.append(message)
    
    def get_sent_messages(self) -> List[Dict[str, Any]]:
        """Get all sent messages."""
        return self.sent_messages.copy()
    
    def clear_messages(self) -> None:
        """Clear all message history."""
        self.sent_messages.clear()
        self.received_messages.clear()