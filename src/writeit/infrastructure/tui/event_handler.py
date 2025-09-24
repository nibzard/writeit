"""TUI Event Handler for user interaction handling.

Provides domain-aware event handling for TUI applications with
custom event types, event routing, and integration with domain events.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Type, Union
from enum import Enum
import asyncio
import logging
from datetime import datetime

from textual.message import Message
from textual.widget import Widget
from textual.events import Key, Click, Focus, Blur

from ...shared.events import DomainEvent
from ...shared.events import EventBus
from .context import TUIContextManager, TUIContext, NavigationState, TUIMode

logger = logging.getLogger(__name__)


class TUIEventType(str, Enum):
    """TUI-specific event types."""
    NAVIGATION = "navigation"
    USER_INPUT = "user_input"
    PIPELINE_ACTION = "pipeline_action"
    WORKSPACE_ACTION = "workspace_action"
    UI_STATE_CHANGE = "ui_state_change"
    FOCUS_CHANGE = "focus_change"
    KEYBOARD_SHORTCUT = "keyboard_shortcut"


@dataclass
class TUIEvent:
    """Base TUI event class."""
    
    event_type: TUIEventType
    source_widget: Optional[Widget] = None
    target_widget: Optional[Widget] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Event control
    handled: bool = False
    cancelled: bool = False
    
    def mark_handled(self) -> None:
        """Mark this event as handled."""
        self.handled = True
    
    def cancel(self) -> None:
        """Cancel this event."""
        self.cancelled = True
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get event data safely."""
        return self.data.get(key, default)
    
    def set_data(self, key: str, value: Any) -> None:
        """Set event data."""
        self.data[key] = value


@dataclass
class NavigationEvent:
    """Navigation-specific event."""
    
    from_state: NavigationState
    to_state: NavigationState
    event_type: TUIEventType = TUIEventType.NAVIGATION
    source_widget: Optional[Widget] = None
    target_widget: Optional[Widget] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    handled: bool = False
    cancelled: bool = False


@dataclass
class PipelineActionEvent:
    """Pipeline action event."""
    
    action: str  # "start", "step_complete", "pause", "resume", "cancel"
    pipeline_id: Optional[str] = None
    event_type: TUIEventType = TUIEventType.PIPELINE_ACTION
    source_widget: Optional[Widget] = None
    target_widget: Optional[Widget] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    handled: bool = False
    cancelled: bool = False
    step_id: Optional[str] = None


@dataclass
class WorkspaceActionEvent:
    """Workspace action event."""
    
    action: str  # "switch", "create", "delete", "configure"
    workspace_name: Optional[str] = None
    event_type: TUIEventType = TUIEventType.WORKSPACE_ACTION
    source_widget: Optional[Widget] = None
    target_widget: Optional[Widget] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    handled: bool = False
    cancelled: bool = False


@dataclass
class UserInputEvent:
    """User input event."""
    
    input_type: str  # "text", "selection", "confirmation"
    value: Any = None
    event_type: TUIEventType = TUIEventType.USER_INPUT
    field_name: Optional[str] = None
    source_widget: Optional[Widget] = None
    target_widget: Optional[Widget] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    handled: bool = False
    cancelled: bool = False


@dataclass
class UIStateChangeEvent:
    """UI state change event."""
    
    state_key: str
    old_value: Any = None
    event_type: TUIEventType = TUIEventType.UI_STATE_CHANGE
    new_value: Any = None
    source_widget: Optional[Widget] = None
    target_widget: Optional[Widget] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    handled: bool = False
    cancelled: bool = False


@dataclass
class KeyboardShortcutEvent:
    """Keyboard shortcut event."""
    
    shortcut: str
    event_type: TUIEventType = TUIEventType.KEYBOARD_SHORTCUT
    key_event: Optional[Key] = None
    source_widget: Optional[Widget] = None
    target_widget: Optional[Widget] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    handled: bool = False
    cancelled: bool = False


class TUIEventHandler(ABC):
    """Abstract base class for TUI event handlers."""
    
    @abstractmethod
    def can_handle(self, event: Union[TUIEvent, DomainEvent]) -> bool:
        """Check if this handler can handle the event."""
        pass
    
    @abstractmethod
    async def handle(self, event: Union[TUIEvent, DomainEvent]) -> None:
        """Handle the event."""
        pass
    
    @property
    @abstractmethod
    def handler_type(self) -> str:
        """Get the handler type for routing."""
        pass


class NavigationEventHandler(TUIEventHandler):
    """Handler for navigation events."""
    
    def can_handle(self, event: Union[TUIEvent, DomainEvent]) -> bool:
        return isinstance(event, (NavigationEvent, TUIEvent)) and (
            event.event_type == TUIEventType.NAVIGATION
        )
    
    async def handle(self, event: Union[TUIEvent, DomainEvent]) -> None:
        if isinstance(event, NavigationEvent):
            context = TUIContextManager.get_current_context()
            if context:
                context.navigation_state = event.to_state
                logger.info(f"Navigation changed: {event.from_state} -> {event.to_state}")
    
    @property
    def handler_type(self) -> str:
        return "navigation"


class PipelineActionEventHandler(TUIEventHandler):
    """Handler for pipeline action events."""
    
    def can_handle(self, event: Union[TUIEvent, DomainEvent]) -> bool:
        return isinstance(event, (PipelineActionEvent, TUIEvent)) and (
            event.event_type == TUIEventType.PIPELINE_ACTION
        )
    
    async def handle(self, event: Union[TUIEvent, DomainEvent]) -> None:
        if isinstance(event, PipelineActionEvent):
            logger.info(f"Pipeline action: {event.action} for pipeline {event.pipeline_id}")
            
            # Route to appropriate pipeline service
            context = TUIContextManager.get_current_context()
            if context and context.container:
                # This would integrate with pipeline service
                pass
    
    @property
    def handler_type(self) -> str:
        return "pipeline_action"


class WorkspaceActionEventHandler(TUIEventHandler):
    """Handler for workspace action events."""
    
    def can_handle(self, event: Union[TUIEvent, DomainEvent]) -> bool:
        return isinstance(event, (WorkspaceActionEvent, TUIEvent)) and (
            event.event_type == TUIEventType.WORKSPACE_ACTION
        )
    
    async def handle(self, event: Union[TUIEvent, DomainEvent]) -> None:
        if isinstance(event, WorkspaceActionEvent):
            logger.info(f"Workspace action: {event.action} for workspace {event.workspace_name}")
            
            # Route to workspace service
            context = TUIContextManager.get_current_context()
            if context and context.container:
                # This would integrate with workspace service
                pass
    
    @property
    def handler_type(self) -> str:
        return "workspace_action"


class UserInputEventHandler(TUIEventHandler):
    """Handler for user input events."""
    
    def can_handle(self, event: Union[TUIEvent, DomainEvent]) -> bool:
        return isinstance(event, (UserInputEvent, TUIEvent)) and (
            event.event_type == TUIEventType.USER_INPUT
        )
    
    async def handle(self, event: Union[TUIEvent, DomainEvent]) -> None:
        if isinstance(event, UserInputEvent):
            logger.info(f"User input: {event.input_type} = {event.value}")
            
            # Handle user input based on type
            context = TUIContextManager.get_current_context()
            if context:
                # Store input in context data
                context.user_input_data[event.field_name or "default"] = event.value
    
    @property
    def handler_type(self) -> str:
        return "user_input"


class UIStateChangeEventHandler(TUIEventHandler):
    """Handler for UI state change events."""
    
    def can_handle(self, event: Union[TUIEvent, DomainEvent]) -> bool:
        return isinstance(event, (UIStateChangeEvent, TUIEvent)) and (
            event.event_type == TUIEventType.UI_STATE_CHANGE
        )
    
    async def handle(self, event: Union[TUIEvent, DomainEvent]) -> None:
        if isinstance(event, UIStateChangeEvent):
            logger.info(f"UI state change: {event.state_key} = {event.old_value} -> {event.new_value}")
            
            # Update UI state in context
            context = TUIContextManager.get_current_context()
            if context:
                context.ui_state[event.state_key] = event.new_value
    
    @property
    def handler_type(self) -> str:
        return "ui_state_change"


class KeyboardShortcutEventHandler(TUIEventHandler):
    """Handler for keyboard shortcut events."""
    
    def can_handle(self, event: Union[TUIEvent, DomainEvent]) -> bool:
        return isinstance(event, (KeyboardShortcutEvent, TUIEvent)) and (
            event.event_type == TUIEventType.KEYBOARD_SHORTCUT
        )
    
    async def handle(self, event: Union[TUIEvent, DomainEvent]) -> None:
        if isinstance(event, KeyboardShortcutEvent):
            logger.info(f"Keyboard shortcut: {event.shortcut}")
            
            # Handle common shortcuts
            if event.shortcut == "ctrl+c":
                # Quit application
                pass
            elif event.shortcut == "ctrl+p":
                # Pause/resume
                pass
            elif event.shortcut == "ctrl+s":
                # Save
                pass
    
    @property
    def handler_type(self) -> str:
        return "keyboard_shortcut"


class TUIEventBus:
    """TUI-specific event bus for handling UI events.
    
    Provides a specialized event bus for TUI applications with support for:
    - UI-specific event types
    - Event routing based on widget hierarchy
    - Event propagation control
    - Integration with domain events
    """
    
    def __init__(self, domain_event_bus: Optional[EventBus] = None):
        self.domain_event_bus = domain_event_bus
        self.handlers: Dict[str, List[TUIEventHandler]] = {}
        self.event_log: List[TUIEvent] = []
        self.max_log_size = 1000
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default TUI event handlers."""
        handlers = [
            NavigationEventHandler(),
            PipelineActionEventHandler(),
            WorkspaceActionEventHandler(),
            UserInputEventHandler(),
            UIStateChangeEventHandler(),
            KeyboardShortcutEventHandler(),
        ]
        
        for handler in handlers:
            self.register_handler(handler)
    
    def register_handler(self, handler: TUIEventHandler) -> None:
        """Register a TUI event handler."""
        handler_type = handler.handler_type
        if handler_type not in self.handlers:
            self.handlers[handler_type] = []
        self.handlers[handler_type].append(handler)
    
    def unregister_handler(self, handler: TUIEventHandler) -> None:
        """Unregister a TUI event handler."""
        handler_type = handler.handler_type
        if handler_type in self.handlers:
            try:
                self.handlers[handler_type].remove(handler)
            except ValueError:
                pass
    
    async def publish(self, event: Union[TUIEvent, NavigationEvent, PipelineActionEvent, 
                          WorkspaceActionEvent, UserInputEvent, UIStateChangeEvent, 
                          KeyboardShortcutEvent]) -> None:
        """Publish a TUI event."""
        # Log the event
        if isinstance(event, TUIEvent):
            self.event_log.append(event)
            if len(self.event_log) > self.max_log_size:
                self.event_log.pop(0)
        
        # Find and execute handlers
        for handler_type, handlers in self.handlers.items():
            for handler in handlers:
                if handler.can_handle(event):
                    try:
                        await handler.handle(event)
                        
                        # Stop propagation if event is cancelled
                        if hasattr(event, 'cancelled') and event.cancelled:
                            break
                        
                        # Mark as handled
                        if hasattr(event, 'handled'):
                            event.mark_handled()
                            
                    except Exception as e:
                        logger.error(f"Error in TUI event handler {handler_type}: {e}")
        
        # Forward to domain event bus if available
        if self.domain_event_bus and isinstance(event, DomainEvent):
            await self.domain_event_bus.publish(event)
    
    async def publish_navigation(self, from_state: NavigationState, to_state: NavigationState,
                               source_widget: Optional[Widget] = None) -> None:
        """Convenience method to publish navigation event."""
        event = NavigationEvent(
            from_state=from_state,
            to_state=to_state,
            source_widget=source_widget
        )
        await self.publish(event)
    
    async def publish_pipeline_action(self, action: str, pipeline_id: Optional[str] = None,
                                    step_id: Optional[str] = None,
                                    source_widget: Optional[Widget] = None) -> None:
        """Convenience method to publish pipeline action event."""
        event = PipelineActionEvent(
            action=action,
            pipeline_id=pipeline_id,
            step_id=step_id,
            source_widget=source_widget
        )
        await self.publish(event)
    
    async def publish_workspace_action(self, action: str, workspace_name: Optional[str] = None,
                                     source_widget: Optional[Widget] = None) -> None:
        """Convenience method to publish workspace action event."""
        event = WorkspaceActionEvent(
            action=action,
            workspace_name=workspace_name,
            source_widget=source_widget
        )
        await self.publish(event)
    
    async def publish_user_input(self, input_type: str, value: Any, field_name: Optional[str] = None,
                                source_widget: Optional[Widget] = None) -> None:
        """Convenience method to publish user input event."""
        event = UserInputEvent(
            input_type=input_type,
            value=value,
            field_name=field_name,
            source_widget=source_widget
        )
        await self.publish(event)
    
    async def publish_ui_state_change(self, state_key: str, old_value: Any, new_value: Any,
                                    source_widget: Optional[Widget] = None) -> None:
        """Convenience method to publish UI state change event."""
        event = UIStateChangeEvent(
            state_key=state_key,
            old_value=old_value,
            new_value=new_value,
            source_widget=source_widget
        )
        await self.publish(event)
    
    async def publish_keyboard_shortcut(self, shortcut: str, key_event: Optional[Key] = None,
                                       source_widget: Optional[Widget] = None) -> None:
        """Convenience method to publish keyboard shortcut event."""
        event = KeyboardShortcutEvent(
            shortcut=shortcut,
            key_event=key_event,
            source_widget=source_widget
        )
        await self.publish(event)
    
    def get_event_log(self, limit: Optional[int] = None) -> List[TUIEvent]:
        """Get the event log."""
        if limit is None:
            return self.event_log.copy()
        return self.event_log[-limit:]
    
    def clear_event_log(self) -> None:
        """Clear the event log."""
        self.event_log.clear()
    
    def get_handlers_by_type(self, handler_type: str) -> List[TUIEventHandler]:
        """Get handlers by type."""
        return self.handlers.get(handler_type, [])
    
    def get_all_handler_types(self) -> List[str]:
        """Get all registered handler types."""
        return list(self.handlers.keys())


# Global TUI event bus instance
_tui_event_bus: Optional[TUIEventBus] = None


def get_tui_event_bus() -> TUIEventBus:
    """Get the global TUI event bus instance."""
    global _tui_event_bus
    if _tui_event_bus is None:
        _tui_event_bus = TUIEventBus()
    return _tui_event_bus


def set_tui_event_bus(bus: TUIEventBus) -> None:
    """Set the global TUI event bus instance."""
    global _tui_event_bus
    _tui_event_bus = bus


# Convenience functions
async def publish_tui_event(event: Union[TUIEvent, NavigationEvent, PipelineActionEvent,
                           WorkspaceActionEvent, UserInputEvent, UIStateChangeEvent,
                           KeyboardShortcutEvent]) -> None:
    """Publish a TUI event using the global event bus."""
    bus = get_tui_event_bus()
    await bus.publish(event)


async def publish_navigation(from_state: NavigationState, to_state: NavigationState,
                           source_widget: Optional[Widget] = None) -> None:
    """Convenience function to publish navigation event."""
    bus = get_tui_event_bus()
    await bus.publish_navigation(from_state, to_state, source_widget)


async def publish_pipeline_action(action: str, pipeline_id: Optional[str] = None,
                                step_id: Optional[str] = None,
                                source_widget: Optional[Widget] = None) -> None:
    """Convenience function to publish pipeline action event."""
    bus = get_tui_event_bus()
    await bus.publish_pipeline_action(action, pipeline_id, step_id, source_widget)


async def publish_workspace_action(action: str, workspace_name: Optional[str] = None,
                                 source_widget: Optional[Widget] = None) -> None:
    """Convenience function to publish workspace action event."""
    bus = get_tui_event_bus()
    await bus.publish_workspace_action(action, workspace_name, source_widget)


async def publish_user_input(input_type: str, value: Any, field_name: Optional[str] = None,
                            source_widget: Optional[Widget] = None) -> None:
    """Convenience function to publish user input event."""
    bus = get_tui_event_bus()
    await bus.publish_user_input(input_type, value, field_name, source_widget)


async def publish_ui_state_change(state_key: str, old_value: Any, new_value: Any,
                               source_widget: Optional[Widget] = None) -> None:
    """Convenience function to publish UI state change event."""
    bus = get_tui_event_bus()
    await bus.publish_ui_state_change(state_key, old_value, new_value, source_widget)


async def publish_keyboard_shortcut(shortcut: str, key_event: Optional[Key] = None,
                                   source_widget: Optional[Widget] = None) -> None:
    """Convenience function to publish keyboard shortcut event."""
    bus = get_tui_event_bus()
    await bus.publish_keyboard_shortcut(shortcut, key_event, source_widget)