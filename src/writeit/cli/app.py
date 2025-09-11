# ABOUTME: Typer app instance and configuration for WriteIt CLI
# ABOUTME: Central app definition with Rich integration and global settings

import typer
from typing import Optional

from writeit import __version__
from writeit.cli.output import console, print_info


# Main Typer app with Rich integration
app = typer.Typer(
    name="writeit",
    help="[bold blue]WriteIt[/bold blue] - LLM-powered writing pipeline tool with terminal UI",
    rich_markup_mode="rich",  # Enable Rich formatting in help
    pretty_exceptions_enable=True,  # Rich exception formatting
    no_args_is_help=True,  # Show help when no args provided
    add_completion=False,  # We'll handle completion manually for better control
)

# Global state for workspace override
workspace_override: Optional[str] = None
verbose_mode: bool = False


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    ),
    workspace: Optional[str] = typer.Option(
        None,
        "--workspace",
        "-w",
        help="Use specific workspace (overrides active workspace)",
    ),
    verbose: bool = typer.Option(False, "--verbose", help="Enable verbose output"),
):
    """
    [bold blue]WriteIt[/bold blue] - LLM-powered writing pipeline tool with terminal UI.

    [bold cyan]Examples:[/bold cyan]

    Initialize WriteIt:
      [dim]$ writeit init[/dim]

    Create and use a workspace:
      [dim]$ writeit workspace create myproject[/dim]
      [dim]$ writeit workspace use myproject[/dim]

    List available pipelines:
      [dim]$ writeit list-pipelines[/dim]

    Run a pipeline:
      [dim]$ writeit run article-template[/dim]

    Validate templates:
      [dim]$ writeit validate tech-article --detailed[/dim]

    [bold cyan]Shell Completion:[/bold cyan]

    Install completion for your shell:
      [dim]$ writeit --install-completion[/dim]

    Or generate completion script:
      [dim]$ writeit --show-completion[/dim]
    """
    global workspace_override, verbose_mode

    if version:
        console.print(
            f"[bold blue]WriteIt[/bold blue] version [primary]{__version__}[/primary]"
        )
        raise typer.Exit()

    # Store global options for use in commands
    workspace_override = workspace
    verbose_mode = verbose

    if verbose:
        print_info("Verbose mode enabled")


def get_workspace_override() -> Optional[str]:
    """Get the workspace override from global state."""
    return workspace_override


def is_verbose() -> bool:
    """Check if verbose mode is enabled."""
    return verbose_mode


# Add completion commands to the main app
@app.command(name="completion")
def completion_command(
    install: bool = typer.Option(
        False, "--install", help="Install shell completion for the current shell"
    ),
    show: bool = typer.Option(
        False, "--show", help="Show completion script for manual installation"
    ),
    shell: Optional[str] = typer.Option(
        None,
        "--shell",
        help="Specify shell (bash, zsh, fish, powershell). Auto-detects if not specified.",
    ),
):
    """
    Manage shell completion for WriteIt CLI.

    [bold cyan]Examples:[/bold cyan]

    Install completion for current shell:
      [dim]$ writeit completion --install[/dim]

    Show completion script:
      [dim]$ writeit completion --show[/dim]

    Install for specific shell:
      [dim]$ writeit completion --install --shell zsh[/dim]
    """
    if install and show:
        console.print(
            "[error]Cannot use both --install and --show options together[/error]"
        )
        raise typer.Exit(1)

    if not install and not show:
        console.print("[error]Must specify either --install or --show[/error]")
        console.print(
            "Use [primary]'writeit completion --help'[/primary] for usage examples"
        )
        raise typer.Exit(1)

    from writeit.cli.completion import install_completion, show_completion

    if install:
        install_completion(shell)
    else:
        show_completion(shell)
