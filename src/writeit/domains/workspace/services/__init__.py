"""Workspace domain services.

Service layer for the workspace domain containing business logic
that doesn't belong to individual entities.
"""

from .workspace_management_service import (
    WorkspaceManagementService,
    WorkspaceCreationOptions,
    WorkspaceMigrationPlan,
    WorkspaceBackupInfo,
    WorkspaceValidationError,
    WorkspaceAccessError,
    WorkspaceMigrationError
)
from .workspace_configuration_service import (
    WorkspaceConfigurationService,
    ConfigurationScope,
    ConfigurationValidationIssue,
    ConfigurationMergeConflict,
    ConfigurationSchema,
    ConfigurationValidationError,
    ConfigurationMergeError,
    ConfigurationSchemaError
)
from .workspace_analytics_service import (
    WorkspaceAnalyticsService,
    WorkspaceAnalytics,
    AnalyticsReport,
    UsageMetrics,
    PerformanceMetrics,
    ResourceMetrics,
    HealthDiagnostics,
    BehaviorMetrics,
    AnalyticsScope,
    MetricType,
    HealthStatus
)
from .workspace_isolation_service import (
    WorkspaceIsolationService,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    WorkspaceContext,
    WorkspaceAccessError,
    WorkspaceIsolationError,
    IsolatedWorkspaceOperations
)
from .workspace_template_service import (
    WorkspaceTemplateService,
    TemplateScope,
    TemplateVisibility,
    TemplateResolutionResult,
    TemplateSearchCriteria,
    WorkspaceTemplateError,
    TemplateNotFoundError,
    TemplateConflictError
)

__all__ = [
    # Management Service
    "WorkspaceManagementService",
    "WorkspaceCreationOptions",
    "WorkspaceMigrationPlan", 
    "WorkspaceBackupInfo",
    "WorkspaceValidationError",
    "WorkspaceAccessError",
    "WorkspaceMigrationError",
    
    # Configuration Service
    "WorkspaceConfigurationService",
    "ConfigurationScope",
    "ConfigurationValidationIssue",
    "ConfigurationMergeConflict",
    "ConfigurationSchema",
    "ConfigurationValidationError",
    "ConfigurationMergeError",
    "ConfigurationSchemaError",
    
    # Analytics Service
    "WorkspaceAnalyticsService",
    "WorkspaceAnalytics",
    "AnalyticsReport",
    "UsageMetrics",
    "PerformanceMetrics",
    "ResourceMetrics",
    "HealthDiagnostics",
    "BehaviorMetrics",
    "AnalyticsScope",
    "MetricType",
    "HealthStatus",
    
    # Isolation Service
    "WorkspaceIsolationService",
    "ValidationResult",
    "ValidationIssue", 
    "ValidationSeverity",
    "WorkspaceContext",
    "WorkspaceAccessError",
    "WorkspaceIsolationError",
    "IsolatedWorkspaceOperations",
    
    # Template Service
    "WorkspaceTemplateService",
    "TemplateScope",
    "TemplateVisibility",
    "TemplateResolutionResult",
    "TemplateSearchCriteria",
    "WorkspaceTemplateError",
    "TemplateNotFoundError",
    "TemplateConflictError",
]