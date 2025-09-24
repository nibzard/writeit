"""Storage domain services.

Provides services for file system operations, storage management,
and workspace-aware data persistence.
"""

from .storage_management_service import (
    StorageManagementService,
    StorageManagerInterface,
    StorageOperation,
    StorageError,
    StoragePermissionError,
    StorageSpaceError,
    StorageConcurrencyError,
    StorageOperationResult,
    StorageInfo,
)

__all__ = [
    "StorageManagementService",
    "StorageManagerInterface", 
    "StorageOperation",
    "StorageError",
    "StoragePermissionError",
    "StorageSpaceError",
    "StorageConcurrencyError",
    "StorageOperationResult",
    "StorageInfo",
]