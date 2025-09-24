"""Specialized TUI Components for WriteIt.

Provides specialized components for workspace management, template browsing,
configuration interface, and pipeline execution with DDD integration.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from pathlib import Path
from datetime import datetime

from textual.app import ComposeResult
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
    ListItem,
    ListView,
)
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import Screen
from textual.message import Message
from textual.timer import Timer
import asyncio

from ..context import (
    TUIContext,
    TUIMode,
    NavigationState,
    require_tui_context,
)
from .modern_tui import (
    TUIComponentMessage,
    PipelineTemplateInfo,
    PipelineInputData,
    PipelineStepData,
)

from ....application.services.workspace_application_service import (
    WorkspaceApplicationService,
)
from ....application.services.content_application_service import (
    ContentApplicationService,
)
from ....application.services.pipeline_application_service import (
    PipelineApplicationService,
)

from ....domains.workspace.value_objects import WorkspaceName
from ....domains.pipeline.value_objects import PipelineId
from ....domains.pipeline.value_objects.execution_status import ExecutionStatus
from ....shared.dependencies.container import Container


class WorkspaceManagementScreen(Screen):
    """Workspace management screen with full CRUD operations."""
    
    CSS = """
    .workspace-management {
        height: 100%;
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 2fr;
        grid-rows: 1fr;
    }
    
    .workspace-list {
        grid-column: 1;
        grid-row: 1;
        padding: 1;
        border: solid $primary;
    }
    
    .workspace-details {
        grid-column: 2;
        grid-row: 1;
        padding: 1;
    }
    
    .workspace-info {
        background: $surface;
        padding: 1;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    .workspace-actions {
        margin: 1 0;
    }
    
    .workspace-form {
        background: $surface;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .workspace-stats {
        background: $surface;
        padding: 1;
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
        self.workspace_service: Optional[WorkspaceApplicationService] = None
        self.selected_workspace: Optional[str] = None
        self.edit_mode: bool = False
        
        if context.container:
            self.workspace_service = context.container.resolve(WorkspaceApplicationService)
    
    def compose(self) -> ComposeResult:
        """Create the workspace management layout."""
        
        with Container(classes="workspace-management"):
            # Workspace list
            with Container(classes="workspace-list"):
                yield Static("📁 Workspaces", classes="section-header")
                yield ListView(id="workspace-list-view", classes="workspace-list")
                
                with Horizontal(classes="action-buttons"):
                    yield Button("Create New", id="create-workspace", variant="success")
                    yield Button("Refresh", id="refresh-workspaces", variant="primary")
            
            # Workspace details
            with Container(classes="workspace-details"):
                yield Static("📋 Workspace Details", classes="section-header")
                
                with Container(id="workspace-info", classes="workspace-info"):
                    yield Static("Select a workspace to view details")
                
                with Container(id="workspace-form", classes="workspace-form"):
                    yield Static("Workspace actions will appear here")
                
                with Container(id="workspace-stats", classes="workspace-stats"):
                    yield Static("Workspace statistics will appear here")
    
    async def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        await self.load_workspaces()
    
    async def load_workspaces(self) -> None:
        """Load all workspaces."""
        if not self.workspace_service:
            return
        
        try:
            workspaces = await self.workspace_service.list_workspaces()
            
            list_view = self.query_one("#workspace-list-view", ListView)
            await list_view.clear()
            
            for workspace in workspaces:
                item = ListItem(
                    Static(f"{workspace.name} ({workspace.path})"),
                    id=f"workspace-{workspace.name}"
                )
                await list_view.append(item)
                
        except Exception as e:
            await self.show_error(f"Failed to load workspaces: {e}")
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle workspace selection."""
        if event.list_view.id == "workspace-list-view":
            workspace_name = event.item.id.replace("workspace-", "")
            await self.select_workspace(workspace_name)
    
    async def select_workspace(self, workspace_name: str) -> None:
        """Select and display workspace details."""
        if not self.workspace_service:
            return
        
        try:
            self.selected_workspace = workspace_name
            
            # Get workspace details
            workspace = await self.workspace_service.get_workspace(WorkspaceName(workspace_name))
            
            if workspace:
                await self.show_workspace_details(workspace)
                
        except Exception as e:
            await self.show_error(f"Failed to load workspace: {e}")
    
    async def show_workspace_details(self, workspace_name: str) -> None:
        """Show workspace details and actions."""
        info_container = self.query_one("#workspace-info")
        await info_container.remove_children()
        
        await info_container.mount(Static(f"Workspace: {workspace_name}"))
        await info_container.mount(Static(f"Path: ~/.writeit/workspaces/{workspace_name}"))
        await info_container.mount(Static("Status: Active"))
        
        # Show workspace actions
        form_container = self.query_one("#workspace-form")
        await form_container.remove_children()
        
        await form_container.mount(Static("🔧 Workspace Actions", classes="section-header"))
        
        with Horizontal(classes="action-buttons"):
            yield Button("Switch to", id="switch-to-workspace", variant="success")
            yield Button("Edit", id="edit-workspace", variant="primary")
            yield Button("Backup", id="backup-workspace", variant="warning")
            yield Button("Delete", id="delete-workspace", variant="error")
        
        # Show workspace statistics
        stats_container = self.query_one("#workspace-stats")
        await stats_container.remove_children()
        
        await stats_container.mount(Static("📊 Workspace Statistics", classes="section-header"))
        await stats_container.mount(Static("Pipelines: 0"))
        await stats_container.mount(Static("Templates: 0"))
        await stats_container.mount(Static("Storage Used: 0 MB"))
        await stats_container.mount(Static("Last Activity: Never"))
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "create-workspace":
            await self.create_workspace()
        elif event.button.id == "refresh-workspaces":
            await self.load_workspaces()
        elif event.button.id == "switch-to-workspace":
            await self.switch_to_workspace()
        elif event.button.id == "edit-workspace":
            await self.edit_workspace()
        elif event.button.id == "backup-workspace":
            await self.backup_workspace()
        elif event.button.id == "delete-workspace":
            await self.delete_workspace()
    
    async def create_workspace(self) -> None:
        """Create a new workspace."""
        # This would open a workspace creation dialog
        await self.show_error("Workspace creation not yet implemented")
    
    async def switch_to_workspace(self) -> None:
        """Switch to the selected workspace."""
        if self.selected_workspace:
            # Update context and switch workspace
            self.context.workspace_name = self.selected_workspace
            await self.show_success(f"Switched to workspace: {self.selected_workspace}")
            
            # This would also trigger a workspace switch in the backend
            if self.workspace_service:
                await self.workspace_service.switch_workspace(WorkspaceName(self.selected_workspace))
    
    async def edit_workspace(self) -> None:
        """Edit the selected workspace."""
        await self.show_error("Workspace editing not yet implemented")
    
    async def backup_workspace(self) -> None:
        """Backup the selected workspace."""
        await self.show_error("Workspace backup not yet implemented")
    
    async def delete_workspace(self) -> None:
        """Delete the selected workspace."""
        await self.show_error("Workspace deletion not yet implemented")
    
    async def show_error(self, message: str) -> None:
        """Show an error message."""
        # Show error in the info container
        info_container = self.query_one("#workspace-info")
        await info_container.remove_children()
        await info_container.mount(Static(message, classes="error-message"))
    
    async def show_success(self, message: str) -> None:
        """Show a success message."""
        # Show success in the info container
        info_container = self.query_one("#workspace-info")
        await info_container.remove_children()
        await info_container.mount(Static(message, classes="success-message"))


class TemplateBrowserScreen(Screen):
    """Template browser and management screen."""
    
    CSS = """
    .template-browser {
        height: 100%;
        layout: grid;
        grid-size: 3 1;
        grid-columns: 1fr 2fr 1fr;
        grid-rows: 1fr;
    }
    
    .template-sources {
        grid-column: 1;
        grid-row: 1;
        padding: 1;
        border: solid $primary;
    }
    
    .template-list {
        grid-column: 2;
        grid-row: 1;
        padding: 1;
        border: solid $accent;
    }
    
    .template-preview {
        grid-column: 3;
        grid-row: 1;
        padding: 1;
        border: solid $primary;
    }
    
    .source-tree {
        height: 20;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    .template-table {
        height: 25;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .preview-area {
        height: 20;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    .template-actions {
        margin: 1 0;
    }
    
    .action-buttons {
        height: auto;
        margin: 1 0;
    }
    
    .action-buttons Button {
        margin: 0 1;
    }
    
    .section-header {
        text-style: bold;
        color: $accent;
        margin: 0 0 1 0;
    }
    """
    
    def __init__(self, context: TUIContext):
        super().__init__()
        self.context = context
        self.content_service: Optional[ContentApplicationService] = None
        self.pipeline_service: Optional[PipelineApplicationService] = None
        self.selected_template: Optional[PipelineTemplateInfo] = None
        
        if context.container:
            self.content_service = context.container.resolve(ContentApplicationService)
            self.pipeline_service = context.container.resolve(PipelineApplicationService)
    
    def compose(self) -> ComposeResult:
        """Create the template browser layout."""
        
        with Container(classes="template-browser"):
            # Template sources
            with Container(classes="template-sources"):
                yield Static("📂 Sources", classes="section-header")
                
                with Container(classes="source-tree"):
                    yield Tree("Template Sources", id="source-tree")
                
                with Horizontal(classes="action-buttons"):
                    yield Button("Add Source", id="add-source", variant="success")
                    yield Button("Refresh", id="refresh-sources", variant="primary")
            
            # Template list
            with Container(classes="template-list"):
                yield Static("📋 Templates", classes="section-header")
                
                with Container(classes="template-table"):
                    yield DataTable(id="template-table")
                
                with Horizontal(classes="action-buttons"):
                    yield Button("Create New", id="create-template", variant="success")
                    yield Button("Edit", id="edit-template", variant="primary", disabled=True)
                    yield Button("Delete", id="delete-template", variant="error", disabled=True)
                    yield Button("Run", id="run-template", variant="success", disabled=True)
            
            # Template preview
            with Container(classes="template-preview"):
                yield Static("👁️ Preview", classes="section-header")
                
                with Container(classes="preview-area"):
                    yield TextArea(
                        id="template-preview",
                        read_only=True,
                        placeholder="Select a template to preview"
                    )
                
                with Horizontal(classes="action-buttons"):
                    yield Button("Export", id="export-template", variant="primary", disabled=True)
                    yield Button("Copy", id="copy-template", variant="default", disabled=True)
    
    async def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        await self.setup_source_tree()
        await self.setup_template_table()
        await self.load_templates()
    
    async def setup_source_tree(self) -> None:
        """Set up the template source tree."""
        tree = self.query_one("#source-tree", Tree)
        
        # Add template sources
        local_root = tree.root.add("Local", expand=True)
        local_root.add_leaf("Current Directory")
        local_root.add_leaf("~/.writeit/templates")
        
        workspace_root = tree.root.add("Workspace", expand=True)
        workspace_root.add_leaf(f"{self.context.workspace_name}")
        
        global_root = tree.root.add("Global", expand=True)
        global_root.add_leaf("Built-in Templates")
        global_root.add_leaf("Community Templates")
    
    async def setup_template_table(self) -> None:
        """Set up the template data table."""
        table = self.query_one("#template-table", DataTable)
        table.clear(columns=True)
        
        # Add columns
        table.add_column("Name", key="name")
        table.add_column("Type", key="type")
        table.add_column("Source", key="source")
        table.add_column("Modified", key="modified")
        table.add_column("Size", key="size")
        
        # Make table clickable
        table.cursor_type = "row"
    
    async def load_templates(self) -> None:
        """Load templates from all sources."""
        # This would load templates from the content service
        table = self.query_one("#template-table", DataTable)
        table.clear()
        
        # Mock data for now
        table.add_row(
            "tech-article",
            "Pipeline",
            "Workspace",
            "2024-01-15",
            "2.1 KB",
            key="tech-article"
        )
        table.add_row(
            "blog-post",
            "Pipeline",
            "Global",
            "2024-01-10",
            "1.8 KB",
            key="blog-post"
        )
        table.add_row(
            "code-review",
            "Pipeline",
            "Local",
            "2024-01-12",
            "3.2 KB",
            key="code-review"
        )
    
    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle template selection."""
        template_id = event.row_key.value if event.row_key else None
        if template_id:
            await self.select_template(template_id)
    
    async def select_template(self, template_id: str) -> None:
        """Select and display a template."""
        self.selected_template = template_id
        
        # Enable action buttons
        edit_btn = self.query_one("#edit-template")
        delete_btn = self.query_one("#delete-template")
        run_btn = self.query_one("#run-template")
        export_btn = self.query_one("#export-template")
        copy_btn = self.query_one("#copy-template")
        
        edit_btn.disabled = False
        delete_btn.disabled = False
        run_btn.disabled = False
        export_btn.disabled = False
        copy_btn.disabled = False
        
        # Show template preview
        preview_area = self.query_one("#template-preview", TextArea)
        preview_area.text = f"# Template: {template_id}\n\nTemplate content would be displayed here..."
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "refresh-sources":
            await self.load_templates()
        elif event.button.id == "create-template":
            await self.create_template()
        elif event.button.id == "edit-template":
            await self.edit_template()
        elif event.button.id == "delete-template":
            await self.delete_template()
        elif event.button.id == "run-template":
            await self.run_template()
        elif event.button.id == "export-template":
            await self.export_template()
        elif event.button.id == "copy-template":
            await self.copy_template()
    
    async def create_template(self) -> None:
        """Create a new template."""
        await self.show_error("Template creation not yet implemented")
    
    async def edit_template(self) -> None:
        """Edit the selected template."""
        await self.show_error("Template editing not yet implemented")
    
    async def delete_template(self) -> None:
        """Delete the selected template."""
        await self.show_error("Template deletion not yet implemented")
    
    async def run_template(self) -> None:
        """Run the selected template."""
        await self.show_error("Template execution not yet implemented")
    
    async def export_template(self) -> None:
        """Export the selected template."""
        await self.show_error("Template export not yet implemented")
    
    async def copy_template(self) -> None:
        """Copy the selected template."""
        await self.show_error("Template copying not yet implemented")
    
    async def show_error(self, message: str) -> None:
        """Show an error message."""
        # This would show a proper error dialog
        pass


class ConfigurationScreen(Screen):
    """Configuration and settings screen."""
    
    CSS = """
    .configuration {
        height: 100%;
        layout: grid;
        grid-size: 2 1;
        grid-columns: 1fr 2fr;
        grid-rows: 1fr;
    }
    
    .settings-categories {
        grid-column: 1;
        grid-row: 1;
        padding: 1;
        border: solid $primary;
    }
    
    .settings-panel {
        grid-column: 2;
        grid-row: 1;
        padding: 1;
    }
    
    .category-list {
        height: 20;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    .settings-form {
        background: $surface;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .settings-preview {
        background: $surface;
        padding: 1;
        border: solid $accent;
    }
    
    .action-buttons {
        height: auto;
        margin: 1 0;
    }
    
    .action-buttons Button {
        margin: 0 1;
    }
    
    .section-header {
        text-style: bold;
        color: $accent;
        margin: 0 0 1 0;
    }
    
    .setting-item {
        margin: 1 0;
    }
    
    .setting-label {
        color: $text-muted;
        margin-bottom: 0.5;
    }
    
    .setting-help {
        color: $text-muted;
        font-size: 0.9em;
        margin-top: 0.5;
    }
    """
    
    def __init__(self, context: TUIContext):
        super().__init__()
        self.context = context
        self.selected_category: Optional[str] = None
        
        # Settings categories
        self.categories = [
            ("general", "General"),
            ("workspace", "Workspace"),
            ("llm", "LLM Providers"),
            ("pipeline", "Pipeline"),
            ("ui", "User Interface"),
            ("advanced", "Advanced"),
        ]
    
    def compose(self) -> ComposeResult:
        """Create the configuration layout."""
        
        with Container(classes="configuration"):
            # Settings categories
            with Container(classes="settings-categories"):
                yield Static("⚙️ Settings", classes="section-header")
                
                with Container(classes="category-list"):
                    yield ListView(id="category-list")
                
                with Horizontal(classes="action-buttons"):
                    yield Button("Reset All", id="reset-settings", variant="warning")
                    yield Button("Export Config", id="export-config", variant="primary")
            
            # Settings panel
            with Container(classes="settings-panel"):
                yield Static("📋 Configuration", classes="section-header")
                
                with Container(id="settings-form", classes="settings-form"):
                    yield Static("Select a category to configure settings")
                
                with Container(id="settings-preview", classes="settings-preview"):
                    yield Static("Configuration preview will appear here")
    
    async def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        await self.setup_category_list()
    
    async def setup_category_list(self) -> None:
        """Set up the category list."""
        list_view = self.query_one("#category-list", ListView)
        await list_view.clear()
        
        for category_id, category_name in self.categories:
            item = ListItem(Static(category_name), id=f"category-{category_id}")
            await list_view.append(item)
    
    async def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle category selection."""
        if event.list_view.id == "category-list":
            category_id = event.item.id.replace("category-", "")
            await self.select_category(category_id)
    
    async def select_category(self, category_id: str) -> None:
        """Select and display category settings."""
        self.selected_category = category_id
        
        form_container = self.query_one("#settings-form")
        await form_container.remove_children()
        
        await form_container.mount(Static(f"⚙️ {category_id.title()} Settings", classes="section-header"))
        
        # Show settings based on category
        if category_id == "general":
            await self.show_general_settings()
        elif category_id == "workspace":
            await self.show_workspace_settings()
        elif category_id == "llm":
            await self.show_llm_settings()
        elif category_id == "pipeline":
            await self.show_pipeline_settings()
        elif category_id == "ui":
            await self.show_ui_settings()
        elif category_id == "advanced":
            await self.show_advanced_settings()
    
    async def show_general_settings(self) -> None:
        """Show general application settings."""
        # Default workspace
        yield Static("Default Workspace", classes="setting-label")
        yield Select(
            [("default", "Default"), ("work", "Work"), ("personal", "Personal")],
            id="default-workspace",
            value="default"
        )
        yield Static("The workspace to use when no workspace is specified", classes="setting-help")
        
        # Auto-save
        yield Static("Auto-save", classes="setting-label")
        yield Switch(id="auto-save", value=True)
        yield Static("Automatically save changes to pipelines and templates", classes="setting-help")
        
        # Check for updates
        yield Static("Check for Updates", classes="setting-label")
        yield Switch(id="check-updates", value=True)
        yield Static("Automatically check for application updates", classes="setting-help")
    
    async def show_workspace_settings(self) -> None:
        """Show workspace-specific settings."""
        yield Static("Workspace Location", classes="setting-label")
        yield Input(
            placeholder="~/.writeit/workspaces",
            id="workspace-location",
            value="~/.writeit/workspaces"
        )
        yield Static("Default location for workspace directories", classes="setting-help")
        
        yield Static("Workspace Isolation", classes="setting-label")
        yield Switch(id="workspace-isolation", value=True)
        yield Static("Strictly isolate data between workspaces", classes="setting-help")
        
        yield Static("Auto-backup", classes="setting-label")
        yield Switch(id="auto-backup", value=False)
        yield Static("Automatically backup workspace data", classes="setting-help")
    
    async def show_llm_settings(self) -> None:
        """Show LLM provider settings."""
        yield Static("Default LLM Provider", classes="setting-label")
        yield Select(
            [("openai", "OpenAI"), ("anthropic", "Anthropic"), ("local", "Local")],
            id="default-llm",
            value="openai"
        )
        yield Static("Default LLM provider for new pipelines", classes="setting-help")
        
        yield Static("API Keys", classes="setting-label")
        yield Input(
            placeholder="Enter API keys",
            id="api-keys",
            password=True
        )
        yield Static("API keys for LLM providers", classes="setting-help")
        
        yield Static("Cache Responses", classes="setting-label")
        yield Switch(id="cache-responses", value=True)
        yield Static("Cache LLM responses to reduce API calls", classes="setting-help")
    
    async def show_pipeline_settings(self) -> None:
        """Show pipeline execution settings."""
        yield Static("Default Execution Mode", classes="setting-label")
        yield Select(
            [("cli", "CLI"), ("tui", "TUI"), ("api", "API")],
            id="default-execution-mode",
            value="tui"
        )
        yield Static("Default execution mode for pipelines", classes="setting-help")
        
        yield Static("Max Concurrent Steps", classes="setting-label")
        yield Input(
            placeholder="3",
            id="max-concurrent-steps",
            value="3"
        )
        yield Static("Maximum number of steps to execute concurrently", classes="setting-help")
        
        yield Static("Step Timeout", classes="setting-label")
        yield Input(
            placeholder="300",
            id="step-timeout",
            value="300"
        )
        yield Static("Maximum time (seconds) for a single step to complete", classes="setting-help")
    
    async def show_ui_settings(self) -> None:
        """Show user interface settings."""
        yield Static("Theme", classes="setting-label")
        yield Select(
            [("default", "Default"), ("dark", "Dark"), ("light", "Light")],
            id="theme",
            value="default"
        )
        yield Static("Application color theme", classes="setting-help")
        
        yield Static("Show Debug Info", classes="setting-label")
        yield Switch(id="show-debug", value=False)
        yield Static("Show debug information in the UI", classes="setting-help")
        
        yield Static("Keyboard Shortcuts", classes="setting-label")
        yield Switch(id="keyboard-shortcuts", value=True)
        yield Static("Enable keyboard shortcuts", classes="setting-help")
    
    async def show_advanced_settings(self) -> None:
        """Show advanced settings."""
        yield Static("Log Level", classes="setting-label")
        yield Select(
            [("DEBUG", "Debug"), ("INFO", "Info"), ("WARNING", "Warning"), ("ERROR", "Error")],
            id="log-level",
            value="INFO"
        )
        yield Static("Application logging level", classes="setting-help")
        
        yield Static("Data Directory", classes="setting-label")
        yield Input(
            placeholder="~/.writeit",
            id="data-directory",
            value="~/.writeit"
        )
        yield Static("Directory for application data", classes="setting-help")
        
        yield Static("Telemetry", classes="setting-label")
        yield Switch(id="telemetry", value=False)
        yield Static("Send anonymous usage data to improve the application", classes="setting-help")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "reset-settings":
            await self.reset_settings()
        elif event.button.id == "export-config":
            await self.export_config()
    
    async def reset_settings(self) -> None:
        """Reset all settings to defaults."""
        await self.show_error("Settings reset not yet implemented")
    
    async def export_config(self) -> None:
        """Export configuration to file."""
        await self.show_error("Configuration export not yet implemented")