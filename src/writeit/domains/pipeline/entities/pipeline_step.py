"""Pipeline step entity.

Domain entity representing an individual step within a pipeline execution."""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Dict, Any, List, Optional, Self

from ..value_objects.step_id import StepId
from ..value_objects.step_name import StepName
from ..value_objects.execution_status import ExecutionStatus, StepExecutionStatus
from ..value_objects.prompt_template import PromptTemplate
from ..value_objects.model_preference import ModelPreference


@dataclass
class StepExecution:
    """Domain entity representing the execution state of a pipeline step.
    
    Tracks the runtime state, inputs, outputs, and execution metadata
    for a specific step within a pipeline run.
    
    Examples:
        execution = StepExecution.create(
            step_id=StepId("outline"),
            step_name=StepName("Create Outline"),
            status=ExecutionStatus.step_pending()
        )
        
        # Start execution
        execution = execution.start(inputs={"topic": "AI Ethics"})
        
        # Complete execution
        execution = execution.complete(outputs={"outline": "..."})
    """
    
    step_id: StepId
    step_name: StepName
    status: ExecutionStatus
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: float = 0.0
    tokens_used: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self) -> None:
        """Validate step execution."""
        if not isinstance(self.step_id, StepId):
            raise TypeError("Step id must be a StepId")
            
        if not isinstance(self.step_name, StepName):
            raise TypeError("Step name must be a StepName")
            
        if not isinstance(self.status, ExecutionStatus):
            raise TypeError("Status must be an ExecutionStatus")
            
        if not isinstance(self.inputs, dict):
            raise TypeError("Inputs must be a dictionary")
            
        if not isinstance(self.outputs, dict):
            raise TypeError("Outputs must be a dictionary")
            
        if self.started_at is not None and not isinstance(self.started_at, datetime):
            raise TypeError("Started_at must be a datetime or None")
            
        if self.completed_at is not None and not isinstance(self.completed_at, datetime):
            raise TypeError("Completed_at must be a datetime or None")
            
        if self.execution_time < 0:
            raise ValueError("Execution time cannot be negative")
            
        if self.retry_count < 0:
            raise ValueError("Retry count cannot be negative")
            
        if self.max_retries < 0:
            raise ValueError("Max retries cannot be negative")
            
        # Validate state consistency
        if self.status.is_active and self.started_at is None:
            raise ValueError("Active step execution must have started_at set")
            
        if self.status.is_terminal and self.completed_at is None:
            raise ValueError("Completed step execution must have completed_at set")
            
        if self.status.is_failed and not self.error_message:
            raise ValueError("Failed step execution must have error message")
    
    @property
    def is_pending(self) -> bool:
        """Check if step is pending execution."""
        return self.status.status == StepExecutionStatus.PENDING
    
    @property
    def is_running(self) -> bool:
        """Check if step is currently running."""
        return self.status.status == StepExecutionStatus.RUNNING
    
    @property
    def is_waiting_input(self) -> bool:
        """Check if step is waiting for user input."""
        return self.status.status == StepExecutionStatus.WAITING_INPUT
    
    @property
    def is_completed(self) -> bool:
        """Check if step completed successfully."""
        return self.status.is_successful
    
    @property
    def is_failed(self) -> bool:
        """Check if step failed."""
        return self.status.is_failed
    
    @property
    def is_skipped(self) -> bool:
        """Check if step was skipped."""
        return self.status.status == StepExecutionStatus.SKIPPED
    
    @property
    def is_cancelled(self) -> bool:
        """Check if step was cancelled."""
        return self.status.is_cancelled
    
    @property
    def can_retry(self) -> bool:
        """Check if step can be retried."""
        return self.is_failed and self.retry_count < self.max_retries
    
    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    def start(self, inputs: Optional[Dict[str, Any]] = None) -> Self:
        """Start step execution.
        
        Args:
            inputs: Step input values
            
        Returns:
            New step execution with running status
            
        Raises:
            ValueError: If step is not in pending state
        """
        if not self.is_pending:
            raise ValueError("Can only start pending step execution")
            
        new_status = self.status.transition_to(StepExecutionStatus.RUNNING)
        
        return replace(
            self,
            status=new_status,
            inputs=inputs or self.inputs,
            started_at=datetime.now()
        )
    
    def wait_for_input(self) -> Self:
        """Mark step as waiting for user input.
        
        Returns:
            New step execution with waiting_input status
            
        Raises:
            ValueError: If step is not running
        """
        if not self.is_running:
            raise ValueError("Can only wait for input during running step")
            
        new_status = self.status.transition_to(StepExecutionStatus.WAITING_INPUT)
        
        return replace(self, status=new_status)
    
    def resume_from_input(self) -> Self:
        """Resume step from waiting for input.
        
        Returns:
            New step execution with running status
            
        Raises:
            ValueError: If step is not waiting for input
        """
        if not self.is_waiting_input:
            raise ValueError("Can only resume from waiting_input state")
            
        new_status = self.status.transition_to(StepExecutionStatus.RUNNING)
        
        return replace(self, status=new_status)
    
    def complete(self, outputs: Optional[Dict[str, Any]] = None) -> Self:
        """Complete step execution successfully.
        
        Args:
            outputs: Step output values
            
        Returns:
            New step execution with completed status
            
        Raises:
            ValueError: If step is not in active state
        """
        if not (self.is_running or self.is_waiting_input):
            raise ValueError("Can only complete active step execution")
            
        new_status = self.status.transition_to(StepExecutionStatus.COMPLETED)
        
        execution_time = self.duration or 0.0
        
        return replace(
            self,
            status=new_status,
            outputs=outputs or self.outputs,
            completed_at=datetime.now(),
            execution_time=execution_time
        )
    
    def fail(self, error_message: str) -> Self:
        """Fail step execution.
        
        Args:
            error_message: Error description
            
        Returns:
            New step execution with failed status
        """
        new_status = self.status.transition_to(
            StepExecutionStatus.FAILED,
            error_message=error_message
        )
        
        execution_time = self.duration or 0.0
        
        return replace(
            self,
            status=new_status,
            error_message=error_message,
            completed_at=datetime.now(),
            execution_time=execution_time
        )
    
    def skip(self, reason: str = "") -> Self:
        """Skip step execution.
        
        Args:
            reason: Optional reason for skipping
            
        Returns:
            New step execution with skipped status
        """
        new_status = self.status.transition_to(StepExecutionStatus.SKIPPED)
        
        metadata = self.metadata.copy()
        if reason:
            metadata["skip_reason"] = reason
        
        return replace(
            self,
            status=new_status,
            completed_at=datetime.now(),
            metadata=metadata
        )
    
    def cancel(self) -> Self:
        """Cancel step execution.
        
        Returns:
            New step execution with cancelled status
        """
        new_status = self.status.transition_to(StepExecutionStatus.CANCELLED)
        
        execution_time = self.duration or 0.0
        
        return replace(
            self,
            status=new_status,
            completed_at=datetime.now(),
            execution_time=execution_time
        )
    
    def retry(self) -> Self:
        """Retry failed step execution.
        
        Returns:
            New step execution ready for retry
            
        Raises:
            ValueError: If step cannot be retried
        """
        if not self.can_retry:
            raise ValueError(
                f"Cannot retry step: retry_count={self.retry_count}, "
                f"max_retries={self.max_retries}, status={self.status.status}"
            )
            
        new_status = ExecutionStatus.step_pending()
        
        return replace(
            self,
            status=new_status,
            error_message=None,
            started_at=None,
            completed_at=None,
            retry_count=self.retry_count + 1
        )
    
    def add_token_usage(self, provider: str, tokens: int) -> Self:
        """Add token usage for a provider.
        
        Args:
            provider: LLM provider name
            tokens: Number of tokens used
            
        Returns:
            New step execution with updated token usage
        """
        new_token_usage = self.tokens_used.copy()
        new_token_usage[provider] = new_token_usage.get(provider, 0) + tokens
        
        return replace(self, tokens_used=new_token_usage)
    
    def update_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Update step metadata.
        
        Args:
            metadata: New metadata (merged with existing)
            
        Returns:
            New step execution with updated metadata
        """
        new_metadata = {**self.metadata, **metadata}
        return replace(self, metadata=new_metadata)
    
    def set_outputs(self, outputs: Dict[str, Any]) -> Self:
        """Set step outputs.
        
        Args:
            outputs: Step output values
            
        Returns:
            New step execution with updated outputs
        """
        return replace(self, outputs=outputs)
    
    def get_input(self, key: str, default: Any = None) -> Any:
        """Get input value by key.
        
        Args:
            key: Input key
            default: Default value if key not found
            
        Returns:
            Input value or default
        """
        return self.inputs.get(key, default)
    
    def get_output(self, key: str, default: Any = None) -> Any:
        """Get output value by key.
        
        Args:
            key: Output key
            default: Default value if key not found
            
        Returns:
            Output value or default
        """
        return self.outputs.get(key, default)
    
    def get_total_tokens(self) -> int:
        """Get total tokens used across all providers."""
        return sum(self.tokens_used.values())
    
    @classmethod
    def create(
        cls,
        step_id: StepId,
        step_name: StepName,
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Self:
        """Create a new step execution.
        
        Args:
            step_id: Step identifier
            step_name: Step name
            max_retries: Maximum retry attempts
            metadata: Additional metadata
            
        Returns:
            New step execution
        """
        return cls(
            step_id=step_id,
            step_name=step_name,
            status=ExecutionStatus.step_pending(),
            max_retries=max_retries,
            metadata=metadata or {}
        )
    
    @classmethod
    def from_template(
        cls,
        step_template,  # PipelineStepTemplate
        max_retries: int = 3,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Self:
        """Create step execution from template.
        
        Args:
            step_template: Pipeline step template
            max_retries: Maximum retry attempts
            metadata: Additional metadata
            
        Returns:
            New step execution
        """
        step_name = StepName.from_string(step_template.name)
        
        template_metadata = {
            "step_type": step_template.type,
            "description": step_template.description,
            "parallel": step_template.parallel,
            "depends_on": [str(dep) for dep in step_template.depends_on]
        }
        
        if metadata:
            template_metadata.update(metadata)
        
        return cls.create(
            step_id=step_template.id,
            step_name=step_name,
            max_retries=max_retries,
            metadata=template_metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'step_id': str(self.step_id),
            'step_name': str(self.step_name),
            'status': str(self.status.status),
            'inputs': self.inputs,
            'outputs': self.outputs,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'execution_time': self.execution_time,
            'tokens_used': self.tokens_used,
            'metadata': self.metadata,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"StepExecution({self.step_id} - {self.status.status})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"StepExecution(step_id={self.step_id}, "
                f"name='{self.step_name}', status={self.status.status})")


@dataclass
class PipelineStep:
    """Domain entity representing a pipeline step configuration.
    
    Combines the template definition with runtime configuration
    for a specific step within a pipeline.
    
    Examples:
        step = PipelineStep.create(
            step_id=StepId("outline"),
            name=StepName("Create Outline"),
            step_type="llm_generate",
            prompt_template=PromptTemplate("Create outline for {{ topic }}"),
            model_preference=ModelPreference.default()
        )
        
        # Check dependencies
        has_deps = step.has_dependencies()
        
        # Validate configuration
        errors = step.validate()
    """
    
    step_id: StepId
    name: StepName
    description: str
    step_type: str  # 'llm_generate', 'user_input', 'transform', 'validate'
    prompt_template: PromptTemplate
    model_preference: ModelPreference
    selection_prompt: str = ""
    depends_on: List[StepId] = field(default_factory=list)
    parallel: bool = False
    timeout_seconds: Optional[int] = None
    retry_config: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)
    ui_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate step configuration."""
        if not isinstance(self.step_id, StepId):
            raise TypeError("Step id must be a StepId")
            
        if not isinstance(self.name, StepName):
            raise TypeError("Step name must be a StepName")
            
        if not self.description or not isinstance(self.description, str):
            raise ValueError("Step description must be a non-empty string")
            
        valid_types = {'llm_generate', 'user_input', 'transform', 'validate', 'conditional'}
        if self.step_type not in valid_types:
            raise ValueError(f"Step type must be one of {valid_types}")
            
        if not isinstance(self.prompt_template, PromptTemplate):
            raise TypeError("Prompt template must be a PromptTemplate")
            
        if not isinstance(self.model_preference, ModelPreference):
            raise TypeError("Model preference must be a ModelPreference")
            
        # Validate dependencies
        for dep in self.depends_on:
            if not isinstance(dep, StepId):
                raise TypeError("Dependencies must be StepId instances")
                
        # Validate timeout
        if self.timeout_seconds is not None:
            if self.timeout_seconds <= 0:
                raise ValueError("Timeout must be positive")
                
        # Validate dictionaries
        for field_name, field_value in [
            ("retry_config", self.retry_config),
            ("validation", self.validation),
            ("ui_config", self.ui_config),
            ("metadata", self.metadata)
        ]:
            if not isinstance(field_value, dict):
                raise TypeError(f"{field_name} must be a dictionary")
    
    @property
    def is_llm_step(self) -> bool:
        """Check if this is an LLM generation step."""
        return self.step_type == "llm_generate"
    
    @property
    def is_user_input_step(self) -> bool:
        """Check if this is a user input step."""
        return self.step_type == "user_input"
    
    @property
    def is_transform_step(self) -> bool:
        """Check if this is a data transformation step."""
        return self.step_type == "transform"
    
    @property
    def is_validation_step(self) -> bool:
        """Check if this is a validation step."""
        return self.step_type == "validate"
    
    @property
    def is_conditional_step(self) -> bool:
        """Check if this is a conditional step."""
        return self.step_type == "conditional"
    
    def has_dependencies(self) -> bool:
        """Check if step has dependencies."""
        return len(self.depends_on) > 0
    
    def can_run_in_parallel(self) -> bool:
        """Check if step can run in parallel."""
        return self.parallel and not self.has_dependencies()
    
    def depends_on_step(self, step_id: StepId) -> bool:
        """Check if step depends on another step."""
        return step_id in self.depends_on
    
    def get_required_variables(self) -> set[str]:
        """Get variables required by this step's prompt template."""
        return self.prompt_template.variables
    
    def get_timeout(self) -> Optional[int]:
        """Get step timeout in seconds."""
        return self.timeout_seconds
    
    def get_max_retries(self) -> int:
        """Get maximum retry attempts."""
        return self.retry_config.get("max_retries", 3)
    
    def get_retry_delay(self) -> float:
        """Get retry delay in seconds."""
        return self.retry_config.get("delay_seconds", 1.0)
    
    def should_retry_on_error(self, error_type: str) -> bool:
        """Check if step should retry on specific error type."""
        retryable_errors = self.retry_config.get("retryable_errors", ["timeout", "rate_limit"])
        return error_type in retryable_errors
    
    def validate(self) -> List[str]:
        """Validate step configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate prompt template variables
        required_vars = self.get_required_variables()
        if not required_vars and self.is_llm_step:
            errors.append("LLM generation step should have template variables")
        
        # Validate model preference for LLM steps
        if self.is_llm_step and not self.model_preference.models:
            errors.append("LLM generation step must have model preference")
        
        # Validate selection prompt
        if self.selection_prompt and not self.is_llm_step:
            errors.append("Selection prompt only valid for LLM generation steps")
        
        # Validate UI config for user input steps
        if self.is_user_input_step and not self.ui_config:
            errors.append("User input step should have UI configuration")
        
        return errors
    
    def create_execution(
        self,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StepExecution:
        """Create step execution from this step configuration.
        
        Args:
            metadata: Additional execution metadata
            
        Returns:
            New step execution
        """
        execution_metadata = {
            "step_type": self.step_type,
            "description": self.description,
            "parallel": self.parallel,
            "depends_on": [str(dep) for dep in self.depends_on],
            "timeout_seconds": self.timeout_seconds
        }
        
        if metadata:
            execution_metadata.update(metadata)
        
        return StepExecution.create(
            step_id=self.step_id,
            step_name=self.name,
            max_retries=self.get_max_retries(),
            metadata=execution_metadata
        )
    
    @classmethod
    def create(
        cls,
        step_id: StepId,
        name: StepName,
        description: str,
        step_type: str,
        prompt_template: PromptTemplate,
        model_preference: Optional[ModelPreference] = None,
        **kwargs
    ) -> Self:
        """Create a new pipeline step.
        
        Args:
            step_id: Step identifier
            name: Step name
            description: Step description
            step_type: Type of step
            prompt_template: Prompt template
            model_preference: Model preference (defaults to default)
            **kwargs: Additional configuration
            
        Returns:
            New pipeline step
        """
        return cls(
            step_id=step_id,
            name=name,
            description=description,
            step_type=step_type,
            prompt_template=prompt_template,
            model_preference=model_preference or ModelPreference.default(),
            **kwargs
        )
    
    @classmethod
    def llm_generate(
        cls,
        step_id: StepId,
        name: StepName,
        description: str,
        prompt_template: PromptTemplate,
        model_preference: Optional[ModelPreference] = None,
        **kwargs
    ) -> Self:
        """Create LLM generation step."""
        return cls.create(
            step_id=step_id,
            name=name,
            description=description,
            step_type="llm_generate",
            prompt_template=prompt_template,
            model_preference=model_preference,
            **kwargs
        )
    
    @classmethod
    def user_input(
        cls,
        step_id: StepId,
        name: StepName,
        description: str,
        ui_config: Dict[str, Any],
        **kwargs
    ) -> Self:
        """Create user input step."""
        return cls.create(
            step_id=step_id,
            name=name,
            description=description,
            step_type="user_input",
            prompt_template=PromptTemplate.simple("User input required"),
            ui_config=ui_config,
            **kwargs
        )
    
    def update(
        self,
        name: Optional[StepName] = None,
        description: Optional[str] = None,
        prompt_template: Optional[PromptTemplate] = None,
        model_preference: Optional[ModelPreference] = None,
        **kwargs
    ) -> Self:
        """Create updated copy of this step.
        
        Returns:
            New pipeline step with updated fields
        """
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if prompt_template is not None:
            updates["prompt_template"] = prompt_template
        if model_preference is not None:
            updates["model_preference"] = model_preference
        
        # Handle other keyword arguments
        for key, value in kwargs.items():
            if hasattr(self, key):
                updates[key] = value
        
        return replace(self, **updates)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'step_id': str(self.step_id),
            'name': str(self.name),
            'description': self.description,
            'step_type': self.step_type,
            'prompt_template': str(self.prompt_template),
            'model_preference': str(self.model_preference),
            'selection_prompt': self.selection_prompt,
            'depends_on': [str(dep) for dep in self.depends_on],
            'parallel': self.parallel,
            'timeout_seconds': self.timeout_seconds,
            'retry_config': self.retry_config,
            'validation': self.validation,
            'ui_config': self.ui_config,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"PipelineStep({self.step_id} - {self.name})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"PipelineStep(id={self.step_id}, name='{self.name}', "
                f"type='{self.step_type}')")
    
    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self.step_id)