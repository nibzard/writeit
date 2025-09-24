"""Storage domain errors."""

from ...shared.errors import DomainError


class StorageError(DomainError):
    """Base exception for storage domain errors."""
    pass


class DatabaseConnectionError(StorageError):
    """Raised when database connection fails."""
    
    def __init__(self, database_path: str, reason: str = None):
        self.database_path = database_path
        self.reason = reason
        message = f"Database connection failed for '{database_path}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class DatabaseCorruptionError(StorageError):
    """Raised when database is corrupted."""
    
    def __init__(self, database_path: str, details: str = None):
        self.database_path = database_path
        self.details = details
        message = f"Database '{database_path}' is corrupted"
        if details:
            message += f": {details}"
        super().__init__(message)


class DatabaseLockedError(StorageError):
    """Raised when database is locked by another process."""
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        super().__init__(f"Database '{database_path}' is locked by another process")


class DatabaseSpaceError(StorageError):
    """Raised when database space is exhausted."""
    
    def __init__(self, database_path: str, required_size: int, available_size: int):
        self.database_path = database_path
        self.required_size = required_size
        self.available_size = available_size
        super().__init__(
            f"Database '{database_path}' space exhausted: "
            f"required {required_size} bytes, available {available_size} bytes"
        )


class TransactionError(StorageError):
    """Raised when transaction operation fails."""
    
    def __init__(self, operation: str, reason: str = None):
        self.operation = operation
        self.reason = reason
        message = f"Transaction {operation} failed"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class DataIntegrityError(StorageError):
    """Raised when data integrity is compromised."""
    
    def __init__(self, entity_type: str, entity_id: str, details: str = None):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.details = details
        message = f"Data integrity error for {entity_type} '{entity_id}'"
        if details:
            message += f": {details}"
        super().__init__(message)


class SerializationError(StorageError):
    """Raised when data serialization/deserialization fails."""
    
    def __init__(self, data_type: str, reason: str = None):
        self.data_type = data_type
        self.reason = reason
        message = f"Serialization error for type '{data_type}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class FileSystemError(StorageError):
    """Raised when file system operation fails."""
    
    def __init__(self, file_path: str, operation: str, reason: str = None):
        self.file_path = file_path
        self.operation = operation
        self.reason = reason
        message = f"File system {operation} failed for '{file_path}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class AccessDeniedError(StorageError):
    """Raised when access to storage is denied."""
    
    def __init__(self, resource_path: str, operation: str):
        self.resource_path = resource_path
        self.operation = operation
        super().__init__(f"Access denied for {operation} on '{resource_path}'")


__all__ = [
    "StorageError",
    "DatabaseConnectionError",
    "DatabaseCorruptionError",
    "DatabaseLockedError", 
    "DatabaseSpaceError",
    "TransactionError",
    "DataIntegrityError",
    "SerializationError",
    "FileSystemError",
    "AccessDeniedError",
]