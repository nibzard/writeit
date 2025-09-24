"""Mock implementations for workspace domain services."""

from .mock_workspace_isolation_service import MockWorkspaceIsolationService
from .mock_workspace_template_service import MockWorkspaceTemplateService

__all__ = [
    "MockWorkspaceIsolationService",
    "MockWorkspaceTemplateService",
]
