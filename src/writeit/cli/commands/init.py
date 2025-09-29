# ABOUTME: Init command for WriteIt CLI
# ABOUTME: Handles WriteIt initialization with Rich progress display

import typer

from writeit.workspace.workspace import Workspace
from writeit.cli.output import console, print_success, print_error, create_progress


app = typer.Typer(name="init", help="Initialize WriteIt home directory")


@app.command()
def init():
    """
    Initialize WriteIt home directory (~/.writeit).

    This creates the WriteIt home directory structure and a default workspace.

    [bold cyan]Examples:[/bold cyan]

    Basic initialization:
      [dim]$ writeit init[/dim]
    """
    workspace_manager = Workspace()

    console.print(
        f"[primary]Initializing WriteIt home directory:[/primary] [path]{workspace_manager.home_dir}[/path]"
    )

    try:
        with create_progress() as progress:
            # Initialize WriteIt
            init_task = progress.add_task("Initializing WriteIt...", total=3)

            workspace_manager.initialize()
            progress.update(
                init_task,
                advance=1,
                description="✓ Created ~/.writeit directory structure",
            )

            progress.update(
                init_task, advance=1, description="✓ Created default workspace"
            )

            progress.update(
                init_task, advance=1, description="✓ Created global configuration"
            )

            progress.update(
                init_task,
                description="[green]✓ WriteIt initialized successfully![/green]",
            )

        # Show completion messages
        print_success("Created ~/.writeit directory structure")
        print_success("Created default workspace")
        print_success("Created global configuration")


        # Final success message
        console.print("\n[success]WriteIt initialized successfully![/success]")
        console.print(
            "Use [primary]'writeit workspace list'[/primary] to see available workspaces."
        )

    except Exception as e:
        print_error(f"Error initializing WriteIt: {e}")
        raise typer.Exit(1)
