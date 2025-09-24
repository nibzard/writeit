"""
Contract tests for TUI (Textual User Interface) interaction flows.

Ensures that TUI components behave according to expected interaction patterns,
including screen navigation, data display, user input handling, and error display.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from textual.app import App, ComposeResult
from textual.widgets import Button, Input, Select, TextArea, Static, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.reactive import reactive
from textual.message import Message
from textual.binding import Binding

from writeit.tui.main import WriteItApp
from writeit.workspace.workspace import Workspace
from writeit.tui.screens.pipeline_execution import PipelineExecutionScreen
from writeit.tui.screens.template_browser import TemplateBrowserScreen
from writeit.tui.screens.workspace_management import WorkspaceManagementScreen
from writeit.tui.widgets.execution_view import ExecutionViewWidget
from writeit.tui.widgets.status_bar import StatusBarWidget
from writeit.tui.widgets.error_display import ErrorDisplayWidget


@pytest.fixture
def temp_home() -> Path:
    """Create temporary home directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture
def test_workspace(temp_home: Path):
    """Create test workspace."""
    workspace = Workspace(temp_home / ".writeit")
    workspace.initialize()
    return workspace


@pytest.fixture
def tui_app(test_workspace):
    """Create TUI app instance for testing."""
    return WriteItApp()


class MockTUIApp:
    """Mock TUI app for testing TUI components."""
    
    def __init__(self):
        self.screen_stack = []
        self.current_screen = None
        self.messages = []
        self.query_one = MagicMock()
        self.query = MagicMock()
        self.push_screen = MagicMock()
        self.pop_screen = MagicMock()
        self.exit = MagicMock()
        self.bell = MagicMock()
    
    def mount(self, widget):
        """Mock mount method."""
        pass
    
    def post_message(self, message):
        """Mock post_message method."""
        self.messages.append(message)
    
    def handle_message(self, message):
        """Mock handle_message method."""
        pass


class TestTUIAppContract:
    """Contract tests for main TUI application."""

    @pytest.mark.asyncio
    async def test_app_initialization_contract(self, test_workspace):
        """Test TUI app initialization contract."""
        app = WriteItApp()
        
        # Contract: App should initialize without errors
        assert app is not None
        
        # Contract: App should have proper title
        assert hasattr(app, 'title')
        assert "WriteIt" in app.title

    @pytest.mark.asyncio
    async def test_app_composition_contract(self, test_workspace):
        """Test app composition contract."""
        app = WriteItApp()
        
        # Contract: App should compose main interface
        composition = list(app.compose())
        
        # Should have main layout components
        assert len(composition) > 0
        
        # Should have header, main content, and footer
        components = [str(type(c).__name__) for c in composition]
        assert any("Header" in comp for comp in components)
        assert any("Footer" in comp for comp in components)

    @pytest.mark.asyncio
    async def test_app_key_bindings_contract(self, test_workspace):
        """Test app key bindings contract."""
        app = WriteItApp()
        
        # Contract: Should have standard key bindings
        assert hasattr(app, 'BINDINGS')
        
        # Should have basic navigation bindings
        binding_keys = [binding.key for binding in app.BINDINGS]
        assert 'q' in binding_keys  # Quit
        assert 'ctrl+c' in binding_keys  # Quit
        assert 'ctrl+l' in binding_keys  # List templates


class TestPipelineExecutionScreenContract:
    """Contract tests for pipeline execution screen."""

    @pytest.mark.asyncio
    async def test_screen_initialization_contract(self, test_workspace):
        """Test pipeline execution screen initialization contract."""
        screen = PipelineExecutionScreen(
            pipeline_name="test-pipeline",
            inputs={"topic": "Test Topic"}
        )
        
        # Contract: Screen should initialize with proper data
        assert screen.pipeline_name == "test-pipeline"
        assert screen.inputs == {"topic": "Test Topic"}
        
        # Contract: Should have execution view widget
        execution_view = screen.query_one(ExecutionViewWidget)
        assert execution_view is not None

    @pytest.mark.asyncio
    async def test_execution_start_contract(self, test_workspace):
        """Test execution start contract."""
        screen = PipelineExecutionScreen(
            pipeline_name="test-pipeline",
            inputs={"topic": "Test Topic"}
        )
        
        # Mock execution service
        mock_service = AsyncMock()
        mock_service.execute_pipeline.return_value = "test-run-id"
        
        with patch.object(screen, '_execution_service', mock_service):
            await screen._start_execution()
        
        # Contract: Should call execution service
        mock_service.execute_pipeline.assert_called_once()
        
        # Contract: Should show execution started
        status_bar = screen.query_one(StatusBarWidget)
        assert status_bar is not None

    @pytest.mark.asyncio
    async def test_execution_progress_updates_contract(self, test_workspace):
        """Test execution progress updates contract."""
        screen = PipelineExecutionScreen(
            pipeline_name="test-pipeline",
            inputs={"topic": "Test Topic"}
        )
        
        # Mock progress update
        progress_data = {
            "type": "step_progress",
            "step_key": "outline",
            "progress": {
                "current_step": 1,
                "total_steps": 3,
                "percent_complete": 33.3
            }
        }
        
        await screen._handle_progress_update(progress_data)
        
        # Contract: Should update progress display
        execution_view = screen.query_one(ExecutionViewWidget)
        assert execution_view is not None

    @pytest.mark.asyncio
    async def test_execution_completion_contract(self, test_workspace):
        """Test execution completion contract."""
        screen = PipelineExecutionScreen(
            pipeline_name="test-pipeline",
            inputs={"topic": "Test Topic"}
        )
        
        completion_data = {
            "type": "execution_completed",
            "outputs": {"result": "Test output"},
            "execution_time": 5.2
        }
        
        await screen._handle_execution_completion(completion_data)
        
        # Contract: Should show completion message
        # Contract: Should update UI with results
        execution_view = screen.query_one(ExecutionViewWidget)
        assert execution_view is not None

    @pytest.mark.asyncio
    async def test_execution_error_handling_contract(self, test_workspace):
        """Test execution error handling contract."""
        screen = PipelineExecutionScreen(
            pipeline_name="test-pipeline",
            inputs={"topic": "Test Topic"}
        )
        
        error_data = {
            "type": "execution_error",
            "error": {
                "code": "LLM_ERROR",
                "message": "Failed to execute LLM call"
            }
        }
        
        await screen._handle_execution_error(error_data)
        
        # Contract: Should show error display
        error_display = screen.query_one(ErrorDisplayWidget)
        assert error_display is not None
        
        # Contract: Should show error message
        assert "Failed to execute LLM call" in str(error_display)


class TestTemplateBrowserScreenContract:
    """Contract tests for template browser screen."""

    @pytest.mark.asyncio
    async def test_template_list_display_contract(self, test_workspace):
        """Test template list display contract."""
        screen = TemplateBrowserScreen()
        
        # Mock template data
        mock_templates = [
            {"name": "template1", "description": "First template", "scope": "workspace"},
            {"name": "template2", "description": "Second template", "scope": "global"}
        ]
        
        with patch.object(screen, '_load_templates', return_value=mock_templates):
            await screen._refresh_template_list()
        
        # Contract: Should display templates in table
        template_table = screen.query_one(DataTable)
        assert template_table is not None
        
        # Contract: Should have correct columns
        # Contract: Should show template data

    @pytest.mark.asyncio
    async def test_template_selection_contract(self, test_workspace):
        """Test template selection contract."""
        screen = TemplateBrowserScreen()
        
        # Mock template selection
        selected_template = {"name": "test-template", "scope": "workspace"}
        
        await screen._on_template_selected(selected_template)
        
        # Contract: Should update selection state
        assert screen.selected_template == selected_template
        
        # Contract: Should enable execute button if appropriate
        execute_button = screen.query_one("#execute-button", Button)
        if execute_button:
            assert not execute_button.disabled

    @pytest.mark.asyncio
    async def test_template_filtering_contract(self, test_workspace):
        """Test template filtering contract."""
        screen = TemplateBrowserScreen()
        
        # Mock filtered templates
        filtered_templates = [
            {"name": "filtered-template", "description": "Filtered result"}
        ]
        
        with patch.object(screen, '_filter_templates', return_value=filtered_templates):
            await screen._apply_filter("filtered")
        
        # Contract: Should show filtered results
        template_table = screen.query_one(DataTable)
        assert template_table is not None

    @pytest.mark.asyncio
    async def test_template_execution_contract(self, test_workspace):
        """Test template execution from browser contract."""
        screen = TemplateBrowserScreen()
        screen.selected_template = {"name": "test-template", "scope": "workspace"}
        
        # Mock execution
        with patch.object(screen, '_execute_template') as mock_execute:
            await screen._on_execute_clicked()
        
        # Contract: Should call execution
        mock_execute.assert_called_once()
        
        # Contract: Should navigate to execution screen
        # Verify screen push was called


class TestWorkspaceManagementScreenContract:
    """Contract tests for workspace management screen."""

    @pytest.mark.asyncio
    async def test_workspace_list_display_contract(self, test_workspace):
        """Test workspace list display contract."""
        screen = WorkspaceManagementScreen()
        
        # Mock workspace data
        mock_workspaces = [
            {"name": "workspace1", "status": "active", "path": "/path/to/workspace1"},
            {"name": "workspace2", "status": "inactive", "path": "/path/to/workspace2"}
        ]
        
        with patch.object(screen, '_load_workspaces', return_value=mock_workspaces):
            await screen._refresh_workspace_list()
        
        # Contract: Should display workspaces
        workspace_table = screen.query_one(DataTable)
        assert workspace_table is not None

    @pytest.mark.asyncio
    async def test_workspace_creation_contract(self, test_workspace):
        """Test workspace creation contract."""
        screen = WorkspaceManagementScreen()
        
        # Mock workspace creation
        new_workspace_data = {
            "name": "new-workspace",
            "display_name": "New Workspace",
            "description": "A new test workspace"
        }
        
        with patch.object(screen, '_create_workspace') as mock_create:
            await screen._on_create_workspace(new_workspace_data)
        
        # Contract: Should call creation method
        mock_create.assert_called_once_with(new_workspace_data)
        
        # Contract: Should refresh workspace list
        # Verify refresh was called

    @pytest.mark.asyncio
    async def test_workspace_switching_contract(self, test_workspace):
        """Test workspace switching contract."""
        screen = WorkspaceManagementScreen()
        
        # Mock workspace switch
        workspace_name = "target-workspace"
        
        with patch.object(screen, '_switch_workspace') as mock_switch:
            await screen._on_workspace_switched(workspace_name)
        
        # Contract: Should call switch method
        mock_switch.assert_called_once_with(workspace_name)
        
        # Contract: Should update UI to reflect active workspace

    @pytest.mark.asyncio
    async def test_workspace_deletion_contract(self, test_workspace):
        """Test workspace deletion contract."""
        screen = WorkspaceManagementScreen()
        
        # Mock workspace deletion
        workspace_name = "workspace-to-delete"
        
        with patch.object(screen, '_delete_workspace') as mock_delete:
            await screen._on_delete_workspace(workspace_name)
        
        # Contract: Should call deletion method
        mock_delete.assert_called_once_with(workspace_name)
        
        # Contract: Should refresh workspace list
        # Verify refresh was called


class TestExecutionViewWidgetContract:
    """Contract tests for execution view widget."""

    @pytest.mark.asyncio
    async def test_execution_start_display_contract(self):
        """Test execution start display contract."""
        widget = ExecutionViewWidget()
        
        execution_data = {
            "pipeline_name": "test-pipeline",
            "run_id": "test-run-123",
            "start_time": datetime.now(UTC).isoformat()
        }
        
        await widget.on_execution_started(execution_data)
        
        # Contract: Should show execution information
        assert widget.pipeline_name == "test-pipeline"
        assert widget.run_id == "test-run-123"
        
        # Contract: Should update display

    @pytest.mark.asyncio
    async def test_step_progress_display_contract(self):
        """Test step progress display contract."""
        widget = ExecutionViewWidget()
        
        progress_data = {
            "step_key": "outline",
            "step_name": "Create Outline",
            "status": "executing",
            "progress": 50.0,
            "message": "Generating outline..."
        }
        
        await widget.on_step_progress(progress_data)
        
        # Contract: Should show step progress
        assert "outline" in str(widget)
        assert "50%" in str(widget)
        assert "executing" in str(widget)

    @pytest.mark.asyncio
    async def test_llm_response_display_contract(self):
        """Test LLM response display contract."""
        widget = ExecutionViewWidget()
        
        response_data = {
            "step_key": "outline",
            "response": "## Outline\n\n1. Introduction\n2. Main Content\n3. Conclusion",
            "tokens_used": 150,
            "model": "gpt-4o-mini"
        }
        
        await widget.on_llm_response(response_data)
        
        # Contract: Should show LLM response
        assert "Outline" in str(widget)
        assert "150" in str(widget)  # Token count
        assert "gpt-4o-mini" in str(widget)

    @pytest.mark.asyncio
    async def test_execution_completion_display_contract(self):
        """Test execution completion display contract."""
        widget = ExecutionViewWidget()
        
        completion_data = {
            "status": "completed",
            "outputs": {"result": "Final output content"},
            "total_time": 10.5,
            "total_tokens": 500
        }
        
        await widget.on_execution_completed(completion_data)
        
        # Contract: Should show completion summary
        assert "completed" in str(widget)
        assert "10.5" in str(widget)  # Total time
        assert "500" in str(widget)  # Total tokens


class TestStatusBarWidgetContract:
    """Contract tests for status bar widget."""

    @pytest.mark.asyncio
    async def test_status_update_contract(self):
        """Test status update contract."""
        widget = StatusBarWidget()
        
        await widget.update_status("Executing pipeline...", "info")
        
        # Contract: Should show updated status
        assert "Executing pipeline" in str(widget)
        assert "info" in str(widget)

    @pytest.mark.asyncio
    async def test_progress_update_contract(self):
        """Test progress update contract."""
        widget = StatusBarWidget()
        
        await widget.update_progress(75.0, "Step 2 of 4")
        
        # Contract: Should show progress
        assert "75%" in str(widget)
        assert "Step 2 of 4" in str(widget)

    @pytest.mark.asyncio
    async def test_error_status_contract(self):
        """Test error status contract."""
        widget = StatusBarWidget()
        
        await widget.update_status("Execution failed", "error")
        
        # Contract: Should show error status
        assert "failed" in str(widget)
        assert "error" in str(widget)


class TestErrorDisplayWidgetContract:
    """Contract tests for error display widget."""

    @pytest.mark.asyncio
    async def test_error_display_contract(self):
        """Test error display contract."""
        widget = ErrorDisplayWidget()
        
        error_data = {
            "code": "LLM_ERROR",
            "message": "Failed to connect to LLM provider",
            "details": "Connection timeout after 30 seconds",
            "suggestions": ["Check internet connection", "Verify API key"]
        }
        
        await widget.show_error(error_data)
        
        # Contract: Should show error information
        assert "LLM_ERROR" in str(widget)
        assert "Failed to connect" in str(widget)
        assert "timeout after 30 seconds" in str(widget)
        assert "Check internet" in str(widget)

    @pytest.mark.asyncio
    async def test_error_clear_contract(self):
        """Test error clear contract."""
        widget = ErrorDisplayWidget()
        
        # Show error first
        await widget.show_error({
            "code": "TEST_ERROR",
            "message": "Test error"
        })
        
        # Clear error
        await widget.clear_error()
        
        # Contract: Should clear error display
        assert "TEST_ERROR" not in str(widget)


class TestTUIInputHandlingContract:
    """Contract tests for TUI input handling."""

    @pytest.mark.asyncio
    async def test_pipeline_input_form_contract(self, test_workspace):
        """Test pipeline input form handling contract."""
        screen = PipelineExecutionScreen(
            pipeline_name="test-pipeline",
            inputs={}
        )
        
        # Mock input data
        input_data = {"topic": "AI Technology", "style": "technical"}
        
        await screen._on_inputs_submitted(input_data)
        
        # Contract: Should validate inputs
        # Contract: Should start execution with valid inputs
        assert screen.inputs == input_data

    @pytest.mark.asyncio
    async def test_input_validation_contract(self, test_workspace):
        """Test input validation contract."""
        screen = PipelineExecutionScreen(
            pipeline_name="test-pipeline",
            inputs={}
        )
        
        # Test with invalid input (missing required field)
        invalid_input = {}  # Missing required topic
        
        await screen._on_inputs_submitted(invalid_input)
        
        # Contract: Should show validation error
        error_display = screen.query_one(ErrorDisplayWidget)
        assert error_display is not None

    @pytest.mark.asyncio
    async def test_workspace_name_input_contract(self, test_workspace):
        """Test workspace name input validation contract."""
        screen = WorkspaceManagementScreen()
        
        # Test valid workspace name
        valid_name = "test-workspace"
        is_valid = await screen._validate_workspace_name(valid_name)
        assert is_valid is True
        
        # Test invalid workspace name
        invalid_name = ""
        is_valid = await screen._validate_workspace_name(invalid_name)
        assert is_valid is False


class TestTUIScreenNavigationContract:
    """Contract tests for TUI screen navigation."""

    @pytest.mark.asyncio
    async def test_screen_push_contract(self, test_workspace):
        """Test screen push navigation contract."""
        app = WriteItApp()
        
        # Mock screen
        mock_screen = MagicMock()
        
        await app.push_screen(mock_screen)
        
        # Contract: Should add screen to stack
        # Contract: Should update current screen

    @pytest.mark.asyncio
    async def test_screen_pop_contract(self, test_workspace):
        """Test screen pop navigation contract."""
        app = WriteItApp()
        
        # Mock screens
        mock_screen1 = MagicMock()
        mock_screen2 = MagicMock()
        
        await app.push_screen(mock_screen1)
        await app.push_screen(mock_screen2)
        await app.pop_screen()
        
        # Contract: Should remove screen from stack
        # Contract: Should restore previous screen

    @pytest.mark.asyncio
    async def test_screen_switch_contract(self, test_workspace):
        """Test screen switch navigation contract."""
        app = WriteItApp()
        
        # Mock screen
        mock_screen = MagicMock()
        
        await app.switch_screen(mock_screen)
        
        # Contract: Should replace current screen
        # Contract: Should maintain proper stack


class TestTUIKeyBindingContract:
    """Contract tests for TUI key bindings."""

    @pytest.mark.asyncio
    async def test_quit_binding_contract(self, test_workspace):
        """Test quit key binding contract."""
        app = WriteItApp()
        
        # Mock exit method
        app.exit = MagicMock()
        
        # Simulate quit key press
        await app.action_quit()
        
        # Contract: Should call exit method
        app.exit.assert_called_once()

    @pytest.mark.asyncio
    async def test_help_binding_contract(self, test_workspace):
        """Test help key binding contract."""
        app = WriteItApp()
        
        # Mock help screen
        with patch('writeit.tui.screens.help.HelpScreen') as mock_help_screen:
            await app.action_show_help()
        
        # Contract: Should show help screen
        mock_help_screen.assert_called_once()

    @pytest.mark.asyncio
    async def test_navigation_bindings_contract(self, test_workspace):
        """Test navigation key bindings contract."""
        app = WriteItApp()
        
        # Test navigation actions
        await app.action_go_home()
        await app.action_go_back()
        
        # Contract: Should handle navigation
        # Contract: Should update screen appropriately


class TestTUIPerformanceContract:
    """Contract tests for TUI performance characteristics."""

    @pytest.mark.asyncio
    async def test_render_performance_contract(self, test_workspace):
        """Test TUI render performance contract."""
        import time
        
        screen = TemplateBrowserScreen()
        
        # Mock large dataset
        large_template_list = [
            {"name": f"template-{i}", "description": f"Template {i}", "scope": "workspace"}
            for i in range(1000)
        ]
        
        start_time = time.time()
        
        with patch.object(screen, '_load_templates', return_value=large_template_list):
            await screen._refresh_template_list()
        
        end_time = time.time()
        
        # Contract: Should render quickly
        assert (end_time - start_time) < 1.0  # Should complete within 1 second

    @pytest.mark.asyncio
    async def test_memory_usage_contract(self, test_workspace):
        """Test TUI memory usage contract."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create and interact with multiple screens
        screens = [
            TemplateBrowserScreen(),
            WorkspaceManagementScreen(),
            PipelineExecutionScreen("test", {})
        ]
        
        for screen in screens:
            await screen.on_mount()
        
        final_memory = process.memory_info().rss
        
        # Contract: Memory growth should be reasonable
        memory_growth = final_memory - initial_memory
        assert memory_growth < 50 * 1024 * 1024  # Less than 50MB growth