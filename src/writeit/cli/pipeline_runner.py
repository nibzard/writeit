# ABOUTME: CLI pipeline runner for non-interactive execution with simple prompts
# ABOUTME: Provides command-line interface for pipeline execution without TUI dependencies

import asyncio
import yaml
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import llm
from jinja2 import Template
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns

from writeit.workspace.workspace import Workspace
from writeit.llm.token_usage import TokenUsageTracker
from writeit.domains.content.services.output_export_service import (
    OutputExportService, 
    ExportMetadata, 
    ExportResult
)


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
    response_count: int = 1  # Number of responses to generate
    allow_feedback: bool = True  # Allow user feedback
    auto_approve: bool = False  # Auto-approve without user interaction


@dataclass
class PipelineConfig:
    """Represents the complete pipeline configuration."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    inputs: List[PipelineInput] = field(default_factory=list)
    steps: List[PipelineStep] = field(default_factory=list)


class CLIPipelineRunner:
    """CLI-based pipeline runner for non-interactive execution."""

    def __init__(self, pipeline_path: Path, workspace_name: str):
        self.pipeline_path = pipeline_path
        self.workspace_name = workspace_name
        self.pipeline_config: Optional[PipelineConfig] = None
        self.pipeline_values: Dict[str, Any] = {}
        self.step_results: Dict[str, Dict[str, Any]] = {}
        self.current_step_index = 0

        # Initialize dependencies
        self.console = Console()
        self.workspace_manager = Workspace()
        self.token_tracker = TokenUsageTracker()
        self.current_run_id: Optional[str] = None
        
        # Initialize export service
        self.export_service = OutputExportService(Path.home() / ".writeit")
        
        # Execution tracking
        self.execution_start_time: Optional[datetime] = None
        self.user_feedback: Dict[str, List[str]] = {}  # step_key -> feedback list

    def load_pipeline(self) -> None:
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
            defaults = raw_config.get("defaults", {})
            for key, config in raw_config.get("steps", {}).items():
                allow_feedback_final = config.get("allow_feedback", defaults.get("allow_feedback", True))
                
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
                        response_count=config.get("response_count", defaults.get("responses_per_step", 1)),
                        allow_feedback=allow_feedback_final,
                        auto_approve=config.get("auto_approve", defaults.get("auto_approve", False)),
                    )
                )

            self.pipeline_config = PipelineConfig(
                metadata=raw_config.get("metadata", {}),
                defaults=raw_config.get("defaults", {}),
                inputs=inputs,
                steps=steps,
            )

        except Exception as e:
            self.console.print(f"[red]Failed to load pipeline: {e}[/red]")
            raise

    def collect_inputs(self) -> bool:
        """Collect input values from user via CLI prompts."""
        if not self.pipeline_config or not self.pipeline_config.inputs:
            return True

        self.console.print("\n[bold blue]Pipeline Input Collection[/bold blue]")
        self.console.print(
            f"Pipeline: {self.pipeline_config.metadata.get('name', 'Unknown')}"
        )
        if desc := self.pipeline_config.metadata.get("description"):
            self.console.print(f"Description: {desc}")

        self.console.print()

        for input_field in self.pipeline_config.inputs:
            value = self._collect_single_input(input_field)
            if value is None and input_field.required:
                self.console.print(
                    f"[red]Required field '{input_field.label}' cannot be empty[/red]"
                )
                return False
            self.pipeline_values[input_field.key] = value

        return True

    def _collect_single_input(self, input_field: PipelineInput) -> Any:
        """Collect a single input value from user."""
        # Show help if available
        if input_field.help:
            self.console.print(f"[dim]{input_field.help}[/dim]")

        # Handle different input types
        if input_field.type == "text":
            return self._collect_text_input(input_field)
        elif input_field.type == "textarea":
            return self._collect_textarea_input(input_field)
        elif input_field.type in ["select", "choice"]:
            return self._collect_select_input(input_field)
        elif input_field.type == "radio":
            return self._collect_radio_input(input_field)
        else:
            # Fallback to text input
            return self._collect_text_input(input_field)

    def _collect_text_input(self, input_field: PipelineInput) -> str:
        """Collect text input from user."""
        prompt_text = input_field.label
        if not input_field.required and input_field.default:
            prompt_text += f" (default: {input_field.default})"

        try:
            value = Prompt.ask(
                prompt_text,
                default=str(input_field.default) if input_field.default is not None else "",
                show_default=bool(input_field.default),
            )
        except EOFError:
            # Handle non-interactive mode by using default or fallback
            if input_field.default is not None:
                value = str(input_field.default)
                self.console.print(f"[dim]Using default: {value}[/dim]")
            elif not input_field.required:
                value = ""
                self.console.print("[dim]Using empty value (optional field)[/dim]")
            else:
                # For testing purposes, use placeholder or sample value
                value = "Test AI and automation workflows"
                self.console.print(f"[dim]Using sample value for testing: {value}[/dim]")

        # Handle max_length validation
        if input_field.max_length and len(value) > input_field.max_length:
            self.console.print(
                f"[yellow]Input too long (max {input_field.max_length} chars), truncating...[/yellow]"
            )
            value = value[: input_field.max_length]

        return value

    def _collect_textarea_input(self, input_field: PipelineInput) -> str:
        """Collect multi-line text input from user."""
        self.console.print(f"{input_field.label}:")
        self.console.print(
            "[dim]Enter your text (press Ctrl+D or Ctrl+Z when finished):[/dim]"
        )

        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass

        value = "\n".join(lines)

        # Apply default if empty and not required
        if not value and not input_field.required and input_field.default:
            value = str(input_field.default)

        return value

    def _collect_select_input(self, input_field: PipelineInput) -> str:
        """Collect select input from user."""
        if not input_field.options:
            return self._collect_text_input(input_field)

        self.console.print(f"{input_field.label}:")
        choices = [opt["value"] for opt in input_field.options]
        labels = [
            f"{opt['value']} - {opt.get('label', opt['value'])}"
            for opt in input_field.options
        ]

        for i, label in enumerate(labels, 1):
            self.console.print(f"  {i}. {label}")

        while True:
            try:
                choice_idx = int(Prompt.ask("Select option (number)")) - 1
                if 0 <= choice_idx < len(choices):
                    return choices[choice_idx]
                else:
                    self.console.print(
                        "[red]Invalid selection. Please try again.[/red]"
                    )
            except (ValueError, EOFError):
                if isinstance(input_field.default, str) and input_field.default in choices:
                    self.console.print(f"[dim]Using default: {input_field.default}[/dim]")
                    return input_field.default
                elif choices:
                    self.console.print(f"[dim]Using first option for testing: {choices[0]}[/dim]")
                    return choices[0]
                else:
                    self.console.print("[red]Please enter a number.[/red]")

    def _collect_radio_input(self, input_field: PipelineInput) -> str:
        """Collect radio button input from user."""
        return self._collect_select_input(input_field)  # Same logic as select for CLI

    async def execute_pipeline(self) -> bool:
        """Execute all pipeline steps."""
        if not self.pipeline_config or not self.pipeline_config.steps:
            self.console.print("[yellow]No steps to execute[/yellow]")
            return True

        # Start token tracking and timing
        self.current_run_id = str(uuid.uuid4())
        self.execution_start_time = datetime.now()
        pipeline_name = self.pipeline_config.metadata.get("name", "Unknown Pipeline")
        self.token_tracker.start_pipeline_run(pipeline_name, self.current_run_id)

        self.console.print(
            f"\n[bold blue]Executing Pipeline: {pipeline_name}[/bold blue]"
        )
        self.console.print("─" * 60)

        for i, step in enumerate(self.pipeline_config.steps):
            self.console.print(
                f"\n[bold cyan]Step {i + 1}/{len(self.pipeline_config.steps)}: {step.name}[/bold cyan]"
            )
            self.console.print(f"[dim]{step.description}[/dim]")

            success = await self._execute_step(step)
            if not success:
                return False

        # End token tracking
        self.token_tracker.finish_current_run()

        # Show final results
        self._show_pipeline_summary()
        return True

    async def _execute_step(self, step: PipelineStep) -> bool:
        """Execute a single pipeline step with enhanced user interaction."""
        try:
            # Build base prompt from template
            base_prompt = self._build_prompt(step.prompt_template)
            
            # Show pre-execution options
            action = await self._get_step_action(step)
            
            if action == "skip":
                return Confirm.ask("Continue with remaining steps?", default=True)
            elif action == "quit":
                return False
            elif action == "guide":
                # Collect user guidance before execution
                guidance = await self._collect_user_guidance(step)
                if guidance:
                    # Add guidance to the prompt
                    enhanced_prompt = f"{base_prompt}\n\nUser guidance: {guidance}"
                    self.user_feedback.setdefault(step.key, []).append(guidance)
                else:
                    enhanced_prompt = base_prompt
            else:  # "continue"
                enhanced_prompt = base_prompt
            
            # Generate responses
            responses = await self._generate_multiple_responses(step, enhanced_prompt)
            
            if not responses:
                self.console.print("[red]Failed to generate any responses[/red]")
                try:
                    return Confirm.ask("Continue despite error?", default=False)
                except EOFError:
                    self.console.print("[dim]Auto-stopping due to error (non-interactive mode)[/dim]")
                    return False
            
            # Handle response selection
            selected_response = await self._handle_response_selection(step, responses)
            
            if not selected_response:
                try:
                    return Confirm.ask("Continue despite no selection?", default=False)
                except EOFError:
                    self.console.print("[dim]Auto-stopping due to no selection (non-interactive mode)[/dim]")
                    return False
            
            # Store results
            self.step_results[step.key] = {
                "response": selected_response,
                "approved": True,
                "all_responses": responses,
                "user_feedback": self.user_feedback.get(step.key, []),
            }
            
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error executing step {step.name}: {e}[/red]")
            return Confirm.ask("Continue despite error?", default=False)

    def _build_template_context(self) -> Dict[str, Any]:
        """Build template context for Jinja2 rendering."""
        context = {
            "inputs": self.pipeline_values,
            "steps": {},
            "defaults": self.pipeline_config.defaults if self.pipeline_config else {},
        }

        # Add step results
        for step_key, result in self.step_results.items():
            context["steps"][step_key] = {
                "selected_response": result.get("response", ""),
                "response": result.get("response", ""),
                "all_responses": result.get("all_responses", []),
                "user_feedback": result.get("user_feedback", []),
            }

        return context

    def _render_template(self, template_str: str) -> str:
        """Render a Jinja2 template string with current context."""
        if not template_str:
            return template_str

        try:
            template = Template(template_str)
            context = self._build_template_context()
            return template.render(**context)
        except Exception as e:
            # Fallback to original string if template rendering fails
            self.console.print(
                f"[yellow]Warning: Template rendering failed: {e}[/yellow]"
            )
            return template_str

    def _build_prompt(self, template: str) -> str:
        """Build prompt from template using collected values."""
        return self._render_template(template)

    def _get_llm_model(self, model_preference):
        """Get LLM model based on preference."""
        # Handle both string and list preferences
        if isinstance(model_preference, str):
            model_preference = [model_preference]
        elif not isinstance(model_preference, list):
            model_preference = []

        # Resolve template variables in model preferences
        resolved_preferences = []
        for model_name in model_preference:
            if isinstance(model_name, str):
                resolved_name = self._render_template(model_name)
                resolved_preferences.append(resolved_name)

        # Try preferred models first
        for model_name in resolved_preferences:
            try:
                return llm.get_model(model_name)
            except Exception:
                continue

        # Fallback to default model
        try:
            return llm.get_model()
        except Exception as e:
            raise RuntimeError(f"No LLM model available: {e}")
    
    async def _get_unified_action(self, context: str, has_response: bool = False, step: Optional[PipelineStep] = None) -> str:
        """Unified action menu for both steps and responses."""
        # Auto-approve check for steps
        if step and step.auto_approve:
            self.console.print(f"[dim]Auto-approving step: {step.name}[/dim]")
            return "continue"
        
        # Display context information
        if step:
            self.console.print(f"\n[bold cyan]Step: {step.name}[/bold cyan]")
            self.console.print(f"[dim]{step.description}[/dim]")
        
        # Fallback to simple prompt if feedback is disabled
        if step and step.allow_feedback is False:
            try:
                return "continue" if Confirm.ask(f"Execute step: {step.name}?", default=True) else "skip"
            except EOFError:
                self.console.print("[dim]Auto-continuing step (non-interactive mode)[/dim]")
                return "continue"
        
        while True:
            self.console.print(f"\n[bold]Choose an action:[/bold]")
            self.console.print("  [cyan][c][/cyan] Continue - Accept and proceed")
            self.console.print("  [cyan][g][/cyan] Guide - Add instructions and regenerate")
            
            # Show regenerate only for responses
            choices = ["c", "g", "s", "q", "?"]
            if has_response:
                self.console.print("  [cyan][r][/cyan] Regenerate - Try again with same prompt")
                choices.insert(2, "r")  # Insert 'r' before 's' and 'q'
            
            self.console.print("  [cyan][s][/cyan] Skip - Skip this step")
            self.console.print("  [cyan][q][/cyan] Quit - Stop pipeline")
            self.console.print("  [dim][?][/dim] Help - Show action explanations")
            
            try:
                choice = Prompt.ask("Action", choices=choices, default="c")
            except EOFError:
                self.console.print("[dim]Auto-continuing (non-interactive mode)[/dim]")
                return "continue"
            
            if choice == "c":
                return "continue"
            elif choice == "g":
                return "guide"
            elif choice == "r":
                return "regenerate"
            elif choice == "s":
                return "skip"
            elif choice == "q":
                return "quit"
            elif choice == "?":
                self._show_action_help(has_response)
                continue  # Show menu again after help

    def _show_action_help(self, has_response: bool = False) -> None:
        """Show help for available actions."""
        self.console.print("\n[bold cyan]Action Guide:[/bold cyan]")
        self.console.print("• [bold]Continue[/bold]: Use the current result and move forward")
        self.console.print("• [bold]Guide[/bold]: Provide instructions to improve/modify the output")
        if has_response:
            self.console.print("• [bold]Regenerate[/bold]: Get a fresh response with the same prompt")
        self.console.print("• [bold]Skip[/bold]: Move to next step without using this output")
        self.console.print("• [bold]Quit[/bold]: Stop the entire pipeline execution")

    async def _get_step_action(self, step: PipelineStep) -> str:
        """Get user action for step execution."""
        return await self._get_unified_action("step execution", has_response=False, step=step)
    
    async def _collect_user_guidance(self, step: PipelineStep) -> Optional[str]:
        """Collect user guidance for a step."""
        self.console.print(f"\n[bold yellow]Provide guidance for: {step.name}[/bold yellow]")
        self.console.print("[dim]Your instructions will guide the AI to improve the output.[/dim]")
        self.console.print("[dim]Press Enter twice when finished, or just Enter to skip.[/dim]")
        
        lines = []
        empty_line_count = 0
        
        while True:
            try:
                line = input(">>> ")
                if not line.strip():
                    empty_line_count += 1
                    if empty_line_count >= 2 or (empty_line_count >= 1 and not lines):
                        break
                else:
                    empty_line_count = 0
                    lines.append(line)
            except (EOFError, KeyboardInterrupt):
                break
        
        guidance = "\n".join(lines).strip()
        return guidance if guidance else None
    
    async def _collect_response_guidance(self) -> Optional[str]:
        """Collect user guidance for response modification."""
        self.console.print(f"\n[bold yellow]Provide guidance to improve the response:[/bold yellow]")
        self.console.print("[dim]Your instructions will guide the AI to modify the output.[/dim]")
        self.console.print("[dim]Press Enter twice when finished, or just Enter to skip.[/dim]")
        
        lines = []
        empty_line_count = 0
        
        while True:
            try:
                line = input(">>> ")
                if not line.strip():
                    empty_line_count += 1
                    if empty_line_count >= 2 or (empty_line_count >= 1 and not lines):
                        break
                else:
                    empty_line_count = 0
                    lines.append(line)
            except (EOFError, KeyboardInterrupt):
                break
        
        guidance = "\n".join(lines).strip()
        return guidance if guidance else None
    
    async def _generate_multiple_responses(self, step: PipelineStep, prompt: str) -> List[str]:
        """Generate multiple responses for a step."""
        responses = []
        model = self._get_llm_model(step.model_preference)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            for i in range(step.response_count):
                task_desc = f"Generating response {i+1}/{step.response_count}..."
                task = progress.add_task(task_desc, total=None)
                
                try:
                    # Execute LLM call
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: model.prompt(prompt)
                    )
                    
                    # Extract response text
                    if hasattr(response, "text") and callable(response.text):
                        response_text = response.text()
                    elif hasattr(response, "text"):
                        response_text = str(response.text)
                    else:
                        response_text = str(response)
                    
                    responses.append(response_text)
                    
                    # Track token usage for first response only to avoid double counting
                    if i == 0 and hasattr(response, "usage"):
                        model_name = (
                            step.model_preference[0]
                            if step.model_preference
                            else "unknown"
                        )
                        self.token_tracker.track_step_usage(
                            step.key, step.name, model_name, response
                        )
                    
                    progress.update(task, completed=100)
                    
                except Exception as e:
                    self.console.print(f"[red]Failed to generate response {i+1}: {e}[/red]")
                    progress.update(task, completed=100)
        
        return responses
    
    async def _handle_response_selection(self, step: PipelineStep, responses: List[str]) -> Optional[str]:
        """Handle response selection and approval."""
        if not responses:
            return None
        
        if len(responses) == 1:
            # Single response - show and ask for approval
            self.console.print("\n[bold green]Response:[/bold green]")
            self.console.print(Panel(responses[0], expand=False))
            
            if step.auto_approve:
                return responses[0]
            
            while True:
                action = await self._get_unified_action("response handling", has_response=True)
                
                if action == "continue":
                    return responses[0]
                elif action == "regenerate":
                    # Regenerate with same prompt
                    new_responses = await self._generate_multiple_responses(step, self._build_prompt(step.prompt_template))
                    if new_responses:
                        responses = new_responses
                        self.console.print("\n[bold green]Response:[/bold green]")
                        self.console.print(Panel(responses[0], expand=False))
                        continue
                    else:
                        self.console.print("[red]Failed to regenerate. Using original response.[/red]")
                        return responses[0]
                elif action == "guide":
                    # Get guidance and regenerate
                    guidance = await self._collect_response_guidance()
                    if guidance:
                        enhanced_prompt = f"{self._build_prompt(step.prompt_template)}\n\nUser guidance: {guidance}"
                        new_responses = await self._generate_multiple_responses(step, enhanced_prompt)
                        if new_responses:
                            responses = new_responses
                            self.console.print("\n[bold green]Response:[/bold green]")
                            self.console.print(Panel(responses[0], expand=False))
                            continue
                    # If no guidance or failed regeneration, continue with menu
                    continue
                elif action == "skip":
                    return None
                elif action == "quit":
                    return None
        else:
            # Multiple responses - show all and let user choose
            return await self._select_from_multiple_responses(step, responses)
    
    async def _select_from_multiple_responses(self, step: PipelineStep, responses: List[str]) -> Optional[str]:
        """Handle selection from multiple responses."""
        self.console.print(f"\n[bold green]Generated {len(responses)} responses:[/bold green]")
        
        # Display all responses with numbers
        for i, response in enumerate(responses, 1):
            self.console.print(f"\n[bold cyan]Response {i}:[/bold cyan]")
            # Show truncated version for selection
            preview = response[:200] + "..." if len(response) > 200 else response
            self.console.print(Panel(preview, title=f"Option {i}", expand=False))
        
        while True:
            self.console.print("\nOptions:")
            for i in range(len(responses)):
                self.console.print(f"  [{i+1}] - Select response {i+1}")
            self.console.print(f"  [v] - View full responses")
            self.console.print(f"  [r] - Regenerate all responses")
            self.console.print(f"  [s] - Skip this step")
            
            try:
                choice = Prompt.ask("Choice", default="1")
            except EOFError:
                self.console.print("[dim]Auto-selecting first response (non-interactive mode)[/dim]")
                choice = "1"
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(responses):
                    # Show full selected response for confirmation
                    self.console.print(f"\n[bold yellow]Selected Response {idx+1}:[/bold yellow]")
                    self.console.print(Panel(responses[idx], expand=False))
                    
                    try:
                        if Confirm.ask("Continue with this response?", default=True):
                            return responses[idx]
                    except EOFError:
                        self.console.print("[dim]Auto-continuing with response (non-interactive mode)[/dim]")
                        return responses[idx]
            elif choice.lower() == "v":
                # Show all full responses
                for i, response in enumerate(responses, 1):
                    self.console.print(f"\n[bold magenta]Full Response {i}:[/bold magenta]")
                    self.console.print(Panel(response, title=f"Response {i}", expand=False))
            elif choice.lower() == "r":
                # Regenerate all responses
                new_responses = await self._generate_multiple_responses(step, self._build_prompt(step.prompt_template))
                if new_responses:
                    responses = new_responses
                    self.console.print(f"\n[bold green]Regenerated {len(responses)} new responses:[/bold green]")
                    # Show preview of new responses
                    for i, response in enumerate(responses, 1):
                        preview = response[:200] + "..." if len(response) > 200 else response
                        self.console.print(f"\n[cyan]Response {i} (preview):[/cyan] {preview}")
            elif choice.lower() == "s":
                return None
            else:
                self.console.print("[red]Invalid choice. Please try again.[/red]")
    

    def _show_pipeline_summary(self) -> None:
        """Show pipeline execution summary with export functionality."""
        self.console.print("\n" + "─" * 60)
        self.console.print("\n[bold green]🎉 Pipeline Completed![/bold green]")
        
        # Calculate execution time
        execution_time = None
        if self.execution_start_time:
            execution_time = (datetime.now() - self.execution_start_time).total_seconds()
            self.console.print(f"Execution time: {execution_time:.1f} seconds")

        # Show token usage summary if available
        token_usage = {"input": 0, "output": 0, "total": 0}
        if self.token_tracker.completed_runs:
            last_run = self.token_tracker.completed_runs[-1]
            token_usage = {
                "input": last_run.total_input_tokens,
                "output": last_run.total_output_tokens,
                "total": last_run.total_input_tokens + last_run.total_output_tokens
            }
            
            self.console.print("\n[bold cyan]Token Usage Summary:[/bold cyan]")
            self.console.print(f"  Input Tokens: {token_usage['input']:,}")
            self.console.print(f"  Output Tokens: {token_usage['output']:,}")
            self.console.print(f"  Total Tokens: {token_usage['total']:,}")

        # Show step results summary
        self.console.print(f"\n[bold]Steps completed:[/bold]")
        for step_key, result in self.step_results.items():
            status = "✅ Completed" if result.get("approved", True) else "⚠️  Not approved"
            feedback_count = len(result.get("user_feedback", []))
            response_count = len(result.get("all_responses", [result.get("response", "")]))
            
            extra_info = []
            if feedback_count > 0:
                extra_info.append(f"{feedback_count} feedback")
            if response_count > 1:
                extra_info.append(f"{response_count} responses")
            
            extra_str = f" ({', '.join(extra_info)})" if extra_info else ""
            self.console.print(f"  {step_key}: {status}{extra_str}")
        
        # Auto-save pipeline output
        asyncio.create_task(self._save_pipeline_output(execution_time, token_usage))
    
    async def _save_pipeline_output(self, execution_time: Optional[float], token_usage: Dict[str, int]) -> None:
        """Save pipeline output to workspace."""
        try:
            if not self.step_results:
                self.console.print("\n[yellow]No outputs to save[/yellow]")
                return
            
            # Extract step results for export
            step_outputs = {}
            for step_key, result in self.step_results.items():
                step_outputs[step_key] = result.get("response", "")
            
            # Create export metadata
            pipeline_name = self.pipeline_config.metadata.get("name", "Unknown Pipeline")
            metadata = ExportMetadata(
                pipeline_name=pipeline_name,
                workspace_name=self.workspace_name,
                execution_id=self.current_run_id or str(uuid.uuid4()),
                created_at=self.execution_start_time or datetime.now(),
                template_version=self.pipeline_config.metadata.get("version"),
                total_steps=len(self.step_results),
                token_usage=token_usage,
                execution_time_seconds=execution_time
            )
            
            # Export the output
            result = await self.export_service.export_step_outputs(
                step_outputs,
                metadata,
                include_intermediate=False  # Only save final output by default
            )
            
            if result.success and result.file_path:
                self.console.print(f"\n[bold green]✅ Output saved to:[/bold green]")
                self.console.print(f"   [cyan]{result.file_path}[/cyan]")
                
                # Show workspace and pipeline info
                self.console.print(f"\n[bold cyan]Execution Summary:[/bold cyan]")
                self.console.print(f"  Pipeline: {pipeline_name}")
                self.console.print(f"  Workspace: {self.workspace_name}")
                self.console.print(f"  File: {result.file_path.name}")
                
                # Ask if user wants to view the file
                try:
                    if Confirm.ask("\nWould you like to view the saved file?", default=False):
                        self._show_saved_file_content(result.file_path)
                except EOFError:
                    self.console.print("[dim]Skipping file preview (non-interactive mode)[/dim]")
            else:
                self.console.print(f"\n[red]❌ Failed to save output: {result.error_message}[/red]")
                
        except Exception as e:
            self.console.print(f"\n[red]Error saving output: {e}[/red]")
    
    def _show_saved_file_content(self, file_path: Path) -> None:
        """Show the content of the saved file."""
        try:
            content = file_path.read_text(encoding='utf-8')
            self.console.print(f"\n[bold cyan]Content of {file_path.name}:[/bold cyan]")
            self.console.print(Panel(content, title=str(file_path), expand=False))
        except Exception as e:
            self.console.print(f"[red]Error reading file: {e}[/red]")

    async def run(self) -> int:
        """Main entry point for CLI pipeline execution."""
        try:
            # Load pipeline configuration
            self.load_pipeline()

            # Collect inputs
            if not self.collect_inputs():
                return 1

            # Execute pipeline
            if not await self.execute_pipeline():
                return 1

            return 0

        except KeyboardInterrupt:
            self.console.print(
                "\n[yellow]Pipeline execution cancelled by user[/yellow]"
            )
            return 130
        except Exception as e:
            self.console.print(f"[red]Pipeline execution failed: {e}[/red]")
            return 1


async def run_pipeline_cli(pipeline_path: Path, workspace_name: str) -> int:
    """Entry point for CLI pipeline execution."""
    runner = CLIPipelineRunner(pipeline_path, workspace_name)
    return await runner.run()
