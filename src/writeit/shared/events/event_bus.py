"""Event bus infrastructure.

Provides asynchronous event publishing and handling with error recovery."""

import asyncio
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Type, Callable, Awaitable
from uuid import uuid4

from .domain_event import DomainEvent
from .event_handler import EventHandler, EventHandlerRegistry
from .event_store import EventStore, InMemoryEventStore, StoredEvent


logger = logging.getLogger(__name__)


@dataclass
class EventPublishResult:
    """Result of publishing an event."""
    
    event: DomainEvent
    handlers_executed: int
    handlers_failed: int
    execution_time: timedelta
    stored_event: Optional[StoredEvent] = None
    errors: List[Exception] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        """Whether the event was published successfully."""
        return self.handlers_failed == 0
    
    @property
    def partial_success(self) -> bool:
        """Whether some handlers succeeded but others failed."""
        return self.handlers_executed > 0 and self.handlers_failed > 0


@dataclass
class RetryPolicy:
    """Policy for retrying failed event handling."""
    
    max_attempts: int = 3
    initial_delay: timedelta = timedelta(seconds=1)
    max_delay: timedelta = timedelta(seconds=60)
    backoff_factor: float = 2.0
    
    def get_delay(self, attempt: int) -> timedelta:
        """Get the delay for a given attempt.
        
        Args:
            attempt: The attempt number (1-based)
            
        Returns:
            The delay before the next attempt
        """
        delay = self.initial_delay.total_seconds() * (self.backoff_factor ** (attempt - 1))
        delay = min(delay, self.max_delay.total_seconds())
        return timedelta(seconds=delay)


@dataclass
class FailedEventAttempt:
    """Represents a failed event handling attempt."""
    
    event: DomainEvent
    handler: EventHandler
    attempt: int
    error: Exception
    timestamp: datetime
    retry_at: Optional[datetime] = None


class CircuitBreaker:
    """Circuit breaker for event handler resilience."""
    
    def __init__(self, failure_threshold: int = 5, timeout: timedelta = timedelta(minutes=1)):
        """Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening the circuit
            timeout: Time to wait before attempting to close the circuit
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = 'closed'  # closed, open, half-open
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable[[], Awaitable[Any]]) -> Any:
        """Execute a function with circuit breaker protection.
        
        Args:
            func: The async function to execute
            
        Returns:
            The result of the function call
            
        Raises:
            CircuitOpenError: If the circuit is open
            Exception: Any exception from the function
        """
        async with self._lock:
            if self.state == 'open':
                if datetime.now() - self.last_failure_time < self.timeout:
                    raise CircuitOpenError("Circuit breaker is open")
                else:
                    self.state = 'half-open'
        
        try:
            result = await func()
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
    
    async def _on_success(self):
        """Handle successful execution."""
        async with self._lock:
            self.failure_count = 0
            self.state = 'closed'
    
    async def _on_failure(self):
        """Handle failed execution."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'open'


class EventBus(ABC):
    """Abstract base class for event buses.
    
    Event buses coordinate the publishing of domain events to registered handlers.
    """
    
    @abstractmethod
    async def publish(self, event: DomainEvent, metadata: Optional[Dict[str, Any]] = None) -> EventPublishResult:
        """Publish an event to all registered handlers.
        
        Args:
            event: The domain event to publish
            metadata: Optional metadata to include
            
        Returns:
            Result of the publish operation
        """
        pass
    
    @abstractmethod
    async def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler.
        
        Args:
            handler: The event handler to register
        """
        pass
    
    @abstractmethod
    async def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler.
        
        Args:
            handler: The event handler to unregister
        """
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start the event bus."""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the event bus."""
        pass


class AsyncEventBus(EventBus):
    """Asynchronous event bus implementation.
    
    Features:
    - Async event handling with concurrent execution
    - Error isolation between handlers
    - Retry logic for failed handlers
    - Circuit breaker protection
    - Event persistence for debugging
    - Dead letter queue for persistently failed events
    """
    
    def __init__(
        self,
        event_store: Optional[EventStore] = None,
        retry_policy: Optional[RetryPolicy] = None,
        max_concurrent_handlers: int = 10,
        enable_circuit_breaker: bool = True
    ):
        """Initialize the event bus.
        
        Args:
            event_store: Optional event store for persistence
            retry_policy: Policy for retrying failed handlers
            max_concurrent_handlers: Maximum concurrent handler executions
            enable_circuit_breaker: Whether to enable circuit breaker protection
        """
        self.event_store = event_store or InMemoryEventStore()
        self.retry_policy = retry_policy or RetryPolicy()
        self.max_concurrent_handlers = max_concurrent_handlers
        self.enable_circuit_breaker = enable_circuit_breaker
        
        self.handler_registry = EventHandlerRegistry()
        self.failed_attempts: List[FailedEventAttempt] = []
        self.dead_letter_queue: List[DomainEvent] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        self._semaphore = asyncio.Semaphore(max_concurrent_handlers)
        self._retry_task: Optional[asyncio.Task] = None
        self._running = False
        self._lock = asyncio.Lock()
    
    async def publish(self, event: DomainEvent, metadata: Optional[Dict[str, Any]] = None) -> EventPublishResult:
        """Publish an event to all registered handlers."""
        start_time = datetime.now()
        
        # Store the event
        stored_event = None
        try:
            stored_event = await self.event_store.store(event, metadata)
            logger.debug(f"Stored event {event.event_id}: {event.event_type}")
        except Exception as e:
            logger.error(f"Failed to store event {event.event_id}: {e}")
        
        # Get handlers for this event type
        handlers = await self.handler_registry.get_handlers(type(event))
        
        if not handlers:
            logger.debug(f"No handlers registered for event type: {event.event_type}")
            return EventPublishResult(
                event=event,
                handlers_executed=0,
                handlers_failed=0,
                execution_time=datetime.now() - start_time,
                stored_event=stored_event
            )
        
        # Execute handlers concurrently
        results = await asyncio.gather(
            *[self._execute_handler(handler, event) for handler in handlers],
            return_exceptions=True
        )
        
        # Process results
        handlers_executed = 0
        handlers_failed = 0
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                handlers_failed += 1
                errors.append(result)
                # Schedule retry
                await self._schedule_retry(handlers[i], event, result)
                logger.warning(f"Handler {handlers[i].__class__.__name__} failed for event {event.event_id}: {result}")
            else:
                handlers_executed += 1
                logger.debug(f"Handler {handlers[i].__class__.__name__} succeeded for event {event.event_id}")
        
        execution_time = datetime.now() - start_time
        
        return EventPublishResult(
            event=event,
            handlers_executed=handlers_executed,
            handlers_failed=handlers_failed,
            execution_time=execution_time,
            stored_event=stored_event,
            errors=errors
        )
    
    async def _execute_handler(self, handler: EventHandler, event: DomainEvent) -> None:
        """Execute a single handler with circuit breaker protection."""
        async with self._semaphore:
            if self.enable_circuit_breaker:
                circuit_breaker = self._get_circuit_breaker(handler)
                await circuit_breaker.call(lambda: handler.handle(event))
            else:
                await handler.handle(event)
    
    def _get_circuit_breaker(self, handler: EventHandler) -> CircuitBreaker:
        """Get or create a circuit breaker for a handler."""
        handler_key = f"{handler.__class__.__module__}.{handler.__class__.__name__}"
        if handler_key not in self.circuit_breakers:
            self.circuit_breakers[handler_key] = CircuitBreaker()
        return self.circuit_breakers[handler_key]
    
    async def _schedule_retry(self, handler: EventHandler, event: DomainEvent, error: Exception) -> None:
        """Schedule a retry for a failed handler."""
        async with self._lock:
            # Count existing attempts for this event/handler combination
            existing_attempts = sum(
                1 for attempt in self.failed_attempts
                if attempt.event.event_id == event.event_id and
                   attempt.handler == handler
            )
            
            if existing_attempts < self.retry_policy.max_attempts:
                delay = self.retry_policy.get_delay(existing_attempts + 1)
                retry_at = datetime.now() + delay
                
                failed_attempt = FailedEventAttempt(
                    event=event,
                    handler=handler,
                    attempt=existing_attempts + 1,
                    error=error,
                    timestamp=datetime.now(),
                    retry_at=retry_at
                )
                
                self.failed_attempts.append(failed_attempt)
                logger.info(f"Scheduled retry {existing_attempts + 1}/{self.retry_policy.max_attempts} for {handler.__class__.__name__} in {delay}")
            else:
                # Move to dead letter queue
                self.dead_letter_queue.append(event)
                logger.error(f"Event {event.event_id} moved to dead letter queue after {self.retry_policy.max_attempts} failed attempts")
    
    async def _process_retries(self) -> None:
        """Background task to process retry attempts."""
        while self._running:
            try:
                now = datetime.now()
                ready_attempts = []
                
                async with self._lock:
                    # Find attempts ready for retry
                    for attempt in self.failed_attempts[:]:
                        if attempt.retry_at and attempt.retry_at <= now:
                            ready_attempts.append(attempt)
                            self.failed_attempts.remove(attempt)
                
                # Execute retries
                for attempt in ready_attempts:
                    try:
                        await self._execute_handler(attempt.handler, attempt.event)
                        logger.info(f"Retry successful for {attempt.handler.__class__.__name__} on attempt {attempt.attempt}")
                    except Exception as e:
                        logger.warning(f"Retry failed for {attempt.handler.__class__.__name__} on attempt {attempt.attempt}: {e}")
                        await self._schedule_retry(attempt.handler, attempt.event, e)
                
                # Sleep before next check
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in retry processing: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def register_handler(self, handler: EventHandler) -> None:
        """Register an event handler."""
        await self.handler_registry.register(handler)
        logger.info(f"Registered handler {handler.__class__.__name__} for event type {handler.event_type.__name__}")
    
    async def unregister_handler(self, handler: EventHandler) -> None:
        """Unregister an event handler."""
        await self.handler_registry.unregister(handler)
        logger.info(f"Unregistered handler {handler.__class__.__name__}")
    
    async def start(self) -> None:
        """Start the event bus."""
        if self._running:
            return
        
        self._running = True
        self._retry_task = asyncio.create_task(self._process_retries())
        logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus."""
        if not self._running:
            return
        
        self._running = False
        
        if self._retry_task:
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event bus stopped")
    
    @asynccontextmanager
    async def lifespan(self):
        """Context manager for event bus lifecycle."""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            'handlers_registered': len(self.handler_registry),
            'failed_attempts': len(self.failed_attempts),
            'dead_letter_queue': len(self.dead_letter_queue),
            'circuit_breakers': len(self.circuit_breakers),
            'running': self._running
        }
    
    def __str__(self) -> str:
        """String representation."""
        stats = self.get_stats()
        return f"AsyncEventBus(handlers={stats['handlers_registered']}, running={stats['running']})"


class CircuitOpenError(Exception):
    """Exception raised when a circuit breaker is open."""
    pass


class EventBusError(Exception):
    """Base exception for event bus operations."""
    pass
