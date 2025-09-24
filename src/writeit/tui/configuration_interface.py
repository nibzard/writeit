"""Configuration Interface TUI Component.

Provides a rich terminal interface for managing WriteIt configuration across different
scopes (global, workspace, environment, runtime). Supports schema validation,
configuration merging, and environment-specific overrides.
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
    Log,
    Markdown,
    Switch,
    TextArea,
    RadioButton,
    RadioSet,
)
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.message import Message
from textual.timer import Timer

from ...domains.workspace.services.workspace_configuration_service import (
    WorkspaceConfigurationService,
    ConfigurationValidationIssue,
    ConfigurationScope,
    ConfigurationSchema,
)
from ...shared.dependencies.container import Container as DIContainer


@dataclass
class ConfigurationInterfaceConfig:
    """Configuration for the configuration interface TUI."""
    auto_refresh_interval: int = 30  # seconds
    max_log_entries: int = 1000
    show_validation: bool = True
    enable_schema_editing: bool = True
    enable_animations: bool = True


class ConfigAction(str, Enum):
    """Configuration actions available in the TUI."""
    VIEW = "view"
    EDIT = "edit"
    CREATE = "create"
    DELETE = "delete"
    VALIDATE = "validate"
    RESET = "reset"


@dataclass
class ConfigurationEntry:
    """Configuration entry for display."""
    key: str
    value: Any
    scope: ConfigurationScope
    type: str
    is_valid: bool
    description: Optional[str] = None
    default_value: Optional[Any] = None
    environment_override: Optional[Any] = None


class ConfigurationSelected(Message):
    """Message emitted when a configuration entry is selected."""
    def __init__(self, config_key: str, scope: ConfigurationScope) -> None:
        self.config_key = config_key
        self.scope = scope
        super().__init__()


class ConfigurationUpdated(Message):
    """Message emitted when configuration is updated."""
    def __init__(self, config_key: str, old_value: Any, new_value: Any) -> None:
        self.config_key = config_key
        self.old_value = old_value
        self.new_value = new_value
        super().__init__()


class ConfigurationReset(Message):
    """Message emitted when configuration is reset to defaults."""
    def __init__(self, config_key: str, scope: ConfigurationScope) -> None:
        self.config_key = config_key
        self.scope = scope
        super().__init__()


class EditConfigurationModal(ModalScreen):
    """Modal screen for editing configuration values."""
    
    def __init__(self, entry: ConfigurationEntry) -> None:
        super().__init__()
        self.entry = entry
        self.value_input = self._create_value_input()
        self.description_input = Input(value=entry.description or "", placeholder="Enter description")
        
    def _create_value_input(self):
        """Create appropriate input widget based on value type."""
        if self.entry.type == "bool":
            return Switch(value=bool(self.entry.value))
        elif self.entry.type == "int":
            return Input(value=str(self.entry.value), placeholder="Enter integer value")
        elif self.entry.type == "list":
            return TextArea(
                text="\n".join(str(item) for item in (self.entry.value or [])),
                placeholder="Enter list values (one per line)"
            )
        else:
            return Input(value=str(self.entry.value), placeholder="Enter value")
    
    def compose(self) -> ComposeResult:
        with Container(id="edit-config-modal"):
            yield Static(f"Edit Configuration: {self.entry.key}", classes="modal-title")
            with ScrollableContainer():
                yield Static(f"**Key:** {self.entry.key}")
                yield Static(f"**Type:** {self.entry.type}")
                yield Static(f"**Scope:** {self.entry.scope.value}")
                if self.entry.default_value is not None:
                    yield Static(f"**Default:** {self.entry.default_value}")
                
                yield Static("Value:")
                yield self.value_input
                
                yield Static("Description:")
                yield self.description_input
                
                Horizontal(
                    Button("Save", id="save-btn", variant="primary"),
                    Button("Reset to Default", id="reset-btn", variant="warning"),
                    Button("Cancel", id="cancel-btn")
                )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-btn":
            new_value = self._parse_value()
            self.dismiss({
                "action": "save",
                "value": new_value,
                "description": self.description_input.value
            })
        elif event.button.id == "reset-btn":
            self.dismiss({
                "action": "reset",
                "value": self.entry.default_value,
                "description": self.entry.description
            })
        else:
            self.dismiss(None)
    
    def _parse_value(self) -> Any:
        """Parse the input value based on the configuration type."""
        if self.entry.type == "bool":
            return self.value_input.value
        elif self.entry.type == "int":
            try:
                return int(self.value_input.value)
            except ValueError:
                return self.entry.value
        elif self.entry.type == "list":
            text = self.value_input.text
            return [line.strip() for line in text.split('\n') if line.strip()]
        else:
            return self.value_input.value


class CreateConfigurationModal(ModalScreen):
    """Modal screen for creating new configuration entries."""
    
    def __init__(self, schema: ConfigurationSchema) -> None:
        super().__init__()
        self.schema = schema
        self.key_select = Select(options=[(key, key) for key in schema.keys.keys()])
        self.scope_select = Select(
            options=[
                ("Global", ConfigurationScope.GLOBAL),
                ("Workspace", ConfigurationScope.WORKSPACE),
                ("Environment", ConfigurationScope.ENVIRONMENT),
                ("Runtime", ConfigurationScope.RUNTIME),
            ],
            value=ConfigurationScope.WORKSPACE
        )
        self.value_input = Input(placeholder="Enter value")
        self.description_input = Input(placeholder="Enter description")
        
    def compose(self) -> ComposeResult:
        with Container(id="create-config-modal"):
            yield Static("Create Configuration Entry", classes="modal-title")
            with Vertical():
                Static("Configuration Key:")
                self.key_select
                
                Static("Scope:")
                self.scope_select
                
                Static("Value:")
                self.value_input
                
                Static("Description:")
                self.description_input
                
                Horizontal(
                    Button("Create", id="create-btn", variant="primary"),
                    Button("Cancel", id="cancel-btn")
                )
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create-btn":
            key = self.key_select.value
            schema_info = self.schema.keys[key]
            
            # Parse value based on schema type
            value = self._parse_value(self.value_input.value, schema_info.get("type", "string"))
            
            self.dismiss({
                "key": key,
                "scope": self.scope_select.value,
                "value": value,
                "description": self.description_input.value
            })
        else:
            self.dismiss(None)
    
    def _parse_value(self, value_str: str, value_type: str) -> Any:
        """Parse value based on type."""
        if value_type == "bool":
            return value_str.lower() in ("true", "yes", "1", "on")
        elif value_type == "int":
            try:
                return int(value_str)
            except ValueError:
                return value_str
        elif value_type == "list":
            return [item.strip() for item in value_str.split(",") if item.strip()]
        else:
            return value_str


class ValidationResultsModal(ModalScreen):
    """Modal screen for displaying configuration validation results."""
    
    def __init__(self, issues: List[ConfigurationValidationIssue]) -> None:
        super().__init__()
        self.issues = issues
        
    def compose(self) -> ComposeResult:
        with Container(id="validation-modal"):
            yield Static("Configuration Validation Results", classes="modal-title")
            with ScrollableContainer():
                if not self.issues:
                    yield Static("✅ All configuration entries are valid!", classes="success-message")
                else:
                    for issue in self.issues:
                        severity_icon = "❌" if issue.severity == "error" else "⚠️" if issue.severity == "warning" else "ℹ️"
                        yield Markdown(f"""
### {severity_icon} {issue.key}

**Severity:** {issue.severity}  
**Message:** {issue.message}  
**Current Value:** `{issue.current_value}`  
**Expected Type:** {issue.expected_type or 'unknown'}

{f"**Suggestion:** {issue.suggestion}" if issue.suggestion else ""}
---
                        """)
            yield Button("Close", id="close-btn")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


class ConfigurationInterfaceApp(App):
    """Main configuration interface application."""
    
    CSS_PATH = "configuration_interface.css"
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+r", "refresh", "Refresh"),
        Binding("ctrl+n", "create_config", "New Config"),
        Binding("ctrl+e", "edit_config", "Edit Config"),
        Binding("ctrl+d", "delete_config", "Delete Config"),
        Binding("ctrl+v", "validate_config", "Validate"),
        Binding("ctrl+s", "save_config", "Save"),
        Binding("up", "select_previous", "Previous"),
        Binding("down", "select_next", "Next"),
    ]
    
    configurations: reactive[List[ConfigurationEntry]] = reactive([])
    selected_config: reactive[Optional[ConfigurationEntry]] = reactive(None)
    current_scope: reactive[ConfigurationScope] = reactive(ConfigurationScope.WORKSPACE)
    log_entries: reactive[List[str]] = reactive([])
    is_loading: reactive[bool] = reactive(False)
    
    def __init__(
        self, 
        config_service: WorkspaceConfigurationService,
        config: ConfigurationInterfaceConfig
    ) -> None:
        super().__init__()
        self.config_service = config_service
        self.config = config
        self.refresh_timer: Optional[Timer] = None
        self.configuration_schema: Optional[ConfigurationSchema] = None
        
    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Static("Configuration Interface", classes="title"),
            Horizontal(
                Vertical(
                    Static("Scope Filter", classes="section-title"),
                    RadioSet(
                        RadioButton("Global", ConfigurationScope.GLOBAL, id="scope-global"),
                        RadioButton("Workspace", ConfigurationScope.WORKSPACE, id="scope-workspace"),
                        RadioButton("Environment", ConfigurationScope.ENVIRONMENT, id="scope-environment"),
                        RadioButton("Runtime", ConfigurationScope.RUNTIME, id="scope-runtime"),
                    ),
                    Static("Configuration Entries", classes="section-title"),
                    DataTable(id="config-table", classes="config-table"),
                    Horizontal(
                        Button("Refresh", id="refresh-btn", variant="default"),
                        Button("New", id="new-btn", variant="primary"),
                        Button("Edit", id="edit-btn", variant="success"),
                        Button("Delete", id="delete-btn", variant="error"),
                        Button("Validate", id="validate-btn", variant="warning"),
                        Button("Save", id="save-btn", variant="primary"),
                    ),
                    classes="config-panel"
                ),
                Vertical(
                    Tabs(
                        Tab("Details", id="details-tab"),
                        Tab("Activity Log", id="log-tab"),
                        Tab("Schema", id="schema-tab"),
                    ),
                    TabPane("Details", id="details-pane"),
                    TabPane("Activity Log", id="log-pane"),
                    TabPane("Schema", id="schema-pane"),
                    classes="info-panel"
                ),
                classes="main-content"
            ),
            classes="app-container"
        )
        yield Footer()
        
    def on_mount(self) -> None:
        """Initialize the application."""
        self.setup_config_table()
        self.setup_scope_selection()
        asyncio.create_task(self.load_configurations())
        self.start_auto_refresh()
        
    def setup_config_table(self) -> None:
        """Set up the configuration data table."""
        table = self.query_one("#config-table", DataTable)
        table.add_columns("Key", "Value", "Type", "Scope", "Status")
        table.cursor_type = "row"
        
    def setup_scope_selection(self) -> None:
        """Set up the scope selection radio buttons."""
        # Set default scope
        workspace_radio = self.query_one("#scope-workspace", RadioButton)
        workspace_radio.value = True
        
    async def load_configurations(self) -> None:
        """Load configuration entries."""
        self.is_loading = True
        try:
            # Get configuration schema
            self.configuration_schema = await self.config_service.get_configuration_schema()
            
            # Get configurations for current scope
            configs = await self.config_service.get_configurations_by_scope(self.current_scope)
            
            self.configurations = [
                ConfigurationEntry(
                    key=config.key,
                    value=config.value,
                    scope=config.scope,
                    type=config.value_type,
                    is_valid=True,  # Will be validated later
                    description=config.description
                )
                for config in configs
            ]
            
            await self.update_config_table()
            self.add_log_entry(f"Loaded {len(self.configurations)} configuration entries")
            
        except Exception as e:
            self.add_log_entry(f"Error loading configurations: {str(e)}")
        finally:
            self.is_loading = False
            
    async def update_config_table(self) -> None:
        """Update the configuration table with current data."""
        table = self.query_one("#config-table", DataTable)
        table.clear()
        
        for config in self.configurations:
            status = "✅ Valid" if config.is_valid else "❌ Invalid"
            value_str = str(config.value)[:50] + "..." if len(str(config.value)) > 50 else str(config.value)
            
            table.add_row(
                config.key,
                value_str,
                config.type,
                config.scope.value,
                status,
                key=config.key
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
            log_pane = self.query_one("#log-pane")
            log_pane.remove_children()
            log_widget = Log()
            log_pane.mount(log_widget)
            for entry in self.log_entries:
                log_widget.write_line(entry)
        except Exception:
            # Log widget might not be available yet
            pass
            
    def update_details_display(self) -> None:
        """Update the details panel with selected configuration info."""
        details_pane = self.query_one("#details-pane")
        details_pane.remove_children()
        
        if self.selected_config:
            details_content = Markdown(f"""
## Configuration Details

**Key:** {self.selected_config.key}  
**Value:** `{self.selected_config.value}`  
**Type:** {self.selected_config.type}  
**Scope:** {self.selected_config.scope.value}  
**Status:** {'✅ Valid' if self.selected_config.is_valid else '❌ Invalid'}

**Description:** {self.selected_config.description or 'No description'}

**Default Value:** `{self.selected_config.default_value or 'Not set'}`

**Environment Override:** `{self.selected_config.environment_override or 'None'}`
            """)
            details_pane.mount(details_content)
        else:
            details_pane.mount(Static("Select a configuration entry to view details"))
            
    def update_schema_display(self) -> None:
        """Update the schema display."""
        schema_pane = self.query_one("#schema-pane")
        schema_pane.remove_children()
        
        if self.configuration_schema:
            schema_content = Markdown(f"""
## Configuration Schema

**Version:** {self.configuration_schema.version}  
**Created:** {self.configuration_schema.created_at.strftime('%Y-%m-%d %H:%M:%S')}  
**Description:** {self.configuration_schema.description}

### Available Keys

{self._format_schema_keys()}
            """)
            schema_pane.mount(schema_content)
        else:
            schema_pane.mount(Static("No schema available"))
            
    def _format_schema_keys(self) -> str:
        """Format schema keys for display."""
        if not self.configuration_schema:
            return ""
            
        result = []
        for key, schema_info in self.configuration_schema.keys.items():
            result.append(f"""
**{key}**
- Type: {schema_info.get('type', 'string')}
- Required: {schema_info.get('required', False)}
- Default: `{schema_info.get('default', 'Not set')}`
- Description: {schema_info.get('description', 'No description')}
""")
        return "\n".join(result)
            
    def start_auto_refresh(self) -> None:
        """Start the auto-refresh timer."""
        if self.config.auto_refresh_interval > 0:
            self.refresh_timer = self.set_interval(
                self.config.auto_refresh_interval,
                lambda: asyncio.create_task(self.load_configurations())
            )
            
    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        """Handle scope selection change."""
        if event.radio_set.id in ["scope-global", "scope-workspace", "scope-environment", "scope-runtime"]:
            # Map radio button IDs to scopes
            scope_mapping = {
                "scope-global": ConfigurationScope.GLOBAL,
                "scope-workspace": ConfigurationScope.WORKSPACE,
                "scope-environment": ConfigurationScope.ENVIRONMENT,
                "scope-runtime": ConfigurationScope.RUNTIME,
            }
            self.current_scope = scope_mapping.get(event.radio_set.id, ConfigurationScope.WORKSPACE)
            asyncio.create_task(self.load_configurations())
                
    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle configuration row selection."""
        table = self.query_one("#config-table", DataTable)
        if event.data_table == table:
            key = event.row_key.value if event.row_key else None
            self.selected_config = next((c for c in self.configurations if c.key == key), None)
            self.update_details_display()
            
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "refresh-btn":
            asyncio.create_task(self.load_configurations())
        elif button_id == "new-btn" and self.configuration_schema:
            asyncio.create_task(self.show_create_config_modal())
        elif button_id == "edit-btn" and self.selected_config:
            asyncio.create_task(self.show_edit_config_modal())
        elif button_id == "delete-btn" and self.selected_config:
            asyncio.create_task(self.delete_selected_config())
        elif button_id == "validate-btn":
            asyncio.create_task(self.validate_configurations())
        elif button_id == "save-btn":
            asyncio.create_task(self.save_configurations())
            
    async def show_create_config_modal(self) -> None:
        """Show the create configuration modal."""
        if not self.configuration_schema:
            return
            
        modal = CreateConfigurationModal(self.configuration_schema)
        result = await self.push_screen_wait(modal)
        if result:
            await self.create_configuration(result)
            
    async def show_edit_config_modal(self) -> None:
        """Show the edit configuration modal."""
        if not self.selected_config:
            return
            
        modal = EditConfigurationModal(self.selected_config)
        result = await self.push_screen_wait(modal)
        if result:
            await self.update_configuration(result)
            
    async def create_configuration(self, config_data: Dict[str, Any]) -> None:
        """Create a new configuration entry."""
        try:
            await self.config_service.set_configuration(
                config_data["key"],
                config_data["value"],
                config_data["scope"],
                config_data["description"]
            )
            
            self.add_log_entry(f"Created configuration: {config_data['key']}")
            await self.load_configurations()
            
        except Exception as e:
            self.add_log_entry(f"Error creating configuration: {str(e)}")
            
    async def update_configuration(self, update_data: Dict[str, Any]) -> None:
        """Update an existing configuration entry."""
        if not self.selected_config:
            return
            
        try:
            old_value = self.selected_config.value
            
            if update_data["action"] == "save":
                await self.config_service.set_configuration(
                    self.selected_config.key,
                    update_data["value"],
                    self.selected_config.scope,
                    update_data["description"]
                )
                self.add_log_entry(f"Updated configuration: {self.selected_config.key}")
            elif update_data["action"] == "reset":
                await self.config_service.reset_configuration(
                    self.selected_config.key,
                    self.selected_config.scope
                )
                self.add_log_entry(f"Reset configuration: {self.selected_config.key}")
            
            await self.load_configurations()
            self.post_message(ConfigurationUpdated(
                self.selected_config.key,
                old_value,
                update_data["value"]
            ))
            
        except Exception as e:
            self.add_log_entry(f"Error updating configuration: {str(e)}")
            
    async def delete_selected_config(self) -> None:
        """Delete the selected configuration."""
        if not self.selected_config:
            return
            
        try:
            await self.config_service.delete_configuration(
                self.selected_config.key,
                self.selected_config.scope
            )
            
            self.add_log_entry(f"Deleted configuration: {self.selected_config.key}")
            await self.load_configurations()
            self.selected_config = None
            self.update_details_display()
            
        except Exception as e:
            self.add_log_entry(f"Error deleting configuration: {str(e)}")
            
    async def validate_configurations(self) -> None:
        """Validate all configuration entries."""
        try:
            issues = await self.config_service.validate_all_configurations()
            
            modal = ValidationResultsModal(issues)
            await self.push_screen(modal)
            
            self.add_log_entry(f"Validated configurations: {len(issues)} issues found")
            
            # Update validation status in the table
            for config in self.configurations:
                config.is_valid = not any(issue.key == config.key for issue in issues)
            
            await self.update_config_table()
            
        except Exception as e:
            self.add_log_entry(f"Error validating configurations: {str(e)}")
            
    async def save_configurations(self) -> None:
        """Save all configuration changes."""
        try:
            await self.config_service.save_configurations()
            self.add_log_entry("Configurations saved successfully")
            
        except Exception as e:
            self.add_log_entry(f"Error saving configurations: {str(e)}")
            
    async def action_quit(self) -> None:
        """Quit the application."""
        self.exit()
        
    def action_refresh(self) -> None:
        """Refresh the configuration list."""
        asyncio.create_task(self.load_configurations())
        
    def action_create_config(self) -> None:
        """Create a new configuration."""
        if self.configuration_schema:
            asyncio.create_task(self.show_create_config_modal())
        
    def action_edit_config(self) -> None:
        """Edit the selected configuration."""
        if self.selected_config:
            asyncio.create_task(self.show_edit_config_modal())
        
    def action_delete_config(self) -> None:
        """Delete the selected configuration."""
        if self.selected_config:
            asyncio.create_task(self.delete_selected_config())
        
    def action_validate_config(self) -> None:
        """Validate all configurations."""
        asyncio.create_task(self.validate_configurations())
        
    def action_save_config(self) -> None:
        """Save all configurations."""
        asyncio.create_task(self.save_configurations())
        
    def action_select_previous(self) -> None:
        """Select the previous configuration in the table."""
        table = self.query_one("#config-table", DataTable)
        table.action_cursor_up()
        
    def action_select_next(self) -> None:
        """Select the next configuration in the table."""
        table = self.query_one("#config-table", DataTable)
        table.action_cursor_down()


async def run_configuration_interface(
    config: Optional[ConfigurationInterfaceConfig] = None
) -> None:
    """Run the configuration interface TUI application."""
    if config is None:
        config = ConfigurationInterfaceConfig()
    
    # Initialize dependency container
    container = DIContainer()
    
    # Get configuration service
    config_service = container.resolve(WorkspaceConfigurationService)
    
    # Create and run the app
    app = ConfigurationInterfaceApp(config_service, config)
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(run_configuration_interface())