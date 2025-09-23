"""CLI-specific error handling for WriteIt.

Provides comprehensive error handling, user-friendly error messages,
and error recovery suggestions for CLI operations.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
import logging
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ...application.services import (
    PipelineApplicationError,
    WorkspaceApplicationError,
    ContentApplicationError,
    ExecutionApplicationError,
)
from ...domains.pipeline.exceptions import (
    PipelineValidationError,
    PipelineExecutionError,
    PipelineNotFoundError,
)
from ...domains.workspace.exceptions import (
    WorkspaceNotFoundError,
    WorkspaceCreationError,
)
from ...domains.content.exceptions import (
    TemplateNotFoundError,
    ContentValidationError,
)
from ...domains.execution.exceptions import (
    LLMProviderError,
    CacheError,
)
from ..persistence.exceptions import StorageError


class ErrorSeverity(str, Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ErrorSuggestion:
    """Error recovery suggestion."""
    action: str
    description: str
    command: Optional[str] = None
    priority: int = 1  # 1 = highest priority


@dataclass
class ErrorContext:
    """Context information for error handling."""
    command_name: str
    workspace_name: Optional[str] = None
    pipeline_name: Optional[str] = None
    template_name: Optional[str] = None
    user_input: Optional[Dict[str, Any]] = None
    verbose: bool = False


class CLIErrorHandler:
    """
    Comprehensive CLI error handler for WriteIt.
    
    Provides user-friendly error messages, recovery suggestions,
    and appropriate exit codes for different types of errors.
    """
    
    def __init__(self, console: Optional[Console] = None):
        """Initialize error handler."""
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)
    
    def handle_error(
        self, 
        error: Exception, 
        context: ErrorContext
    ) -> int:
        """
        Handle error with user-friendly output and return appropriate exit code.
        
        Args:
            error: The exception that occurred
            context: Context information for better error handling
            
        Returns:
            Appropriate exit code
        """
        severity = self._determine_severity(error)
        message = self._format_error_message(error, context)
        suggestions = self._generate_suggestions(error, context)
        
        # Display error to user
        self._display_error(error, message, severity, suggestions, context)
        
        # Log error for debugging
        self._log_error(error, context)
        
        # Return appropriate exit code
        return self._get_exit_code(error, severity)
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity."""
        if isinstance(error, (
            WorkspaceNotFoundError,
            PipelineNotFoundError,
            TemplateNotFoundError,
        )):
            return ErrorSeverity.MEDIUM
        
        elif isinstance(error, (
            PipelineValidationError,
            ContentValidationError,
        )):
            return ErrorSeverity.LOW
        
        elif isinstance(error, (
            WorkspaceCreationError,
            PipelineExecutionError,
            LLMProviderError,
        )):
            return ErrorSeverity.HIGH
        
        elif isinstance(error, (
            StorageError,
            CacheError,
        )):
            return ErrorSeverity.CRITICAL
        
        else:
            return ErrorSeverity.MEDIUM
    
    def _format_error_message(self, error: Exception, context: ErrorContext) -> str:
        """Format user-friendly error message."""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Format specific error types
        if isinstance(error, WorkspaceNotFoundError):
            return f"Workspace '{context.workspace_name or 'unknown'}' was not found. Make sure it exists and you have access to it."
        
        elif isinstance(error, PipelineNotFoundError):
            return f"Pipeline '{context.pipeline_name or 'unknown'}' was not found. Check the pipeline name and try again."
        
        elif isinstance(error, TemplateNotFoundError):
            return f"Template '{context.template_name or 'unknown'}' was not found. Verify the template name and ensure it exists."
        
        elif isinstance(error, PipelineValidationError):
            return f"Pipeline validation failed: {error_message}"
        
        elif isinstance(error, ContentValidationError):
            return f"Content validation failed: {error_message}"
        
        elif isinstance(error, WorkspaceCreationError):
            return f"Failed to create workspace: {error_message}"
        
        elif isinstance(error, PipelineExecutionError):
            return f"Pipeline execution failed: {error_message}"
        
        elif isinstance(error, LLMProviderError):
            return f"LLM provider error: {error_message}. Check your API keys and network connection."
        
        elif isinstance(error, StorageError):
            return f"Storage error: {error_message}. Check file permissions and disk space."
        
        elif isinstance(error, CacheError):
            return f"Cache error: {error_message}. Try clearing the cache or running without cache."
        
        else:
            # Generic error message
            return f"An error occurred: {error_message}"
    
    def _generate_suggestions(self, error: Exception, context: ErrorContext) -> List[ErrorSuggestion]:
        """Generate recovery suggestions for the error."""
        suggestions = []
        
        if isinstance(error, WorkspaceNotFoundError):
            suggestions.extend([
                ErrorSuggestion(
                    action="List available workspaces",
                    description="See what workspaces are available",
                    command="writeit workspace list",
                    priority=1
                ),
                ErrorSuggestion(
                    action="Create the workspace",
                    description="Create the workspace if it doesn't exist",
                    command=f"writeit workspace create {context.workspace_name}" if context.workspace_name else "writeit workspace create <name>",
                    priority=2
                ),
            ])
        
        elif isinstance(error, PipelineNotFoundError):
            suggestions.extend([
                ErrorSuggestion(
                    action="List available pipelines",
                    description="See what pipelines are available",
                    command="writeit list-pipelines",
                    priority=1
                ),
                ErrorSuggestion(
                    action="Check pipeline spelling",
                    description="Verify the pipeline name is spelled correctly",
                    priority=2
                ),
            ])
        
        elif isinstance(error, TemplateNotFoundError):
            suggestions.extend([
                ErrorSuggestion(
                    action="List available templates",
                    description="See what templates are available",
                    command="writeit template list",
                    priority=1
                ),
                ErrorSuggestion(
                    action="Check template location",
                    description="Verify the template exists in the current workspace",
                    priority=2
                ),
            ])
        
        elif isinstance(error, PipelineValidationError):
            suggestions.extend([
                ErrorSuggestion(
                    action="Run detailed validation",
                    description="Get more information about validation issues",
                    command=f"writeit validate {context.pipeline_name} --detailed" if context.pipeline_name else "writeit validate <pipeline> --detailed",
                    priority=1
                ),
                ErrorSuggestion(
                    action="Check pipeline syntax",
                    description="Review the pipeline YAML for syntax errors",
                    priority=2
                ),
            ])
        
        elif isinstance(error, LLMProviderError):
            suggestions.extend([
                ErrorSuggestion(
                    action="Check API keys",
                    description="Verify your LLM provider API keys are set correctly",
                    priority=1
                ),
                ErrorSuggestion(
                    action="Check network connection",
                    description="Ensure you have internet access",
                    priority=2
                ),
                ErrorSuggestion(
                    action="Check provider status",
                    description="Verify the LLM provider service is available",
                    priority=3
                ),
            ])
        
        elif isinstance(error, StorageError):
            suggestions.extend([
                ErrorSuggestion(
                    action="Check disk space",
                    description="Ensure you have sufficient disk space",
                    priority=1
                ),
                ErrorSuggestion(
                    action="Check permissions",
                    description="Verify you have write permissions to the WriteIt directory",
                    priority=2
                ),
                ErrorSuggestion(
                    action="Reinitialize WriteIt",
                    description="Try reinitializing WriteIt if storage is corrupted",
                    command="writeit init --migrate",
                    priority=3
                ),
            ])
        
        else:
            # Generic suggestions
            suggestions.extend([
                ErrorSuggestion(
                    action="Try with verbose output",
                    description="Run the command with --verbose for more details",
                    command=f"{context.command_name} --verbose",
                    priority=1
                ),
                ErrorSuggestion(
                    action="Check WriteIt status",
                    description="Verify WriteIt is properly initialized",
                    command="writeit workspace info",
                    priority=2
                ),
            ])
        
        return sorted(suggestions, key=lambda x: x.priority)
    
    def _display_error(
        self, 
        error: Exception, 
        message: str, 
        severity: ErrorSeverity,
        suggestions: List[ErrorSuggestion],
        context: ErrorContext
    ) -> None:
        """Display error to user with formatting."""
        # Choose color and icon based on severity
        if severity == ErrorSeverity.CRITICAL:
            color = "bold red"
            icon = "💥"
        elif severity == ErrorSeverity.HIGH:
            color = "red"
            icon = "❌"
        elif severity == ErrorSeverity.MEDIUM:
            color = "yellow"
            icon = "⚠️"
        else:  # LOW
            color = "orange3"
            icon = "⚠️"
        
        # Display main error
        error_text = Text(f"{icon} {message}", style=color)
        panel = Panel(
            error_text,
            title=f"Error in {context.command_name}",
            border_style=color.split()[0] if " " in color else color
        )
        self.console.print(panel)
        
        # Display suggestions if available
        if suggestions:
            self.console.print("\n[cyan]💡 Suggestions:[/cyan]")
            for i, suggestion in enumerate(suggestions[:3], 1):  # Show top 3 suggestions
                self.console.print(f"  {i}. [bold]{suggestion.action}[/bold]")
                self.console.print(f"     {suggestion.description}")
                if suggestion.command:
                    self.console.print(f"     [dim]Command:[/dim] [green]{suggestion.command}[/green]")
                self.console.print()
        
        # Show debug information in verbose mode
        if context.verbose:
            self._display_debug_info(error, context)
    
    def _display_debug_info(self, error: Exception, context: ErrorContext) -> None:
        """Display debug information in verbose mode."""
        debug_info = Text("Debug Information", style="dim")
        debug_panel = Panel(
            f"Error Type: {type(error).__name__}\n"
            f"Error Message: {str(error)}\n"
            f"Command: {context.command_name}\n"
            f"Workspace: {context.workspace_name or 'None'}\n"
            f"Pipeline: {context.pipeline_name or 'None'}\n"
            f"Template: {context.template_name or 'None'}",
            title=debug_info,
            border_style="dim"
        )
        self.console.print(debug_panel)
    
    def _log_error(self, error: Exception, context: ErrorContext) -> None:
        """Log error for debugging purposes."""
        self.logger.error(
            f"CLI Error in {context.command_name}: {type(error).__name__}: {error}",
            extra={
                "error_type": type(error).__name__,
                "command": context.command_name,
                "workspace": context.workspace_name,
                "pipeline": context.pipeline_name,
                "template": context.template_name,
            },
            exc_info=True
        )
    
    def _get_exit_code(self, error: Exception, severity: ErrorSeverity) -> int:
        """Get appropriate exit code for error."""
        if severity == ErrorSeverity.CRITICAL:
            return 2
        elif isinstance(error, (
            WorkspaceNotFoundError,
            PipelineNotFoundError,
            TemplateNotFoundError,
        )):
            return 3  # Not found errors
        elif isinstance(error, (
            PipelineValidationError,
            ContentValidationError,
        )):
            return 4  # Validation errors
        else:
            return 1  # Generic error


def handle_cli_error(
    error: Exception,
    command_name: str,
    console: Optional[Console] = None,
    **context_kwargs
) -> int:
    """
    Convenience function to handle CLI errors.
    
    Args:
        error: The exception to handle
        command_name: Name of the command that failed
        console: Console instance for output
        **context_kwargs: Additional context parameters
        
    Returns:
        Appropriate exit code
    """
    handler = CLIErrorHandler(console)
    context = ErrorContext(command_name=command_name, **context_kwargs)
    return handler.handle_error(error, context)