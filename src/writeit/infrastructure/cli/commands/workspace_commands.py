"""Modern workspace commands using CQRS architecture.

Updated workspace commands that use the new BaseCommand infrastructure
and WorkspaceApplicationService for domain-driven design.
"""

import typer
from typing import Optional, Dict, Any
from rich.console import Console

from ..base_command import BaseCommand, CommandContext, ValidationCommandError
from ..error_handler import handle_cli_error
from ..output_formatter import OutputFormat
from ....application.services import (
    WorkspaceApplicationService,
    WorkspaceCreationRequest,
    WorkspaceListingOptions,
    WorkspaceInitializationMode,
)


# Create Typer app for workspace commands
app = typer.Typer(
    name="workspace", 
    help="Manage WriteIt workspaces with domain-driven architecture",
    rich_markup_mode="rich"
)


class CreateWorkspaceCommand(BaseCommand):
    """Command to create a new workspace."""
    
    def __init__(self, context: CommandContext, name: str, set_active: bool = False, 
                 description: Optional[str] = None, initialization_mode: str = "standard"):
        super().__init__(context)
        self.name = name
        self.set_active = set_active
        self.description = description
        self.initialization_mode = WorkspaceInitializationMode(initialization_mode)
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.name or not self.name.strip():
            raise ValidationCommandError("Workspace name cannot be empty")
        
        if len(self.name) > 50:
            raise ValidationCommandError("Workspace name must be 50 characters or less")
        
        # Basic name validation
        if not self.name.replace('-', '').replace('_', '').isalnum():
            raise ValidationCommandError(
                "Workspace name must contain only letters, numbers, hyphens, and underscores"
            )
    
    async def execute(self) -> Dict[str, Any]:
        """Execute workspace creation."""
        workspace_service = self.get_workspace_service()
        
        # Create workspace request
        request = WorkspaceCreationRequest(
            name=self.name,
            description=self.description,
            initialization_mode=self.initialization_mode
        )
        
        # Create workspace
        workspace = await workspace_service.create_workspace(request)
        
        result = {
            "workspace_name": workspace.name.value,
            "description": workspace.description or "",
            "created_at": workspace.created_at,
            "status": "created"
        }
        
        # Set as active if requested
        if self.set_active:
            await workspace_service.switch_workspace(self.name)
            result["status"] = "created_and_active"
        
        return result


class ListWorkspacesCommand(BaseCommand):
    """Command to list available workspaces."""
    
    def __init__(self, context: CommandContext, include_analytics: bool = False):
        super().__init__(context)
        self.include_analytics = include_analytics
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        # No validation needed for list command
        pass
    
    async def execute(self) -> Dict[str, Any]:
        """Execute workspace listing."""
        workspace_service = self.get_workspace_service()
        
        # Create listing options
        options = WorkspaceListingOptions(
            include_analytics=self.include_analytics,
            sort_by="name"
        )
        
        # Get workspaces
        workspaces = await workspace_service.list_workspaces(options)
        
        return {
            "workspaces": workspaces,
            "total_count": len(workspaces)
        }


class SwitchWorkspaceCommand(BaseCommand):
    """Command to switch to a different workspace."""
    
    def __init__(self, context: CommandContext, name: str):
        super().__init__(context)
        self.name = name
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.name or not self.name.strip():
            raise ValidationCommandError("Workspace name cannot be empty")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute workspace switch."""
        workspace_service = self.get_workspace_service()
        
        # Switch workspace
        workspace = await workspace_service.switch_workspace(self.name)
        
        return {
            "workspace_name": workspace.name.value,
            "description": workspace.description or "",
            "status": "active"
        }


class WorkspaceInfoCommand(BaseCommand):
    """Command to show workspace information."""
    
    def __init__(self, context: CommandContext, workspace_name: Optional[str] = None):
        super().__init__(context)
        self.workspace_name = workspace_name
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        # No validation needed - uses active workspace if none specified
        pass
    
    async def execute(self) -> Dict[str, Any]:
        """Execute workspace info retrieval."""
        workspace_service = self.get_workspace_service()
        
        # Get workspace information
        info = await workspace_service.get_workspace_info(self.workspace_name)
        
        return info


class DeleteWorkspaceCommand(BaseCommand):
    """Command to delete a workspace."""
    
    def __init__(self, context: CommandContext, name: str, backup: bool = True):
        super().__init__(context)
        self.name = name
        self.backup = backup
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        if not self.name or not self.name.strip():
            raise ValidationCommandError("Workspace name cannot be empty")
    
    async def execute(self) -> Dict[str, Any]:
        """Execute workspace deletion."""
        workspace_service = self.get_workspace_service()
        
        # Confirm deletion if not forced
        if not self.context.force:
            confirmed = self.confirm_action(
                f"Are you sure you want to delete workspace '{self.name}'? This action cannot be undone."
            )
            if not confirmed:
                return {"status": "cancelled", "workspace_name": self.name}
        
        # Delete workspace
        success = await workspace_service.delete_workspace(
            self.name, 
            force=self.context.force,
            backup_before_delete=self.backup
        )
        
        return {
            "workspace_name": self.name,
            "status": "deleted" if success else "failed",
            "backup_created": self.backup
        }


# Typer command functions that use the new command classes

@app.command()
def create(
    name: str = typer.Argument(..., help="Name of the workspace to create"),
    set_active: bool = typer.Option(
        False, "--set-active", "-s", help="Set as active workspace after creation"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Description for the workspace"
    ),
    initialization_mode: str = typer.Option(
        "standard", "--mode", "-m", 
        help="Initialization mode: minimal, standard, full"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    force: bool = typer.Option(False, "--force", "-f", help="Force creation without prompts"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    Create a new workspace.

    [bold cyan]Examples:[/bold cyan]

    Create a workspace:
      [dim]$ writeit workspace create myproject[/dim]

    Create with description and set as active:
      [dim]$ writeit workspace create myproject --description "My project workspace" --set-active[/dim]

    Create with full initialization:
      [dim]$ writeit workspace create myproject --mode full[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        force=force,
        output_format=output_format,
        console=console
    )
    
    command = CreateWorkspaceCommand(context, name, set_active, description, initialization_mode)
    
    try:
        result = command.run()
        
        # Display success message
        if result["status"] == "created_and_active":
            command.print_success(f"Created workspace '{name}' and set as active")
        else:
            command.print_success(f"Created workspace '{name}'")
        
        # Display result based on format
        if output_format != "table":
            command.format_output(result)
    
    except Exception as e:
        exit_code = handle_cli_error(e, "workspace create", console, workspace_name=workspace)
        raise typer.Exit(exit_code)


@app.command(name="list")
def list_workspaces(
    include_analytics: bool = typer.Option(
        False, "--analytics", "-a", help="Include analytics information"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    List all available workspaces.

    Shows all workspaces with status and analytics information.

    [bold cyan]Examples:[/bold cyan]

    List workspaces:
      [dim]$ writeit workspace list[/dim]

    List with analytics:
      [dim]$ writeit workspace list --analytics[/dim]

    List as JSON:
      [dim]$ writeit workspace list --format json[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = ListWorkspacesCommand(context, include_analytics)
    
    try:
        result = command.run()
        
        if not result["workspaces"]:
            command.print_info("No workspaces found. Create one with: writeit workspace create <name>")
            return
        
        # Display results
        if output_format == "table":
            command.format_output(result["workspaces"], "Available Workspaces")
            console.print(f"\nTotal workspaces: {result['total_count']}")
        else:
            command.format_output(result)
    
    except Exception as e:
        exit_code = handle_cli_error(e, "workspace list", console, workspace_name=workspace)
        raise typer.Exit(exit_code)


@app.command()
def use(
    name: str = typer.Argument(..., help="Name of the workspace to use"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    Switch to a different workspace.

    [bold cyan]Examples:[/bold cyan]

    Switch workspace:
      [dim]$ writeit workspace use myproject[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    command = SwitchWorkspaceCommand(context, name)
    
    try:
        result = command.run()
        command.print_success(f"Switched to workspace '{name}'")
        
        if output_format != "table":
            command.format_output(result)
    
    except Exception as e:
        exit_code = handle_cli_error(e, "workspace use", console, workspace_name=workspace)
        raise typer.Exit(exit_code)


@app.command()
def info(
    workspace_name: Optional[str] = typer.Argument(None, help="Workspace name (uses active if not specified)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    Show detailed workspace information.

    [bold cyan]Examples:[/bold cyan]

    Show active workspace info:
      [dim]$ writeit workspace info[/dim]

    Show specific workspace info:
      [dim]$ writeit workspace info myproject[/dim]

    Show as JSON:
      [dim]$ writeit workspace info --format json[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        output_format=output_format,
        console=console
    )
    
    # Use the provided workspace_name or fall back to context workspace
    target_workspace = workspace_name or workspace
    command = WorkspaceInfoCommand(context, target_workspace)
    
    try:
        result = command.run()
        
        # Use specialized formatter for workspace info
        from ..output_formatter import CLIOutputFormatter
        formatter = CLIOutputFormatter(console, OutputFormat(output_format))
        
        if output_format == "table":
            formatter.print_workspace_info(result)
        else:
            formatter.format_and_print(result, "Workspace Information")
    
    except Exception as e:
        exit_code = handle_cli_error(e, "workspace info", console, workspace_name=workspace)
        raise typer.Exit(exit_code)


@app.command()
def remove(
    name: str = typer.Argument(..., help="Name of the workspace to remove"),
    no_backup: bool = typer.Option(
        False, "--no-backup", help="Skip creating backup before deletion"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Force deletion without confirmation"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format: table, json, yaml"),
    workspace: Optional[str] = typer.Option(None, "--workspace", "-w", help="Workspace context"),
):
    """
    Remove a workspace.

    [bold cyan]Examples:[/bold cyan]

    Remove workspace with confirmation:
      [dim]$ writeit workspace remove myproject[/dim]

    Force remove without backup:
      [dim]$ writeit workspace remove myproject --force --no-backup[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace,
        verbose=verbose,
        force=force,
        output_format=output_format,
        console=console
    )
    
    command = DeleteWorkspaceCommand(context, name, backup=not no_backup)
    
    try:
        result = command.run()
        
        if result["status"] == "cancelled":
            command.print_info("Workspace deletion cancelled")
        elif result["status"] == "deleted":
            command.print_success(f"Workspace '{name}' deleted successfully")
            if result["backup_created"]:
                command.print_info("Backup created before deletion")
        else:
            command.print_warning(f"Failed to delete workspace '{name}'")
        
        if output_format != "table":
            command.format_output(result)
    
    except Exception as e:
        exit_code = handle_cli_error(e, "workspace remove", console, workspace_name=workspace)
        raise typer.Exit(exit_code)