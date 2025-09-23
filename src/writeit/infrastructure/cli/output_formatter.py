"""CLI output formatting for WriteIt.

Provides comprehensive output formatting capabilities for different data types
and output formats (table, JSON, YAML) with rich styling and user-friendly display.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.columns import Columns

from ...application.services import (
    PipelineExecutionResult,
    WorkspaceCreationRequest,
    ContentGenerationRequest,
)


class OutputFormat(str, Enum):
    """Supported output formats."""
    TABLE = "table"
    JSON = "json"
    YAML = "yaml"
    TREE = "tree"
    PLAIN = "plain"


class CLIOutputFormatter:
    """
    Comprehensive output formatter for WriteIt CLI.
    
    Handles formatting of various data types with support for multiple
    output formats and rich styling.
    """
    
    def __init__(self, console: Optional[Console] = None, format: OutputFormat = OutputFormat.TABLE):
        """Initialize output formatter."""
        self.console = console or Console()
        self.format = format
    
    def format_and_print(self, data: Any, title: Optional[str] = None, **kwargs) -> None:
        """Format and print data according to configured format."""
        if self.format == OutputFormat.JSON:
            self.print_json(data, title)
        elif self.format == OutputFormat.YAML:
            self.print_yaml(data, title)
        elif self.format == OutputFormat.TREE:
            self.print_tree(data, title)
        elif self.format == OutputFormat.PLAIN:
            self.print_plain(data, title)
        else:  # TABLE
            self.print_table(data, title, **kwargs)
    
    # Table formatting
    
    def print_table(self, data: Any, title: Optional[str] = None, **kwargs) -> None:
        """Print data as a formatted table."""
        if isinstance(data, list):
            self._print_list_table(data, title, **kwargs)
        elif isinstance(data, dict):
            self._print_dict_table(data, title, **kwargs)
        else:
            self._print_simple_table(data, title, **kwargs)
    
    def _print_list_table(self, data: List[Any], title: Optional[str] = None, **kwargs) -> None:
        """Print list data as table."""
        if not data:
            self.console.print("[dim]No data to display[/dim]")
            return
        
        table = Table(title=title, show_header=True, header_style="bold cyan")
        
        # Handle different list item types
        first_item = data[0]
        
        if isinstance(first_item, dict):
            # List of dictionaries - use keys as columns
            columns = first_item.keys()
            for col in columns:
                table.add_column(self._format_column_name(col), style="white")
            
            for item in data:
                values = []
                for col in columns:
                    value = item.get(col, '')
                    values.append(self._format_cell_value(value))
                table.add_row(*values)
        
        elif hasattr(first_item, '__dict__'):
            # List of objects - use attributes as columns
            columns = [attr for attr in vars(first_item).keys() if not attr.startswith('_')]
            for col in columns:
                table.add_column(self._format_column_name(col), style="white")
            
            for item in data:
                values = []
                for col in columns:
                    value = getattr(item, col, '')
                    values.append(self._format_cell_value(value))
                table.add_row(*values)
        
        else:
            # List of simple values
            table.add_column("Value", style="cyan")
            for item in data:
                table.add_row(self._format_cell_value(item))
        
        self.console.print(table)
    
    def _print_dict_table(self, data: Dict[str, Any], title: Optional[str] = None, **kwargs) -> None:
        """Print dictionary data as table."""
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")
        
        for key, value in data.items():
            formatted_key = self._format_column_name(key)
            formatted_value = self._format_cell_value(value)
            table.add_row(formatted_key, formatted_value)
        
        self.console.print(table)
    
    def _print_simple_table(self, data: Any, title: Optional[str] = None, **kwargs) -> None:
        """Print simple data as table."""
        table = Table(title=title, show_header=True, header_style="bold cyan")
        table.add_column("Value", style="white")
        table.add_row(self._format_cell_value(data))
        self.console.print(table)
    
    # JSON formatting
    
    def print_json(self, data: Any, title: Optional[str] = None) -> None:
        """Print data as formatted JSON."""
        try:
            # Convert data to JSON-serializable format
            json_data = self._prepare_for_json(data)
            json_str = json.dumps(json_data, indent=2, default=str)
            
            if title:
                self.console.print(f"\n[bold cyan]{title}[/bold cyan]")
            
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
            self.console.print(syntax)
        
        except Exception as e:
            self.console.print(f"[red]Error formatting JSON: {e}[/red]")
            self.console.print(str(data))
    
    # YAML formatting
    
    def print_yaml(self, data: Any, title: Optional[str] = None) -> None:
        """Print data as formatted YAML."""
        try:
            import yaml
            
            # Convert data to YAML-serializable format
            yaml_data = self._prepare_for_json(data)  # Same preparation as JSON
            yaml_str = yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)
            
            if title:
                self.console.print(f"\n[bold cyan]{title}[/bold cyan]")
            
            syntax = Syntax(yaml_str, "yaml", theme="monokai", line_numbers=False)
            self.console.print(syntax)
        
        except ImportError:
            self.console.print("[yellow]YAML output requires PyYAML package. Falling back to JSON.[/yellow]")
            self.print_json(data, title)
        except Exception as e:
            self.console.print(f"[red]Error formatting YAML: {e}[/red]")
            self.console.print(str(data))
    
    # Tree formatting
    
    def print_tree(self, data: Any, title: Optional[str] = None) -> None:
        """Print data as a tree structure."""
        tree_title = title or "Data"
        tree = Tree(f"[bold cyan]{tree_title}[/bold cyan]")
        
        self._add_to_tree(tree, data)
        self.console.print(tree)
    
    def _add_to_tree(self, parent: Tree, data: Any, key: Optional[str] = None) -> None:
        """Recursively add data to tree."""
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, (dict, list)):
                    branch = parent.add(f"[cyan]{k}[/cyan]")
                    self._add_to_tree(branch, v, k)
                else:
                    parent.add(f"[cyan]{k}[/cyan]: {self._format_cell_value(v)}")
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    branch = parent.add(f"[dim][{i}][/dim]")
                    self._add_to_tree(branch, item)
                else:
                    parent.add(f"[dim][{i}][/dim] {self._format_cell_value(item)}")
        
        else:
            parent.add(self._format_cell_value(data))
    
    # Plain formatting
    
    def print_plain(self, data: Any, title: Optional[str] = None) -> None:
        """Print data as plain text."""
        if title:
            self.console.print(f"{title}:")
        
        if isinstance(data, (list, dict)):
            for line in self._format_plain_recursive(data):
                self.console.print(line)
        else:
            self.console.print(str(data))
    
    def _format_plain_recursive(self, data: Any, indent: int = 0) -> List[str]:
        """Recursively format data for plain output."""
        lines = []
        prefix = "  " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.extend(self._format_plain_recursive(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}[{i}]:")
                    lines.extend(self._format_plain_recursive(item, indent + 1))
                else:
                    lines.append(f"{prefix}[{i}] {item}")
        
        else:
            lines.append(f"{prefix}{data}")
        
        return lines
    
    # Specialized formatters
    
    def print_pipeline_execution_result(self, result: PipelineExecutionResult) -> None:
        """Print pipeline execution result with rich formatting."""
        # Status panel
        status_color = "green" if result.execution_status.value == "completed" else "yellow"
        status_panel = Panel(
            f"[{status_color}]{result.execution_status.value.upper()}[/{status_color}]",
            title="Execution Status",
            border_style=status_color
        )
        self.console.print(status_panel)
        
        # Results table
        if result.step_results:
            table = Table(title="Step Results", show_header=True, header_style="bold cyan")
            table.add_column("Step", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Output", style="dim")
            
            for step, output in result.step_results.items():
                status = "✓" if output else "❌"
                output_preview = str(output)[:50] + "..." if len(str(output)) > 50 else str(output)
                table.add_row(step, status, output_preview)
            
            self.console.print(table)
        
        # Metrics if available
        if result.execution_metrics:
            self.print_table(result.execution_metrics, "Execution Metrics")
        
        # Errors and warnings
        if result.errors:
            self.console.print("\n[red]❌ Errors:[/red]")
            for error in result.errors:
                self.console.print(f"  • {error}")
        
        if result.warnings:
            self.console.print("\n[yellow]⚠️ Warnings:[/yellow]")
            for warning in result.warnings:
                self.console.print(f"  • {warning}")
    
    def print_workspace_info(self, workspace_data: Dict[str, Any]) -> None:
        """Print workspace information with rich formatting."""
        workspace = workspace_data.get("workspace", {})
        
        # Workspace header
        name = workspace.get("name", "Unknown")
        is_active = workspace.get("is_active", False)
        status = "🟢 Active" if is_active else "⚪ Inactive"
        
        header = Panel(
            f"[bold cyan]{name}[/bold cyan]\n{status}",
            title="Workspace",
            border_style="cyan"
        )
        self.console.print(header)
        
        # Create columns for different sections
        sections = []
        
        # Configuration section
        if "configuration" in workspace_data:
            config_table = Table(title="Configuration", show_header=False)
            config_table.add_column("Key", style="cyan")
            config_table.add_column("Value", style="white")
            
            config = workspace_data["configuration"]
            for key, value in config.items():
                if value is not None:
                    config_table.add_row(self._format_column_name(key), str(value))
            
            sections.append(config_table)
        
        # Analytics section
        if "analytics" in workspace_data:
            analytics_table = Table(title="Analytics", show_header=False)
            analytics_table.add_column("Metric", style="cyan")
            analytics_table.add_column("Value", style="white")
            
            analytics = workspace_data["analytics"]
            for key, value in analytics.items():
                if isinstance(value, dict):
                    continue  # Skip nested dicts for this view
                analytics_table.add_row(self._format_column_name(key), str(value))
            
            sections.append(analytics_table)
        
        # Display sections in columns
        if sections:
            self.console.print(Columns(sections, equal=True))
    
    def create_progress_bar(self, description: str = "Processing...") -> Progress:
        """Create a progress bar with consistent styling."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TaskProgressColumn(),
            console=self.console,
        )
    
    # Helper methods
    
    def _format_column_name(self, name: str) -> str:
        """Format column name for display."""
        return name.replace('_', ' ').title()
    
    def _format_cell_value(self, value: Any) -> str:
        """Format cell value for display."""
        if value is None:
            return "[dim]None[/dim]"
        elif isinstance(value, bool):
            return "✓" if value else "✗"
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, Path):
            return str(value)
        elif isinstance(value, (list, dict)) and len(str(value)) > 50:
            return f"{type(value).__name__}({len(value)} items)"
        else:
            return str(value)
    
    def _prepare_for_json(self, data: Any) -> Any:
        """Prepare data for JSON serialization."""
        if hasattr(data, 'to_dict'):
            return data.to_dict()
        elif hasattr(data, '__dict__'):
            # Convert object to dict, handling nested objects
            result = {}
            for key, value in data.__dict__.items():
                if not key.startswith('_'):
                    result[key] = self._prepare_for_json(value)
            return result
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        elif isinstance(data, dict):
            return {key: self._prepare_for_json(value) for key, value in data.items()}
        elif isinstance(data, (datetime, Path)):
            return str(data)
        else:
            return data


def create_formatter(format: OutputFormat = OutputFormat.TABLE, console: Optional[Console] = None) -> CLIOutputFormatter:
    """Create a CLI output formatter."""
    return CLIOutputFormatter(console, format)