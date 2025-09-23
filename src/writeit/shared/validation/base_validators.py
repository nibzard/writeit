"""Base validation rules for common scenarios."""

import os
import re
from pathlib import Path
from typing import Any, List, Optional, Pattern, Union

from .interfaces import ValidationContext, ValidationResult, ValidationRule


class NotNullValidator(ValidationRule[Any]):
    """Validates that a value is not None."""
    
    def validate(self, value: Any, context: ValidationContext) -> ValidationResult:
        if value is None:
            return ValidationResult.failure(["Value cannot be null"])
        return ValidationResult.success()
    
    @property
    def description(self) -> str:
        return "Value must not be null"


class StringLengthValidator(ValidationRule[str]):
    """Validates string length constraints."""
    
    def __init__(self, min_length: Optional[int] = None, 
                 max_length: Optional[int] = None):
        self._min_length = min_length
        self._max_length = max_length
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        errors = []
        
        if self._min_length is not None and len(value) < self._min_length:
            errors.append(f"String must be at least {self._min_length} characters long")
        
        if self._max_length is not None and len(value) > self._max_length:
            errors.append(f"String must be at most {self._max_length} characters long")
        
        if errors:
            return ValidationResult.failure(errors)
        
        return ValidationResult.success()
    
    @property
    def description(self) -> str:
        constraints = []
        if self._min_length is not None:
            constraints.append(f"min length {self._min_length}")
        if self._max_length is not None:
            constraints.append(f"max length {self._max_length}")
        
        if constraints:
            return f"String length ({', '.join(constraints)})"
        return "String length validation"


class RegexValidator(ValidationRule[str]):
    """Validates strings against a regular expression."""
    
    def __init__(self, pattern: Union[str, Pattern], 
                 error_message: Optional[str] = None):
        if isinstance(pattern, str):
            self._pattern = re.compile(pattern)
            self._pattern_str = pattern
        else:
            self._pattern = pattern
            self._pattern_str = pattern.pattern
        
        self._error_message = error_message or f"Value must match pattern: {self._pattern_str}"
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        if not self._pattern.match(value):
            return ValidationResult.failure([self._error_message])
        
        return ValidationResult.success()
    
    @property
    def description(self) -> str:
        return f"Must match regex pattern: {self._pattern_str}"


class FileExtensionValidator(ValidationRule[str]):
    """Validates file extensions."""
    
    def __init__(self, allowed_extensions: List[str], 
                 case_sensitive: bool = False):
        self._allowed_extensions = allowed_extensions
        self._case_sensitive = case_sensitive
        
        if not case_sensitive:
            self._allowed_extensions = [ext.lower() for ext in allowed_extensions]
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        file_path = Path(value)
        extension = file_path.suffix
        
        if not self._case_sensitive:
            extension = extension.lower()
        
        if extension not in self._allowed_extensions:
            return ValidationResult.failure([
                f"File extension '{extension}' not allowed. "
                f"Allowed extensions: {', '.join(self._allowed_extensions)}"
            ])
        
        return ValidationResult.success()
    
    @property
    def description(self) -> str:
        return f"File extension must be one of: {', '.join(self._allowed_extensions)}"


class DirectoryExistsValidator(ValidationRule[str]):
    """Validates that a directory exists."""
    
    def __init__(self, create_if_missing: bool = False):
        self._create_if_missing = create_if_missing
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        dir_path = Path(value)
        
        if not dir_path.exists():
            if self._create_if_missing:
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    return ValidationResult.success(
                        warnings=[f"Created missing directory: {value}"]
                    )
                except OSError as e:
                    return ValidationResult.failure([
                        f"Directory does not exist and could not be created: {e}"
                    ])
            else:
                return ValidationResult.failure([f"Directory does not exist: {value}"])
        
        if not dir_path.is_dir():
            return ValidationResult.failure([f"Path exists but is not a directory: {value}"])
        
        return ValidationResult.success()
    
    @property
    def description(self) -> str:
        suffix = " (will create if missing)" if self._create_if_missing else ""
        return f"Directory must exist{suffix}"


class PathTraversalValidator(ValidationRule[str]):
    """Validates against path traversal attacks."""
    
    def __init__(self, base_path: Optional[str] = None):
        self._base_path = Path(base_path) if base_path else None
    
    def validate(self, value: str, context: ValidationContext) -> ValidationResult:
        if not isinstance(value, str):
            return ValidationResult.failure(["Value must be a string"])
        
        try:
            # Resolve the path to detect path traversal attempts
            resolved_path = Path(value).resolve()
            
            # Check for path traversal patterns
            if ".." in value or value.startswith("/"):
                return ValidationResult.failure([
                    "Path contains potential path traversal sequences"
                ])
            
            # If base path is specified, ensure the resolved path is within it
            if self._base_path:
                base_resolved = self._base_path.resolve()
                try:
                    resolved_path.relative_to(base_resolved)
                except ValueError:
                    return ValidationResult.failure([
                        f"Path escapes base directory: {self._base_path}"
                    ])
            
            return ValidationResult.success()
            
        except (OSError, ValueError) as e:
            return ValidationResult.failure([f"Invalid path: {e}"])
    
    @property
    def description(self) -> str:
        base_msg = f" within {self._base_path}" if self._base_path else ""
        return f"Path must be safe from traversal attacks{base_msg}"