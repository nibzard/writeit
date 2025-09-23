"""Integration example for Event Bus with Dependency Injection.

Demonstrates how to integrate the event bus with the DI container
and use it in a real WriteIt application context."""

import asyncio
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime

from ..dependencies import Container, ServiceLifetime
from . import (
    DomainEvent,
    AsyncEventBus,
    InMemoryEventStore,
    BaseEventHandler,
    event_handler,
    HandlerDiscovery
)


# Example Domain Events
class PipelineExecutionStarted(DomainEvent):
    """Event fired when pipeline execution starts."""
    
    def __init__(self, pipeline_id: str, workspace_name: str, started_by: str):
        super().__init__()
        self.pipeline_id = pipeline_id
        self.workspace_name = workspace_name
        self.started_by = started_by
    
    @property
    def event_type(self) -> str:
        return "pipeline.execution.started"
    
    @property
    def aggregate_id(self) -> str:
        return self.pipeline_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'pipeline_id': self.pipeline_id,
            'workspace_name': self.workspace_name,
            'started_by': self.started_by,
            'timestamp': self.timestamp.isoformat()
        }


class PipelineExecutionCompleted(DomainEvent):
    """Event fired when pipeline execution completes."""
    
    def __init__(self, pipeline_id: str, workspace_name: str, success: bool, duration_seconds: float):
        super().__init__()
        self.pipeline_id = pipeline_id
        self.workspace_name = workspace_name
        self.success = success
        self.duration_seconds = duration_seconds
    
    @property
    def event_type(self) -> str:
        return "pipeline.execution.completed"
    
    @property
    def aggregate_id(self) -> str:
        return self.pipeline_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'pipeline_id': self.pipeline_id,
            'workspace_name': self.workspace_name,
            'success': self.success,
            'duration_seconds': self.duration_seconds,
            'timestamp': self.timestamp.isoformat()
        }


# Example Event Handlers using decorators
@event_handler(PipelineExecutionStarted, priority=10)
class PipelineMetricsHandler(BaseEventHandler[PipelineExecutionStarted]):
    """Handler that tracks pipeline metrics."""
    
    def __init__(self, metrics_service=None):
        super().__init__(priority=10)
        self.metrics_service = metrics_service
    
    async def handle(self, event: PipelineExecutionStarted) -> None:
        """Record pipeline start metrics."""
        print(f"📊 Recording pipeline start: {event.pipeline_id} in workspace {event.workspace_name}")
        # In real implementation, would call metrics_service.record_start()
    
    @property
    def event_type(self) -> type:
        return PipelineExecutionStarted


@event_handler(PipelineExecutionStarted, priority=50)
class NotificationHandler(BaseEventHandler[PipelineExecutionStarted]):
    """Handler that sends notifications."""
    
    def __init__(self, notification_service=None):
        super().__init__(priority=50)
        self.notification_service = notification_service
    
    async def handle(self, event: PipelineExecutionStarted) -> None:
        """Send start notification."""
        print(f"🔔 Sending notification: Pipeline {event.pipeline_id} started by {event.started_by}")
        # In real implementation, would call notification_service.send()
    
    @property
    def event_type(self) -> type:
        return PipelineExecutionStarted


@event_handler(PipelineExecutionCompleted, priority=20)
class CompletionMetricsHandler(BaseEventHandler[PipelineExecutionCompleted]):
    """Handler that tracks completion metrics."""
    
    def __init__(self, metrics_service=None):
        super().__init__(priority=20)
        self.metrics_service = metrics_service
    
    async def handle(self, event: PipelineExecutionCompleted) -> None:
        """Record pipeline completion metrics."""
        status = "✅ SUCCESS" if event.success else "❌ FAILED"
        print(f"📈 Pipeline {event.pipeline_id} completed: {status} in {event.duration_seconds:.2f}s")
        # In real implementation, would call metrics_service.record_completion()
    
    @property
    def event_type(self) -> type:
        return PipelineExecutionCompleted


# Function-based handler example
@event_handler(priority=100)
async def log_all_pipeline_events(event: PipelineExecutionStarted) -> None:
    """Simple logging handler using function decorator."""
    print(f"📝 LOG: {event.event_type} - {event.pipeline_id} at {event.timestamp}")


@event_handler(priority=100)
async def log_pipeline_completions(event: PipelineExecutionCompleted) -> None:
    """Log pipeline completion events."""
    print(f"📝 LOG: Pipeline {event.pipeline_id} completed with success={event.success}")


# Services that depend on the event bus
class PipelineExecutionService:
    """Service that publishes domain events during pipeline execution."""
    
    def __init__(self, event_bus: AsyncEventBus):
        self.event_bus = event_bus
    
    async def start_pipeline(self, pipeline_id: str, workspace_name: str, started_by: str) -> None:
        """Start pipeline execution and publish event."""
        print(f"🚀 Starting pipeline {pipeline_id}...")
        
        # Publish domain event
        event = PipelineExecutionStarted(
            pipeline_id=pipeline_id,
            workspace_name=workspace_name,
            started_by=started_by
        )
        
        result = await self.event_bus.publish(event)
        print(f"   Event published to {result.handlers_executed} handlers")
    
    async def complete_pipeline(self, pipeline_id: str, workspace_name: str, success: bool, duration: float) -> None:
        """Complete pipeline execution and publish event."""
        print(f"🏁 Completing pipeline {pipeline_id}...")
        
        # Publish domain event
        event = PipelineExecutionCompleted(
            pipeline_id=pipeline_id,
            workspace_name=workspace_name,
            success=success,
            duration_seconds=duration
        )
        
        result = await self.event_bus.publish(event)
        print(f"   Event published to {result.handlers_executed} handlers")


class MetricsService:
    """Mock metrics service."""
    
    def __init__(self):
        self.metrics = []
    
    def record_start(self, pipeline_id: str) -> None:
        self.metrics.append(f"START: {pipeline_id}")
    
    def record_completion(self, pipeline_id: str, success: bool, duration: float) -> None:
        self.metrics.append(f"COMPLETE: {pipeline_id} - {success} - {duration}s")


class NotificationService:
    """Mock notification service."""
    
    def __init__(self):
        self.notifications = []
    
    def send(self, message: str) -> None:
        self.notifications.append(message)


def configure_event_system(container: Container) -> None:
    """Configure the event system in the DI container.
    
    This function shows how to integrate the event bus with WriteIt's
    dependency injection system.
    """
    # Register event infrastructure
    container.register(
        interface=InMemoryEventStore,
        implementation=InMemoryEventStore,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # Register event bus as singleton
    def create_event_bus(event_store: InMemoryEventStore) -> AsyncEventBus:
        return AsyncEventBus(
            event_store=event_store,
            max_concurrent_handlers=10
        )
    
    container.register(
        interface=AsyncEventBus,
        factory=create_event_bus,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # Register supporting services
    container.register(
        interface=MetricsService,
        implementation=MetricsService,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    container.register(
        interface=NotificationService,
        implementation=NotificationService,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # Register domain services that use the event bus
    container.register(
        interface=PipelineExecutionService,
        implementation=PipelineExecutionService,
        lifetime=ServiceLifetime.SCOPED
    )


async def setup_event_handlers(container: Container) -> None:
    """Set up event handlers with dependency injection.
    
    This function demonstrates how to register event handlers
    that have dependencies injected by the container.
    """
    event_bus = container.resolve(AsyncEventBus)
    metrics_service = container.resolve(MetricsService)
    notification_service = container.resolve(NotificationService)
    
    # Register handlers with dependencies
    await event_bus.register_handler(PipelineMetricsHandler(metrics_service))
    await event_bus.register_handler(NotificationHandler(notification_service))
    await event_bus.register_handler(CompletionMetricsHandler(metrics_service))
    
    # Auto-discover and register decorated handlers
    handler_count = await HandlerDiscovery.discover_and_register(
        event_bus,
        [__name__]  # Discover handlers in this module
    )
    
    print(f"🔧 Registered {handler_count} event handlers")


async def main_example() -> None:
    """Main example demonstrating the complete event system.
    
    This shows how everything works together in a real application.
    """
    print("🚀 WriteIt Event Bus Integration Example")
    print("=" * 50)
    
    # Create and configure container
    container = Container()
    configure_event_system(container)
    
    # Get services from container
    event_bus = container.resolve(AsyncEventBus)
    pipeline_service = container.resolve(PipelineExecutionService)
    
    # Set up event handlers
    await setup_event_handlers(container)
    
    # Start the event bus
    async with event_bus.lifespan():
        print("\n📡 Event bus started, simulating pipeline execution...\n")
        
        # Simulate pipeline execution
        await pipeline_service.start_pipeline(
            pipeline_id="article-generation-001",
            workspace_name="my-blog",
            started_by="user@example.com"
        )
        
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        await pipeline_service.complete_pipeline(
            pipeline_id="article-generation-001",
            workspace_name="my-blog",
            success=True,
            duration=2.34
        )
        
        # Show event bus stats
        stats = event_bus.get_stats()
        print(f"\n📊 Event Bus Stats:")
        print(f"   Handlers registered: {stats['handlers_registered']}")
        print(f"   Failed attempts: {stats['failed_attempts']}")
        print(f"   Dead letter queue: {stats['dead_letter_queue']}")
        
        # Show stored events
        from .event_store import EventQuery
        stored_events = await event_bus.event_store.get_events(EventQuery())
        print(f"\n📚 Stored Events ({len(stored_events)} total):")
        for event in stored_events:
            print(f"   {event.sequence_number}: {event.event_type} - {event.aggregate_id}")
    
    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    # Run the example
    asyncio.run(main_example())
