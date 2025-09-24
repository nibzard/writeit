"""Pipeline CQRS Queries.

Queries for read operations related to pipeline templates,
executions, and analytics.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from ...shared.query import Query, QueryHandler, QueryResult, ListQuery, GetByIdQuery, SearchQuery
from ...domains.pipeline.value_objects import PipelineId, StepId, PipelineName
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.pipeline.entities import PipelineTemplate, PipelineRun


class PipelineStatus(str, Enum):
    """Pipeline execution status for filtering."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class TemplateScope(str, Enum):
    """Template scope for filtering."""
    WORKSPACE = "workspace"
    GLOBAL = "global"
    ALL = "all"


# Pipeline Template Queries

@dataclass(frozen=True)
class GetPipelineTemplateQuery(GetByIdQuery):
    """Query to get a pipeline template by ID."""
    
    pipeline_id: PipelineId = field(default=None)
    workspace_name: Optional[str] = None
    include_steps: bool = True
    include_inputs: bool = True
    include_metadata: bool = True
    
    def __post_init__(self):
        object.__setattr__(self, 'entity_id', str(self.pipeline_id))
        super().__post_init__()


@dataclass(frozen=True)
class GetPipelineTemplateByNameQuery(Query):
    """Query to get a pipeline template by name."""
    
    pipeline_name: str = ""
    workspace_name: Optional[str] = None
    scope: TemplateScope = TemplateScope.WORKSPACE


@dataclass(frozen=True)
class ListPipelineTemplatesQuery(ListQuery):
    """Query to list pipeline templates with filtering and pagination."""
    
    workspace_name: Optional[str] = None
    scope: TemplateScope = TemplateScope.WORKSPACE
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    author: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    
    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class SearchPipelineTemplatesQuery(SearchQuery):
    """Query to search pipeline templates by text."""
    
    workspace_name: Optional[str] = None
    scope: TemplateScope = TemplateScope.WORKSPACE
    search_fields: List[str] = field(default_factory=list)
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.search_fields:
            object.__setattr__(self, 'search_fields', ['name', 'description', 'tags'])
        if not self.tags:
            object.__setattr__(self, 'tags', [])
        super().__post_init__()


@dataclass(frozen=True)
class GetPipelineTemplateVersionsQuery(Query):
    """Query to get all versions of a pipeline template."""
    
    pipeline_name: str = ""
    workspace_name: Optional[str] = None
    include_deprecated: bool = False


@dataclass(frozen=True)
class ValidatePipelineTemplateQuery(Query):
    """Query to validate a pipeline template."""
    
    pipeline_id: Optional[PipelineId] = None
    template_content: Optional[str] = None
    validation_level: str = "strict"


# Pipeline Execution Queries

@dataclass(frozen=True)
class GetPipelineRunQuery(GetByIdQuery):
    """Query to get a pipeline run by ID."""
    
    run_id: str = ""
    include_steps: bool = True
    include_outputs: bool = True
    include_metrics: bool = True
    
    def __post_init__(self):
        object.__setattr__(self, 'entity_id', self.run_id)
        super().__post_init__()


@dataclass(frozen=True)
class ListPipelineRunsQuery(ListQuery):
    """Query to list pipeline runs with filtering and pagination."""
    
    workspace_name: Optional[str] = None
    pipeline_name: Optional[str] = None
    status: Optional[PipelineStatus] = None
    started_after: Optional[datetime] = None
    started_before: Optional[datetime] = None
    completed_after: Optional[datetime] = None
    completed_before: Optional[datetime] = None
    user_id: Optional[str] = None


@dataclass(frozen=True)
class GetPipelineRunStatusQuery(Query):
    """Query to get current status of a pipeline run."""
    
    run_id: str = ""
    include_progress: bool = True
    include_current_step: bool = True
    include_step_outputs: bool = False


@dataclass(frozen=True)
class GetPipelineRunOutputsQuery(Query):
    """Query to get outputs from a pipeline run."""
    
    run_id: str = ""
    step_id: Optional[StepId] = field(default=None)  # Get outputs for specific step
    output_format: str = "json"


@dataclass(frozen=True)
class GetPipelineRunMetricsQuery(Query):
    """Query to get metrics for a pipeline run."""
    
    run_id: str = ""
    include_step_metrics: bool = True
    include_token_usage: bool = True
    include_timing: bool = True


# Pipeline Analytics Queries

@dataclass(frozen=True)
class GetPipelineAnalyticsQuery(Query):
    """Query to get analytics for pipeline usage."""
    
    workspace_name: Optional[str] = None
    pipeline_name: Optional[str] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    group_by: str = "day"  # hour, day, week, month
    
    def __post_init__(self):
        super().__post_init__()
        
        if self.group_by not in ("hour", "day", "week", "month"):
            raise ValueError(f"Invalid group_by value: {self.group_by}")


@dataclass(frozen=True)
class GetPipelineUsageStatsQuery(Query):
    """Query to get usage statistics for pipelines."""
    
    workspace_name: Optional[str] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    include_success_rate: bool = True
    include_execution_time: bool = True
    include_token_usage: bool = True


@dataclass(frozen=True)
class GetPopularPipelinesQuery(Query):
    """Query to get most popular pipelines."""
    
    workspace_name: Optional[str] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    limit: int = 10
    metric: str = "execution_count"  # execution_count, success_rate, avg_duration
    
    def __post_init__(self):
        super().__post_init__()
        
        if self.limit < 1 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        
        if self.metric not in ("execution_count", "success_rate", "avg_duration"):
            raise ValueError(f"Invalid metric: {self.metric}")


# Step Execution Queries

@dataclass(frozen=True)
class GetStepExecutionQuery(Query):
    """Query to get step execution details."""
    
    run_id: str = ""
    step_id: Optional[StepId] = field(default=None)
    include_inputs: bool = True
    include_outputs: bool = True
    include_metrics: bool = True


@dataclass(frozen=True)
class ListStepExecutionsQuery(ListQuery):
    """Query to list step executions for a pipeline run."""
    
    run_id: str = ""
    status: Optional[str] = None
    step_type: Optional[str] = None


# Query Results

@dataclass(frozen=True)
class PipelineTemplateQueryResult(QueryResult):
    """Result for pipeline template queries."""
    
    templates: List[PipelineTemplate] = field(default_factory=list)
    template: Optional[PipelineTemplate] = None
    validation_errors: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class PipelineRunQueryResult(QueryResult):
    """Result for pipeline run queries."""
    
    runs: List[PipelineRun] = field(default_factory=list)
    run: Optional[PipelineRun] = None
    status: Optional[str] = None
    progress: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        super().__post_init__()


@dataclass(frozen=True)
class PipelineAnalyticsQueryResult(QueryResult):
    """Result for pipeline analytics queries."""
    
    analytics: Dict[str, Any] = field(default_factory=dict)
    usage_stats: Optional[Dict[str, Any]] = None
    popular_pipelines: List[Dict[str, Any]] = field(default_factory=list)
    time_series: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()


# Query Handler Interfaces

class PipelineTemplateQueryHandler(QueryHandler[GetPipelineTemplateQuery, PipelineTemplateQueryResult], ABC):
    """Base interface for pipeline template query handlers."""
    pass


class ListPipelineTemplatesQueryHandler(QueryHandler[ListPipelineTemplatesQuery, PipelineTemplateQueryResult], ABC):
    """Base interface for listing pipeline templates query handlers."""
    pass


class SearchPipelineTemplatesQueryHandler(QueryHandler[SearchPipelineTemplatesQuery, PipelineTemplateQueryResult], ABC):
    """Base interface for searching pipeline templates query handlers."""
    pass


class PipelineRunQueryHandler(QueryHandler[GetPipelineRunQuery, PipelineRunQueryResult], ABC):
    """Base interface for pipeline run query handlers."""
    pass


class ListPipelineRunsQueryHandler(QueryHandler[ListPipelineRunsQuery, PipelineRunQueryResult], ABC):
    """Base interface for listing pipeline runs query handlers."""
    pass


class PipelineAnalyticsQueryHandler(QueryHandler[GetPipelineAnalyticsQuery, PipelineAnalyticsQueryResult], ABC):
    """Base interface for pipeline analytics query handlers."""
    pass


# Specific Query Handlers

class GetPipelineTemplateQueryHandler(PipelineTemplateQueryHandler):
    """Handler for getting pipeline template by ID."""
    
    @abstractmethod
    async def handle(self, query: GetPipelineTemplateQuery) -> PipelineTemplateQueryResult:
        """Handle get pipeline template query."""
        pass


class ListPipelineTemplatesQueryHandler(ListPipelineTemplatesQueryHandler):
    """Handler for listing pipeline templates."""
    
    @abstractmethod
    async def handle(self, query: ListPipelineTemplatesQuery) -> PipelineTemplateQueryResult:
        """Handle list pipeline templates query."""
        pass


class SearchPipelineTemplatesQueryHandler(SearchPipelineTemplatesQueryHandler):
    """Handler for searching pipeline templates."""
    
    @abstractmethod
    async def handle(self, query: SearchPipelineTemplatesQuery) -> PipelineTemplateQueryResult:
        """Handle search pipeline templates query."""
        pass


class GetPipelineRunQueryHandler(PipelineRunQueryHandler):
    """Handler for getting pipeline run by ID."""
    
    @abstractmethod
    async def handle(self, query: GetPipelineRunQuery) -> PipelineRunQueryResult:
        """Handle get pipeline run query."""
        pass


class ListPipelineRunsQueryHandler(ListPipelineRunsQueryHandler):
    """Handler for listing pipeline runs."""
    
    @abstractmethod
    async def handle(self, query: ListPipelineRunsQuery) -> PipelineRunQueryResult:
        """Handle list pipeline runs query."""
        pass


class GetPipelineAnalyticsQueryHandler(PipelineAnalyticsQueryHandler):
    """Handler for getting pipeline analytics."""
    
    @abstractmethod
    async def handle(self, query: GetPipelineAnalyticsQuery) -> PipelineAnalyticsQueryResult:
        """Handle get pipeline analytics query."""
        pass