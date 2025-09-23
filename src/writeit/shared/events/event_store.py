"""Event store infrastructure.

Provides event persistence for debugging, audit trails, and event replay."""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncIterator
from uuid import uuid4

from .domain_event import DomainEvent


@dataclass(frozen=True)
class StoredEvent:
    """Represents a stored event with metadata."""
    
    sequence_number: int
    event_id: str
    event_type: str
    aggregate_id: str
    event_data: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: datetime
    stored_at: datetime
    
    @classmethod
    def from_domain_event(cls, event: DomainEvent, sequence_number: int, metadata: Optional[Dict[str, Any]] = None) -> 'StoredEvent':
        """Create a stored event from a domain event.
        
        Args:
            event: The domain event to store
            sequence_number: The sequence number for this event
            metadata: Additional metadata to store
            
        Returns:
            StoredEvent instance
        """
        return cls(
            sequence_number=sequence_number,
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_id=event.aggregate_id,
            event_data=event.to_dict(),
            metadata=metadata or {},
            timestamp=event.timestamp,
            stored_at=datetime.now()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        data['timestamp'] = self.timestamp.isoformat()
        data['stored_at'] = self.stored_at.isoformat()
        return data


@dataclass(frozen=True)
class EventQuery:
    """Query parameters for event retrieval."""
    
    aggregate_id: Optional[str] = None
    event_type: Optional[str] = None
    from_sequence: Optional[int] = None
    to_sequence: Optional[int] = None
    from_timestamp: Optional[datetime] = None
    to_timestamp: Optional[datetime] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class EventStore(ABC):
    """Abstract base class for event stores.
    
    Event stores provide persistent storage for domain events,
    enabling audit trails, debugging, and event replay.
    """
    
    @abstractmethod
    async def store(self, event: DomainEvent, metadata: Optional[Dict[str, Any]] = None) -> StoredEvent:
        """Store a domain event.
        
        Args:
            event: The domain event to store
            metadata: Optional metadata to store with the event
            
        Returns:
            The stored event with sequence number
            
        Raises:
            EventStoreError: If storage fails
        """
        pass
    
    @abstractmethod
    async def get_events(self, query: EventQuery) -> List[StoredEvent]:
        """Retrieve events matching the query.
        
        Args:
            query: Query parameters
            
        Returns:
            List of stored events matching the query
            
        Raises:
            EventStoreError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_events_stream(self, query: EventQuery) -> AsyncIterator[StoredEvent]:
        """Stream events matching the query.
        
        Args:
            query: Query parameters
            
        Yields:
            StoredEvent instances matching the query
            
        Raises:
            EventStoreError: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def get_latest_sequence(self) -> int:
        """Get the latest sequence number.
        
        Returns:
            The highest sequence number in the store, or 0 if empty
        """
        pass
    
    @abstractmethod
    async def delete_events(self, query: EventQuery) -> int:
        """Delete events matching the query.
        
        Args:
            query: Query parameters
            
        Returns:
            Number of events deleted
            
        Raises:
            EventStoreError: If deletion fails
        """
        pass


class InMemoryEventStore(EventStore):
    """In-memory event store implementation.
    
    Suitable for testing and development. Events are lost when the process exits.
    """
    
    def __init__(self):
        """Initialize the in-memory store."""
        self._events: List[StoredEvent] = []
        self._sequence_counter = 0
        self._lock = asyncio.Lock()
    
    async def store(self, event: DomainEvent, metadata: Optional[Dict[str, Any]] = None) -> StoredEvent:
        """Store a domain event."""
        async with self._lock:
            self._sequence_counter += 1
            stored_event = StoredEvent.from_domain_event(event, self._sequence_counter, metadata)
            self._events.append(stored_event)
            return stored_event
    
    async def get_events(self, query: EventQuery) -> List[StoredEvent]:
        """Retrieve events matching the query."""
        async with self._lock:
            filtered_events = list(self._filter_events(query))
            
            # Apply offset and limit
            if query.offset:
                filtered_events = filtered_events[query.offset:]
            if query.limit:
                filtered_events = filtered_events[:query.limit]
            
            return filtered_events
    
    async def get_events_stream(self, query: EventQuery) -> AsyncIterator[StoredEvent]:
        """Stream events matching the query."""
        events = await self.get_events(query)
        for event in events:
            yield event
    
    async def get_latest_sequence(self) -> int:
        """Get the latest sequence number."""
        async with self._lock:
            return self._sequence_counter
    
    async def delete_events(self, query: EventQuery) -> int:
        """Delete events matching the query."""
        async with self._lock:
            events_to_delete = list(self._filter_events(query))
            deleted_count = 0
            
            for event in events_to_delete:
                try:
                    self._events.remove(event)
                    deleted_count += 1
                except ValueError:
                    # Event was already removed
                    pass
            
            return deleted_count
    
    def _filter_events(self, query: EventQuery) -> List[StoredEvent]:
        """Filter events based on query parameters."""
        filtered = self._events
        
        if query.aggregate_id:
            filtered = [e for e in filtered if e.aggregate_id == query.aggregate_id]
        
        if query.event_type:
            filtered = [e for e in filtered if e.event_type == query.event_type]
        
        if query.from_sequence is not None:
            filtered = [e for e in filtered if e.sequence_number >= query.from_sequence]
        
        if query.to_sequence is not None:
            filtered = [e for e in filtered if e.sequence_number <= query.to_sequence]
        
        if query.from_timestamp:
            filtered = [e for e in filtered if e.timestamp >= query.from_timestamp]
        
        if query.to_timestamp:
            filtered = [e for e in filtered if e.timestamp <= query.to_timestamp]
        
        return filtered
    
    def __len__(self) -> int:
        """Get the number of stored events."""
        return len(self._events)
    
    def __str__(self) -> str:
        """String representation."""
        return f"InMemoryEventStore(events={len(self._events)}, sequence={self._sequence_counter})"


class EventStoreError(Exception):
    """Base exception for event store operations."""
    pass


class EventStorageError(EventStoreError):
    """Exception raised when event storage fails."""
    pass


class EventRetrievalError(EventStoreError):
    """Exception raised when event retrieval fails."""
    pass
