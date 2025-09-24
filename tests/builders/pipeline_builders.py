"""Test data builders for Pipeline domain entities."""

from datetime import datetime
from typing import Dict, Any, List, Optional, Self
from dataclasses import replace

from src.writeit.domains.pipeline.entities.pipeline_template import (
    PipelineTemplate, PipelineStepTemplate, PipelineInput
)
from src.writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from src.writeit.domains.pipeline.entities.pipeline_step import StepExecution
from src.writeit.domains.pipeline.value_objects.step_name import StepName
from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from src.writeit.domains.pipeline.value_objects.step_id import StepId
from src.writeit.domains.pipeline.value_objects.prompt_template import PromptTemplate
from src.writeit.domains.pipeline.value_objects.model_preference import ModelPreference
from src.writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus, PipelineExecutionStatus, StepExecutionStatus


class PipelineInputBuilder:
    """Builder for PipelineInput test data."""
    
    def __init__(self) -> None:
        self._key = "default_input"
        self._type = "text"
        self._label = "Default Input"
        self._required = False
        self._default = None
        self._placeholder = ""
        self._help = ""
        self._options = []
        self._max_length = None
        self._validation = {}
    
    def with_key(self, key: str) -> Self:
        """Set the input key."""
        self._key = key
        return self
    
    def with_type(self, input_type: str) -> Self:
        """Set the input type."""
        self._type = input_type
        return self
    
    def with_label(self, label: str) -> Self:
        """Set the input label."""
        self._label = label
        return self
    
    def required(self) -> Self:
        """Mark the input as required."""
        self._required = True
        return self
    
    def optional(self) -> Self:
        """Mark the input as optional."""
        self._required = False
        return self
    
    def with_default(self, default: Any) -> Self:
        """Set the default value."""
        self._default = default
        return self
    
    def with_placeholder(self, placeholder: str) -> Self:
        """Set the placeholder text."""
        self._placeholder = placeholder
        return self
    
    def with_help(self, help_text: str) -> Self:
        """Set the help text."""
        self._help = help_text
        return self
    
    def with_options(self, options: List[Dict[str, str]]) -> Self:
        """Set the options for choice inputs."""
        self._options = options
        return self
    
    def with_max_length(self, max_length: int) -> Self:
        """Set the maximum length."""
        self._max_length = max_length
        return self
    
    def with_validation(self, validation: Dict[str, Any]) -> Self:
        """Set validation rules."""
        self._validation = validation
        return self
    
    def build(self) -> PipelineInput:
        """Build the PipelineInput."""
        return PipelineInput(
            key=self._key,
            type=self._type,
            label=self._label,
            required=self._required,
            default=self._default,
            placeholder=self._placeholder,
            help=self._help,
            options=self._options,
            max_length=self._max_length,
            validation=self._validation
        )
    
    @classmethod
    def text_input(cls, key: str = "text_input") -> Self:
        """Create a text input builder."""
        return cls().with_key(key).with_type("text").with_label(f"{key.title()} Input")
    
    @classmethod
    def choice_input(cls, key: str = "choice_input", options: Optional[List[Dict[str, str]]] = None) -> Self:
        """Create a choice input builder."""
        default_options = options or [
            {"label": "Option 1", "value": "opt1"},
            {"label": "Option 2", "value": "opt2"}
        ]
        return (cls()
                .with_key(key)
                .with_type("choice")
                .with_label(f"{key.title()} Input")
                .with_options(default_options))
    
    @classmethod
    def required_text(cls, key: str = "required_input") -> Self:
        """Create a required text input builder."""
        return cls().text_input(key).required()


class PipelineStepTemplateBuilder:
    """Builder for PipelineStepTemplate test data."""
    
    def __init__(self) -> None:
        self._id = StepId("default_step")
        self._name = "Default Step"
        self._description = "A default test step"
        self._type = "llm_generate"
        self._prompt_template = PromptTemplate("Generate content based on {{input}}")
        self._selection_prompt = ""
        self._model_preference = ModelPreference.default()
        self._validation = {}
        self._ui = {}
        self._depends_on = []
        self._parallel = False
        self._retry_config = {}
    
    def with_id(self, step_id: str | StepId) -> Self:
        """Set the step ID."""
        if isinstance(step_id, str):
            step_id = StepId(step_id)
        self._id = step_id
        return self
    
    def with_name(self, name: str) -> Self:
        """Set the step name."""
        self._name = name
        return self
    
    def with_description(self, description: str) -> Self:
        """Set the step description."""
        self._description = description
        return self
    
    def with_type(self, step_type: str) -> Self:
        """Set the step type."""
        self._type = step_type
        return self
    
    def with_prompt_template(self, template: str | PromptTemplate) -> Self:
        """Set the prompt template."""
        if isinstance(template, str):
            template = PromptTemplate(template)
        self._prompt_template = template
        return self
    
    def with_selection_prompt(self, prompt: str) -> Self:
        """Set the selection prompt."""
        self._selection_prompt = prompt
        return self
    
    def with_model_preference(self, preference: ModelPreference) -> Self:
        """Set the model preference."""
        self._model_preference = preference
        return self
    
    def with_dependencies(self, deps: List[str | StepId]) -> Self:
        """Set step dependencies."""
        dependencies = []
        for dep in deps:
            if isinstance(dep, str):
                dep = StepId(dep)
            dependencies.append(dep)
        self._depends_on = dependencies
        return self
    
    def parallel(self) -> Self:
        """Mark the step as parallel-capable."""
        self._parallel = True
        return self
    
    def sequential(self) -> Self:
        """Mark the step as sequential-only."""
        self._parallel = False
        return self
    
    def with_retry_config(self, config: Dict[str, Any]) -> Self:
        """Set retry configuration."""
        self._retry_config = config
        return self
    
    def build(self) -> PipelineStepTemplate:
        """Build the PipelineStepTemplate."""
        return PipelineStepTemplate(
            id=self._id,
            name=self._name,
            description=self._description,
            type=self._type,
            prompt_template=self._prompt_template,
            selection_prompt=self._selection_prompt,
            model_preference=self._model_preference,
            validation=self._validation,
            ui=self._ui,
            depends_on=self._depends_on,
            parallel=self._parallel,
            retry_config=self._retry_config
        )
    
    @classmethod
    def llm_step(cls, step_id: str = "llm_step") -> Self:
        """Create an LLM generation step builder."""
        return (cls()
                .with_id(step_id)
                .with_name(f"{step_id.title()} Step")
                .with_type("llm_generate"))
    
    @classmethod
    def user_input_step(cls, step_id: str = "user_input") -> Self:
        """Create a user input step builder."""
        return (cls()
                .with_id(step_id)
                .with_name(f"{step_id.title()} Step")
                .with_type("user_input"))
    
    @classmethod
    def dependent_step(cls, step_id: str = "dependent_step", dependencies: List[str] = None) -> Self:
        """Create a step with dependencies."""
        deps = dependencies or ["previous_step"]
        return (cls()
                .with_id(step_id)
                .with_name(f"{step_id.title()} Step")
                .with_dependencies(deps))


class PipelineTemplateBuilder:
    """Builder for PipelineTemplate test data."""
    
    def __init__(self) -> None:
        self._id = PipelineId.from_name("default_pipeline")
        self._name = "Default Pipeline"
        self._description = "A default test pipeline"
        self._version = "1.0.0"
        self._metadata = {}
        self._defaults = {}
        self._inputs = {}
        self._steps = {}
        self._tags = []
        self._author = None
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
    
    def with_id(self, pipeline_id: str | PipelineId) -> Self:
        """Set the pipeline ID."""
        if isinstance(pipeline_id, str):
            pipeline_id = PipelineId.from_name(pipeline_id)
        self._id = pipeline_id
        return self
    
    def with_name(self, name: str) -> Self:
        """Set the pipeline name."""
        self._name = name
        self._id = PipelineId.from_name(name)  # Update ID to match name
        return self
    
    def with_description(self, description: str) -> Self:
        """Set the pipeline description."""
        self._description = description
        return self
    
    def with_version(self, version: str) -> Self:
        """Set the pipeline version."""
        self._version = version
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the pipeline metadata."""
        self._metadata = metadata
        return self
    
    def with_defaults(self, defaults: Dict[str, Any]) -> Self:
        """Set the pipeline defaults."""
        self._defaults = defaults
        return self
    
    def with_inputs(self, inputs: List[PipelineInput]) -> Self:
        """Set the pipeline inputs."""
        self._inputs = {inp.key: inp for inp in inputs}
        return self
    
    def with_steps(self, steps: List[PipelineStepTemplate]) -> Self:
        """Set the pipeline steps."""
        self._steps = {step.id.value: step for step in steps}
        return self
    
    def with_tags(self, tags: List[str]) -> Self:
        """Set the pipeline tags."""
        self._tags = tags
        return self
    
    def with_author(self, author: str) -> Self:
        """Set the pipeline author."""
        self._author = author
        return self
    
    def with_timestamps(self, created_at: datetime, updated_at: datetime) -> Self:
        """Set the pipeline timestamps."""
        self._created_at = created_at
        self._updated_at = updated_at
        return self
    
    def build(self) -> PipelineTemplate:
        """Build the PipelineTemplate."""
        return PipelineTemplate(
            id=self._id,
            name=self._name,
            description=self._description,
            version=self._version,
            metadata=self._metadata,
            defaults=self._defaults,
            inputs=self._inputs,
            steps=self._steps,
            tags=self._tags,
            author=self._author,
            created_at=self._created_at,
            updated_at=self._updated_at
        )
    
    @classmethod
    def simple(cls, name: str = "Simple Pipeline") -> Self:
        """Create a simple pipeline with basic configuration."""
        step = PipelineStepTemplateBuilder.llm_step("generate").build()
        input_def = PipelineInputBuilder.text_input("topic").required().build()
        
        return (cls()
                .with_name(name)
                .with_description("A simple test pipeline")
                .with_inputs([input_def])
                .with_steps([step]))
    
    @classmethod
    def complex_with_dependencies(cls, name: str = "Complex Pipeline") -> Self:
        """Create a complex pipeline with step dependencies."""
        step1 = PipelineStepTemplateBuilder.llm_step("outline").build()
        step2 = (PipelineStepTemplateBuilder
                 .llm_step("content")
                 .with_dependencies(["outline"])
                 .build())
        step3 = (PipelineStepTemplateBuilder
                 .llm_step("review")
                 .with_dependencies(["content"])
                 .build())
        
        topic_input = PipelineInputBuilder.required_text("topic").build()
        style_input = PipelineInputBuilder.choice_input("style").build()
        
        return (cls()
                .with_name(name)
                .with_description("A complex pipeline with dependencies")
                .with_inputs([topic_input, style_input])
                .with_steps([step1, step2, step3])
                .with_tags(["complex", "test"]))
    
    @classmethod
    def with_parallel_steps(cls, name: str = "Parallel Pipeline") -> Self:
        """Create a pipeline with parallel-capable steps."""
        step1 = PipelineStepTemplateBuilder.llm_step("step1").parallel().build()
        step2 = PipelineStepTemplateBuilder.llm_step("step2").parallel().build()
        step3 = (PipelineStepTemplateBuilder
                 .llm_step("merge")
                 .with_dependencies(["step1", "step2"])
                 .build())
        
        input_def = PipelineInputBuilder.text_input("input").required().build()
        
        return (cls()
                .with_name(name)
                .with_description("A pipeline with parallel steps")
                .with_inputs([input_def])
                .with_steps([step1, step2, step3]))


class PipelineRunBuilder:
    """Builder for PipelineRun test data."""
    
    def __init__(self) -> None:
        self._id = "test_run_id"
        self._pipeline_id = PipelineId.from_name("test_pipeline")
        self._workspace_name = "test_workspace"
        self._inputs = {}
        self._status = ExecutionStatus.created()
        self._current_step = None
        self._step_executions = {}
        self._execution_plan = []
        self._results = {}
        self._error = None
        self._metadata = {}
        self._created_at = datetime.now()
        self._updated_at = datetime.now()
        self._started_at = None
        self._completed_at = None
    
    def with_id(self, run_id: str) -> Self:
        """Set the run ID."""
        self._id = run_id
        return self
    
    def with_pipeline_id(self, pipeline_id: str | PipelineId) -> Self:
        """Set the pipeline ID."""
        if isinstance(pipeline_id, str):
            pipeline_id = PipelineId.from_name(pipeline_id)
        self._pipeline_id = pipeline_id
        return self
    
    def with_workspace(self, workspace_name: str) -> Self:
        """Set the workspace name."""
        self._workspace_name = workspace_name
        return self
    
    def with_inputs(self, inputs: Dict[str, Any]) -> Self:
        """Set the run inputs."""
        self._inputs = inputs
        return self
    
    def with_status(self, status: ExecutionStatus) -> Self:
        """Set the execution status."""
        self._status = status
        return self
    
    def with_current_step(self, step_id: str) -> Self:
        """Set the current step."""
        self._current_step = step_id
        return self
    
    def with_execution_plan(self, plan: List[str]) -> Self:
        """Set the execution plan."""
        self._execution_plan = plan
        return self
    
    def with_results(self, results: Dict[str, Any]) -> Self:
        """Set the results."""
        self._results = results
        return self
    
    def with_error(self, error: str) -> Self:
        """Set the error message."""
        self._error = error
        return self
    
    def with_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Set the metadata."""
        self._metadata = metadata
        return self
    
    def running(self) -> Self:
        """Set the run as running."""
        self._status = ExecutionStatus.running()
        self._started_at = datetime.now()
        return self
    
    def completed(self) -> Self:
        """Set the run as completed."""
        self._status = ExecutionStatus.completed()
        self._completed_at = datetime.now()
        return self
    
    def failed(self, error: str = "Test error") -> Self:
        """Set the run as failed."""
        self._status = ExecutionStatus.failed(error)
        self._error = error
        return self
    
    def build(self) -> PipelineRun:
        """Build the PipelineRun."""
        return PipelineRun(
            id=self._id,
            pipeline_id=self._pipeline_id,
            workspace_name=self._workspace_name,
            status=self._status,
            inputs=self._inputs,
            outputs=self._results,
            created_at=self._created_at,
            started_at=self._started_at,
            completed_at=self._completed_at,
            error=self._error,
            metadata=self._metadata
        )
    
    @classmethod
    def pending(cls, run_id: str = "pending_run") -> Self:
        """Create a pending run builder."""
        return cls().with_id(run_id).with_status(ExecutionStatus.created())
    
    @classmethod
    def running(cls, run_id: str = "running_run") -> Self:
        """Create a running run builder."""
        builder = cls().with_id(run_id)
        builder._status = ExecutionStatus.running()
        builder._started_at = datetime.now()
        return builder
    
    @classmethod
    def completed(cls, run_id: str = "completed_run") -> Self:
        """Create a completed run builder."""
        now = datetime.now()
        builder = cls().with_id(run_id)
        builder._status = ExecutionStatus.completed()
        builder._completed_at = now
        return builder
    
    @classmethod
    def failed(cls, run_id: str = "failed_run", error: str = "Test error") -> Self:
        """Create a failed run builder."""
        now = datetime.now()
        builder = cls().with_id(run_id)
        builder._status = ExecutionStatus.failed(error)
        builder._error = error
        builder._completed_at = now  # Failed is also terminal state
        return builder


class StepExecutionBuilder:
    """Builder for StepExecution test data."""
    
    def __init__(self) -> None:
        self._step_id = StepId("test_step")
        self._step_name = StepName("Test Step")
        self._status = ExecutionStatus.step_pending()
        self._inputs = {}
        self._outputs = {}
        self._error_message = None
        self._started_at = None
        self._completed_at = None
        self._execution_time = 0.0
        self._tokens_used = {}
        self._metadata = {}
        self._retry_count = 0
        self._max_retries = 3
    
    def with_step_id(self, step_id: str | StepId) -> Self:
        """Set the step ID."""
        if isinstance(step_id, str):
            step_id = StepId(step_id)
        self._step_id = step_id
        return self
    
    def with_step_name(self, name: str | StepName) -> Self:
        """Set the step name."""
        if isinstance(name, str):
            name = StepName(name)
        self._step_name = name
        return self
    
    def with_status(self, status: ExecutionStatus) -> Self:
        """Set the execution status."""
        self._status = status
        return self
    
    def with_inputs(self, inputs: Dict[str, Any]) -> Self:
        """Set the inputs."""
        self._inputs = inputs
        return self
    
    def with_outputs(self, outputs: Dict[str, Any]) -> Self:
        """Set the outputs."""
        self._outputs = outputs
        return self
    
    def with_error_message(self, error_message: str) -> Self:
        """Set the error message."""
        self._error_message = error_message
        return self
    
    def with_execution_time(self, execution_time: float) -> Self:
        """Set the execution time."""
        self._execution_time = execution_time
        return self
    
    def with_tokens_used(self, tokens_used: Dict[str, int]) -> Self:
        """Set the tokens used."""
        self._tokens_used = tokens_used
        return self
    
    def with_retry_count(self, count: int) -> Self:
        """Set the retry count."""
        self._retry_count = count
        return self
    
    def with_max_retries(self, max_retries: int) -> Self:
        """Set the max retries."""
        self._max_retries = max_retries
        return self
    
    def running(self) -> Self:
        """Set the execution as running."""
        self._status = ExecutionStatus(StepExecutionStatus.RUNNING, datetime.now())
        self._started_at = datetime.now()
        return self
    
    def completed(self, output: str = "Test response") -> Self:
        """Set the execution as completed."""
        self._status = ExecutionStatus(StepExecutionStatus.COMPLETED, datetime.now())
        self._outputs = {"result": output}
        self._completed_at = datetime.now()
        return self
    
    def failed(self, error: str = "Test error") -> Self:
        """Set the execution as failed."""
        self._status = ExecutionStatus(StepExecutionStatus.FAILED, datetime.now(), error_message=error)
        self._error_message = error
        return self
    
    def build(self) -> StepExecution:
        """Build the StepExecution."""
        return StepExecution(
            step_id=self._step_id,
            step_name=self._step_name,
            status=self._status,
            inputs=self._inputs,
            outputs=self._outputs,
            error_message=self._error_message,
            started_at=self._started_at,
            completed_at=self._completed_at,
            execution_time=self._execution_time,
            tokens_used=self._tokens_used,
            metadata=self._metadata,
            retry_count=self._retry_count,
            max_retries=self._max_retries
        )
    
    @classmethod
    def pending(cls, step_id: str = "pending_step") -> Self:
        """Create a pending execution builder."""
        return cls().with_step_id(step_id).with_step_name(f"{step_id.title()} Step")
    
    @classmethod
    def completed(cls, step_id: str = "completed_step", output: str = "Test response") -> Self:
        """Create a completed execution builder."""
        now = datetime.now()
        builder = cls().with_step_id(step_id).with_step_name(f"{step_id.title()} Step")
        builder._status = ExecutionStatus(StepExecutionStatus.COMPLETED, now)
        builder._outputs = {"result": output}
        builder._completed_at = now
        return builder
    
    @classmethod
    def failed(cls, step_id: str = "failed_step", error: str = "Test error") -> Self:
        """Create a failed execution builder."""
        now = datetime.now()
        builder = cls().with_step_id(step_id).with_step_name(f"{step_id.title()} Step")
        builder._status = ExecutionStatus(StepExecutionStatus.FAILED, now, error_message=error)
        builder._error_message = error
        builder._completed_at = now  # Failed is also terminal state
        return builder