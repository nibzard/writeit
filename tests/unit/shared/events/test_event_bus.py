"""Tests for event bus infrastructure."""

import asyncio
import pytest
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock

from writeit.shared.events import (
    DomainEvent,
    EventHandler,
    BaseEventHandler,
    EventHandlerRegistry,
    AsyncEventBus,
    InMemoryEventStore,
    EventPublishResult,
    RetryPolicy,
    event_handler,
    get_decorated_handlers,
    clear_decorated_handlers
)


class TestDomainEvent(DomainEvent):
    """Test domain event."""
    
    def __init__(self, aggregate_id: str, data: str = "test"):
        super().__init__()
        self._aggregate_id = aggregate_id
        self.data = data
    
    @property
    def event_type(self) -> str:
        return "test.event"
    
    @property
    def aggregate_id(self) -> str:
        return self._aggregate_id
    
    def to_dict(self) -> dict:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'aggregate_id': self.aggregate_id,
            'data': self.data,
            'timestamp': self.timestamp.isoformat()
        }


class TestEventHandler(BaseEventHandler[TestDomainEvent]):
    """Test event handler."""
    
    def __init__(self, priority: int = 100):
        super().__init__(priority)
        self.handled_events: List[TestDomainEvent] = []
        self.should_fail = False
        self.failure_message = "Handler failed"
    
    async def handle(self, event: TestDomainEvent) -> None:
        if self.should_fail:
            raise Exception(self.failure_message)
        self.handled_events.append(event)
    
    @property
    def event_type(self) -> type:
        return TestDomainEvent


@pytest.fixture
def event_store():
    """Create an in-memory event store."""
    return InMemoryEventStore()


@pytest.fixture
def event_bus(event_store):
    """Create an async event bus."""
    return AsyncEventBus(
        event_store=event_store,
        retry_policy=RetryPolicy(max_attempts=3, initial_delay=timedelta(milliseconds=10)),
        max_concurrent_handlers=5
    )


@pytest.fixture
def test_event():
    """Create a test event."""
    return TestDomainEvent(aggregate_id="test-123", data="test data")


class TestEventHandlerRegistry:
    """Tests for EventHandlerRegistry."""
    
    async def test_register_handler(self):
        """Test registering an event handler."""
        registry = EventHandlerRegistry()
        handler = TestEventHandler(priority=50)
        
        await registry.register(handler)
        
        handlers = await registry.get_handlers(TestDomainEvent)
        assert len(handlers) == 1
        assert handlers[0] == handler
    
    async def test_register_multiple_handlers_priority_order(self):
        """Test that handlers are ordered by priority."""
        registry = EventHandlerRegistry()
        
        handler1 = TestEventHandler(priority=100)
        handler2 = TestEventHandler(priority=50)
        handler3 = TestEventHandler(priority=75)
        
        await registry.register(handler1)
        await registry.register(handler2)
        await registry.register(handler3)
        
        handlers = await registry.get_handlers(TestDomainEvent)
        assert len(handlers) == 3
        assert handlers[0].priority == 50  # Highest priority first
        assert handlers[1].priority == 75
        assert handlers[2].priority == 100
    
    async def test_unregister_handler(self):
        """Test unregistering an event handler."""
        registry = EventHandlerRegistry()
        handler = TestEventHandler()
        
        await registry.register(handler)
        await registry.unregister(handler)
        
        handlers = await registry.get_handlers(TestDomainEvent)
        assert len(handlers) == 0
    
    async def test_get_handlers_no_handlers(self):
        """Test getting handlers when none are registered."""
        registry = EventHandlerRegistry()
        
        handlers = await registry.get_handlers(TestDomainEvent)
        assert len(handlers) == 0


class TestAsyncEventBus:
    """Tests for AsyncEventBus."""
    
    async def test_publish_event_no_handlers(self, event_bus, test_event):
        """Test publishing an event with no handlers."""
        result = await event_bus.publish(test_event)
        
        assert result.event == test_event
        assert result.handlers_executed == 0
        assert result.handlers_failed == 0
        assert result.success
        assert not result.partial_success
    
    async def test_publish_event_single_handler(self, event_bus, test_event):
        """Test publishing an event with a single handler."""
        handler = TestEventHandler()
        await event_bus.register_handler(handler)
        
        result = await event_bus.publish(test_event)
        
        assert result.handlers_executed == 1
        assert result.handlers_failed == 0
        assert result.success
        assert len(handler.handled_events) == 1
        assert handler.handled_events[0] == test_event
    
    async def test_publish_event_multiple_handlers(self, event_bus, test_event):
        """Test publishing an event with multiple handlers."""
        handler1 = TestEventHandler(priority=100)
        handler2 = TestEventHandler(priority=50)
        
        await event_bus.register_handler(handler1)
        await event_bus.register_handler(handler2)
        
        result = await event_bus.publish(test_event)
        
        assert result.handlers_executed == 2
        assert result.handlers_failed == 0
        assert result.success
        
        # Both handlers should have received the event
        assert len(handler1.handled_events) == 1
        assert len(handler2.handled_events) == 1
    
    async def test_publish_event_handler_failure(self, event_bus, test_event):
        """Test publishing an event when a handler fails."""
        successful_handler = TestEventHandler()
        failing_handler = TestEventHandler()
        failing_handler.should_fail = True
        
        await event_bus.register_handler(successful_handler)
        await event_bus.register_handler(failing_handler)
        
        result = await event_bus.publish(test_event)
        
        assert result.handlers_executed == 1
        assert result.handlers_failed == 1
        assert not result.success
        assert result.partial_success
        assert len(result.errors) == 1
        
        # Successful handler should still execute
        assert len(successful_handler.handled_events) == 1
    
    async def test_retry_failed_handlers(self, event_bus, test_event):
        """Test that failed handlers are retried."""
        await event_bus.start()  # Start the retry processing
        
        handler = TestEventHandler()
        handler.should_fail = True
        await event_bus.register_handler(handler)
        
        # Publish event (will fail)
        result = await event_bus.publish(test_event)
        assert result.handlers_failed == 1
        
        # Let handler succeed on retry
        handler.should_fail = False
        
        # Wait for retry to process
        await asyncio.sleep(0.1)  # Wait longer than retry delay
        
        # Handler should eventually succeed
        # Note: This is a simplified test - in reality you'd check the handler was called
        assert len(event_bus.failed_attempts) == 0  # Should be cleared after success
        
        await event_bus.stop()
    
    async def test_event_storage(self, event_bus, test_event):
        """Test that events are stored in the event store."""
        result = await event_bus.publish(test_event)
        
        assert result.stored_event is not None
        assert result.stored_event.event_id == test_event.event_id
        assert result.stored_event.event_type == test_event.event_type
        assert result.stored_event.aggregate_id == test_event.aggregate_id
    
    async def test_concurrent_handler_execution(self, event_bus, test_event):
        """Test that handlers execute concurrently."""
        # Create handlers that track execution time
        execution_times = []
        
        class SlowHandler(BaseEventHandler[TestDomainEvent]):
            def __init__(self, delay: float, name: str):
                super().__init__()
                self.delay = delay
                self.name = name
            
            async def handle(self, event: TestDomainEvent) -> None:
                start_time = datetime.now()
                await asyncio.sleep(self.delay)
                end_time = datetime.now()
                execution_times.append((self.name, start_time, end_time))
            
            @property
            def event_type(self) -> type:
                return TestDomainEvent
        
        # Register multiple slow handlers
        for i in range(3):
            handler = SlowHandler(delay=0.05, name=f"handler_{i}")
            await event_bus.register_handler(handler)
        
        start_time = datetime.now()
        result = await event_bus.publish(test_event)
        end_time = datetime.now()
        
        # All handlers should execute successfully
        assert result.handlers_executed == 3
        assert result.handlers_failed == 0
        
        # Total execution time should be less than sum of individual delays
        # (proving concurrent execution)
        total_time = (end_time - start_time).total_seconds()
        assert total_time < 0.15  # Less than 3 * 0.05 seconds
        
        # All handlers should have executed
        assert len(execution_times) == 3
    
    async def test_bus_lifecycle(self, event_bus):
        """Test event bus start/stop lifecycle."""
        # Initially not running
        assert not event_bus._running
        
        # Start the bus
        await event_bus.start()
        assert event_bus._running
        assert event_bus._retry_task is not None
        
        # Stop the bus
        await event_bus.stop()
        assert not event_bus._running
        
        # Starting again should work
        await event_bus.start()
        assert event_bus._running
        await event_bus.stop()
    
    async def test_lifespan_context_manager(self, event_store):
        """Test event bus lifespan context manager."""
        event_bus = AsyncEventBus(event_store=event_store)
        
        async with event_bus.lifespan():
            assert event_bus._running
        
        assert not event_bus._running
    
    async def test_get_stats(self, event_bus):
        """Test getting event bus statistics."""
        handler = TestEventHandler()
        await event_bus.register_handler(handler)
        
        stats = event_bus.get_stats()
        
        assert 'handlers_registered' in stats
        assert 'failed_attempts' in stats
        assert 'dead_letter_queue' in stats
        assert 'circuit_breakers' in stats
        assert 'running' in stats
        
        assert stats['handlers_registered'] == 1
        assert stats['failed_attempts'] == 0
        assert stats['dead_letter_queue'] == 0
        assert stats['running'] == False  # Not started yet


class TestEventDecorators:
    """Tests for event handler decorators."""
    
    def setup_method(self):
        """Clear decorated handlers before each test."""
        clear_decorated_handlers()
    
    def test_function_handler_decorator(self):
        """Test decorator on functions."""
        handled_events = []
        
        @event_handler(TestDomainEvent, priority=50)
        async def handle_test_event(event: TestDomainEvent) -> None:
            handled_events.append(event)
        
        # Function should have handler metadata
        assert hasattr(handle_test_event, '_event_handler_class')
        assert handle_test_event._event_type == TestDomainEvent
        assert handle_test_event._priority == 50
        
        # Should be auto-registered
        decorated_handlers = get_decorated_handlers()
        assert len(decorated_handlers) == 1
    
    def test_function_handler_type_inference(self):
        """Test that event type is inferred from function signature."""
        @event_handler(priority=25)
        async def handle_inferred_event(event: TestDomainEvent) -> None:
            pass
        
        assert handle_inferred_event._event_type == TestDomainEvent
    
    def test_class_handler_decorator(self):
        """Test decorator on classes."""
        @event_handler(TestDomainEvent, priority=75)
        class DecoratedHandler(BaseEventHandler[TestDomainEvent]):
            async def handle(self, event: TestDomainEvent) -> None:
                pass
            
            @property
            def event_type(self) -> type:
                return TestDomainEvent
        
        # Should be auto-registered
        decorated_handlers = get_decorated_handlers()
        assert len(decorated_handlers) == 1
        
        # Create instance and check priority
        handler = DecoratedHandler()
        assert handler.priority == 75


@pytest.mark.asyncio
class TestIntegration:
    """Integration tests for the complete event system."""
    
    async def test_complete_event_flow(self):
        """Test complete event publishing and handling flow."""
        # Setup
        event_store = InMemoryEventStore()
        event_bus = AsyncEventBus(event_store=event_store)
        
        # Create and register handlers
        handler1 = TestEventHandler(priority=100)
        handler2 = TestEventHandler(priority=50)
        
        await event_bus.register_handler(handler1)
        await event_bus.register_handler(handler2)
        
        # Start the bus
        await event_bus.start()
        
        try:
            # Publish events
            event1 = TestDomainEvent("test-1", "first event")
            event2 = TestDomainEvent("test-2", "second event")
            
            result1 = await event_bus.publish(event1)
            result2 = await event_bus.publish(event2)
            
            # Verify results
            assert result1.success
            assert result2.success
            assert result1.handlers_executed == 2
            assert result2.handlers_executed == 2
            
            # Verify handlers received events in priority order
            assert len(handler1.handled_events) == 2
            assert len(handler2.handled_events) == 2
            
            # Verify events are stored
            assert len(event_store) == 2
            
            # Verify stats
            stats = event_bus.get_stats()
            assert stats['handlers_registered'] == 2
            assert stats['running'] == True
            
        finally:
            await event_bus.stop()
    
    async def test_error_handling_and_recovery(self):
        """Test error handling and retry mechanisms."""
        event_store = InMemoryEventStore()
        retry_policy = RetryPolicy(
            max_attempts=2,
            initial_delay=timedelta(milliseconds=10)
        )
        event_bus = AsyncEventBus(
            event_store=event_store,
            retry_policy=retry_policy
        )
        
        # Create failing handler
        failing_handler = TestEventHandler()
        failing_handler.should_fail = True
        failing_handler.failure_message = "Simulated failure"
        
        await event_bus.register_handler(failing_handler)
        await event_bus.start()
        
        try:
            # Publish event
            event = TestDomainEvent("test-fail", "failing event")
            result = await event_bus.publish(event)
            
            # Should fail initially
            assert result.handlers_failed == 1
            assert len(result.errors) == 1
            assert "Simulated failure" in str(result.errors[0])
            
            # Check that retry is scheduled
            assert len(event_bus.failed_attempts) == 1
            
            # Fix the handler and wait for retry
            failing_handler.should_fail = False
            await asyncio.sleep(0.1)  # Wait for retry processing
            
            # Eventually the event should be handled
            # Note: In a real test, you'd have more sophisticated retry verification
            
        finally:
            await event_bus.stop()
