"""Application Queries - CQRS Read Operations.

Queries represent read operations that retrieve data without modifying state.
Each query has a corresponding handler that executes the data retrieval logic.
"""

from .pipeline_queries import (
    # Pipeline Template Queries
    GetPipelineTemplateQuery,
    GetPipelineTemplateByNameQuery,
    ListPipelineTemplatesQuery,
    SearchPipelineTemplatesQuery,
    GetPipelineTemplateVersionsQuery,
    ValidatePipelineTemplateQuery,
    
    # Pipeline Execution Queries
    GetPipelineRunQuery,
    ListPipelineRunsQuery,
    GetPipelineRunStatusQuery,
    GetPipelineRunOutputsQuery,
    GetPipelineRunMetricsQuery,
    
    # Pipeline Analytics Queries
    GetPipelineAnalyticsQuery,
    GetPipelineUsageStatsQuery,
    GetPopularPipelinesQuery,
    
    # Step Execution Queries
    GetStepExecutionQuery,
    ListStepExecutionsQuery,
    
    # Query Results
    PipelineTemplateQueryResult,
    PipelineRunQueryResult,
    PipelineAnalyticsQueryResult,
    
    # Query Handlers
    GetPipelineTemplateQueryHandler,
    ListPipelineTemplatesQueryHandler,
    SearchPipelineTemplatesQueryHandler,
    GetPipelineRunQueryHandler,
    ListPipelineRunsQueryHandler,
    GetPipelineAnalyticsQueryHandler,
    
    # Enums
    PipelineStatus,
    TemplateScope,
)

from .workspace_queries import (
    # Workspace Management Queries
    GetWorkspacesQuery,
    GetWorkspaceQuery,
    GetActiveWorkspaceQuery,
    GetWorkspaceConfigQuery,
    GetWorkspaceStatsQuery,
    SearchWorkspacesQuery,
    
    # Workspace Template Queries
    GetWorkspaceTemplatesQuery,
    GetWorkspaceTemplateQuery,
    
    # Workspace Validation Queries
    ValidateWorkspaceNameQuery,
    CheckWorkspaceExistsQuery,
    GetWorkspaceHealthQuery,
    
    # Query Results
    WorkspaceQueryResult,
    WorkspaceTemplateQueryResult,
    
    # Query Handlers
    GetWorkspacesQueryHandler,
    GetWorkspaceQueryHandler,
    GetActiveWorkspaceQueryHandler,
    GetWorkspaceConfigQueryHandler,
    GetWorkspaceStatsQueryHandler,
    SearchWorkspacesQueryHandler,
    ValidateWorkspaceNameQueryHandler,
    CheckWorkspaceExistsQueryHandler,
    GetWorkspaceHealthQueryHandler,
    GetWorkspaceTemplatesQueryHandler,
    GetWorkspaceTemplateQueryHandler,
    
    # Enums
    WorkspaceStatus,
    WorkspaceScope,
)

from .content_queries import (
    # Template Queries
    GetTemplatesQuery,
    GetTemplateQuery,
    GetTemplateByNameQuery,
    SearchTemplatesQuery,
    
    # Generated Content Queries
    GetGeneratedContentQuery,
    ListGeneratedContentQuery,
    SearchGeneratedContentQuery,
    
    # Style Primer Queries
    GetStylePrimersQuery,
    GetStylePrimerQuery,
    
    # Content Analytics Queries
    GetContentAnalyticsQuery,
    GetPopularTemplatesQuery,
    
    # Content Validation Queries
    ValidateTemplateQuery,
    CheckTemplateExistsQuery,
    
    # Query Results
    TemplateQueryResult,
    GeneratedContentQueryResult,
    StylePrimerQueryResult,
    ContentAnalyticsQueryResult,
    
    # Query Handlers
    GetTemplatesQueryHandler,
    GetTemplateQueryHandler,
    GetTemplateByNameQueryHandler,
    SearchTemplatesQueryHandler,
    GetGeneratedContentQueryHandler,
    ListGeneratedContentQueryHandler,
    SearchGeneratedContentQueryHandler,
    GetStylePrimersQueryHandler,
    GetStylePrimerQueryHandler,
    GetContentAnalyticsQueryHandler,
    GetPopularTemplatesQueryHandler,
    ValidateTemplateQueryHandler,
    CheckTemplateExistsQueryHandler,
    
    # Enums
    ContentType,
    TemplateStatus,
    ContentScope,
)

__all__ = [
    # Pipeline Template Queries
    "GetPipelineTemplateQuery",
    "GetPipelineTemplateByNameQuery",
    "ListPipelineTemplatesQuery",
    "SearchPipelineTemplatesQuery",
    "GetPipelineTemplateVersionsQuery",
    "ValidatePipelineTemplateQuery",
    
    # Pipeline Execution Queries
    "GetPipelineRunQuery",
    "ListPipelineRunsQuery",
    "GetPipelineRunStatusQuery",
    "GetPipelineRunOutputsQuery",
    "GetPipelineRunMetricsQuery",
    
    # Pipeline Analytics Queries
    "GetPipelineAnalyticsQuery",
    "GetPipelineUsageStatsQuery",
    "GetPopularPipelinesQuery",
    
    # Step Execution Queries
    "GetStepExecutionQuery",
    "ListStepExecutionsQuery",
    
    # Pipeline Query Results
    "PipelineTemplateQueryResult",
    "PipelineRunQueryResult",
    "PipelineAnalyticsQueryResult",
    
    # Pipeline Query Handlers
    "GetPipelineTemplateQueryHandler",
    "ListPipelineTemplatesQueryHandler",
    "SearchPipelineTemplatesQueryHandler",
    "GetPipelineRunQueryHandler",
    "ListPipelineRunsQueryHandler",
    "GetPipelineAnalyticsQueryHandler",
    
    # Pipeline Enums
    "PipelineStatus",
    "TemplateScope",
    
    # Workspace Management Queries
    "GetWorkspacesQuery",
    "GetWorkspaceQuery",
    "GetActiveWorkspaceQuery",
    "GetWorkspaceConfigQuery",
    "GetWorkspaceStatsQuery",
    "SearchWorkspacesQuery",
    
    # Workspace Template Queries
    "GetWorkspaceTemplatesQuery",
    "GetWorkspaceTemplateQuery",
    
    # Workspace Validation Queries
    "ValidateWorkspaceNameQuery",
    "CheckWorkspaceExistsQuery",
    "GetWorkspaceHealthQuery",
    
    # Workspace Query Results
    "WorkspaceQueryResult",
    "WorkspaceTemplateQueryResult",
    
    # Workspace Query Handlers
    "GetWorkspacesQueryHandler",
    "GetWorkspaceQueryHandler",
    "GetActiveWorkspaceQueryHandler",
    "GetWorkspaceConfigQueryHandler",
    "GetWorkspaceStatsQueryHandler",
    "SearchWorkspacesQueryHandler",
    "ValidateWorkspaceNameQueryHandler",
    "CheckWorkspaceExistsQueryHandler",
    "GetWorkspaceHealthQueryHandler",
    "GetWorkspaceTemplatesQueryHandler",
    "GetWorkspaceTemplateQueryHandler",
    
    # Workspace Enums
    "WorkspaceStatus",
    "WorkspaceScope",
    
    # Template Queries
    "GetTemplatesQuery",
    "GetTemplateQuery",
    "GetTemplateByNameQuery",
    "SearchTemplatesQuery",
    
    # Generated Content Queries
    "GetGeneratedContentQuery",
    "ListGeneratedContentQuery",
    "SearchGeneratedContentQuery",
    
    # Style Primer Queries
    "GetStylePrimersQuery",
    "GetStylePrimerQuery",
    
    # Content Analytics Queries
    "GetContentAnalyticsQuery",
    "GetPopularTemplatesQuery",
    
    # Content Validation Queries
    "ValidateTemplateQuery",
    "CheckTemplateExistsQuery",
    
    # Content Query Results
    "TemplateQueryResult",
    "GeneratedContentQueryResult",
    "StylePrimerQueryResult",
    "ContentAnalyticsQueryResult",
    
    # Content Query Handlers
    "GetTemplatesQueryHandler",
    "GetTemplateQueryHandler",
    "GetTemplateByNameQueryHandler",
    "SearchTemplatesQueryHandler",
    "GetGeneratedContentQueryHandler",
    "ListGeneratedContentQueryHandler",
    "SearchGeneratedContentQueryHandler",
    "GetStylePrimersQueryHandler",
    "GetStylePrimerQueryHandler",
    "GetContentAnalyticsQueryHandler",
    "GetPopularTemplatesQueryHandler",
    "ValidateTemplateQueryHandler",
    "CheckTemplateExistsQueryHandler",
    
    # Content Enums
    "ContentType",
    "TemplateStatus",
    "ContentScope",
]