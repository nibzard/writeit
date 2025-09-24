"""Workspace domain errors."""

from ...shared.errors import DomainError


class WorkspaceError(DomainError):
    """Base exception for workspace domain errors."""
    pass


class WorkspaceNotFoundError(WorkspaceError):
    """Raised when a workspace is not found."""
    
    def __init__(self, workspace_name: str):
        self.workspace_name = workspace_name
        super().__init__(f"Workspace '{workspace_name}' not found")


class WorkspaceAlreadyExistsError(WorkspaceError):
    """Raised when trying to create a workspace that already exists."""
    
    def __init__(self, workspace_name: str):
        self.workspace_name = workspace_name
        super().__init__(f"Workspace '{workspace_name}' already exists")


class WorkspaceConfigurationError(WorkspaceError):
    """Raised when workspace configuration is invalid."""
    pass


class WorkspaceAccessDeniedError(WorkspaceError):
    """Raised when access to workspace is denied."""
    
    def __init__(self, workspace_name: str, reason: str = None):
        self.workspace_name = workspace_name
        self.reason = reason
        message = f"Access denied to workspace '{workspace_name}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class WorkspaceInitializationError(WorkspaceError):
    """Raised when workspace initialization fails."""
    
    def __init__(self, workspace_name: str, reason: str = None):
        self.workspace_name = workspace_name
        self.reason = reason
        message = f"Failed to initialize workspace '{workspace_name}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class WorkspaceCorruptionError(WorkspaceError):
    """Raised when workspace data is corrupted."""
    
    def __init__(self, workspace_name: str, details: str = None):
        self.workspace_name = workspace_name
        self.details = details
        message = f"Workspace '{workspace_name}' data is corrupted"
        if details:
            message += f": {details}"
        super().__init__(message)


__all__ = [
    "WorkspaceError",
    "WorkspaceNotFoundError", 
    "WorkspaceAlreadyExistsError",
    "WorkspaceConfigurationError",
    "WorkspaceAccessDeniedError",
    "WorkspaceInitializationError",
    "WorkspaceCorruptionError",
]