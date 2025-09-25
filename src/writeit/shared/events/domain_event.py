"""Base domain event class.

Provides the foundation for all domain events in the system."""

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any


class DomainEvent(ABC):
    """Base class for all domain events.
    
    Domain events represent significant business occurrences that
    other parts of the system might be interested in.
    
    All domain events must:
    - Be immutable (frozen dataclass)
    - Have a unique event ID
    - Have a timestamp
    - Implement event_type and aggregate_id properties
    - Be serializable to dictionary
    """
    
    def __init__(self) -> None:
        """Base initialization - subclasses must call super().__init__()"""
        object.__setattr__(self, '_event_id', str(uuid.uuid4()))
        object.__setattr__(self, '_timestamp', datetime.now())
    
    @property
    def event_id(self) -> str:
        """Get the event ID."""
        return self._event_id
    
    @property 
    def timestamp(self) -> datetime:
        """Get the event timestamp.""" 
        return self._timestamp
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Get the event type identifier.
        
        This should be a unique string that identifies the type
        of event (e.g., 'pipeline.created', 'step.completed').
        """
        pass
    
    @property
    @abstractmethod
    def aggregate_id(self) -> str:
        """Get the aggregate root identifier.
        
        This identifies the aggregate that this event relates to
        (e.g., pipeline ID, run ID, etc.).
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization.
        
        Returns:
            Dictionary representation of the event
        """
        pass
    
    def _validate(self) -> None:
        """Validate event after creation."""
        if not self.event_id:
            raise ValueError("Event ID cannot be empty")
        
        if not isinstance(self.timestamp, datetime):
            raise TypeError("Timestamp must be a datetime")
    
    def __str__(self) -> str:
        """String representation."""
        return f"{self.event_type}[{self.event_id[:8]}]"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"{self.__class__.__name__}("
                f"event_id='{self.event_id}', "
                f"event_type='{self.event_type}', "
                f"aggregate_id='{self.aggregate_id}', "
                f"timestamp={self.timestamp})")