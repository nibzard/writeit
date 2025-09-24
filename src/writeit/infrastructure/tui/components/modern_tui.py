"""Modern TUI Components for WriteIt with DDD Integration.

Provides modern, feature-rich TUI components that integrate with the new
DDD architecture, offering real-time updates, workspace management,
and comprehensive pipeline execution interface.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
from pathlib import Path
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    TextArea,
    Select,
    ProgressBar,
    Input,
    Tabs,
    Tab,
    TabPane,
    DataTable,
    Tree,
    Log,
    Switch,
    Checkbox,
    RadioButton,
    RadioSet,
    Label,
    Markdown,
)
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import Screen
from textual.message import Message
from textual.timer import Timer
import asyncio

from ..context import (
    TUIContext,
    TUIContextManager,
    TUIMode,
    NavigationState,
    get_current_tui_context,
    require_tui_context,
)
from ..event_handler import TUIEventHandler
from ..state_manager import TUIStateManager
from ..error_handler import TUIErrorHandler

from ....application.services.pipeline_application_service import (
    PipelineApplicationService,
    PipelineExecutionRequest,
    PipelineExecutionResult,
    PipelineExecutionMode,
    PipelineSource,
)
from ....application.services.workspace_application_service import (
    WorkspaceApplicationService,
)
from ....application.services.content_application_service import (
    ContentApplicationService,
)

from ....domains.workspace.value_objects import WorkspaceName
from ....domains.pipeline.value_objects import PipelineId
from ....domains.pipeline.value_objects.execution_status import ExecutionStatus, StepExecutionStatus
from ....shared.dependencies.container import Container


class TUIComponentMessage(Message):
    """Base message for TUI component communication."""
    
    def __init__(self, component_id: str, data: Dict[str, Any] = None) -> None:
        self.component_id = component_id
        self.data = data or {}
        super().__init__()


class PipelineExecutionStarted(TUIComponentMessage):
    """Message indicating pipeline execution started."""
    pass


class PipelineExecutionProgress(TUIComponentMessage):
    """Message indicating pipeline execution progress."""
    pass


class PipelineExecutionCompleted(TUIComponentMessage):
    """Message indicating pipeline execution completed."""
    pass


class WorkspaceSwitched(TUIComponentMessage):
    """Message indicating workspace was switched."""
    pass


class TemplateSelected(TUIComponentMessage):
    """Message indicating template was selected."""
    pass


@dataclass
class PipelineTemplateInfo:
    """Information about a pipeline template for TUI display."""
    
    id: str
    name: str
    description: str
    source: PipelineSource
    workspace_name: str
    created_at: datetime
    updated_at: datetime
    steps_count: int
    estimated_duration: Optional[int] = None  # in seconds
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineInputData:
    """Pipeline input data for TUI form."""
    
    key: str
    type: str
    label: str
    required: bool = False
    default: Any = None
    placeholder: str = ""
    help_text: str = ""
    options: List[Dict[str, str]] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    max_length: Optional[int] = None


@dataclass
class PipelineStepData:
    """Pipeline step data for TUI display."""
    
    key: str
    name: str
    description: str
    type: str
    status: ExecutionStatus = ExecutionStatus.step_pending()
    progress: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    error_message: Optional[str] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    response_preview: Optional[str] = None


class ModernPipelineRunnerScreen(Screen):
    """Modern pipeline runner screen with DDD integration."""
    
    CSS = """
    .pipeline-runner {
        height: 100%;
        layout: grid;
        grid-size: 1 1;
        grid-columns: 1fr;
        grid-rows: 1fr;
    }
    
    .header-section {
        height: auto;
        dock: top;
        padding: 1;
        background: $surface;
        border: solid $primary;
    }
    
    .content-section {
        height: 1fr;
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 2fr;
        grid-rows: 1fr;
    }
    
    .sidebar {
        grid-column: 1;
        grid-row: 1;
        background: $surface;
        border: solid $accent;
        padding: 1;
    }
    
    .main-area {
        grid-column: 2;
        grid-row: 1;
        padding: 1;
    }
    
    .workspace-info {
        background: $surface;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .template-list {
        height: 20;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    .input-form {
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }
    
    .execution-area {
        border: solid $accent;
        padding: 1;
    }
    
    .progress-bar {
        height: 1;
        margin: 1 0;
    }
    
    .step-list {
        height: 15;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .output-area {
        height: 20;
        border: solid $accent;
    }
    
    .action-buttons {
        height: auto;
        margin: 1 0;
    }
    
    .action-buttons Button {
        margin: 0 1;
    }
    
    .error-message {
        background: $error;
        color: $text;
        padding: 1;
        border: solid $error;
        margin: 1 0;
    }
    
    .success-message {
        background: $success;
        color: $text;
        padding: 1;
        border: solid $success;
        margin: 1 0;
    }
    """
    
    def __init__(self, context: TUIContext):
        super().__init__()
        self.context = context
        self.pipeline_service: Optional[PipelineApplicationService] = None
        self.workspace_service: Optional[WorkspaceApplicationService] = None
        self.content_service: Optional[ContentApplicationService] = None
        
        # UI state
        self.selected_template: Optional[PipelineTemplateInfo] = None
        self.pipeline_inputs: Dict[str, Any] = {}
        self.execution_steps: List[PipelineStepData] = []
        self.current_execution_id: Optional[str] = None
        self.execution_task: Optional[asyncio.Task] = None
        
        # Bind services from container
        if context.container:
            self.pipeline_service = context.container.resolve(PipelineApplicationService)
            self.workspace_service = context.container.resolve(WorkspaceApplicationService)
            self.content_service = context.container.resolve(ContentApplicationService)
    
    def compose(self) -> ComposeResult:
        """Create the pipeline runner layout."""
        
        with Container(classes="pipeline-runner"):
            # Header section
            with Container(classes="header-section"):
                yield Static("🚀 Modern Pipeline Runner", classes="title")
                yield Static(f"Workspace: {self.context.workspace_name}", classes="workspace-name")
                yield Static(f"Session: {self.context.session_id[:8]}...", classes="session-id")
            
            # Main content area
            with Container(classes="content-section"):
                # Sidebar
                with Container(classes="sidebar"):
                    # Workspace info
                    with Container(classes="workspace-info"):
                        yield Static("📁 Current Workspace", classes="section-header")
                        yield Static(f"Name: {self.context.workspace_name}")
                        yield Static("Status: Active")
                        yield Button("Switch Workspace", id="switch-workspace", variant="default")
                    
                    # Template browser
                    yield Static("📋 Pipeline Templates", classes="section-header")
                    with Container(classes="template-list"):
                        yield DataTable(id="template-table")
                    
                    # Actions
                    with Horizontal(classes="action-buttons"):
                        yield Button("Refresh", id="refresh-templates", variant="primary")
                        yield Button("New Template", id="new-template", variant="success")
                
                # Main area
                with Container(classes="main-area"):
                    # Dynamic content area (changes based on state)
                    with Container(id="dynamic-content"):
                        yield Static("Select a pipeline template to begin", classes="placeholder")
    
    async def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        await self.load_templates()
        self.setup_template_table()
    
    def setup_template_table(self) -> None:
        """Set up the template data table."""
        table = self.query_one("#template-table", DataTable)
        table.clear(columns=True)
        
        # Add columns
        table.add_column("Name", key="name")
        table.add_column("Source", key="source")
        table.add_column("Steps", key="steps")
        table.add_column("Workspace", key="workspace")
        
        # Make table clickable
        table.cursor_type = "row"
    
    async def load_templates(self) -> None:
        """Load pipeline templates from all sources."""
        if not self.pipeline_service:
            return
        
        try:
            # Get templates from current workspace
            workspace_name = WorkspaceName(self.context.workspace_name)
            templates = await self.pipeline_service.list_pipeline_templates(workspace_name)
            
            # Update table with templates
            table = self.query_one("#template-table", DataTable)
            table.clear()
            
            for template in templates:
                table.add_row(
                    template.name,
                    template.source.value,
                    str(template.steps_count),
                    template.workspace_name,
                    key=template.id
                )
                
        except Exception as e:
            await self.show_error(f"Failed to load templates: {e}")
    
    async def show_error(self, message: str) -> None:
        """Show an error message."""
        dynamic_content = self.query_one("#dynamic-content")
        await dynamic_content.remove_children()
        await dynamic_content.mount(Static(message, classes="error-message"))
    
    async def show_success(self, message: str) -> None:
        """Show a success message."""
        dynamic_content = self.query_one("#dynamic-content")
        await dynamic_content.remove_children()
        await dynamic_content.mount(Static(message, classes="success-message"))
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle template selection."""
        template_id = event.row_key.value if event.row_key else None
        if template_id:
            await self.select_template(template_id)
    
    async def select_template(self, template_id: str) -> None:
        """Select and display a template."""
        if not self.pipeline_service:
            return
        
        try:
            # Get template details
            workspace_name = WorkspaceName(self.context.workspace_name)
            template = await self.pipeline_service.get_pipeline_template(
                workspace_name, PipelineId(template_id)
            )
            
            if template:
                self.selected_template = template
                await self.show_template_inputs(template)
                
        except Exception as e:
            await self.show_error(f"Failed to load template: {e}")
    
    async def show_template_inputs(self, template: PipelineTemplateInfo) -> None:
        """Show template input form."""
        dynamic_content = self.query_one("#dynamic-content")
        await dynamic_content.remove_children()
        
        with Container(classes="input-form"):
            yield Static(f"📝 {template.name} - Inputs", classes="section-header")
            yield Static(template.description, classes="template-description")
            
            # Show template metadata
            metadata_text = (
                f"Source: {template.source.value} | "
                f"Steps: {template.steps_count} | "
                f"Created: {template.created_at.strftime('%Y-%m-%d')}"
            )
            yield Static(metadata_text, classes="template-metadata")
            
            # Load and display input fields (would need to be implemented)
            yield Static("Input fields would be rendered here based on template configuration")
            
            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("Back to Templates", id="back-to-templates", variant="default")
                yield Button("Execute Pipeline", id="execute-pipeline", variant="success", disabled=True)
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "switch-workspace":
            await self.switch_workspace()
        elif event.button.id == "refresh-templates":
            await self.load_templates()
        elif event.button.id == "new-template":
            await self.create_new_template()
        elif event.button.id == "back-to-templates":
            await self.back_to_templates()
        elif event.button.id == "execute-pipeline":
            await self.execute_pipeline()
    
    async def switch_workspace(self) -> None:
        """Switch to a different workspace."""
        # This would open a workspace selection dialog
        await self.show_error("Workspace switching not yet implemented")
    
    async def create_new_template(self) -> None:
        """Create a new pipeline template."""
        # This would open a template creation dialog
        await self.show_error("Template creation not yet implemented")
    
    async def back_to_templates(self) -> None:
        """Go back to template selection."""
        dynamic_content = self.query_one("#dynamic-content")
        await dynamic_content.remove_children()
        yield Static("Select a pipeline template to begin", classes="placeholder")
    
    async def execute_pipeline(self) -> None:
        """Execute the selected pipeline."""
        if not self.selected_template or not self.pipeline_service:
            return
        
        try:
            # Create execution request
            workspace_name = WorkspaceName(self.context.workspace_name)
            request = PipelineExecutionRequest(
                pipeline_id=PipelineId(self.selected_template.id),
                workspace_name=workspace_name,
                execution_mode=PipelineExecutionMode.TUI,
                inputs=self.pipeline_inputs,
            )
            
            # Start execution
            self.current_execution_id = str(uuid.uuid4())
            await self.show_execution_screen()
            
            # Execute pipeline in background
            self.execution_task = asyncio.create_task(self._execute_pipeline_worker(request))
            
        except Exception as e:
            await self.show_error(f"Failed to start pipeline: {e}")
    
    async def _execute_pipeline_worker(self, request: PipelineExecutionRequest) -> PipelineExecutionResult:
        """Async task method for pipeline execution."""
        if not self.pipeline_service:
            raise RuntimeError("Pipeline service not available")
        
        # Execute pipeline with streaming updates
        response = await self.pipeline_service.execute_pipeline_streaming(request)
        return response
    
    async def show_execution_screen(self) -> None:
        """Show the pipeline execution screen."""
        dynamic_content = self.query_one("#dynamic-content")
        await dynamic_content.remove_children()
        
        with Container(classes="execution-area"):
            yield Static("⚡ Pipeline Execution", classes="section-header")
            yield Static(f"Template: {self.selected_template.name}")
            yield Static(f"Execution ID: {self.current_execution_id}")
            
            # Progress bar
            yield ProgressBar(id="execution-progress", classes="progress-bar")
            
            # Step list
            yield Static("📋 Execution Steps", classes="section-header")
            with Container(classes="step-list"):
                yield DataTable(id="step-table")
            
            # Output area
            yield Static("📤 Execution Output", classes="section-header")
            with Container(classes="output-area"):
                yield Log(id="execution-log")
            
            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("Pause", id="pause-execution", variant="warning")
                yield Button("Stop", id="stop-execution", variant="error")
                yield Button("View Results", id="view-results", variant="primary", disabled=True)


class ModernWriteItTUI(App):
    """Modern WriteIt TUI application with DDD integration."""
    
    CSS = """
    .main-container {
        height: 100%;
        layout: grid;
        grid-size: 1 1;
        grid-columns: 1fr;
        grid-rows: auto 1fr auto;
    }
    
    .header {
        grid-row: 1;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .content {
        grid-row: 2;
        height: 1fr;
        padding: 1;
    }
    
    .footer {
        grid-row: 3;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .title {
        text-style: bold;
        color: $accent;
        text-align: center;
    }
    
    .status-bar {
        text-align: right;
        color: $text-muted;
    }
    
    .navigation-tabs {
        height: auto;
        margin: 1 0;
    }
    
    .error-message {
        background: $error;
        color: $text;
        padding: 1;
        border: solid $error;
        margin: 1 0;
    }
    
    .success-message {
        background: $success;
        color: $text;
        padding: 1;
        border: solid $success;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+q", "quit", "Quit"),
        Binding("f1", "show_help", "Help"),
        Binding("ctrl+t", "show_templates", "Templates"),
        Binding("ctrl+w", "show_workspaces", "Workspaces"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("ctrl+s", "show_settings", "Settings"),
    ]
    
    def __init__(self, container: Container, workspace_name: str = "default"):
        super().__init__()
        self.container = container
        self.workspace_name = workspace_name
        
        # Initialize TUI context
        self.context = TUIContext(
            workspace_name=workspace_name,
            container=container,
            mode=TUIMode.PIPELINE,
            navigation_state=NavigationState.HOME,
        )
        
        # Initialize services
        self.pipeline_service = container.resolve(PipelineApplicationService)
        self.workspace_service = container.resolve(WorkspaceApplicationService)
        self.content_service = container.resolve(ContentApplicationService)
        
        # Set up TUI context
        TUIContextManager.set_context(self.context)
    
    def compose(self) -> ComposeResult:
        """Create the main application layout."""
        
        with Container(classes="main-container"):
            # Header
            with Container(classes="header"):
                yield Static("🚀 WriteIt - Modern TUI", classes="title")
                yield Static(f"Workspace: {self.workspace_name}", classes="status-bar")
            
            # Content area with tabs
            with Container(classes="content"):
                with Tabs(id="main-tabs"):
                    yield Tab("Pipeline Runner", id="pipeline-tab")
                    yield Tab("Templates", id="templates-tab")
                    yield Tab("Workspaces", id="workspaces-tab")
                    yield Tab("Settings", id="settings-tab")
                
                with TabPane("Pipeline Runner", id="pipeline-pane"):
                    yield ModernPipelineRunnerScreen(self.context)
                
                with TabPane("Templates", id="templates-pane"):
                    yield Static("Template management coming soon...")
                
                with TabPane("Workspaces", id="workspaces-pane"):
                    yield Static("Workspace management coming soon...")
                
                with TabPane("Settings", id="settings-pane"):
                    yield Static("Settings coming soon...")
            
            # Footer
            with Container(classes="footer"):
                yield Static("Press F1 for help | Ctrl+C to quit", classes="status-bar")
    
    async def on_mount(self) -> None:
        """Initialize the application when mounted."""
        # Set up main tabs
        tabs = self.query_one("#main-tabs", Tabs)
        tabs.active = "pipeline-tab"
    
    async def on_tabs_tab_activated(self, event: Tabs.TabActivated) -> None:
        """Handle tab activation."""
        tab_id = event.tab.id
        
        if tab_id == "pipeline-tab":
            self.context.mode = TUIMode.PIPELINE
            self.context.navigation_state = NavigationState.HOME
        elif tab_id == "templates-tab":
            self.context.mode = TUIMode.TEMPLATE
            self.context.navigation_state = NavigationState.HOME
        elif tab_id == "workspaces-tab":
            self.context.mode = TUIMode.WORKSPACE
            self.context.navigation_state = NavigationState.HOME
        elif tab_id == "settings-tab":
            self.context.mode = TUIMode.CONFIGURATION
            self.context.navigation_state = NavigationState.SETTINGS
    
    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
# WriteIt Modern TUI Help

## Keyboard Shortcuts:
- **Ctrl+C/Q**: Quit application
- **F1**: Show this help
- **Ctrl+T**: Go to Templates
- **Ctrl+W**: Go to Workspaces
- **Ctrl+R**: Refresh current view
- **Ctrl+S**: Go to Settings

## Features:
- **Pipeline Runner**: Execute pipelines with real-time updates
- **Template Management**: Browse and create pipeline templates
- **Workspace Management**: Switch between workspaces
- **Settings**: Configure application preferences

## Tips:
- Use the tab navigation to switch between sections
- Pipeline execution shows real-time progress and logs
- Templates can be selected from multiple sources (local, workspace, global)
- Workspaces provide isolated environments for your projects
"""
        
        self.push_screen("help", lambda: Markdown(help_text))
    
    def action_show_templates(self) -> None:
        """Switch to templates tab."""
        tabs = self.query_one("#main-tabs", Tabs)
        tabs.active = "templates-tab"
    
    def action_show_workspaces(self) -> None:
        """Switch to workspaces tab."""
        tabs = self.query_one("#main-tabs", Tabs)
        tabs.active = "workspaces-tab"
    
    def action_show_settings(self) -> None:
        """Switch to settings tab."""
        tabs = self.query_one("#main-tabs", Tabs)
        tabs.active = "settings-tab"
    
    def action_refresh(self) -> None:
        """Refresh current view."""
        # This would refresh the current active tab
        pass


async def run_modern_tui(container: Container, workspace_name: str = "default") -> None:
    """Run the modern WriteIt TUI application."""
    app = ModernWriteItTUI(container, workspace_name)
    await app.run_async()