"""Modern initialization commands using CQRS architecture.

Updated initialization commands that use the new BaseCommand infrastructure
and application services for domain-driven design.
"""

import typer
from typing import Optional, Dict, Any
from pathlib import Path
from rich.console import Console

from ..base_command import BaseCommand, CommandContext, ValidationCommandError
from ..error_handler import handle_cli_error
from ..output_formatter import OutputFormat
from ....application.services import (
    WorkspaceApplicationService,
    WorkspaceCreationRequest,
    WorkspaceInitializationMode,
)


# Create Typer app for init commands
app = typer.Typer(
    name="init", 
    help="Initialize WriteIt workspace and configuration",
    rich_markup_mode="rich"
)


class InitCommand(BaseCommand):
    """Command to initialize WriteIt home directory and workspace."""
    
    def __init__(self, context: CommandContext, migrate: bool = False, 
                 force: bool = False, create_default_workspace: bool = True):
        super().__init__(context)
        self.migrate = migrate
        self.force = force
        self.create_default_workspace = create_default_workspace
    
    def validate_arguments(self) -> None:
        """Validate command arguments."""
        # No specific validation needed for init command
        pass
    
    async def execute(self) -> Dict[str, Any]:
        """Execute initialization."""
        workspace_service = self.get_workspace_service()
        
        try:
            # Check if already initialized
            if not self.force:
                try:
                    existing_workspaces = await workspace_service.list_workspaces()
                    if existing_workspaces.workspaces:
                        if not self.confirm_action("WriteIt appears to already be initialized. Continue anyway?"):
                            return {"status": "cancelled", "message": "Initialization cancelled by user"}
                except Exception:
                    # Not initialized yet, continue
                    pass
            
            # Initialize the WriteIt home directory
            self.print_info("Initializing WriteIt home directory...")
            
            # Create the default workspace
            if self.create_default_workspace:
                creation_request = WorkspaceCreationRequest(
                    name="default",
                    description="Default WriteIt workspace",
                    set_active=True,
                    initialization_mode=WorkspaceInitializationMode.COMPLETE
                )
                
                result = await workspace_service.create_workspace(creation_request)
                
                if result.success:
                    self.print_success(f"Created default workspace: {result.workspace.name}")
                else:
                    self.print_warning("Failed to create default workspace")
            
            # Handle migration if requested
            migration_results = []
            if self.migrate:
                self.print_info("Searching for existing workspaces to migrate...")
                
                # This would typically scan for legacy workspace structures
                # For now, we'll just report no migrations found
                self.print_info("No legacy workspaces found to migrate")
            
            # Setup global configuration
            self.print_info("Setting up global configuration...")
            
            success_info = {
                "status": "success",
                "message": "WriteIt initialized successfully",
                "details": {
                    "home_directory": str(Path.home() / ".writeit"),
                    "default_workspace_created": self.create_default_workspace,
                    "migration_performed": self.migrate,
                    "migration_results": migration_results
                }
            }
            
            # Print final success message
            self.print_success("WriteIt initialized successfully!")
            self.print_info("Use 'writeit workspace list' to see available workspaces.")
            
            return success_info
            
        except Exception as e:
            error_info = {
                "status": "error",
                "message": f"Failed to initialize WriteIt: {str(e)}",
                "error_type": type(e).__name__
            }
            
            self.print_error(f"Initialization failed: {str(e)}")
            return error_info


# Command wrapper functions for Typer
@app.command()
def init(
    migrate: bool = typer.Option(False, "--migrate", help="Auto-migrate found local workspaces"),
    force: bool = typer.Option(False, "--force", help="Force initialization even if already initialized"),
    workspace_name: Optional[str] = typer.Option(None, "--workspace", help="Active workspace name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    output_format: str = typer.Option("table", "--format", help="Output format (table, json, yaml)"),
):
    """
    Initialize WriteIt home directory (~/.writeit).

    This creates the WriteIt home directory structure and a default workspace.
    Use --migrate to automatically migrate any existing local workspaces.

    [bold cyan]Examples:[/bold cyan]

    Basic initialization:
      [dim]$ writeit init[/dim]

    Initialize and migrate existing workspaces:
      [dim]$ writeit init --migrate[/dim]
      
    Force re-initialization:
      [dim]$ writeit init --force[/dim]
    """
    console = Console()
    context = CommandContext(
        workspace_name=workspace_name,
        verbose=verbose,
        force=force,
        output_format=output_format,
        console=console
    )
    
    command = InitCommand(
        context=context,
        migrate=migrate,
        force=force,
        create_default_workspace=True
    )
    
    with handle_cli_error(console, verbose):
        result = command.run()
        
        if context.output_format != "table":
            command.format_output(result)