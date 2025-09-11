# ABOUTME: Textual TUI application for running WriteIt pipelines interactively
# ABOUTME: Handles step-by-step pipeline execution with real-time feedback and user input

import asyncio
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import llm
import uuid

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.widgets import (
    Header,
    Footer,
    Static,
    Button,
    TextArea,
    Select,
    ProgressBar,
)
from textual.reactive import reactive
from textual.binding import Binding

from writeit.workspace.workspace import Workspace
from writeit.llm.token_usage import TokenUsageTracker


@dataclass
class PipelineInput:
    """Represents a pipeline input field configuration."""

    key: str
    type: str
    label: str
    required: bool = False
    default: Any = None
    placeholder: str = ""
    help: str = ""
    options: List[Dict[str, str]] = field(default_factory=list)
    max_length: Optional[int] = None


@dataclass
class PipelineStep:
    """Represents a pipeline step configuration."""

    key: str
    name: str
    description: str
    type: str
    prompt_template: str
    selection_prompt: str
    model_preference: List[str] = field(default_factory=list)
    validation: Dict[str, Any] = field(default_factory=dict)
    ui: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """Represents a complete pipeline configuration."""

    metadata: Dict[str, Any]
    defaults: Dict[str, Any]
    inputs: List[PipelineInput]
    steps: List[PipelineStep]


class PipelineInputsWidget(Container):
    """Widget for collecting pipeline inputs from user."""

    def __init__(self, inputs: List[PipelineInput]) -> None:
        super().__init__()
        self.inputs = inputs
        self.values: Dict[str, Any] = {}

    def compose(self) -> ComposeResult:
        yield Static("📝 Pipeline Inputs", classes="section-header")

        for input_config in self.inputs:
            yield Static(
                f"**{input_config.label}**{'*' if input_config.required else ''}"
            )
            if input_config.help:
                yield Static(f"[dim]{input_config.help}[/dim]", classes="help-text")

            if input_config.type == "text":
                yield TextArea(
                    placeholder=input_config.placeholder,
                    id=f"input-{input_config.key}",
                    classes="input-field",
                )
            elif input_config.type == "choice":
                # Create properly formatted options for Textual Select
                options = [(opt["label"], opt["value"]) for opt in input_config.options]

                # Create select without default value first
                yield Select(
                    options, id=f"input-{input_config.key}", classes="input-field"
                )

        yield Button("Start Pipeline", id="start-pipeline", variant="success")

    async def on_mount(self) -> None:
        """Set default values after mount."""
        for input_config in self.inputs:
            if input_config.type == "choice" and input_config.default:
                select_widget = self.query_one(f"#input-{input_config.key}", Select)
                try:
                    select_widget.value = input_config.default
                except Exception:
                    # If default value doesn't exist in options, ignore
                    pass

    def collect_values(self) -> Dict[str, Any]:
        """Collect all input values."""
        values = {}
        for input_config in self.inputs:
            widget = self.query_one(f"#input-{input_config.key}")
            if input_config.type == "text":
                values[input_config.key] = widget.text
            elif input_config.type == "choice":
                values[input_config.key] = widget.value
        return values

    def validate_inputs(self) -> tuple[bool, str]:
        """Validate all required inputs are filled."""
        values = self.collect_values()

        for input_config in self.inputs:
            if input_config.required:
                value = values.get(input_config.key)
                if not value or (isinstance(value, str) and not value.strip()):
                    return False, f"{input_config.label} is required"

        return True, ""


class StepExecutionWidget(Container):
    """Widget for executing a single pipeline step."""

    current_step = reactive(-1)

    def __init__(self, step: PipelineStep) -> None:
        super().__init__()
        self.step = step
        self.responses: List[str] = []
        self.selected_response: Optional[str] = None
        self.user_feedback: str = ""

    def compose(self) -> ComposeResult:
        yield Static(f"⚡ {self.step.name}", classes="section-header")
        yield Static(self.step.description, classes="step-description")

        # Progress and status
        yield ProgressBar(id="step-progress")
        yield Static("Preparing...", id="step-status")

        # Response display area
        yield TextArea(
            "Generated responses will appear here...",
            read_only=True,
            id="responses-display",
            show_line_numbers=False,
            classes="responses-area",
        )

        # User feedback area
        yield Static("💬 Your Feedback (optional)")
        yield TextArea(
            placeholder="Provide feedback to guide the next step...",
            id="user-feedback",
            classes="feedback-area",
        )

        # Action buttons
        with Horizontal(classes="action-buttons"):
            yield Button(
                "Regenerate", id="regenerate", variant="warning", disabled=True
            )
            yield Button(
                "Continue", id="continue-step", variant="success", disabled=True
            )


class PipelineSummaryWidget(Container):
    """Widget showing pipeline completion summary."""

    def __init__(self, results: Dict[str, Any]) -> None:
        super().__init__()
        self.results = results

    def compose(self) -> ComposeResult:
        yield Static("🎉 Pipeline Complete!", classes="section-header")
        yield Static(
            "Your pipeline has completed successfully. Review the final output below:"
        )

        # Final output
        final_result = self.results.get("final_output", "")
        yield TextArea(
            final_result, read_only=True, id="final-output", classes="final-output"
        )

        # Action buttons
        with Horizontal(classes="action-buttons"):
            yield Button("Export", id="export-result", variant="primary")
            yield Button("New Pipeline", id="new-pipeline", variant="default")
            yield Button("Exit", id="exit-app", variant="default")


class PipelineRunnerApp(App[None]):
    """Main TUI application for running WriteIt pipelines."""

    CSS = """
    .section-header {
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }
    
    .step-description {
        color: $text-muted;
        margin: 0 0 1 0;
    }
    
    .help-text {
        color: $text-muted;
        margin: 0 0 0 2;
    }
    
    .input-field {
        margin: 0 0 1 0;
        min-height: 3;
    }
    
    .responses-area {
        height: 20;
        border: solid $primary;
        margin: 1 0;
    }
    
    .feedback-area {
        height: 8;
        margin: 1 0;
    }
    
    .final-output {
        height: 30;
        border: solid $success;
        margin: 1 0;
    }
    
    .action-buttons {
        height: auto;
        margin: 1 0;
    }
    
    .action-buttons Button {
        margin: 0 1;
    }
    
    /* Make focus more visible */
    TextArea:focus {
        border: thick $accent;
    }
    
    Select:focus {
        border: thick $accent;
    }
    
    Button:focus {
        border: thick $accent;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("cmd+c,ctrl+shift+c", "copy_response", "Copy Response"),
        Binding("cmd+a,ctrl+a", "select_all_response", "Select All"),
        Binding("f1", "show_help", "Help"),
        Binding("ctrl+j", "focus_next", "Next Field"),
        Binding("ctrl+k", "focus_previous", "Previous Field"),
        Binding("ctrl+d", "scroll_down", "Scroll Down"),
        Binding("ctrl+u", "scroll_up", "Scroll Up"),
        Binding("tab", "focus_next_enhanced", "Next Field (Enhanced)", show=False),
        Binding(
            "shift+tab",
            "focus_previous_enhanced",
            "Previous Field (Enhanced)",
            show=False,
        ),
    ]

    def __init__(self, pipeline_path: Path, workspace_name: str):
        super().__init__()
        self.pipeline_path = pipeline_path
        self.workspace_name = workspace_name
        self.workspace = Workspace()
        self.pipeline_config: Optional[PipelineConfig] = None

        self.current_phase = "loading"  # loading, inputs, execution, complete
        self.current_step_index = -1
        self.pipeline_values: Dict[str, Any] = {}
        self.step_results: Dict[str, Any] = {}
        self.token_tracker = TokenUsageTracker()
        self.current_run_id: Optional[str] = None

    def update_status_bar(self, message: str) -> None:
        """Update the status bar with a message."""
        # Use sub_title to show status in the header instead since Footer is read-only
        self.sub_title = message

    def action_copy_response(self) -> None:
        """Copy the current response to clipboard."""
        try:
            response_area = self.query_one("#responses-display", TextArea)
            if response_area.text.strip():
                # Try to copy selected text first, then all text
                selected_text = response_area.selected_text
                text_to_copy = selected_text if selected_text else response_area.text

                import pyperclip

                pyperclip.copy(text_to_copy)
                self.update_status_bar("📋 Copied to clipboard!")

                # Clear status after 2 seconds
                self.set_timer(2.0, lambda: self.update_status_bar(""))
            else:
                self.update_status_bar("No response to copy")
        except ImportError:
            self.update_status_bar(
                "❌ pyperclip not installed - can't copy to clipboard"
            )
        except Exception as e:
            self.update_status_bar(f"❌ Copy failed: {str(e)}")

    def action_select_all_response(self) -> None:
        """Select all text in the response area."""
        try:
            response_area = self.query_one("#responses-display", TextArea)
            if response_area.text.strip():
                response_area.focus()
                response_area.select_all()
                self.update_status_bar("Text selected - use Cmd+C to copy")
                self.set_timer(3.0, lambda: self.update_status_bar(""))
        except Exception as e:
            self.update_status_bar(f"❌ Select failed: {str(e)}")

    def compose(self) -> ComposeResult:
        """Create the app layout."""
        yield Header()

        with ScrollableContainer(id="main-content"):
            yield Static("🚀 WriteIt Pipeline Runner", classes="section-header")
            yield Static(f"Pipeline: {self.pipeline_path.stem}", id="pipeline-info")
            yield Static(f"Workspace: {self.workspace_name}", id="workspace-info")

            # Dynamic content area
            yield Container(id="dynamic-content")

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the app and load pipeline configuration."""
        await self.load_pipeline()

    async def load_pipeline(self) -> None:
        """Load and parse the pipeline configuration."""
        try:
            with open(self.pipeline_path, "r") as f:
                raw_config = yaml.safe_load(f)

            # Parse inputs
            inputs = []
            for key, config in raw_config.get("inputs", {}).items():
                inputs.append(
                    PipelineInput(
                        key=key,
                        type=config["type"],
                        label=config["label"],
                        required=config.get("required", False),
                        default=config.get("default"),
                        placeholder=config.get("placeholder", ""),
                        help=config.get("help", ""),
                        options=config.get("options", []),
                        max_length=config.get("max_length"),
                    )
                )

            # Parse steps
            steps = []
            for key, config in raw_config.get("steps", {}).items():
                steps.append(
                    PipelineStep(
                        key=key,
                        name=config["name"],
                        description=config["description"],
                        type=config["type"],
                        prompt_template=config["prompt_template"],
                        selection_prompt=config.get("selection_prompt", ""),
                        model_preference=config.get("model_preference", []),
                        validation=config.get("validation", {}),
                        ui=config.get("ui", {}),
                    )
                )

            self.pipeline_config = PipelineConfig(
                metadata=raw_config.get("metadata", {}),
                defaults=raw_config.get("defaults", {}),
                inputs=inputs,
                steps=steps,
            )

            # Show inputs phase
            await self.show_inputs_phase()

        except Exception as e:
            await self.show_error(f"Failed to load pipeline: {e}")

    async def show_inputs_phase(self) -> None:
        """Show the input collection phase."""
        if not self.pipeline_config:
            return

        self.current_phase = "inputs"

        # Update dynamic content
        content = self.query_one("#dynamic-content")
        await content.remove_children()

        inputs_widget = PipelineInputsWidget(self.pipeline_config.inputs)
        await content.mount(inputs_widget)

        # Focus the first input field
        self.call_after_refresh(self._focus_first_input)

    async def show_execution_phase(self) -> None:
        """Show the pipeline execution phase."""
        self.current_phase = "execution"
        self.current_step_index = 0

        await self.execute_current_step()

    async def execute_current_step(self) -> None:
        """Execute the current pipeline step."""
        if not self.pipeline_config or self.current_step_index >= len(
            self.pipeline_config.steps
        ):
            await self.show_completion_phase()
            return

        step = self.pipeline_config.steps[self.current_step_index]

        # Update dynamic content
        content = self.query_one("#dynamic-content")
        await content.remove_children()

        step_widget = StepExecutionWidget(step)
        await content.mount(step_widget)

        # Execute step with actual LLM integration
        await self.execute_step_with_llm(step, step_widget)

    async def execute_step_with_llm(
        self, step: PipelineStep, widget: StepExecutionWidget
    ) -> None:
        """Execute step with actual LLM API calls."""
        # Update status
        status = widget.query_one("#step-status")
        progress = widget.query_one("#step-progress")
        responses_display = widget.query_one("#responses-display")

        # Show step start in status bar
        self.update_status_bar(f"Starting step: {step.name}")
        status.update("Preparing request...")
        progress.update(progress=25)

        try:
            # Render the prompt template with current context
            rendered_prompt = self.render_prompt_template(step)
            progress.update(progress=50)

            # Get model preference
            model_name = (
                step.model_preference[0]
                if isinstance(step.model_preference, list)
                else step.model_preference
            )
            if not model_name:
                model_name = "gpt-4o-mini"  # Default fallback

            # Also render model name template variables
            for key, value in self.pipeline_config.defaults.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        model_name = model_name.replace(
                            f"{{{{ defaults.{key}.{sub_key} }}}}", str(sub_value)
                        )
                else:
                    model_name = model_name.replace(
                        f"{{{{ defaults.{key} }}}}", str(value)
                    )

            # Move LLM status to status bar
            self.update_status_bar(f"Calling {model_name}...")
            status.update("Connecting to AI model...")
            progress.update(progress=75)

            # Make LLM API call with progress updates
            model = llm.get_model(model_name)

            # Create a task to periodically update status bar while waiting for response
            async def update_thinking_status():
                dots = ""
                while True:
                    await asyncio.sleep(2)
                    dots = "." * (
                        (len(dots) + 1) % 4
                    )  # Cycle through "", ".", "..", "..."
                    self.update_status_bar(
                        f"🤖 {model_name} is thinking{dots} (10-30 seconds)"
                    )

            # Start the status animation
            thinking_task = asyncio.create_task(update_thinking_status())
            status.update("⏳ Waiting for AI response...")

            try:
                # Run the LLM call in a separate thread to avoid blocking the UI
                response = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: model.prompt(rendered_prompt)
                )
            finally:
                thinking_task.cancel()
                try:
                    await thinking_task
                except asyncio.CancelledError:
                    pass

            # Track token usage for this step
            if self.current_run_id:
                step_usage = self.token_tracker.track_step_usage(
                    step_key=step.key,
                    step_name=step.name,
                    model_name=str(model),
                    response=response,
                )
                if step_usage and self.token_tracker.current_run:
                    current_run = self.token_tracker.current_run
                    token_info = f" | {step_usage.usage.input_tokens}→{step_usage.usage.output_tokens} tokens"

                    # Update header subtitle with running total
                    total_tokens = (
                        current_run.total_input_tokens + current_run.total_output_tokens
                    )
                    self.sub_title = f"Pipeline: {current_run.pipeline_name} | Total: {total_tokens:,} tokens"
                else:
                    token_info = ""
            else:
                token_info = ""

            # Success - update status bar and display response
            self.update_status_bar(f"✅ {step.name} completed successfully{token_info}")
            responses_display.text = f"**Response:**\n{response.text()}"

            progress.update(progress=100)
            status.update("✅ Response received! Review and continue.")

            # Store response for template rendering in next steps
            if not hasattr(self, "step_responses"):
                self.step_responses = {}
            self.step_responses[step.key] = response.text()

        except Exception as e:
            # Show error in both status bar and inline
            self.update_status_bar(f"❌ Error in {step.name}: {str(e)}")
            status.update("❌ Error occurred")
            responses_display.text = f"**Error:**\n{str(e)}"

        # Enable buttons
        continue_btn = widget.query_one("#continue-step")
        regenerate_btn = widget.query_one("#regenerate")
        continue_btn.disabled = False
        regenerate_btn.disabled = False

    def render_prompt_template(self, step: PipelineStep) -> str:
        """Render the prompt template with current context."""
        template = step.prompt_template

        # Replace input variables
        for key, value in self.pipeline_values.items():
            template = template.replace(f"{{{{ inputs.{key} }}}}", str(value))

        # Replace step responses
        if hasattr(self, "step_responses"):
            for step_key, response in self.step_responses.items():
                template = template.replace(
                    f"{{{{ steps.{step_key}.selected_response }}}}", response
                )

        # Replace defaults
        for key, value in self.pipeline_config.defaults.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    template = template.replace(
                        f"{{{{ defaults.{key}.{sub_key} }}}}", str(sub_value)
                    )
            else:
                template = template.replace(f"{{{{ defaults.{key} }}}}", str(value))

        return template

    async def show_completion_phase(self) -> None:
        """Show the pipeline completion phase."""
        self.current_phase = "complete"

        # Finalize token usage tracking
        completed_run = self.token_tracker.finish_current_run()

        # Collect final results
        final_output = self.step_results.get(
            "polish", "Pipeline completed successfully!"
        )

        # Add concise token usage to final output
        if completed_run:
            models_used = ", ".join(completed_run.by_model.keys())
            token_summary = (
                f"\n\n---\n**📊 Token Usage:** {completed_run.total_tokens:,} total "
                f"({completed_run.total_input_tokens:,}→{completed_run.total_output_tokens:,}) "
                f"| Models: {models_used}"
            )
            final_output += token_summary

        # Update dynamic content
        content = self.query_one("#dynamic-content")
        await content.remove_children()

        summary_widget = PipelineSummaryWidget({"final_output": final_output})

        # Update header with final token count
        if completed_run:
            self.sub_title = f"Complete | Total: {completed_run.total_tokens:,} tokens | {len(completed_run.by_model)} models used"

        await content.mount(summary_widget)

    async def show_error(self, message: str) -> None:
        """Show an error message."""
        content = self.query_one("#dynamic-content")
        await content.remove_children()

        await content.mount(Static(f"❌ Error: {message}", classes="error"))
        await content.mount(Button("Exit", id="exit-app", variant="default"))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "start-pipeline":
            await self.handle_start_pipeline()
        elif event.button.id == "continue-step":
            await self.handle_continue_step()
        elif event.button.id == "regenerate":
            await self.handle_regenerate_step()
        elif event.button.id == "new-pipeline":
            await self.handle_new_pipeline()
        elif event.button.id == "exit-app":
            self.exit()
        elif event.button.id == "export-result":
            await self.handle_export_result()

    async def handle_start_pipeline(self) -> None:
        """Handle starting the pipeline execution."""
        inputs_widget = self.query_one(PipelineInputsWidget)

        # Validate inputs
        valid, error_msg = inputs_widget.validate_inputs()
        if not valid:
            # Show error (would implement proper error display)
            return

        # Collect values and start execution
        self.pipeline_values = inputs_widget.collect_values()

        # Start token usage tracking for this pipeline run
        self.current_run_id = str(uuid.uuid4())
        pipeline_name = self.pipeline_config.metadata.get("name", "Unknown Pipeline")
        self.token_tracker.start_pipeline_run(pipeline_name, self.current_run_id)

        # Update header to show pipeline and tracking started
        self.sub_title = f"Pipeline: {pipeline_name} | Token tracking: ON"
        self.update_status_bar("🚀 Starting pipeline execution")

        await self.show_execution_phase()

    async def handle_continue_step(self) -> None:
        """Handle continuing to the next step."""
        if not self.pipeline_config:
            return

        # Collect user feedback
        step_widget = self.query_one(StepExecutionWidget)
        feedback_area = step_widget.query_one("#user-feedback")

        # Store step results (mock for now)
        current_step = self.pipeline_config.steps[self.current_step_index]
        self.step_results[current_step.key] = {
            "selected_response": "Mock selected response",
            "user_feedback": feedback_area.text,
        }

        # Move to next step
        self.current_step_index += 1
        await self.execute_current_step()

    async def handle_regenerate_step(self) -> None:
        """Handle regenerating the current step."""
        await self.execute_current_step()

    async def handle_new_pipeline(self) -> None:
        """Handle starting a new pipeline."""
        # Reset state
        self.current_step_index = -1
        self.pipeline_values = {}
        self.step_results = {}

        await self.show_inputs_phase()

    async def handle_export_result(self) -> None:
        """Handle exporting the final result."""
        # Export final result to file
        if not self.step_results:
            await self.show_error("No results to export")
            return

        from pathlib import Path
        from datetime import datetime

        # Create exports directory if it doesn't exist
        export_dir = Path.home() / ".writeit" / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pipeline_name = self.pipeline_config.metadata.get("name", "pipeline").replace(
            " ", "_"
        )
        filename = export_dir / f"{pipeline_name}_{timestamp}.md"

        # Get the final output
        final_output = self.step_results.get("polish", "")
        if not final_output:
            # Try to get the last available result
            for key in reversed(list(self.step_results.keys())):
                if self.step_results[key]:
                    final_output = self.step_results[key]
                    break

        if final_output:
            filename.write_text(final_output)
            # Show success message
            content = self.query_one("#dynamic-content")
            await content.mount(
                Static(f"✅ Exported to: {filename}", classes="success")
            )

    def action_show_help(self) -> None:
        """Show help information."""
        from textual.widgets import Static

        help_text = """# WriteIt Pipeline Runner Help

## Keyboard Shortcuts:
- **Tab/Shift+Tab**: Navigate between elements
- **Enter**: Select/activate buttons
- **Arrow Keys**: Navigate responses
- **Space**: Select response
- **Ctrl+C**: Exit application
- **Ctrl+R**: Regenerate current step
- **Ctrl+E**: Export results

## Pipeline Phases:
1. **Input Phase**: Enter required values
2. **Step Execution**: Generate and select responses
3. **Completion**: View and export final result

## Tips:
- Provide detailed feedback to guide generation
- Use style primers for consistent output
- Export results for later use
"""

        # Push a help screen
        self.push_screen("help", lambda: Static(help_text))

    def action_focus_next(self) -> None:
        """Focus next widget and ensure it's visible."""
        self.screen.focus_next()
        self._ensure_focused_visible()

    def action_focus_previous(self) -> None:
        """Focus previous widget and ensure it's visible."""
        self.screen.focus_previous()
        self._ensure_focused_visible()

    def action_focus_next_enhanced(self) -> None:
        """Enhanced focus next that skips non-interactive elements."""
        self._focus_next_interactive()
        self._ensure_focused_visible()

    def action_focus_previous_enhanced(self) -> None:
        """Enhanced focus previous that skips non-interactive elements."""
        self._focus_previous_interactive()
        self._ensure_focused_visible()

    def action_scroll_down(self) -> None:
        """Scroll main content down."""
        try:
            # Always scroll main content, not nested containers
            main_content = self.query_one("#main-content", ScrollableContainer)
            main_content.scroll_down(animate=False)
        except Exception:
            pass

    def action_scroll_up(self) -> None:
        """Scroll main content up."""
        try:
            # Always scroll main content, not nested containers
            main_content = self.query_one("#main-content", ScrollableContainer)
            main_content.scroll_up(animate=False)
        except Exception:
            pass

    def _ensure_focused_visible(self) -> None:
        """Ensure the currently focused widget is visible by scrolling to it."""
        try:
            focused = self.screen.focused
            if not focused:
                return

            # Get main scrollable container
            main_content = self.query_one("#main-content", ScrollableContainer)

            # Get the focused widget's position relative to viewport
            focused_offset = focused.virtual_region_with_margin

            # Calculate if widget is outside visible area
            visible_top = main_content.scroll_y
            visible_bottom = visible_top + main_content.region.height
            widget_top = focused_offset.y
            widget_bottom = focused_offset.bottom

            # Scroll to make widget visible with some padding
            padding = 2
            if widget_top < visible_top:
                # Widget is above visible area - scroll up
                scroll_target = max(0, widget_top - padding)
                main_content.scroll_to(y=scroll_target, animate=False)
            elif widget_bottom > visible_bottom:
                # Widget is below visible area - scroll down
                scroll_target = widget_bottom - main_content.region.height + padding
                scroll_target = max(0, min(scroll_target, main_content.max_scroll_y))
                main_content.scroll_to(y=scroll_target, animate=False)

        except Exception:
            # Fallback to simple visibility check
            try:
                focused = self.screen.focused
                if focused:
                    focused.scroll_visible(animate=False)
            except Exception:
                pass

    def _focus_next_interactive(self) -> None:
        """Focus next interactive widget, skipping read-only elements."""
        try:
            # Get current active container (dynamic content area)
            dynamic_content = self.query_one("#dynamic-content")
            current_focus = self.screen.focused

            # Get focusable widgets within active area only
            active_focusable = dynamic_content.query(
                "TextArea, Select, Input, Button"
            ).filter(
                lambda w: (
                    w.can_focus
                    and not w.disabled
                    and not getattr(w, "read_only", False)
                    and w.display
                    and w.region.height > 0
                )
            )

            # Include start/continue/action buttons from current phase
            action_buttons = self.query(".action-buttons Button").filter(
                lambda w: w.can_focus and not w.disabled and w.display
            )

            all_focusable = [*active_focusable, *action_buttons]

            if not all_focusable:
                self.screen.focus_next()
                return

            # Find current position and move to next
            if current_focus and current_focus in all_focusable:
                current_idx = all_focusable.index(current_focus)
                next_idx = (current_idx + 1) % len(all_focusable)
                all_focusable[next_idx].focus()
            else:
                # Focus first available widget
                all_focusable[0].focus()
        except Exception:
            self.screen.focus_next()

    def _focus_previous_interactive(self) -> None:
        """Focus previous interactive widget, skipping read-only elements."""
        try:
            # Get current active container (dynamic content area)
            dynamic_content = self.query_one("#dynamic-content")
            current_focus = self.screen.focused

            # Get focusable widgets within active area only
            active_focusable = dynamic_content.query(
                "TextArea, Select, Input, Button"
            ).filter(
                lambda w: (
                    w.can_focus
                    and not w.disabled
                    and not getattr(w, "read_only", False)
                    and w.display
                    and w.region.height > 0
                )
            )

            # Include start/continue/action buttons from current phase
            action_buttons = self.query(".action-buttons Button").filter(
                lambda w: w.can_focus and not w.disabled and w.display
            )

            all_focusable = [*active_focusable, *action_buttons]

            if not all_focusable:
                self.screen.focus_previous()
                return

            # Find current position and move to previous
            if current_focus and current_focus in all_focusable:
                current_idx = all_focusable.index(current_focus)
                prev_idx = (current_idx - 1) % len(all_focusable)
                all_focusable[prev_idx].focus()
            else:
                # Focus last available widget
                all_focusable[-1].focus()
        except Exception:
            self.screen.focus_previous()

    def _focus_first_input(self) -> None:
        """Focus the first input field and ensure it's visible."""
        try:
            # Find first focusable widget in current dynamic content
            dynamic_content = self.query_one("#dynamic-content")
            focusable_widgets = dynamic_content.query("TextArea, Select, Input").filter(
                lambda w: (
                    w.can_focus
                    and not w.disabled
                    and not getattr(w, "read_only", False)
                    and w.display
                    and w.region.height > 0
                )
            )
            if focusable_widgets:
                first_widget = focusable_widgets.first()
                first_widget.focus()
                self._ensure_focused_visible()
        except Exception:
            pass


async def run_pipeline_tui(pipeline_path: Path, workspace_name: str) -> None:
    """Run the pipeline TUI application."""
    app = PipelineRunnerApp(pipeline_path, workspace_name)
    await app.run_async()


if __name__ == "__main__":
    # For testing
    import sys

    if len(sys.argv) > 1:
        pipeline_path = Path(sys.argv[1])
        workspace_name = sys.argv[2] if len(sys.argv) > 2 else "default"
        asyncio.run(run_pipeline_tui(pipeline_path, workspace_name))
