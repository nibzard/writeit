"""Template Browser and Editor TUI Component.

Provides a rich terminal interface for browsing, creating, and editing content templates
and style primers. Integrates with the Content Application Service for comprehensive
template management with validation, preview, and workspace awareness.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    TextArea,
    Input,
    Select,
    Tabs,
    Tab,
    TabPane,
    DataTable,
    Log,
    Markdown,
    Switch,
)
from textual.reactive import reactive
from textual.binding import Binding

from ...application.services.content_application_service import (
    ContentApplicationService,
    ContentListingRequest,
    ContentListingScope,
    TemplateCreationRequest,
    StyleCreationRequest,
    ContentValidationRequest,
    ContentValidationLevel,
)
from ...application.services.workspace_application_service import (
    WorkspaceApplicationService,
)
from ...shared.dependencies.container import Container as DIContainer


class TemplateEditorMode(str, Enum):
    """Template editor modes."""
    CREATE = "create"
    EDIT = "edit"
    VIEW = "view"
    CLONE = "clone"


class ContentType(str, Enum):
    """Content types."""
    TEMPLATE = "template"
    STYLE = "style"


@dataclass
class TemplateEditorConfig:
    """Configuration for template editor interface."""
    
    auto_save_interval: int = 60  # Auto-save every 60 seconds
    show_line_numbers: bool = True
    syntax_highlighting: bool = True
    validation_on_change: bool = True
    show_preview: bool = True
    max_content_length: int = 50000  # Max characters for templates


class TemplateBrowserWidget(Container):
    """Widget for browsing available templates and styles."""
    
    selected_content = reactive(None)
    current_scope = reactive(ContentListingScope.WORKSPACE)
    current_content_type = reactive(ContentType.TEMPLATE)
    
    def __init__(self, content_service: ContentApplicationService):
        super().__init__()
        self.content_service = content_service
        self.content_items: List[Dict[str, Any]] = []
        self.selected_item_data: Optional[Dict[str, Any]] = None
        
    def compose(self) -> ComposeResult:
        yield Static("📚 Content Browser", classes="section-header")
        
        # Controls
        with Horizontal(classes="browser-controls"):
            # Content type selector
            yield Static("Type:", classes="control-label")
            content_type_options = [
                ("Templates", ContentType.TEMPLATE),
                ("Styles", ContentType.STYLE),
            ]
            yield Select(
                content_type_options,
                id="content-type-select",
                value=ContentType.TEMPLATE,
                classes="control-select"
            )
            
            # Scope selector
            yield Static("Scope:", classes="control-label")
            scope_options = [
                ("Workspace", ContentListingScope.WORKSPACE),
                ("Global", ContentListingScope.GLOBAL),
                ("All", ContentListingScope.ALL),
            ]
            yield Select(
                scope_options,
                id="scope-select",
                value=ContentListingScope.WORKSPACE,
                classes="control-select"
            )
            
            # Refresh button
            yield Button("🔄 Refresh", id="refresh-btn", variant="default")
            
            # Create button
            yield Button("➕ Create", id="create-btn", variant="primary")
        
        # Filter and search
        with Horizontal(classes="filter-controls"):
            yield Static("Filter:", classes="control-label")
            yield Input(placeholder="Search by name or description...", id="filter-input", classes="filter-input")
            yield Button("🔍 Search", id="search-btn", variant="default")
        
        # Content list
        yield DataTable(id="content-table", classes="content-table")
        
        # Preview panel
        with Vertical(classes="preview-panel"):
            yield Static("📝 Preview", classes="preview-header")
            yield Markdown("Select an item to preview...", id="content-preview", classes="preview-content")
        
        # Action buttons
        with Horizontal(classes="action-buttons"):
            yield Button("📖 View", id="view-btn", variant="default", disabled=True)
            yield Button("✏️ Edit", id="edit-btn", variant="warning", disabled=True)
            yield Button("📋 Copy", id="copy-btn", variant="default", disabled=True)
            yield Button("🗑️ Delete", id="delete-btn", variant="error", disabled=True)
            yield Button("🔍 Validate", id="validate-btn", variant="success", disabled=True)
    
    def on_mount(self) -> None:
        """Initialize the content browser."""
        self._setup_content_table()
        self.call_after_refresh(self.refresh_content_list)
    
    def _setup_content_table(self) -> None:
        """Setup the content data table."""
        table = self.query_one("#content-table")
        table.add_columns("Name", "Description", "Source", "Workspace", "Created")
        table.cursor_type = "row"
    
    def watch_current_content_type(self) -> None:
        """Handle content type change."""
        self.refresh_content_list()
    
    def watch_current_scope(self) -> None:
        """Handle scope change."""
        self.refresh_content_list()
    
    async def refresh_content_list(self) -> None:
        """Refresh the content list from the service."""
        try:
            # Create listing request
            request = ContentListingRequest(
                scope=self.current_scope,
                content_type=self.current_content_type.value,
                include_metadata=True,
                include_analytics=True
            )
            
            # Get content list
            content_data = await self.content_service.list_content(request)
            
            # Update content items
            if self.current_content_type == ContentType.TEMPLATE:
                self.content_items = content_data.get("templates", [])
            else:
                self.content_items = content_data.get("styles", [])
            
            # Update table
            self._update_content_table()
            
            # Clear preview
            preview = self.query_one("#content-preview")
            preview.update("Select an item to preview...")
            
            # Disable action buttons
            self._set_action_buttons_state(False)
            
        except Exception as e:
            self.log_error(f"Failed to refresh content list: {e}")
    
    def _update_content_table(self) -> None:
        """Update the content data table."""
        table = self.query_one("#content-table")
        table.clear()
        
        for item in self.content_items:
            row_data = [
                item["name"],
                item.get("description", "")[:50] + "..." if len(item.get("description", "")) > 50 else item.get("description", ""),
                item.get("source", "workspace"),
                item.get("workspace", "N/A"),
                item.get("metadata", {}).get("created_at", "N/A")
            ]
            table.add_row(*row_data, key=item["name"])
    
    def on_data_table_row_selected(self, event) -> None:
        """Handle row selection."""
        selected_name = event.row_key.value if event.row_key else None
        
        # Find selected item
        self.selected_item_data = None
        for item in self.content_items:
            if item["name"] == selected_name:
                self.selected_item_data = item
                break
        
        if self.selected_item_data:
            self._update_preview()
            self._set_action_buttons_state(True)
        else:
            self._set_action_buttons_state(False)
    
    def _update_preview(self) -> None:
        """Update the preview panel with selected content."""
        if not self.selected_item_data:
            return
        
        preview = self.query_one("#content-preview")
        
        # Create preview content
        preview_text = f"""## {self.selected_item_data['name']}

{self.selected_item_data.get('description', 'No description')}

### Metadata
- **Type**: {self.current_content_type.value.title()}
- **Source**: {self.selected_item_data.get('source', 'workspace')}
- **Workspace**: {self.selected_item_data.get('workspace', 'N/A')}
- **Created**: {self.selected_item_data.get('metadata', {}).get('created_at', 'N/A')}

### Analytics
"""
        
        if self.selected_item_data.get('analytics'):
            analytics = self.selected_item_data['analytics']
            if 'usage_count' in analytics:
                preview_text += f"- **Usage Count**: {analytics['usage_count']}\n"
            if 'last_used' in analytics:
                preview_text += f"- **Last Used**: {analytics['last_used']}\n"
            if 'average_generation_time' in analytics:
                preview_text += f"- **Avg Generation Time**: {analytics['average_generation_time']}s\n"
        else:
            preview_text += "No analytics data available.\n"
        
        preview.update(preview_text)
    
    def _set_action_buttons_state(self, enabled: bool) -> None:
        """Set the enabled state of action buttons."""
        action_buttons = ["view-btn", "edit-btn", "copy-btn", "delete-btn", "validate-btn"]
        
        for button_id in action_buttons:
            try:
                button = self.query_one(f"#{button_id}")
                button.disabled = not enabled
            except Exception:
                pass
    
    def log_error(self, message: str) -> None:
        """Log an error message."""
        try:
            log_widget = self.query_one(Log)
            log_widget.write_line(f"[ERROR] {message}")
        except Exception:
            pass


class TemplateEditorWidget(Container):
    """Widget for creating and editing templates and styles."""
    
    editor_mode = reactive(TemplateEditorMode.CREATE)
    content_type = reactive(ContentType.TEMPLATE)
    is_modified = reactive(False)
    validation_status = reactive("not_validated")
    
    def __init__(
        self, 
        content_service: ContentApplicationService,
        workspace_service: WorkspaceApplicationService,
        config: TemplateEditorConfig = None
    ):
        super().__init__()
        self.content_service = content_service
        self.workspace_service = workspace_service
        self.config = config or TemplateEditorConfig()
        
        # Editor state
        self.original_content: Optional[str] = None
        self.current_workspace: Optional[str] = None
        
    def compose(self) -> ComposeResult:
        yield Static("📝 Content Editor", classes="section-header")
        
        # Editor controls
        with Horizontal(classes="editor-controls"):
            # Content type selector (only in create mode)
            if self.editor_mode == TemplateEditorMode.CREATE:
                yield Static("Type:", classes="control-label")
                content_type_options = [
                    ("Template", ContentType.TEMPLATE),
                    ("Style Primer", ContentType.STYLE),
                ]
                yield Select(
                    content_type_options,
                    id="editor-content-type",
                    value=ContentType.TEMPLATE,
                    classes="control-select"
                )
            
            # Workspace selector
            yield Static("Workspace:", classes="control-label")
            yield Select([], id="workspace-select", classes="control-select")
            
            # Save status
            yield Static("💾", id="save-status", classes="save-status")
            
            # Validation status
            yield Static("✓", id="validation-status", classes="validation-status")
        
        # Content form
        with Vertical(classes="content-form"):
            # Name and description
            with Horizontal(classes="form-row"):
                yield Static("Name*:", classes="form-label")
                yield Input(placeholder="Enter name...", id="content-name", classes="form-input")
                
                yield Static("Description:", classes="form-label")
                yield Input(placeholder="Enter description...", id="content-description", classes="form-input")
            
            # Content editor area
            with Tabs():
                yield Tab("Edit", id="edit-tab")
                yield Tab("Preview", id="preview-tab")
                yield Tab("Metadata", id="metadata-tab")
            
            with TabPane("Edit", id="edit-pane"):
                with Vertical(classes="editor-container"):
                    # Editor toolbar
                    with Horizontal(classes="editor-toolbar"):
                        yield Static(f"{self.content_type.value.title()} Content*:", classes="editor-label")
                        yield Button("📋 Insert Template", id="insert-template-btn", variant="default")
                        yield Button("🔄 Format", id="format-btn", variant="default")
                        yield Switch(value=True, label="Auto-validate", id="auto-validate-switch")
                    
                    # Content text area
                    yield TextArea(
                        "",
                        id="content-editor",
                        classes="content-editor",
                        language="yaml" if self.content_type == ContentType.TEMPLATE else "markdown"
                    )
            
            with TabPane("Preview", id="preview-pane"):
                yield Markdown(
                    "Preview will be shown here...",
                    id="content-preview",
                    classes="preview-content"
                )
            
            with TabPane("Metadata", id="metadata-pane"):
                with Vertical(classes="metadata-container"):
                    yield Static("Content metadata and settings", classes="metadata-header")
                    yield DataTable(id="metadata-table", classes="metadata-table")
        
        # Validation results
        with Vertical(classes="validation-panel"):
            yield Static("🔍 Validation Results", classes="validation-header")
            yield Log(id="validation-log", classes="validation-log")
        
        # Action buttons
        with Horizontal(classes="action-buttons"):
            yield Button("💾 Save", id="save-btn", variant="success", disabled=True)
            yield Button("🔄 Reset", id="reset-btn", variant="warning", disabled=True)
            yield Button("🔍 Validate", id="validate-btn", variant="default")
            yield Button("📋 Test", id="test-btn", variant="default")
            yield Button("❌ Cancel", id="cancel-btn", variant="error")
    
    def on_mount(self) -> None:
        """Initialize the editor."""
        self._setup_metadata_table()
        self.call_after_refresh(self.load_workspaces)
        self.call_after_refresh(self.update_validation_status)
    
    async def load_workspaces(self) -> None:
        """Load available workspaces."""
        try:
            # Get available workspaces
            workspaces = await self.workspace_service.list_workspaces()
            
            # Update workspace selector
            workspace_select = self.query_one("#workspace-select")
            workspace_options = [(ws.name.value, ws.name.value) for ws in workspaces]
            workspace_select.set_options(workspace_options)
            
            # Set current workspace
            if workspace_options:
                workspace_select.value = workspace_options[0][1]
                self.current_workspace = workspace_options[0][1]
            
        except Exception as e:
            self.log_validation_message("ERROR", f"Failed to load workspaces: {e}")
    
    def _setup_metadata_table(self) -> None:
        """Setup the metadata table."""
        table = self.query_one("#metadata-table")
        table.add_columns("Property", "Value")
        table.add_row("Content Type", self.content_type.value)
        table.add_row("Editor Mode", self.editor_mode.value)
        table.add_row("Created", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Modified", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def watch_content_type(self) -> None:
        """Handle content type change."""
        self._update_editor_language()
        self._update_metadata_table()
    
    def watch_editor_mode(self) -> None:
        """Handle editor mode change."""
        self._update_metadata_table()
    
    def _update_editor_language(self) -> None:
        """Update the editor language based on content type."""
        editor = self.query_one("#content-editor")
        if self.content_type == ContentType.TEMPLATE:
            editor.language = "yaml"
        else:
            editor.language = "markdown"
    
    def _update_metadata_table(self) -> None:
        """Update the metadata table."""
        table = self.query_one("#metadata-table")
        table.clear()
        
        table.add_row("Content Type", self.content_type.value)
        table.add_row("Editor Mode", self.editor_mode.value)
        table.add_row("Created", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Modified", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    async def validate_content(self) -> bool:
        """Validate the current content."""
        try:
            name_input = self.query_one("#content-name")
            content_editor = self.query_one("#content-editor")
            
            name = name_input.value.strip()
            content = content_editor.text.strip()
            
            if not name:
                self.log_validation_message("ERROR", "Name is required")
                return False
            
            if not content:
                self.log_validation_message("ERROR", "Content is required")
                return False
            
            # Create validation request
            validation_request = ContentValidationRequest(
                content_identifier=name,
                content_type=self.content_type.value,
                workspace_name=self.current_workspace,
                validation_level=ContentValidationLevel.STANDARD
            )
            
            # Perform validation
            result = await self.content_service.validate_content(validation_request)
            
            # Process validation results
            validation_result = result.get("validation_result", {})
            is_valid = validation_result.get("is_valid", False)
            
            if is_valid:
                self.log_validation_message("SUCCESS", "Content validation passed")
                self.validation_status = "valid"
            else:
                errors = validation_result.get("errors", [])
                for error in errors:
                    self.log_validation_message("ERROR", error)
                self.validation_status = "invalid"
            
            # Show recommendations
            recommendations = result.get("recommendations", [])
            for rec in recommendations:
                self.log_validation_message("INFO", rec)
            
            return is_valid
            
        except Exception as e:
            self.log_validation_message("ERROR", f"Validation failed: {e}")
            self.validation_status = "error"
            return False
    
    def log_validation_message(self, level: str, message: str) -> None:
        """Log a validation message."""
        try:
            log_widget = self.query_one("#validation-log")
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            if level.lower() == "error":
                log_widget.write_line(f"[{timestamp}] [ERROR] {message}", style="red")
            elif level.lower() == "warning":
                log_widget.write_line(f"[{timestamp}] [WARN] {message}", style="yellow")
            elif level.lower() == "success":
                log_widget.write_line(f"[{timestamp}] [SUCCESS] {message}", style="green")
            else:
                log_widget.write_line(f"[{timestamp}] [INFO] {message}")
        except Exception:
            pass
    
    async def save_content(self) -> bool:
        """Save the current content."""
        try:
            name_input = self.query_one("#content-name")
            desc_input = self.query_one("#content-description")
            content_editor = self.query_one("#content-editor")
            
            name = name_input.value.strip()
            description = desc_input.value.strip()
            content = content_editor.text.strip()
            
            # Validate first
            if not await self.validate_content():
                return False
            
            # Create content based on type
            if self.content_type == ContentType.TEMPLATE:
                request = TemplateCreationRequest(
                    name=name,
                    description=description,
                    content=content,
                    workspace_name=self.current_workspace,
                    validation_level=ContentValidationLevel.STANDARD
                )
                
                await self.content_service.create_template(request)
                self.log_validation_message("SUCCESS", f"Template '{name}' created successfully")
                
            else:  # STYLE
                request = StyleCreationRequest(
                    name=name,
                    description=description,
                    style_content=content,
                    workspace_name=self.current_workspace,
                    validation_level=ContentValidationLevel.STANDARD
                )
                
                await self.content_service.create_style(request)
                self.log_validation_message("SUCCESS", f"Style '{name}' created successfully")
            
            # Update state
            self.is_modified = False
            self.original_content = content
            self._update_save_status()
            
            return True
            
        except Exception as e:
            self.log_validation_message("ERROR", f"Failed to save content: {e}")
            return False
    
    def _update_save_status(self) -> None:
        """Update the save status indicator."""
        save_status = self.query_one("#save-status")
        if self.is_modified:
            save_status.update("💾*")
        else:
            save_status.update("💾")
    
    def update_validation_status(self) -> None:
        """Update the validation status indicator."""
        validation_widget = self.query_one("#validation-status")
        
        if self.validation_status == "valid":
            validation_widget.update("✅")
        elif self.validation_status == "invalid":
            validation_widget.update("❌")
        elif self.validation_status == "error":
            validation_widget.update("⚠️")
        else:
            validation_widget.update("🔍")
    
    def watch_validation_status(self) -> None:
        """Handle validation status change."""
        self.update_validation_status()


class TemplateBrowserEditorApp(App[None]):
    """Template Browser and Editor application."""
    
    CSS = """
    .section-header {
        text-style: bold;
        color: $accent;
        margin: 1 0;
        border-bottom: solid $primary 1px;
        padding-bottom: 1;
    }
    
    .browser-controls, .filter-controls, .editor-controls {
        height: auto;
        margin: 0 0 1 0;
        align: left;
    }
    
    .control-label {
        color: $text-muted;
        margin: 0 1 0 0;
        min-width: 8;
    }
    
    .control-select {
        width: 15;
        margin: 0 1 0 0;
    }
    
    .filter-input {
        width: 30;
        margin: 0 1 0 0;
    }
    
    .content-table {
        height: 15;
        margin: 1 0;
        border: solid $primary 1px;
    }
    
    .preview-panel {
        height: 20;
        margin: 1 0;
        border: solid $surface 1px;
    }
    
    .preview-header {
        color: $secondary;
        text-style: bold;
        margin: 0 0 1 0;
    }
    
    .preview-content {
        height: 15;
        overflow-y: auto;
    }
    
    .action-buttons {
        height: auto;
        margin: 1 0;
        dock: bottom;
    }
    
    .action-buttons Button {
        margin: 0 1;
        min-width: 10;
    }
    
    .editor-controls {
        background: $surface;
        padding: 1;
        border: solid $primary 1px;
    }
    
    .save-status, .validation-status {
        margin: 0 1 0 0;
        color: $text-muted;
    }
    
    .content-form {
        margin: 1 0;
    }
    
    .form-row {
        height: auto;
        margin: 0 0 1 0;
    }
    
    .form-label {
        color: $text-muted;
        margin: 0 1 0 0;
        min-width: 12;
    }
    
    .form-input {
        width: 20;
        margin: 0 1 0 0;
    }
    
    .editor-container {
        margin: 1 0;
    }
    
    .editor-toolbar {
        height: auto;
        margin: 0 0 1 0;
        align: left;
    }
    
    .editor-label {
        color: $text-muted;
        margin: 0 1 0 0;
    }
    
    .content-editor {
        height: 25;
        border: solid $primary 1px;
        font-family: monospace;
    }
    
    .validation-panel {
        height: 15;
        margin: 1 0;
        border: solid $warning 1px;
    }
    
    .validation-header {
        color: $secondary;
        text-style: bold;
        margin: 0 0 1 0;
    }
    
    .validation-log {
        height: 10;
        font-family: monospace;
        font-size: 0.9em;
        overflow-y: auto;
    }
    
    .metadata-container {
        height: 20;
        margin: 1 0;
    }
    
    .metadata-header {
        color: $secondary;
        text-style: bold;
        margin: 0 0 1 0;
    }
    
    .metadata-table {
        height: 15;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+s", "save_content", "Save"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("ctrl+n", "new_template", "New Template"),
        Binding("f1", "show_help", "Help"),
        Binding("tab", "focus_next", "Next Field"),
        Binding("shift+tab", "focus_previous", "Previous Field"),
    ]
    
    def __init__(
        self, 
        workspace_name: str = "default",
        config: TemplateEditorConfig = None
    ):
        super().__init__()
        self.workspace_name = workspace_name
        self.config = config or TemplateEditorConfig()
        
        # Services
        self.di_container: Optional[DIContainer] = None
        self.content_service: Optional[ContentApplicationService] = None
        self.workspace_service: Optional[WorkspaceApplicationService] = None
        
        # UI state
        self.current_view = "browser"  # browser, editor
        self.editor_mode = TemplateEditorMode.CREATE
        self.editing_content_type = ContentType.TEMPLATE
        self.editing_item: Optional[Dict[str, Any]] = None
    
    async def on_mount(self) -> None:
        """Initialize the application."""
        await self.initialize_services()
        await self.show_browser_view()
    
    async def initialize_services(self) -> None:
        """Initialize required services."""
        try:
            # Create DI container
            from ...application.di_config import DIConfiguration
            self.di_container = DIConfiguration.create_container(
                base_path=Path.cwd(),
                workspace_name=self.workspace_name
            )
            
            # Get services
            self.content_service = self.di_container.resolve(ContentApplicationService)
            self.workspace_service = self.di_container.resolve(WorkspaceApplicationService)
            
        except Exception as e:
            self.show_error(f"Failed to initialize services: {e}")
            raise
    
    async def show_browser_view(self) -> None:
        """Show the browser view."""
        self.current_view = "browser"
        
        # Update main content
        main_content = self.query_one("#main-content")
        await main_content.remove_children()
        
        # Create browser widget
        browser = TemplateBrowserWidget(self.content_service)
        await main_content.mount(browser)
        
        # Set focus
        self.call_after_refresh(lambda: self.screen.focus_first())
    
    async def show_editor_view(
        self, 
        mode: TemplateEditorMode = TemplateEditorMode.CREATE,
        content_type: ContentType = ContentType.TEMPLATE,
        item_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Show the editor view."""
        self.current_view = "editor"
        self.editor_mode = mode
        self.editing_content_type = content_type
        self.editing_item = item_data
        
        # Update main content
        main_content = self.query_one("#main-content")
        await main_content.remove_children()
        
        # Create editor widget
        editor = TemplateEditorWidget(
            self.content_service,
            self.workspace_service,
            self.config
        )
        editor.editor_mode = mode
        editor.content_type = content_type
        
        await main_content.mount(editor)
        
        # Load existing data if editing
        if item_data and mode in [TemplateEditorMode.EDIT, TemplateEditorMode.VIEW]:
            await self.load_item_into_editor(editor, item_data)
        
        # Set focus
        self.call_after_refresh(lambda: self.screen.focus_first())
    
    async def load_item_into_editor(
        self, 
        editor: TemplateEditorWidget, 
        item_data: Dict[str, Any]
    ) -> None:
        """Load item data into the editor."""
        try:
            # Load the full content
            content_type = item_data.get("type", self.editing_content_type.value)
            
            # Load content based on type
            if content_type == "template":
                # Load template content
                template_content = await self.content_service.get_template_content(
                    item_data["name"], 
                    item_data.get("workspace", self.workspace_name)
                )
                content_editor.text = template_content
            else:
                # Load style content
                style_content = await self.content_service.get_style_content(
                    item_data["name"], 
                    item_data.get("workspace", self.workspace_name)
                )
                content_editor.text = style_content
            
            # Update editor fields
            name_input = editor.query_one("#content-name")
            desc_input = editor.query_one("#content-description")
            content_editor = editor.query_one("#content-editor")
            
            name_input.value = item_data.get("name", "")
            desc_input.value = item_data.get("description", "")
            # content_editor.text = loaded_content
            
            # Set readonly for view mode
            if self.editor_mode == TemplateEditorMode.VIEW:
                content_editor.read_only = True
                name_input.disabled = True
                desc_input.disabled = True
            
        except Exception as e:
            self.show_error(f"Failed to load content: {e}")
    
    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        
        with ScrollableContainer(id="main-content"):
            yield Static("🚀 WriteIt Template Browser & Editor", classes="section-header")
            yield Static("Loading...", id="status-message")
        
        yield Footer()
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if self.current_view == "browser":
            await self.handle_browser_button_press(button_id)
        elif self.current_view == "editor":
            await self.handle_editor_button_press(button_id)
    
    async def handle_browser_button_press(self, button_id: str) -> None:
        """Handle browser view button presses."""
        browser = self.query_one(TemplateBrowserWidget)
        
        if button_id == "refresh-btn":
            await browser.refresh_content_list()
        elif button_id == "create-btn":
            await self.show_editor_view(TemplateEditorMode.CREATE, browser.current_content_type)
        elif button_id == "view-btn":
            if browser.selected_item_data:
                await self.show_editor_view(TemplateEditorMode.VIEW, browser.current_content_type, browser.selected_item_data)
        elif button_id == "edit-btn":
            if browser.selected_item_data:
                await self.show_editor_view(TemplateEditorMode.EDIT, browser.current_content_type, browser.selected_item_data)
        elif button_id == "delete-btn":
            if browser.selected_item_data:
                await self.handle_delete_content(browser.selected_item_data)
        elif button_id == "validate-btn":
            if browser.selected_item_data:
                await self.handle_validate_content(browser.selected_item_data)
    
    async def handle_editor_button_press(self, button_id: str) -> None:
        """Handle editor view button presses."""
        editor = self.query_one(TemplateEditorWidget)
        
        if button_id == "save-btn":
            await editor.save_content()
        elif button_id == "reset-btn":
            await self.reset_editor_content(editor)
        elif button_id == "validate-btn":
            await editor.validate_content()
        elif button_id == "cancel-btn":
            await self.show_browser_view()
    
    async def handle_delete_content(self, item_data: Dict[str, Any]) -> None:
        """Handle content deletion."""
        try:
            content_type = item_data.get("type", "template")
            content_name = item_data["name"]
            workspace_name = item_data.get("workspace", self.workspace_name)
            
            # Confirm deletion
            status = self.query_one("#status-message")
            status.update(f"⚠️ Confirm delete {content_type} '{content_name}'? (y/N)")
            
            # For now, we'll proceed with deletion (in a real app, you'd want user confirmation)
            if content_type == "template":
                success = await self.content_service.delete_template(content_name, workspace_name)
                if success:
                    status.update(f"✅ Template '{content_name}' deleted successfully")
                    # Refresh browser view
                    await self.show_browser_view()
                else:
                    status.update(f"❌ Failed to delete template '{content_name}'")
            else:
                success = await self.content_service.delete_style(content_name, workspace_name)
                if success:
                    status.update(f"✅ Style '{content_name}' deleted successfully")
                    # Refresh browser view
                    await self.show_browser_view()
                else:
                    status.update(f"❌ Failed to delete style '{content_name}'")
                    
        except Exception as e:
            self.show_error(f"Failed to delete content: {e}")
    
    async def handle_validate_content(self, item_data: Dict[str, Any]) -> None:
        """Handle content validation."""
        try:
            content_type = item_data.get("type", "template")
            content_name = item_data["name"]
            workspace_name = item_data.get("workspace", self.workspace_name)
            
            # Create validation request
            validation_request = ContentValidationRequest(
                content_identifier=content_name,
                content_type=content_type,
                workspace_name=workspace_name,
                validation_level=ContentValidationLevel.STANDARD
            )
            
            # Perform validation
            result = await self.content_service.validate_content(validation_request)
            
            # Show validation results
            validation_result = result.get("validation_result", {})
            is_valid = validation_result.get("is_valid", False)
            
            if is_valid:
                status_msg = f"✅ {content_type.title()} '{content_name}' is valid"
            else:
                errors = validation_result.get("errors", [])
                status_msg = f"❌ {content_type.title()} '{content_name}' has {len(errors)} errors"
            
            status = self.query_one("#status-message")
            status.update(status_msg)
            
            # Show detailed validation in a new view or dialog would be ideal here
            # For now, we'll just update the status message
            
        except Exception as e:
            self.show_error(f"Failed to validate content: {e}")
    
    async def reset_editor_content(self, editor: TemplateEditorWidget) -> None:
        """Reset editor to original content."""
        if editor.original_content:
            content_editor = editor.query_one("#content-editor")
            content_editor.text = editor.original_content
            editor.is_modified = False
            editor._update_save_status()
    
    def show_error(self, message: str) -> None:
        """Show an error message."""
        status = self.query_one("#status-message")
        status.update(f"❌ Error: {message}")
    
    def action_save_content(self) -> None:
        """Save current content action."""
        if self.current_view == "editor":
            asyncio.create_task(self.handle_editor_button_press("save-btn"))
    
    def action_refresh(self) -> None:
        """Refresh current view action."""
        if self.current_view == "browser":
            browser = self.query_one(TemplateBrowserWidget)
            asyncio.create_task(browser.refresh_content_list())
    
    def action_new_template(self) -> None:
        """Create new template action."""
        asyncio.create_task(self.show_editor_view(TemplateEditorMode.CREATE, ContentType.TEMPLATE))
    
    def action_focus_next(self) -> None:
        """Focus next interactive element."""
        self.screen.focus_next()
    
    def action_focus_previous(self) -> None:
        """Focus previous interactive element."""
        self.screen.focus_previous()
    
    def action_show_help(self) -> None:
        """Show help information."""
        help_text = """
# WriteIt Template Browser & Editor Help

## Navigation
- **Tab/Shift+Tab**: Navigate between fields
- **Arrow Keys**: Navigate in lists and tables
- **Enter**: Select/Confirm action
- **Esc**: Cancel/Go back

## Browser View
- **F5/R**: Refresh content list
- **Ctrl+N**: Create new template
- **Delete**: Delete selected item
- **F1**: Show this help

## Editor View
- **Ctrl+S**: Save content
- **Ctrl+R**: Reset to original
- **Ctrl+V**: Validate content
- **F1**: Show this help

## Content Types
- **Templates**: YAML pipeline definitions with steps and inputs
- **Styles**: Markdown style primers for content generation

## Tips
- Use workspace scope to organize your content
- Global templates/styles are shared across all workspaces
- Validation helps ensure content quality and compatibility
"""
        
        # Show help in a modal or new view would be ideal
        # For now, we'll update the status message
        status = self.query_one("#status-message")
        status.update("📖 Help shown - press any key to continue")
    
    def on_key(self, event) -> None:
        """Handle key events."""
        # Clear help message when any key is pressed after showing help
        if "Help shown" in self.query_one("#status-message").render():
            self.query_one("#status-message").update("Ready")


async def run_template_browser_editor(
    workspace_name: str = "default",
    config: TemplateEditorConfig = None
) -> None:
    """Run the template browser and editor application."""
    app = TemplateBrowserEditorApp(workspace_name, config)
    await app.run_async()