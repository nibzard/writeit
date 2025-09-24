"""Workspace query definitions for application layer.

Provides application-level queries for workspace operations with proper
abstraction and type safety.
"""

from abc import ABC
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
    PaginationInfo,
    QueryHandler
)
from ...domains.workspace.value_objects import WorkspaceName
from ...domains.workspace.entities import Workspace
from ...domains.workspace.services.workspace_configuration_service import (
    ConfigurationScope,
    ConfigurationSchema
)


class WorkspaceSortField(Enum):
    """Available fields for sorting workspaces."""
    NAME = "name"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    SIZE = "size"
    PIPELINE_COUNT = "pipeline_count"


@dataclass(frozen=True)
class GetWorkspacesQuery(ListQuery):
    """Query for listing workspaces with filtering and pagination."""
    
    include_inactive: bool = False
    include_analytics: bool = False
    name_filter: Optional[str] = None


@dataclass(frozen=True)
class GetWorkspaceQuery(GetByIdQuery):
    """Query for getting workspace by name."""
    
    workspace_name: str


@dataclass(frozen=True)
class GetActiveWorkspaceQuery(Query):
    """Query for getting the active workspace."""
    
    pass


@dataclass(frozen=True)
class GetWorkspaceConfigQuery(Query):
    """Query for getting workspace configuration."""
    
    workspace_name: str = ""
    scope: ConfigurationScope = ConfigurationScope.WORKSPACE


@dataclass(frozen=True)
class GetWorkspaceStatsQuery(Query):
    """Query for getting workspace statistics."""
    
    workspace_name: str = ""
    include_analytics: bool = True


@dataclass(frozen=True)
class SearchWorkspacesQuery(SearchQuery):
    """Query for searching workspaces."""
    
    search_fields: List[str] = field(default_factory=lambda: ["name", "description"])
    
    def __post_init__(self):
        """Initialize with default search term if not provided."""
        super().__post_init__()
        
        # Set a default search term if empty
        if not self.search_term or not self.search_term.strip():
            object.__setattr__(self, 'search_term', '*')  # Match all


@dataclass(frozen=True)
class ValidateWorkspaceNameQuery(Query):
    """Query for validating workspace name."""
    
    name: str = ""
    check_exists: bool = True


@dataclass(frozen=True)
class CheckWorkspaceExistsQuery(Query):
    """Query for checking if workspace exists."""
    
    name: str = ""


@dataclass(frozen=True)
class GetWorkspaceHealthQuery(Query):
    """Query for getting workspace health status."""
    
    workspace_name: str = ""
    include_detailed: bool = False


@dataclass(frozen=True)
class GetWorkspaceTemplatesQuery(ListQuery):
    """Query for getting workspace templates."""
    
    workspace_name: str = ""
    template_type: Optional[str] = None


@dataclass(frozen=True)
class GetWorkspaceTemplateQuery(GetByIdQuery):
    """Query for getting workspace template by name."""
    
    workspace_name: str = ""
    template_name: str = ""


# Query Result Classes

@dataclass(frozen=True)
class WorkspaceQueryResult(QueryResult):
    """Base result for workspace queries."""
    
    workspace: Optional[Workspace] = None
    workspaces: List[Workspace] = field(default_factory=list)
    config: Optional[Dict[str, Any]] = None
    stats: Optional[Dict[str, Any]] = None
    health: Optional[Dict[str, Any]] = None
    exists: Optional[bool] = None
    is_valid: Optional[bool] = None
    validation_errors: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class WorkspaceTemplateQueryResult(QueryResult):
    """Result for workspace template queries."""
    
    templates: List[Dict[str, Any]] = field(default_factory=list)
    template: Optional[Dict[str, Any]] = None


# Query Handler Interfaces

class GetWorkspacesQueryHandler(QueryHandler[GetWorkspacesQuery, WorkspaceQueryResult], ABC):
    """Base interface for getting workspaces query handlers."""
    pass


class GetWorkspaceQueryHandler(QueryHandler[GetWorkspaceQuery, WorkspaceQueryResult], ABC):
    """Base interface for getting workspace query handlers."""
    pass


class GetActiveWorkspaceQueryHandler(QueryHandler[GetActiveWorkspaceQuery, WorkspaceQueryResult], ABC):
    """Base interface for getting active workspace query handlers."""
    pass


class GetWorkspaceConfigQueryHandler(QueryHandler[GetWorkspaceConfigQuery, WorkspaceQueryResult], ABC):
    """Base interface for getting workspace config query handlers."""
    pass


class GetWorkspaceStatsQueryHandler(QueryHandler[GetWorkspaceStatsQuery, WorkspaceQueryResult], ABC):
    """Base interface for getting workspace stats query handlers."""
    pass


class SearchWorkspacesQueryHandler(QueryHandler[SearchWorkspacesQuery, WorkspaceQueryResult], ABC):
    """Base interface for searching workspaces query handlers."""
    pass


class ValidateWorkspaceNameQueryHandler(QueryHandler[ValidateWorkspaceNameQuery, WorkspaceQueryResult], ABC):
    """Base interface for validating workspace name query handlers."""
    pass


class CheckWorkspaceExistsQueryHandler(QueryHandler[CheckWorkspaceExistsQuery, WorkspaceQueryResult], ABC):
    """Base interface for checking workspace exists query handlers."""
    pass


class GetWorkspaceHealthQueryHandler(QueryHandler[GetWorkspaceHealthQuery, WorkspaceQueryResult], ABC):
    """Base interface for getting workspace health query handlers."""
    pass


class GetWorkspaceTemplatesQueryHandler(QueryHandler[GetWorkspaceTemplatesQuery, WorkspaceTemplateQueryResult], ABC):
    """Base interface for getting workspace templates query handlers."""
    pass


class GetWorkspaceTemplateQueryHandler(QueryHandler[GetWorkspaceTemplateQuery, WorkspaceTemplateQueryResult], ABC):
    """Base interface for getting workspace template query handlers."""
    pass