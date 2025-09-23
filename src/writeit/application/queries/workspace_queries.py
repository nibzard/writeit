"""Workspace CQRS Queries.

Queries for read operations related to workspace management,
configuration, and isolation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from ...shared.query import Query, QueryHandler, QueryResult, ListQuery, GetByIdQuery, SearchQuery
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.workspace.entities import Workspace, WorkspaceConfig


class WorkspaceStatus(str, Enum):
    """Workspace status for filtering."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    INITIALIZING = "initializing"
    ERROR = "error"


class WorkspaceScope(str, Enum):
    """Workspace scope for filtering."""
    USER = "user"
    GLOBAL = "global"
    SYSTEM = "system"


# Workspace Management Queries

@dataclass(frozen=True)
class GetWorkspacesQuery(ListQuery):
    """Query to list all workspaces with filtering and pagination."""
    
    scope: Optional[WorkspaceScope] = None
    status: Optional[WorkspaceStatus] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    last_accessed_after: Optional[datetime] = None
    include_stats: bool = True
    include_config: bool = False


@dataclass(frozen=True)
class GetWorkspaceQuery(GetByIdQuery):
    """Query to get a workspace by name."""
    
    workspace_name: WorkspaceName
    include_config: bool = True
    include_stats: bool = True
    include_templates: bool = False
    
    def __post_init__(self):
        object.__setattr__(self, 'entity_id', str(self.workspace_name))
        super().__post_init__()


@dataclass(frozen=True)
class GetActiveWorkspaceQuery(Query):
    """Query to get the currently active workspace."""
    
    include_config: bool = True
    include_stats: bool = True


@dataclass(frozen=True)
class GetWorkspaceConfigQuery(Query):
    """Query to get workspace configuration."""
    
    workspace_name: Optional[WorkspaceName] = None  # None for active workspace


@dataclass(frozen=True)
class GetWorkspaceStatsQuery(Query):
    """Query to get workspace statistics."""
    
    workspace_name: Optional[WorkspaceName] = None  # None for active workspace
    include_pipeline_stats: bool = True
    include_content_stats: bool = True
    include_storage_stats: bool = True


@dataclass(frozen=True)
class SearchWorkspacesQuery(SearchQuery):
    """Query to search workspaces by text."""
    
    scope: Optional[WorkspaceScope] = None
    status: Optional[WorkspaceStatus] = None
    search_fields: List[str] = None  # name, description, tags, etc.
    
    def __post_init__(self):
        if self.search_fields is None:
            object.__setattr__(self, 'search_fields', ['name', 'description', 'tags'])
        super().__post_init__()


# Workspace Template Queries

@dataclass(frozen=True)
class GetWorkspaceTemplatesQuery(ListQuery):
    """Query to list workspace templates."""
    
    scope: Optional[WorkspaceScope] = None
    category: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, 'tags', [])
        super().__post_init__()


@dataclass(frozen=True)
class GetWorkspaceTemplateQuery(GetByIdQuery):
    """Query to get a workspace template by name."""
    
    template_name: str
    
    def __post_init__(self):
        object.__setattr__(self, 'entity_id', self.template_name)
        super().__post_init__()


# Workspace Validation Queries

@dataclass(frozen=True)
class ValidateWorkspaceNameQuery(Query):
    """Query to validate workspace name availability."""
    
    workspace_name: WorkspaceName


@dataclass(frozen=True)
class CheckWorkspaceExistsQuery(Query):
    """Query to check if workspace exists."""
    
    workspace_name: WorkspaceName


@dataclass(frozen=True)
class GetWorkspaceHealthQuery(Query):
    """Query to get workspace health status."""
    
    workspace_name: Optional[WorkspaceName] = None  # None for active workspace
    check_storage: bool = True
    check_permissions: bool = True
    check_integrity: bool = True


# Query Results

@dataclass(frozen=True)
class WorkspaceQueryResult(QueryResult):
    """Result for workspace queries."""
    
    workspaces: List[Workspace] = None
    workspace: Optional[Workspace] = None
    config: Optional[WorkspaceConfig] = None
    stats: Optional[Dict[str, Any]] = None
    health: Optional[Dict[str, Any]] = None
    exists: Optional[bool] = None
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.workspaces is None:
            object.__setattr__(self, 'workspaces', [])
        if self.validation_errors is None:
            object.__setattr__(self, 'validation_errors', [])
        super().__post_init__()


@dataclass(frozen=True)
class WorkspaceTemplateQueryResult(QueryResult):
    """Result for workspace template queries."""
    
    templates: List[Dict[str, Any]] = None
    template: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.templates is None:
            object.__setattr__(self, 'templates', [])
        super().__post_init__()


# Query Handler Interfaces

class WorkspaceQueryHandler(QueryHandler[WorkspaceQueryResult], ABC):
    """Base interface for workspace query handlers."""
    pass


class WorkspaceTemplateQueryHandler(QueryHandler[WorkspaceTemplateQueryResult], ABC):
    """Base interface for workspace template query handlers."""
    pass


# Specific Query Handlers

class GetWorkspacesQueryHandler(WorkspaceQueryHandler):
    """Handler for listing workspaces."""
    
    @abstractmethod
    async def handle(self, query: GetWorkspacesQuery) -> WorkspaceQueryResult:
        """Handle list workspaces query."""
        pass


class GetWorkspaceQueryHandler(WorkspaceQueryHandler):
    """Handler for getting workspace by name."""
    
    @abstractmethod
    async def handle(self, query: GetWorkspaceQuery) -> WorkspaceQueryResult:
        """Handle get workspace query."""
        pass


class GetActiveWorkspaceQueryHandler(WorkspaceQueryHandler):
    """Handler for getting active workspace."""
    
    @abstractmethod
    async def handle(self, query: GetActiveWorkspaceQuery) -> WorkspaceQueryResult:
        """Handle get active workspace query."""
        pass


class GetWorkspaceConfigQueryHandler(WorkspaceQueryHandler):
    """Handler for getting workspace configuration."""
    
    @abstractmethod
    async def handle(self, query: GetWorkspaceConfigQuery) -> WorkspaceQueryResult:
        """Handle get workspace config query."""
        pass


class GetWorkspaceStatsQueryHandler(WorkspaceQueryHandler):
    """Handler for getting workspace statistics."""
    
    @abstractmethod
    async def handle(self, query: GetWorkspaceStatsQuery) -> WorkspaceQueryResult:
        """Handle get workspace stats query."""
        pass


class SearchWorkspacesQueryHandler(WorkspaceQueryHandler):
    """Handler for searching workspaces."""
    
    @abstractmethod
    async def handle(self, query: SearchWorkspacesQuery) -> WorkspaceQueryResult:
        """Handle search workspaces query."""
        pass


class ValidateWorkspaceNameQueryHandler(WorkspaceQueryHandler):
    """Handler for validating workspace name."""
    
    @abstractmethod
    async def handle(self, query: ValidateWorkspaceNameQuery) -> WorkspaceQueryResult:
        """Handle validate workspace name query."""
        pass


class CheckWorkspaceExistsQueryHandler(WorkspaceQueryHandler):
    """Handler for checking workspace existence."""
    
    @abstractmethod
    async def handle(self, query: CheckWorkspaceExistsQuery) -> WorkspaceQueryResult:
        """Handle check workspace exists query."""
        pass


class GetWorkspaceHealthQueryHandler(WorkspaceQueryHandler):
    """Handler for getting workspace health."""
    
    @abstractmethod
    async def handle(self, query: GetWorkspaceHealthQuery) -> WorkspaceQueryResult:
        """Handle get workspace health query."""
        pass


class GetWorkspaceTemplatesQueryHandler(WorkspaceTemplateQueryHandler):
    """Handler for listing workspace templates."""
    
    @abstractmethod
    async def handle(self, query: GetWorkspaceTemplatesQuery) -> WorkspaceTemplateQueryResult:
        """Handle list workspace templates query."""
        pass


class GetWorkspaceTemplateQueryHandler(WorkspaceTemplateQueryHandler):
    """Handler for getting workspace template."""
    
    @abstractmethod
    async def handle(self, query: GetWorkspaceTemplateQuery) -> WorkspaceTemplateQueryResult:
        """Handle get workspace template query."""
        pass