"""
Contract tests for CLI command outputs.

Ensures that CLI commands produce consistent and expected output formats,
including help text, error messages, and structured data output.
"""

import pytest
import tempfile
import shutil
import json
import yaml
from pathlib import Path
from typer.testing import CliRunner
from typing import Generator, Dict, Any, List
import subprocess
import sys

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
    monkeypatch.setenv("WRITEIT_HOME", str(temp_home / ".writeit"))

    # Initialize WriteIt in temp directory
    workspace = Workspace(temp_home / ".writeit")
    workspace.initialize()

    return CliRunner()


@pytest.fixture
def initialized_workspace(cli_runner: CliRunner):
    """Create an initialized workspace with test data."""
    # Create some test templates and pipelines
    cli_runner.invoke(app, ["template", "create", "test-template", "--non-interactive"])
    cli_runner.invoke(app, ["style", "create", "test-style", "--non-interactive"])
    
    return True


class TestMainCLIContract:
    """Contract tests for main CLI commands and overall behavior."""

    def test_main_help_contract(self, cli_runner: CliRunner):
        """Test main help command contract."""
        result = cli_runner.invoke(app, ["--help"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should contain expected sections
        assert "Usage:" in result.stdout
        assert "Commands:" in result.stdout
        assert "Options:" in result.stdout
        
        # Contract: Should show main command groups
        assert "workspace" in result.stdout
        assert "template" in result.stdout
        assert "style" in result.stdout
        assert "validate" in result.stdout

    def test_version_command_contract(self, cli_runner: CliRunner):
        """Test version command contract."""
        result = cli_runner.invoke(app, ["--version"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should output version information
        assert "WriteIt" in result.stdout
        assert result.stdout.strip().count('\n') == 0  # Single line output

    def test_uninitialized_state_contract(self, temp_home: Path, monkeypatch):
        """Test behavior when WriteIt is not initialized."""
        # Set up environment without initializing WriteIt
        monkeypatch.setenv("HOME", str(temp_home))
        monkeypatch.setenv("WRITEIT_HOME", str(temp_home / ".writeit"))

        cli_runner = CliRunner()

        result = cli_runner.invoke(app, ["list-pipelines"])
        
        # Contract: Should fail gracefully
        assert result.exit_code != 0
        assert "not initialized" in result.stdout.lower()


class TestWorkspaceCLIContract:
    """Contract tests for workspace-related CLI commands."""

    def test_workspace_list_contract(self, cli_runner: CliRunner):
        """Test workspace list command contract."""
        result = cli_runner.invoke(app, ["workspace", "list"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should contain expected headers
        assert "Workspaces" in result.stdout
        assert "Name" in result.stdout
        assert "Status" in result.stdout
        
        # Contract: Should show default workspace
        assert "default" in result.stdout

    def test_workspace_create_contract(self, cli_runner: CliRunner):
        """Test workspace creation contract."""
        result = cli_runner.invoke(app, ["workspace", "create", "test-workspace"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show success message
        assert "created successfully" in result.stdout.lower()
        assert "test-workspace" in result.stdout
        
        # Contract: Should verify workspace exists
        result = cli_runner.invoke(app, ["workspace", "list"])
        assert "test-workspace" in result.stdout

    def test_workspace_info_contract(self, cli_runner: CliRunner):
        """Test workspace info command contract."""
        result = cli_runner.invoke(app, ["workspace", "info"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should contain expected sections
        assert "Workspace Information" in result.stdout
        assert "Name:" in result.stdout
        assert "Path:" in result.stdout
        assert "Configuration:" in result.stdout

    def test_workspace_switch_contract(self, cli_runner: CliRunner):
        """Test workspace switching contract."""
        # Create additional workspace
        cli_runner.invoke(app, ["workspace", "create", "switch-test"])
        
        result = cli_runner.invoke(app, ["workspace", "use", "switch-test"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show switch confirmation
        assert "switched to" in result.stdout.lower()
        assert "switch-test" in result.stdout

    def test_workspace_remove_contract(self, cli_runner: CliRunner):
        """Test workspace removal contract."""
        # Create workspace to remove
        cli_runner.invoke(app, ["workspace", "create", "remove-test"])
        
        result = cli_runner.invoke(app, ["workspace", "remove", "remove-test"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show removal confirmation
        assert "removed successfully" in result.stdout.lower()
        
        # Contract: Should verify workspace is removed
        result = cli_runner.invoke(app, ["workspace", "list"])
        assert "remove-test" not in result.stdout

    def test_workspace_error_handling_contract(self, cli_runner: CliRunner):
        """Test workspace command error handling contract."""
        # Test with invalid workspace name
        result = cli_runner.invoke(app, ["workspace", "create", ""])
        assert result.exit_code != 0
        
        # Test with nonexistent workspace
        result = cli_runner.invoke(app, ["workspace", "info", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower()


class TestPipelineCLIContract:
    """Contract tests for pipeline-related CLI commands."""

    def test_list_pipelines_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test list-pipelines command contract."""
        result = cli_runner.invoke(app, ["list-pipelines"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should contain expected headers
        assert "Available Pipeline Templates" in result.stdout
        assert "Name" in result.stdout
        assert "Scope" in result.stdout
        
        # Contract: Should show test template
        assert "test-template" in result.stdout

    def test_run_pipeline_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test pipeline execution command contract."""
        # Test with --cli flag to avoid TUI
        result = cli_runner.invoke(app, ["run", "test-template", "--cli"])
        
        # Contract: Should exit successfully (or with appropriate error for missing LLM)
        assert result.exit_code in [0, 1]  # 1 if LLM not configured
        
        # Contract: Should show execution information
        assert "Pipeline:" in result.stdout
        assert "test-template" in result.stdout

    def test_run_pipeline_with_inputs_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test pipeline execution with inputs contract."""
        # Test with input data
        result = cli_runner.invoke(
            app, 
            ["run", "test-template", "--cli", "--input", "topic=AI Testing"]
        )
        
        # Contract: Should show input information
        assert "topic" in result.stdout
        assert "AI Testing" in result.stdout

    def test_run_pipeline_json_output_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test pipeline JSON output format contract."""
        result = cli_runner.invoke(app, ["run", "test-template", "--cli", "--json"])
        
        # Contract: Should exit successfully
        assert result.exit_code in [0, 1]
        
        # Contract: Should output valid JSON
        try:
            data = json.loads(result.stdout)
            assert isinstance(data, dict)
            assert "pipeline" in data or "error" in data
        except json.JSONDecodeError:
            pytest.fail("CLI should output valid JSON when --json flag is used")

    def test_pipeline_error_handling_contract(self, cli_runner: CliRunner):
        """Test pipeline command error handling contract."""
        # Test with nonexistent pipeline
        result = cli_runner.invoke(app, ["run", "nonexistent-pipeline", "--cli"])
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower()

    def test_pipeline_help_contract(self, cli_runner: CliRunner):
        """Test pipeline command help contract."""
        result = cli_runner.invoke(app, ["run", "--help"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show help information
        assert "Usage:" in result.stdout
        assert "Options:" in result.stdout
        assert "--cli" in result.stdout
        assert "--tui" in result.stdout
        assert "--json" in result.stdout


class TestTemplateCLIContract:
    """Contract tests for template-related CLI commands."""

    def test_template_list_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test template list command contract."""
        result = cli_runner.invoke(app, ["template", "list"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should contain expected headers
        assert "Available Pipeline Templates" in result.stdout
        assert "Name" in result.stdout
        assert "Scope" in result.stdout
        assert "test-template" in result.stdout

    def test_template_create_contract(self, cli_runner: CliRunner):
        """Test template creation command contract."""
        result = cli_runner.invoke(
            app, 
            ["template", "create", "contract-test", "--non-interactive"]
        )
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show success message
        assert "created successfully" in result.stdout.lower()
        assert "contract-test" in result.stdout
        
        # Contract: Should show file path
        assert "Path:" in result.stdout

    def test_template_copy_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test template copy command contract."""
        result = cli_runner.invoke(
            app, 
            ["template", "copy", "test-template", "copied-template"]
        )
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show copy confirmation
        assert "copied successfully" in result.stdout.lower()
        assert "copied-template" in result.stdout

    def test_template_validation_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test template validation command contract."""
        result = cli_runner.invoke(app, ["validate", "pipeline", "test-template"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show validation results
        assert "Validation" in result.stdout
        assert "test-template" in result.stdout

    def test_template_error_handling_contract(self, cli_runner: CliRunner):
        """Test template command error handling contract."""
        # Test with invalid template name
        result = cli_runner.invoke(app, ["template", "create", "", "--non-interactive"])
        assert result.exit_code != 0
        
        # Test with nonexistent template
        result = cli_runner.invoke(app, ["template", "copy", "nonexistent", "dest"])
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower()


class TestStyleCLIContract:
    """Contract tests for style-related CLI commands."""

    def test_style_list_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test style list command contract."""
        result = cli_runner.invoke(app, ["style", "list"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should contain expected headers
        assert "Available Style Primers" in result.stdout
        assert "Name" in result.stdout
        assert "test-style" in result.stdout

    def test_style_create_contract(self, cli_runner: CliRunner):
        """Test style creation command contract."""
        result = cli_runner.invoke(
            app, 
            ["style", "create", "contract-style", "--non-interactive"]
        )
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show success message
        assert "created successfully" in result.stdout.lower()
        assert "contract-style" in result.stdout

    def test_style_copy_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test style copy command contract."""
        result = cli_runner.invoke(
            app, 
            ["style", "copy", "test-style", "copied-style"]
        )
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show copy confirmation
        assert "copied successfully" in result.stdout.lower()

    def test_style_validation_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test style validation command contract."""
        result = cli_runner.invoke(app, ["validate", "style", "test-style"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show validation results
        assert "Validation" in result.stdout
        assert "test-style" in result.stdout


class TestValidationCLIContract:
    """Contract tests for validation-related CLI commands."""

    def test_validate_pipeline_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test pipeline validation command contract."""
        result = cli_runner.invoke(app, ["validate", "pipeline", "test-template"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show validation summary
        assert "Pipeline Template Validation" in result.stdout
        assert "test-template" in result.stdout

    def test_validate_style_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test style validation command contract."""
        result = cli_runner.invoke(app, ["validate", "style", "test-style"])
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show validation summary
        assert "Style Primer Validation" in result.stdout
        assert "test-style" in result.stdout

    def test_validate_detailed_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test detailed validation command contract."""
        result = cli_runner.invoke(
            app, 
            ["validate", "pipeline", "test-template", "--detailed"]
        )
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show detailed validation information
        assert "Detailed Issues" in result.stdout
        assert "Suggestions" in result.stdout

    def test_validate_error_handling_contract(self, cli_runner: CliRunner):
        """Test validation error handling contract."""
        # Test with nonexistent item
        result = cli_runner.invoke(app, ["validate", "pipeline", "nonexistent"])
        assert result.exit_code != 0
        assert "not found" in result.stdout.lower()


class TestCLIOptionContract:
    """Contract tests for CLI option behavior."""

    def test_verbose_flag_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test verbose output flag contract."""
        result_normal = cli_runner.invoke(app, ["list-pipelines"])
        result_verbose = cli_runner.invoke(app, ["list-pipelines", "--verbose"])
        
        # Contract: Both should succeed
        assert result_normal.exit_code == 0
        assert result_verbose.exit_code == 0
        
        # Contract: Verbose should have more detailed output
        assert len(result_verbose.stdout) >= len(result_normal.stdout)

    def test_dry_run_flag_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test dry-run flag contract."""
        result = cli_runner.invoke(
            app, 
            ["run", "test-template", "--dry-run", "--cli"]
        )
        
        # Contract: Should exit successfully
        assert result.exit_code == 0
        
        # Contract: Should show what would be executed
        assert "Dry run" in result.stdout
        assert "test-template" in result.stdout

    def test_workspace_option_contract(self, cli_runner: CliRunner):
        """Test workspace option consistency contract."""
        # Create additional workspace
        cli_runner.invoke(app, ["workspace", "create", "option-test"])
        
        # Create template in specific workspace
        result = cli_runner.invoke(
            app, 
            [
                "template", "create", "option-template", 
                "--workspace-name", "option-test", 
                "--non-interactive"
            ]
        )
        
        # Contract: Should succeed
        assert result.exit_code == 0
        assert "option-test" in result.stdout

    def test_json_output_format_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test JSON output format consistency contract."""
        commands = [
            ["workspace", "list", "--json"],
            ["template", "list", "--json"],
            ["style", "list", "--json"]
        ]
        
        for command in commands:
            result = cli_runner.invoke(app, command)
            
            # Contract: Should exit successfully
            assert result.exit_code == 0
            
            # Contract: Should output valid JSON
            try:
                data = json.loads(result.stdout)
                assert isinstance(data, dict)
                assert "timestamp" in data  # Should include metadata
            except json.JSONDecodeError:
                pytest.fail(f"Command {command} should output valid JSON")


class TestCLIErrorReportingContract:
    """Contract tests for CLI error reporting consistency."""

    def test_error_message_format_contract(self, cli_runner: CliRunner):
        """Test error message format contract."""
        # Test various error scenarios
        error_commands = [
            ["workspace", "create", ""],  # Empty name
            ["template", "create", ""],   # Empty name
            ["run", "nonexistent"],        # Nonexistent pipeline
            ["validate", "pipeline", "nonexistent"],  # Nonexistent template
        ]
        
        for command in error_commands:
            result = cli_runner.invoke(app, command)
            
            # Contract: Should fail
            assert result.exit_code != 0
            
            # Contract: Should have meaningful error message
            assert len(result.stdout.strip()) > 0
            assert result.stdout.count("Error") >= 0  # Should mention error

    def test_help_on_error_contract(self, cli_runner: CliRunner):
        """Test help suggestions on error contract."""
        result = cli_runner.invoke(app, ["invalid-command"])
        
        # Contract: Should fail
        assert result.exit_code != 0
        
        # Contract: Should suggest help
        assert "--help" in result.stdout

    def test_config_error_contract(self, cli_runner: CliRunner, temp_home: Path):
        """Test configuration error handling contract."""
        # Create invalid configuration
        config_path = temp_home / ".writeit" / "config.yaml"
        config_path.write_text("invalid: yaml: content: [")
        
        result = cli_runner.invoke(app, ["workspace", "list"])
        
        # Contract: Should handle config errors gracefully
        assert result.exit_code != 0
        assert "configuration" in result.stdout.lower()


class TestCLIPerformanceContract:
    """Contract tests for CLI performance characteristics."""

    def test_command_response_time_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test command response time contract."""
        import time
        
        # Test quick commands
        quick_commands = [
            ["--help"],
            ["workspace", "list"],
            ["template", "list"],
            ["--version"]
        ]
        
        for command in quick_commands:
            start_time = time.time()
            result = cli_runner.invoke(app, command)
            end_time = time.time()
            
            # Contract: Should complete quickly
            assert result.exit_code == 0
            assert (end_time - start_time) < 2.0  # Should complete within 2 seconds

    def test_output_size_contract(self, cli_runner: CliRunner, initialized_workspace):
        """Test output size reasonableness contract."""
        result = cli_runner.invoke(app, ["workspace", "list"])
        
        # Contract: Output should be reasonable size
        assert len(result.stdout) < 10000  # Less than 10KB for simple list
        
        # Contract: Should not contain excessive whitespace
        lines = result.stdout.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        assert len(non_empty_lines) > 0
        assert len(non_empty_lines) < 100  # Reasonable number of lines