"""TUI Error Handler for user-friendly error display.

Provides comprehensive error handling for TUI applications with
visual error displays, error recovery, and user-friendly messaging.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable, Type, Union
from enum import Enum
import traceback
import logging
from datetime import datetime
from pathlib import Path

from textual.app import App
from textual.widgets import Static, Button, TextArea, Label
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual import events
from textual.binding import Binding

from ...shared.errors import DomainError, ValidationError, NotFoundError, ConflictError
from ...shared.dependencies.exceptions import (
    ServiceNotFoundError,
    CircularDependencyError,
    InvalidServiceRegistrationError,
    ServiceLifetimeError,
    AsyncServiceError
)
from ...domains.workspace.errors import (
    WorkspaceNotFoundError,
    WorkspaceAlreadyExistsError,
    WorkspaceConfigurationError,
    WorkspaceAccessDeniedError
)
from ...domains.pipeline.errors import (
    PipelineNotFoundError,
    PipelineValidationError,
    PipelineExecutionError,
    StepExecutionError
)
from ...domains.content.errors import (
    TemplateNotFoundError,
    ContentValidationError,
    ContentGenerationError
)
from .context import TUIContextManager, TUIContext

logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Error severity levels for TUI display."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorAction(str, Enum):
    """Actions that can be taken in response to errors."""
    RETRY = "retry"
    IGNORE = "ignore"
    CANCEL = "cancel"
    NAVIGATE_HOME = "navigate_home"
    RESTART = "restart"
    REPORT = "report"
    SHOW_DETAILS = "show_details"


@dataclass
class TUIErrorInfo:
    """Comprehensive error information for TUI display."""
    
    # Basic error info
    title: str
    message: str
    severity: ErrorSeverity = ErrorSeverity.ERROR
    
    # Detailed information
    details: Optional[str] = None
    technical_details: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    # User guidance
    suggestions: List[str] = field(default_factory=list)
    available_actions: List[ErrorAction] = field(default_factory=list)
    
    # Metadata
    error_code: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: Optional[str] = None
    
    # Recovery information
    recoverable: bool = True
    recovery_callback: Optional[Callable[[], None]] = None
    
    def add_suggestion(self, suggestion: str) -> None:
        """Add a user suggestion."""
        if suggestion not in self.suggestions:
            self.suggestions.append(suggestion)
    
    def add_action(self, action: ErrorAction) -> None:
        """Add an available action."""
        if action not in self.available_actions:
            self.available_actions.append(action)
    
    def get_icon(self) -> str:
        """Get icon for error severity."""
        icons = {
            ErrorSeverity.INFO: "ℹ️",
            ErrorSeverity.WARNING: "⚠️",
            ErrorSeverity.ERROR: "❌",
            ErrorSeverity.CRITICAL: "🔥"
        }
        return icons.get(self.severity, "❌")
    
    def get_color_class(self) -> str:
        """Get CSS class for error severity."""
        return f"error-{self.severity.value}"


class ErrorDisplayWidget(Container):
    """Widget for displaying error information."""
    
    DEFAULT_CSS = """
    ErrorDisplayWidget {
        height: auto;
        padding: 1;
        border: solid $error;
        margin: 1;
    }
    
    .error-info {
        color: $text;
    }
    
    .error-warning {
        color: $warning;
    }
    
    .error-error {
        color: $error;
    }
    
    .error-critical {
        color: $error;
        text-style: bold;
    }
    
    .error-title {
        text-style: bold;
        margin-bottom: 1;
    }
    
    .error-message {
        margin-bottom: 1;
    }
    
    .error-suggestions {
        margin-top: 1;
        padding-left: 2;
    }
    
    .error-actions {
        margin-top: 1;
    }
    
    .error-details {
        margin-top: 1;
        border: solid $primary;
        padding: 1;
        max-height: 20;
    }
    """
    
    def __init__(self, error_info: TUIErrorInfo, on_action: Optional[Callable[[ErrorAction], None]] = None):
        super().__init__()
        self.error_info = error_info
        self.on_action = on_action
        self.show_details = False
    
    def compose(self):
        """Compose the error display."""
        with Vertical():
            # Title with icon
            yield Static(
                f"{self.error_info.get_icon()} {self.error_info.title}",
                classes=f"error-title {self.error_info.get_color_class()}"
            )
            
            # Main message
            yield Static(
                self.error_info.message,
                classes="error-message"
            )
            
            # Suggestions
            if self.error_info.suggestions:
                yield Static("💡 Suggestions:", classes="error-suggestions")
                for suggestion in self.error_info.suggestions:
                    yield Static(f"  • {suggestion}", classes="error-suggestions")
            
            # Action buttons
            if self.error_info.available_actions:
                with Horizontal(classes="error-actions"):
                    for action in self.error_info.available_actions:
                        yield Button(
                            self._get_action_label(action),
                            id=f"action-{action.value}",
                            classes=self._get_action_class(action)
                        )
            
            # Details toggle
            if self.error_info.details or self.error_info.technical_details:
                yield Button(
                    "Show Details" if not self.show_details else "Hide Details",
                    id="toggle-details",
                    variant="primary"
                )
                
                if self.show_details:
                    if self.error_info.details:
                        yield TextArea(
                            self.error_info.details,
                            read_only=True,
                            classes="error-details",
                            id="error-details"
                        )
                    
                    if self.error_info.technical_details:
                        yield TextArea(
                            self.error_info.technical_details,
                            read_only=True,
                            classes="error-details",
                            id="technical-details"
                        )
    
    def _get_action_label(self, action: ErrorAction) -> str:
        """Get display label for action."""
        labels = {
            ErrorAction.RETRY: "🔄 Retry",
            ErrorAction.IGNORE: "⏭️ Ignore",
            ErrorAction.CANCEL: "❌ Cancel",
            ErrorAction.NAVIGATE_HOME: "🏠 Home",
            ErrorAction.RESTART: "🔄 Restart",
            ErrorAction.REPORT: "📝 Report",
            ErrorAction.SHOW_DETAILS: "📋 Details"
        }
        return labels.get(action, action.value.title())
    
    def _get_action_class(self, action: ErrorAction) -> str:
        """Get CSS class for action button."""
        if action in [ErrorAction.RETRY]:
            return "success"
        elif action in [ErrorAction.CANCEL, ErrorAction.IGNORE]:
            return "warning"
        else:
            return "default"
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "toggle-details":
            self.show_details = not self.show_details
            await self.recompose()
        elif event.button.id and event.button.id.startswith("action-"):
            action_value = event.button.id[7:]  # Remove "action-" prefix
            try:
                action = ErrorAction(action_value)
                if self.on_action:
                    self.on_action(action)
            except ValueError:
                logger.warning(f"Unknown error action: {action_value}")


class ErrorModal(ModalScreen):
    """Modal screen for displaying errors."""
    
    BINDINGS = [
        Binding("escape", "dismiss", "Dismiss"),
        Binding("enter", "default_action", "Default Action"),
    ]
    
    def __init__(self, error_info: TUIErrorInfo, on_action: Optional[Callable[[ErrorAction], None]] = None):
        super().__init__()
        self.error_info = error_info
        self.on_action = on_action
    
    def compose(self):
        """Compose the modal."""
        with Container(id="error-modal"):
            yield ErrorDisplayWidget(self.error_info, self._handle_action)
    
    def _handle_action(self, action: ErrorAction) -> None:
        """Handle error action."""
        if self.on_action:
            self.on_action(action)
        
        # Auto-dismiss for certain actions
        if action in [ErrorAction.NAVIGATE_HOME, ErrorAction.CANCEL, ErrorAction.IGNORE]:
            self.dismiss()
    
    def action_dismiss(self) -> None:
        """Dismiss the modal."""
        self.dismiss()
    
    def action_default_action(self) -> None:
        """Execute the default action."""
        if self.error_info.available_actions:
            default_action = self.error_info.available_actions[0]
            self._handle_action(default_action)
        else:
            self.dismiss()


class TUIErrorHandler:
    """Handles errors in TUI applications with user-friendly displays."""
    
    def __init__(self, app: Optional[App] = None):
        self.app = app
        self.error_history: List[TUIErrorInfo] = []
        self.max_history = 50
        
        # Error mapping configuration
        self.error_mappers: Dict[Type[Exception], Callable[[Exception], TUIErrorInfo]] = {}
        self._setup_default_mappers()
        
        # Global error handlers
        self.global_handlers: List[Callable[[TUIErrorInfo], bool]] = []
    
    def _setup_default_mappers(self) -> None:
        """Set up default exception to error info mappers."""
        
        # Domain validation errors
        self.error_mappers[ValidationError] = self._map_validation_error
        self.error_mappers[PipelineValidationError] = self._map_pipeline_validation_error
        self.error_mappers[ContentValidationError] = self._map_content_validation_error
        self.error_mappers[WorkspaceConfigurationError] = self._map_workspace_config_error
        
        # Not found errors
        self.error_mappers[NotFoundError] = self._map_not_found_error
        self.error_mappers[WorkspaceNotFoundError] = self._map_workspace_not_found_error
        self.error_mappers[PipelineNotFoundError] = self._map_pipeline_not_found_error
        self.error_mappers[ContentNotFoundError] = self._map_content_not_found_error
        
        # Conflict errors
        self.error_mappers[ConflictError] = self._map_conflict_error
        self.error_mappers[WorkspaceAlreadyExistsError] = self._map_workspace_conflict_error
        
        # Access errors
        self.error_mappers[WorkspaceAccessDeniedError] = self._map_access_denied_error
        
        # Execution errors
        self.error_mappers[PipelineExecutionError] = self._map_execution_error
        self.error_mappers[StepExecutionError] = self._map_step_execution_error
        self.error_mappers[TemplateProcessingError] = self._map_template_processing_error
        
        # Service errors
        self.error_mappers[ServiceNotFoundError] = self._map_service_not_found_error
        self.error_mappers[CircularDependencyError] = self._map_circular_dependency_error
        self.error_mappers[InvalidServiceRegistrationError] = self._map_invalid_service_registration_error
        self.error_mappers[ServiceLifetimeError] = self._map_service_lifetime_error
        self.error_mappers[AsyncServiceError] = self._map_async_service_error
    
    def register_error_mapper(self, exception_type: Type[Exception], mapper: Callable[[Exception], TUIErrorInfo]) -> None:
        """Register custom error mapper."""
        self.error_mappers[exception_type] = mapper
    
    def add_global_handler(self, handler: Callable[[TUIErrorInfo], bool]) -> None:
        """Add global error handler."""
        self.global_handlers.append(handler)
    
    def create_error_info(self, exception: Exception, context: Optional[TUIContext] = None) -> TUIErrorInfo:
        """Create error info from exception."""
        # Find appropriate mapper
        for exc_type, mapper in self.error_mappers.items():
            if isinstance(exception, exc_type):
                error_info = mapper(exception)
                
                # Add context information
                if context:
                    error_info.context.update({
                        "workspace": context.workspace_name,
                        "mode": context.mode.value,
                        "navigation_state": context.navigation_state.value,
                        "session_id": context.session_id
                    })
                
                return error_info
        
        # Default handler for unhandled exceptions
        return self._map_generic_error(exception, context)
    
    async def handle_error(
        self, 
        exception: Exception, 
        context: Optional[TUIContext] = None,
        show_modal: bool = True
    ) -> bool:
        """Handle an error with appropriate display and recovery.
        
        Args:
            exception: The exception to handle
            context: Current TUI context
            show_modal: Whether to show error modal
            
        Returns:
            True if error was handled successfully
        """
        try:
            # Create error info
            error_info = self.create_error_info(exception, context)
            
            # Add to history
            self.error_history.append(error_info)
            if len(self.error_history) > self.max_history:
                self.error_history.pop(0)
            
            # Log error
            log_level = {
                ErrorSeverity.INFO: logging.INFO,
                ErrorSeverity.WARNING: logging.WARNING,
                ErrorSeverity.ERROR: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }.get(error_info.severity, logging.ERROR)
            
            logger.log(log_level, f"TUI Error: {error_info.title} - {error_info.message}")
            
            # Try global handlers first
            for handler in self.global_handlers:
                if handler(error_info):
                    return True
            
            # Show modal if requested and app is available
            if show_modal and self.app:
                await self._show_error_modal(error_info)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in error handler: {e}", exc_info=True)
            return False
    
    async def _show_error_modal(self, error_info: TUIErrorInfo) -> None:
        """Show error modal."""
        if not self.app:
            return
        
        modal = ErrorModal(error_info, self._handle_error_action)
        self.app.push_screen(modal)
    
    def _handle_error_action(self, action: ErrorAction) -> None:
        """Handle error action."""
        context = TUIContextManager.get_context()
        
        if action == ErrorAction.NAVIGATE_HOME:
            if context:
                from .context import NavigationState
                context.push_navigation(NavigationState.HOME)
        
        elif action == ErrorAction.RESTART:
            if self.app:
                # This would restart the app - implementation depends on app structure
                pass
        
        elif action == ErrorAction.REPORT:
            self._create_error_report()
        
        # Add more action handling as needed
    
    def _create_error_report(self) -> None:
        """Create error report file."""
        try:
            report_dir = Path.home() / ".writeit" / "error_reports"
            report_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"error_report_{timestamp}.txt"
            
            with open(report_file, 'w') as f:
                f.write("WriteIt TUI Error Report\n")
                f.write("=" * 50 + "\n\n")
                
                for i, error_info in enumerate(self.error_history[-10:], 1):
                    f.write(f"Error {i}:\n")
                    f.write(f"  Title: {error_info.title}\n")
                    f.write(f"  Message: {error_info.message}\n")
                    f.write(f"  Severity: {error_info.severity.value}\n")
                    f.write(f"  Timestamp: {error_info.timestamp}\n")
                    if error_info.technical_details:
                        f.write(f"  Technical Details: {error_info.technical_details}\n")
                    f.write("\n")
            
            logger.info(f"Error report created: {report_file}")
            
        except Exception as e:
            logger.error(f"Failed to create error report: {e}", exc_info=True)
    
    # Error mapping methods
    
    def _map_validation_error(self, exc: ValidationError) -> TUIErrorInfo:
        """Map validation error."""
        return TUIErrorInfo(
            title="Input Validation Error",
            message=str(exc),
            severity=ErrorSeverity.WARNING,
            suggestions=[
                "Check your input values",
                "Ensure all required fields are filled",
                "Verify data format matches requirements"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.CANCEL],
            recoverable=True
        )
    
    def _map_pipeline_validation_error(self, exc: PipelineValidationError) -> TUIErrorInfo:
        """Map pipeline validation error."""
        return TUIErrorInfo(
            title="Pipeline Configuration Error",
            message=f"Pipeline validation failed: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check pipeline YAML syntax",
                "Verify all required fields are present",
                "Use validation command to check locally"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.NAVIGATE_HOME],
            recoverable=True
        )
    
    def _map_content_validation_error(self, exc: ContentValidationError) -> TUIErrorInfo:
        """Map content validation error."""
        return TUIErrorInfo(
            title="Content Validation Error",
            message=f"Content validation failed: {exc}",
            severity=ErrorSeverity.WARNING,
            suggestions=[
                "Check content format",
                "Ensure required content fields are present"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.IGNORE],
            recoverable=True
        )
    
    def _map_workspace_config_error(self, exc: WorkspaceConfigurationError) -> TUIErrorInfo:
        """Map workspace configuration error."""
        return TUIErrorInfo(
            title="Workspace Configuration Error",
            message=f"Workspace configuration error: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check workspace configuration",
                "Initialize workspace if needed",
                "Verify workspace permissions"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.NAVIGATE_HOME],
            recoverable=True
        )
    
    def _map_not_found_error(self, exc: NotFoundError) -> TUIErrorInfo:
        """Map generic not found error."""
        return TUIErrorInfo(
            title="Resource Not Found",
            message=str(exc),
            severity=ErrorSeverity.WARNING,
            suggestions=[
                "Check the resource name or path",
                "Verify the resource exists"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.NAVIGATE_HOME],
            recoverable=True
        )
    
    def _map_workspace_not_found_error(self, exc: WorkspaceNotFoundError) -> TUIErrorInfo:
        """Map workspace not found error."""
        return TUIErrorInfo(
            title="Workspace Not Found",
            message=f"Workspace not found: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Create the workspace first",
                "Check workspace name spelling",
                "Use default workspace if unsure"
            ],
            available_actions=[ErrorAction.NAVIGATE_HOME, ErrorAction.RETRY],
            recoverable=True
        )
    
    def _map_pipeline_not_found_error(self, exc: PipelineNotFoundError) -> TUIErrorInfo:
        """Map pipeline not found error."""
        return TUIErrorInfo(
            title="Pipeline Not Found",
            message=f"Pipeline not found: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check pipeline name or path",
                "Verify pipeline exists in workspace"
            ],
            available_actions=[ErrorAction.NAVIGATE_HOME, ErrorAction.RETRY],
            recoverable=True
        )
    
    def _map_content_not_found_error(self, exc: ContentNotFoundError) -> TUIErrorInfo:
        """Map content not found error."""
        return TUIErrorInfo(
            title="Content Not Found",
            message=f"Content not found: {exc}",
            severity=ErrorSeverity.WARNING,
            suggestions=[
                "Check content path",
                "Verify content exists in workspace"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.IGNORE],
            recoverable=True
        )
    
    def _map_conflict_error(self, exc: ConflictError) -> TUIErrorInfo:
        """Map generic conflict error."""
        return TUIErrorInfo(
            title="Resource Conflict",
            message=str(exc),
            severity=ErrorSeverity.WARNING,
            suggestions=[
                "Use a different name",
                "Check for existing resources"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.CANCEL],
            recoverable=True
        )
    
    def _map_workspace_conflict_error(self, exc: WorkspaceAlreadyExistsError) -> TUIErrorInfo:
        """Map workspace conflict error."""
        return TUIErrorInfo(
            title="Workspace Already Exists",
            message=f"Workspace already exists: {exc}",
            severity=ErrorSeverity.WARNING,
            suggestions=[
                "Use a different workspace name",
                "Switch to existing workspace"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.CANCEL],
            recoverable=True
        )
    
    def _map_access_denied_error(self, exc: WorkspaceAccessDeniedError) -> TUIErrorInfo:
        """Map access denied error."""
        return TUIErrorInfo(
            title="Access Denied",
            message=f"Access denied: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check permissions",
                "Contact administrator"
            ],
            available_actions=[ErrorAction.NAVIGATE_HOME, ErrorAction.CANCEL],
            recoverable=False
        )
    
    def _map_execution_error(self, exc: PipelineExecutionError) -> TUIErrorInfo:
        """Map pipeline execution error."""
        return TUIErrorInfo(
            title="Pipeline Execution Failed",
            message=f"Pipeline execution failed: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check pipeline configuration",
                "Verify inputs are correct",
                "Check network connectivity"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.NAVIGATE_HOME],
            recoverable=True
        )
    
    def _map_step_execution_error(self, exc: StepExecutionError) -> TUIErrorInfo:
        """Map step execution error."""
        return TUIErrorInfo(
            title="Step Execution Failed",
            message=f"Step execution failed: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check step configuration",
                "Verify step dependencies",
                "Try different input values"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.IGNORE, ErrorAction.CANCEL],
            recoverable=True
        )
    
    def _map_template_processing_error(self, exc: TemplateProcessingError) -> TUIErrorInfo:
        """Map template processing error."""
        return TUIErrorInfo(
            title="Template Processing Failed",
            message=f"Template processing failed: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Check template syntax",
                "Verify template variables",
                "Check template file format"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.CANCEL],
            recoverable=True
        )
    
    def _map_service_not_found_error(self, exc: ServiceNotFoundError) -> TUIErrorInfo:
        """Map service not found error."""
        return TUIErrorInfo(
            title="Service Unavailable",
            message=f"Required service not available: {exc}",
            severity=ErrorSeverity.CRITICAL,
            details="A required service dependency is not available.",
            suggestions=[
                "Restart the application",
                "Check service configuration"
            ],
            available_actions=[ErrorAction.RESTART, ErrorAction.REPORT],
            recoverable=False
        )
    
    def _map_circular_dependency_error(self, exc: CircularDependencyError) -> TUIErrorInfo:
        """Map circular dependency error."""
        return TUIErrorInfo(
            title="Configuration Error",
            message=f"Circular dependency detected: {exc}",
            severity=ErrorSeverity.CRITICAL,
            details="Service dependency chain forms a circular reference.",
            suggestions=[
                "Report this issue",
                "Restart the application"
            ],
            available_actions=[ErrorAction.RESTART, ErrorAction.REPORT],
            recoverable=False
        )
    
    def _map_invalid_service_registration_error(self, exc: InvalidServiceRegistrationError) -> TUIErrorInfo:
        """Map invalid service registration error."""
        return TUIErrorInfo(
            title="Configuration Error",
            message=f"Invalid service registration: {exc}",
            severity=ErrorSeverity.CRITICAL,
            suggestions=[
                "Report this issue",
                "Restart the application"
            ],
            available_actions=[ErrorAction.RESTART, ErrorAction.REPORT],
            recoverable=False
        )
    
    def _map_service_lifetime_error(self, exc: ServiceLifetimeError) -> TUIErrorInfo:
        """Map service lifetime error."""
        return TUIErrorInfo(
            title="Service Error",
            message=f"Service lifetime error: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Restart the application",
                "Check service configuration"
            ],
            available_actions=[ErrorAction.RESTART, ErrorAction.REPORT],
            recoverable=False
        )
    
    def _map_async_service_error(self, exc: AsyncServiceError) -> TUIErrorInfo:
        """Map async service error."""
        return TUIErrorInfo(
            title="Async Service Error",
            message=f"Async service error: {exc}",
            severity=ErrorSeverity.ERROR,
            suggestions=[
                "Retry the operation",
                "Check async context"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.CANCEL],
            recoverable=True
        )
    
    def _map_generic_error(self, exc: Exception, context: Optional[TUIContext]) -> TUIErrorInfo:
        """Map generic unhandled exception."""
        return TUIErrorInfo(
            title="Unexpected Error",
            message="An unexpected error occurred",
            severity=ErrorSeverity.CRITICAL,
            details=str(exc),
            technical_details=traceback.format_exc(),
            suggestions=[
                "Try again",
                "Restart the application",
                "Report this issue"
            ],
            available_actions=[ErrorAction.RETRY, ErrorAction.RESTART, ErrorAction.REPORT],
            recoverable=True
        )


# Global error handler instance
_global_error_handler: Optional[TUIErrorHandler] = None


def get_global_error_handler() -> TUIErrorHandler:
    """Get the global TUI error handler."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = TUIErrorHandler()
    return _global_error_handler


def initialize_error_handler(app: Optional[App] = None) -> TUIErrorHandler:
    """Initialize the global TUI error handler."""
    global _global_error_handler
    _global_error_handler = TUIErrorHandler(app)
    return _global_error_handler


async def handle_error(
    exception: Exception,
    context: Optional[TUIContext] = None,
    show_modal: bool = True
) -> bool:
    """Handle an error using the global error handler."""
    error_handler = get_global_error_handler()
    return await error_handler.handle_error(exception, context, show_modal)


class TUIErrorDisplay:
    """Utility class for creating error displays."""
    
    @staticmethod
    def create_inline_error(message: str, severity: ErrorSeverity = ErrorSeverity.ERROR) -> Static:
        """Create an inline error display widget."""
        error_info = TUIErrorInfo(
            title="Error",
            message=message,
            severity=severity
        )
        
        icon = error_info.get_icon()
        color_class = error_info.get_color_class()
        
        return Static(
            f"{icon} {message}",
            classes=f"inline-error {color_class}"
        )
    
    @staticmethod
    def create_notification(message: str, severity: ErrorSeverity = ErrorSeverity.INFO) -> Static:
        """Create a notification widget."""
        error_info = TUIErrorInfo(
            title="Notification",
            message=message,
            severity=severity
        )
        
        icon = error_info.get_icon()
        color_class = error_info.get_color_class()
        
        return Static(
            f"{icon} {message}",
            classes=f"notification {color_class}"
        )