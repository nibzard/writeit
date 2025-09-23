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
    
    # Query Results
    "PipelineTemplateQueryResult",
    "PipelineRunQueryResult",
    "PipelineAnalyticsQueryResult",
    
    # Query Handlers
    "GetPipelineTemplateQueryHandler",
    "ListPipelineTemplatesQueryHandler",
    "SearchPipelineTemplatesQueryHandler",
    "GetPipelineRunQueryHandler",
    "ListPipelineRunsQueryHandler",
    "GetPipelineAnalyticsQueryHandler",
    
    # Enums
    "PipelineStatus",
    "TemplateScope",
]