# ABOUTME: Core pipeline execution engine for WriteIt
# ABOUTME: Handles step-by-step execution with LLM integration and state management

import uuid
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import yaml
from datetime import datetime, UTC

from writeit.models import (
    Pipeline,
    PipelineStep as ModelStep,
    PipelineRun,
    StepExecution,
)
from writeit.storage.adapter import create_storage_adapter
from writeit.storage import StorageManager
from writeit.workspace.workspace import Workspace
from writeit.llm.token_usage import TokenUsageTracker
from writeit.llm.cache import LLMCache, CachedLLMClient
from writeit.domains.pipeline.errors import PipelineError, StepExecutionError, PipelineValidationError as ValidationError


@dataclass
class ExecutionContext:
    """Context passed between pipeline steps."""

    pipeline_id: str
    run_id: str
    workspace_name: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    step_outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_tracker: Optional[TokenUsageTracker] = None


@dataclass
class StepResult:
    """Result of executing a single step."""

    step_key: str
    responses: List[str]
    selected_response: Optional[str] = None
    user_feedback: str = ""
    tokens_used: Dict[str, int] = field(default_factory=dict)
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PipelineExecutor:
    """Core engine for executing WriteIt pipelines."""

    def __init__(
        self,
        workspace: Workspace,
        storage: StorageManager,
        workspace_name: str = "default",
    ):
        self.workspace = workspace
        self.storage = storage
        self.workspace_name = workspace_name
        self.active_runs: Dict[str, PipelineRun] = {}

        # Initialize caching
        self.llm_cache = LLMCache(storage, workspace_name)
        self.cached_llm_client = CachedLLMClient(self.llm_cache)

    async def load_pipeline(self, pipeline_path: Path) -> Pipeline:
        """Load and validate a pipeline configuration."""
        try:
            with open(pipeline_path, "r") as f:
                raw_config = yaml.safe_load(f)

            # Parse and validate pipeline structure
            pipeline = Pipeline(
                id=str(uuid.uuid4()),
                name=raw_config.get("metadata", {}).get("name", pipeline_path.stem),
                description=raw_config.get("metadata", {}).get("description", ""),
                version=raw_config.get("metadata", {}).get("version", "1.0.0"),
                metadata=raw_config.get("metadata", {}),
                defaults=raw_config.get("defaults", {}),
                inputs={},
                steps=[],
            )

            # Parse inputs
            for key, config in raw_config.get("inputs", {}).items():
                pipeline.inputs[key] = {
                    "type": config["type"],
                    "label": config["label"],
                    "required": config.get("required", False),
                    "default": config.get("default"),
                    "placeholder": config.get("placeholder", ""),
                    "help": config.get("help", ""),
                    "options": config.get("options", []),
                    "max_length": config.get("max_length"),
                }

            # Parse steps
            for key, config in raw_config.get("steps", {}).items():
                step = ModelStep(
                    key=key,
                    name=config["name"],
                    description=config["description"],
                    type=config["type"],
                    prompt_template=config["prompt_template"],
                    selection_prompt=config.get("selection_prompt", ""),
                    model_preference=config.get("model_preference", []),
                    validation=config.get("validation", {}),
                    ui=config.get("ui", {}),
                    depends_on=config.get("depends_on", []),
                )
                pipeline.steps.append(step)

            return pipeline

        except Exception as e:
            raise PipelineError(
                f"Failed to load pipeline from {pipeline_path}: {str(e)}"
            )

    async def create_run(
        self, pipeline: Pipeline, inputs: Dict[str, Any], workspace_name: str
    ) -> str:
        """Create a new pipeline run."""
        run_id = str(uuid.uuid4())

        # Validate inputs
        await self._validate_inputs(pipeline, inputs)

        # Create run record
        run = PipelineRun(
            id=run_id,
            pipeline_id=pipeline.id,
            workspace_name=workspace_name,
            inputs=inputs,
            status="created",
            created_at=datetime.now(UTC),
            steps=[],
        )

        # Store in memory and persistent storage
        self.active_runs[run_id] = run
        await self._store_pipeline_run(run)

        return run_id

    async def execute_run(
        self,
        run_id: str,
        pipeline: Pipeline,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        response_callback: Optional[Callable[[str, str], None]] = None,
    ) -> PipelineRun:
        """Execute a complete pipeline run."""
        if run_id not in self.active_runs:
            raise PipelineError(f"Run {run_id} not found")

        run = self.active_runs[run_id]
        run.status = "running"
        run.started_at = datetime.now(UTC)

        # Initialize execution context
        context = ExecutionContext(
            pipeline_id=pipeline.id,
            run_id=run_id,
            workspace_name=run.workspace_name,
            inputs=run.inputs,
            token_tracker=TokenUsageTracker(),
        )

        try:
            # Execute steps in order
            for i, step in enumerate(pipeline.steps):
                if progress_callback:
                    progress_callback(
                        "step_start",
                        {
                            "step_index": i,
                            "step_key": step.key,
                            "step_name": step.name,
                            "total_steps": len(pipeline.steps),
                        },
                    )

                # Execute step
                step_result = await self.execute_step(
                    step, context, pipeline, response_callback
                )

                # Create step execution record
                step_execution = StepExecution(
                    step_key=step.key,
                    status="completed",
                    started_at=datetime.now(UTC),
                    responses=step_result.responses,
                    selected_response=step_result.selected_response,
                    user_feedback=step_result.user_feedback,
                    tokens_used=step_result.tokens_used,
                    execution_time=step_result.execution_time,
                )

                run.steps.append(step_execution)

                # Update context with step output
                context.step_outputs[step.key] = (
                    step_result.selected_response or step_result.responses[0]
                )

                if progress_callback:
                    progress_callback(
                        "step_complete",
                        {
                            "step_index": i,
                            "step_key": step.key,
                            "responses": step_result.responses,
                            "selected": step_result.selected_response,
                        },
                    )

            # Mark run as completed
            run.status = "completed"
            run.completed_at = datetime.now(UTC)

        except Exception as e:
            run.status = "failed"
            run.error = str(e)
            run.completed_at = datetime.now(UTC)
            raise StepExecutionError(f"Pipeline execution failed: {str(e)}")

        finally:
            await self._store_pipeline_run(run)

        return run

    async def execute_step(
        self,
        step: ModelStep,
        context: ExecutionContext,
        pipeline: Pipeline,
        response_callback: Optional[Callable[[str, str], None]] = None,
    ) -> StepResult:
        """Execute a single pipeline step."""
        start_time = datetime.now(UTC)

        try:
            # Render prompt template
            rendered_prompt = self._render_prompt_template(
                step.prompt_template, context, pipeline
            )

            # Determine model to use
            model_name = self._select_model(step.model_preference, pipeline.defaults)

            # Execute LLM call
            responses = await self._execute_llm_call(
                rendered_prompt, model_name, context, response_callback
            )

            # Calculate execution time
            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            return StepResult(
                step_key=step.key,
                responses=responses,
                execution_time=execution_time,
                tokens_used=context.token_tracker.get_step_usage(step.key)
                if context.token_tracker
                else {},
            )

        except Exception as e:
            raise StepExecutionError(f"Failed to execute step {step.key}: {str(e)}")

    def _render_prompt_template(
        self, template: str, context: ExecutionContext, pipeline: Pipeline
    ) -> str:
        """Render a prompt template with context variables."""
        rendered = template

        # Replace input variables
        for key, value in context.inputs.items():
            rendered = rendered.replace(f"{{{{ inputs.{key} }}}}", str(value))

        # Replace step output variables
        for key, value in context.step_outputs.items():
            rendered = rendered.replace(f"{{{{ steps.{key} }}}}", str(value))

        # Replace defaults
        for key, value in pipeline.defaults.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    rendered = rendered.replace(
                        f"{{{{ defaults.{key}.{sub_key} }}}}", str(sub_value)
                    )
            else:
                rendered = rendered.replace(f"{{{{ defaults.{key} }}}}", str(value))

        return rendered

    def _select_model(self, preferences: List[str], defaults: Dict[str, Any]) -> str:
        """Select the best available model from preferences."""
        if not preferences:
            return defaults.get("model", "gpt-4o-mini")

        # Use first preference (later we can add fallback logic)
        model_name = (
            preferences[0] if isinstance(preferences, list) else str(preferences)
        )

        # Apply defaults template substitution
        for key, value in defaults.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    model_name = model_name.replace(
                        f"{{{{ defaults.{key}.{sub_key} }}}}", str(sub_value)
                    )
            else:
                model_name = model_name.replace(f"{{{{ defaults.{key} }}}}", str(value))

        return model_name

    async def _execute_llm_call(
        self,
        prompt: str,
        model_name: str,
        context: ExecutionContext,
        response_callback: Optional[Callable[[str, str], None]] = None,
    ) -> List[str]:
        """Execute an LLM API call and return responses."""
        try:
            # Start token tracking for this step
            if context.token_tracker:
                context.token_tracker.start_step(context.run_id, model_name)

            # Prepare cache context
            cache_context = {
                "run_id": context.run_id,
                "pipeline_id": context.pipeline_id,
                "step_outputs": context.step_outputs,
            }

            # Make cached API call
            full_response, tokens_used = await self.cached_llm_client.prompt(
                prompt, model_name, cache_context
            )

            # Track token usage
            if context.token_tracker:
                context.token_tracker.add_usage(
                    model_name,
                    tokens_used.get("prompt_tokens", 0),
                    tokens_used.get("completion_tokens", 0),
                )

            # Call response callback if provided
            if response_callback:
                response_callback("response", full_response)

            return [full_response]

        except Exception as e:
            raise StepExecutionError(
                f"LLM call failed for model {model_name}: {str(e)}"
            )

    async def _validate_inputs(
        self, pipeline: Pipeline, inputs: Dict[str, Any]
    ) -> None:
        """Validate pipeline inputs."""
        for key, config in pipeline.inputs.items():
            if config.get("required", False):
                if key not in inputs or not inputs[key]:
                    raise ValidationError(f"Required input '{key}' is missing")

            # Type validation
            if key in inputs:
                value = inputs[key]
                expected_type = config.get("type")

                if expected_type == "text" and not isinstance(value, str):
                    raise ValidationError(f"Input '{key}' must be text")
                elif expected_type == "choice":
                    valid_options = [
                        opt.get("value") for opt in config.get("options", [])
                    ]
                    if value not in valid_options:
                        raise ValidationError(
                            f"Input '{key}' must be one of: {valid_options}"
                        )

    async def _store_pipeline_run(self, run: PipelineRun) -> None:
        """Store pipeline run to persistent storage."""
        try:
            # Serialize run data
            run_data = {
                "id": run.id,
                "pipeline_id": run.pipeline_id,
                "workspace_name": run.workspace_name,
                "inputs": run.inputs,
                "status": run.status,
                "created_at": run.created_at.isoformat() if run.created_at else None,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "completed_at": run.completed_at.isoformat()
                if run.completed_at
                else None,
                "error": run.error,
                "steps": [
                    {
                        "step_key": step.step_key,
                        "status": step.status,
                        "started_at": step.started_at.isoformat()
                        if step.started_at
                        else None,
                        "responses": step.responses,
                        "selected_response": step.selected_response,
                        "user_feedback": step.user_feedback,
                        "tokens_used": step.tokens_used,
                        "execution_time": step.execution_time,
                    }
                    for step in run.steps
                ],
            }

            # Store in LMDB
            await self.storage.store_json(
                f"pipeline_run_{run.id}", run_data, db_name="pipeline_runs"
            )

        except Exception as e:
            # Log error but don't fail pipeline execution
            print(f"Warning: Failed to store pipeline run {run.id}: {e}")

    async def get_run(self, run_id: str) -> Optional[PipelineRun]:
        """Retrieve a pipeline run."""
        if run_id in self.active_runs:
            return self.active_runs[run_id]

        # Try loading from storage
        try:
            run_data = await self.storage.get_json(
                f"pipeline_run_{run_id}", db_name="pipeline_runs"
            )
            if run_data:
                # Reconstruct PipelineRun object
                # TODO: Implement full deserialization
                pass
        except Exception:
            pass

        return None
