"""Infrastructure-specific exceptions.

Provides concrete exception types for infrastructure layer operations
including storage, serialization, and connection errors.
"""

from typing import Optional, Any

from ...shared.repository import RepositoryError, UnitOfWorkError


class InfrastructureError(Exception):
    """Base exception for infrastructure layer errors."""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        super().__init__(message)
        self.cause = cause


class StorageError(InfrastructureError, RepositoryError):
    """Error in storage operations."""
    
    def __init__(self, message: str, operation: str, entity_type: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.operation = operation
        self.entity_type = entity_type


class ConnectionError(InfrastructureError):
    """Error in database connection operations."""
    
    def __init__(self, message: str, database: str, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.database = database


class SerializationError(InfrastructureError):
    """Error in entity serialization/deserialization."""
    
    def __init__(self, message: str, entity_type: str, operation: str, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.entity_type = entity_type
        self.operation = operation


class TransactionError(InfrastructureError, UnitOfWorkError):
    """Error in transaction management."""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.transaction_id = transaction_id


class ValidationError(InfrastructureError):
    """Error in data validation."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.field = field
        self.value = value


class ConfigurationError(InfrastructureError):
    """Error in infrastructure configuration."""
    
    def __init__(self, message: str, component: str, setting: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.component = component
        self.setting = setting


class CacheError(InfrastructureError):
    """Error in cache operations."""
    
    def __init__(self, message: str, cache_key: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.cache_key = cache_key


class IndexError(InfrastructureError):
    """Error in index operations."""
    
    def __init__(self, message: str, index_name: str, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.index_name = index_name


class MigrationError(InfrastructureError):
    """Error in database migration operations."""
    
    def __init__(self, message: str, version: Optional[str] = None, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.version = version


class CapacityError(InfrastructureError):
    """Error due to capacity limits (storage, memory, etc.)."""
    
    def __init__(self, message: str, resource: str, limit: Optional[Any] = None, cause: Optional[Exception] = None):
        super().__init__(message, cause)
        self.resource = resource
        self.limit = limit


def wrap_storage_exception(operation: str, entity_type: str = None) -> callable:
    """Decorator to wrap storage operations and convert exceptions.
    
    Args:
        operation: Name of the operation being performed
        entity_type: Type of entity being operated on
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, (StorageError, RepositoryError)):
                    raise
                raise StorageError(
                    f"Storage operation '{operation}' failed: {e}",
                    operation=operation,
                    entity_type=entity_type,
                    cause=e
                )
        return wrapper
    return decorator


def wrap_async_storage_exception(operation: str, entity_type: str = None) -> callable:
    """Decorator to wrap async storage operations and convert exceptions.
    
    Args:
        operation: Name of the operation being performed
        entity_type: Type of entity being operated on
        
    Returns:
        Decorator function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if isinstance(e, (StorageError, RepositoryError)):
                    raise
                raise StorageError(
                    f"Storage operation '{operation}' failed: {e}",
                    operation=operation,
                    entity_type=entity_type,
                    cause=e
                )
        return wrapper
    return decorator


def validate_required_field(value: Any, field_name: str, entity_type: str = None) -> None:
    """Validate that a required field has a value.
    
    Args:
        value: Field value to validate
        field_name: Name of the field
        entity_type: Type of entity being validated
        
    Raises:
        ValidationError: If field is empty or None
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        entity_info = f" for {entity_type}" if entity_type else ""
        raise ValidationError(
            f"Required field '{field_name}'{entity_info} cannot be empty",
            field=field_name,
            value=value
        )


def validate_field_type(value: Any, expected_type: type, field_name: str, entity_type: str = None) -> None:
    """Validate that a field has the expected type.
    
    Args:
        value: Field value to validate
        expected_type: Expected type for the field
        field_name: Name of the field
        entity_type: Type of entity being validated
        
    Raises:
        ValidationError: If field has wrong type
    """
    if not isinstance(value, expected_type):
        entity_info = f" for {entity_type}" if entity_type else ""
        raise ValidationError(
            f"Field '{field_name}'{entity_info} must be of type {expected_type.__name__}, got {type(value).__name__}",
            field=field_name,
            value=value
        )


def validate_field_range(value: Any, min_val: Any = None, max_val: Any = None, field_name: str = None, entity_type: str = None) -> None:
    """Validate that a field value is within an acceptable range.
    
    Args:
        value: Field value to validate
        min_val: Minimum acceptable value (inclusive)
        max_val: Maximum acceptable value (inclusive)
        field_name: Name of the field
        entity_type: Type of entity being validated
        
    Raises:
        ValidationError: If field is outside the acceptable range
    """
    if min_val is not None and value < min_val:
        entity_info = f" for {entity_type}" if entity_type else ""
        field_info = f" '{field_name}'" if field_name else ""
        raise ValidationError(
            f"Field{field_info}{entity_info} value {value} is below minimum {min_val}",
            field=field_name,
            value=value
        )
    
    if max_val is not None and value > max_val:
        entity_info = f" for {entity_type}" if entity_type else ""
        field_info = f" '{field_name}'" if field_name else ""
        raise ValidationError(
            f"Field{field_info}{entity_info} value {value} is above maximum {max_val}",
            field=field_name,
            value=value
        )