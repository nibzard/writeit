"""Advanced Pipeline Execution Interface for WriteIt TUI.

Provides sophisticated pipeline execution interface with real-time updates,
step-by-step execution, token tracking, and comprehensive monitoring.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timedelta

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
    ContentSwitcher,
)
from textual.reactive import reactive
from textual.binding import Binding
from textual.screen import Screen
from textual.message import Message
from textual.timer import Timer
import asyncio
from textual.css.query import NoMatches

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

from ....application.services.pipeline_application_service import (
    PipelineApplicationService,
    PipelineExecutionRequest,
    PipelineExecutionResult,
    PipelineExecutionMode,
    PipelineSource,
)

from ....domains.workspace.value_objects import WorkspaceName
from ....domains.pipeline.value_objects import PipelineId
from ....domains.pipeline.value_objects.execution_status import ExecutionStatus
from ....shared.dependencies.container import Container


class ExecutionPhase(str, Enum):
    """Pipeline execution phases."""
    INITIALIZATION = "initialization"
    INPUT_COLLECTION = "input_collection"
    STEP_EXECUTION = "step_execution"
    RESULT_GENERATION = "result_generation"
    COMPLETION = "completion"
    ERROR = "error"


@dataclass
class ExecutionMetrics:
    """Metrics for pipeline execution."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    total_duration: Optional[timedelta] = None
    total_tokens: int = 0
    total_cost: float = 0.0
    steps_completed: int = 0
    steps_failed: int = 0
    average_step_duration: Optional[float] = None
    throughput: Optional[float] = None  # steps per minute


@dataclass
class StepExecutionDetail:
    """Detailed information about a step execution."""
    step_id: str
    step_name: str
    status: ExecutionStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[timedelta] = None
    model_used: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    error_message: Optional[str] = None
    retry_count: int = 0
    response_preview: Optional[str] = None
    user_feedback: Optional[str] = None


class AdvancedPipelineExecutionScreen(Screen):
    """Advanced pipeline execution screen with real-time monitoring."""
    
    CSS = """
    .advanced-execution {
        height: 100%;
        layout: grid;
        grid-size: 1 3;
        grid-columns: 1fr;
        grid-rows: auto 1fr auto;
    }
    
    .execution-header {
        grid-row: 1;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .execution-main {
        grid-row: 2;
        height: 1fr;
        layout: grid;
        grid-size: 3 1;
        grid-columns: 1fr 2fr 1fr;
        grid-rows: 1fr;
    }
    
    .execution-sidebar {
        grid-column: 1;
        grid-row: 1;
        padding: 1;
        border: solid $accent;
    }
    
    .execution-center {
        grid-column: 2;
        grid-row: 1;
        padding: 1;
    }
    
    .execution-right {
        grid-column: 3;
        grid-row: 1;
        padding: 1;
        border: solid $primary;
    }
    
    .execution-footer {
        grid-row: 3;
        height: auto;
        background: $surface;
        border: solid $primary;
        padding: 1;
    }
    
    .pipeline-info {
        background: $surface;
        padding: 1;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    .execution-status {
        background: $surface;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .metrics-panel {
        background: $surface;
        padding: 1;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    .step-list {
        height: 20;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .execution-log {
        height: 15;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    .output-area {
        height: 20;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .input-panel {
        background: $surface;
        padding: 1;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    .controls-panel {
        background: $surface;
        padding: 1;
        border: solid $primary;
        margin-bottom: 1;
    }
    
    .progress-container {
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
    
    .status-indicator {
        text-style: bold;
        padding: 0 1;
    }
    
    .status-running {
        color: $warning;
    }
    
    .status-completed {
        color: $success;
    }
    
    .status-error {
        color: $error;
    }
    
    .status-pending {
        color: $primary;
    }
    
    .metric-value {
        text-style: bold;
        color: $accent;
    }
    
    .step-status {
        text-style: bold;
        padding: 0 0.5;
    }
    
    .step-pending {
        color: $text-muted;
    }
    
    .step-running {
        color: $warning;
    }
    
    .step-completed {
        color: $success;
    }
    
    .step-failed {
        color: $error;
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
    
    .warning-message {
        background: $warning;
        color: $text;
        padding: 1;
        border: solid $warning;
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+p", "pause", "Pause/Resume"),
        Binding("ctrl+s", "stop", "Stop"),
        Binding("ctrl+r", "restart", "Restart"),
        Binding("ctrl+l", "toggle_log", "Toggle Log"),
        Binding("f1", "show_help", "Help"),
        Binding("ctrl+left", "previous_step", "Previous Step"),
        Binding("ctrl+right", "next_step", "Next Step"),
    ]
    
    def __init__(self, context: TUIContext, template: PipelineTemplateInfo):
        super().__init__()
        self.context = context
        self.template = template
        self.pipeline_service: Optional[PipelineApplicationService] = None
        
        if context.container:
            self.pipeline_service = context.container.resolve(PipelineApplicationService)
        
        # Execution state
        self.execution_phase = ExecutionPhase.INITIALIZATION
        self.execution_id = str(uuid.uuid4())
        self.metrics = ExecutionMetrics()
        self.step_details: Dict[str, StepExecutionDetail] = {}
        self.current_step_index = 0
        self.is_paused = False
        self.is_stopped = False
        self.show_log_panel = True
        
        # Input data
        self.input_data: Dict[str, Any] = {}
        
        # Worker for execution
        self.execution_worker: Optional[Worker] = None
        self.update_timer: Optional[Timer] = None
        
        # Bind context to this execution
        context.pipeline_id = template.id
        context.execution_context["execution_id"] = self.execution_id
        context.navigation_state = NavigationState.EXECUTION
    
    def compose(self) -> ComposeResult:
        """Create the advanced execution layout."""
        
        with Container(classes="advanced-execution"):
            # Header
            with Container(classes="execution-header"):
                with Horizontal():
                    yield Static(f"🚀 {self.template.name}", classes="section-header")
                    yield Static(f"ID: {self.execution_id[:8]}...", classes="execution-id")
                    yield Static("Workspace: " + self.context.workspace_name, classes="workspace-name")
                    
                    # Status indicator
                    yield Static(
                        self.get_status_text(),
                        classes=f"status-indicator status-{self.get_status_class()}"
                    )
                
                # Progress bar
                with Container(classes="progress-container"):
                    yield ProgressBar(
                        id="execution-progress",
                        total=100,
                        show_percentage=True,
                        show_eta=True
                    )
            
            # Main content area
            with Container(classes="execution-main"):
                # Left sidebar - Steps and metrics
                with Container(classes="execution-sidebar"):
                    # Pipeline info
                    with Container(classes="pipeline-info"):
                        yield Static("📋 Pipeline Info", classes="section-header")
                        yield Static(f"Name: {self.template.name}")
                        yield Static(f"Steps: {self.template.steps_count}")
                        yield Static(f"Source: {self.template.source.value}")
                        if self.template.estimated_duration:
                            yield Static(f"Est. Duration: {self.template.estimated_duration}s")
                    
                    # Execution metrics
                    with Container(classes="metrics-panel"):
                        yield Static("📊 Metrics", classes="section-header")
                        yield Static("Duration: ", classes="metric-label")
                        yield Static("0:00", id="duration-metric", classes="metric-value")
                        yield Static("Tokens: ", classes="metric-label")
                        yield Static("0", id="tokens-metric", classes="metric-value")
                        yield Static("Cost: ", classes="metric-label")
                        yield Static("$0.00", id="cost-metric", classes="metric-value")
                        yield Static("Steps: ", classes="metric-label")
                        yield Static("0/0", id="steps-metric", classes="metric-value")
                    
                    # Step list
                    yield Static("📝 Steps", classes="section-header")
                    with Container(classes="step-list"):
                        yield DataTable(id="step-table")
                
                # Center - Main execution area
                with Container(classes="execution-center"):
                    # Content switcher for different phases
                    with ContentSwitcher(id="execution-content", initial="input-phase"):
                        # Input collection phase
                        with Container(id="input-phase"):
                            yield Static("📝 Pipeline Inputs", classes="section-header")
                            yield Static(self.template.description)
                            
                            with Container(classes="input-panel", id="input-panel"):
                                yield Static("Input fields will be rendered here...")
                            
                            with Horizontal(classes="action-buttons"):
                                yield Button("Start Execution", id="start-execution", variant="success")
                                yield Button("Back", id="back-to-templates", variant="default")
                        
                        # Step execution phase
                        with Container(id="step-phase"):
                            yield Static("⚡ Step Execution", classes="section-header")
                            
                            with Container(id="current-step-info"):
                                yield Static("Select a step to execute")
                            
                            with Container(classes="output-area"):
                                yield TextArea(
                                    id="step-output",
                                    read_only=True,
                                    placeholder="Step output will appear here..."
                                )
                            
                            with Horizontal(classes="action-buttons"):
                                yield Button("Execute Step", id="execute-step", variant="success")
                                yield Button("Skip Step", id="skip-step", variant="warning")
                                yield Button("Retry Step", id="retry-step", variant="default", disabled=True)
                        
                        # Result generation phase
                        with Container(id="result-phase"):
                            yield Static("🎯 Result Generation", classes="section-header")
                            
                            with Container(classes="output-area"):
                                yield TextArea(
                                    id="final-output",
                                    read_only=True,
                                    placeholder="Final results will appear here..."
                                )
                            
                            with Horizontal(classes="action-buttons"):
                                yield Button("Regenerate", id="regenerate-result", variant="warning")
                                yield Button("Export", id="export-result", variant="primary")
                                yield Button("New Pipeline", id="new-pipeline", variant="default")
                        
                        # Completion phase
                        with Container(id="completion-phase"):
                            yield Static("✅ Execution Complete", classes="section-header")
                            
                            with Container(id="completion-summary"):
                                yield Static("Execution summary will appear here...")
                            
                            with Horizontal(classes="action-buttons"):
                                yield Button("View Report", id="view-report", variant="primary")
                                yield Button("Export Results", id="export-results", variant="success")
                                yield Button("New Pipeline", id="new-pipeline-2", variant="default")
                    
                    # Execution log (toggleable)
                    if self.show_log_panel:
                        with Container(classes="execution-log"):
                            yield Static("📋 Execution Log", classes="section-header")
                            yield Log(id="execution-log", classes="log-content")
                
                # Right sidebar - Controls and info
                with Container(classes="execution-right"):
                    # Controls panel
                    with Container(classes="controls-panel"):
                        yield Static("🎮 Controls", classes="section-header")
                        
                        with Horizontal(classes="action-buttons"):
                            yield Button("▶️ Start", id="control-start", variant="success")
                            yield Button("⏸️ Pause", id="control-pause", variant="warning", disabled=True)
                            yield Button("⏹️ Stop", id="control-stop", variant="error", disabled=True)
                            yield Button("🔄 Restart", id="control-restart", variant="default", disabled=True)
                        
                        # Quick actions
                        yield Static("Quick Actions", classes="section-header")
                        yield Checkbox("Show Debug Info", id="show-debug", value=False)
                        yield Checkbox("Auto-save Progress", id="auto-save", value=True)
                        yield Checkbox("Verbose Logging", id="verbose-logging", value=False)
                    
                    # Execution info
                    with Container(classes="execution-status"):
                        yield Static("ℹ️ Execution Info", classes="section-header")
                        yield Static("Phase: ", id="execution-phase-display")
                        yield Static("Current Step: ", id="current-step-display")
                        yield Static("Progress: ", id="progress-display")
                        yield Static("ETA: ", id="eta-display")
                    
                    # Help and shortcuts
                    with Container(classes="help-panel"):
                        yield Static("❓ Keyboard Shortcuts", classes="section-header")
                        yield Static("Ctrl+C: Quit")
                        yield Static("Ctrl+P: Pause/Resume")
                        yield Static("Ctrl+S: Stop")
                        yield Static("Ctrl+R: Restart")
                        yield Static("Ctrl+L: Toggle Log")
                        yield Static("F1: Help")
            
            # Footer
            with Container(classes="execution-footer"):
                yield Static("Press F1 for help | Use mouse or keyboard to navigate", classes="footer-info")
    
    async def on_mount(self) -> None:
        """Initialize the screen when mounted."""
        await self.setup_step_table()
        await self.update_ui()
        
        # Start update timer
        self.update_timer = self.set_interval(1.0, self.update_ui)
    
    async def setup_step_table(self) -> None:
        """Set up the step data table."""
        table = self.query_one("#step-table", DataTable)
        table.clear(columns=True)
        
        # Add columns
        table.add_column("Step", key="step")
        table.add_column("Name", key="name")
        table.add_column("Status", key="status")
        table.add_column("Duration", key="duration")
        
        # Make table clickable
        table.cursor_type = "row"
        
        # Add steps from template
        for i in range(self.template.steps_count):
            step_id = f"step_{i + 1}"
            table.add_row(
                str(i + 1),
                f"Step {i + 1}",
                "⏳ Pending",
                "-",
                key=step_id
            )
            
            # Initialize step detail
            self.step_details[step_id] = StepExecutionDetail(
                step_id=step_id,
                step_name=f"Step {i + 1}",
                status=ExecutionStatus.PENDING
            )
    
    async def update_ui(self) -> None:
        """Update UI elements with current state."""
        try:
            # Update progress bar
            progress_bar = self.query_one("#execution-progress", ProgressBar)
            progress = self.calculate_progress()
            progress_bar.update(progress=progress)
            
            # Update metrics
            await self.update_metrics_display()
            
            # Update step table
            await self.update_step_table()
            
            # Update status displays
            await self.update_status_displays()
            
        except Exception as e:
            # Don't let UI updates crash the execution
            pass
    
    def calculate_progress(self) -> float:
        """Calculate overall execution progress."""
        if self.template.steps_count == 0:
            return 0.0
        
        completed_steps = sum(
            1 for detail in self.step_details.values()
            if detail.status == ExecutionStatus.COMPLETED
        )
        
        return (completed_steps / self.template.steps_count) * 100
    
    async def update_metrics_display(self) -> None:
        """Update the metrics display."""
        # Duration
        duration_widget = self.query_one("#duration-metric", Static)
        if self.metrics.start_time:
            if self.metrics.end_time:
                duration = self.metrics.total_duration
            else:
                duration = datetime.now() - self.metrics.start_time
            
            duration_str = str(duration).split('.')[0]  # Remove microseconds
            duration_widget.update(duration_str)
        else:
            duration_widget.update("0:00")
        
        # Tokens
        tokens_widget = self.query_one("#tokens-metric", Static)
        tokens_widget.update(f"{self.metrics.total_tokens:,}")
        
        # Cost
        cost_widget = self.query_one("#cost-metric", Static)
        cost_widget.update(f"${self.metrics.total_cost:.2f}")
        
        # Steps
        steps_widget = self.query_one("#steps-metric", Static)
        steps_widget.update(f"{self.metrics.steps_completed}/{self.template.steps_count}")
    
    async def update_step_table(self) -> None:
        """Update the step table with current status."""
        table = self.query_one("#step-table", DataTable)
        
        for step_id, detail in self.step_details.items():
            try:
                # Update status
                status_text = self.get_step_status_text(detail.status)
                status_class = f"step-{detail.status.value.lower()}"
                
                # Update duration
                duration_str = "-"
                if detail.duration:
                    duration_str = str(detail.duration).split('.')[0]
                
                # Update the row
                row = table.get_row(detail.step_id)
                if row:
                    row.update_key("status", status_text)
                    row.update_key("duration", duration_str)
                
            except (NoMatches, KeyError):
                # Row might not exist yet
                pass
    
    async def update_status_displays(self) -> None:
        """Update status display elements."""
        # Execution phase
        phase_widget = self.query_one("#execution-phase-display", Static)
        phase_widget.update(f"Phase: {self.execution_phase.value.replace('_', ' ').title()}")
        
        # Current step
        step_widget = self.query_one("#current-step-display", Static)
        if self.current_step_index < len(self.step_details):
            current_step = list(self.step_details.values())[self.current_step_index]
            step_widget.update(f"Current Step: {current_step.step_name}")
        else:
            step_widget.update("Current Step: None")
        
        # Progress
        progress_widget = self.query_one("#progress-display", Static)
        progress = self.calculate_progress()
        progress_widget.update(f"Progress: {progress:.1f}%")
        
        # ETA (simplified)
        eta_widget = self.query_one("#eta-display", Static)
        if self.metrics.start_time and progress > 0:
            elapsed = datetime.now() - self.metrics.start_time
            total_estimated = elapsed.total_seconds() / (progress / 100)
            remaining = total_estimated - elapsed.total_seconds()
            if remaining > 0:
                eta_widget.update(f"ETA: {int(remaining)}s")
            else:
                eta_widget.update("ETA: Soon")
        else:
            eta_widget.update("ETA: Unknown")
    
    def get_status_text(self) -> str:
        """Get current status text."""
        if self.is_stopped:
            return "STOPPED"
        elif self.is_paused:
            return "PAUSED"
        elif self.execution_phase == ExecutionPhase.ERROR:
            return "ERROR"
        elif self.execution_phase == ExecutionPhase.COMPLETION:
            return "COMPLETED"
        elif self.execution_phase == ExecutionPhase.STEP_EXECUTION:
            return "RUNNING"
        else:
            return "READY"
    
    def get_status_class(self) -> str:
        """Get CSS class for current status."""
        if self.is_stopped:
            return "error"
        elif self.is_paused:
            return "warning"
        elif self.execution_phase == ExecutionPhase.ERROR:
            return "error"
        elif self.execution_phase == ExecutionPhase.COMPLETION:
            return "completed"
        elif self.execution_phase == ExecutionPhase.STEP_EXECUTION:
            return "running"
        else:
            return "pending"
    
    def get_step_status_text(self, status: ExecutionStatus) -> str:
        """Get status text for a step."""
        status_map = {
            ExecutionStatus.PENDING: "⏳ Pending",
            ExecutionStatus.RUNNING: "▶️ Running",
            ExecutionStatus.COMPLETED: "✅ Completed",
            ExecutionStatus.FAILED: "❌ Failed",
            ExecutionStatus.CANCELLED: "⏸️ Cancelled",
        }
        return status_map.get(status, "❓ Unknown")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        
        # Main execution controls
        if button_id == "start-execution":
            await self.start_execution()
        elif button_id == "back-to-templates":
            await self.back_to_templates()
        elif button_id == "execute-step":
            await self.execute_current_step()
        elif button_id == "skip-step":
            await self.skip_current_step()
        elif button_id == "retry-step":
            await self.retry_current_step()
        elif button_id == "regenerate-result":
            await self.regenerate_result()
        elif button_id == "export-result":
            await self.export_result()
        elif button_id == "new-pipeline" or button_id == "new-pipeline-2":
            await self.start_new_pipeline()
        elif button_id == "view-report":
            await self.view_report()
        elif button_id == "export-results":
            await self.export_results()
        
        # Control panel buttons
        elif button_id == "control-start":
            await self.start_execution()
        elif button_id == "control-pause":
            await self.toggle_pause()
        elif button_id == "control-stop":
            await self.stop_execution()
        elif button_id == "control-restart":
            await self.restart_execution()
    
    async def start_execution(self) -> None:
        """Start pipeline execution."""
        if self.execution_phase == ExecutionPhase.INITIALIZATION:
            self.execution_phase = ExecutionPhase.INPUT_COLLECTION
            await self.show_input_phase()
        elif self.execution_phase == ExecutionPhase.INPUT_COLLECTION:
            # Validate inputs and start execution
            if await self.validate_inputs():
                await self.start_step_execution()
    
    async def show_input_phase(self) -> None:
        """Show the input collection phase."""
        content_switcher = self.query_one("#execution-content", ContentSwitcher)
        content_switcher.current = "input-phase"
        
        # Enable/disable controls
        self.update_control_states()
    
    async def validate_inputs(self) -> bool:
        """Validate pipeline inputs."""
        # This would validate all required inputs
        # For now, just return True
        return True
    
    async def start_step_execution(self) -> None:
        """Start step execution phase."""
        self.execution_phase = ExecutionPhase.STEP_EXECUTION
        self.metrics.start_time = datetime.now()
        
        # Update UI
        content_switcher = self.query_one("#execution-content", ContentSwitcher)
        content_switcher.current = "step-phase"
        
        # Update control states
        self.update_control_states()
        
        # Start execution of first step
        await self.execute_current_step()
    
    async def execute_current_step(self) -> None:
        """Execute the current step."""
        if self.is_paused or self.is_stopped:
            return
        
        if self.current_step_index >= len(self.step_details):
            await self.complete_execution()
            return
        
        # Get current step
        step_ids = list(self.step_details.keys())
        current_step_id = step_ids[self.current_step_index]
        step_detail = self.step_details[current_step_id]
        
        # Update step status
        step_detail.status = ExecutionStatus.RUNNING
        step_detail.start_time = datetime.now()
        
        # Update UI
        await self.update_step_table()
        
        # Simulate step execution (would integrate with pipeline service)
        await self.simulate_step_execution(step_detail)
    
    async def simulate_step_execution(self, step_detail: StepExecutionDetail) -> None:
        """Simulate step execution (replace with actual integration)."""
        # Add log entry
        log_widget = self.query_one("#execution-log", Log)
        log_widget.write_line(f"Executing step: {step_detail.step_name}")
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Update step detail
        step_detail.status = ExecutionStatus.COMPLETED
        step_detail.end_time = datetime.now()
        step_detail.duration = step_detail.end_time - step_detail.start_time
        
        # Simulate token usage and cost
        step_detail.input_tokens = 100
        step_detail.output_tokens = 200
        step_detail.cost = 0.02
        
        # Update metrics
        self.metrics.total_tokens += step_detail.input_tokens + step_detail.output_tokens
        self.metrics.total_cost += step_detail.cost
        self.metrics.steps_completed += 1
        
        # Update step detail in output
        output_widget = self.query_one("#step-output", TextArea)
        output_widget.text = f"Step {step_detail.step_name} completed successfully.\n\n"
        output_widget.text += f"Model: gpt-4o-mini\n"
        output_widget.text += f"Tokens: {step_detail.input_tokens} → {step_detail.output_tokens}\n"
        output_widget.text += f"Cost: ${step_detail.cost:.3f}\n"
        output_widget.text += f"Duration: {step_detail.duration}\n\n"
        output_widget.text += "Generated content would appear here..."
        
        # Add log entry
        log_widget.write_line(f"Step completed: {step_detail.step_name}")
        
        # Move to next step
        self.current_step_index += 1
        
        # Update UI
        await self.update_ui()
        
        # Enable retry button
        retry_btn = self.query_one("#retry-step")
        retry_btn.disabled = False
        
        # Auto-advance to next step after a delay
        if not self.is_paused and not self.is_stopped:
            self.set_timer(1.0, self.execute_current_step)
    
    async def skip_current_step(self) -> None:
        """Skip the current step."""
        if self.current_step_index >= len(self.step_details):
            return
        
        # Get current step
        step_ids = list(self.step_details.keys())
        current_step_id = step_ids[self.current_step_index]
        step_detail = self.step_details[current_step_id]
        
        # Update step status
        step_detail.status = ExecutionStatus.CANCELLED
        step_detail.end_time = datetime.now()
        
        # Add log entry
        log_widget = self.query_one("#execution-log", Log)
        log_widget.write_line(f"Step skipped: {step_detail.step_name}")
        
        # Move to next step
        self.current_step_index += 1
        await self.execute_current_step()
    
    async def retry_current_step(self) -> None:
        """Retry the current step."""
        if self.current_step_index == 0:
            return
        
        # Go back to previous step
        self.current_step_index -= 1
        
        # Reset step status
        step_ids = list(self.step_details.keys())
        current_step_id = step_ids[self.current_step_index]
        step_detail = self.step_details[current_step_id]
        
        step_detail.status = ExecutionStatus.PENDING
        step_detail.start_time = None
        step_detail.end_time = None
        step_detail.duration = None
        step_detail.retry_count += 1
        
        # Add log entry
        log_widget = self.query_one("#execution-log", Log)
        log_widget.write_line(f"Retrying step: {step_detail.step_name} (attempt {step_detail.retry_count})")
        
        # Update UI
        await self.update_ui()
        
        # Execute the step
        await self.execute_current_step()
    
    async def complete_execution(self) -> None:
        """Complete the pipeline execution."""
        self.execution_phase = ExecutionPhase.COMPLETION
        self.metrics.end_time = datetime.now()
        self.metrics.total_duration = self.metrics.end_time - self.metrics.start_time
        
        # Update control states
        self.update_control_states()
        
        # Show completion phase
        content_switcher = self.query_one("#execution-content", ContentSwitcher)
        content_switcher.current = "completion-phase"
        
        # Update completion summary
        await self.update_completion_summary()
        
        # Add log entry
        log_widget = self.query_one("#execution-log", Log)
        log_widget.write_line("Pipeline execution completed successfully!")
    
    async def update_completion_summary(self) -> None:
        """Update the completion summary."""
        summary_widget = self.query_one("#completion-summary", Static)
        
        summary_text = f"""
# Execution Summary

**Pipeline:** {self.template.name}
**Execution ID:** {self.execution_id}
**Duration:** {self.metrics.total_duration}
**Status:** Completed

## Metrics
- **Total Tokens:** {self.metrics.total_tokens:,}
- **Total Cost:** ${self.metrics.total_cost:.2f}
- **Steps Completed:** {self.metrics.steps_completed}/{self.template.steps_count}
- **Steps Failed:** {self.metrics.steps_failed}

## Performance
- **Average Step Duration:** {self.metrics.average_step_duration:.2f}s
- **Throughput:** {self.metrics.throughput:.2f} steps/minute

The pipeline has been executed successfully. You can now view the detailed results or export them for further use.
"""
        
        await summary_widget.remove_children()
        await summary_widget.mount(Markdown(summary_text))
    
    async def toggle_pause(self) -> None:
        """Toggle pause state."""
        self.is_paused = not self.is_paused
        
        # Add log entry
        log_widget = self.query_one("#execution-log", Log)
        if self.is_paused:
            log_widget.write_line("Execution paused")
        else:
            log_widget.write_line("Execution resumed")
        
        # Update control states
        self.update_control_states()
        
        # If resuming, continue execution
        if not self.is_paused and not self.is_stopped:
            await self.execute_current_step()
    
    async def stop_execution(self) -> None:
        """Stop the execution."""
        self.is_stopped = True
        
        # Add log entry
        log_widget = self.query_one("#execution-log", Log)
        log_widget.write_line("Execution stopped by user")
        
        # Update control states
        self.update_control_states()
    
    async def restart_execution(self) -> None:
        """Restart the execution from the beginning."""
        # Reset all state
        self.current_step_index = 0
        self.is_paused = False
        self.is_stopped = False
        self.metrics = ExecutionMetrics()
        
        # Reset step details
        for step_detail in self.step_details.values():
            step_detail.status = ExecutionStatus.PENDING
            step_detail.start_time = None
            step_detail.end_time = None
            step_detail.duration = None
            step_detail.retry_count = 0
        
        # Clear log
        log_widget = self.query_one("#execution-log", Log)
        log_widget.clear()
        
        # Add log entry
        log_widget.write_line("Execution restarted")
        
        # Update UI
        await self.update_ui()
        
        # Start execution
        await self.start_execution()
    
    def update_control_states(self) -> None:
        """Update control button states based on current state."""
        try:
            # Control panel buttons
            start_btn = self.query_one("#control-start")
            pause_btn = self.query_one("#control-pause")
            stop_btn = self.query_one("#control-stop")
            restart_btn = self.query_one("#control-restart")
            
            # Enable/disable based on state
            start_btn.disabled = (
                self.execution_phase == ExecutionPhase.STEP_EXECUTION or
                self.execution_phase == ExecutionPhase.COMPLETION
            )
            
            pause_btn.disabled = (
                self.execution_phase != ExecutionPhase.STEP_EXECUTION or
                self.is_stopped
            )
            
            stop_btn.disabled = (
                self.execution_phase not in [
                    ExecutionPhase.INPUT_COLLECTION,
                    ExecutionPhase.STEP_EXECUTION
                ] or
                self.is_stopped
            )
            
            restart_btn.disabled = (
                self.execution_phase == ExecutionPhase.INITIALIZATION
            )
            
            # Update pause button text
            if self.is_paused:
                pause_btn.label = "▶️ Resume"
            else:
                pause_btn.label = "⏸️ Pause"
                
        except NoMatches:
            # Buttons might not exist in current phase
            pass
    
    async def back_to_templates(self) -> None:
        """Go back to template selection."""
        # This would switch back to the template browser
        await self.show_error("Back to templates not yet implemented")
    
    async def regenerate_result(self) -> None:
        """Regenerate the final result."""
        await self.show_error("Result regeneration not yet implemented")
    
    async def export_result(self) -> None:
        """Export the result."""
        await self.show_error("Result export not yet implemented")
    
    async def start_new_pipeline(self) -> None:
        """Start a new pipeline."""
        await self.show_error("New pipeline not yet implemented")
    
    async def view_report(self) -> None:
        """View detailed execution report."""
        await self.show_error("Report view not yet implemented")
    
    async def export_results(self) -> None:
        """Export all results."""
        await self.show_error("Results export not yet implemented")
    
    async def show_error(self, message: str) -> None:
        """Show an error message."""
        # This would show a proper error dialog
        log_widget = self.query_one("#execution-log", Log)
        log_widget.write_line(f"❌ Error: {message}")
    
    # Action handlers
    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
    
    def action_pause(self) -> None:
        """Pause/resume execution."""
        asyncio.create_task(self.toggle_pause())
    
    def action_stop(self) -> None:
        """Stop execution."""
        asyncio.create_task(self.stop_execution())
    
    def action_restart(self) -> None:
        """Restart execution."""
        asyncio.create_task(self.restart_execution())
    
    def action_toggle_log(self) -> None:
        """Toggle log panel visibility."""
        self.show_log_panel = not self.show_log_panel
        # This would require rebuilding the UI
        self.show_error("Log toggle not yet implemented")
    
    def action_show_help(self) -> None:
        """Show help."""
        help_text = """
# Advanced Pipeline Execution Help

## Keyboard Shortcuts
- **Ctrl+C**: Quit application
- **Ctrl+P**: Pause/Resume execution
- **Ctrl+S**: Stop execution
- **Ctrl+R**: Restart execution
- **Ctrl+L**: Toggle log panel
- **F1**: Show this help
- **Ctrl+Left**: Previous step
- **Ctrl+Right**: Next step

## Execution Phases
1. **Input Collection**: Gather required inputs for the pipeline
2. **Step Execution**: Execute each step sequentially
3. **Result Generation**: Generate final results
4. **Completion**: Review and export results

## Controls
- **Start**: Begin pipeline execution
- **Pause/Resume**: Pause and resume execution
- **Stop**: Stop execution (cannot be resumed)
- **Restart**: Restart from the beginning
- **Skip**: Skip current step
- **Retry**: Retry current step

## Tips
- Monitor the execution log for detailed progress
- Use the metrics panel to track performance
- Save progress automatically for long-running pipelines
- Export results for further analysis
"""
        
        self.push_screen("help", lambda: Markdown(help_text))
    
    def action_previous_step(self) -> None:
        """Go to previous step."""
        if self.current_step_index > 0:
            self.current_step_index -= 1
            asyncio.create_task(self.update_ui())
    
    def action_next_step(self) -> None:
        """Go to next step."""
        if self.current_step_index < len(self.step_details) - 1:
            self.current_step_index += 1
            asyncio.create_task(self.update_ui())
    
    async def on_unmount(self) -> None:
        """Clean up when the screen is unmounted."""
        if self.update_timer:
            self.update_timer.stop()
        
        if self.execution_worker:
            self.execution_worker.stop()