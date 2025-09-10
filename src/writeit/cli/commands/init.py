# ABOUTME: Init command for WriteIt CLI
# ABOUTME: Handles WriteIt initialization with Rich progress display

import typer

from writeit.workspace.workspace import Workspace
from writeit.workspace.migration import find_and_migrate_workspaces
from writeit.cli.output import console, print_success, print_error, create_progress


app = typer.Typer(name="init", help="Initialize WriteIt home directory")


@app.command()
def init(
    migrate: bool = typer.Option(
        False,
        "--migrate",
        help="Auto-migrate found local workspaces"
    )
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
    """
    workspace_manager = Workspace()
    
    console.print(f"[primary]Initializing WriteIt home directory:[/primary] [path]{workspace_manager.home_dir}[/path]")
    
    try:
        with create_progress() as progress:
            # Initialize WriteIt
            init_task = progress.add_task("Initializing WriteIt...", total=3)
            
            workspace_manager.initialize()
            progress.update(init_task, advance=1, description="✓ Created ~/.writeit directory structure")
            
            progress.update(init_task, advance=1, description="✓ Created default workspace")
            
            progress.update(init_task, advance=1, description="✓ Created global configuration")
            
            progress.update(init_task, description="[green]✓ WriteIt initialized successfully![/green]")
        
        # Show completion messages
        print_success("Created ~/.writeit directory structure")
        print_success("Created default workspace")
        print_success("Created global configuration")
        
        # Handle migration if requested
        if migrate:
            console.print("\n[primary]Searching for local workspaces to migrate...[/primary]")
            
            with create_progress() as progress:
                migrate_task = progress.add_task("Scanning for workspaces...", total=None)
                
                results = find_and_migrate_workspaces(workspace_manager, interactive=False)
                
                if results:
                    successful_migrations = [r for r in results if r[1]]
                    progress.update(migrate_task, 
                                  description=f"[green]✓ Migrated {len(successful_migrations)} workspaces[/green]")
                    
                    if successful_migrations:
                        print_success(f"Migrated {len(successful_migrations)} workspaces")
                        for workspace_path, success in results:
                            if success:
                                console.print(f"  ✓ [path]{workspace_path}[/path]")
                    
                    # Show any failures
                    failed_migrations = [r for r in results if not r[1]]
                    if failed_migrations:
                        console.print("\n[warning]Some workspaces could not be migrated:[/warning]")
                        for workspace_path, success in failed_migrations:
                            console.print(f"  ❌ [path]{workspace_path}[/path]")
                else:
                    progress.update(migrate_task, description="[secondary]No local workspaces found to migrate[/secondary]")
                    console.print("[secondary]No local workspaces found to migrate[/secondary]")
        
        # Final success message
        console.print("\n[success]WriteIt initialized successfully![/success]")
        console.print("Use [primary]'writeit workspace list'[/primary] to see available workspaces.")
        
    except Exception as e:
        print_error(f"Error initializing WriteIt: {e}")
        raise typer.Exit(1)