"""Pipeline template entity.

Domain entity representing a pipeline template that can be instantiated into pipeline runs.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Dict, Any, List, Optional, Self

from ..value_objects.pipeline_id import PipelineId
from ..value_objects.step_id import StepId
from ..value_objects.prompt_template import PromptTemplate
from ..value_objects.model_preference import ModelPreference


@dataclass
class PipelineInput:
    """Configuration for a pipeline input field.
    
    Defines the structure and validation rules for user inputs
    required to execute a pipeline.
    """
    
    key: str
    type: str  # 'text', 'choice', 'number', 'boolean'
    label: str
    required: bool = False
    default: Any = None
    placeholder: str = ""
    help: str = ""
    options: List[Dict[str, str]] = field(default_factory=list)
    max_length: Optional[int] = None
    validation: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate input configuration."""
        if not self.key or not isinstance(self.key, str):
            raise ValueError("Input key must be a non-empty string")
            
        if not self.label or not isinstance(self.label, str):
            raise ValueError("Input label must be a non-empty string")
            
        valid_types = {'text', 'choice', 'number', 'boolean'}
        if self.type not in valid_types:
            raise ValueError(f"Input type must be one of {valid_types}")
            
        if self.type == 'choice' and not self.options:
            raise ValueError("Choice input must have options")
            
        if self.max_length is not None and self.max_length <= 0:
            raise ValueError("Max length must be positive")
    
    def validate_value(self, value: Any) -> bool:
        """Validate a value against this input definition."""
        if self.required and (value is None or value == ""):
            return False
            
        if value is None:
            return not self.required
            
        if self.type == 'text':
            if not isinstance(value, str):
                return False
            if self.max_length and len(value) > self.max_length:
                return False
                
        elif self.type == 'choice':
            valid_values = {opt['value'] for opt in self.options}
            return value in valid_values
            
        elif self.type == 'number':
            try:
                float(value)
            except (ValueError, TypeError):
                return False
                
        elif self.type == 'boolean':
            return isinstance(value, bool)
            
        return True


@dataclass
class PipelineStepTemplate:
    """Template for a pipeline step.
    
    Defines the configuration and behavior of a single step
    within a pipeline template.
    """
    
    id: StepId
    name: str
    description: str
    type: str  # 'llm_generate', 'user_input', 'transform', 'validate'
    prompt_template: PromptTemplate
    selection_prompt: str = ""
    model_preference: ModelPreference = field(default_factory=ModelPreference.default)
    validation: Dict[str, Any] = field(default_factory=dict)
    ui: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[StepId] = field(default_factory=list)
    parallel: bool = False
    retry_config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate step configuration."""
        if not isinstance(self.id, StepId):
            raise TypeError("Step id must be a StepId")
            
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Step name must be a non-empty string")
            
        if not self.description or not isinstance(self.description, str):
            raise ValueError("Step description must be a non-empty string")
            
        valid_types = {'llm_generate', 'user_input', 'transform', 'validate'}
        if self.type not in valid_types:
            raise ValueError(f"Step type must be one of {valid_types}")
            
        if not isinstance(self.prompt_template, PromptTemplate):
            raise TypeError("Prompt template must be a PromptTemplate")
            
        if not isinstance(self.model_preference, ModelPreference):
            raise TypeError("Model preference must be a ModelPreference")
            
        # Validate dependencies
        for dep in self.depends_on:
            if not isinstance(dep, StepId):
                raise TypeError("Dependencies must be StepId instances")
    
    def has_dependency(self, step_id: StepId) -> bool:
        """Check if this step depends on another step."""
        return step_id in self.depends_on
    
    def can_run_in_parallel(self) -> bool:
        """Check if this step can run in parallel with others."""
        return self.parallel and not self.depends_on
    
    def get_required_variables(self) -> set[str]:
        """Get all variables required by this step's prompt template."""
        return self.prompt_template.variables


@dataclass
class PipelineTemplate:
    """Domain entity representing a pipeline template.
    
    A pipeline template defines the structure, inputs, and steps
    that can be executed to create a pipeline run.
    
    Examples:
        template = PipelineTemplate.create(
            name="Article Generator",
            description="Generate structured articles",
            inputs=[...],
            steps=[...]
        )
        
        # Validate inputs before execution
        template.validate_inputs(user_inputs)
        
        # Get execution order
        execution_order = template.get_execution_order()
    """
    
    id: PipelineId
    name: str
    description: str
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)
    defaults: Dict[str, Any] = field(default_factory=dict)
    inputs: Dict[str, PipelineInput] = field(default_factory=dict)
    steps: Dict[str, PipelineStepTemplate] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self) -> None:
        """Validate pipeline template."""
        if not isinstance(self.id, PipelineId):
            raise TypeError("Pipeline id must be a PipelineId")
            
        if not self.name or not isinstance(self.name, str):
            raise ValueError("Pipeline name must be a non-empty string")
            
        if not self.description or not isinstance(self.description, str):
            raise ValueError("Pipeline description must be a non-empty string")
            
        if not self.version or not isinstance(self.version, str):
            raise ValueError("Pipeline version must be a non-empty string")
            
        # Validate inputs
        for key, input_def in self.inputs.items():
            if not isinstance(input_def, PipelineInput):
                raise TypeError(f"Input {key} must be a PipelineInput")
            if input_def.key != key:
                raise ValueError(f"Input key mismatch: {key} != {input_def.key}")
        
        # Validate steps
        for key, step in self.steps.items():
            if not isinstance(step, PipelineStepTemplate):
                raise TypeError(f"Step {key} must be a PipelineStepTemplate")
            if step.id.value != key:
                raise ValueError(f"Step key mismatch: {key} != {step.id.value}")
        
        # Validate step dependencies
        self._validate_dependencies()
    
    def _validate_dependencies(self) -> None:
        """Validate that all step dependencies exist and don't create cycles."""
        step_keys = set(self.steps.keys())
        
        # Check that all dependencies exist
        for step_key, step in self.steps.items():
            for dep in step.depends_on:
                if dep.value not in step_keys:
                    raise ValueError(f"Step {step_key} depends on non-existent step {dep.value}")
        
        # Check for circular dependencies
        def has_cycle(step_key: str, visited: set, path: set) -> bool:
            if step_key in path:
                return True
            if step_key in visited:
                return False
                
            visited.add(step_key)
            path.add(step_key)
            
            step = self.steps[step_key]
            for dep in step.depends_on:
                if has_cycle(dep.value, visited, path):
                    return True
                    
            path.remove(step_key)
            return False
        
        visited: set[str] = set()
        for step_key in self.steps:
            if step_key not in visited:
                if has_cycle(step_key, visited, set()):
                    raise ValueError(f"Circular dependency detected involving step {step_key}")
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """Validate user inputs against template requirements.
        
        Args:
            inputs: User-provided input values
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required inputs
        for key, input_def in self.inputs.items():
            if input_def.required and key not in inputs:
                errors.append(f"Required input '{key}' is missing")
                continue
                
            if key in inputs and not input_def.validate_value(inputs[key]):
                errors.append(f"Invalid value for input '{key}'")
        
        # Check for unexpected inputs
        for key in inputs:
            if key not in self.inputs:
                errors.append(f"Unexpected input '{key}'")
        
        return errors
    
    def get_execution_order(self) -> List[str]:
        """Get the execution order of steps based on dependencies.
        
        Returns:
            List of step keys in execution order
            
        Raises:
            ValueError: If circular dependencies exist
        """
        # Topological sort
        visited = set()
        temp_visited = set()
        result = []
        
        def visit(step_key: str):
            if step_key in temp_visited:
                raise ValueError(f"Circular dependency detected at step {step_key}")
            if step_key in visited:
                return
                
            temp_visited.add(step_key)
            
            step = self.steps[step_key]
            for dep in step.depends_on:
                visit(dep.value)
                
            temp_visited.remove(step_key)
            visited.add(step_key)
            result.append(step_key)
        
        for step_key in self.steps:
            if step_key not in visited:
                visit(step_key)
        
        return result
    
    def get_parallel_groups(self) -> List[List[str]]:
        """Get groups of steps that can run in parallel.
        
        Returns:
            List of groups, where each group contains step keys
            that can run in parallel
        """
        execution_order = self.get_execution_order()
        groups = []
        current_group: list[str] = []
        
        for step_key in execution_order:
            step = self.steps[step_key]
            
            # Check if step can run in parallel and has no unmet dependencies
            can_parallel = step.can_run_in_parallel()
            if not can_parallel or step.depends_on:
                # Start new group if current group has items
                if current_group:
                    groups.append(current_group)
                    current_group = []
                groups.append([step_key])
            else:
                current_group.append(step_key)
        
        # Add final group if it has items
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def get_step(self, step_key: str) -> PipelineStepTemplate:
        """Get a step by key.
        
        Args:
            step_key: Step identifier
            
        Returns:
            Pipeline step template
            
        Raises:
            KeyError: If step doesn't exist
        """
        if step_key not in self.steps:
            raise KeyError(f"Step '{step_key}' not found in pipeline")
        return self.steps[step_key]
    
    def has_step(self, step_key: str) -> bool:
        """Check if pipeline has a step with the given key."""
        return step_key in self.steps
    
    def get_required_variables(self) -> set[str]:
        """Get all variables required by this pipeline's steps."""
        variables = set()
        for step in self.steps.values():
            variables.update(step.get_required_variables())
        return variables
    
    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        inputs: List[PipelineInput],
        steps: List[PipelineStepTemplate],
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None
    ) -> Self:
        """Create a new pipeline template.
        
        Args:
            name: Pipeline name
            description: Pipeline description
            inputs: Input definitions
            steps: Step templates
            version: Pipeline version
            metadata: Additional metadata
            defaults: Default values
            tags: Tags for categorization
            author: Author name
            
        Returns:
            New pipeline template
        """
        pipeline_id = PipelineId.from_name(name)
        
        # Convert lists to dictionaries
        inputs_dict = {inp.key: inp for inp in inputs}
        steps_dict = {step.id.value: step for step in steps}
        
        return cls(
            id=pipeline_id,
            name=name,
            description=description,
            version=version,
            metadata=metadata or {},
            defaults=defaults or {},
            inputs=inputs_dict,
            steps=steps_dict,
            tags=tags or [],
            author=author,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def update(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        defaults: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        author: Optional[str] = None
    ) -> Self:
        """Create an updated copy of this pipeline template.
        
        Returns:
            New pipeline template with updated fields
        """
        return replace(
            self,
            name=name if name is not None else self.name,
            description=description if description is not None else self.description,
            version=version if version is not None else self.version,
            metadata=metadata if metadata is not None else self.metadata,
            defaults=defaults if defaults is not None else self.defaults,
            tags=tags if tags is not None else self.tags,
            author=author if author is not None else self.author,
            updated_at=datetime.now()
        )
    
    def __str__(self) -> str:
        """String representation."""
        return f"PipelineTemplate({self.name} v{self.version})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"PipelineTemplate(id={self.id}, name='{self.name}', "
                f"version='{self.version}', steps={len(self.steps)})")