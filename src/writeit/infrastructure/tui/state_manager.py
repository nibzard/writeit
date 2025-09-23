"""TUI State Manager for interface state management.

Provides centralized state management for TUI applications with
reactive state updates, state persistence, and undo/redo functionality.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, TypeVar, Generic, Union
from enum import Enum
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from copy import deepcopy

from ...shared.events.bus import EventBus
from .context import TUIContextManager, TUIContext
from .event_handler import TUIEventBus, UIStateChangeEvent

logger = logging.getLogger(__name__)

T = TypeVar('T')


class StateChangeType(str, Enum):
    """Types of state changes."""
    SET = "set"
    UPDATE = "update"
    DELETE = "delete"
    RESET = "reset"
    MERGE = "merge"


@dataclass
class StateChange:
    """Represents a state change operation."""
    
    key: str
    change_type: StateChangeType
    old_value: Any = None
    new_value: Any = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def apply_to_state(self, state: Dict[str, Any]) -> None:
        """Apply this change to a state dictionary."""
        if self.change_type == StateChangeType.SET:
            state[self.key] = self.new_value
        elif self.change_type == StateChangeType.UPDATE and isinstance(self.new_value, dict):
            if self.key not in state:
                state[self.key] = {}
            if isinstance(state[self.key], dict):
                state[self.key].update(self.new_value)
            else:
                state[self.key] = self.new_value
        elif self.change_type == StateChangeType.DELETE:
            state.pop(self.key, None)
        elif self.change_type == StateChangeType.MERGE and isinstance(self.new_value, dict):
            if self.key not in state:
                state[self.key] = {}
            if isinstance(state[self.key], dict):
                state[self.key] = {**state[self.key], **self.new_value}
            else:
                state[self.key] = self.new_value
    
    def reverse(self) -> StateChange:
        """Create a reverse state change to undo this change."""
        if self.change_type == StateChangeType.SET:
            if self.old_value is None:
                return StateChange(
                    key=self.key,
                    change_type=StateChangeType.DELETE,
                    old_value=self.new_value,
                    new_value=None
                )
            else:
                return StateChange(
                    key=self.key,
                    change_type=StateChangeType.SET,
                    old_value=self.new_value,
                    new_value=self.old_value
                )
        elif self.change_type == StateChangeType.DELETE:
            return StateChange(
                key=self.key,
                change_type=StateChangeType.SET,
                old_value=None,
                new_value=self.old_value
            )
        # For UPDATE and MERGE, reversal is more complex and depends on the specific case
        return StateChange(
            key=self.key,
            change_type=StateChangeType.SET,
            old_value=self.new_value,
            new_value=self.old_value
        )


class StateSubscription:
    """Represents a subscription to state changes."""
    
    def __init__(
        self,
        key_pattern: str,
        callback: Callable[[str, Any, Any], None],
        immediate: bool = True
    ):
        self.key_pattern = key_pattern
        self.callback = callback
        self.immediate = immediate
        self.active = True
    
    def matches(self, key: str) -> bool:
        """Check if this subscription matches the given key."""
        if self.key_pattern == "*":
            return True
        elif self.key_pattern.endswith("*"):
            prefix = self.key_pattern[:-1]
            return key.startswith(prefix)
        else:
            return key == self.key_pattern
    
    def notify(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify subscriber of state change."""
        if self.active:
            try:
                self.callback(key, old_value, new_value)
            except Exception as e:
                logger.error(f"State subscription callback error: {e}", exc_info=True)
    
    def unsubscribe(self) -> None:
        """Unsubscribe from state changes."""
        self.active = False


class TUIState:
    """Reactive state container for TUI applications."""
    
    def __init__(self, initial_state: Optional[Dict[str, Any]] = None):
        self._state: Dict[str, Any] = initial_state or {}
        self._subscriptions: List[StateSubscription] = []
        self._change_history: List[StateChange] = []
        self._undo_stack: List[StateChange] = []
        self._redo_stack: List[StateChange] = []
        self._max_history = 100
        
        # State metadata
        self._locked_keys: set[str] = set()
        self._computed_keys: Dict[str, Callable[[], Any]] = {}
        self._validators: Dict[str, Callable[[Any], bool]] = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get state value by key."""
        if key in self._computed_keys:
            return self._computed_keys[key]()
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Set state value by key."""
        if key in self._locked_keys:
            logger.warning(f"Attempted to set locked key: {key}")
            return False
        
        # Validate value if validator exists
        if key in self._validators and not self._validators[key](value):
            logger.warning(f"Validation failed for key {key} with value {value}")
            return False
        
        old_value = self._state.get(key)
        
        # Create state change
        change = StateChange(
            key=key,
            change_type=StateChangeType.SET,
            old_value=deepcopy(old_value),
            new_value=deepcopy(value),
            metadata=metadata or {}
        )
        
        # Apply change
        self._apply_change(change)
        return True
    
    def update(self, key: str, updates: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update state value (for dict values)."""
        if key in self._locked_keys:
            logger.warning(f"Attempted to update locked key: {key}")
            return False
        
        old_value = self._state.get(key)
        
        change = StateChange(
            key=key,
            change_type=StateChangeType.UPDATE,
            old_value=deepcopy(old_value),
            new_value=deepcopy(updates),
            metadata=metadata or {}
        )
        
        self._apply_change(change)
        return True
    
    def delete(self, key: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Delete state value by key."""
        if key in self._locked_keys:
            logger.warning(f"Attempted to delete locked key: {key}")
            return False
        
        if key not in self._state:
            return False
        
        old_value = self._state[key]
        
        change = StateChange(
            key=key,
            change_type=StateChangeType.DELETE,
            old_value=deepcopy(old_value),
            new_value=None,
            metadata=metadata or {}
        )
        
        self._apply_change(change)
        return True
    
    def merge(self, key: str, values: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Merge values into existing dict state."""
        if key in self._locked_keys:
            logger.warning(f"Attempted to merge locked key: {key}")
            return False
        
        old_value = self._state.get(key)
        
        change = StateChange(
            key=key,
            change_type=StateChangeType.MERGE,
            old_value=deepcopy(old_value),
            new_value=deepcopy(values),
            metadata=metadata or {}
        )
        
        self._apply_change(change)
        return True
    
    def reset(self, initial_state: Optional[Dict[str, Any]] = None) -> None:
        """Reset state to initial or provided state."""
        old_state = deepcopy(self._state)
        new_state = initial_state or {}
        
        # Clear current state
        self._state.clear()
        self._state.update(new_state)
        
        # Notify all subscribers
        for key in set(list(old_state.keys()) + list(new_state.keys())):
            old_value = old_state.get(key)
            new_value = new_state.get(key)
            if old_value != new_value:
                self._notify_subscribers(key, old_value, new_value)
        
        # Clear history
        self._change_history.clear()
        self._undo_stack.clear()
        self._redo_stack.clear()
    
    def _apply_change(self, change: StateChange) -> None:
        """Apply a state change and manage history."""
        # Store old value for undo
        old_value = self._state.get(change.key)
        
        # Apply change
        change.apply_to_state(self._state)
        
        # Add to history
        self._change_history.append(change)
        if len(self._change_history) > self._max_history:
            self._change_history.pop(0)
        
        # Add to undo stack
        self._undo_stack.append(change)
        
        # Clear redo stack (new change invalidates redo)
        self._redo_stack.clear()
        
        # Notify subscribers
        new_value = self._state.get(change.key)
        self._notify_subscribers(change.key, old_value, new_value)
    
    def _notify_subscribers(self, key: str, old_value: Any, new_value: Any) -> None:
        """Notify subscribers of state change."""
        for subscription in self._subscriptions:
            if subscription.matches(key):
                subscription.notify(key, old_value, new_value)
    
    def subscribe(
        self, 
        key_pattern: str, 
        callback: Callable[[str, Any, Any], None],
        immediate: bool = True
    ) -> StateSubscription:
        """Subscribe to state changes."""
        subscription = StateSubscription(key_pattern, callback, immediate)
        self._subscriptions.append(subscription)
        
        # Immediate notification for existing values
        if immediate:
            if key_pattern == "*":
                for key, value in self._state.items():
                    subscription.notify(key, None, value)
            elif key_pattern in self._state:
                subscription.notify(key_pattern, None, self._state[key_pattern])
        
        return subscription
    
    def unsubscribe(self, subscription: StateSubscription) -> None:
        """Remove a subscription."""
        subscription.unsubscribe()
        if subscription in self._subscriptions:
            self._subscriptions.remove(subscription)
    
    def lock_key(self, key: str) -> None:
        """Lock a key to prevent modifications."""
        self._locked_keys.add(key)
    
    def unlock_key(self, key: str) -> None:
        """Unlock a key to allow modifications."""
        self._locked_keys.discard(key)
    
    def add_computed_key(self, key: str, compute_func: Callable[[], Any]) -> None:
        """Add a computed state key."""
        self._computed_keys[key] = compute_func
    
    def add_validator(self, key: str, validator: Callable[[Any], bool]) -> None:
        """Add a validator for a state key."""
        self._validators[key] = validator
    
    def can_undo(self) -> bool:
        """Check if undo is possible."""
        return len(self._undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible."""
        return len(self._redo_stack) > 0
    
    def undo(self) -> bool:
        """Undo the last state change."""
        if not self.can_undo():
            return False
        
        # Get last change
        last_change = self._undo_stack.pop()
        
        # Create reverse change
        reverse_change = last_change.reverse()
        
        # Apply reverse change (without adding to undo stack)
        old_value = self._state.get(reverse_change.key)
        reverse_change.apply_to_state(self._state)
        new_value = self._state.get(reverse_change.key)
        
        # Add to redo stack
        self._redo_stack.append(last_change)
        
        # Notify subscribers
        self._notify_subscribers(reverse_change.key, old_value, new_value)
        
        return True
    
    def redo(self) -> bool:
        """Redo the last undone state change."""
        if not self.can_redo():
            return False
        
        # Get change to redo
        change_to_redo = self._redo_stack.pop()
        
        # Apply change (without adding to undo stack initially)
        old_value = self._state.get(change_to_redo.key)
        change_to_redo.apply_to_state(self._state)
        new_value = self._state.get(change_to_redo.key)
        
        # Add back to undo stack
        self._undo_stack.append(change_to_redo)
        
        # Notify subscribers
        self._notify_subscribers(change_to_redo.key, old_value, new_value)
        
        return True
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get a deep copy of current state."""
        return deepcopy(self._state)
    
    def get_change_history(self) -> List[StateChange]:
        """Get the change history."""
        return self._change_history.copy()


class TUIStateManager:
    """Manages multiple TUI states with persistence and workspace awareness."""
    
    def __init__(
        self, 
        event_bus: Optional[TUIEventBus] = None,
        persistence_dir: Optional[Path] = None
    ):
        self.event_bus = event_bus
        self.persistence_dir = persistence_dir or Path.home() / ".writeit" / "tui_state"
        
        # State storage
        self._states: Dict[str, TUIState] = {}
        self._global_state = TUIState()
        
        # Default states
        self._initialize_default_states()
        
        # Auto-save settings
        self._auto_save_enabled = True
        self._save_interval = 30  # seconds
        self._save_task: Optional[asyncio.Task] = None
    
    def _initialize_default_states(self) -> None:
        """Initialize default application states."""
        # UI state
        ui_state = TUIState({
            "theme": "default",
            "dark_mode": True,
            "show_debug": False,
            "keyboard_shortcuts_enabled": True,
            "font_size": "medium",
            "animation_enabled": True
        })
        self._states["ui"] = ui_state
        
        # Navigation state
        nav_state = TUIState({
            "current_mode": "pipeline",
            "current_screen": "home",
            "history": [],
            "breadcrumbs": []
        })
        self._states["navigation"] = nav_state
        
        # Pipeline state
        pipeline_state = TUIState({
            "current_pipeline_id": None,
            "current_step": None,
            "execution_state": "idle",
            "step_results": {},
            "user_inputs": {},
            "selected_responses": {}
        })
        self._states["pipeline"] = pipeline_state
        
        # Workspace state
        workspace_state = TUIState({
            "current_workspace": "default",
            "available_workspaces": [],
            "workspace_configs": {},
            "recent_workspaces": []
        })
        self._states["workspace"] = workspace_state
        
        # Template state
        template_state = TUIState({
            "current_template": None,
            "template_list": [],
            "template_cache": {},
            "recent_templates": []
        })
        self._states["template"] = template_state
    
    def get_state(self, state_name: str) -> Optional[TUIState]:
        """Get a named state."""
        return self._states.get(state_name)
    
    def get_or_create_state(self, state_name: str, initial_state: Optional[Dict[str, Any]] = None) -> TUIState:
        """Get or create a named state."""
        if state_name not in self._states:
            self._states[state_name] = TUIState(initial_state)
        return self._states[state_name]
    
    def get_global_state(self) -> TUIState:
        """Get the global state."""
        return self._global_state
    
    def get_workspace_state(self, workspace_name: str) -> TUIState:
        """Get workspace-specific state."""
        workspace_key = f"workspace_{workspace_name}"
        return self.get_or_create_state(workspace_key)
    
    def delete_state(self, state_name: str) -> bool:
        """Delete a named state."""
        if state_name in self._states:
            del self._states[state_name]
            return True
        return False
    
    def save_state(self, state_name: Optional[str] = None) -> bool:
        """Save state(s) to disk."""
        if not self.persistence_dir:
            return False
        
        try:
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
            
            if state_name:
                # Save specific state
                state = self._states.get(state_name)
                if state:
                    file_path = self.persistence_dir / f"{state_name}.json"
                    with open(file_path, 'w') as f:
                        json.dump(state.get_state_snapshot(), f, indent=2, default=str)
                    return True
            else:
                # Save all states
                for name, state in self._states.items():
                    file_path = self.persistence_dir / f"{name}.json"
                    with open(file_path, 'w') as f:
                        json.dump(state.get_state_snapshot(), f, indent=2, default=str)
                
                # Save global state
                global_file = self.persistence_dir / "global.json"
                with open(global_file, 'w') as f:
                    json.dump(self._global_state.get_state_snapshot(), f, indent=2, default=str)
                
                return True
        
        except Exception as e:
            logger.error(f"Failed to save state: {e}", exc_info=True)
            return False
        
        return False
    
    def load_state(self, state_name: Optional[str] = None) -> bool:
        """Load state(s) from disk."""
        if not self.persistence_dir or not self.persistence_dir.exists():
            return False
        
        try:
            if state_name:
                # Load specific state
                file_path = self.persistence_dir / f"{state_name}.json"
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if state_name in self._states:
                        self._states[state_name].reset(data)
                    else:
                        self._states[state_name] = TUIState(data)
                    return True
            else:
                # Load all available states
                for file_path in self.persistence_dir.glob("*.json"):
                    name = file_path.stem
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if name == "global":
                        self._global_state.reset(data)
                    else:
                        if name in self._states:
                            self._states[name].reset(data)
                        else:
                            self._states[name] = TUIState(data)
                
                return True
        
        except Exception as e:
            logger.error(f"Failed to load state: {e}", exc_info=True)
            return False
        
        return False
    
    async def start_auto_save(self) -> None:
        """Start automatic state saving."""
        if self._auto_save_enabled and not self._save_task:
            self._save_task = asyncio.create_task(self._auto_save_loop())
    
    async def stop_auto_save(self) -> None:
        """Stop automatic state saving."""
        if self._save_task:
            self._save_task.cancel()
            try:
                await self._save_task
            except asyncio.CancelledError:
                pass
            self._save_task = None
    
    async def _auto_save_loop(self) -> None:
        """Auto-save loop."""
        while True:
            try:
                await asyncio.sleep(self._save_interval)
                self.save_state()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Auto-save error: {e}", exc_info=True)
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self._save_task:
            self._save_task.cancel()
        
        # Final save
        self.save_state()
    
    # Convenience methods for common operations
    
    def get_ui_setting(self, key: str, default: Any = None) -> Any:
        """Get UI setting value."""
        ui_state = self.get_state("ui")
        return ui_state.get(key, default) if ui_state else default
    
    def set_ui_setting(self, key: str, value: Any) -> bool:
        """Set UI setting value."""
        ui_state = self.get_state("ui")
        if ui_state:
            return ui_state.set(key, value)
        return False
    
    def get_current_workspace(self) -> str:
        """Get current workspace name."""
        workspace_state = self.get_state("workspace")
        if workspace_state:
            return workspace_state.get("current_workspace", "default")
        return "default"
    
    def set_current_workspace(self, workspace_name: str) -> bool:
        """Set current workspace."""
        workspace_state = self.get_state("workspace")
        if workspace_state:
            return workspace_state.set("current_workspace", workspace_name)
        return False
    
    def get_pipeline_execution_state(self) -> str:
        """Get current pipeline execution state."""
        pipeline_state = self.get_state("pipeline")
        if pipeline_state:
            return pipeline_state.get("execution_state", "idle")
        return "idle"
    
    def set_pipeline_execution_state(self, state: str) -> bool:
        """Set pipeline execution state."""
        pipeline_state = self.get_state("pipeline")
        if pipeline_state:
            return pipeline_state.set("execution_state", state)
        return False


# Global state manager instance
_global_state_manager: Optional[TUIStateManager] = None


def get_global_state_manager() -> TUIStateManager:
    """Get the global state manager instance."""
    global _global_state_manager
    if _global_state_manager is None:
        _global_state_manager = TUIStateManager()
    return _global_state_manager


def initialize_state_manager(
    event_bus: Optional[TUIEventBus] = None,
    persistence_dir: Optional[Path] = None
) -> TUIStateManager:
    """Initialize the global state manager."""
    global _global_state_manager
    _global_state_manager = TUIStateManager(event_bus, persistence_dir)
    return _global_state_manager