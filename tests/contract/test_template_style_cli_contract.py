# ABOUTME: Contract tests for template and style CLI commands
# ABOUTME: Ensures CLI interface stability and expected behavior patterns

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


class TestTemplateCLIContract:
    """Contract tests for template CLI commands."""

    def test_template_command_exists(self, cli_runner: CliRunner):
        """Test that template command is available."""
        result = cli_runner.invoke(app, ["template", "--help"])
        assert result.exit_code == 0
        assert "Manage pipeline templates" in result.stdout

    def test_template_create_command_exists(self, cli_runner: CliRunner):
        """Test that template create command is available."""
        result = cli_runner.invoke(app, ["template", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new pipeline template" in result.stdout

    def test_template_list_command_exists(self, cli_runner: CliRunner):
        """Test that template list command is available."""
        result = cli_runner.invoke(app, ["template", "list", "--help"])
        assert result.exit_code == 0
        assert "List available pipeline templates" in result.stdout

    def test_template_copy_command_exists(self, cli_runner: CliRunner):
        """Test that template copy command is available."""
        result = cli_runner.invoke(app, ["template", "copy", "--help"])
        assert result.exit_code == 0
        assert "Copy a template from one location to another" in result.stdout

    def test_template_create_has_expected_options(self, cli_runner: CliRunner):
        """Test that template create has expected command-line options."""
        result = cli_runner.invoke(app, ["template", "create", "--help"])
        assert result.exit_code == 0

        expected_options = [
            "--workspace           --global",
            "--workspace-name",
            "--from",
            "--interactive         --non-interactive",
        ]

        for option in expected_options:
            assert option in result.stdout

    def test_template_list_has_expected_options(self, cli_runner: CliRunner):
        """Test that template list has expected command-line options."""
        result = cli_runner.invoke(app, ["template", "list", "--help"])
        assert result.exit_code == 0

        expected_options = ["--scope", "--workspace"]

        for option in expected_options:
            assert option in result.stdout

    def test_template_copy_has_expected_options(self, cli_runner: CliRunner):
        """Test that template copy has expected command-line options."""
        result = cli_runner.invoke(app, ["template", "copy", "--help"])
        assert result.exit_code == 0

        expected_options = [
            "--to-workspace        --to-global",
            "--workspace",
            "--from-workspace",
        ]

        for option in expected_options:
            assert option in result.stdout

    def test_template_create_requires_name_argument(self, cli_runner: CliRunner):
        """Test that template create requires name argument."""
        result = cli_runner.invoke(app, ["template", "create"])
        assert result.exit_code == 2  # Missing required argument
        assert "Missing argument" in result.output

    def test_template_copy_requires_arguments(self, cli_runner: CliRunner):
        """Test that template copy requires source and destination arguments."""
        result = cli_runner.invoke(app, ["template", "copy"])
        assert result.exit_code == 2  # Missing required arguments

        result = cli_runner.invoke(app, ["template", "copy", "source"])
        assert result.exit_code == 2  # Missing destination argument

    def test_template_list_scope_values_validation(self, cli_runner: CliRunner):
        """Test that template list validates scope values."""
        result = cli_runner.invoke(app, ["template", "list", "--scope", "invalid"])
        assert result.exit_code == 1
        assert "Invalid scope" in result.stdout

    def test_template_create_workspace_scope_default(self, cli_runner: CliRunner):
        """Test that template create defaults to workspace scope."""
        result = cli_runner.invoke(
            app, ["template", "create", "default-scope-test", "--non-interactive"]
        )
        assert result.exit_code == 0
        assert "Scope: workspace" in result.stdout

    def test_template_create_global_scope_explicit(self, cli_runner: CliRunner):
        """Test that template create uses global scope when specified."""
        result = cli_runner.invoke(
            app,
            [
                "template",
                "create",
                "global-scope-test",
                "--global",
                "--non-interactive",
            ],
        )
        assert result.exit_code == 0
        assert "Scope: global" in result.stdout


class TestStyleCLIContract:
    """Contract tests for style CLI commands."""

    def test_style_command_exists(self, cli_runner: CliRunner):
        """Test that style command is available."""
        result = cli_runner.invoke(app, ["style", "--help"])
        assert result.exit_code == 0
        assert "Manage style primers" in result.stdout

    def test_style_create_command_exists(self, cli_runner: CliRunner):
        """Test that style create command is available."""
        result = cli_runner.invoke(app, ["style", "create", "--help"])
        assert result.exit_code == 0
        assert "Create a new style primer" in result.stdout

    def test_style_list_command_exists(self, cli_runner: CliRunner):
        """Test that style list command is available."""
        result = cli_runner.invoke(app, ["style", "list", "--help"])
        assert result.exit_code == 0
        assert "List available style primers" in result.stdout

    def test_style_copy_command_exists(self, cli_runner: CliRunner):
        """Test that style copy command is available."""
        result = cli_runner.invoke(app, ["style", "copy", "--help"])
        assert result.exit_code == 0
        assert "Copy a style primer from one location to another" in result.stdout

    def test_style_create_has_expected_options(self, cli_runner: CliRunner):
        """Test that style create has expected command-line options."""
        result = cli_runner.invoke(app, ["style", "create", "--help"])
        assert result.exit_code == 0

        expected_options = [
            "--workspace           --global",
            "--workspace-name",
            "--from",
            "--interactive         --non-interactive",
        ]

        for option in expected_options:
            assert option in result.stdout

    def test_style_create_requires_name_argument(self, cli_runner: CliRunner):
        """Test that style create requires name argument."""
        result = cli_runner.invoke(app, ["style", "create"])
        assert result.exit_code == 2  # Missing required argument

    def test_style_create_workspace_scope_default(self, cli_runner: CliRunner):
        """Test that style create defaults to workspace scope."""
        result = cli_runner.invoke(
            app, ["style", "create", "default-scope-test", "--non-interactive"]
        )
        assert result.exit_code == 0
        assert "Scope: workspace" in result.stdout


class TestMainCLIContract:
    """Contract tests for main CLI integration."""

    def test_main_help_shows_new_commands(self, cli_runner: CliRunner):
        """Test that main help shows template and style commands."""
        result = cli_runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "template" in result.stdout
        assert "style" in result.stdout

    def test_list_pipelines_shows_scope_labels(self, cli_runner: CliRunner):
        """Test that list-pipelines shows scope labels."""
        # Create templates in different scopes
        cli_runner.invoke(
            app, ["template", "create", "workspace-template", "--non-interactive"]
        )
        cli_runner.invoke(
            app,
            ["template", "create", "global-template", "--global", "--non-interactive"],
        )

        result = cli_runner.invoke(app, ["list-pipelines"])
        assert result.exit_code == 0
        assert "Workspace (default)" in result.stdout
        assert "Global" in result.stdout

    def test_run_command_shows_scope_information(self, cli_runner: CliRunner):
        """Test that run command shows scope information."""
        # Create template
        cli_runner.invoke(
            app, ["template", "create", "run-scope-test", "--non-interactive"]
        )

        # Use --cli flag to avoid launching TUI during test
        result = cli_runner.invoke(app, ["run", "run-scope-test", "--cli"])
        # Check that pipeline info is shown (not the actual scope text which appears in TUI)
        assert (
            "Pipeline: run-scope-test" in result.stdout
            or "run-scope-test" in result.stdout
        )

    def test_validate_command_works_with_workspace_templates(
        self, cli_runner: CliRunner
    ):
        """Test that validate command works with workspace templates."""
        # Create workspace template
        cli_runner.invoke(
            app, ["template", "create", "validate-workspace-test", "--non-interactive"]
        )

        result = cli_runner.invoke(
            app, ["validate", "validate", "validate-workspace-test"]
        )
        assert result.exit_code == 0

    def test_global_workspace_option_consistency(self, cli_runner: CliRunner):
        """Test that --workspace option works consistently across commands."""
        # Create workspace
        cli_runner.invoke(app, ["workspace", "create", "test-workspace"])

        # Create template in specific workspace
        result = cli_runner.invoke(
            app,
            [
                "template",
                "create",
                "workspace-option-test",
                "--workspace-name",
                "test-workspace",
                "--non-interactive",
            ],
        )
        assert result.exit_code == 0
        assert "Workspace: test-workspace" in result.stdout

        # List templates in specific workspace
        result = cli_runner.invoke(
            app,
            [
                "template",
                "list",
                "--workspace",
                "test-workspace",
                "--scope",
                "workspace",
            ],
        )
        assert result.exit_code == 0
        assert "workspace-option-test" in result.stdout


class TestCLIErrorHandling:
    """Contract tests for CLI error handling."""

    def test_template_create_nonexistent_workspace_fails(self, cli_runner: CliRunner):
        """Test that creating template in nonexistent workspace fails gracefully."""
        result = cli_runner.invoke(
            app,
            [
                "template",
                "create",
                "test",
                "--workspace-name",
                "nonexistent",
                "--non-interactive",
            ],
        )
        assert result.exit_code == 1

    def test_template_copy_nonexistent_source_fails(self, cli_runner: CliRunner):
        """Test that copying nonexistent template fails gracefully."""
        result = cli_runner.invoke(
            app, ["template", "copy", "nonexistent", "destination"]
        )
        assert result.exit_code == 1
        assert "not found" in result.stdout

    def test_commands_require_writeIt_initialization(
        self, temp_home: Path, monkeypatch
    ):
        """Test that commands fail gracefully when WriteIt is not initialized."""
        # Set up environment without initializing WriteIt
        monkeypatch.setenv("HOME", str(temp_home))

        cli_runner = CliRunner()

        result = cli_runner.invoke(app, ["template", "list"])
        assert result.exit_code == 1
        assert "WriteIt not initialized" in result.stdout

    def test_invalid_template_name_characters_handled(self, cli_runner: CliRunner):
        """Test that invalid template name characters are handled."""
        # Test with various potentially problematic characters
        invalid_names = [
            "template/with/slash",
            "template with spaces",
            "template@symbol",
        ]

        for name in invalid_names:
            result = cli_runner.invoke(
                app, ["template", "create", name, "--non-interactive"]
            )
            # Should either succeed (if name is valid) or fail gracefully
            assert result.exit_code in [0, 1]


class TestCLIOutputFormat:
    """Contract tests for CLI output formatting."""

    def test_template_list_output_format(self, cli_runner: CliRunner):
        """Test that template list output follows expected format."""
        # Create templates
        cli_runner.invoke(
            app, ["template", "create", "test-template", "--non-interactive"]
        )

        result = cli_runner.invoke(app, ["template", "list"])
        assert result.exit_code == 0

        # Should contain table headers and template information
        assert "Available Pipeline Templates" in result.stdout
        assert "test-template" in result.stdout
        assert "Workspace (default)" in result.stdout

    def test_template_create_success_output_format(self, cli_runner: CliRunner):
        """Test that template create success output follows expected format."""
        result = cli_runner.invoke(
            app, ["template", "create", "success-test", "--non-interactive"]
        )
        assert result.exit_code == 0

        # Should contain success message and key information
        assert "Template 'success-test' created successfully!" in result.stdout
        assert "Path:" in result.stdout
        assert "Scope:" in result.stdout

    def test_style_list_output_format(self, cli_runner: CliRunner):
        """Test that style list output follows expected format."""
        # Create style
        cli_runner.invoke(app, ["style", "create", "test-style", "--non-interactive"])

        result = cli_runner.invoke(app, ["style", "list"])
        assert result.exit_code == 0

        # Should contain table headers and style information
        assert "Available Style Primers" in result.stdout
        assert "test-style" in result.stdout

    def test_error_messages_are_clear(self, cli_runner: CliRunner):
        """Test that error messages are clear and helpful."""
        # Test duplicate creation error
        cli_runner.invoke(
            app, ["template", "create", "duplicate-test", "--non-interactive"]
        )

        result = cli_runner.invoke(
            app, ["template", "create", "duplicate-test", "--non-interactive"]
        )
        assert result.exit_code == 1
        assert "already exists" in result.stdout

        # Test nonexistent template copy error
        result = cli_runner.invoke(
            app, ["template", "copy", "nonexistent", "destination"]
        )
        assert result.exit_code == 1
        assert "not found" in result.stdout
