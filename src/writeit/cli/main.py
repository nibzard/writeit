# ABOUTME: WriteIt main CLI entry point using Typer
# ABOUTME: Coordinates all command modules and provides the main app entry point

import sys
import logging

from writeit.cli.app import app
from writeit.cli.commands.workspace import app as workspace_app
from writeit.cli.commands.pipeline import app as pipeline_app
from writeit.cli.commands.pipeline import (
    list_pipelines,
    run,
)  # Move here to fix import order
from writeit.cli.commands.validate import app as validate_app
from writeit.cli.commands.template import app as template_app
from writeit.cli.commands.style import app as style_app
from writeit.cli.commands.docs import app as docs_app
from writeit.cli.commands.config import app as config_app


# Add all command modules to the main app
# Import init command directly since it's a single command
from writeit.cli.commands.init import init

app.command(name="init")(init)
app.add_typer(workspace_app, name="workspace")
app.add_typer(pipeline_app, name="pipeline")
app.add_typer(validate_app, name="validate")
app.add_typer(template_app, name="template")
app.add_typer(style_app, name="style")
app.add_typer(docs_app, name="docs")
app.add_typer(config_app, name="config")

app.command(name="list-pipelines")(list_pipelines)
app.command(name="run")(run)


def main():
    """Main CLI entry point for WriteIt."""
    try:
        # Setup basic logging
        from writeit.infrastructure.logging import configure_default_logging

        logger = configure_default_logging()
        logger.debug("Starting WriteIt CLI application")

        app()

        logger.debug("WriteIt CLI application completed successfully")
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        logger = logging.getLogger("writeit")
        logger.info("Application interrupted by user")
        sys.exit(1)
    except Exception as e:
        # Handle unexpected errors
        logger = logging.getLogger("writeit")
        logger.error(f"Unexpected error: {e}", exc_info=True)

        from writeit.cli.output import print_error

        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
