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

from ...shared.events.base import DomainEvent
from ...shared.events.bus import EventBus
from .context import TUIContextManager, TUIContext, NavigationState, TUIMode

logger = logging.getLogger(__name__)


class TUIEventType(str, Enum):
    """TUI-specific event types."""
    NAVIGATION = "navigation"
    USER_INPUT = "user_input"
    PIPELINE_ACTION = "pipeline_action"
    WORKSPACE_ACTION = "workspace_action"
    UI_STATE_CHANGE = "ui_state_change"
    ERROR_OCCURRED = "error_occurred"
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
class NavigationEvent(TUIEvent):
    """Navigation-specific event."""
    
    from_state: NavigationState
    to_state: NavigationState
    
    def __post_init__(self):
        self.event_type = TUIEventType.NAVIGATION


@dataclass
class PipelineActionEvent(TUIEvent):
    """Pipeline action event."""
    
    action: str  # "start", "step_complete", "pause", "resume", "cancel"
    pipeline_id: Optional[str] = None
    step_id: Optional[str] = None
    
    def __post_init__(self):
        self.event_type = TUIEventType.PIPELINE_ACTION


@dataclass
class WorkspaceActionEvent(TUIEvent):
    """Workspace action event."""
    
    action: str  # "switch", "create", "delete", "configure"
    workspace_name: Optional[str] = None
    
    def __post_init__(self):
        self.event_type = TUIEventType.WORKSPACE_ACTION


@dataclass
class UserInputEvent(TUIEvent):
    """User input event."""
    
    input_type: str  # "text", "selection", "confirmation"
    value: Any = None
    field_name: Optional[str] = None
    
    def __post_init__(self):
        self.event_type = TUIEventType.USER_INPUT


@dataclass
class UIStateChangeEvent(TUIEvent):
    """UI state change event."""
    
    state_key: str
    old_value: Any = None
    new_value: Any = None
    
    def __post_init__(self):
        self.event_type = TUIEventType.UI_STATE_CHANGE


@dataclass
class KeyboardShortcutEvent(TUIEvent):
    """Keyboard shortcut event."""
    
    shortcut: str
    key_event: Optional[Key] = None
    
    def __post_init__(self):
        self.event_type = TUIEventType.KEYBOARD_SHORTCUT


class TUIEventHandler(ABC):
    """Abstract base class for TUI event handlers."""
    
    @abstractmethod
    async def handle_event(self, event: TUIEvent, context: TUIContext) -> bool:
        """Handle a TUI event.
        
        Args:
            event: The TUI event to handle
            context: Current TUI context
            
        Returns:
            True if event was handled, False otherwise
        """
        pass
    
    def can_handle(self, event: TUIEvent) -> bool:
        """Check if this handler can handle the event."""
        return True


class NavigationEventHandler(TUIEventHandler):
    """Handler for navigation events."""
    
    async def handle_event(self, event: TUIEvent, context: TUIContext) -> bool:
        """Handle navigation events."""
        if not isinstance(event, NavigationEvent):
            return False
        
        logger.debug(f"Navigation: {event.from_state} -> {event.to_state}")
        
        # Validate navigation
        if not self._can_navigate(event.from_state, event.to_state, context):
            event.cancel()
            return True
        
        # Update context
        context.push_navigation(event.to_state)
        
        # Set metadata
        context.set_metadata("last_navigation", {
            "from": event.from_state.value,
            "to": event.to_state.value,
            "timestamp": event.timestamp.isoformat()
        })
        
        event.mark_handled()
        return True
    
    def _can_navigate(self, from_state: NavigationState, to_state: NavigationState, context: TUIContext) -> bool:
        """Check if navigation is allowed."""
        # Prevent navigation during execution unless going to results
        if (
            context.is_in_execution() and 
            to_state not in [NavigationState.RESULTS, NavigationState.HOME]
        ):
            return False
        
        return True


class PipelineActionEventHandler(TUIEventHandler):
    """Handler for pipeline action events."""
    
    async def handle_event(self, event: TUIEvent, context: TUIContext) -> bool:
        """Handle pipeline action events."""
        if not isinstance(event, PipelineActionEvent):
            return False
        
        logger.debug(f"Pipeline action: {event.action}")
        
        # Update execution context based on action
        if event.action == "start":
            context.mode = TUIMode.PIPELINE
            context.push_navigation(NavigationState.EXECUTION)
            if event.pipeline_id:
                context.pipeline_id = event.pipeline_id
        
        elif event.action == "step_complete":
            if event.step_id:
                context.current_step = event.step_id
                context.set_metadata(f"step_{event.step_id}_completed", True)
        
        elif event.action in ["pause", "cancel"]:
            context.push_navigation(NavigationState.HOME)
        
        elif event.action == "resume":
            context.push_navigation(NavigationState.EXECUTION)
        
        # Store action in execution context
        TUIContextManager.update_execution_context("last_action", {
            "action": event.action,
            "pipeline_id": event.pipeline_id,
            "step_id": event.step_id,
            "timestamp": event.timestamp.isoformat()
        })
        
        event.mark_handled()
        return True


class WorkspaceActionEventHandler(TUIEventHandler):
    """Handler for workspace action events."""
    
    async def handle_event(self, event: TUIEvent, context: TUIContext) -> bool:
        """Handle workspace action events."""
        if not isinstance(event, WorkspaceActionEvent):
            return False
        
        logger.debug(f"Workspace action: {event.action}")
        
        # Handle workspace switching
        if event.action == "switch" and event.workspace_name:
            old_workspace = context.workspace_name
            context.workspace_name = event.workspace_name
            
            # Clear execution context when switching workspaces
            context.execution_context.clear()
            context.pipeline_id = None
            context.current_step = None
            
            context.set_metadata("workspace_switch", {
                "from": old_workspace,
                "to": event.workspace_name,
                "timestamp": event.timestamp.isoformat()
            })
        
        event.mark_handled()
        return True


class UIStateChangeEventHandler(TUIEventHandler):
    """Handler for UI state change events."""
    
    async def handle_event(self, event: TUIEvent, context: TUIContext) -> bool:
        """Handle UI state change events."""
        if not isinstance(event, UIStateChangeEvent):
            return False
        
        logger.debug(f"UI state change: {event.state_key} = {event.new_value}")
        
        # Update context based on state key
        if event.state_key == "theme":
            context.theme = str(event.new_value)
        elif event.state_key == "dark_mode":
            context.dark_mode = bool(event.new_value)
        elif event.state_key == "show_debug":
            context.show_debug = bool(event.new_value)
        elif event.state_key == "keyboard_shortcuts_enabled":
            context.keyboard_shortcuts_enabled = bool(event.new_value)
        
        # Store in metadata
        context.set_metadata(f"ui_state_{event.state_key}", {
            "old_value": event.old_value,
            "new_value": event.new_value,
            "timestamp": event.timestamp.isoformat()
        })
        
        event.mark_handled()
        return True


class KeyboardShortcutEventHandler(TUIEventHandler):
    """Handler for keyboard shortcut events."""
    
    def __init__(self):
        self.shortcut_handlers: Dict[str, Callable[[TUIContext], None]] = {
            "ctrl+h": self._handle_home,
            "ctrl+b": self._handle_back,
            "ctrl+w": self._handle_workspace_switch,
            "ctrl+p": self._handle_pipeline_mode,
            "ctrl+t": self._handle_template_mode,
            "ctrl+s": self._handle_settings,
            "f1": self._handle_help,
            "ctrl+q": self._handle_quit,
        }
    
    async def handle_event(self, event: TUIEvent, context: TUIContext) -> bool:
        """Handle keyboard shortcut events."""
        if not isinstance(event, KeyboardShortcutEvent):
            return False
        
        if not context.keyboard_shortcuts_enabled:
            return False
        
        logger.debug(f"Keyboard shortcut: {event.shortcut}")
        
        handler = self.shortcut_handlers.get(event.shortcut)
        if handler:
            handler(context)
            event.mark_handled()
            return True
        
        return False
    
    def _handle_home(self, context: TUIContext) -> None:
        """Handle home shortcut."""
        context.push_navigation(NavigationState.HOME)
    
    def _handle_back(self, context: TUIContext) -> None:
        """Handle back shortcut."""
        context.pop_navigation()
    
    def _handle_workspace_switch(self, context: TUIContext) -> None:
        """Handle workspace switch shortcut."""
        context.mode = TUIMode.WORKSPACE
    
    def _handle_pipeline_mode(self, context: TUIContext) -> None:
        """Handle pipeline mode shortcut."""
        context.mode = TUIMode.PIPELINE
    
    def _handle_template_mode(self, context: TUIContext) -> None:
        """Handle template mode shortcut."""
        context.mode = TUIMode.TEMPLATE
    
    def _handle_settings(self, context: TUIContext) -> None:
        """Handle settings shortcut."""
        context.push_navigation(NavigationState.SETTINGS)
    
    def _handle_help(self, context: TUIContext) -> None:
        """Handle help shortcut."""
        context.push_navigation(NavigationState.HELP)
    
    def _handle_quit(self, context: TUIContext) -> None:
        """Handle quit shortcut."""
        # This would trigger app quit - implementation depends on app structure
        context.set_metadata("quit_requested", True)


class TUIEventBus:
    """Event bus for TUI events with domain integration."""
    
    def __init__(self, domain_event_bus: Optional[EventBus] = None):
        self.domain_event_bus = domain_event_bus
        self.handlers: List[TUIEventHandler] = []
        self.middleware: List[Callable[[TUIEvent, TUIContext], None]] = []
        
        # Register default handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self) -> None:
        """Register default TUI event handlers."""
        self.register_handler(NavigationEventHandler())
        self.register_handler(PipelineActionEventHandler())
        self.register_handler(WorkspaceActionEventHandler())
        self.register_handler(UIStateChangeEventHandler())
        self.register_handler(KeyboardShortcutEventHandler())
    
    def register_handler(self, handler: TUIEventHandler) -> None:
        """Register a TUI event handler."""
        self.handlers.append(handler)
    
    def unregister_handler(self, handler: TUIEventHandler) -> None:
        """Unregister a TUI event handler."""
        if handler in self.handlers:
            self.handlers.remove(handler)
    
    def add_middleware(self, middleware: Callable[[TUIEvent, TUIContext], None]) -> None:
        """Add middleware for event processing."""
        self.middleware.append(middleware)
    
    async def emit_event(self, event: TUIEvent) -> bool:
        """Emit a TUI event to all registered handlers.
        
        Args:
            event: The TUI event to emit
            
        Returns:
            True if event was handled by at least one handler
        """
        context = TUIContextManager.get_context_or_raise()
        
        # Apply middleware
        for middleware in self.middleware:
            try:
                middleware(event, context)
            except Exception as e:
                logger.error(f"Middleware error: {e}", exc_info=True)
        
        # Check if event was cancelled by middleware
        if event.cancelled:
            return False
        
        # Process through handlers
        handled = False
        for handler in self.handlers:
            if handler.can_handle(event):
                try:
                    if await handler.handle_event(event, context):
                        handled = True
                        if event.handled:
                            break
                except Exception as e:
                    logger.error(f"Handler error: {e}", exc_info=True)
        
        # Convert to domain event if applicable
        if handled and self.domain_event_bus:
            domain_event = self._convert_to_domain_event(event, context)
            if domain_event:
                await self.domain_event_bus.publish_async(domain_event)
        
        return handled
    
    def _convert_to_domain_event(self, tui_event: TUIEvent, context: TUIContext) -> Optional[DomainEvent]:
        """Convert TUI event to domain event if applicable."""
        # This would convert specific TUI events to domain events
        # Implementation depends on specific domain event types
        return None
    
    # Convenience methods for emitting specific events
    
    async def emit_navigation(self, from_state: NavigationState, to_state: NavigationState) -> bool:
        """Emit a navigation event."""
        event = NavigationEvent(from_state=from_state, to_state=to_state)
        return await self.emit_event(event)
    
    async def emit_pipeline_action(self, action: str, pipeline_id: Optional[str] = None, step_id: Optional[str] = None) -> bool:
        """Emit a pipeline action event."""
        event = PipelineActionEvent(action=action, pipeline_id=pipeline_id, step_id=step_id)
        return await self.emit_event(event)
    
    async def emit_workspace_action(self, action: str, workspace_name: Optional[str] = None) -> bool:
        """Emit a workspace action event."""
        event = WorkspaceActionEvent(action=action, workspace_name=workspace_name)
        return await self.emit_event(event)
    
    async def emit_user_input(self, input_type: str, value: Any, field_name: Optional[str] = None) -> bool:
        """Emit a user input event."""
        event = UserInputEvent(input_type=input_type, value=value, field_name=field_name)
        return await self.emit_event(event)
    
    async def emit_ui_state_change(self, state_key: str, old_value: Any, new_value: Any) -> bool:
        """Emit a UI state change event."""
        event = UIStateChangeEvent(state_key=state_key, old_value=old_value, new_value=new_value)
        return await self.emit_event(event)
    
    async def emit_keyboard_shortcut(self, shortcut: str, key_event: Optional[Key] = None) -> bool:
        """Emit a keyboard shortcut event."""
        event = KeyboardShortcutEvent(shortcut=shortcut, key_event=key_event)
        return await self.emit_event(event)


# Utility functions
def create_default_tui_event_bus(domain_event_bus: Optional[EventBus] = None) -> TUIEventBus:
    """Create a TUI event bus with default configuration."""
    return TUIEventBus(domain_event_bus)


async def emit_tui_event(event: TUIEvent) -> bool:
    """Emit a TUI event using the current context's event bus."""
    # This would require the event bus to be stored in context or globally
    # Implementation depends on how the event bus is managed
    raise NotImplementedError("TUI event bus not available in context")