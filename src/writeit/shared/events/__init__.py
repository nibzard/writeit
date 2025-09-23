"""Shared events module.

Contains base classes and utilities for domain events."""

from .domain_event import DomainEvent
from .event_handler import EventHandler, BaseEventHandler, EventHandlerRegistry
from .event_store import EventStore, InMemoryEventStore, StoredEvent, EventQuery, EventStoreError
from .event_bus import EventBus, AsyncEventBus, EventPublishResult, RetryPolicy, CircuitBreaker, EventBusError
from .decorators import event_handler, get_decorated_handlers, auto_discover_handlers, HandlerDiscovery

__all__ = [
    # Base classes
    "DomainEvent",
    
    # Event handlers
    "EventHandler",
    "BaseEventHandler", 
    "EventHandlerRegistry",
    
    # Event store
    "EventStore",
    "InMemoryEventStore",
    "StoredEvent",
    "EventQuery",
    "EventStoreError",
    
    # Event bus
    "EventBus",
    "AsyncEventBus",
    "EventPublishResult",
    "RetryPolicy",
    "CircuitBreaker",
    "EventBusError",
    
    # Decorators and discovery
    "event_handler",
    "get_decorated_handlers",
    "auto_discover_handlers",
    "HandlerDiscovery",
]