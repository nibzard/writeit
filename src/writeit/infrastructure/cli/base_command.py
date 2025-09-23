"""Base CLI command infrastructure for WriteIt.

Provides common functionality for all CLI commands including context management,
error handling, and integration with the CQRS application layer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any, Dict, List, Union
from pathlib import Path
import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...shared.dependencies.container import Container
from ...application.services import (
    PipelineApplicationService,
    WorkspaceApplicationService,
    ContentApplicationService,
    ExecutionApplicationService,
)
from ..persistence.exceptions import StorageError
from ...domains.workspace.value_objects import WorkspaceName


@dataclass
class CommandContext:
    """Context for CLI command execution."""
    workspace_name: Optional[str] = None
    verbose: bool = False
    dry_run: bool = False
    force: bool = False
    output_format: str = "table"  # table, json, yaml
    container: Optional[Container] = None
    console: Optional[Console] = None
    
    def get_workspace_name(self) -> Optional[WorkspaceName]:
        """Get validated workspace name if provided."""
        if self.workspace_name:
            return WorkspaceName(self.workspace_name)
        return None


class CommandExecutionError(Exception):
    """Base exception for command execution errors."""
    def __init__(self, message: str, exit_code: int = 1, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.exit_code = exit_code
        self.details = details or {}


class ValidationCommandError(CommandExecutionError):
    """Command validation failed."""
    pass


class ServiceCommandError(CommandExecutionError):
    """Service layer error in command."""
    pass


class BaseCommand(ABC):
    """
    Base class for all CLI commands in WriteIt.
    
    Provides common functionality including:
    - Service initialization through DI container
    - Error handling and user-friendly error messages
    - Output formatting options
    - Context management
    - Async execution support
    """
    
    def __init__(self, context: CommandContext):
        """Initialize command with context."""
        self.context = context
        self.console = context.console or Console()
        
        # Initialize DI container if not provided
        if not context.container:
            from ...application.di_config import DIConfiguration
            self.container = DIConfiguration.create_container()
        else:
            self.container = context.container
    
    # Service access methods
    
    def get_pipeline_service(self) -> PipelineApplicationService:
        """Get pipeline application service."""
        return self.container.resolve(PipelineApplicationService)
    
    def get_workspace_service(self) -> WorkspaceApplicationService:
        """Get workspace application service."""
        return self.container.resolve(WorkspaceApplicationService)
    
    def get_content_service(self) -> ContentApplicationService:
        """Get content application service."""
        return self.container.resolve(ContentApplicationService)
    
    def get_execution_service(self) -> ExecutionApplicationService:
        """Get execution application service."""
        return self.container.resolve(ExecutionApplicationService)
    
    # Abstract methods to be implemented by subclasses
    
    @abstractmethod
    async def execute(self) -> Any:
        """Execute the command logic."""
        pass
    
    @abstractmethod
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        pass
    
    # Common execution flow
    
    def run(self) -> Any:
        """
        Main command execution entry point.
        
        Handles validation, execution, and error handling.
        """
        try:
            # Validate arguments
            self.validate_arguments()
            
            # Execute command (async)
            return asyncio.run(self._execute_with_error_handling())
            
        except CommandExecutionError as e:
            self._handle_command_error(e)
            raise typer.Exit(e.exit_code)
        except Exception as e:
            self._handle_unexpected_error(e)
            raise typer.Exit(1)
    
    async def _execute_with_error_handling(self) -> Any:
        """Execute command with comprehensive error handling."""
        try:
            return await self.execute()
        except Exception as e:
            # Convert service errors to command errors
            if self._is_service_error(e):
                raise ServiceCommandError(
                    message=self._format_service_error(e),
                    details={"original_error": str(e), "error_type": type(e).__name__}
                )
            else:
                raise
    
    # Error handling methods
    
    def _handle_command_error(self, error: CommandExecutionError) -> None:
        """Handle command execution errors."""
        if isinstance(error, ValidationCommandError):
            self.console.print(f"[red]❌ Validation Error:[/red] {error}")
            if self.context.verbose and error.details:
                self._print_error_details(error.details)
        elif isinstance(error, ServiceCommandError):
            self.console.print(f"[red]❌ Service Error:[/red] {error}")
            if self.context.verbose and error.details:
                self._print_error_details(error.details)
        else:
            self.console.print(f"[red]❌ Command Error:[/red] {error}")
    
    def _handle_unexpected_error(self, error: Exception) -> None:
        """Handle unexpected errors."""
        self.console.print(f"[red]❌ Unexpected Error:[/red] {error}")
        if self.context.verbose:
            import traceback
            self.console.print("\n[dim]Traceback:[/dim]")
            self.console.print(traceback.format_exc())
    
    def _print_error_details(self, details: Dict[str, Any]) -> None:
        """Print error details in verbose mode."""
        if not details:
            return
        
        self.console.print("\n[dim]Error Details:[/dim]")
        for key, value in details.items():
            self.console.print(f"  [dim]{key}:[/dim] {value}")
    
    def _is_service_error(self, error: Exception) -> bool:
        """Check if error is from service layer."""
        service_error_types = (
            "PipelineApplicationError",
            "WorkspaceApplicationError", 
            "ContentApplicationError",
            "ExecutionApplicationError",
            "StorageError",
        )
        return any(err_type in str(type(error)) for err_type in service_error_types)
    
    def _format_service_error(self, error: Exception) -> str:
        """Format service error for user display."""
        error_message = str(error)
        
        # Clean up technical error messages for user consumption
        if "not found" in error_message.lower():
            return error_message  # These are usually user-friendly
        elif "validation" in error_message.lower():
            return error_message  # Validation errors are user-friendly
        else:
            # Generic service error
            return f"Operation failed: {error_message}"
    
    # Output formatting methods
    
    def format_output(self, data: Any, title: Optional[str] = None) -> None:
        """Format and print output based on context preferences."""
        if self.context.output_format == "json":
            self._format_json_output(data)
        elif self.context.output_format == "yaml":
            self._format_yaml_output(data)
        else:
            self._format_table_output(data, title)
    
    def _format_json_output(self, data: Any) -> None:
        """Format output as JSON."""
        import json
        from rich.syntax import Syntax
        
        try:
            if hasattr(data, 'to_dict'):
                json_data = data.to_dict()
            elif hasattr(data, '__dict__'):
                json_data = data.__dict__
            else:
                json_data = data
            
            json_str = json.dumps(json_data, indent=2, default=str)
            syntax = Syntax(json_str, "json", theme="monokai")
            self.console.print(syntax)
        except Exception:
            self.console.print(str(data))
    
    def _format_yaml_output(self, data: Any) -> None:
        """Format output as YAML."""
        try:
            import yaml
            from rich.syntax import Syntax
            
            if hasattr(data, 'to_dict'):
                yaml_data = data.to_dict()
            elif hasattr(data, '__dict__'):
                yaml_data = data.__dict__
            else:
                yaml_data = data
            
            yaml_str = yaml.dump(yaml_data, default_flow_style=False)
            syntax = Syntax(yaml_str, "yaml", theme="monokai")
            self.console.print(syntax)
        except ImportError:
            self.console.print("[red]YAML output requires PyYAML package[/red]")
            self._format_json_output(data)
        except Exception:
            self.console.print(str(data))
    
    def _format_table_output(self, data: Any, title: Optional[str] = None) -> None:
        """Format output as table (default)."""
        if isinstance(data, list) and data:
            self._format_list_as_table(data, title)
        elif isinstance(data, dict):
            self._format_dict_as_table(data, title)
        else:
            self.console.print(str(data))
    
    def _format_list_as_table(self, data: List[Any], title: Optional[str] = None) -> None:
        """Format list data as table."""
        if not data:
            self.console.print("[dim]No data to display[/dim]")
            return
        
        table = Table(title=title)
        
        # Extract columns from first item
        first_item = data[0]
        if isinstance(first_item, dict):
            for key in first_item.keys():
                table.add_column(key.replace('_', ' ').title(), style="cyan")
            
            for item in data:
                values = [str(item.get(key, '')) for key in first_item.keys()]
                table.add_row(*values)
        else:
            table.add_column("Value", style="cyan")
            for item in data:
                table.add_row(str(item))
        
        self.console.print(table)
    
    def _format_dict_as_table(self, data: Dict[str, Any], title: Optional[str] = None) -> None:
        """Format dictionary data as table."""
        table = Table(title=title)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="white")
        
        for key, value in data.items():
            table.add_row(key.replace('_', ' ').title(), str(value))
        
        self.console.print(table)
    
    # Utility methods
    
    def print_success(self, message: str, title: Optional[str] = None) -> None:
        """Print success message."""
        if title:
            panel = Panel(f"[green]{message}[/green]", title=f"✓ {title}", border_style="green")
            self.console.print(panel)
        else:
            self.console.print(f"[green]✓ {message}[/green]")
    
    def print_warning(self, message: str, title: Optional[str] = None) -> None:
        """Print warning message."""
        if title:
            panel = Panel(f"[yellow]{message}[/yellow]", title=f"⚠️ {title}", border_style="yellow")
            self.console.print(panel)
        else:
            self.console.print(f"[yellow]⚠️ {message}[/yellow]")
    
    def print_info(self, message: str, title: Optional[str] = None) -> None:
        """Print info message."""
        if title:
            panel = Panel(f"[cyan]{message}[/cyan]", title=f"ℹ️ {title}", border_style="cyan")
            self.console.print(panel)
        else:
            self.console.print(f"[cyan]ℹ️ {message}[/cyan]")
    
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """Confirm action with user."""
        if self.context.force:
            return True
        
        default_text = "Y/n" if default else "y/N"
        prompt = f"[cyan]{message}[/cyan] [dim]({default_text})[/dim]: "
        
        response = self.console.input(prompt).lower().strip()
        
        if not response:
            return default
        
        return response in ["y", "yes", "true", "1"]