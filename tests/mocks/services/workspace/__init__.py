"""Mock implementations for workspace domain services."""

from .mock_workspace_isolation_service import MockWorkspaceIsolationService
from .mock_workspace_template_service import MockWorkspaceTemplateService
from .mock_workspace_management_service import MockWorkspaceManagementService
from .mock_workspace_configuration_service import MockWorkspaceConfigurationService
from .mock_workspace_analytics_service import MockWorkspaceAnalyticsService

__all__ = [
    "MockWorkspaceIsolationService",
    "MockWorkspaceTemplateService",
    "MockWorkspaceManagementService",
    "MockWorkspaceConfigurationService",
    "MockWorkspaceAnalyticsService",
]
