# ABOUTME: Pipeline template validator for WriteIt YAML pipeline files
# ABOUTME: Validates pipeline structure, steps, prompts, and variable references
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from .validation_result import ValidationResult, IssueType


class PipelineValidator:
    """Validates WriteIt pipeline template files."""
    
    # Required top-level keys for pipeline templates
    REQUIRED_KEYS = {'metadata', 'inputs', 'steps'}
    
    # Required metadata fields
    REQUIRED_METADATA = {'name', 'description', 'version', 'author'}
    
    # Valid step types
    VALID_STEP_TYPES = {'llm_generation', 'user_selection', 'user_input'}
    
    # Valid LLM providers
    VALID_LLM_PROVIDERS = {'openai', 'anthropic', 'google', 'ollama'}
    
    def __init__(self):
        """Initialize the pipeline validator."""
        self.variable_pattern = re.compile(r'\{\{\s*([^}]+)\s*\}\}')
    
    def validate_file(self, file_path: Path) -> ValidationResult:
        """Validate a pipeline template file."""
        result = ValidationResult(
            file_path=file_path,
            is_valid=True,
            issues=[],
            metadata={}
        )
        
        try:
            # Check file exists and is readable
            if not file_path.exists():
                result.add_error(f"Pipeline file not found: {file_path}")
                return result
            
            if not file_path.is_file():
                result.add_error(f"Path is not a file: {file_path}")
                return result
            
            # Load and parse YAML
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    pipeline = yaml.safe_load(content)
            except yaml.YAMLError as e:
                result.add_error(f"Invalid YAML syntax: {str(e)}")
                return result
            except Exception as e:
                result.add_error(f"Failed to read file: {str(e)}")
                return result
            
            if not isinstance(pipeline, dict):
                result.add_error("Pipeline must be a YAML object/dictionary")
                return result
            
            # Store parsed pipeline for metadata
            result.metadata['parsed_pipeline'] = pipeline
            
            # Validate structure
            self._validate_top_level_structure(pipeline, result)
            self._validate_metadata(pipeline.get('metadata', {}), result)
            self._validate_inputs(pipeline.get('inputs', {}), result)
            self._validate_steps(pipeline.get('steps', {}), result)
            
            # Cross-validation
            self._validate_variable_references(pipeline, result)
            self._validate_step_dependencies(pipeline.get('steps', {}), result)
            
            # Add statistics to metadata
            steps = pipeline.get('steps', {})
            result.metadata.update({
                'step_count': len(steps),
                'llm_step_count': len([s for s in steps.values() if s.get('type') == 'llm_generation']),
                'input_count': len(pipeline.get('inputs', {})),
                'has_style_primer': 'style_primer' in pipeline.get('global', {})
            })
            
        except Exception as e:
            result.add_error(f"Unexpected validation error: {str(e)}")
        
        return result
    
    def _validate_top_level_structure(self, pipeline: Dict[str, Any], result: ValidationResult) -> None:
        """Validate top-level pipeline structure."""
        # Check required keys
        missing_keys = self.REQUIRED_KEYS - set(pipeline.keys())
        if missing_keys:
            for key in sorted(missing_keys):
                result.add_error(
                    f"Missing required top-level key: '{key}'",
                    suggestion=f"Add '{key}:' section to pipeline"
                )
        
        # Check for unknown top-level keys
        known_keys = {'metadata', 'inputs', 'steps', 'global', 'defaults'}
        unknown_keys = set(pipeline.keys()) - known_keys
        if unknown_keys:
            for key in sorted(unknown_keys):
                result.add_warning(
                    f"Unknown top-level key: '{key}'",
                    suggestion="Check for typos or refer to pipeline documentation"
                )
    
    def _validate_metadata(self, metadata: Dict[str, Any], result: ValidationResult) -> None:
        """Validate metadata section."""
        if not metadata:
            result.add_error("Empty metadata section", suggestion="Add pipeline name, description, version, and author")
            return
        
        # Check required metadata fields
        missing_fields = self.REQUIRED_METADATA - set(metadata.keys())
        if missing_fields:
            for field in sorted(missing_fields):
                result.add_error(
                    f"Missing required metadata field: '{field}'",
                    location="metadata"
                )
        
        # Validate specific fields
        if 'version' in metadata:
            version = metadata['version']
            if not isinstance(version, str) or not re.match(r'^\d+\.\d+\.\d+', str(version)):
                result.add_warning(
                    "Version should follow semantic versioning (e.g., '1.0.0')",
                    location="metadata.version"
                )
        
        # Check for common typos
        common_typos = {
            'decription': 'description',
            'auther': 'author',
            'versoin': 'version'
        }
        
        for typo, correct in common_typos.items():
            if typo in metadata:
                result.add_error(
                    f"Possible typo in metadata: '{typo}' should be '{correct}'",
                    location=f"metadata.{typo}"
                )
    
    def _validate_inputs(self, inputs: Dict[str, Any], result: ValidationResult) -> None:
        """Validate inputs section."""
        if not inputs:
            result.add_warning("No inputs defined", suggestion="Consider adding input parameters for flexibility")
            return
        
        for input_name, input_config in inputs.items():
            if not isinstance(input_config, dict):
                result.add_error(
                    f"Input '{input_name}' must be an object",
                    location=f"inputs.{input_name}"
                )
                continue
            
            # Check required fields
            if 'type' not in input_config:
                result.add_error(
                    f"Input '{input_name}' missing required 'type' field",
                    location=f"inputs.{input_name}"
                )
            
            # Validate type
            valid_types = {'string', 'text', 'number', 'boolean', 'choice'}
            input_type = input_config.get('type')
            if input_type and input_type not in valid_types:
                result.add_warning(
                    f"Input '{input_name}' has unknown type '{input_type}'",
                    location=f"inputs.{input_name}.type",
                    suggestion=f"Valid types: {', '.join(sorted(valid_types))}"
                )
            
            # Validate choice inputs
            if input_type == 'choice' and 'options' not in input_config:
                result.add_error(
                    f"Choice input '{input_name}' missing 'options' field",
                    location=f"inputs.{input_name}"
                )
    
    def _validate_steps(self, steps: Dict[str, Any], result: ValidationResult) -> None:
        """Validate steps section."""
        if not steps:
            result.add_error("No steps defined", suggestion="Pipeline must have at least one step")
            return
        
        for step_name, step_config in steps.items():
            if not isinstance(step_config, dict):
                result.add_error(
                    f"Step '{step_name}' must be an object",
                    location=f"steps.{step_name}"
                )
                continue
            
            self._validate_step(step_name, step_config, result)
    
    def _validate_step(self, step_name: str, step_config: Dict[str, Any], result: ValidationResult) -> None:
        """Validate individual step configuration."""
        location = f"steps.{step_name}"
        
        # Check required fields
        if 'type' not in step_config:
            result.add_error(f"Step '{step_name}' missing required 'type' field", location=location)
            return
        
        step_type = step_config['type']
        if step_type not in self.VALID_STEP_TYPES:
            result.add_error(
                f"Step '{step_name}' has invalid type '{step_type}'",
                location=f"{location}.type",
                suggestion=f"Valid types: {', '.join(sorted(self.VALID_STEP_TYPES))}"
            )
        
        # Validate based on step type
        if step_type == 'llm_generation':
            self._validate_llm_step(step_name, step_config, result)
        elif step_type == 'user_selection':
            self._validate_selection_step(step_name, step_config, result)
        elif step_type == 'user_input':
            self._validate_input_step(step_name, step_config, result)
    
    def _validate_llm_step(self, step_name: str, step_config: Dict[str, Any], result: ValidationResult) -> None:
        """Validate LLM generation step."""
        location = f"steps.{step_name}"
        
        # Check required fields for LLM steps
        required_fields = {'description', 'model_preference', 'prompt_template'}
        missing_fields = required_fields - set(step_config.keys())
        
        for field in missing_fields:
            result.add_error(
                f"LLM step '{step_name}' missing required field '{field}'",
                location=location
            )
        
        # Validate model preferences
        if 'model_preference' in step_config:
            models = step_config['model_preference']
            if isinstance(models, list):
                for model in models:
                    if not isinstance(model, str):
                        result.add_warning(
                            f"Model preference should be string, got {type(model).__name__}",
                            location=f"{location}.model_preference"
                        )
            elif not isinstance(models, str):
                result.add_error(
                    f"Model preference must be string or list of strings",
                    location=f"{location}.model_preference"
                )
        
        # Validate prompt template
        if 'prompt_template' in step_config:
            template = step_config['prompt_template']
            if not isinstance(template, str):
                result.add_error(
                    f"Prompt template must be a string",
                    location=f"{location}.prompt_template"
                )
            elif not template.strip():
                result.add_error(
                    f"Prompt template cannot be empty",
                    location=f"{location}.prompt_template"
                )
        
        # Check for common configuration options
        if 'response_count' in step_config:
            count = step_config['response_count']
            if not isinstance(count, int) or count < 1:
                result.add_error(
                    f"Response count must be a positive integer",
                    location=f"{location}.response_count"
                )
    
    def _validate_selection_step(self, step_name: str, step_config: Dict[str, Any], result: ValidationResult) -> None:
        """Validate user selection step."""
        location = f"steps.{step_name}"
        
        if 'from_step' not in step_config:
            result.add_error(
                f"Selection step '{step_name}' missing 'from_step' field",
                location=location,
                suggestion="Specify which step's responses to select from"
            )
    
    def _validate_input_step(self, step_name: str, step_config: Dict[str, Any], result: ValidationResult) -> None:
        """Validate user input step."""
        location = f"steps.{step_name}"
        
        required_fields = {'description', 'input_type'}
        missing_fields = required_fields - set(step_config.keys())
        
        for field in missing_fields:
            result.add_error(
                f"Input step '{step_name}' missing required field '{field}'",
                location=location
            )
    
    def _add_dict_variables(self, data: Dict[str, Any], prefix: str, available_vars: Set[str]) -> None:
        """Recursively add all paths from a dictionary as available variables."""
        for key, value in data.items():
            current_path = f"{prefix}.{key}"
            available_vars.add(current_path)
            
            # If value is a dict, recursively add nested paths
            if isinstance(value, dict):
                self._add_dict_variables(value, current_path, available_vars)
    
    def _validate_variable_references(self, pipeline: Dict[str, Any], result: ValidationResult) -> None:
        """Validate that all variable references point to valid sources."""
        # Collect available variables
        available_vars = set()
        
        # Add inputs
        for input_name in pipeline.get('inputs', {}):
            available_vars.add(f'inputs.{input_name}')
        
        # Add step outputs
        for step_name in pipeline.get('steps', {}):
            available_vars.add(f'steps.{step_name}.selected_response')
            available_vars.add(f'steps.{step_name}.responses')
            available_vars.add(f'steps.{step_name}.user_input')
        
        # Add defaults variables
        if 'defaults' in pipeline:
            self._add_dict_variables(pipeline['defaults'], 'defaults', available_vars)
        
        # Add global variables
        if 'global' in pipeline:
            self._add_dict_variables(pipeline['global'], 'global', available_vars)
        
        # Check variable references in all string values
        self._check_variables_in_dict(pipeline, available_vars, result)
    
    def _check_variables_in_dict(self, data: Any, available_vars: Set[str], result: ValidationResult, path: str = "") -> None:
        """Recursively check variable references in data structure."""
        if isinstance(data, dict):
            for key, value in data.items():
                new_path = f"{path}.{key}" if path else key
                self._check_variables_in_dict(value, available_vars, result, new_path)
        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_path = f"{path}[{i}]" if path else f"[{i}]"
                self._check_variables_in_dict(item, available_vars, result, new_path)
        elif isinstance(data, str):
            # Find all variable references
            for match in self.variable_pattern.finditer(data):
                var_ref = match.group(1).strip()
                if var_ref not in available_vars:
                    result.add_error(
                        f"Unknown variable reference: '{{{{ {var_ref} }}}}'",
                        location=path,
                        suggestion=f"Available variables: {', '.join(sorted(available_vars))}"
                    )
    
    def _validate_step_dependencies(self, steps: Dict[str, Any], result: ValidationResult) -> None:
        """Validate step dependency order."""
        step_names = list(steps.keys())
        
        for i, (step_name, step_config) in enumerate(steps.items()):
            # Check if selection steps reference previous steps
            if step_config.get('type') == 'user_selection':
                from_step = step_config.get('from_step')
                if from_step:
                    if from_step not in step_names:
                        result.add_error(
                            f"Selection step '{step_name}' references unknown step '{from_step}'",
                            location=f"steps.{step_name}.from_step"
                        )
                    elif step_names.index(from_step) >= i:
                        result.add_error(
                            f"Selection step '{step_name}' references step '{from_step}' that comes after it",
                            location=f"steps.{step_name}.from_step",
                            suggestion="Steps must reference previous steps only"
                        )