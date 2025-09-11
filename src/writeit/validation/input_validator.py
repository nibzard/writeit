# ABOUTME: Input validation utilities for WriteIt CLI commands
# ABOUTME: Provides validation functions for user inputs and command parameters

import re
from pathlib import Path
from typing import List, Optional, Union, Dict, Any
from writeit.errors import ValidationError


class InputValidator:
    """Input validation utilities for WriteIt commands."""
    
    # Valid workspace name pattern (alphanumeric, hyphens, underscores)
    WORKSPACE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    # Valid template/pipeline name pattern
    TEMPLATE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    
    @staticmethod
    def validate_workspace_name(name: str) -> str:
        """Validate workspace name.
        
        Args:
            name: Workspace name to validate
            
        Returns:
            Validated workspace name
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name:
            raise ValidationError(
                message="Workspace name cannot be empty",
                suggestion="Provide a valid workspace name (alphanumeric, hyphens, underscores)"
            )
        
        if len(name) > 50:
            raise ValidationError(
                message="Workspace name is too long",
                details=f"Name '{name}' is {len(name)} characters (max 50)",
                suggestion="Use a shorter workspace name"
            )
        
        if not InputValidator.WORKSPACE_NAME_PATTERN.match(name):
            raise ValidationError(
                message="Invalid workspace name format",
                details=f"Name '{name}' contains invalid characters",
                suggestion="Use only letters, numbers, hyphens, and underscores"
            )
        
        # Reserved names
        reserved_names = {'default', 'global', 'system', 'temp', 'cache'}
        if name.lower() in reserved_names:
            raise ValidationError(
                message=f"Workspace name '{name}' is reserved",
                suggestion="Choose a different name"
            )
        
        return name
    
    @staticmethod
    def validate_template_name(name: str) -> str:
        """Validate template/pipeline name.
        
        Args:
            name: Template name to validate
            
        Returns:
            Validated template name
            
        Raises:
            ValidationError: If name is invalid
        """
        if not name:
            raise ValidationError(
                message="Template name cannot be empty",
                suggestion="Provide a valid template name"
            )
        
        if len(name) > 100:
            raise ValidationError(
                message="Template name is too long",
                details=f"Name '{name}' is {len(name)} characters (max 100)",
                suggestion="Use a shorter template name"
            )
        
        if not InputValidator.TEMPLATE_NAME_PATTERN.match(name):
            raise ValidationError(
                message="Invalid template name format",
                details=f"Name '{name}' contains invalid characters",
                suggestion="Use only letters, numbers, hyphens, and underscores"
            )
        
        return name
    
    @staticmethod
    def validate_file_path(path: Union[str, Path], must_exist: bool = True) -> Path:
        """Validate file path.
        
        Args:
            path: File path to validate
            must_exist: Whether the file must exist
            
        Returns:
            Validated Path object
            
        Raises:
            ValidationError: If path is invalid
        """
        if not path:
            raise ValidationError(
                message="File path cannot be empty",
                suggestion="Provide a valid file path"
            )
        
        path_obj = Path(path)
        
        if must_exist and not path_obj.exists():
            raise ValidationError(
                message=f"File not found: {path}",
                suggestion="Check the file path and ensure the file exists"
            )
        
        # Check if parent directory exists for new files
        if not must_exist and not path_obj.parent.exists():
            raise ValidationError(
                message=f"Parent directory does not exist: {path_obj.parent}",
                suggestion="Create the parent directory first"
            )
        
        return path_obj
    
    @staticmethod
    def validate_yaml_content(content: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Validate YAML content.
        
        Args:
            content: YAML content to validate
            file_path: Optional file path for error context
            
        Returns:
            Parsed YAML data
            
        Raises:
            ValidationError: If YAML is invalid
        """
        try:
            import yaml
            data = yaml.safe_load(content)
            return data
        except yaml.YAMLError as e:
            file_info = f" in {file_path}" if file_path else ""
            raise ValidationError(
                message=f"Invalid YAML format{file_info}",
                details=str(e),
                suggestion="Check YAML syntax and fix any formatting errors"
            )
    
    @staticmethod
    def validate_model_name(model: str) -> str:
        """Validate LLM model name.
        
        Args:
            model: Model name to validate
            
        Returns:
            Validated model name
            
        Raises:
            ValidationError: If model name is invalid
        """
        if not model:
            raise ValidationError(
                message="Model name cannot be empty",
                suggestion="Specify a valid LLM model name"
            )
        
        # Common model patterns
        valid_prefixes = [
            'gpt-', 'claude-', 'gemini-', 'llama-', 'mistral-',
            'anthropic/', 'openai/', 'google/', 'meta/',
            'huggingface/', 'cohere/', 'ai21/'
        ]
        
        if not any(model.startswith(prefix) for prefix in valid_prefixes):
            # Allow any model name but warn about common patterns
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Unusual model name '{model}' - ensure it's correct")
        
        return model
    
    @staticmethod
    def validate_scope(scope: str) -> str:
        """Validate scope value.
        
        Args:
            scope: Scope to validate ('global' or 'workspace')
            
        Returns:
            Validated scope
            
        Raises:
            ValidationError: If scope is invalid
        """
        valid_scopes = {'global', 'workspace'}
        
        if scope not in valid_scopes:
            raise ValidationError(
                message=f"Invalid scope '{scope}'",
                details=f"Scope must be one of: {', '.join(valid_scopes)}",
                suggestion="Use 'global' for system-wide or 'workspace' for current workspace"
            )
        
        return scope
    
    @staticmethod
    def validate_log_level(level: str) -> str:
        """Validate logging level.
        
        Args:
            level: Log level to validate
            
        Returns:
            Validated log level
            
        Raises:
            ValidationError: If level is invalid
        """
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        level_upper = level.upper()
        
        if level_upper not in valid_levels:
            raise ValidationError(
                message=f"Invalid log level '{level}'",
                details=f"Level must be one of: {', '.join(valid_levels)}",
                suggestion="Use standard Python logging levels"
            )
        
        return level_upper


def validate_command_inputs(**kwargs) -> Dict[str, Any]:
    """Validate multiple command inputs at once.
    
    Args:
        **kwargs: Input values to validate
        
    Returns:
        Dictionary of validated inputs
        
    Raises:
        ValidationError: If any input is invalid
    """
    validated = {}
    validator = InputValidator()
    
    for key, value in kwargs.items():
        if value is None:
            continue
            
        if key.endswith('_workspace_name') or key == 'workspace_name':
            validated[key] = validator.validate_workspace_name(value)
        elif key.endswith('_template_name') or key == 'template_name':
            validated[key] = validator.validate_template_name(value)
        elif key.endswith('_path') or key == 'file_path':
            validated[key] = validator.validate_file_path(value)
        elif key == 'model':
            validated[key] = validator.validate_model_name(value)
        elif key == 'scope':
            validated[key] = validator.validate_scope(value)
        elif key == 'log_level':
            validated[key] = validator.validate_log_level(value)
        else:
            # Pass through unknown keys
            validated[key] = value
    
    return validated