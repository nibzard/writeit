# ABOUTME: Template validators for WriteIt pipeline and style files
# ABOUTME: Validates pipeline templates and style primers using the shared validation framework

import yaml
import re
import warnings
from pathlib import Path
from typing import Dict, Any, Set, List, Optional
from dataclasses import dataclass

from .interfaces import ValidationContext, ValidationRule, ValidationResult
from .validation_result import (
    ValidationResult as TemplateValidationResult,
    ValidationIssue,
    IssueType,
)


class PipelineValidator(ValidationRule[Path]):
    """Validates WriteIt pipeline template files."""

    # Required top-level keys for pipeline templates
    REQUIRED_KEYS = {"metadata", "inputs", "steps"}

    # Required metadata fields
    REQUIRED_METADATA = {"name", "description", "version", "author"}

    # Valid step types
    VALID_STEP_TYPES = {"llm_generation", "user_selection", "user_input"}

    # Valid LLM providers
    VALID_LLM_PROVIDERS = {"openai", "anthropic", "google", "ollama"}

    def __init__(self) -> None:
        """Initialize the pipeline validator."""
        self.variable_pattern = re.compile(r"\{\{\s*([^}]+)\s*\}\}")

    def validate(self, file_path: Path, context: ValidationContext) -> ValidationResult:
        """Validate a pipeline template file."""
        errors: List[str] = []
        warnings: List[str] = []
        metadata: Dict[str, Any] = {}

        try:
            # Check file exists and is readable
            if not file_path.exists():
                errors.append(f"Pipeline file not found: {file_path}")
                return ValidationResult.failure(errors, warnings, metadata)

            if not file_path.is_file():
                errors.append(f"Path is not a file: {file_path}")
                return ValidationResult.failure(errors, warnings, metadata)

            # Load and parse YAML
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax: {str(e)}")
                return ValidationResult.failure(errors, warnings, metadata)

            # Validate top-level structure
            missing_keys = self.REQUIRED_KEYS - set(data.keys())
            if missing_keys:
                errors.append(f"Missing required top-level keys: {', '.join(missing_keys)}")

            # Validate metadata
            if 'metadata' in data:
                metadata_errors = self._validate_metadata(data['metadata'])
                errors.extend(metadata_errors)

            # Validate inputs
            if 'inputs' in data:
                input_errors = self._validate_inputs(data['inputs'])
                errors.extend(input_errors)

            # Validate steps
            if 'steps' in data:
                step_errors = self._validate_steps(data['steps'])
                errors.extend(step_errors)

            # Validate variable references
            var_errors = self._validate_variable_references(data)
            warnings.extend(var_errors)

            # Add metadata
            metadata['file_path'] = str(file_path)
            metadata['file_type'] = 'pipeline'
            metadata['size'] = file_path.stat().st_size

            if errors:
                return ValidationResult.failure(errors, warnings, metadata)
            else:
                return ValidationResult.success(warnings, metadata)

        except Exception as e:
            errors.append(f"Unexpected error during validation: {str(e)}")
            return ValidationResult.failure(errors, warnings, metadata)

    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate metadata section."""
        errors: List[str] = []
        
        missing_metadata = self.REQUIRED_METADATA - set(metadata.keys())
        if missing_metadata:
            errors.append(f"Missing required metadata fields: {', '.join(missing_metadata)}")

        # Validate version format
        if 'version' in metadata:
            version = metadata['version']
            if not isinstance(version, str) or not re.match(r'^\d+\.\d+\.\d+$', str(version)):
                errors.append("Version must be in semantic versioning format (e.g., 1.0.0)")

        return errors

    def _validate_inputs(self, inputs: Dict[str, Any]) -> List[str]:
        """Validate inputs section."""
        errors: List[str] = []

        if not isinstance(inputs, dict):
            errors.append("Inputs must be a dictionary")
            return errors

        for input_name, input_config in inputs.items():
            if not isinstance(input_config, dict):
                errors.append(f"Input '{input_name}' must be a dictionary")
                continue

            # Required fields for each input
            if 'type' not in input_config:
                errors.append(f"Input '{input_name}' missing required 'type' field")

            # Validate type
            if 'type' in input_config:
                valid_types = {'text', 'choice', 'number', 'boolean'}
                if input_config['type'] not in valid_types:
                    errors.append(f"Input '{input_name}' has invalid type: {input_config['type']}")

        return errors

    def _validate_steps(self, steps: Dict[str, Any]) -> List[str]:
        """Validate steps section."""
        errors: List[str] = []

        if not isinstance(steps, dict):
            errors.append("Steps must be a dictionary")
            return errors

        for step_name, step_config in steps.items():
            if not isinstance(step_config, dict):
                errors.append(f"Step '{step_name}' must be a dictionary")
                continue

            # Required fields for each step
            if 'type' not in step_config:
                errors.append(f"Step '{step_name}' missing required 'type' field")

            # Validate step type
            if 'type' in step_config:
                if step_config['type'] not in self.VALID_STEP_TYPES:
                    errors.append(f"Step '{step_name}' has invalid type: {step_config['type']}")

            # Validate LLM-specific fields
            if step_config.get('type') == 'llm_generation':
                if 'prompt_template' not in step_config:
                    errors.append(f"LLM step '{step_name}' missing required 'prompt_template' field")

                # Validate model preference
                if 'model_preference' in step_config:
                    model_pref = step_config['model_preference']
                    if isinstance(model_pref, list):
                        for model in model_pref:
                            if not any(model.startswith(provider) for provider in self.VALID_LLM_PROVIDERS):
                                errors.append(f"Step '{step_name}' has invalid model provider: {model}")

            # Validate dependencies
            if 'depends_on' in step_config:
                deps = step_config['depends_on']
                if isinstance(deps, list):
                    for dep in deps:
                        if dep not in steps:
                            errors.append(f"Step '{step_name}' depends on non-existent step: {dep}")
                elif isinstance(deps, str):
                    if deps not in steps:
                        errors.append(f"Step '{step_name}' depends on non-existent step: {deps}")
                else:
                    errors.append(f"Step '{step_name}' 'depends_on' must be a string or list")

        return errors

    def _validate_variable_references(self, data: Dict[str, Any]) -> List[str]:
        """Validate variable references in templates."""
        errors: List[str] = []
        
        # Collect all available variables
        available_vars: set[str] = set()
        
        # Add input variables
        if 'inputs' in data:
            available_vars.update(f"inputs.{key}" for key in data['inputs'].keys())
            available_vars.update(data['inputs'].keys())  # shorthand without inputs. prefix
        
        # Add step outputs
        if 'steps' in data:
            available_vars.update(f"steps.{key}" for key in data['steps'].keys())
        
        # Check variable references in prompt templates
        if 'steps' in data:
            for step_name, step_config in data['steps'].items():
                if 'prompt_template' in step_config:
                    template = step_config['prompt_template']
                    if isinstance(template, str):
                        refs = self.variable_pattern.findall(template)
                        for ref in refs:
                            # Strip whitespace and check if it's a valid variable
                            ref = ref.strip()
                            if ref not in available_vars:
                                errors.append(f"Step '{step_name}' references undefined variable: {ref}")

        return errors

    def validate_file(self, file_path: Path) -> TemplateValidationResult:
        """Validate a pipeline template file (legacy compatibility)."""
        context = ValidationContext(strict_mode=False)
        framework_result = self.validate(file_path, context)
        
        # Convert framework result to template result
        template_result = TemplateValidationResult(
            file_path=file_path,
            is_valid=framework_result.is_valid,
            issues=[],
            metadata=framework_result.metadata,
            file_type="pipeline"
        )
        
        # Convert errors and warnings to issues
        for error in framework_result.errors:
            template_result.add_error(error)
        
        for warning in framework_result.warnings:
            template_result.add_warning(warning)
        
        return template_result


class StyleValidator(ValidationRule[Path]):
    """Validates WriteIt style primer files."""

    # Required top-level keys for style primers
    REQUIRED_KEYS = {"metadata", "voice", "language", "structure"}

    # Required metadata fields
    REQUIRED_METADATA = {
        "name",
        "description",
        "version",
        "author",
        "category",
        "difficulty",
    }

    # Valid categories
    VALID_CATEGORIES = {
        "professional",
        "informal",
        "academic",
        "creative",
        "marketing",
        "technical",
    }

    # Valid difficulty levels
    VALID_DIFFICULTIES = {"beginner", "intermediate", "advanced"}

    # Common style primer sections
    COMMON_SECTIONS = {
        "voice",
        "language",
        "structure",
        "formatting",
        "audience",
        "examples",
        "anti_patterns",
        "integration",
    }

    def __init__(self) -> None:
        """Initialize the style validator."""
        pass

    def validate(self, file_path: Path, context: ValidationContext) -> ValidationResult:
        """Validate a style primer file."""
        errors: List[str] = []
        warnings: List[str] = []
        metadata: Dict[str, Any] = {}

        try:
            # Check file exists and is readable
            if not file_path.exists():
                errors.append(f"Style file not found: {file_path}")
                return ValidationResult.failure(errors, warnings, metadata)

            if not file_path.is_file():
                errors.append(f"Path is not a file: {file_path}")
                return ValidationResult.failure(errors, warnings, metadata)

            # Load and parse YAML
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                errors.append(f"Invalid YAML syntax: {str(e)}")
                return ValidationResult.failure(errors, warnings, metadata)

            # Validate top-level structure
            missing_keys = self.REQUIRED_KEYS - set(data.keys())
            if missing_keys:
                errors.append(f"Missing required top-level keys: {', '.join(missing_keys)}")

            # Validate metadata
            if 'metadata' in data:
                metadata_errors = self._validate_metadata(data['metadata'])
                errors.extend(metadata_errors)

            # Validate voice
            if 'voice' in data:
                voice_errors = self._validate_voice(data['voice'])
                errors.extend(voice_errors)

            # Validate language
            if 'language' in data:
                language_errors = self._validate_language(data['language'])
                errors.extend(language_errors)

            # Validate structure
            if 'structure' in data:
                structure_errors = self._validate_structure(data['structure'])
                errors.extend(structure_errors)

            # Check for recommended sections
            self._check_recommended_sections(data, warnings)

            # Add metadata
            metadata['file_path'] = str(file_path)
            metadata['file_type'] = 'style'
            metadata['size'] = file_path.stat().st_size

            if errors:
                return ValidationResult.failure(errors, warnings, metadata)
            else:
                return ValidationResult.success(warnings, metadata)

        except Exception as e:
            errors.append(f"Unexpected error during validation: {str(e)}")
            return ValidationResult.failure(errors, warnings, metadata)

    def _validate_metadata(self, metadata: Dict[str, Any]) -> List[str]:
        """Validate metadata section."""
        errors: List[str] = []
        
        missing_metadata = self.REQUIRED_METADATA - set(metadata.keys())
        if missing_metadata:
            errors.append(f"Missing required metadata fields: {', '.join(missing_metadata)}")

        # Validate category
        if 'category' in metadata:
            category = metadata['category']
            if category not in self.VALID_CATEGORIES:
                errors.append(f"Invalid category: {category}. Valid options: {', '.join(self.VALID_CATEGORIES)}")

        # Validate difficulty
        if 'difficulty' in metadata:
            difficulty = metadata['difficulty']
            if difficulty not in self.VALID_DIFFICULTIES:
                errors.append(f"Invalid difficulty: {difficulty}. Valid options: {', '.join(self.VALID_DIFFICULTIES)}")

        # Validate version format
        if 'version' in metadata:
            version = metadata['version']
            if not isinstance(version, str) or not re.match(r'^\d+\.\d+\.\d+$', str(version)):
                errors.append("Version must be in semantic versioning format (e.g., 1.0.0)")

        return errors

    def _validate_voice(self, voice: Dict[str, Any]) -> List[str]:
        """Validate voice section."""
        errors: List[str] = []

        if not isinstance(voice, dict):
            errors.append("Voice section must be a dictionary")
            return errors

        # Check for key voice attributes
        if 'tone' not in voice and 'personality' not in voice:
            errors.append("Voice section should include 'tone' or 'personality' attributes")

        return errors

    def _validate_language(self, language: Dict[str, Any]) -> List[str]:
        """Validate language section."""
        errors: List[str] = []

        if not isinstance(language, dict):
            errors.append("Language section must be a dictionary")
            return errors

        # Check for key language attributes
        if 'vocabulary' not in language and 'grammar' not in language:
            errors.append("Language section should include 'vocabulary' or 'grammar' attributes")

        return errors

    def _validate_structure(self, structure: Dict[str, Any]) -> List[str]:
        """Validate structure section."""
        errors: List[str] = []

        if not isinstance(structure, dict):
            errors.append("Structure section must be a dictionary")
            return errors

        # Check for key structure attributes
        if 'organization' not in structure and 'formatting' not in structure:
            errors.append("Structure section should include 'organization' or 'formatting' attributes")

        return errors

    def _check_recommended_sections(self, data: Dict[str, Any], warnings: List[str]) -> None:
        """Check for recommended sections and add warnings if missing."""
        present_sections = set(data.keys())
        missing_recommended = self.COMMON_SECTIONS - present_sections - self.REQUIRED_KEYS
        
        if missing_recommended:
            warnings.append(f"Consider adding recommended sections: {', '.join(missing_recommended)}")

    def validate_file(self, file_path: Path) -> TemplateValidationResult:
        """Validate a style primer file (legacy compatibility)."""
        context = ValidationContext(strict_mode=False)
        framework_result = self.validate(file_path, context)
        
        # Convert framework result to template result
        template_result = TemplateValidationResult(
            file_path=file_path,
            is_valid=framework_result.is_valid,
            issues=[],
            metadata=framework_result.metadata,
            file_type="style"
        )
        
        # Convert errors and warnings to issues
        for error in framework_result.errors:
            template_result.add_error(error)
        
        for warning in framework_result.warnings:
            template_result.add_warning(warning)
        
        return template_result