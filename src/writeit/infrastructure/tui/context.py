"""TUI Context for user interface context management.

Provides context management for TUI applications with workspace awareness,
user state tracking, and navigation context.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TYPE_CHECKING, List
from contextvars import ContextVar
import uuid
from datetime import datetime
from enum import Enum

from textual.app import App
from textual.widget import Widget
from textual.screen import Screen

from ...domains.workspace.value_objects import WorkspaceName
from ...shared.dependencies.container import Container

if TYPE_CHECKING:
    from ...domains.workspace.entities import Workspace


class TUIMode(str, Enum):
    """TUI application modes."""
    PIPELINE = "pipeline"
    WORKSPACE = "workspace"
    TEMPLATE = "template"
    CONFIGURATION = "configuration"


class NavigationState(str, Enum):
    """Navigation states within TUI."""
    HOME = "home"
    INPUTS = "inputs"
    EXECUTION = "execution"
    RESULTS = "results"
    SETTINGS = "settings"
    HELP = "help"


@dataclass
class TUIContext:
    """TUI context with application and user state."""
    
    # Application identification
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    # User and workspace context
    user_id: Optional[str] = None
    workspace_name: str = "default"
    workspace: Optional[Workspace] = None
    
    # TUI application context
    app_instance: Optional[App] = None
    current_screen: Optional[Screen] = None
    focused_widget: Optional[Widget] = None
    
    # Navigation and mode
    mode: TUIMode = TUIMode.PIPELINE
    navigation_state: NavigationState = NavigationState.HOME
    navigation_history: List[NavigationState] = field(default_factory=list)
    
    # Application state
    pipeline_id: Optional[str] = None
    current_step: Optional[str] = None
    execution_context: Dict[str, Any] = field(default_factory=dict)
    
    # UI state
    theme: str = "default"
    dark_mode: bool = True
    show_debug: bool = False
    keyboard_shortcuts_enabled: bool = True
    
    # Dependency injection
    container: Optional[Container] = None
    
    # Metadata and temporary data
    metadata: Dict[str, Any] = field(default_factory=dict)
    temp_data: Dict[str, Any] = field(default_factory=dict)
    
    def get_workspace_name(self) -> WorkspaceName:
        """Get workspace name as value object."""
        return WorkspaceName(self.workspace_name)
    
    def is_in_execution(self) -> bool:
        """Check if currently executing a pipeline."""
        return (
            self.mode == TUIMode.PIPELINE and 
            self.navigation_state == NavigationState.EXECUTION
        )
    
    def can_navigate_back(self) -> bool:
        """Check if back navigation is possible."""
        return len(self.navigation_history) > 0
    
    def push_navigation(self, state: NavigationState) -> None:
        """Push current state to navigation history."""
        if self.navigation_state != state:
            self.navigation_history.append(self.navigation_state)
            self.navigation_state = state
    
    def pop_navigation(self) -> Optional[NavigationState]:
        """Pop previous state from navigation history."""
        if self.navigation_history:
            previous_state = self.navigation_history.pop()
            self.navigation_state = previous_state
            return previous_state
        return None
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value safely."""
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value."""
        self.metadata[key] = value
    
    def get_temp_data(self, key: str, default: Any = None) -> Any:
        """Get temporary data value safely."""
        return self.temp_data.get(key, default)
    
    def set_temp_data(self, key: str, value: Any) -> None:
        """Set temporary data value."""
        self.temp_data[key] = value
    
    def clear_temp_data(self) -> None:
        """Clear all temporary data."""
        self.temp_data.clear()
    
    def update_focus_context(self, widget: Optional[Widget]) -> None:
        """Update focus context with current widget."""
        self.focused_widget = widget
        if widget:
            self.set_metadata("last_focused_widget_id", getattr(widget, 'id', None))
            self.set_metadata("last_focused_widget_type", type(widget).__name__)


# Context variables for TUI-scoped access
_tui_context: ContextVar[Optional[TUIContext]] = ContextVar(
    'tui_context', default=None
)


class TUIContextManager:
    """Manages TUI context throughout the application lifecycle."""
    
    @staticmethod
    def set_context(context: TUIContext) -> None:
        """Set the current TUI context."""
        _tui_context.set(context)
    
    @staticmethod
    def get_context() -> Optional[TUIContext]:
        """Get the current TUI context."""
        return _tui_context.get()
    
    @staticmethod
    def get_context_or_raise() -> TUIContext:
        """Get the current TUI context or raise error."""
        context = _tui_context.get()
        if context is None:
            raise RuntimeError("No TUI context available")
        return context
    
    @staticmethod
    def clear_context() -> None:
        """Clear the current TUI context."""
        _tui_context.set(None)
    
    @staticmethod
    def get_workspace_name() -> str:
        """Get current workspace name from context."""
        context = TUIContextManager.get_context()
        return context.workspace_name if context else "default"
    
    @staticmethod
    def get_user_id() -> Optional[str]:
        """Get current user ID from context."""
        context = TUIContextManager.get_context()
        return context.user_id if context else None
    
    @staticmethod
    def get_container() -> Optional[Container]:
        """Get dependency injection container from context."""
        context = TUIContextManager.get_context()
        return context.container if context else None
    
    @staticmethod
    def get_current_mode() -> TUIMode:
        """Get current TUI mode."""
        context = TUIContextManager.get_context()
        return context.mode if context else TUIMode.PIPELINE
    
    @staticmethod
    def get_navigation_state() -> NavigationState:
        """Get current navigation state."""
        context = TUIContextManager.get_context()
        return context.navigation_state if context else NavigationState.HOME
    
    @staticmethod
    def navigate_to(state: NavigationState) -> None:
        """Navigate to a new state."""
        context = TUIContextManager.get_context_or_raise()
        context.push_navigation(state)
    
    @staticmethod
    def navigate_back() -> bool:
        """Navigate back to previous state."""
        context = TUIContextManager.get_context_or_raise()
        return context.pop_navigation() is not None
    
    @staticmethod
    def update_execution_context(key: str, value: Any) -> None:
        """Update execution context."""
        context = TUIContextManager.get_context_or_raise()
        context.execution_context[key] = value
    
    @staticmethod
    def get_execution_context(key: str, default: Any = None) -> Any:
        """Get execution context value."""
        context = TUIContextManager.get_context()
        if context:
            return context.execution_context.get(key, default)
        return default
    
    @staticmethod
    def set_pipeline_context(pipeline_id: str, step: Optional[str] = None) -> None:
        """Set pipeline execution context."""
        context = TUIContextManager.get_context_or_raise()
        context.pipeline_id = pipeline_id
        context.current_step = step
        context.mode = TUIMode.PIPELINE
    
    @staticmethod
    def clear_pipeline_context() -> None:
        """Clear pipeline execution context."""
        context = TUIContextManager.get_context_or_raise()
        context.pipeline_id = None
        context.current_step = None
        context.execution_context.clear()


# Utility functions for easy access
def get_current_tui_context() -> Optional[TUIContext]:
    """Get the current TUI context."""
    return TUIContextManager.get_context()


def get_current_workspace_name() -> str:
    """Get the current workspace name."""
    return TUIContextManager.get_workspace_name()


def get_current_user_id() -> Optional[str]:
    """Get the current user ID."""
    return TUIContextManager.get_user_id()


def get_current_container() -> Optional[Container]:
    """Get the current dependency injection container."""
    return TUIContextManager.get_container()


def navigate_to(state: NavigationState) -> None:
    """Navigate to a new state."""
    TUIContextManager.navigate_to(state)


def navigate_back() -> bool:
    """Navigate back to previous state."""
    return TUIContextManager.navigate_back()


def require_tui_context() -> TUIContext:
    """Require TUI context and return it."""
    return TUIContextManager.get_context_or_raise()