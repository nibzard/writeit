"""Domain-specific validators for WriteIt entities."""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_validators import (
    DirectoryExistsValidator,
    NotNullValidator, 
    PathTraversalValidator,
    RegexValidator,
    StringLengthValidator,
)
from .framework import CompositeValidationRule
from .interfaces import ValidationContext, ValidationResult, ValidationRule


class PipelineTemplateValidator(ValidationRule[Dict[str, Any]]):
    """Validates pipeline template structure and content."""
    
    REQUIRED_FIELDS = {"metadata", "steps"}
    METADATA_REQUIRED_FIELDS = {"name", "description", "version"}
    
    def validate(self, value: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        if not isinstance(value, dict):
            return ValidationResult.failure(["Pipeline template must be a dictionary"])
        
        errors = []
        warnings = []
        
        # Check required top-level fields
        missing_fields = self.REQUIRED_FIELDS - set(value.keys())
        if missing_fields:
            errors.append(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Validate metadata section
        metadata = value.get("metadata", {})
        if isinstance(metadata, dict):
            missing_metadata = self.METADATA_REQUIRED_FIELDS - set(metadata.keys())
            if missing_metadata:
                errors.append(f"Missing required metadata fields: {', '.join(missing_metadata)}")
            
            # Validate metadata values
            if "name" in metadata and not isinstance(metadata["name"], str):
                errors.append("Metadata 'name' must be a string")
            
            if "version" in metadata:
                version_result = self._validate_version(metadata["version"])
                if not version_result.is_valid:
                    errors.extend(version_result.errors)
        
        # Validate steps section
        steps = value.get("steps", {})
        if not isinstance(steps, dict):
            errors.append("Steps must be a dictionary")
        elif not steps:
            warnings.append("Pipeline has no steps defined")
        else:
            step_errors = self._validate_steps(steps)
            errors.extend(step_errors)
        
        # Validate inputs if present
        if "inputs" in value:
            input_errors = self._validate_inputs(value["inputs"])
            errors.extend(input_errors)
        
        if errors:
            return ValidationResult.failure(errors, warnings)
        return ValidationResult.success(warnings)
    
    def _validate_version(self, version: Any) -> ValidationResult:
        """Validate version format (semantic versioning)."""
        if not isinstance(version, str):
            return ValidationResult.failure(["Version must be a string"])
        
        # Simple semantic version pattern
        version_pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9\-\.]+)?$'
        validator = RegexValidator(version_pattern, "Version must follow semantic versioning (e.g., '1.0.0')")
        return validator.validate(version, ValidationContext())
    
    def _validate_steps(self, steps: Dict[str, Any]) -> List[str]:
        """Validate steps structure."""
        errors = []
        
        for step_id, step_config in steps.items():
            if not isinstance(step_config, dict):
                errors.append(f"Step '{step_id}' must be a dictionary")
                continue
            
            # Check required step fields
            required_step_fields = {"name", "type"}
            missing_step_fields = required_step_fields - set(step_config.keys())
            if missing_step_fields:
                errors.append(f"Step '{step_id}' missing required fields: {', '.join(missing_step_fields)}")
            
            # Validate step type
            step_type = step_config.get("type")
            if step_type and step_type not in {"llm_generate", "template_render", "file_write", "custom"}:
                errors.append(f"Step '{step_id}' has invalid type: {step_type}")
            
            # Validate dependencies
            if "depends_on" in step_config:
                depends_on = step_config["depends_on"]
                if isinstance(depends_on, list):
                    for dep in depends_on:
                        if dep not in steps:
                            errors.append(f"Step '{step_id}' depends on unknown step: {dep}")
                elif isinstance(depends_on, str):
                    if depends_on not in steps:
                        errors.append(f"Step '{step_id}' depends on unknown step: {depends_on}")
        
        return errors
    
    def _validate_inputs(self, inputs: Any) -> List[str]:
        """Validate inputs structure."""
        errors = []
        
        if not isinstance(inputs, dict):
            errors.append("Inputs must be a dictionary")
            return errors
        
        for input_id, input_config in inputs.items():
            if not isinstance(input_config, dict):
                errors.append(f"Input '{input_id}' must be a dictionary")
                continue
            
            # Check required input fields
            if "type" not in input_config:
                errors.append(f"Input '{input_id}' missing required field: type")
            
            input_type = input_config.get("type")
            if input_type not in {"text", "choice", "number", "boolean", "file"}:
                errors.append(f"Input '{input_id}' has invalid type: {input_type}")
            
            # Validate choice options
            if input_type == "choice" and "options" not in input_config:
                errors.append(f"Input '{input_id}' of type 'choice' must have 'options'")
        
        return errors
    
    @property
    def description(self) -> str:
        return "Pipeline template must have valid structure with metadata and steps"


class WorkspaceValidator(ValidationRule[str]):
    """Validates workspace names and configuration."""
    
    def __init__(self):
        # Workspace names must be valid identifiers
        self._name_validator = CompositeValidationRule([
            NotNullValidator(),
            StringLengthValidator(min_length=1, max_length=50),
            RegexValidator(
                r'^[a-zA-Z][a-zA-Z0-9_-]*$',
                "Workspace name must start with a letter and contain only letters, numbers, underscores, and hyphens"
            )
        ])
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        return self._name_validator.validate(value, context)
    
    @property
    def description(self) -> str:
        return "Workspace name must be a valid identifier"


class FilePathValidator(ValidationRule[str]):
    """Validates file paths for security and existence."""
    
    def __init__(self, base_path: Optional[str] = None, 
                 must_exist: bool = False,
                 allowed_extensions: Optional[List[str]] = None):
        self._base_path = base_path
        self._must_exist = must_exist
        self._allowed_extensions = allowed_extensions
        
        # Build composite validator
        validators = [
            NotNullValidator(),
            PathTraversalValidator(base_path)
        ]
        
        if allowed_extensions:
            from .base_validators import FileExtensionValidator
            validators.append(FileExtensionValidator(allowed_extensions))
        
        self._composite_validator = CompositeValidationRule(validators)
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        # First run the composite validator
        result = self._composite_validator.validate(value, context)
        if not result.is_valid:
            return result
        
        # Check existence if required
        if self._must_exist:
            path = Path(value)
            if not path.exists():
                return ValidationResult.failure([f"File does not exist: {value}"])
            
            if not path.is_file():
                return ValidationResult.failure([f"Path is not a file: {value}"])
        
        return result
    
    @property
    def description(self) -> str:
        parts = ["File path must be safe"]
        if self._must_exist:
            parts.append("and exist")
        if self._allowed_extensions:
            parts.append(f"with extension: {', '.join(self._allowed_extensions)}")
        return " ".join(parts)


class ConfigurationValueValidator(ValidationRule[Any]):
    """Validates configuration values based on their expected type."""
    
    def __init__(self, expected_type: type, 
                 allowed_values: Optional[List[Any]] = None,
                 min_value: Optional[Any] = None,
                 max_value: Optional[Any] = None):
        self._expected_type = expected_type
        self._allowed_values = allowed_values
        self._min_value = min_value
        self._max_value = max_value
    
    def validate(self, value: Any, context: ValidationContext) -> ValidationResult:
        errors = []
        
        # Check type
        if not isinstance(value, self._expected_type):
            errors.append(f"Value must be of type {self._expected_type.__name__}, got {type(value).__name__}")
            return ValidationResult.failure(errors)
        
        # Check allowed values
        if self._allowed_values is not None and value not in self._allowed_values:
            errors.append(f"Value must be one of: {', '.join(map(str, self._allowed_values))}")
        
        # Check range for comparable types
        if self._min_value is not None and value < self._min_value:
            errors.append(f"Value must be at least {self._min_value}")
        
        if self._max_value is not None and value > self._max_value:
            errors.append(f"Value must be at most {self._max_value}")
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success()
    
    @property
    def description(self) -> str:
        constraints = [f"must be {self._expected_type.__name__}"]
        
        if self._allowed_values:
            constraints.append(f"one of: {', '.join(map(str, self._allowed_values))}")
        
        if self._min_value is not None:
            constraints.append(f"≥ {self._min_value}")
        
        if self._max_value is not None:
            constraints.append(f"≤ {self._max_value}")
        
        return "Configuration value " + ", ".join(constraints)


class YAMLContentValidator(ValidationRule[str]):
    """Validates YAML content for syntax and structure."""
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        try:
            # Try to parse the YAML
            parsed = yaml.safe_load(value)
            
            # Check for empty content
            if parsed is None:
                return ValidationResult.success(warnings=["YAML content is empty"])
            
            return ValidationResult.success()
            
        except yaml.YAMLError as e:
            return ValidationResult.failure([f"Invalid YAML syntax: {e}"])
    
    @property
    def description(self) -> str:
        return "Content must be valid YAML syntax"