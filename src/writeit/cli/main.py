# ABOUTME: WriteIt main CLI entry point using Typer
# ABOUTME: Coordinates all command modules and provides the main app entry point

import sys

from writeit.cli.app import app
from writeit.cli.commands.workspace import app as workspace_app
from writeit.cli.commands.pipeline import app as pipeline_app
from writeit.cli.commands.validate import app as validate_app
from writeit.cli.commands.template import app as template_app
from writeit.cli.commands.style import app as style_app


# Add all command modules to the main app
# Import init command directly since it's a single command
from writeit.cli.commands.init import init

app.command(name="init")(init)
app.add_typer(workspace_app, name="workspace")
app.add_typer(pipeline_app, name="pipeline")
app.add_typer(validate_app, name="validate")
app.add_typer(template_app, name="template")
app.add_typer(style_app, name="style")

# Add individual commands from pipeline module to maintain backwards compatibility
# Import specific commands for direct registration
from writeit.cli.commands.pipeline import list_pipelines, run

app.command(name="list-pipelines")(list_pipelines)
app.command(name="run")(run)


def main():
    """Main CLI entry point for WriteIt."""
    try:
        app()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        sys.exit(1)
    except Exception as e:
        # Handle unexpected errors
        from writeit.cli.output import print_error
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()