"""Event handler infrastructure.

Provides interfaces and base classes for event handlers."""

import asyncio
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, Protocol, runtime_checkable
from .domain_event import DomainEvent


T = TypeVar('T', bound=DomainEvent)


@runtime_checkable
class EventHandler(Generic[T], Protocol):
    """Protocol for event handlers.
    
    Event handlers are responsible for responding to domain events.
    They should be focused, fast, and fault-tolerant.
    """
    
    async def handle(self, event: T) -> None:
        """Handle the given event.
        
        Args:
            event: The domain event to handle
            
        Raises:
            Exception: Any exception that occurs during handling
        """
        ...
    
    @property
    def event_type(self) -> Type[T]:
        """Get the type of event this handler processes."""
        ...
    
    @property
    def priority(self) -> int:
        """Get the handler priority (lower numbers = higher priority)."""
        ...


class BaseEventHandler(ABC, Generic[T]):
    """Base class for event handlers.
    
    Provides common functionality and ensures proper interface implementation.
    """
    
    def __init__(self, priority: int = 100):
        """Initialize the handler.
        
        Args:
            priority: Handler priority (lower = higher priority)
        """
        self._priority = priority
    
    @abstractmethod
    async def handle(self, event: T) -> None:
        """Handle the given event.
        
        Args:
            event: The domain event to handle
        """
        pass
    
    @property
    @abstractmethod
    def event_type(self) -> Type[T]:
        """Get the type of event this handler processes."""
        pass
    
    @property
    def priority(self) -> int:
        """Get the handler priority."""
        return self._priority
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(priority={self.priority})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"{self.__class__.__name__}("
                f"event_type={self.event_type.__name__}, "
                f"priority={self.priority})")


class EventHandlerRegistry:
    """Registry for event handlers.
    
    Manages the registration and lookup of event handlers by event type.
    """
    
    def __init__(self):
        """Initialize the registry."""
        self._handlers: dict[Type[DomainEvent], list[EventHandler]] = {}
        self._lock = asyncio.Lock()
    
    async def register(self, handler: EventHandler) -> None:
        """Register an event handler.
        
        Args:
            handler: The event handler to register
        """
        async with self._lock:
            event_type = handler.event_type
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            # Insert handler in priority order (lower priority number = higher priority)
            handlers = self._handlers[event_type]
            insert_index = 0
            for i, existing_handler in enumerate(handlers):
                if handler.priority < existing_handler.priority:
                    insert_index = i
                    break
                insert_index = i + 1
            
            handlers.insert(insert_index, handler)
    
    async def unregister(self, handler: EventHandler) -> None:
        """Unregister an event handler.
        
        Args:
            handler: The event handler to unregister
        """
        async with self._lock:
            event_type = handler.event_type
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                    # Clean up empty lists
                    if not self._handlers[event_type]:
                        del self._handlers[event_type]
                except ValueError:
                    # Handler wasn't registered
                    pass
    
    async def get_handlers(self, event_type: Type[DomainEvent]) -> list[EventHandler]:
        """Get handlers for an event type.
        
        Args:
            event_type: The event type to get handlers for
            
        Returns:
            List of handlers in priority order
        """
        async with self._lock:
            return list(self._handlers.get(event_type, []))
    
    async def get_all_handlers(self) -> dict[Type[DomainEvent], list[EventHandler]]:
        """Get all registered handlers.
        
        Returns:
            Dictionary mapping event types to their handlers
        """
        async with self._lock:
            return {event_type: list(handlers) for event_type, handlers in self._handlers.items()}
    
    def __len__(self) -> int:
        """Get the number of registered event types."""
        return len(self._handlers)
    
    def __str__(self) -> str:
        """String representation."""
        total_handlers = sum(len(handlers) for handlers in self._handlers.values())
        return f"EventHandlerRegistry(types={len(self._handlers)}, handlers={total_handlers})"
