"""Pipeline domain queries.

CQRS Query classes for read operations on pipeline entities.
Provides structured queries for templates, runs, and execution history.
"""

from .pipeline_queries import (
    GetPipelineTemplatesQuery,
    GetPipelineTemplatesResult,
    GetPipelineTemplateQuery,
    GetPipelineTemplateResult,
    GetPipelineRunQuery,
    GetPipelineRunResult,
    GetPipelineRunsQuery,
    GetPipelineRunsResult,
    SearchPipelineTemplatesQuery,
    SearchPipelineTemplatesResult,
    GetPipelineHistoryQuery,
    GetPipelineHistoryResult,
    GetPipelineMetricsQuery,
    GetPipelineMetricsResult,
    GetStepExecutionsQuery,
    GetStepExecutionsResult,
)

from .pipeline_query_handlers import (
    GetPipelineTemplatesHandler,
    GetPipelineTemplateHandler,
    GetPipelineRunHandler,
    GetPipelineRunsHandler,
    SearchPipelineTemplatesHandler,
    GetPipelineHistoryHandler,
    GetPipelineMetricsHandler,
    GetStepExecutionsHandler,
)

__all__ = [
    # Query classes
    "GetPipelineTemplatesQuery",
    "GetPipelineTemplatesResult",
    "GetPipelineTemplateQuery", 
    "GetPipelineTemplateResult",
    "GetPipelineRunQuery",
    "GetPipelineRunResult",
    "GetPipelineRunsQuery",
    "GetPipelineRunsResult",
    "SearchPipelineTemplatesQuery",
    "SearchPipelineTemplatesResult",
    "GetPipelineHistoryQuery",
    "GetPipelineHistoryResult",
    "GetPipelineMetricsQuery",
    "GetPipelineMetricsResult",
    "GetStepExecutionsQuery",
    "GetStepExecutionsResult",
    
    # Query handlers
    "GetPipelineTemplatesHandler",
    "GetPipelineTemplateHandler",
    "GetPipelineRunHandler",
    "GetPipelineRunsHandler",
    "SearchPipelineTemplatesHandler",
    "GetPipelineHistoryHandler",
    "GetPipelineMetricsHandler", 
    "GetStepExecutionsHandler",
]