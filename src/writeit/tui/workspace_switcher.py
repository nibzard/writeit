"""Workspace Switcher TUI Component.

Provides a rich terminal interface for managing and switching between workspaces.
Integrates with the Workspace Application Service for comprehensive workspace management
with creation, deletion, backup, and analytics capabilities.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    Input,
    Select,
    Tabs,
    Tab,
    TabPane,
    DataTable,
    Markdown,
    Switch,
    Log,
)
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.message import Message
from textual.timer import Timer

from ..application.services.workspace_application_service import (
    WorkspaceApplicationService,
    WorkspaceCreationRequest,
    WorkspaceListingOptions,
    WorkspaceInitializationMode,
)
from ..shared.dependencies.container import Container as DIContainer


@dataclass
class WorkspaceSwitcherConfig:
    """Configuration for the workspace switcher TUI."""
    auto_refresh_interval: int = 30  # seconds
    max_log_entries: int = 1000
    show_analytics: bool = True
    enable_animations: bool = True


class WorkspaceAction(str, Enum):
    """Workspace actions available in the TUI."""
    SWITCH = "switch"
    CREATE = "create"
    DELETE = "delete"
    BACKUP = "backup"
    INFO = "info"


@dataclass
class WorkspaceInfo:
    """Workspace information for display."""
    name: str
    path: str
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime]
    pipeline_count: int
    template_count: int
    size_mb: float
    health_status: str


class WorkspaceSelected(Message):
    """Message emitted when a workspace is selected."""
    def __init__(self, workspace_name: str) -> None:
        self.workspace_name = workspace_name
        super().__init__()


class WorkspaceCreated(Message):
    """Message emitted when a workspace is created."""
    def __init__(self, workspace_name: str) -> None:
        self.workspace_name = workspace_name
        super().__init__()


class WorkspaceDeleted(Message):
    """Message emitted when a workspace is deleted."""
    def __init__(self, workspace_name: str) -> None:
        self.workspace_name = workspace_name
        super().__init__()


class CreateWorkspaceModal(ModalScreen):
    """Modal screen for creating a new workspace."""
    
    def __init__(self) -> None:
        super().__init__()
        self.workspace_name_input = Input(placeholder="Enter workspace name")
        self.description_input = Input(placeholder="Enter description (optional)")
        self.init_mode_select = Select(
            options=[
                ("Minimal (basic structure)", WorkspaceInitializationMode.MINIMAL),
                ("Standard (with templates)", WorkspaceInitializationMode.STANDARD),
                ("Full (with samples)", WorkspaceInitializationMode.FULL),
            ],
            value=WorkspaceInitializationMode.STANDARD
        )
        self.copy_from_select = Select(options=[("None", None)])
        self.include_samples_switch = Switch(value=True)
        
    def compose(self) -> ComposeResult:
        with Container(id="create-workspace-modal"):
            yield Static("Create New Workspace", classes="modal-title")
            yield Vertical(
                Static("Workspace Name:"),
                self.workspace_name_input,
                Static("Description:"),
                self.description_input,
                Static("Initialization Mode:"),
                self.init_mode_select,
                Static("Copy from existing workspace:"),
                self.copy_from_select,
                Horizontal(
                    Static("Include samples:"),
                    self.include_samples_switch
                ),
                Horizontal(
                    Button("Create", id="create-btn", variant="primary"),
                    Button("Cancel", id="cancel-btn")
                )
            )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            self.dismiss({
                "name": self.workspace_name_input.value,
                "description": self.description_input.value or None,
                "initialization_mode": self.init_mode_select.value,
                "copy_from_workspace": self.copy_from_select.value,
                "include_sample_templates": self.include_samples_switch.value,
                "include_sample_styles": self.include_samples_switch.value,
            })
        else:
            self.dismiss(None)


class WorkspaceInfoModal(ModalScreen):
    """Modal screen for displaying workspace information."""
    
    def __init__(self, workspace_info: Dict[str, Any]) -> None:
        super().__init__()
        self.workspace_info = workspace_info
        
    def compose(self) -> ComposeResult:
        with Container(id="workspace-info-modal"):
            yield Static(f"Workspace: {self.workspace_info['name']}", classes="modal-title")
            with ScrollableContainer():
                yield Markdown(f"""
## Workspace Details

**Name:** {self.workspace_info['name']}  
**Path:** {self.workspace_info['path']}  
**Status:** {'Active' if self.workspace_info['is_active'] else 'Inactive'}  
**Created:** {self.workspace_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}  
**Last Used:** {self.workspace_info['last_used'].strftime('%Y-%m-%d %H:%M:%S') if self.workspace_info['last_used'] else 'Never'}

## Statistics

**Pipelines:** {self.workspace_info['pipeline_count']}  
**Templates:** {self.workspace_info['template_count']}  
**Size:** {self.workspace_info['size_mb']:.2f} MB  
**Health:** {self.workspace_info['health_status']}
                """)
            yield Button("Close", id="close-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


class WorkspaceSwitcherApp(App):
    """Main workspace switcher application."""
    
    CSS_PATH = "workspace_switcher.css"
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("ctrl+n", "create_workspace", "New Workspace"),
        Binding("ctrl+d", "delete_workspace", "Delete Workspace"),
        Binding("ctrl+i", "show_info", "Show Info"),
        Binding("ctrl+s", "switch_workspace", "Switch Workspace"),
        Binding("up", "select_previous", "Previous"),
        Binding("down", "select_next", "Next"),
    ]
    
    workspaces: reactive[List[WorkspaceInfo]] = reactive([])
    selected_workspace: reactive[Optional[str]] = reactive(None)
    log_entries: reactive[List[str]] = reactive([])
    is_loading: reactive[bool] = reactive(False)
    
    def __init__(
        self, 
        workspace_service: WorkspaceApplicationService,
        config: WorkspaceSwitcherConfig
    ) -> None:
        super().__init__()
        self.workspace_service = workspace_service
        self.config = config
        self.refresh_timer: Optional[Timer] = None
        
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Workspace Switcher", classes="title"),
            Horizontal(
                Vertical(
                    Static("Workspaces", classes="section-title"),
                    DataTable(id="workspace-table", classes="workspace-table"),
                    Horizontal(
                        Button("Refresh", id="refresh-btn", variant="default"),
                        Button("New", id="new-btn", variant="primary"),
                        Button("Switch", id="switch-btn", variant="success"),
                        Button("Delete", id="delete-btn", variant="error"),
                        Button("Info", id="info-btn", variant="default"),
                    ),
                    classes="workspace-panel"
                ),
                Vertical(
                    Tabs(
                        Tab("Activity Log", id="log-tab"),
                        Tab("Analytics", id="analytics-tab"),
                    ),
                    TabPane("Activity Log", id="log-pane"),
                    TabPane("Analytics", id="analytics-pane"),
                    classes="info-panel"
                ),
                classes="main-content"
            ),
            classes="app-container"
        )
        yield Footer()
        
    async def on_mount(self) -> None:
        """Initialize the application."""
        self.setup_workspace_table()
        await self.refresh_workspaces()
        self.start_auto_refresh()
        
    def setup_workspace_table(self) -> None:
        """Set up the workspace data table."""
        table = self.query_one("#workspace-table", DataTable)
        table.add_columns("Name", "Status", "Last Used", "Pipelines", "Size (MB)")
        table.cursor_type = "row"
        
    async def refresh_workspaces(self) -> None:
        """Refresh the workspace list."""
        self.is_loading = True
        try:
            options = WorkspaceListingOptions(
                include_inactive=True,
                include_analytics=True
            )
            workspace_list = await self.workspace_service.list_workspaces(options)
            
            self.workspaces = [
                WorkspaceInfo(
                    name=ws.name,
                    path=ws.path,
                    is_active=ws.is_active,
                    created_at=ws.created_at,
                    last_used=ws.last_used,
                    pipeline_count=ws.analytics.pipeline_count if ws.analytics else 0,
                    template_count=ws.analytics.template_count if ws.analytics else 0,
                    size_mb=ws.analytics.size_mb if ws.analytics else 0.0,
                    health_status=ws.analytics.health_status if ws.analytics else "Unknown"
                )
                for ws in workspace_list.workspaces
            ]
            
            await self.update_workspace_table()
            self.add_log_entry("Workspaces refreshed")
            
        except Exception as e:
            self.add_log_entry(f"Error refreshing workspaces: {str(e)}")
        finally:
            self.is_loading = False
            
    async def update_workspace_table(self) -> None:
        """Update the workspace table with current data."""
        table = self.query_one("#workspace-table", DataTable)
        table.clear()
        
        for workspace in self.workspaces:
            last_used = workspace.last_used.strftime("%Y-%m-%d") if workspace.last_used else "Never"
            status = "Active" if workspace.is_active else "Inactive"
            
            table.add_row(
                workspace.name,
                status,
                last_used,
                str(workspace.pipeline_count),
                f"{workspace.size_mb:.1f}",
                key=workspace.name
            )
            
    def add_log_entry(self, message: str) -> None:
        """Add an entry to the activity log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_entries.append(log_entry)
        
        # Keep only the most recent entries
        if len(self.log_entries) > self.config.max_log_entries:
            self.log_entries = self.log_entries[-self.config.max_log_entries :]
            
        self.update_log_display()
        
    def update_log_display(self) -> None:
        """Update the activity log display."""
        try:
            # Create a new Log widget with the current entries
            log_pane = self.query_one("#log-pane")
            log_pane.remove_children()
            log_widget = Log()
            log_pane.mount(log_widget)
            for entry in self.log_entries:
                log_widget.write_line(entry)
        except Exception:
            # Log widget might not be available yet
            pass
            
    def start_auto_refresh(self) -> None:
        """Start the auto-refresh timer."""
        if self.config.auto_refresh_interval > 0:
            self.refresh_timer = self.set_interval(
                self.config.auto_refresh_interval,
                lambda: asyncio.create_task(self.refresh_workspaces())
            )
            
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle workspace row selection."""
        table = self.query_one("#workspace-table", DataTable)
        if event.data_table == table:
            self.selected_workspace = event.row_key.value if event.row_key else None
            self.add_log_entry(f"Selected workspace: {self.selected_workspace}")
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "refresh-btn":
            asyncio.create_task(self.refresh_workspaces())
        elif button_id == "new-btn":
            asyncio.create_task(self.show_create_workspace_modal())
        elif button_id == "switch-btn" and self.selected_workspace:
            asyncio.create_task(self.switch_to_workspace())
        elif button_id == "delete-btn" and self.selected_workspace:
            asyncio.create_task(self.delete_selected_workspace())
        elif button_id == "info-btn" and self.selected_workspace:
            asyncio.create_task(self.show_workspace_info())
            
    async def show_create_workspace_modal(self) -> None:
        """Show the create workspace modal."""
        modal = CreateWorkspaceModal()
        
        # Populate copy_from options
        copy_from_select = modal.copy_from_select
        options = [("None", None)] + [(ws.name, ws.name) for ws in self.workspaces]
        copy_from_select.set_options([(opt[0], None) for opt in options])
        
        result = await self.push_screen_wait(modal)
        if result:
            await self.create_workspace(result)
            
    async def create_workspace(self, workspace_data: Dict[str, Any]) -> None:
        """Create a new workspace."""
        try:
            request = WorkspaceCreationRequest(**workspace_data)
            workspace = await self.workspace_service.create_workspace(request)
            
            self.add_log_entry(f"Created workspace: {workspace.name}")
            await self.refresh_workspaces()
            
            self.post_message(WorkspaceCreated(workspace.name))
            await self.update_workspace_table()
            
        except Exception as e:
            self.add_log_entry(f"Error creating workspace: {str(e)}")
            
    async def switch_to_workspace(self) -> None:
        """Switch to the selected workspace."""
        if not self.selected_workspace:
            return
            
        try:
            workspace = await self.workspace_service.switch_workspace(self.selected_workspace)
            self.add_log_entry(f"Switched to workspace: {workspace.name}")
            await self.refresh_workspaces()
            
            self.post_message(WorkspaceSelected(workspace.name))
            await self.update_workspace_table()
            
        except Exception as e:
            self.add_log_entry(f"Error switching workspace: {str(e)}")
            
    async def delete_selected_workspace(self) -> None:
        """Delete the selected workspace."""
        if not self.selected_workspace:
            return
            
        try:
            await self.workspace_service.delete_workspace(self.selected_workspace)
            self.add_log_entry(f"Deleted workspace: {self.selected_workspace}")
            await self.refresh_workspaces()
            
            self.post_message(WorkspaceDeleted(self.selected_workspace))
            self.selected_workspace = None
            await self.update_workspace_table()
            
        except Exception as e:
            self.add_log_entry(f"Error deleting workspace: {str(e)}")
            
    async def show_workspace_info(self) -> None:
        """Show detailed information about the selected workspace."""
        if not self.selected_workspace:
            return
            
        try:
            workspace_info = await self.workspace_service.get_workspace_info(self.selected_workspace)
            
            modal = WorkspaceInfoModal(workspace_info)
            await self.push_screen(modal)
            
        except Exception as e:
            self.add_log_entry(f"Error getting workspace info: {str(e)}")
            
    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
        
    def action_refresh(self) -> None:
        """Refresh the workspace list."""
        asyncio.create_task(self.refresh_workspaces())
        
    def action_create_workspace(self) -> None:
        """Create a new workspace."""
        asyncio.create_task(self.show_create_workspace_modal())
        
    def action_delete_workspace(self) -> None:
        """Delete the selected workspace."""
        if self.selected_workspace:
            asyncio.create_task(self.delete_selected_workspace())
            
    def action_show_info(self) -> None:
        """Show workspace information."""
        if self.selected_workspace:
            asyncio.create_task(self.show_workspace_info())
            
    def action_switch_workspace(self) -> None:
        """Switch to the selected workspace."""
        if self.selected_workspace:
            asyncio.create_task(self.switch_to_workspace())
            
    def action_select_previous(self) -> None:
        """Select the previous workspace in the table."""
        table = self.query_one("#workspace-table", DataTable)
        table.action_cursor_up()
        
    def action_select_next(self) -> None:
        """Select the next workspace in the table."""
        table = self.query_one("#workspace-table", DataTable)
        table.action_cursor_down()


async def run_workspace_switcher(
    config: Optional[WorkspaceSwitcherConfig] = None
) -> None:
    """Run the workspace switcher TUI application."""
    if config is None:
        config = WorkspaceSwitcherConfig()
    
    # Initialize dependency container
    container = DIContainer()
    
    # Get workspace service
    workspace_service = container.resolve(WorkspaceApplicationService)
    
    # Create and run the app
    app = WorkspaceSwitcherApp(workspace_service, config)
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(run_workspace_switcher())