# ABOUTME: Workspace commands for WriteIt CLI
# ABOUTME: Handles workspace creation, listing, switching, and management with Rich tables

import typer
from typing import Optional

from writeit.workspace.workspace import Workspace
from writeit.storage.manager import StorageManager
from writeit.cli.output import (
    console,
    print_success,
    print_error,
    print_warning,
    create_workspace_table,
    create_workspace_info_table,
    confirm_with_style,
    create_directory_tree,
)
from writeit.cli.completion import complete_workspace_name


app = typer.Typer(
    name="workspace", help="Manage WriteIt workspaces", rich_markup_mode="rich"
)


def get_workspace_manager() -> Workspace:
    """Get workspace manager and ensure WriteIt is initialized."""
    workspace_manager = Workspace()

    if not workspace_manager.home_dir.exists():
        print_error(
            "WriteIt not initialized. Run 'writeit init' first.",
            "Initialization Required",
        )
        raise typer.Exit(1)

    return workspace_manager


@app.command()
def create(
    name: str = typer.Argument(..., help="Name of the workspace to create"),
    set_active: bool = typer.Option(
        False, "--set-active", "-s", help="Set as active workspace after creation"
    ),
):
    """
    Create a new workspace.

    [bold cyan]Examples:[/bold cyan]

    Create a workspace:
      [dim]$ writeit workspace create myproject[/dim]

    Create and set as active:
      [dim]$ writeit workspace create myproject --set-active[/dim]
    """
    workspace_manager = get_workspace_manager()

    try:
        workspace_manager.create_workspace(name)
        print_success(f"Created workspace '{name}'")

        if set_active:
            workspace_manager.set_active_workspace(name)
            print_success(f"Set '{name}' as active workspace")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise typer.Exit(1)


@app.command(name="list")
def list_workspaces():
    """
    List all available workspaces.

    Shows all workspaces with an indicator for the currently active one.
    """
    workspace_manager = get_workspace_manager()

    try:
        workspaces = workspace_manager.list_workspaces()
        active = workspace_manager.get_active_workspace()

        if not workspaces:
            print_warning("No workspaces found", "Empty")
            console.print(
                "Create a workspace with: [primary]writeit workspace create <name>[/primary]"
            )
            return

        # Create and display workspace table
        table = create_workspace_table(workspaces, active)
        console.print(table)

        # Show additional info
        console.print(
            f"\nActive workspace: [workspace.active]{active}[/workspace.active]"
        )
        console.print(f"Total workspaces: {len(workspaces)}")

    except Exception as e:
        print_error(f"Error listing workspaces: {e}")
        raise typer.Exit(1)


@app.command()
def use(
    name: str = typer.Argument(
        ..., autocompletion=complete_workspace_name, help="Name of the workspace to use"
    ),
):
    """
    Switch to a different workspace.

    [bold cyan]Examples:[/bold cyan]

    Switch workspace:
      [dim]$ writeit workspace use myproject[/dim]
    """
    workspace_manager = get_workspace_manager()

    try:
        workspace_manager.set_active_workspace(name)
        print_success(f"Switched to workspace '{name}'")

    except ValueError as e:
        print_error(str(e))

        # Show available workspaces
        workspaces = workspace_manager.list_workspaces()
        if workspaces:
            console.print("\n[secondary]Available workspaces:[/secondary]")
            for ws in workspaces:
                console.print(f"  • {ws}")

        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise typer.Exit(1)


@app.command()
def remove(
    name: str = typer.Argument(
        ...,
        autocompletion=complete_workspace_name,
        help="Name of the workspace to remove",
    ),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
):
    """
    Remove a workspace.

    [bold red]Warning:[/bold red] This permanently deletes all data in the workspace.

    [bold cyan]Examples:[/bold cyan]

    Remove workspace (with confirmation):
      [dim]$ writeit workspace remove oldproject[/dim]

    Remove without confirmation:
      [dim]$ writeit workspace remove oldproject --force[/dim]
    """
    workspace_manager = get_workspace_manager()

    try:
        # Check if workspace exists
        workspaces = workspace_manager.list_workspaces()
        if name not in workspaces:
            print_error(f"Workspace '{name}' not found")
            raise typer.Exit(1)

        # Prevent removing active workspace
        active = workspace_manager.get_active_workspace()
        if name == active:
            print_error(
                f"Cannot remove active workspace '{name}'. "
                f"Switch to another workspace first."
            )
            raise typer.Exit(1)

        # Confirmation prompt
        if not force:
            workspace_path = workspace_manager.get_workspace_path(name)

            console.print(
                f"[warning]You are about to remove workspace '[bold]{name}[/bold]'[/warning]"
            )
            console.print(f"[secondary]Path: {workspace_path}[/secondary]")
            console.print(
                "[error]This will permanently delete all data in this workspace.[/error]"
            )

            if not confirm_with_style(
                "Are you sure you want to continue?", default=False
            ):
                console.print("Cancelled.")
                return

        workspace_manager.remove_workspace(name)
        print_success(f"Removed workspace '{name}'")

    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise typer.Exit(1)


@app.command()
def info(
    name: Optional[str] = typer.Argument(
        None,
        autocompletion=complete_workspace_name,
        help="Workspace name (defaults to active workspace)",
    ),
    show_tree: bool = typer.Option(
        False, "--tree", "-t", help="Show directory tree structure"
    ),
):
    """
    Show detailed information about a workspace.

    [bold cyan]Examples:[/bold cyan]

    Show info for active workspace:
      [dim]$ writeit workspace info[/dim]

    Show info for specific workspace:
      [dim]$ writeit workspace info myproject[/dim]

    Show info with directory tree:
      [dim]$ writeit workspace info myproject --tree[/dim]
    """
    workspace_manager = get_workspace_manager()

    try:
        # Use provided name or active workspace
        workspace_name = name or workspace_manager.get_active_workspace()

        # Get workspace info
        workspace_path = workspace_manager.get_workspace_path(workspace_name)
        config = workspace_manager.load_workspace_config(workspace_name)

        # Get storage stats
        try:
            storage = StorageManager(workspace_manager, workspace_name)
            stats = storage.get_stats()
        except Exception:
            stats = None

        # Create and display info table
        table = create_workspace_info_table(workspace_name, config.__dict__, stats)
        console.print(table)

        # Show path
        console.print(f"\n[primary]Path:[/primary] [path]{workspace_path}[/path]")

        # Show directory tree if requested
        if show_tree:
            tree = create_directory_tree(workspace_path, f"Workspace: {workspace_name}")
            console.print(tree)

    except ValueError as e:
        print_error(str(e))

        # Show available workspaces
        workspaces = workspace_manager.list_workspaces()
        if workspaces:
            console.print("\n[secondary]Available workspaces:[/secondary]")
            for ws in workspaces:
                console.print(f"  • {ws}")

        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        raise typer.Exit(1)
