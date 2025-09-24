"""Mock implementations for workspace domain repositories."""

from .mock_workspace_repository import MockWorkspaceRepository
from .mock_workspace_config_repository import MockWorkspaceConfigRepository

__all__ = [
    "MockWorkspaceRepository",
    "MockWorkspaceConfigRepository",
]