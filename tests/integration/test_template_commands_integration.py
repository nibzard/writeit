# ABOUTME: Integration tests for template and style CLI commands
# ABOUTME: Tests the complete workflow of template/style management through CLI

import pytest
import tempfile
import shutil
from pathlib import Path
from typer.testing import CliRunner
from typing import Generator

from writeit.cli.main import app
from writeit.workspace.workspace import Workspace


@pytest.fixture
def temp_home() -> Generator[Path, None, None]:
    """Create temporary home directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def cli_runner(temp_home: Path, monkeypatch) -> CliRunner:
    """Create CLI runner with temporary home directory."""
    # Set up environment to use temp directory
    monkeypatch.setenv("HOME", str(temp_home))

    # Initialize WriteIt in temp directory
    workspace = Workspace(temp_home / ".writeit")
    workspace.initialize()

    return CliRunner()


class TestTemplateCommands:
    """Integration tests for template commands."""

    def test_template_create_workspace_interactive_no(self, cli_runner: CliRunner):
        """Test creating workspace template non-interactively."""
        result = cli_runner.invoke(
            app, ["template", "create", "test-template", "--non-interactive"]
        )

        assert result.exit_code == 0
        assert "Template 'test-template' created successfully!" in result.stdout
        assert "Scope: workspace" in result.stdout

    def test_template_create_global_interactive_no(self, cli_runner: CliRunner):
        """Test creating global template non-interactively."""
        result = cli_runner.invoke(
            app,
            ["template", "create", "global-template", "--global", "--non-interactive"],
        )

        assert result.exit_code == 0
        assert "Template 'global-template' created successfully!" in result.stdout
        assert "Scope: global" in result.stdout

    def test_template_create_interactive_with_input(self, cli_runner: CliRunner):
        """Test creating template interactively with user input."""
        # Simulate user input
        user_input = "Test article template\nTest Author\narticle,test\n"

        result = cli_runner.invoke(
            app, ["template", "create", "interactive-template"], input=user_input
        )

        assert result.exit_code == 0
        assert "Template 'interactive-template' created successfully!" in result.stdout

    def test_template_create_from_existing(self, cli_runner: CliRunner):
        """Test creating template from existing template."""
        # First create a source template
        cli_runner.invoke(
            app, ["template", "create", "source-template", "--non-interactive"]
        )

        # Then create from existing
        result = cli_runner.invoke(
            app, ["template", "create", "copied-template", "--from", "source-template"]
        )

        assert result.exit_code == 0
        assert "Template 'copied-template' created successfully!" in result.stdout

    def test_template_create_duplicate_fails(self, cli_runner: CliRunner):
        """Test that creating duplicate template fails."""
        # Create first template
        cli_runner.invoke(app, ["template", "create", "duplicate", "--non-interactive"])

        # Attempt to create duplicate
        result = cli_runner.invoke(
            app, ["template", "create", "duplicate", "--non-interactive"]
        )

        assert result.exit_code == 1
        assert "already exists" in result.stdout

    def test_template_list_empty(self, cli_runner: CliRunner):
        """Test listing templates when none exist."""
        result = cli_runner.invoke(app, ["template", "list"])

        assert result.exit_code == 0
        assert "No pipeline templates found" in result.stdout

    def test_template_list_with_templates(self, cli_runner: CliRunner):
        """Test listing templates when some exist."""
        # Create templates
        cli_runner.invoke(
            app, ["template", "create", "workspace-template", "--non-interactive"]
        )
        cli_runner.invoke(
            app,
            ["template", "create", "global-template", "--global", "--non-interactive"],
        )

        result = cli_runner.invoke(app, ["template", "list"])

        assert result.exit_code == 0
        assert "workspace-template" in result.stdout
        assert "global-template" in result.stdout
        assert "Workspace (default)" in result.stdout
        assert "Global" in result.stdout

    def test_template_list_scope_filtering(self, cli_runner: CliRunner):
        """Test listing templates with scope filtering."""
        # Create templates
        cli_runner.invoke(
            app, ["template", "create", "workspace-template", "--non-interactive"]
        )
        cli_runner.invoke(
            app,
            ["template", "create", "global-template", "--global", "--non-interactive"],
        )

        # List global only
        result = cli_runner.invoke(app, ["template", "list", "--scope", "global"])
        assert result.exit_code == 0
        assert "global-template" in result.stdout
        assert "workspace-template" not in result.stdout

        # List workspace only
        result = cli_runner.invoke(app, ["template", "list", "--scope", "workspace"])
        assert result.exit_code == 0
        assert "workspace-template" in result.stdout
        assert "global-template" not in result.stdout

    def test_template_copy_global_to_workspace(self, cli_runner: CliRunner):
        """Test copying template from global to workspace."""
        # Create global template
        cli_runner.invoke(
            app, ["template", "create", "source", "--global", "--non-interactive"]
        )

        # Copy to workspace
        result = cli_runner.invoke(app, ["template", "copy", "source", "destination"])

        assert result.exit_code == 0
        assert "Template copied successfully!" in result.stdout
        assert "Source: source" in result.stdout
        assert "Destination: destination" in result.stdout

    def test_template_copy_workspace_to_global(self, cli_runner: CliRunner):
        """Test copying template from workspace to global."""
        # Create workspace template
        cli_runner.invoke(
            app, ["template", "create", "workspace-source", "--non-interactive"]
        )

        # Copy to global
        result = cli_runner.invoke(
            app, ["template", "copy", "workspace-source", "global-dest", "--to-global"]
        )

        assert result.exit_code == 0
        assert "Template copied successfully!" in result.stdout
        assert "Scope: global" in result.stdout

    def test_template_copy_nonexistent_fails(self, cli_runner: CliRunner):
        """Test that copying nonexistent template fails."""
        result = cli_runner.invoke(
            app, ["template", "copy", "nonexistent", "destination"]
        )

        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_template_with_workspace_option(self, cli_runner: CliRunner):
        """Test template commands with workspace option."""
        # Create workspace
        cli_runner.invoke(app, ["workspace", "create", "test-workspace"])

        # Create template in specific workspace
        result = cli_runner.invoke(
            app,
            [
                "template",
                "create",
                "workspace-specific",
                "--workspace-name",
                "test-workspace",
                "--non-interactive",
            ],
        )

        assert result.exit_code == 0
        assert "Workspace: test-workspace" in result.stdout


class TestStyleCommands:
    """Integration tests for style commands."""

    def test_style_create_workspace_interactive_no(self, cli_runner: CliRunner):
        """Test creating workspace style non-interactively."""
        result = cli_runner.invoke(
            app, ["style", "create", "test-style", "--non-interactive"]
        )

        assert result.exit_code == 0
        assert "Style primer 'test-style' created successfully!" in result.stdout
        assert "Scope: workspace" in result.stdout

    def test_style_create_global_interactive_no(self, cli_runner: CliRunner):
        """Test creating global style non-interactively."""
        result = cli_runner.invoke(
            app, ["style", "create", "global-style", "--global", "--non-interactive"]
        )

        assert result.exit_code == 0
        assert "Style primer 'global-style' created successfully!" in result.stdout
        assert "Scope: global" in result.stdout

    def test_style_create_interactive_with_input(self, cli_runner: CliRunner):
        """Test creating style interactively with user input."""
        # Simulate user input
        user_input = "Professional writing style\nprofessional\nClear, engaging\nProfessional and approachable\n"

        result = cli_runner.invoke(
            app, ["style", "create", "interactive-style"], input=user_input
        )

        assert result.exit_code == 0
        assert "Style primer 'interactive-style' created successfully!" in result.stdout

    def test_style_create_from_existing(self, cli_runner: CliRunner):
        """Test creating style from existing style."""
        # First create a source style
        cli_runner.invoke(app, ["style", "create", "source-style", "--non-interactive"])

        # Then create from existing
        result = cli_runner.invoke(
            app, ["style", "create", "copied-style", "--from", "source-style"]
        )

        assert result.exit_code == 0
        assert "Style primer 'copied-style' created successfully!" in result.stdout

    def test_style_list_empty(self, cli_runner: CliRunner):
        """Test listing styles when none exist."""
        result = cli_runner.invoke(app, ["style", "list"])

        assert result.exit_code == 0
        assert "No style primers found" in result.stdout

    def test_style_list_with_styles(self, cli_runner: CliRunner):
        """Test listing styles when some exist."""
        # Create styles
        cli_runner.invoke(
            app, ["style", "create", "workspace-style", "--non-interactive"]
        )
        cli_runner.invoke(
            app, ["style", "create", "global-style", "--global", "--non-interactive"]
        )

        result = cli_runner.invoke(app, ["style", "list"])

        assert result.exit_code == 0
        assert "workspace-style" in result.stdout
        assert "global-style" in result.stdout
        assert "Workspace (default)" in result.stdout
        assert "Global" in result.stdout

    def test_style_copy_global_to_workspace(self, cli_runner: CliRunner):
        """Test copying style from global to workspace."""
        # Create global style
        cli_runner.invoke(
            app, ["style", "create", "source-style", "--global", "--non-interactive"]
        )

        # Copy to workspace
        result = cli_runner.invoke(
            app, ["style", "copy", "source-style", "destination-style"]
        )

        assert result.exit_code == 0
        assert "Style primer copied successfully!" in result.stdout


class TestWorkspaceTemplateIntegration:
    """Integration tests for workspace-specific template functionality."""

    def test_workspace_specific_template_isolation(self, cli_runner: CliRunner):
        """Test that workspace templates are isolated between workspaces."""
        # Create two workspaces
        cli_runner.invoke(app, ["workspace", "create", "workspace-a"])
        cli_runner.invoke(app, ["workspace", "create", "workspace-b"])

        # Create template in workspace A
        cli_runner.invoke(app, ["workspace", "use", "workspace-a"])
        cli_runner.invoke(
            app, ["template", "create", "workspace-a-template", "--non-interactive"]
        )

        # Switch to workspace B and verify template is not visible
        cli_runner.invoke(app, ["workspace", "use", "workspace-b"])
        result = cli_runner.invoke(app, ["template", "list", "--scope", "workspace"])

        assert result.exit_code == 0
        assert "workspace-a-template" not in result.stdout

    def test_workspace_template_priority_over_global(self, cli_runner: CliRunner):
        """Test that workspace templates take priority over global ones."""
        # Create global template
        cli_runner.invoke(
            app,
            ["template", "create", "priority-test", "--global", "--non-interactive"],
        )

        # Create workspace template with same name
        cli_runner.invoke(
            app, ["template", "create", "priority-test", "--non-interactive"]
        )

        # List all templates - should show workspace version
        result = cli_runner.invoke(app, ["template", "list"])

        assert result.exit_code == 0
        # Should only show one priority-test template (the workspace one)
        priority_lines = [
            line for line in result.stdout.split("\n") if "priority-test" in line
        ]
        assert len(priority_lines) == 1
        assert "Workspace (default)" in priority_lines[0]

    def test_pipeline_run_uses_workspace_template(self, cli_runner: CliRunner):
        """Test that pipeline run uses workspace template when available."""
        # Create global template
        cli_runner.invoke(
            app, ["template", "create", "run-test", "--global", "--non-interactive"]
        )

        # Create workspace template with same name
        cli_runner.invoke(app, ["template", "create", "run-test", "--non-interactive"])

        # Use --cli flag to avoid launching TUI during test
        result = cli_runner.invoke(app, ["run", "run-test", "--cli"])

        # Should show workspace scope
        assert "Scope: Workspace (default)" in result.stdout

    def test_global_flag_bypasses_workspace_template(self, cli_runner: CliRunner):
        """Test that --global flag bypasses workspace template."""
        # Create global template
        cli_runner.invoke(
            app, ["template", "create", "global-test", "--global", "--non-interactive"]
        )

        # Create workspace template with same name
        cli_runner.invoke(
            app, ["template", "create", "global-test", "--non-interactive"]
        )

        # Run with --global flag and --cli to avoid TUI
        result = cli_runner.invoke(app, ["run", "global-test", "--global", "--cli"])

        # Should show global scope
        assert "Scope: Global" in result.stdout

    def test_validation_works_with_workspace_templates(self, cli_runner: CliRunner):
        """Test that validation works with workspace templates."""
        # Create workspace template
        cli_runner.invoke(
            app, ["template", "create", "validate-test", "--non-interactive"]
        )

        # Validate the template
        result = cli_runner.invoke(app, ["validate", "validate", "validate-test"])

        assert result.exit_code == 0
        assert "validated successfully" in result.stdout
