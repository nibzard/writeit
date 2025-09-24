"""Modern TUI execution interface with DDD integration.

Provides a rich terminal user interface for pipeline execution that leverages
the new Domain-Driven Design architecture for robust, scalable pipeline operations.
"""

import asyncio
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

import yaml
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
    DataTable,
    Log,
    Markdown,
    Tabs,
    Tab,
    TabPane,
    Input,
    RadioButton,
    RadioSet,
)
from textual.reactive import reactive
from textual.binding import Binding

from ...application.di_config import DIConfiguration
from ...application.services.pipeline_application_service import (
    PipelineApplicationService,
    PipelineExecutionRequest,
    PipelineExecutionResult,
    PipelineExecutionMode,
    PipelineSource,
)
from ...application.services.workspace_application_service import (
    WorkspaceApplicationService,
)
from ...shared.dependencies.container import Container as DIContainer


@dataclass
class TUIExecutionConfig:
    """Configuration for TUI execution interface."""
    
    auto_save_interval: int = 30  # Auto-save progress every 30 seconds
    max_log_entries: int = 1000   # Maximum log entries to keep
    enable_animations: bool = True # Enable UI animations
    show_token_usage: bool = True  # Show token usage metrics
    show_performance: bool = True  # Show performance metrics


class ExecutionProgressWidget(Container):
    """Widget showing pipeline execution progress."""
    
    current_step = reactive(-1)
    total_steps = reactive(0)
    execution_status = reactive("ready")
    
    def __init__(self, total_steps: int = 0):
        super().__init__()
        self.total_steps = total_steps
        self.step_start_time: Optional[datetime] = None
        self.token_usage: Dict[str, int] = {"input": 0, "output": 0}
        
    def compose(self) -> ComposeResult:
        yield Static("⚡ Pipeline Execution", classes="section-header")
        
        # Progress bar and status
        yield ProgressBar(id="execution-progress", total=100)
        yield Static("Ready to start", id="execution-status")
        
        # Token usage display
        with Horizontal(classes="metrics-container"):
            yield Static("📊 Token Usage:", classes="metric-label")
            yield Static("0 → 0", id="token-usage", classes="metric-value")
        
        # Execution metrics
        with Horizontal(classes="metrics-container"):
            yield Static("⏱️ Duration:", classes="metric-label")
            yield Static("0:00", id="execution-duration", classes="metric-value")
            
            yield Static("🎯 Steps:", classes="metric-label")
            yield Static("0/0", id="step-counter", classes="metric-value")
    
    def watch_current_step(self) -> None:
        """Update progress when step changes."""
        self._update_progress()
        
    def watch_total_steps(self) -> None:
        """Update progress when total steps changes."""
        self._update_progress()
        
    def watch_execution_status(self) -> None:
        """Update status display."""
        status_widget = self.query_one("#execution-status")
        status_widget.update(self.execution_status)
        
    def _update_progress(self) -> None:
        """Update progress bar and metrics."""
        if self.total_steps > 0:
            progress = int((self.current_step / self.total_steps) * 100)
        else:
            progress = 0
            
        progress_bar = self.query_one("#execution-progress")
        progress_bar.update(progress=progress)
        
        # Update step counter
        step_counter = self.query_one("#step-counter")
        step_counter.update(f"{self.current_step}/{self.total_steps}")
        
        # Update duration if timer is running
        if self.step_start_time:
            duration = datetime.now() - self.step_start_time
            duration_str = str(duration).split('.')[0]  # Remove microseconds
            duration_widget = self.query_one("#execution-duration")
            duration_widget.update(duration_str)
    
    def update_token_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Update token usage display."""
        self.token_usage["input"] = input_tokens
        self.token_usage["output"] = output_tokens
        
        token_widget = self.query_one("#token-usage")
        token_widget.update(f"{input_tokens:,} → {output_tokens:,}")
    
    def start_execution(self, total_steps: int) -> None:
        """Start execution tracking."""
        self.total_steps = total_steps
        self.current_step = 0
        self.step_start_time = datetime.now()
        self.execution_status = "🚀 Executing..."
        
    def complete_step(self) -> None:
        """Mark current step as completed."""
        self.current_step += 1
        if self.current_step >= self.total_steps:
            self.execution_status = "✅ Completed"
    
    def set_error(self, error_message: str) -> None:
        """Set error state."""
        self.execution_status = f"❌ Error: {error_message}"


class StepExecutionWidget(Container):
    """Widget for executing and displaying a single pipeline step."""
    
    def __init__(self, step_name: str, step_description: str):
        super().__init__()
        self.step_name = step_name
        self.step_description = step_description
        self.responses: List[str] = []
        self.current_response: str = ""
        
    def compose(self) -> ComposeResult:
        yield Static(f"📝 {self.step_name}", classes="step-header")
        yield Static(self.step_description, classes="step-description")
        
        # Response area with tabs for different views
        with Tabs():
            yield Tab("Response", id="response-tab")
            yield Tab("Raw", id="raw-tab")
            yield Tab("Metadata", id="metadata-tab")
        
        with TabPane("Response", id="response-pane"):
            yield Markdown(
                "Generating response...",
                id="response-markdown",
                classes="response-content"
            )
        
        with TabPane("Raw", id="raw-pane"):
            yield TextArea(
                "",
                read_only=True,
                id="response-raw",
                classes="response-raw"
            )
        
        with TabPane("Metadata", id="metadata-pane"):
            yield DataTable(id="metadata-table", classes="metadata-table")
        
        # User interaction area
        with Vertical(classes="interaction-area"):
            yield Static("💬 Your feedback (optional):")
            yield TextArea(
                placeholder="Provide feedback to guide the next step...",
                id="user-feedback",
                classes="feedback-input"
            )
            
            with Horizontal(classes="action-buttons"):
                yield Button("🔄 Regenerate", id="regenerate-btn", variant="warning")
                yield Button("⏭️ Continue", id="continue-btn", variant="success", disabled=True)
                yield Button("⏸️ Pause", id="pause-btn", variant="default")
    
    def on_mount(self) -> None:
        """Initialize metadata table."""
        table = self.query_one("#metadata-table")
        table.add_columns("Property", "Value")
        table.add_row("Step", self.step_name)
        table.add_row("Status", "Pending")
        table.add_row("Model", "N/A")
        table.add_row("Tokens", "N/A")
        table.add_row("Duration", "N/A")
    
    def update_response(self, response: str, metadata: Dict[str, Any]) -> None:
        """Update the response display."""
        self.current_response = response
        
        # Update markdown
        markdown_widget = self.query_one("#response-markdown")
        markdown_widget.update(response)
        
        # Update raw text
        raw_widget = self.query_one("#response-raw")
        raw_widget.text = response
        
        # Update metadata
        self._update_metadata(metadata)
        
        # Enable continue button
        continue_btn = self.query_one("#continue-btn")
        continue_btn.disabled = False
    
    def _update_metadata(self, metadata: Dict[str, Any]) -> None:
        """Update metadata table."""
        table = self.query_one("#metadata-table")
        table.clear()
        
        # Add step info
        table.add_row("Step", self.step_name)
        table.add_row("Status", metadata.get("status", "Completed"))
        
        # Add model info
        if "model" in metadata:
            table.add_row("Model", metadata["model"])
        
        # Add token usage
        if "token_usage" in metadata:
            usage = metadata["token_usage"]
            table.add_row(
                "Tokens", 
                f"{usage.get('input_tokens', 0)} → {usage.get('output_tokens', 0)}"
            )
        
        # Add duration
        if "duration" in metadata:
            table.add_row("Duration", str(metadata["duration"]))
        
        # Add additional metadata
        for key, value in metadata.items():
            if key not in ["status", "model", "token_usage", "duration"]:
                table.add_row(key.replace("_", " ").title(), str(value))
    
    def get_feedback(self) -> str:
        """Get user feedback."""
        feedback_widget = self.query_one("#user-feedback")
        return feedback_widget.text


class PipelineInputsWidget(Container):
    """Widget for collecting pipeline inputs."""
    
    def __init__(self, inputs: List[Dict[str, Any]]):
        super().__init__()
        self.inputs = inputs
        self.values: Dict[str, Any] = {}
        
    def compose(self) -> ComposeResult:
        yield Static("📝 Pipeline Configuration", classes="section-header")
        
        # Create input fields based on configuration
        for input_config in self.inputs:
            yield Static(f"**{input_config['label']}**{'*' if input_config.get('required', False) else ''}")
            
            if input_config.get('help'):
                yield Static(f"[dim]{input_config['help']}[/dim]", classes="help-text")
            
            input_id = f"input-{input_config['key']}"
            
            if input_config['type'] == 'text':
                yield TextArea(
                    placeholder=input_config.get('placeholder', ''),
                    id=input_id,
                    classes="input-field"
                )
            elif input_config['type'] == 'choice':
                options = [(opt['label'], opt['value']) for opt in input_config.get('options', [])]
                yield Select(options, id=input_id, classes="input-field")
            elif input_config['type'] == 'number':
                yield Input(placeholder=input_config.get('placeholder', ''), id=input_id, classes="input-field")
            elif input_config['type'] == 'boolean':
                with RadioSet(id=input_id):
                    yield RadioButton("Yes", value=True, id=f"{input_id}-yes")
                    yield RadioButton("No", value=False, id=f"{input_id}-no")
        
        # Action buttons
        with Horizontal(classes="action-buttons"):
            yield Button("🚀 Start Pipeline", id="start-btn", variant="success")
            yield Button("📋 Validate", id="validate-btn", variant="default")
    
    def collect_values(self) -> Dict[str, Any]:
        """Collect all input values."""
        values = {}
        
        for input_config in self.inputs:
            input_id = f"input-{input_config['key']}"
            
            try:
                if input_config['type'] == 'text':
                    widget = self.query_one(f"#{input_id}", TextArea)
                    values[input_config['key']] = widget.text
                elif input_config['type'] == 'choice':
                    widget = self.query_one(f"#{input_id}", Select)
                    values[input_config['key']] = widget.value
                elif input_config['type'] == 'number':
                    widget = self.query_one(f"#{input_id}", Input)
                    values[input_config['key']] = float(widget.value) if widget.value else None
                elif input_config['type'] == 'boolean':
                    widget = self.query_one(f"#{input_id}", RadioSet)
                    values[input_config['key']] = widget.pressed.value
            except Exception:
                # Use default value if widget not found or error
                values[input_config['key']] = input_config.get('default')
        
        return values
    
    def validate_inputs(self) -> tuple[bool, List[str]]:
        """Validate all inputs."""
        errors = []
        values = self.collect_values()
        
        for input_config in self.inputs:
            key = input_config['key']
            value = values.get(key)
            
            # Check required fields
            if input_config.get('required', False) and not value:
                errors.append(f"{input_config['label']} is required")
            
            # Type-specific validation
            if value is not None:
                if input_config['type'] == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"{input_config['label']} must be a number")
                elif input_config['type'] == 'choice' and value not in [opt['value'] for opt in input_config.get('options', [])]:
                    errors.append(f"{input_config['label']} must be one of the provided options")
        
        return len(errors) == 0, errors


class ExecutionLogWidget(Container):
    """Widget for displaying execution logs."""
    
    def __init__(self, max_entries: int = 1000):
        super().__init__()
        self.max_entries = max_entries
        
    def compose(self) -> ComposeResult:
        yield Static("📋 Execution Log", classes="section-header")
        yield Log(id="execution-log", classes="log-content", max_lines=self.max_entries)
    
    def log_message(self, level: str, message: str) -> None:
        """Add a message to the log."""
        log_widget = self.query_one("#execution-log")
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color code based on level
        if level.lower() == "error":
            log_widget.write_line(f"[{timestamp}] [ERROR] {message}", style="red")
        elif level.lower() == "warning":
            log_widget.write_line(f"[{timestamp}] [WARN] {message}", style="yellow")
        elif level.lower() == "success":
            log_widget.write_line(f"[{timestamp}] [SUCCESS] {message}", style="green")
        else:
            log_widget.write_line(f"[{timestamp}] [INFO] {message}")
    
    def clear_log(self) -> None:
        """Clear the log."""
        log_widget = self.query_one("#execution-log")
        log_widget.clear()


class ModernPipelineRunnerApp(App[None]):
    """Modern TUI application for pipeline execution with DDD integration."""
    
    CSS = """
    .section-header {
        text-style: bold;
        color: $accent;
        margin: 1 0;
        border-bottom: solid $primary 1px;
        padding-bottom: 1;
    }
    
    .step-header {
        text-style: bold;
        color: $secondary;
        margin: 1 0;
    }
    
    .step-description {
        color: $text-muted;
        margin: 0 0 1 0;
        font-style: italic;
    }
    
    .help-text {
        color: $text-muted;
        margin: 0 0 1 2;
        font-size: 0.9em;
    }
    
    .input-field {
        margin: 0 0 1 0;
        min-height: 3;
    }
    
    .feedback-input {
        height: 6;
        margin: 0 0 1 0;
    }
    
    .response-content {
        height: 20;
        border: solid $primary 1px;
        margin: 1 0;
    }
    
    .response-raw {
        height: 20;
        border: solid $warning 1px;
        margin: 1 0;
        font-family: monospace;
    }
    
    .metadata-table {
        height: 15;
        margin: 1 0;
    }
    
    .log-content {
        height: 15;
        border: solid $surface 1px;
        margin: 1 0;
        font-family: monospace;
        font-size: 0.9em;
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
    
    .metrics-container {
        height: auto;
        margin: 0 1;
    }
    
    .metric-label {
        color: $text-muted;
        margin: 0 1 0 0;
    }
    
    .metric-value {
        color: $accent;
        font-weight: bold;
    }
    
    .interaction-area {
        margin: 1 0;
    }
    
    /* Focus indicators */
    TextArea:focus, Input:focus, Select:focus {
        border: solid $accent 2px;
    }
    
    Button:focus {
        border: solid $accent 2px;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+s", "save_progress", "Save Progress"),
        Binding("ctrl+l", "toggle_log", "Toggle Log"),
        Binding("ctrl+r", "restart", "Restart Pipeline"),
        Binding("f1", "show_help", "Help"),
        Binding("tab", "focus_next", "Next Field"),
        Binding("shift+tab", "focus_previous", "Previous Field"),
    ]
    
    def __init__(self, pipeline_path: Path, workspace_name: str, config: TUIExecutionConfig = None):
        super().__init__()
        self.pipeline_path = pipeline_path
        self.workspace_name = workspace_name
        self.config = config or TUIExecutionConfig()
        
        # DDD Services
        self.di_container: Optional[DIContainer] = None
        self.pipeline_service: Optional[PipelineApplicationService] = None
        self.workspace_service: Optional[WorkspaceApplicationService] = None
        
        # Execution state
        self.execution_id: Optional[str] = None
        self.current_step_index = 0
        self.pipeline_inputs: Dict[str, Any] = {}
        self.step_results: Dict[str, Any] = {}
        self.execution_complete = False
        
        # UI state
        self.current_phase = "loading"  # loading, inputs, execution, complete
        self.show_log_panel = False
        
    async def on_mount(self) -> None:
        """Initialize the application."""
        await self.initialize_services()
        await self.load_pipeline()
        
    async def initialize_services(self) -> None:
        """Initialize DDD services."""
        try:
            # Create DI container
            self.di_container = DIConfiguration.create_container(
                base_path=self.pipeline_path.parent,
                workspace_name=self.workspace_name
            )
            
            # Get application services
            self.pipeline_service = self.di_container.resolve(PipelineApplicationService)
            self.workspace_service = self.di_container.resolve(WorkspaceApplicationService)
            
            self.log_message("INFO", "Services initialized successfully")
            
        except Exception as e:
            self.log_message("ERROR", f"Failed to initialize services: {e}")
            raise
    
    async def load_pipeline(self) -> None:
        """Load pipeline configuration."""
        try:
            # Load pipeline YAML
            with open(self.pipeline_path, 'r') as f:
                pipeline_config = yaml.safe_load(f)
            
            # Validate pipeline structure
            if not self.pipeline_service:
                raise RuntimeError("Pipeline service not initialized")
            
            # Show inputs phase
            await self.show_inputs_phase(pipeline_config)
            
        except Exception as e:
            self.log_message("ERROR", f"Failed to load pipeline: {e}")
            await self.show_error(f"Failed to load pipeline: {e}")
    
    async def show_inputs_phase(self, pipeline_config: Dict[str, Any]) -> None:
        """Show the input collection phase."""
        self.current_phase = "inputs"
        
        # Update main content
        main_content = self.query_one("#main-content")
        await main_content.remove_children()
        
        # Create inputs widget
        inputs_widget = PipelineInputsWidget(pipeline_config.get("inputs", []))
        await main_content.mount(inputs_widget)
        
        # Focus first input
        self.call_after_refresh(self._focus_first_input)
        
        self.log_message("INFO", "Pipeline loaded - ready for input")
    
    async def show_execution_phase(self) -> None:
        """Show the pipeline execution phase."""
        self.current_phase = "execution"
        
        # Create execution request
        execution_request = PipelineExecutionRequest(
            pipeline_name=self.pipeline_path.stem,
            workspace_name=self.workspace_name,
            source=PipelineSource.LOCAL,
            template_path=self.pipeline_path,
            mode=PipelineExecutionMode.TUI,
            inputs=self.pipeline_inputs
        )
        
        # Update main content
        main_content = self.query_one("#main-content")
        await main_content.remove_children()
        
        # Create execution layout
        with Vertical():
            # Progress widget
            progress_widget = ExecutionProgressWidget()
            await main_content.mount(progress_widget)
            
            # Dynamic step area
            step_container = Container(id="step-container")
            await main_content.mount(step_container)
            
            # Log widget (initially hidden if not configured)
            if self.show_log_panel:
                log_widget = ExecutionLogWidget(self.config.max_log_entries)
                await main_content.mount(log_widget)
        
        # Start execution
        await self.execute_pipeline(execution_request, progress_widget)
    
    async def execute_pipeline(
        self, 
        request: PipelineExecutionRequest,
        progress_widget: ExecutionProgressWidget
    ) -> None:
        """Execute pipeline with real-time updates."""
        if not self.pipeline_service:
            self.log_message("ERROR", "Pipeline service not available")
            return
        
        try:
            self.execution_id = str(uuid.uuid4())
            progress_widget.start_execution(len(request.inputs or {}))
            
            self.log_message("INFO", f"Starting pipeline execution: {request.pipeline_name}")
            
            # Execute pipeline with streaming
            async for result in self.pipeline_service.execute_pipeline(request):
                await self._handle_execution_result(result, progress_widget)
                
                if result.execution_status.value in ["completed", "failed", "cancelled"]:
                    break
            
            self.log_message("INFO", "Pipeline execution completed")
            await self.show_completion_phase()
            
        except Exception as e:
            self.log_message("ERROR", f"Pipeline execution failed: {e}")
            progress_widget.set_error(str(e))
    
    async def _handle_execution_result(
        self, 
        result: PipelineExecutionResult,
        progress_widget: ExecutionProgressWidget
    ) -> None:
        """Handle an execution result."""
        # Update progress
        if result.step_results:
            completed_steps = len(result.step_results)
            progress_widget.current_step = completed_steps
        
        # Update token usage
        if "token_usage" in result.execution_metrics:
            token_usage = result.execution_metrics["token_usage"]
            progress_widget.update_token_usage(
                token_usage.get("input_tokens", 0),
                token_usage.get("output_tokens", 0)
            )
        
        # Handle errors
        if result.errors:
            for error in result.errors:
                self.log_message("ERROR", error)
        
        # Handle warnings
        if result.warnings:
            for warning in result.warnings:
                self.log_message("WARNING", warning)
        
        # Update current step UI
        if result.step_results and self.current_phase == "execution":
            await self._update_current_step(result.step_results)
    
    async def _update_current_step(self, step_results: Dict[str, Any]) -> None:
        """Update the current step widget."""
        step_container = self.query_one("#step-container")
        
        # Get the most recent step result
        latest_step = list(step_results.keys())[-1] if step_results else None
        if latest_step:
            step_data = step_results[latest_step]
            
            # Create or update step widget
            step_widget = StepExecutionWidget(
                step_name=latest_step,
                step_description=step_data.get("description", "")
            )
            
            await step_container.remove_children()
            await step_container.mount(step_widget)
            
            # Update with step data
            if "response" in step_data:
                step_widget.update_response(
                    step_data["response"],
                    step_data.get("metadata", {})
                )
    
    async def show_completion_phase(self) -> None:
        """Show the pipeline completion phase."""
        self.current_phase = "complete"
        self.execution_complete = True
        
        # Update main content
        main_content = self.query_one("#main-content")
        await main_content.remove_children()
        
        # Show completion summary
        with Vertical():
            yield Static("🎉 Pipeline Complete!", classes="section-header")
            
            # Summary statistics
            with Horizontal(classes="metrics-container"):
                yield Static("📊 Execution Summary:", classes="metric-label")
                
            # Final results
            if self.step_results:
                final_output = self.step_results.get("polish", "Pipeline completed successfully!")
                yield Markdown(final_output, classes="final-output")
            
            # Action buttons
            with Horizontal(classes="action-buttons"):
                yield Button("📁 Export Results", id="export-btn", variant="primary")
                yield Button("🔄 New Pipeline", id="restart-btn", variant="default")
                yield Button("📋 View Log", id="log-btn", variant="default")
                yield Button("❌ Exit", id="exit-btn", variant="default")
    
    def compose(self) -> ComposeResult:
        """Create the application layout."""
        yield Header()
        
        with ScrollableContainer(id="main-content"):
            yield Static("🚀 WriteIt Pipeline Runner", classes="section-header")
            yield Static("Loading pipeline...", id="status-message")
        
        yield Footer()
    
    def log_message(self, level: str, message: str) -> None:
        """Log a message (if log widget is available)."""
        try:
            log_widget = self.query_one(ExecutionLogWidget)
            log_widget.log_message(level, message)
        except Exception:
            # Log widget may not be mounted yet
            pass
    
    async def show_error(self, message: str) -> None:
        """Show an error message."""
        main_content = self.query_one("#main-content")
        await main_content.remove_children()
        
        await main_content.mount(Static(f"❌ Error: {message}", classes="error"))
        await main_content.mount(Button("Exit", id="exit-btn", variant="default"))
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        if button_id == "start-btn":
            await self.handle_start_pipeline()
        elif button_id == "validate-btn":
            await self.handle_validate_inputs()
        elif button_id == "continue-btn":
            await self.handle_continue_step()
        elif button_id == "regenerate-btn":
            await self.handle_regenerate_step()
        elif button_id == "restart-btn":
            await self.handle_restart()
        elif button_id == "export-btn":
            await self.handle_export()
        elif button_id == "log-btn":
            self.show_log_panel = not self.show_log_panel
        elif button_id == "exit-btn":
            self.exit()
    
    async def handle_start_pipeline(self) -> None:
        """Handle starting the pipeline."""
        inputs_widget = self.query_one(PipelineInputsWidget)
        
        # Validate inputs
        valid, errors = inputs_widget.validate_inputs()
        if not valid:
            for error in errors:
                self.log_message("ERROR", error)
            return
        
        # Collect inputs
        self.pipeline_inputs = inputs_widget.collect_values()
        self.log_message("INFO", "Inputs validated - starting execution")
        
        # Start execution
        await self.show_execution_phase()
    
    async def handle_validate_inputs(self) -> None:
        """Handle input validation."""
        inputs_widget = self.query_one(PipelineInputsWidget)
        valid, errors = inputs_widget.validate_inputs()
        
        if valid:
            self.log_message("SUCCESS", "All inputs are valid")
        else:
            for error in errors:
                self.log_message("ERROR", error)
    
    async def handle_continue_step(self) -> None:
        """Handle continuing to the next step."""
        # Implementation would handle step continuation
        self.log_message("INFO", "Continuing to next step")
    
    async def handle_regenerate_step(self) -> None:
        """Handle regenerating the current step."""
        # Implementation would handle step regeneration
        self.log_message("INFO", "Regenerating current step")
    
    async def handle_restart(self) -> None:
        """Handle restarting the pipeline."""
        self.execution_id = None
        self.current_step_index = 0
        self.pipeline_inputs = {}
        self.step_results = {}
        self.execution_complete = False
        
        await self.load_pipeline()
    
    async def handle_export(self) -> None:
        """Handle exporting results."""
        # Implementation would handle result export
        self.log_message("INFO", "Exporting results")
    
    def action_save_progress(self) -> None:
        """Save current progress."""
        self.log_message("INFO", "Progress saved")
    
    def action_toggle_log(self) -> None:
        """Toggle log panel visibility."""
        self.show_log_panel = not self.show_log_panel
        # Implementation would show/hide log panel
    
    def action_restart(self) -> None:
        """Restart the pipeline."""
        asyncio.create_task(self.handle_restart())
    
    def action_focus_next(self) -> None:
        """Focus next interactive element."""
        self.screen.focus_next()
    
    def action_focus_previous(self) -> None:
        """Focus previous interactive element."""
        self.screen.focus_previous()
    
    def _focus_first_input(self) -> None:
        """Focus the first input field."""
        try:
            first_input = self.query_one("TextArea, Select, Input")
            if first_input:
                first_input.focus()
        except Exception:
            pass


async def run_modern_pipeline_tui(
    pipeline_path: Path, 
    workspace_name: str,
    config: TUIExecutionConfig = None
) -> None:
    """Run the modern pipeline TUI application."""
    app = ModernPipelineRunnerApp(pipeline_path, workspace_name, config)
    await app.run_async()