"""Pipeline domain query classes.

CQRS Query definitions for pipeline read operations.
Provides structured queries for templates, runs, executions, and analytics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from ...shared.query import (
    Query,
    QueryResult,
    ListQuery,
    GetByIdQuery,
    SearchQuery,
    PaginationInfo
)
from ..value_objects.pipeline_id import PipelineId
from ..value_objects.step_id import StepId
from ..value_objects.execution_status import ExecutionStatus, PipelineExecutionStatus
from ..entities.pipeline_template import PipelineTemplate
from ..entities.pipeline_run import PipelineRun
from ..entities.pipeline_step import StepExecution


class TemplateSortField(Enum):
    """Available fields for sorting templates."""
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    USAGE_COUNT = "usage_count"
    CATEGORY = "category"
    COMPLEXITY = "complexity"


class RunSortField(Enum):
    """Available fields for sorting runs."""
    CREATED_AT = "created_at"
    STARTED_AT = "started_at"
    COMPLETED_AT = "completed_at"
    DURATION = "duration"
    STATUS = "status"
    PIPELINE_NAME = "pipeline_name"
    TOTAL_TOKENS = "total_tokens"


class ExecutionSortField(Enum):
    """Available fields for sorting step executions."""
    STARTED_AT = "started_at"
    COMPLETED_AT = "completed_at"
    DURATION = "duration"
    STATUS = "status"
    STEP_NAME = "step_name"
    TOKENS_USED = "tokens_used"


# Template Queries

@dataclass(frozen=True)
class GetPipelineTemplatesQuery(ListQuery):
    """Query to list pipeline templates with filtering and pagination.
    
    Supports filtering by workspace, tags, category, author, and search terms.
    Results can be sorted by various fields and paginated.
    """
    
    workspace_name: Optional[str] = None
    include_global: bool = True
    tags: List[str] = field(default_factory=list)
    category: Optional[str] = None
    author: Optional[str] = None
    complexity_level: Optional[str] = None
    sort_by: TemplateSortField = TemplateSortField.NAME
    
    def __post_init__(self):
        super().__post_init__()
        
        # Convert string sort_by to enum if needed
        if isinstance(self.sort_by, str):
            object.__setattr__(self, 'sort_by', TemplateSortField(self.sort_by))


@dataclass(frozen=True)
class GetPipelineTemplatesResult(QueryResult):
    """Result for pipeline templates list query."""
    
    templates: List[PipelineTemplate] = field(default_factory=list)
    pagination: Optional[PaginationInfo] = None
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    total_global_templates: int = 0
    total_workspace_templates: int = 0


@dataclass(frozen=True)
class GetPipelineTemplateQuery(GetByIdQuery):
    """Query to get a specific pipeline template by ID."""
    
    template_id: Union[str, PipelineId] = ""
    workspace_name: Optional[str] = None
    include_global: bool = True
    include_usage_stats: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        
        # Convert string to PipelineId if needed
        if isinstance(self.template_id, str) and self.template_id:
            object.__setattr__(self, 'template_id', PipelineId(self.template_id))


@dataclass(frozen=True)
class GetPipelineTemplateResult(QueryResult):
    """Result for single pipeline template query."""
    
    template: Optional[PipelineTemplate] = None
    usage_stats: Optional[Dict[str, Any]] = None
    recent_runs: List[Dict[str, Any]] = field(default_factory=list)
    is_global: bool = False


@dataclass(frozen=True)
class SearchPipelineTemplatesQuery(SearchQuery):
    """Query to search pipeline templates by text content.
    
    Searches across template name, description, tags, and step descriptions.
    Supports advanced filtering and relevance scoring.
    """
    
    workspace_name: Optional[str] = None
    include_global: bool = True
    search_fields: List[str] = field(default_factory=lambda: ["name", "description", "tags"])
    category_filter: Optional[str] = None
    tag_filter: List[str] = field(default_factory=list)
    min_relevance_score: float = 0.0


@dataclass(frozen=True)
class SearchPipelineTemplatesResult(QueryResult):
    """Result for pipeline template search query."""
    
    templates: List[Dict[str, Any]] = field(default_factory=list)  # Templates with relevance scores
    search_metadata: Dict[str, Any] = field(default_factory=dict)
    suggestion: Optional[str] = None  # Search suggestions
    pagination: Optional[PaginationInfo] = None


# Run Queries

@dataclass(frozen=True)
class GetPipelineRunQuery(GetByIdQuery):
    """Query to get a specific pipeline run by ID."""
    
    run_id: str = ""
    workspace_name: Optional[str] = None
    include_step_executions: bool = True
    include_outputs: bool = True
    include_metrics: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        
        if not self.run_id:
            raise ValueError("Run ID is required")


@dataclass(frozen=True)
class GetPipelineRunResult(QueryResult):
    """Result for single pipeline run query."""
    
    run: Optional[PipelineRun] = None
    step_executions: List[StepExecution] = field(default_factory=list)
    execution_metrics: Optional[Dict[str, Any]] = None
    template_info: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class GetPipelineRunsQuery(ListQuery):
    """Query to list pipeline runs with filtering and pagination.
    
    Supports filtering by template, status, date range, and workspace.
    """
    
    workspace_name: Optional[str] = None
    template_id: Optional[Union[str, PipelineId]] = None
    status_filter: List[PipelineExecutionStatus] = field(default_factory=list)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_failed: bool = True
    include_cancelled: bool = True
    sort_by: RunSortField = RunSortField.CREATED_AT
    
    def __post_init__(self):
        super().__post_init__()
        
        # Convert string template_id to PipelineId if needed
        if isinstance(self.template_id, str) and self.template_id:
            object.__setattr__(self, 'template_id', PipelineId(self.template_id))
        
        # Convert string sort_by to enum if needed
        if isinstance(self.sort_by, str):
            object.__setattr__(self, 'sort_by', RunSortField(self.sort_by))
        
        # Validate date range
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")


@dataclass(frozen=True)
class GetPipelineRunsResult(QueryResult):
    """Result for pipeline runs list query."""
    
    runs: List[PipelineRun] = field(default_factory=list)
    pagination: Optional[PaginationInfo] = None
    status_summary: Dict[str, int] = field(default_factory=dict)
    date_range_stats: Dict[str, Any] = field(default_factory=dict)


# History and Analytics Queries

@dataclass(frozen=True)
class GetPipelineHistoryQuery(Query):
    """Query to get execution history and analytics for pipelines.
    
    Provides historical data for monitoring pipeline performance,
    success rates, and usage patterns over time.
    """
    
    workspace_name: Optional[str] = None
    template_id: Optional[Union[str, PipelineId]] = None
    date_range_days: int = 30
    include_step_breakdown: bool = False
    include_token_usage: bool = True
    include_performance_metrics: bool = True
    group_by_period: str = "day"  # "hour", "day", "week", "month"
    
    def __post_init__(self):
        super().__post_init__()
        
        # Convert string template_id to PipelineId if needed
        if isinstance(self.template_id, str) and self.template_id:
            object.__setattr__(self, 'template_id', PipelineId(self.template_id))
        
        # Validate date range
        if self.date_range_days <= 0 or self.date_range_days > 365:
            raise ValueError("Date range must be between 1 and 365 days")
        
        # Validate group_by_period
        valid_periods = {"hour", "day", "week", "month"}
        if self.group_by_period not in valid_periods:
            raise ValueError(f"Group by period must be one of {valid_periods}")


@dataclass(frozen=True)
class GetPipelineHistoryResult(QueryResult):
    """Result for pipeline history query."""
    
    time_series_data: List[Dict[str, Any]] = field(default_factory=list)
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    success_rate_trend: List[Dict[str, Any]] = field(default_factory=list)
    token_usage_trend: List[Dict[str, Any]] = field(default_factory=list)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    step_performance: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GetPipelineMetricsQuery(Query):
    """Query to get performance metrics and KPIs for pipelines.
    
    Provides key performance indicators, cost analysis,
    and operational metrics for pipeline management.
    """
    
    workspace_name: Optional[str] = None
    template_ids: List[Union[str, PipelineId]] = field(default_factory=list)
    date_range_days: int = 7
    include_cost_analysis: bool = True
    include_performance_breakdown: bool = True
    include_error_analysis: bool = True
    compare_previous_period: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        
        # Convert string template_ids to PipelineId if needed
        converted_ids = []
        for template_id in self.template_ids:
            if isinstance(template_id, str):
                converted_ids.append(PipelineId(template_id))
            else:
                converted_ids.append(template_id)
        object.__setattr__(self, 'template_ids', converted_ids)
        
        # Validate date range
        if self.date_range_days <= 0 or self.date_range_days > 365:
            raise ValueError("Date range must be between 1 and 365 days")


@dataclass(frozen=True)
class GetPipelineMetricsResult(QueryResult):
    """Result for pipeline metrics query."""
    
    overall_metrics: Dict[str, Any] = field(default_factory=dict)
    template_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    cost_analysis: Dict[str, Any] = field(default_factory=dict)
    performance_benchmarks: Dict[str, Any] = field(default_factory=dict)
    error_analysis: Dict[str, Any] = field(default_factory=dict)
    trend_comparison: Optional[Dict[str, Any]] = None
    recommendations: List[str] = field(default_factory=list)


# Step Execution Queries

@dataclass(frozen=True)
class GetStepExecutionsQuery(ListQuery):
    """Query to list step executions with filtering and pagination.
    
    Provides detailed execution data for individual pipeline steps,
    useful for debugging and performance optimization.
    """
    
    run_id: Optional[str] = None
    step_id: Optional[Union[str, StepId]] = None
    workspace_name: Optional[str] = None
    status_filter: List[str] = field(default_factory=list)
    date_range_days: int = 7
    include_outputs: bool = False
    include_llm_details: bool = False
    sort_by: ExecutionSortField = ExecutionSortField.STARTED_AT
    
    def __post_init__(self):
        super().__post_init__()
        
        # Convert string step_id to StepId if needed
        if isinstance(self.step_id, str) and self.step_id:
            object.__setattr__(self, 'step_id', StepId(self.step_id))
        
        # Convert string sort_by to enum if needed
        if isinstance(self.sort_by, str):
            object.__setattr__(self, 'sort_by', ExecutionSortField(self.sort_by))
        
        # Validate that either run_id or workspace_name is provided
        if not self.run_id and not self.workspace_name:
            raise ValueError("Either run_id or workspace_name must be provided")


@dataclass(frozen=True)
class GetStepExecutionsResult(QueryResult):
    """Result for step executions list query."""
    
    executions: List[StepExecution] = field(default_factory=list)
    pagination: Optional[PaginationInfo] = None
    execution_summary: Dict[str, Any] = field(default_factory=dict)
    performance_stats: Dict[str, Any] = field(default_factory=dict)
    error_patterns: List[Dict[str, Any]] = field(default_factory=list)