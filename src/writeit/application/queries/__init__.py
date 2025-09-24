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

from .execution_queries import (
    # LLM Provider Queries
    GetLLMProvidersQuery,
    GetLLMProviderQuery,
    GetLLMProviderHealthQuery,
    SearchLLMProvidersQuery,
    
    # Token Usage Queries
    GetTokenUsageQuery,
    ListTokenUsageQuery,
    GetTokenAnalyticsQuery,
    GetTopTokenConsumersQuery,
    
    # Cache Queries
    GetCacheStatsQuery,
    GetCacheEntryQuery,
    SearchCacheEntriesQuery,
    
    # Execution Context Queries
    GetExecutionContextQuery,
    ListExecutionContextsQuery,
    GetActiveExecutionContextsQuery,
    
    # LLM Request History Queries
    GetLLMRequestHistoryQuery,
    GetLLMRequestPerformanceQuery,
    
    # Query Handlers
    GetLLMProvidersQueryHandler,
    GetLLMProviderQueryHandler,
    GetLLMProviderHealthQueryHandler,
    SearchLLMProvidersQueryHandler,
    GetTokenUsageQueryHandler,
    ListTokenUsageQueryHandler,
    GetTokenAnalyticsQueryHandler,
    GetTopTokenConsumersQueryHandler,
    GetCacheStatsQueryHandler,
    GetCacheEntryQueryHandler,
    SearchCacheEntriesQueryHandler,
    GetExecutionContextQueryHandler,
    ListExecutionContextsQueryHandler,
    GetActiveExecutionContextsQueryHandler,
    GetLLMRequestHistoryQueryHandler,
    GetLLMRequestPerformanceQueryHandler,
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
    
    # LLM Provider Queries
    "GetLLMProvidersQuery",
    "GetLLMProviderQuery",
    "GetLLMProviderHealthQuery",
    "SearchLLMProvidersQuery",
    
    # Token Usage Queries
    "GetTokenUsageQuery",
    "ListTokenUsageQuery",
    "GetTokenAnalyticsQuery",
    "GetTopTokenConsumersQuery",
    
    # Cache Queries
    "GetCacheStatsQuery",
    "GetCacheEntryQuery",
    "SearchCacheEntriesQuery",
    
    # Execution Context Queries
    "GetExecutionContextQuery",
    "ListExecutionContextsQuery",
    "GetActiveExecutionContextsQuery",
    
    # LLM Request History Queries
    "GetLLMRequestHistoryQuery",
    "GetLLMRequestPerformanceQuery",
    
    # Execution Query Handlers
    "GetLLMProvidersQueryHandler",
    "GetLLMProviderQueryHandler",
    "GetLLMProviderHealthQueryHandler",
    "SearchLLMProvidersQueryHandler",
    "GetTokenUsageQueryHandler",
    "ListTokenUsageQueryHandler",
    "GetTokenAnalyticsQueryHandler",
    "GetTopTokenConsumersQueryHandler",
    "GetCacheStatsQueryHandler",
    "GetCacheEntryQueryHandler",
    "SearchCacheEntriesQueryHandler",
    "GetExecutionContextQueryHandler",
    "ListExecutionContextsQueryHandler",
    "GetActiveExecutionContextsQueryHandler",
    "GetLLMRequestHistoryQueryHandler",
    "GetLLMRequestPerformanceQueryHandler",
]