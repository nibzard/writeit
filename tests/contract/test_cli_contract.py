# ABOUTME: Contract tests for WriteIt CLI interface
# ABOUTME: Tests CLI commands and their expected behavior and outputs
import pytest
import tempfile
import shutil
import subprocess
import sys
from pathlib import Path
import yaml
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from writeit.cli.app import app
from writeit.workspace.workspace import Workspace


class TestCLIContract:
    """Contract tests for WriteIt CLI interface."""
    
    @pytest.fixture
    def temp_home(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def runner(self):
        """Create CliRunner for testing Typer commands."""
        return CliRunner()
    
    @pytest.fixture
    def workspace_manager(self, temp_home):
        """Create workspace manager with temporary directory."""
        return Workspace(temp_home / ".writeit")
    
    def test_help_command(self, runner):
        """Test help command shows expected output."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "WriteIt" in result.stdout
        assert "Commands" in result.stdout
        assert "init" in result.stdout
        assert "workspace" in result.stdout
        assert "completion" in result.stdout
    
    def test_init_command_help(self, runner):
        """Test init command help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "Initialize WriteIt home directory" in result.stdout
        assert "--migrate" in result.stdout
    
    def test_workspace_help(self, runner):
        """Test workspace command help."""
        result = runner.invoke(app, ["workspace", "--help"])
        assert result.exit_code == 0
        assert "Manage WriteIt workspaces" in result.stdout
        assert "create" in result.stdout
        assert "list" in result.stdout
        assert "use" in result.stdout
    
    def test_init_command_with_migration(self, workspace_manager, temp_home, capsys):
        """Test init command with migration flag."""
        # Create a mock local workspace to migrate
        local_workspace = temp_home / "local_project"
        local_workspace.mkdir()
        local_writeit = local_workspace / ".writeit"
        local_writeit.mkdir()
        (local_writeit / "pipelines").mkdir()
        (local_writeit / "articles").mkdir()
        
        args = Mock()
        args.migrate = True
        
        # Mock the migration function to return some results
        with patch('writeit.cli.main.find_and_migrate_workspaces') as mock_migrate:
            mock_migrate.return_value = [(local_workspace, True, "Migrated successfully")]
            
            result = handle_init(workspace_manager, args)
            
            assert result == 0
            captured = capsys.readouterr()
            assert "Searching for local workspaces to migrate" in captured.out
            assert "Migrated 1 workspaces" in captured.out
    
    def test_workspace_create_command(self, workspace_manager, capsys):
        """Test workspace create command."""
        workspace_manager.initialize()
        
        args = Mock()
        args.workspace_action = "create"
        args.name = "test_workspace"
        
        result = handle_workspace(workspace_manager, args)
        
        assert result == 0
        assert workspace_manager.workspace_exists("test_workspace")
        
        captured = capsys.readouterr()
        assert "✓ Created workspace 'test_workspace'" in captured.out
    
    def test_workspace_list_command(self, workspace_manager, capsys):
        """Test workspace list command."""
        workspace_manager.initialize()
        workspace_manager.create_workspace("workspace1")
        workspace_manager.create_workspace("workspace2")
        
        args = Mock()
        args.workspace_action = "list"
        
        result = handle_workspace(workspace_manager, args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Available workspaces:" in captured.out
        assert "* default" in captured.out  # Active workspace marked with *
        assert "  workspace1" in captured.out
        assert "  workspace2" in captured.out
    
    def test_workspace_use_command(self, workspace_manager, capsys):
        """Test workspace use command."""
        workspace_manager.initialize()
        workspace_manager.create_workspace("target_workspace")
        
        args = Mock()
        args.workspace_action = "use"
        args.name = "target_workspace"
        
        result = handle_workspace(workspace_manager, args)
        
        assert result == 0
        assert workspace_manager.get_active_workspace() == "target_workspace"
        
        captured = capsys.readouterr()
        assert "✓ Switched to workspace 'target_workspace'" in captured.out
    
    def test_workspace_remove_command(self, workspace_manager, capsys):
        """Test workspace remove command."""
        workspace_manager.initialize()
        workspace_manager.create_workspace("to_remove")
        
        # Make sure we're not trying to remove the active workspace
        assert workspace_manager.get_active_workspace() == "default"
        
        args = Mock()
        args.workspace_action = "remove"
        args.name = "to_remove"
        
        result = handle_workspace(workspace_manager, args)
        
        assert result == 0
        assert not workspace_manager.workspace_exists("to_remove")
        
        captured = capsys.readouterr()
        assert "✓ Removed workspace 'to_remove'" in captured.out
    
    def test_workspace_info_command(self, workspace_manager, capsys):
        """Test workspace info command."""
        workspace_manager.initialize()
        workspace_manager.create_workspace("info_test")
        
        args = Mock()
        args.workspace_action = "info"
        args.name = "info_test"
        
        result = handle_workspace(workspace_manager, args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Workspace: info_test" in captured.out
        assert "Path:" in captured.out
        assert "Created:" in captured.out
        assert "Default pipeline: None" in captured.out
        assert "Stored entries:" in captured.out
    
    def test_workspace_command_not_initialized_error(self, workspace_manager, capsys):
        """Test workspace commands when WriteIt is not initialized."""
        args = Mock()
        args.workspace_action = "list"
        
        result = handle_workspace(workspace_manager, args)
        
        assert result == 1
        
        captured = capsys.readouterr()
        assert "WriteIt not initialized. Run 'writeit init' first." in captured.err
    
    def test_workspace_create_duplicate_error(self, workspace_manager, capsys):
        """Test error when creating duplicate workspace."""
        workspace_manager.initialize()
        
        args = Mock()
        args.workspace_action = "create"
        args.name = "default"  # Default already exists
        
        result = handle_workspace(workspace_manager, args)
        
        assert result == 1
        
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "already exists" in captured.err
    
    def test_list_pipelines_command(self, workspace_manager, capsys):
        """Test list pipelines command."""
        workspace_manager.initialize()
        
        # Create some pipeline templates
        workspace_manager.templates_dir.mkdir(exist_ok=True)
        global_pipeline = workspace_manager.templates_dir / "tech-article.yaml"
        with open(global_pipeline, 'w') as f:
            yaml.dump({"name": "tech-article", "steps": []}, f)
        
        # Create workspace-specific pipeline
        workspace_path = workspace_manager.get_workspace_path("default")
        workspace_pipeline = workspace_path / "pipelines" / "custom-pipeline.yaml"
        with open(workspace_pipeline, 'w') as f:
            yaml.dump({"name": "custom-pipeline", "steps": []}, f)
        
        args = Mock()
        args.workspace = None
        
        with patch('writeit.cli.main.get_active_workspace', return_value='default'):
            result = handle_list_pipelines(workspace_manager, args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "Global pipeline templates:" in captured.out
        assert "tech-article" in captured.out
        assert "Workspace 'default' pipelines:" in captured.out
        assert "custom-pipeline" in captured.out
    
    def test_list_pipelines_no_pipelines(self, workspace_manager, capsys):
        """Test list pipelines when no pipelines exist."""
        workspace_manager.initialize()
        
        args = Mock()
        args.workspace = None
        
        with patch('writeit.cli.main.get_active_workspace', return_value='default'):
            result = handle_list_pipelines(workspace_manager, args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        assert "No pipeline templates found" in captured.out
    
    def test_run_command_pipeline_found(self, workspace_manager):
        """Test run command with existing pipeline."""
        workspace_manager.initialize()
        
        # Create pipeline template with proper structure
        global_pipeline = workspace_manager.templates_dir / "test-pipeline.yaml"
        with open(global_pipeline, 'w') as f:
            yaml.dump({
                "metadata": {"name": "Test Pipeline", "version": "1.0.0"},
                "inputs": {"topic": {"type": "text", "label": "Topic", "required": True}},
                "steps": {"draft": {"name": "Draft", "description": "Create draft", "type": "generate", "prompt_template": "Write about {{topic}}"}}
            }, f)
        
        runner = CliRunner()
        # Patch the TUI launch to avoid actually starting the interactive UI
        with patch('writeit.cli.commands.pipeline.run_pipeline_tui') as mock_tui:
            result = runner.invoke(app, ["run", "test-pipeline"])
        
        assert result.exit_code == 0
        assert "Pipeline: test-pipeline" in result.stdout
        assert "test-pipeline.yaml" in result.stdout
        assert "Launching pipeline TUI" in result.stdout
        mock_tui.assert_called_once()
    
    def test_run_command_pipeline_not_found(self, workspace_manager):
        """Test run command with nonexistent pipeline."""
        workspace_manager.initialize()
        
        runner = CliRunner()
        result = runner.invoke(app, ["run", "nonexistent"])
        
        assert result.exit_code == 1
        assert "Pipeline not found: nonexistent" in result.stdout
    
    def test_run_command_global_flag(self, workspace_manager):
        """Test run command with global flag."""
        workspace_manager.initialize()
        
        # Create global template with proper structure
        global_pipeline = workspace_manager.templates_dir / "global-template.yaml"
        with open(global_pipeline, 'w') as f:
            yaml.dump({
                "metadata": {"name": "Global Template", "version": "1.0.0"},
                "inputs": {"topic": {"type": "text", "label": "Topic", "required": True}},
                "steps": {"draft": {"name": "Draft", "description": "Create draft", "type": "generate", "prompt_template": "Write about {{topic}}"}}
            }, f)
        
        runner = CliRunner()
        # Patch the TUI launch to avoid actually starting the interactive UI
        with patch('writeit.cli.commands.pipeline.run_pipeline_tui') as mock_tui:
            result = runner.invoke(app, ["run", "global-template", "--global"])
        
        assert result.exit_code == 0
        assert "Pipeline: global-template" in result.stdout
        assert "Scope: Global" in result.stdout
    
    def test_run_command_not_initialized_error(self, workspace_manager, capsys):
        """Test run command when WriteIt is not initialized."""
        args = Mock()
        args.workspace = None
        args.pipeline = "test.yaml"
        args.use_global = False
        
        result = handle_run(workspace_manager, args)
        
        assert result == 1
        
        captured = capsys.readouterr()
        assert "WriteIt not initialized. Run 'writeit init' first." in captured.err


class TestCLIErrorHandling:
    """Test CLI error handling and edge cases."""
    
    @pytest.fixture
    def temp_home(self):
        """Create temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture  
    def workspace_manager(self, temp_home):
        """Create workspace manager with temporary directory."""
        return Workspace(temp_home / ".writeit")
    
    def test_init_command_exception_handling(self, workspace_manager, capsys):
        """Test init command handles exceptions gracefully."""
        args = Mock()
        args.migrate = False
        
        # Mock initialize to raise an exception
        with patch.object(workspace_manager, 'initialize', side_effect=Exception("Test error")):
            result = handle_init(workspace_manager, args)
            
            assert result == 1
            captured = capsys.readouterr()
            assert "Error initializing WriteIt: Test error" in captured.err
    
    def test_workspace_invalid_action(self, workspace_manager, capsys):
        """Test workspace command with invalid action."""
        workspace_manager.initialize()
        
        args = Mock()
        args.workspace_action = "invalid_action"
        
        result = handle_workspace(workspace_manager, args)
        
        assert result == 1
        
        captured = capsys.readouterr()
        assert "Invalid workspace action" in captured.err
    
    def test_workspace_command_value_error(self, workspace_manager, capsys):
        """Test workspace command handling ValueError."""
        workspace_manager.initialize()
        
        args = Mock()
        args.workspace_action = "use"
        args.name = "nonexistent_workspace"
        
        result = handle_workspace(workspace_manager, args)
        
        assert result == 1
        
        captured = capsys.readouterr()
        assert "Error:" in captured.err
        assert "does not exist" in captured.err
    
    def test_list_pipelines_exception_handling(self, workspace_manager, capsys):
        """Test list pipelines command handles exceptions."""
        workspace_manager.initialize()
        
        args = Mock()
        args.workspace = None
        
        # Mock get_active_workspace to raise exception
        with patch('writeit.cli.main.get_active_workspace', side_effect=Exception("Test error")):
            result = handle_list_pipelines(workspace_manager, args)
            
            assert result == 1
            captured = capsys.readouterr()
            assert "Error listing pipelines: Test error" in captured.err
    
    def test_run_command_exception_handling(self, workspace_manager, capsys):
        """Test run command handles exceptions gracefully."""
        workspace_manager.initialize()
        
        args = Mock()
        args.workspace = None
        args.pipeline = "test.yaml"
        args.use_global = False
        
        # Mock get_active_workspace to raise exception
        with patch('writeit.cli.main.get_active_workspace', side_effect=Exception("Test error")):
            result = handle_run(workspace_manager, args)
            
            assert result == 1
            captured = capsys.readouterr()
            assert "Error running pipeline: Test error" in captured.err


class TestCLIArgumentParsing:
    """Test CLI argument parsing and validation."""
    
    def test_main_no_command_shows_help(self, capsys):
        """Test that main with no command shows help."""
        with patch('sys.argv', ['writeit']):
            with patch('writeit.cli.main.Workspace'):
                result = main()
                
                assert result == 0
                captured = capsys.readouterr()
                assert "usage: writeit" in captured.out
    
    def test_version_argument(self, capsys):
        """Test --version argument."""
        with patch('sys.argv', ['writeit', '--version']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "writeit" in captured.out
    
    def test_global_workspace_argument(self):
        """Test global --workspace argument parsing."""
        with patch('sys.argv', ['writeit', '--workspace', 'test', 'workspace', 'list']):
            with patch('writeit.cli.main.handle_workspace') as mock_handle:
                mock_handle.return_value = 0
                
                result = main()
                
                assert result == 0
                # Verify that the workspace argument was parsed
                args = mock_handle.call_args[0][1]  # Second argument (args)
                assert args.workspace == 'test'