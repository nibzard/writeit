"""Content CQRS Queries.

Queries for read operations related to templates, style primers,
and generated content.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from ...shared.query import Query, QueryHandler, QueryResult, ListQuery, GetByIdQuery, SearchQuery
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.content.entities import Template, StylePrimer, GeneratedContent
from ...domains.content.value_objects import ContentId


class ContentType(str, Enum):
    """Content type for filtering."""
    TEMPLATE = "template"
    STYLE_PRIMER = "style_primer"
    GENERATED_CONTENT = "generated_content"


class TemplateStatus(str, Enum):
    """Template status for filtering."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class ContentScope(str, Enum):
    """Content scope for filtering."""
    WORKSPACE = "workspace"
    GLOBAL = "global"
    ALL = "all"


# Template Queries

@dataclass(frozen=True)
class GetTemplatesQuery(ListQuery):
    """Query to list content templates with filtering and pagination."""
    
    workspace_name: Optional[str] = None
    scope: ContentScope = ContentScope.WORKSPACE
    category: Optional[str] = None
    tags: List[str] = None
    author: Optional[str] = None
    status: Optional[TemplateStatus] = None
    content_type: Optional[ContentType] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    updated_before: Optional[datetime] = None
    
    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, 'tags', [])
        super().__post_init__()


@dataclass(frozen=True)
class GetTemplateQuery(GetByIdQuery):
    """Query to get a content template by ID."""
    
    template_id: Optional[ContentId] = None
    workspace_name: Optional[str] = None
    include_metadata: bool = True
    include_content: bool = True
    
    def __post_init__(self):
        if self.template_id is None:
            raise ValueError("template_id is required")
        object.__setattr__(self, 'entity_id', str(self.template_id))
        super().__post_init__()


@dataclass(frozen=True)
class GetTemplateByNameQuery(Query):
    """Query to get a template by name."""
    
    template_name: Optional[str] = None
    workspace_name: Optional[str] = None
    scope: ContentScope = ContentScope.WORKSPACE
    include_versions: bool = False
    
    def __post_init__(self):
        if self.template_name is None:
            raise ValueError("template_name is required")
        super().__post_init__()


@dataclass(frozen=True)
class SearchTemplatesQuery(SearchQuery):
    """Query to search templates by text."""
    
    workspace_name: Optional[str] = None
    scope: ContentScope = ContentScope.WORKSPACE
    content_type: Optional[ContentType] = None
    category: Optional[str] = None
    tags: List[str] = None
    search_fields: List[str] = None  # name, description, content, tags, etc.
    
    def __post_init__(self):
        if self.search_fields is None:
            object.__setattr__(self, 'search_fields', ['name', 'description', 'content', 'tags'])
        if self.tags is None:
            object.__setattr__(self, 'tags', [])
        super().__post_init__()


# Generated Content Queries

@dataclass(frozen=True)
class GetGeneratedContentQuery(GetByIdQuery):
    """Query to get generated content by ID."""
    
    content_id: Optional[ContentId] = None
    workspace_name: Optional[str] = None
    include_metadata: bool = True
    include_source: bool = True
    include_metrics: bool = True
    
    def __post_init__(self):
        if self.content_id is None:
            raise ValueError("content_id is required")
        object.__setattr__(self, 'entity_id', str(self.content_id))
        super().__post_init__()


@dataclass(frozen=True)
class ListGeneratedContentQuery(ListQuery):
    """Query to list generated content with filtering and pagination."""
    
    workspace_name: Optional[str] = None
    template_id: Optional[ContentId] = None
    pipeline_run_id: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    content_type: Optional[str] = None
    status: Optional[str] = None
    include_metrics: bool = False


@dataclass(frozen=True)
class SearchGeneratedContentQuery(SearchQuery):
    """Query to search generated content by text."""
    
    workspace_name: Optional[str] = None
    template_id: Optional[ContentId] = None
    pipeline_run_id: Optional[str] = None
    search_fields: List[str] = None  # title, content, metadata, etc.
    
    def __post_init__(self):
        if self.search_fields is None:
            object.__setattr__(self, 'search_fields', ['title', 'content', 'metadata'])
        super().__post_init__()


# Style Primer Queries

@dataclass(frozen=True)
class GetStylePrimersQuery(ListQuery):
    """Query to list style primers with filtering and pagination."""
    
    workspace_name: Optional[str] = None
    scope: ContentScope = ContentScope.WORKSPACE
    category: Optional[str] = None
    tags: List[str] = None
    author: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, 'tags', [])
        super().__post_init__()


@dataclass(frozen=True)
class GetStylePrimerQuery(GetByIdQuery):
    """Query to get a style primer by ID."""
    
    primer_id: Optional[str] = None
    workspace_name: Optional[str] = None
    
    def __post_init__(self):
        if self.primer_id is None:
            raise ValueError("primer_id is required")
        object.__setattr__(self, 'entity_id', self.primer_id)
        super().__post_init__()


# Content Analytics Queries

@dataclass(frozen=True)
class GetContentAnalyticsQuery(Query):
    """Query to get content usage analytics."""
    
    workspace_name: Optional[str] = None
    content_type: Optional[ContentType] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    group_by: str = "day"  # hour, day, week, month
    
    def __post_init__(self):
        super().__post_init__()
        
        if self.group_by not in ("hour", "day", "week", "month"):
            raise ValueError(f"Invalid group_by value: {self.group_by}")


@dataclass(frozen=True)
class GetPopularTemplatesQuery(Query):
    """Query to get most popular templates."""
    
    workspace_name: Optional[str] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    limit: int = 10
    metric: str = "usage_count"  # usage_count, success_rate, avg_rating
    
    def __post_init__(self):
        super().__post_init__()
        
        if self.limit < 1 or self.limit > 100:
            raise ValueError("Limit must be between 1 and 100")
        
        if self.metric not in ("usage_count", "success_rate", "avg_rating"):
            raise ValueError(f"Invalid metric: {self.metric}")


# Content Validation Queries

@dataclass(frozen=True)
class ValidateTemplateQuery(Query):
    """Query to validate a template."""
    
    template_id: Optional[ContentId] = None
    template_content: Optional[str] = None
    validation_level: str = "strict"


@dataclass(frozen=True)
class CheckTemplateExistsQuery(Query):
    """Query to check if template exists."""
    
    template_name: Optional[str] = None
    workspace_name: Optional[str] = None
    scope: ContentScope = ContentScope.WORKSPACE
    
    def __post_init__(self):
        if self.template_name is None:
            raise ValueError("template_name is required")
        super().__post_init__()


# Query Results

@dataclass(frozen=True)
class TemplateQueryResult(QueryResult):
    """Result for template queries."""
    
    templates: List[Template] = None
    template: Optional[Template] = None
    versions: List[Dict[str, Any]] = None
    validation_errors: List[str] = None
    exists: Optional[bool] = None
    
    def __post_init__(self):
        if self.templates is None:
            object.__setattr__(self, 'templates', [])
        if self.versions is None:
            object.__setattr__(self, 'versions', [])
        if self.validation_errors is None:
            object.__setattr__(self, 'validation_errors', [])
        super().__post_init__()


@dataclass(frozen=True)
class GeneratedContentQueryResult(QueryResult):
    """Result for generated content queries."""
    
    content_items: List[GeneratedContent] = None
    content_item: Optional[GeneratedContent] = None
    metrics: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.content_items is None:
            object.__setattr__(self, 'content_items', [])
        super().__post_init__()


@dataclass(frozen=True)
class StylePrimerQueryResult(QueryResult):
    """Result for style primer queries."""
    
    primers: List[StylePrimer] = None
    primer: Optional[StylePrimer] = None
    
    def __post_init__(self):
        if self.primers is None:
            object.__setattr__(self, 'primers', [])
        super().__post_init__()


@dataclass(frozen=True)
class ContentAnalyticsQueryResult(QueryResult):
    """Result for content analytics queries."""
    
    analytics: Dict[str, Any] = None
    popular_templates: List[Dict[str, Any]] = None
    usage_stats: Optional[Dict[str, Any]] = None
    time_series: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.analytics is None:
            object.__setattr__(self, 'analytics', {})
        if self.popular_templates is None:
            object.__setattr__(self, 'popular_templates', [])
        if self.time_series is None:
            object.__setattr__(self, 'time_series', [])
        super().__post_init__()


# Query Handler Interfaces

class TemplateQueryHandler(QueryHandler[GetTemplatesQuery, TemplateQueryResult], ABC):
    """Base interface for template query handlers."""
    pass


class GeneratedContentQueryHandler(QueryHandler[ListGeneratedContentQuery, GeneratedContentQueryResult], ABC):
    """Base interface for generated content query handlers."""
    pass


class StylePrimerQueryHandler(QueryHandler[GetStylePrimersQuery, StylePrimerQueryResult], ABC):
    """Base interface for style primer query handlers."""
    pass


class ContentAnalyticsQueryHandler(QueryHandler[GetContentAnalyticsQuery, ContentAnalyticsQueryResult], ABC):
    """Base interface for content analytics query handlers."""
    pass


# Specific Query Handlers

class GetTemplatesQueryHandler(TemplateQueryHandler):
    """Handler for listing templates."""
    
    @abstractmethod
    async def handle(self, query: GetTemplatesQuery) -> TemplateQueryResult:
        """Handle list templates query."""
        pass


class GetTemplateQueryHandler(TemplateQueryHandler):
    """Handler for getting template by ID."""
    
    @abstractmethod
    async def handle(self, query: GetTemplateQuery) -> TemplateQueryResult:
        """Handle get template query."""
        pass


class GetTemplateByNameQueryHandler(TemplateQueryHandler):
    """Handler for getting template by name."""
    
    @abstractmethod
    async def handle(self, query: GetTemplateByNameQuery) -> TemplateQueryResult:
        """Handle get template by name query."""
        pass


class SearchTemplatesQueryHandler(TemplateQueryHandler):
    """Handler for searching templates."""
    
    @abstractmethod
    async def handle(self, query: SearchTemplatesQuery) -> TemplateQueryResult:
        """Handle search templates query."""
        pass


class GetGeneratedContentQueryHandler(GeneratedContentQueryHandler):
    """Handler for getting generated content by ID."""
    
    @abstractmethod
    async def handle(self, query: GetGeneratedContentQuery) -> GeneratedContentQueryResult:
        """Handle get generated content query."""
        pass


class ListGeneratedContentQueryHandler(GeneratedContentQueryHandler):
    """Handler for listing generated content."""
    
    @abstractmethod
    async def handle(self, query: ListGeneratedContentQuery) -> GeneratedContentQueryResult:
        """Handle list generated content query."""
        pass


class SearchGeneratedContentQueryHandler(GeneratedContentQueryHandler):
    """Handler for searching generated content."""
    
    @abstractmethod
    async def handle(self, query: SearchGeneratedContentQuery) -> GeneratedContentQueryResult:
        """Handle search generated content query."""
        pass


class GetStylePrimersQueryHandler(StylePrimerQueryHandler):
    """Handler for listing style primers."""
    
    @abstractmethod
    async def handle(self, query: GetStylePrimersQuery) -> StylePrimerQueryResult:
        """Handle list style primers query."""
        pass


class GetStylePrimerQueryHandler(StylePrimerQueryHandler):
    """Handler for getting style primer by ID."""
    
    @abstractmethod
    async def handle(self, query: GetStylePrimerQuery) -> StylePrimerQueryResult:
        """Handle get style primer query."""
        pass


class GetContentAnalyticsQueryHandler(ContentAnalyticsQueryHandler):
    """Handler for getting content analytics."""
    
    @abstractmethod
    async def handle(self, query: GetContentAnalyticsQuery) -> ContentAnalyticsQueryResult:
        """Handle get content analytics query."""
        pass


class GetPopularTemplatesQueryHandler(ContentAnalyticsQueryHandler):
    """Handler for getting popular templates."""
    
    @abstractmethod
    async def handle(self, query: GetPopularTemplatesQuery) -> ContentAnalyticsQueryResult:
        """Handle get popular templates query."""
        pass


class ValidateTemplateQueryHandler(TemplateQueryHandler):
    """Handler for validating template."""
    
    @abstractmethod
    async def handle(self, query: ValidateTemplateQuery) -> TemplateQueryResult:
        """Handle validate template query."""
        pass


class CheckTemplateExistsQueryHandler(TemplateQueryHandler):
    """Handler for checking template existence."""
    
    @abstractmethod
    async def handle(self, query: CheckTemplateExistsQuery) -> TemplateQueryResult:
        """Handle check template exists query."""
        pass