"""Event system testing utilities.

Provides helpers for testing domain events, event handlers, event bus functionality,
and event sourcing patterns in WriteIt's domain-driven architecture.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import List, Type, Optional, Dict, Any, Callable, AsyncGenerator
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timedelta
import pytest

from writeit.shared.events import (
    DomainEvent,
    EventHandler,
    BaseEventHandler,
    AsyncEventBus,
    InMemoryEventStore,
    EventPublishResult,
    RetryPolicy
)


class EventCapture:
    """Captures events for testing purposes."""
    
    def __init__(self):
        self.captured_events: List[DomainEvent] = []
        self.capture_enabled = True
    
    def capture_event(self, event: DomainEvent) -> None:
        """Capture an event if capture is enabled."""
        if self.capture_enabled:
            self.captured_events.append(event)
    
    def get_events_of_type(self, event_type: Type[DomainEvent]) -> List[DomainEvent]:
        """Get all captured events of a specific type."""
        return [event for event in self.captured_events if isinstance(event, event_type)]
    
    def get_events_for_aggregate(self, aggregate_id: str) -> List[DomainEvent]:
        """Get all captured events for a specific aggregate."""
        return [event for event in self.captured_events if event.aggregate_id == aggregate_id]
    
    def clear(self) -> None:
        """Clear all captured events."""
        self.captured_events.clear()
    
    def enable_capture(self) -> None:
        """Enable event capture."""
        self.capture_enabled = True
    
    def disable_capture(self) -> None:
        """Disable event capture."""
        self.capture_enabled = False
    
    @property
    def event_count(self) -> int:
        """Get total number of captured events."""
        return len(self.captured_events)


class MockEventHandler(BaseEventHandler):
    """Mock event handler for testing."""
    
    def __init__(self, event_type: Type[DomainEvent], priority: int = 100):
        super().__init__(priority)
        self._event_type = event_type
        self.handled_events: List[DomainEvent] = []
        self.handle_count = 0
        self.should_fail = False
        self.failure_message = "Mock handler failure"
        self.handle_delay = 0.0  # Artificial delay for testing
    
    async def handle(self, event: DomainEvent) -> None:
        """Handle an event (mock implementation)."""
        if self.handle_delay > 0:
            await asyncio.sleep(self.handle_delay)
        
        if self.should_fail:
            raise Exception(self.failure_message)
        
        self.handled_events.append(event)
        self.handle_count += 1
    
    @property
    def event_type(self) -> Type[DomainEvent]:
        """Return the event type this handler processes."""
        return self._event_type
    
    def reset(self) -> None:
        """Reset handler state."""
        self.handled_events.clear()
        self.handle_count = 0
        self.should_fail = False


class EventTestHelper:
    """Helper class for event testing scenarios."""
    
    def __init__(self):
        self.event_capture = EventCapture()
        self.mock_handlers: Dict[Type[DomainEvent], List[MockEventHandler]] = {}
        self.event_bus: Optional[AsyncEventBus] = None
    
    def create_mock_handler(
        self, 
        event_type: Type[DomainEvent], 
        priority: int = 100
    ) -> MockEventHandler:
        """Create a mock event handler for testing."""
        handler = MockEventHandler(event_type, priority)
        
        if event_type not in self.mock_handlers:
            self.mock_handlers[event_type] = []
        self.mock_handlers[event_type].append(handler)
        
        return handler
    
    async def setup_event_bus(
        self,
        retry_policy: Optional[RetryPolicy] = None,
        max_concurrent_handlers: int = 5
    ) -> AsyncEventBus:
        """Set up event bus for testing."""
        if retry_policy is None:
            retry_policy = RetryPolicy(
                max_attempts=2,
                initial_delay=timedelta(milliseconds=10),
                max_delay=timedelta(milliseconds=100)
            )
        
        event_store = InMemoryEventStore()
        self.event_bus = AsyncEventBus(
            event_store=event_store,
            retry_policy=retry_policy,
            max_concurrent_handlers=max_concurrent_handlers
        )
        
        await self.event_bus.start()
        return self.event_bus
    
    async def cleanup(self) -> None:
        """Clean up test resources."""
        if self.event_bus:
            await self.event_bus.stop()
            self.event_bus = None
        self.mock_handlers.clear()
        self.event_capture.clear()
    
    async def register_handlers(self) -> None:
        """Register all mock handlers with the event bus."""
        if not self.event_bus:
            raise RuntimeError("Event bus not set up. Call setup_event_bus() first.")
        
        for handlers in self.mock_handlers.values():
            for handler in handlers:
                await self.event_bus.register_handler(handler)
    
    def get_handlers_for_type(self, event_type: Type[DomainEvent]) -> List[MockEventHandler]:
        """Get all mock handlers for a specific event type."""
        return self.mock_handlers.get(event_type, [])


@asynccontextmanager
async def capture_events(event_types: Optional[List[Type[DomainEvent]]] = None) -> AsyncGenerator[EventCapture, None]:
    """Context manager to capture events during testing.
    
    Args:
        event_types: Optional list of event types to capture (captures all if None)
    
    Usage:
        async with capture_events([UserCreated, UserUpdated]) as capture:
            # Perform operations that generate events
            await user_service.create_user(user_data)
            
            # Check captured events
            assert capture.event_count == 1
            user_events = capture.get_events_of_type(UserCreated)
            assert len(user_events) == 1
    """
    capture = EventCapture()
    
    try:
        yield capture
    finally:
        # Cleanup is handled by the capture object itself
        pass


async def assert_event_published(
    event_bus: AsyncEventBus,
    expected_event_type: Type[DomainEvent],
    aggregate_id: Optional[str] = None,
    timeout: float = 2.0
) -> DomainEvent:
    """Assert that an event of a specific type was published.
    
    Args:
        event_bus: The event bus to check
        expected_event_type: The type of event expected
        aggregate_id: Optional aggregate ID to match
        timeout: Maximum time to wait for the event
    
    Returns:
        The published event
    
    Raises:
        AssertionError: If event is not found within timeout
    """
    start_time = datetime.now()
    
    while (datetime.now() - start_time).total_seconds() < timeout:
        # Check event store for the event
        if hasattr(event_bus.event_store, 'events'):
            for stored_event in event_bus.event_store.events:
                if (stored_event.event_type == expected_event_type.__name__ and
                    (aggregate_id is None or stored_event.aggregate_id == aggregate_id)):
                    return stored_event
        
        await asyncio.sleep(0.1)
    
    raise AssertionError(
        f"Event {expected_event_type.__name__} "
        f"{'for aggregate ' + aggregate_id if aggregate_id else ''} "
        f"not published within {timeout} seconds"
    )


async def wait_for_event(
    event_bus: AsyncEventBus,
    event_type: Type[DomainEvent],
    condition: Optional[Callable[[DomainEvent], bool]] = None,
    timeout: float = 5.0
) -> DomainEvent:
    """Wait for a specific event to be published.
    
    Args:
        event_bus: The event bus to monitor
        event_type: The type of event to wait for
        condition: Optional condition function to filter events
        timeout: Maximum time to wait
    
    Returns:
        The event that matches the criteria
    
    Raises:
        asyncio.TimeoutError: If event is not found within timeout
    """
    start_time = datetime.now()
    
    while (datetime.now() - start_time).total_seconds() < timeout:
        if hasattr(event_bus.event_store, 'events'):
            for stored_event in event_bus.event_store.events:
                if (stored_event.event_type == event_type.__name__ and
                    (condition is None or condition(stored_event))):
                    return stored_event
        
        await asyncio.sleep(0.1)
    
    raise asyncio.TimeoutError(
        f"Event {event_type.__name__} not found within {timeout} seconds"
    )


async def wait_for_handler_execution(
    handler: MockEventHandler,
    expected_count: int = 1,
    timeout: float = 2.0
) -> None:
    """Wait for a handler to process a specific number of events.
    
    Args:
        handler: The mock handler to monitor
        expected_count: Expected number of handled events
        timeout: Maximum time to wait
    
    Raises:
        asyncio.TimeoutError: If handler doesn't process expected events
    """
    start_time = datetime.now()
    
    while (datetime.now() - start_time).total_seconds() < timeout:
        if handler.handle_count >= expected_count:
            return
        await asyncio.sleep(0.1)
    
    raise asyncio.TimeoutError(
        f"Handler did not process {expected_count} events within {timeout} seconds. "
        f"Actual count: {handler.handle_count}"
    )


class EventSequenceValidator:
    """Validates event sequences and ordering."""
    
    def __init__(self):
        self.events: List[DomainEvent] = []
    
    def add_event(self, event: DomainEvent) -> None:
        """Add an event to the sequence."""
        self.events.append(event)
    
    def validate_sequence(self, expected_types: List[Type[DomainEvent]]) -> None:
        """Validate that events occurred in the expected sequence.
        
        Args:
            expected_types: List of event types in expected order
        
        Raises:
            AssertionError: If sequence doesn't match
        """
        if len(self.events) != len(expected_types):
            raise AssertionError(
                f"Expected {len(expected_types)} events, got {len(self.events)}"
            )
        
        for i, (event, expected_type) in enumerate(zip(self.events, expected_types)):
            if not isinstance(event, expected_type):
                raise AssertionError(
                    f"Event {i}: expected {expected_type.__name__}, "
                    f"got {type(event).__name__}"
                )
    
    def validate_timing(self, max_interval: timedelta = timedelta(seconds=1)) -> None:
        """Validate that events occurred within expected time intervals.
        
        Args:
            max_interval: Maximum allowed interval between consecutive events
        
        Raises:
            AssertionError: If timing is outside acceptable bounds
        """
        for i in range(1, len(self.events)):
            interval = self.events[i].timestamp - self.events[i-1].timestamp
            if interval > max_interval:
                raise AssertionError(
                    f"Events {i-1} and {i} have interval {interval}, "
                    f"exceeds maximum {max_interval}"
                )
    
    def clear(self) -> None:
        """Clear the event sequence."""
        self.events.clear()


def create_test_event(
    event_type: Type[DomainEvent],
    aggregate_id: str = "test-aggregate",
    **kwargs
) -> DomainEvent:
    """Create a test event instance.
    
    Args:
        event_type: The type of event to create
        aggregate_id: The aggregate ID for the event
        **kwargs: Additional event-specific parameters
    
    Returns:
        Test event instance
    """
    # This is a generic factory - specific event types may need custom handling
    if hasattr(event_type, 'create_for_testing'):
        return event_type.create_for_testing(aggregate_id=aggregate_id, **kwargs)
    else:
        # Try to instantiate with common parameters
        try:
            return event_type(aggregate_id=aggregate_id, **kwargs)
        except TypeError as e:
            raise ValueError(
                f"Cannot create test event of type {event_type.__name__}. "
                f"Consider implementing 'create_for_testing' class method. Error: {e}"
            )


class EventBusTestDouble:
    """Test double for event bus that captures events without processing."""
    
    def __init__(self):
        self.published_events: List[DomainEvent] = []
        self.handlers: Dict[Type[DomainEvent], List[EventHandler]] = {}
    
    async def publish(self, event: DomainEvent) -> EventPublishResult:
        """Capture published event without processing."""
        self.published_events.append(event)
        
        # Return mock result
        return EventPublishResult(
            event=event,
            handlers_executed=0,
            handlers_failed=0,
            errors=[],
            stored_event=event
        )
    
    async def register_handler(self, handler: EventHandler) -> None:
        """Register handler (for compatibility)."""
        event_type = handler.event_type
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def get_published_events(self, event_type: Optional[Type[DomainEvent]] = None) -> List[DomainEvent]:
        """Get published events, optionally filtered by type."""
        if event_type is None:
            return self.published_events.copy()
        return [event for event in self.published_events if isinstance(event, event_type)]
    
    def clear_published_events(self) -> None:
        """Clear all published events."""
        self.published_events.clear()


@pytest.fixture
def event_test_helper():
    """Provide event test helper."""
    helper = EventTestHelper()
    yield helper
    # Cleanup will be handled by test teardown