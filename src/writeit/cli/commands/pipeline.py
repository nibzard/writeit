# ABOUTME: Pipeline commands for WriteIt CLI
# ABOUTME: Handles pipeline listing and execution with Rich formatting

import typer
from typing import Optional

from writeit.workspace.workspace import Workspace
from writeit.workspace.config import get_active_workspace
from writeit.workspace.template_manager import TemplateManager, TemplateType, TemplateScope
from writeit.cli.output import (
    console, print_error, print_warning,
    create_pipeline_table
)
from writeit.cli.completion import complete_pipeline_name
from writeit.cli.app import get_workspace_override


app = typer.Typer(
    name="pipeline", 
    help="Pipeline operations",
    rich_markup_mode="rich"
)


def get_workspace_manager() -> Workspace:
    """Get workspace manager and ensure WriteIt is initialized."""
    workspace_manager = Workspace()
    
    if not workspace_manager.home_dir.exists():
        print_error(
            "WriteIt not initialized. Run 'writeit init' first.",
            "Initialization Required"
        )
        raise typer.Exit(1)
    
    return workspace_manager


@app.command(name="list")
def list_pipelines():
    """
    List available pipeline templates.
    
    Shows both global templates and workspace-specific pipelines.
    """
    workspace_manager = get_workspace_manager()
    template_manager = TemplateManager(workspace_manager)
    
    try:
        # Get workspace override or active workspace
        workspace_override = get_workspace_override()
        workspace_name = workspace_override or get_active_workspace()
        
        # Use template manager to get all pipeline templates
        templates = template_manager.list_templates(
            template_type=TemplateType.PIPELINE,
            workspace_name=workspace_name,
            scope=TemplateScope.AUTO
        )
        
        if not templates:
            print_warning("No pipeline templates found")
            console.print("Create pipeline templates with:")
            console.print("  • [primary]writeit template create <name>[/primary] (workspace scope)")
            console.print("  • [primary]writeit template create <name> --global[/primary] (global scope)")
            return
        
        # Create table data with scope labels
        table_data = []
        for template in templates:
            scope_label = "Global" if template.scope == TemplateScope.GLOBAL else f"Workspace ({template.workspace_name})"
            table_data.append((template.name, scope_label))
        
        # Create and display table
        table = create_pipeline_table(table_data, "Available Pipeline Templates")
        console.print(table)
        
        # Show usage hint
        console.print("\n[secondary]Use [primary]'writeit run <pipeline-name>'[/primary] to execute a pipeline.[/secondary]")
        
    except Exception as e:
        print_error(f"Error listing pipelines: {e}")
        raise typer.Exit(1)


@app.command()
def run(
    pipeline: str = typer.Argument(
        ...,
        autocompletion=complete_pipeline_name,
        help="Pipeline configuration file (with or without .yaml extension)"
    ),
    use_global: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Use global pipeline template only"
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w", 
        help="Use specific workspace (overrides active workspace and global option)"
    ),
    cli_mode: bool = typer.Option(
        False,
        "--cli",
        help="Run in CLI mode with simple prompts (no TUI)"
    )
):
    """
    Run pipeline execution (TUI or CLI mode).
    
    Searches for the pipeline in workspace-specific directories first, 
    then falls back to global templates.
    
    [bold cyan]Examples:[/bold cyan]
    
    Run a pipeline (TUI):
      [dim]$ writeit run article-template[/dim]
    
    Run in CLI mode:
      [dim]$ writeit run article-template --cli[/dim]
    
    Run global pipeline only:
      [dim]$ writeit run article-template --global[/dim]
      
    Run in specific workspace:
      [dim]$ writeit run article-template --workspace myproject[/dim]
    """
    workspace_manager = get_workspace_manager()
    template_manager = TemplateManager(workspace_manager)
    
    try:
        # Determine workspace to use
        workspace_override = get_workspace_override()
        workspace_name = workspace or workspace_override or get_active_workspace()
        
        # Determine scope
        scope = TemplateScope.GLOBAL if use_global else TemplateScope.AUTO
        
        # Resolve pipeline using template manager
        location = template_manager.resolve_template(
            name=pipeline,
            template_type=TemplateType.PIPELINE,
            workspace_name=workspace_name,
            scope=scope
        )
        
        if location is None or not location.exists:
            print_error(f"Pipeline not found: {pipeline}")
            
            console.print("\nUse [primary]'writeit list-pipelines'[/primary] to see available pipelines")
            raise typer.Exit(1)
        
        pipeline_path = location.path
        
        # Display what we're running
        console.print(f"[primary]Pipeline:[/primary] [pipeline.name]{pipeline}[/pipeline.name]")
        console.print(f"[primary]Path:[/primary] [path]{pipeline_path}[/path]")
        scope_label = "Global" if location.scope == TemplateScope.GLOBAL else f"Workspace ({location.workspace_name})"
        console.print(f"[primary]Scope:[/primary] {scope_label}")
        console.print(f"[primary]Workspace:[/primary] [workspace.active]{workspace_name}[/workspace.active]")
        console.print()
        
        # Choose execution mode
        if cli_mode:
            # CLI mode execution
            try:
                from writeit.cli.pipeline_runner import run_pipeline_cli
                import asyncio
                
                console.print("Starting CLI pipeline execution...")
                result = asyncio.run(run_pipeline_cli(pipeline_path, workspace_name))
                raise typer.Exit(result)
            except Exception as cli_error:
                print_error(f"CLI execution failed: {cli_error}")
                return 1
        else:
            # TUI mode execution
            try:
                from writeit.tui.pipeline_runner import run_pipeline_tui
                import asyncio
                
                console.print("Launching pipeline TUI...")
                asyncio.run(run_pipeline_tui(pipeline_path, workspace_name))
                return 0
            except ImportError:
                print_error("TUI dependencies not available. Install with: pip install textual")
                console.print("[info]Tip: Use --cli flag for non-interactive mode[/info]")
                return 1
            except Exception as tui_error:
                print_error(f"TUI execution failed: {tui_error}")
                return 1
        
    except Exception as e:
        print_error(f"Error running pipeline: {e}")
        raise typer.Exit(1)