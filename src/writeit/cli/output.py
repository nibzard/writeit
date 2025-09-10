# ABOUTME: Rich output utilities for WriteIt CLI
# ABOUTME: Provides console instance, formatters, and reusable Rich components

from typing import List, Optional, Dict, Any
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.syntax import Syntax
from rich.tree import Tree
from rich.text import Text
from rich.theme import Theme

from writeit.validation.validation_result import ValidationResult, ValidationSummary, IssueType


# Custom WriteIt theme
WRITEIT_THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "primary": "bold blue",
    "secondary": "dim",
    "workspace.active": "bold green",
    "workspace.inactive": "dim white",
    "pipeline.name": "cyan",
    "path": "bright_black",
})

# Global console instance
console = Console(theme=WRITEIT_THEME)


def print_success(message: str, title: Optional[str] = None) -> None:
    """Print a success message with rich formatting."""
    if title:
        panel = Panel(f"[success]{message}[/success]", title=f"✓ {title}", border_style="green")
        console.print(panel)
    else:
        console.print(f"[success]✓ {message}[/success]")


def print_error(message: str, title: Optional[str] = None) -> None:
    """Print an error message with rich formatting."""
    if title:
        panel = Panel(f"[error]{message}[/error]", title=f"❌ {title}", border_style="red")
        console.print(panel)
    else:
        console.print(f"[error]❌ {message}[/error]")


def print_warning(message: str, title: Optional[str] = None) -> None:
    """Print a warning message with rich formatting."""
    if title:
        panel = Panel(f"[warning]{message}[/warning]", title=f"⚠️ {title}", border_style="yellow")
        console.print(panel)
    else:
        console.print(f"[warning]⚠️ {message}[/warning]")


def print_info(message: str, title: Optional[str] = None) -> None:
    """Print an info message with rich formatting."""
    if title:
        panel = Panel(f"[info]{message}[/info]", title=f"ℹ️ {title}", border_style="cyan")
        console.print(panel)
    else:
        console.print(f"[info]ℹ️ {message}[/info]")


def create_progress() -> Progress:
    """Create a progress bar with WriteIt styling."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        console=console,
    )


def create_workspace_table(workspaces: List[str], active_workspace: Optional[str] = None) -> Table:
    """Create a Rich table for workspace listing."""
    table = Table(title="Available Workspaces")
    table.add_column("Name", style="workspace.inactive", no_wrap=True)
    table.add_column("Status", style="secondary", no_wrap=True)
    
    for workspace in workspaces:
        if workspace == active_workspace:
            name_style = "workspace.active"
            status = "✓ Active"
            status_style = "success"
        else:
            name_style = "workspace.inactive"
            status = ""
            status_style = "secondary"
        
        table.add_row(
            Text(workspace, style=name_style),
            Text(status, style=status_style)
        )
    
    return table


def create_workspace_info_table(workspace_name: str, config: Dict[str, Any], stats: Optional[Dict[str, Any]] = None) -> Table:
    """Create a Rich table for workspace information."""
    table = Table(title=f"Workspace: {workspace_name}")
    table.add_column("Property", style="primary", no_wrap=True)
    table.add_column("Value", style="info")
    
    # Add basic workspace info
    if "created_at" in config:
        created_at = config["created_at"]
        if isinstance(created_at, str):
            table.add_row("Created", created_at)
    
    if "default_pipeline" in config and config["default_pipeline"]:
        table.add_row("Default Pipeline", config["default_pipeline"])
    else:
        table.add_row("Default Pipeline", Text("None", style="secondary"))
    
    # Add storage stats if available
    if stats:
        entries_count = stats.get("entries", 0)
        table.add_row("Stored Entries", str(entries_count))
    
    return table


def create_pipeline_table(pipelines: List[tuple], title: str = "Pipelines") -> Table:
    """Create a Rich table for pipeline listing."""
    table = Table(title=title)
    table.add_column("Name", style="pipeline.name", no_wrap=True)
    table.add_column("Type", style="secondary", no_wrap=True)
    
    for name, pipeline_type in pipelines:
        table.add_row(name, pipeline_type)
    
    return table


def format_validation_results(results: List[ValidationResult], detailed: bool = False, show_suggestions: bool = False) -> None:
    """Format and display validation results with Rich formatting."""
    if len(results) == 1:
        # Single file - show detailed results
        result = results[0]
        
        # File header
        console.print(f"\n[primary]Validating:[/primary] [path]{result.file_path}[/path]")
        
        if result.is_valid:
            print_success(f"File is valid ({result.file_type})")
        else:
            print_error(f"File has {len(result.issues)} issues ({result.file_type})")
        
        # Show issues
        if result.issues:
            for issue in result.issues:
                format_validation_issue(issue, show_suggestions)
    
    else:
        # Multiple files - show summary
        summary = ValidationSummary(results)
        
        console.print("\n[primary]Validation Summary[/primary]")
        console.print(f"Files processed: {len(results)}")
        console.print(f"[success]Valid files: {summary.valid_files}[/success]")
        
        if summary.failed_files > 0:
            console.print(f"[error]Failed files: {summary.failed_files}[/error]")
        
        # Show details for each file
        if detailed:
            for result in results:
                console.print(f"\n[path]{result.file_path}[/path]: ", end="")
                
                if result.is_valid:
                    console.print("[success]✓ Valid[/success]")
                else:
                    console.print(f"[error]❌ {len(result.issues)} issues[/error]")
                    
                    if show_suggestions:
                        for issue in result.issues:
                            format_validation_issue(issue, show_suggestions)


def format_validation_issue(issue, show_suggestions: bool = False) -> None:
    """Format a single validation issue."""
    # Icon and color based on issue type
    if issue.issue_type == IssueType.ERROR:
        icon = "❌"
        style = "error"
    elif issue.issue_type == IssueType.WARNING:
        icon = "⚠️"
        style = "warning"
    else:
        icon = "ℹ️"
        style = "info"
    
    # Format location
    location_str = ""
    if issue.location:
        location_str = f" at [secondary]{issue.location}[/secondary]"
    if issue.line_number:
        location_str += f" (line {issue.line_number})"
    
    console.print(f"  {icon} [{style}]{issue.message}[/{style}]{location_str}")
    
    # Show suggestion if available and requested
    if show_suggestions and issue.suggestion:
        console.print(f"    [secondary]💡 {issue.suggestion}[/secondary]")


def show_yaml_with_highlighting(file_path: Path, highlight_lines: Optional[List[int]] = None) -> None:
    """Display YAML file with syntax highlighting and optional line highlighting."""
    try:
        content = file_path.read_text(encoding='utf-8')
        syntax = Syntax(
            content, 
            "yaml", 
            line_numbers=True,
            highlight_lines=highlight_lines or [],
            theme="monokai"
        )
        console.print(syntax)
    except Exception as e:
        print_error(f"Could not read file: {e}")


def create_directory_tree(root_path: Path, title: Optional[str] = None) -> Tree:
    """Create a Rich tree for directory structure display."""
    tree_title = title or str(root_path)
    tree = Tree(f"[primary]{tree_title}[/primary]")
    
    def add_directory(current_path: Path, parent_node: Tree) -> None:
        try:
            for item in sorted(current_path.iterdir()):
                if item.is_dir():
                    dir_node = parent_node.add(f"📁 [primary]{item.name}[/primary]")
                    # Only go 2 levels deep to avoid clutter
                    if len(item.parts) - len(root_path.parts) < 2:
                        add_directory(item, dir_node)
                else:
                    parent_node.add(f"📄 [path]{item.name}[/path]")
        except PermissionError:
            parent_node.add("[error]Permission denied[/error]")
    
    if root_path.exists():
        add_directory(root_path, tree)
    else:
        tree.add("[error]Directory not found[/error]")
    
    return tree


def prompt_with_style(message: str, default: Optional[str] = None) -> str:
    """Prompt user with consistent WriteIt styling."""
    if default:
        prompt = f"[primary]{message}[/primary] [secondary]({default})[/secondary]: "
    else:
        prompt = f"[primary]{message}[/primary]: "
    
    return console.input(prompt) or default or ""


def confirm_with_style(message: str, default: bool = False) -> bool:
    """Confirm with user using consistent WriteIt styling."""
    default_text = "Y/n" if default else "y/N"
    prompt = f"[primary]{message}[/primary] [secondary]({default_text})[/secondary]: "
    
    response = console.input(prompt).lower().strip()
    
    if not response:
        return default
    
    return response in ['y', 'yes', 'true', '1']