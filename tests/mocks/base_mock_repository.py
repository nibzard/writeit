"""Base mock repository providing common functionality for all mock implementations.

Provides shared state management, error simulation, and behavior configuration
that all domain-specific mock repositories can inherit from.
"""

import uuid
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Callable, Generic
from unittest.mock import Mock
from copy import deepcopy

from writeit.shared.repository import Specification

T = TypeVar('T')


class MockBehaviorConfig:
    """Configuration for mock repository behavior."""
    
    def __init__(self):
        self.error_conditions: Dict[str, Exception] = {}
        self.call_delays: Dict[str, float] = {}
        self.call_counts: Dict[str, int] = defaultdict(int)
        self.state_modifiers: Dict[str, Callable] = {}
        self.return_values: Dict[str, Any] = {}
        
    def set_error_condition(self, method_name: str, exception: Exception) -> None:
        """Set an exception to be raised when method is called."""
        self.error_conditions[method_name] = exception
        
    def clear_error_condition(self, method_name: str) -> None:
        """Clear error condition for a method."""
        self.error_conditions.pop(method_name, None)
        
    def set_call_delay(self, method_name: str, delay_seconds: float) -> None:
        """Set artificial delay for method calls."""
        self.call_delays[method_name] = delay_seconds
        
    def set_return_value(self, method_name: str, value: Any) -> None:
        """Set fixed return value for method."""
        self.return_values[method_name] = value
        
    def get_call_count(self, method_name: str) -> int:
        """Get number of times method was called."""
        return self.call_counts[method_name]
        
    def reset_call_counts(self) -> None:
        """Reset all call counts."""
        self.call_counts.clear()


class BaseMockRepository(Generic[T], ABC):
    """Base class for all mock repository implementations.
    
    Provides common functionality including:
    - In-memory storage with workspace isolation
    - Error condition simulation
    - Call tracking and behavior configuration
    - State persistence across test operations
    """
    
    def __init__(self, workspace_name: Optional[str] = None):
        """Initialize mock repository.
        
        Args:
            workspace_name: Optional workspace for isolation
        """
        self._workspace_name = workspace_name
        self._storage: Dict[str, Dict[Any, T]] = defaultdict(dict)
        self._behavior = MockBehaviorConfig()
        self._event_log: List[Dict[str, Any]] = []
        self._next_id = 1
        
    @property
    def workspace_name(self) -> Optional[str]:
        """Get current workspace name."""
        return self._workspace_name
        
    @property
    def behavior(self) -> MockBehaviorConfig:
        """Get behavior configuration for testing."""
        return self._behavior
        
    @property
    def event_log(self) -> List[Dict[str, Any]]:
        """Get event log for verification."""
        return self._event_log.copy()
        
    def clear_state(self) -> None:
        """Clear all stored data and reset state."""
        self._storage.clear()
        self._event_log.clear()
        self._behavior = MockBehaviorConfig()
        self._next_id = 1
        
    def generate_id(self) -> str:
        """Generate unique ID for entities."""
        entity_id = str(uuid.uuid4())
        return entity_id
        
    def _log_event(self, operation: str, entity_type: str, entity_id: Any = None, **kwargs) -> None:
        """Log repository operation for verification."""
        event = {
            "timestamp": datetime.now(),
            "operation": operation,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "workspace": self._workspace_name,
            **kwargs
        }
        self._event_log.append(event)
        
    async def _check_error_condition(self, method_name: str) -> None:
        """Check if method should raise configured error."""
        if method_name in self._behavior.error_conditions:
            raise self._behavior.error_conditions[method_name]
            
    async def _apply_call_delay(self, method_name: str) -> None:
        """Apply configured delay for method."""
        if method_name in self._behavior.call_delays:
            import asyncio
            await asyncio.sleep(self._behavior.call_delays[method_name])
            
    def _increment_call_count(self, method_name: str) -> None:
        """Increment call count for method."""
        self._behavior.call_counts[method_name] += 1
        
    def _get_workspace_storage(self, workspace: Optional[str] = None) -> Dict[Any, T]:
        """Get storage dict for specific workspace."""
        target_workspace = workspace or self._workspace_name or "default"
        return self._storage[target_workspace]
        
    def _store_entity(self, entity: T, entity_id: Any, workspace: Optional[str] = None) -> None:
        """Store entity in workspace-specific storage."""
        storage = self._get_workspace_storage(workspace)
        storage[entity_id] = deepcopy(entity)
        
    def _get_entity(self, entity_id: Any, workspace: Optional[str] = None) -> Optional[T]:
        """Get entity from workspace-specific storage."""
        storage = self._get_workspace_storage(workspace)
        entity = storage.get(entity_id)
        return deepcopy(entity) if entity else None
        
    def _get_all_entities(self, workspace: Optional[str] = None) -> List[T]:
        """Get all entities from workspace-specific storage."""
        storage = self._get_workspace_storage(workspace)
        return [deepcopy(entity) for entity in storage.values()]
        
    def _delete_entity(self, entity_id: Any, workspace: Optional[str] = None) -> bool:
        """Delete entity from workspace-specific storage."""
        storage = self._get_workspace_storage(workspace)
        if entity_id in storage:
            del storage[entity_id]
            return True
        return False
        
    def _find_entities_by_specification(
        self, 
        spec: Specification[T], 
        workspace: Optional[str] = None
    ) -> List[T]:
        """Find entities matching specification."""
        entities = self._get_all_entities(workspace)
        return [entity for entity in entities if spec.is_satisfied_by(entity)]
        
    def _count_entities(self, workspace: Optional[str] = None) -> int:
        """Count entities in workspace."""
        storage = self._get_workspace_storage(workspace)
        return len(storage)
        
    def _entity_exists(self, entity_id: Any, workspace: Optional[str] = None) -> bool:
        """Check if entity exists in workspace."""
        storage = self._get_workspace_storage(workspace)
        return entity_id in storage
        
    # Abstract methods that subclasses must implement
    @abstractmethod
    def _get_entity_id(self, entity: T) -> Any:
        """Extract entity ID from entity object."""
        pass
        
    @abstractmethod 
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        pass


class MockRepositoryError(Exception):
    """Exception raised by mock repositories for testing error conditions."""
    pass


class MockEntityNotFoundError(MockRepositoryError):
    """Mock version of EntityNotFoundError."""
    
    def __init__(self, entity_type: str, entity_id: Any):
        super().__init__(f"Mock {entity_type} with id '{entity_id}' not found")
        self.entity_type = entity_type
        self.entity_id = entity_id


class MockEntityAlreadyExistsError(MockRepositoryError):
    """Mock version of EntityAlreadyExistsError."""
    
    def __init__(self, entity_type: str, entity_id: Any):
        super().__init__(f"Mock {entity_type} with id '{entity_id}' already exists")
        self.entity_type = entity_type
        self.entity_id = entity_id