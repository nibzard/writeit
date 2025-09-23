"""API Validation with domain validation rules.

Provides validation for API requests using domain validation logic
while maintaining proper separation of concerns and error handling.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Type, Union, Callable
from enum import Enum
import re
from pathlib import Path

from pydantic import BaseModel, validator, ValidationError as PydanticValidationError
from fastapi import HTTPException, status

from ...domains.workspace.value_objects import WorkspaceName
from ...domains.pipeline.value_objects import PipelineId, StepId, PipelineName, PipelineVersion
from ...domains.content.value_objects import ContentId, TemplateId, StyleId
from ...shared.errors.base import ValidationError


class ValidationType(str, Enum):
    """Types of validation."""
    REQUIRED = "required"
    FORMAT = "format"
    RANGE = "range"
    PATTERN = "pattern"
    ENUM = "enum"
    CUSTOM = "custom"


@dataclass
class ValidationRule:
    """Validation rule definition."""
    field: str
    rule_type: ValidationType
    message: str
    condition: Optional[Any] = None
    validator_func: Optional[Callable] = None


@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_errors: Dict[str, List[str]]
    
    def __post_init__(self):
        if not self.errors:
            self.errors = []
        if not self.warnings:
            self.warnings = []
        if not self.field_errors:
            self.field_errors = {}
    
    def add_error(self, field: str, message: str) -> None:
        """Add field error."""
        if field not in self.field_errors:
            self.field_errors[field] = []
        self.field_errors[field].append(message)
        self.errors.append(f"{field}: {message}")
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add warning."""
        self.warnings.append(message)


# Request Models with Validation

class CreateWorkspaceRequest(BaseModel):
    """Request model for creating workspace."""
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    
    @validator('name')
    def validate_workspace_name(cls, v):
        """Validate workspace name."""
        if not v or not v.strip():
            raise ValueError("Workspace name cannot be empty")
        
        if len(v) < 2 or len(v) > 50:
            raise ValueError("Workspace name must be between 2 and 50 characters")
        
        # Check for valid characters (alphanumeric, hyphens, underscores)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Workspace name can only contain letters, numbers, hyphens, and underscores")
        
        # Cannot start with hyphen
        if v.startswith('-'):
            raise ValueError("Workspace name cannot start with a hyphen")
        
        return v.lower()  # Normalize to lowercase


class UpdateWorkspaceRequest(BaseModel):
    """Request model for updating workspace."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None


class CreatePipelineTemplateRequest(BaseModel):
    """Request model for creating pipeline template."""
    name: str
    description: Optional[str] = None
    content: str
    version: str = "1.0.0"
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    workspace_name: Optional[str] = None
    
    @validator('name')
    def validate_pipeline_name(cls, v):
        """Validate pipeline name."""
        if not v or not v.strip():
            raise ValueError("Pipeline name cannot be empty")
        
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Pipeline name must be between 2 and 100 characters")
        
        return v.strip()
    
    @validator('version')
    def validate_version(cls, v):
        """Validate semantic version."""
        if not re.match(r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9-]+)?$', v):
            raise ValueError("Version must follow semantic versioning (e.g., 1.0.0)")
        
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """Validate YAML content."""
        if not v or not v.strip():
            raise ValueError("Pipeline content cannot be empty")
        
        # Basic YAML structure validation could be added here
        return v.strip()


class UpdatePipelineTemplateRequest(BaseModel):
    """Request model for updating pipeline template."""
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    version: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    
    @validator('version')
    def validate_version(cls, v):
        """Validate semantic version."""
        if v and not re.match(r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9-]+)?$', v):
            raise ValueError("Version must follow semantic versioning (e.g., 1.0.0)")
        
        return v


class ExecutePipelineRequest(BaseModel):
    """Request model for executing pipeline."""
    pipeline_name: str
    workspace_name: Optional[str] = None
    inputs: Optional[Dict[str, Any]] = None
    execution_options: Optional[Dict[str, Any]] = None
    
    @validator('pipeline_name')
    def validate_pipeline_name(cls, v):
        """Validate pipeline name."""
        if not v or not v.strip():
            raise ValueError("Pipeline name cannot be empty")
        
        return v.strip()


class CreateContentRequest(BaseModel):
    """Request model for creating content."""
    name: str
    content_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    workspace_name: Optional[str] = None
    
    @validator('name')
    def validate_content_name(cls, v):
        """Validate content name."""
        if not v or not v.strip():
            raise ValueError("Content name cannot be empty")
        
        if len(v) < 2 or len(v) > 100:
            raise ValueError("Content name must be between 2 and 100 characters")
        
        return v.strip()
    
    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate content type."""
        allowed_types = ['template', 'style', 'document', 'snippet']
        if v not in allowed_types:
            raise ValueError(f"Content type must be one of: {', '.join(allowed_types)}")
        
        return v
    
    @validator('content')
    def validate_content(cls, v):
        """Validate content."""
        if not v or not v.strip():
            raise ValueError("Content cannot be empty")
        
        return v


# Domain Validators

class DomainValidator(ABC):
    """Abstract base class for domain validation."""
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data against domain rules."""
        pass


class WorkspaceValidator(DomainValidator):
    """Validator for workspace operations."""
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate workspace data."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})
        
        # Validate workspace name
        if 'name' in data:
            name = data['name']
            try:
                WorkspaceName(name)
            except ValueError as e:
                result.add_error('name', str(e))
        
        # Validate configuration
        if 'configuration' in data and data['configuration']:
            config = data['configuration']
            if not isinstance(config, dict):
                result.add_error('configuration', 'Configuration must be a dictionary')
            else:
                # Validate configuration structure
                self._validate_workspace_configuration(config, result)
        
        return result
    
    def _validate_workspace_configuration(self, config: Dict[str, Any], result: ValidationResult) -> None:
        """Validate workspace configuration structure."""
        # Check for required configuration sections
        recommended_sections = ['llm_settings', 'storage_settings', 'execution_settings']
        
        for section in recommended_sections:
            if section not in config:
                result.add_warning(f"Consider adding '{section}' configuration section")
        
        # Validate LLM settings if present
        if 'llm_settings' in config:
            llm_settings = config['llm_settings']
            if not isinstance(llm_settings, dict):
                result.add_error('configuration.llm_settings', 'LLM settings must be a dictionary')
            else:
                # Validate specific LLM settings
                if 'default_model' in llm_settings:
                    model = llm_settings['default_model']
                    if not isinstance(model, str) or not model.strip():
                        result.add_error('configuration.llm_settings.default_model', 'Default model must be a non-empty string')


class PipelineValidator(DomainValidator):
    """Validator for pipeline operations."""
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate pipeline data."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})
        
        # Validate pipeline ID
        if 'id' in data:
            try:
                PipelineId(data['id'])
            except ValueError as e:
                result.add_error('id', str(e))
        
        # Validate pipeline name
        if 'name' in data:
            try:
                PipelineName(data['name'])
            except ValueError as e:
                result.add_error('name', str(e))
        
        # Validate version
        if 'version' in data:
            try:
                PipelineVersion(data['version'])
            except ValueError as e:
                result.add_error('version', str(e))
        
        # Validate content structure
        if 'content' in data:
            self._validate_pipeline_content(data['content'], result)
        
        return result
    
    def _validate_pipeline_content(self, content: str, result: ValidationResult) -> None:
        """Validate pipeline YAML content."""
        try:
            import yaml
            parsed = yaml.safe_load(content)
            
            if not isinstance(parsed, dict):
                result.add_error('content', 'Pipeline content must be a valid YAML object')
                return
            
            # Check required sections
            required_sections = ['metadata', 'inputs', 'steps']
            for section in required_sections:
                if section not in parsed:
                    result.add_error('content', f"Missing required section: {section}")
            
            # Validate metadata section
            if 'metadata' in parsed:
                metadata = parsed['metadata']
                if not isinstance(metadata, dict):
                    result.add_error('content.metadata', 'Metadata must be an object')
                else:
                    required_metadata = ['name', 'description']
                    for field in required_metadata:
                        if field not in metadata:
                            result.add_error('content.metadata', f"Missing required metadata field: {field}")
            
            # Validate inputs section
            if 'inputs' in parsed:
                inputs = parsed['inputs']
                if not isinstance(inputs, dict):
                    result.add_error('content.inputs', 'Inputs must be an object')
            
            # Validate steps section
            if 'steps' in parsed:
                steps = parsed['steps']
                if not isinstance(steps, dict):
                    result.add_error('content.steps', 'Steps must be an object')
                else:
                    for step_name, step_config in steps.items():
                        self._validate_step(step_name, step_config, result)
        
        except yaml.YAMLError as e:
            result.add_error('content', f"Invalid YAML: {str(e)}")
        except Exception as e:
            result.add_error('content', f"Content validation error: {str(e)}")
    
    def _validate_step(self, step_name: str, step_config: Dict[str, Any], result: ValidationResult) -> None:
        """Validate individual pipeline step."""
        if not isinstance(step_config, dict):
            result.add_error(f'content.steps.{step_name}', 'Step configuration must be an object')
            return
        
        # Check required step fields
        required_fields = ['name', 'type']
        for field in required_fields:
            if field not in step_config:
                result.add_error(f'content.steps.{step_name}', f"Missing required field: {field}")
        
        # Validate step type
        if 'type' in step_config:
            step_type = step_config['type']
            allowed_types = ['llm_generate', 'llm_edit', 'user_input', 'transformation']
            if step_type not in allowed_types:
                result.add_warning(f'content.steps.{step_name}.type', f"Unknown step type: {step_type}")


class ContentValidator(DomainValidator):
    """Validator for content operations."""
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate content data."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[], field_errors={})
        
        # Validate content ID
        if 'id' in data:
            try:
                ContentId(data['id'])
            except ValueError as e:
                result.add_error('id', str(e))
        
        # Validate content type
        if 'content_type' in data:
            content_type = data['content_type']
            allowed_types = ['template', 'style', 'document', 'snippet']
            if content_type not in allowed_types:
                result.add_error('content_type', f"Content type must be one of: {', '.join(allowed_types)}")
        
        # Validate content based on type
        if 'content' in data and 'content_type' in data:
            self._validate_content_by_type(data['content'], data['content_type'], result)
        
        return result
    
    def _validate_content_by_type(self, content: str, content_type: str, result: ValidationResult) -> None:
        """Validate content based on its type."""
        if content_type == 'template':
            self._validate_template_content(content, result)
        elif content_type == 'style':
            self._validate_style_content(content, result)
        # Add more content type validations as needed
    
    def _validate_template_content(self, content: str, result: ValidationResult) -> None:
        """Validate template content."""
        # Check for common template syntax issues
        if '{{' in content and '}}' not in content:
            result.add_error('content', 'Template has opening braces without closing braces')
        elif '}}' in content and '{{' not in content:
            result.add_error('content', 'Template has closing braces without opening braces')
        
        # Count balanced braces
        open_count = content.count('{{')
        close_count = content.count('}}')
        if open_count != close_count:
            result.add_error('content', 'Template has unbalanced braces')
    
    def _validate_style_content(self, content: str, result: ValidationResult) -> None:
        """Validate style content."""
        # Basic style validation - could be expanded
        if not content.strip():
            result.add_error('content', 'Style content cannot be empty')


# API Validation Manager

class APIValidator:
    """Central validator for API requests."""
    
    def __init__(self):
        self._validators: Dict[str, DomainValidator] = {
            'workspace': WorkspaceValidator(),
            'pipeline': PipelineValidator(),
            'content': ContentValidator()
        }
    
    def validate_request(self, domain: str, data: Dict[str, Any]) -> ValidationResult:
        """Validate request data for a specific domain."""
        validator = self._validators.get(domain)
        if not validator:
            raise ValueError(f"No validator found for domain: {domain}")
        
        return validator.validate(data)
    
    def validate_and_raise(self, domain: str, data: Dict[str, Any]) -> None:
        """Validate and raise HTTPException if validation fails."""
        result = self.validate_request(domain, data)
        
        if not result.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_type": "validation_error",
                    "message": "Request validation failed",
                    "errors": result.errors,
                    "field_errors": result.field_errors,
                    "warnings": result.warnings
                }
            )
    
    def register_validator(self, domain: str, validator: DomainValidator) -> None:
        """Register custom validator for domain."""
        self._validators[domain] = validator


# Global validator instance
api_validator = APIValidator()


# Utility functions

def validate_workspace_request(data: Dict[str, Any]) -> None:
    """Validate workspace request and raise if invalid."""
    api_validator.validate_and_raise('workspace', data)


def validate_pipeline_request(data: Dict[str, Any]) -> None:
    """Validate pipeline request and raise if invalid."""
    api_validator.validate_and_raise('pipeline', data)


def validate_content_request(data: Dict[str, Any]) -> None:
    """Validate content request and raise if invalid."""
    api_validator.validate_and_raise('content', data)


def handle_pydantic_validation_error(exc: PydanticValidationError) -> HTTPException:
    """Convert Pydantic validation error to HTTP exception."""
    errors = []
    field_errors = {}
    
    for error in exc.errors():
        field = '.'.join(str(loc) for loc in error['loc'])
        message = error['msg']
        
        errors.append(f"{field}: {message}")
        
        if field not in field_errors:
            field_errors[field] = []
        field_errors[field].append(message)
    
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "error_type": "validation_error",
            "message": "Request validation failed",
            "errors": errors,
            "field_errors": field_errors
        }
    )