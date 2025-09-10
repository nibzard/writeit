# ABOUTME: CLI pipeline runner for non-interactive execution with simple prompts
# ABOUTME: Provides command-line interface for pipeline execution without TUI dependencies

import asyncio
import yaml
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

import llm
from jinja2 import Template
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

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

    def load_pipeline(self) -> None:
        """Load and parse the pipeline configuration."""
        try:
            with open(self.pipeline_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            # Parse inputs
            inputs = []
            for key, config in raw_config.get('inputs', {}).items():
                inputs.append(PipelineInput(
                    key=key,
                    type=config['type'],
                    label=config['label'],
                    required=config.get('required', False),
                    default=config.get('default'),
                    placeholder=config.get('placeholder', ''),
                    help=config.get('help', ''),
                    options=config.get('options', []),
                    max_length=config.get('max_length')
                ))
            
            # Parse steps
            steps = []
            for key, config in raw_config.get('steps', {}).items():
                steps.append(PipelineStep(
                    key=key,
                    name=config['name'],
                    description=config['description'],
                    type=config['type'],
                    prompt_template=config['prompt_template'],
                    selection_prompt=config.get('selection_prompt', ''),
                    model_preference=config.get('model_preference', []),
                    validation=config.get('validation', {}),
                    ui=config.get('ui', {})
                ))
            
            self.pipeline_config = PipelineConfig(
                metadata=raw_config.get('metadata', {}),
                defaults=raw_config.get('defaults', {}),
                inputs=inputs,
                steps=steps
            )
            
        except Exception as e:
            self.console.print(f"[red]Failed to load pipeline: {e}[/red]")
            raise

    def collect_inputs(self) -> bool:
        """Collect input values from user via CLI prompts."""
        if not self.pipeline_config or not self.pipeline_config.inputs:
            return True
        
        self.console.print("\n[bold blue]Pipeline Input Collection[/bold blue]")
        self.console.print(f"Pipeline: {self.pipeline_config.metadata.get('name', 'Unknown')}")
        if desc := self.pipeline_config.metadata.get('description'):
            self.console.print(f"Description: {desc}")
        
        self.console.print()
        
        for input_field in self.pipeline_config.inputs:
            value = self._collect_single_input(input_field)
            if value is None and input_field.required:
                self.console.print(f"[red]Required field '{input_field.label}' cannot be empty[/red]")
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
        
        value = Prompt.ask(
            prompt_text,
            default=str(input_field.default) if input_field.default is not None else "",
            show_default=bool(input_field.default)
        )
        
        # Handle max_length validation
        if input_field.max_length and len(value) > input_field.max_length:
            self.console.print(f"[yellow]Input too long (max {input_field.max_length} chars), truncating...[/yellow]")
            value = value[:input_field.max_length]
        
        return value

    def _collect_textarea_input(self, input_field: PipelineInput) -> str:
        """Collect multi-line text input from user."""
        self.console.print(f"{input_field.label}:")
        self.console.print("[dim]Enter your text (press Ctrl+D or Ctrl+Z when finished):[/dim]")
        
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except (EOFError, KeyboardInterrupt):
            pass
        
        value = '\n'.join(lines)
        
        # Apply default if empty and not required
        if not value and not input_field.required and input_field.default:
            value = str(input_field.default)
        
        return value

    def _collect_select_input(self, input_field: PipelineInput) -> str:
        """Collect select input from user."""
        if not input_field.options:
            return self._collect_text_input(input_field)
        
        self.console.print(f"{input_field.label}:")
        choices = [opt['value'] for opt in input_field.options]
        labels = [f"{opt['value']} - {opt.get('label', opt['value'])}" for opt in input_field.options]
        
        for i, label in enumerate(labels, 1):
            self.console.print(f"  {i}. {label}")
        
        while True:
            try:
                choice_idx = int(Prompt.ask("Select option (number)")) - 1
                if 0 <= choice_idx < len(choices):
                    return choices[choice_idx]
                else:
                    self.console.print("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number.[/red]")

    def _collect_radio_input(self, input_field: PipelineInput) -> str:
        """Collect radio button input from user."""
        return self._collect_select_input(input_field)  # Same logic as select for CLI

    async def execute_pipeline(self) -> bool:
        """Execute all pipeline steps."""
        if not self.pipeline_config or not self.pipeline_config.steps:
            self.console.print("[yellow]No steps to execute[/yellow]")
            return True
        
        # Start token tracking
        self.current_run_id = str(uuid.uuid4())
        pipeline_name = self.pipeline_config.metadata.get('name', 'Unknown Pipeline')
        self.token_tracker.start_pipeline_run(pipeline_name, self.current_run_id)
        
        self.console.print(f"\n[bold blue]Executing Pipeline: {pipeline_name}[/bold blue]")
        
        for i, step in enumerate(self.pipeline_config.steps):
            self.console.print(f"\n[bold]Step {i+1}/{len(self.pipeline_config.steps)}: {step.name}[/bold]")
            self.console.print(f"[dim]{step.description}[/dim]")
            
            success = await self._execute_step(step)
            if not success:
                return False
        
        # End token tracking
        finished_run = self.token_tracker.finish_current_run()
        
        # Show final results
        self._show_pipeline_summary()
        return True

    async def _execute_step(self, step: PipelineStep) -> bool:
        """Execute a single pipeline step."""
        try:
            # Build prompt from template
            prompt = self._build_prompt(step.prompt_template)
            
            # Show user what we're going to do
            if Confirm.ask(f"Execute step: {step.name}?", default=True):
                
                # Execute LLM call with progress indicator
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    console=self.console,
                    transient=True,
                ) as progress:
                    task = progress.add_task("Processing with LLM...", total=None)
                    
                    # Get LLM model
                    model = self._get_llm_model(step.model_preference)
                    
                    # Execute LLM call
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, lambda: model.prompt(prompt)
                    )
                    
                    # Track token usage
                    if hasattr(response, 'usage'):
                        model_name = step.model_preference[0] if step.model_preference else "unknown"
                        self.token_tracker.track_step_usage(
                            step.key, step.name, model_name, response
                        )
                    
                    progress.update(task, completed=100)
                
                # Display response
                self.console.print("\n[bold green]Response:[/bold green]")
                if hasattr(response, 'text') and callable(response.text):
                    response_text = response.text()
                elif hasattr(response, 'text'):
                    response_text = str(response.text)
                else:
                    response_text = str(response)
                self.console.print(Panel(response_text, expand=False))
                
                # Ask for user feedback/approval
                if step.type == "generate":
                    approved = Confirm.ask("Accept this response?", default=True)
                    if not approved:
                        retry = Confirm.ask("Regenerate?", default=True)
                        if retry:
                            return await self._execute_step(step)  # Recursive retry
                        else:
                            return False
                
                # Store results
                if hasattr(response, 'text') and callable(response.text):
                    response_text = response.text()
                elif hasattr(response, 'text'):
                    response_text = str(response.text)
                else:
                    response_text = str(response)
                    
                self.step_results[step.key] = {
                    "response": response_text,
                    "approved": True
                }
                
                return True
            else:
                # User chose to skip step
                return Confirm.ask("Continue with remaining steps?", default=True)
                
        except Exception as e:
            self.console.print(f"[red]Error executing step {step.name}: {e}[/red]")
            return Confirm.ask("Continue despite error?", default=False)

    def _build_template_context(self) -> Dict[str, Any]:
        """Build template context for Jinja2 rendering."""
        context = {
            'inputs': self.pipeline_values,
            'steps': {},
            'defaults': self.pipeline_config.defaults if self.pipeline_config else {}
        }
        
        # Add step results
        for step_key, result in self.step_results.items():
            context['steps'][step_key] = {
                'selected_response': result.get('response', ''),
                'response': result.get('response', '')
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
            self.console.print(f"[yellow]Warning: Template rendering failed: {e}[/yellow]")
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

    def _show_pipeline_summary(self) -> None:
        """Show pipeline execution summary."""
        self.console.print("\n[bold green]Pipeline Completed![/bold green]")
        
        # Show token usage summary if available
        if self.token_tracker.completed_runs:
            last_run = self.token_tracker.completed_runs[-1]
            self.console.print("\nToken Usage Summary:")
            self.console.print(f"  Total Input Tokens: {last_run.total_input_tokens}")
            self.console.print(f"  Total Output Tokens: {last_run.total_output_tokens}")
            self.console.print(f"  Total Steps: {len(last_run.steps)}")
        
        # Show step results summary
        self.console.print(f"\nExecuted {len(self.step_results)} steps:")
        for step_key, result in self.step_results.items():
            status = "✅ Completed" if result.get('approved', True) else "⚠️  Not approved"
            self.console.print(f"  {step_key}: {status}")

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
            self.console.print("\n[yellow]Pipeline execution cancelled by user[/yellow]")
            return 130
        except Exception as e:
            self.console.print(f"[red]Pipeline execution failed: {e}[/red]")
            return 1


async def run_pipeline_cli(pipeline_path: Path, workspace_name: str) -> int:
    """Entry point for CLI pipeline execution."""
    runner = CLIPipelineRunner(pipeline_path, workspace_name)
    return await runner.run()
