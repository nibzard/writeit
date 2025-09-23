"""Error handling utilities for command handlers.

This module provides standardized error handling patterns and validation
utilities for all command handlers in the WriteIt application.
"""

import logging
from typing import Dict, List, Optional, Any, Type, Union
from datetime import datetime
from enum import Enum

from ...shared.errors import BaseApplicationError, ValidationError, NotFoundError, ConflictError
from ...shared.events.event_bus import EventBus

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Standardized error handler for command operations."""
    
    @staticmethod
    def log_and_return_error(
        operation: str,
        error: Exception,
        error_type: Type[BaseApplicationError] = None,
        context: Dict[str, Any] = None
    ) -> BaseApplicationError:
        """Log an error and return a standardized error.
        
        Args:
            operation: Description of the operation that failed
            error: The original exception
            error_type: Type of error to return (defaults to BaseApplicationError)
            context: Additional context for logging
            
        Returns:
            Standardized application error
        """
        context = context or {}
        
        # Log the full error with context
        logger.error(
            f"Failed to {operation}: {error}",
            exc_info=True,
            extra={"operation": operation, "context": context}
        )
        
        # Create appropriate error type
        if error_type:
            return error_type(str(error))
        else:
            return BaseApplicationError(f"Failed to {operation}: {str(error)}")
    
    @staticmethod
    def log_and_return_success(
        operation: str,
        result_message: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Log a successful operation and return result context.
        
        Args:
            operation: Description of the operation that succeeded
            result_message: Success message
            context: Additional context
            
        Returns:
            Result context with success information
        """
        context = context or {}
        
        logger.info(
            f"Successfully {operation}",
            extra={"operation": operation, "context": context}
        )
        
        return {
            "success": True,
            "message": result_message,
            "operation": operation,
            "timestamp": datetime.now().isoformat(),
            "context": context
        }


class ValidationErrorBuilder:
    """Builder for creating validation error messages."""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_error(self, field: str, message: str) -> 'ValidationErrorBuilder':
        """Add a validation error.
        
        Args:
            field: Field that failed validation
            message: Error message
            
        Returns:
            Self for method chaining
        """
        self.errors.append(f"{field}: {message}")
        return self
    
    def add_warning(self, field: str, message: str) -> 'ValidationErrorBuilder':
        """Add a validation warning.
        
        Args:
            field: Field that generated warning
            message: Warning message
            
        Returns:
            Self for method chaining
        """
        self.warnings.append(f"{field}: {message}")
        return self
    
    def add_required_error(self, field: str) -> 'ValidationErrorBuilder':
        """Add a required field error.
        
        Args:
            field: Required field that is missing
            
        Returns:
            Self for method chaining
        """
        return self.add_error(field, f"{field} is required")
    
    def add_format_error(self, field: str, expected_format: str) -> 'ValidationErrorBuilder':
        """Add a format validation error.
        
        Args:
            field: Field with format error
            expected_format: Expected format description
            
        Returns:
            Self for method chaining
        """
        return self.add_error(field, f"Invalid format. Expected: {expected_format}")
    
    def add_not_found_error(self, resource_type: str, identifier: str) -> 'ValidationErrorBuilder':
        """Add a not found error.
        
        Args:
            resource_type: Type of resource not found
            identifier: Resource identifier
            
        Returns:
            Self for method chaining
        """
        return self.add_error(resource_type, f"{resource_type} not found: {identifier}")
    
    def add_conflict_error(self, resource_type: str, identifier: str) -> 'ValidationErrorBuilder':
        """Add a conflict error.
        
        Args:
            resource_type: Type of resource with conflict
            identifier: Resource identifier
            
        Returns:
            Self for method chaining
        """
        return self.add_error(resource_type, f"{resource_type} already exists: {identifier}")
    
    def build_errors(self) -> List[str]:
        """Build the list of validation errors.
        
        Returns:
            List of validation errors
        """
        return self.errors.copy()
    
    def build_warnings(self) -> List[str]:
        """Build the list of validation warnings.
        
        Returns:
            List of validation warnings
        """
        return self.warnings.copy()
    
    def has_errors(self) -> bool:
        """Check if there are any validation errors.
        
        Returns:
            True if there are errors
        """
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any validation warnings.
        
        Returns:
            True if there are warnings
        """
        return len(self.warnings) > 0
    
    def build_validation_error(self, message: str = "Validation failed") -> ValidationError:
        """Build a ValidationError from accumulated errors and warnings.
        
        Args:
            message: Overall validation error message
            
        Returns:
            ValidationError with all accumulated errors and warnings
        """
        return ValidationError(
            message=message,
            errors=self.errors.copy(),
            warnings=self.warnings.copy()
        )


class CommandValidator:
    """Standardized validation utilities for commands."""
    
    @staticmethod
    def validate_required_string(value: str, field_name: str) -> List[str]:
        """Validate a required string field.
        
        Args:
            value: String value to validate
            field_name: Name of the field for error messages
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        if not value or not value.strip():
            errors.append(f"{field_name} is required")
        return errors
    
    @staticmethod
    def validate_optional_string(value: Optional[str], field_name: str) -> List[str]:
        """Validate an optional string field.
        
        Args:
            value: Optional string value to validate
            field_name: Name of the field for error messages
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        if value is not None and not value.strip():
            errors.append(f"{field_name} must not be empty if provided")
        return errors
    
    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate that required fields are present and non-empty.
        
        Args:
            data: Dictionary containing field values
            required_fields: List of required field names
            
        Returns:
            List of validation errors
        """
        errors = []
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f"{field} is required")
        return errors
    
    @staticmethod
    def validate_at_least_one_field(data: Dict[str, Any], fields: List[str], operation: str) -> List[str]:
        """Validate that at least one of the specified fields is provided.
        
        Args:
            data: Dictionary containing field values
            fields: List of field names
            operation: Description of the operation for error message
            
        Returns:
            List of validation errors
        """
        errors = []
        if not any(data.get(field) for field in fields):
            field_list = ", ".join(fields)
            errors.append(f"At least one field must be provided for {operation}: {field_list}")
        return errors
    
    @staticmethod
    def validate_file_path(path: Optional[str], field_name: str, must_exist: bool = True) -> List[str]:
        """Validate a file path.
        
        Args:
            path: File path to validate
            field_name: Name of the field for error messages
            must_exist: Whether the file must exist
            
        Returns:
            List of validation errors
        """
        errors = []
        if not path:
            return errors
        
        from pathlib import Path
        path_obj = Path(path)
        
        if must_exist and not path_obj.exists():
            errors.append(f"{field_name} does not exist: {path}")
        elif must_exist and not path_obj.is_file():
            errors.append(f"{field_name} is not a file: {path}")
        
        return errors
    
    @staticmethod
    def validate_directory_path(path: Optional[str], field_name: str, must_exist: bool = True) -> List[str]:
        """Validate a directory path.
        
        Args:
            path: Directory path to validate
            field_name: Name of the field for error messages
            must_exist: Whether the directory must exist
            
        Returns:
            List of validation errors
        """
        errors = []
        if not path:
            return errors
        
        from pathlib import Path
        path_obj = Path(path)
        
        if must_exist and not path_obj.exists():
            errors.append(f"{field_name} does not exist: {path}")
        elif must_exist and not path_obj.is_dir():
            errors.append(f"{field_name} is not a directory: {path}")
        
        return errors
    
    @staticmethod
    def validate_enum_value(value: Any, enum_class: Type[Enum], field_name: str) -> List[str]:
        """Validate that a value is a valid enum member.
        
        Args:
            value: Value to validate
            enum_class: Enum class to validate against
            field_name: Name of the field for error messages
            
        Returns:
            List of validation errors
        """
        errors = []
        try:
            if value is not None:
                enum_class(value)
        except ValueError:
            valid_values = [e.value for e in enum_class]
            errors.append(f"Invalid {field_name}. Must be one of: {', '.join(valid_values)}")
        return errors


class CommandContext:
    """Context information for command execution."""
    
    def __init__(
        self,
        operation: str,
        user_id: Optional[str] = None,
        workspace_name: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize command context.
        
        Args:
            operation: Description of the operation being performed
            user_id: User performing the operation
            workspace_name: Workspace context for the operation
            request_id: Unique request identifier
            metadata: Additional metadata
        """
        self.operation = operation
        self.user_id = user_id
        self.workspace_name = workspace_name
        self.request_id = request_id
        self.metadata = metadata or {}
        self.start_time = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging.
        
        Returns:
            Context as dictionary
        """
        return {
            "operation": self.operation,
            "user_id": self.user_id,
            "workspace_name": self.workspace_name,
            "request_id": self.request_id,
            "metadata": self.metadata,
            "start_time": self.start_time.isoformat()
        }
    
    def get_duration(self) -> float:
        """Get duration of the operation in seconds.
        
        Returns:
            Duration in seconds
        """
        return (datetime.now() - self.start_time).total_seconds()


class EventPublisher:
    """Helper for publishing domain events with consistent metadata."""
    
    @staticmethod
    def add_standard_metadata(
        event_data: Dict[str, Any],
        context: CommandContext,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Add standard metadata to event data.
        
        Args:
            event_data: Base event data
            context: Command context
            additional_metadata: Additional metadata to include
            
        Returns:
            Event data with standard metadata
        """
        metadata = {
            "operation": context.operation,
            "user_id": context.user_id,
            "workspace_name": context.workspace_name,
            "request_id": context.request_id,
            "duration_seconds": context.get_duration()
        }
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        event_data["metadata"] = metadata
        return event_data