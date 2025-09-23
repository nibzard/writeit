"""Query Handlers Module.

Concrete implementations of all CQRS query handlers for the WriteIt application.
"""

from .pipeline_handlers import (
    ConcreteGetPipelineTemplateQueryHandler,
    ConcreteListPipelineTemplatesQueryHandler,
    ConcreteSearchPipelineTemplatesQueryHandler,
    ConcreteGetPipelineRunQueryHandler,
    ConcreteListPipelineRunsQueryHandler,
    ConcreteGetPipelineAnalyticsQueryHandler,
)

from .workspace_handlers import (
    ConcreteGetWorkspacesQueryHandler,
    ConcreteGetWorkspaceQueryHandler,
    ConcreteGetActiveWorkspaceQueryHandler,
    ConcreteGetWorkspaceConfigQueryHandler,
    ConcreteGetWorkspaceStatsQueryHandler,
    ConcreteSearchWorkspacesQueryHandler,
    ConcreteValidateWorkspaceNameQueryHandler,
    ConcreteCheckWorkspaceExistsQueryHandler,
    ConcreteGetWorkspaceHealthQueryHandler,
    ConcreteGetWorkspaceTemplatesQueryHandler,
    ConcreteGetWorkspaceTemplateQueryHandler,
)

from .content_handlers import (
    ConcreteGetTemplatesQueryHandler,
    ConcreteGetTemplateQueryHandler,
    ConcreteGetTemplateByNameQueryHandler,
    ConcreteSearchTemplatesQueryHandler,
    ConcreteGetGeneratedContentQueryHandler,
    ConcreteListGeneratedContentQueryHandler,
    ConcreteSearchGeneratedContentQueryHandler,
    ConcreteGetStylePrimersQueryHandler,
    ConcreteGetStylePrimerQueryHandler,
    ConcreteGetContentAnalyticsQueryHandler,
    ConcreteGetPopularTemplatesQueryHandler,
    ConcreteValidateTemplateQueryHandler,
    ConcreteCheckTemplateExistsQueryHandler,
)

__all__ = [
    # Pipeline Query Handlers
    "ConcreteGetPipelineTemplateQueryHandler",
    "ConcreteListPipelineTemplatesQueryHandler",
    "ConcreteSearchPipelineTemplatesQueryHandler",
    "ConcreteGetPipelineRunQueryHandler",
    "ConcreteListPipelineRunsQueryHandler",
    "ConcreteGetPipelineAnalyticsQueryHandler",
    
    # Workspace Query Handlers
    "ConcreteGetWorkspacesQueryHandler",
    "ConcreteGetWorkspaceQueryHandler",
    "ConcreteGetActiveWorkspaceQueryHandler",
    "ConcreteGetWorkspaceConfigQueryHandler",
    "ConcreteGetWorkspaceStatsQueryHandler",
    "ConcreteSearchWorkspacesQueryHandler",
    "ConcreteValidateWorkspaceNameQueryHandler",
    "ConcreteCheckWorkspaceExistsQueryHandler",
    "ConcreteGetWorkspaceHealthQueryHandler",
    "ConcreteGetWorkspaceTemplatesQueryHandler",
    "ConcreteGetWorkspaceTemplateQueryHandler",
    
    # Content Query Handlers
    "ConcreteGetTemplatesQueryHandler",
    "ConcreteGetTemplateQueryHandler",
    "ConcreteGetTemplateByNameQueryHandler",
    "ConcreteSearchTemplatesQueryHandler",
    "ConcreteGetGeneratedContentQueryHandler",
    "ConcreteListGeneratedContentQueryHandler",
    "ConcreteSearchGeneratedContentQueryHandler",
    "ConcreteGetStylePrimersQueryHandler",
    "ConcreteGetStylePrimerQueryHandler",
    "ConcreteGetContentAnalyticsQueryHandler",
    "ConcreteGetPopularTemplatesQueryHandler",
    "ConcreteValidateTemplateQueryHandler",
    "ConcreteCheckTemplateExistsQueryHandler",
]