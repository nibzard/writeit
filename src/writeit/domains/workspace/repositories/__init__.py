"""Workspace domain repositories.

Repository interfaces for workspace domain entities providing
data access operations for workspace and configuration management.
"""

from .workspace_repository import (
    WorkspaceRepository,
    ByNameSpecification,
    ByTagSpecification,
    ActiveWorkspaceSpecification,
    RecentlyAccessedSpecification,
)

from .workspace_config_repository import (
    WorkspaceConfigRepository,
    ByWorkspaceSpecification,
    ByWorkspaceNameSpecification,
    HasConfigKeySpecification,
    HasConfigValueSpecification,
    CustomConfigSpecification,
)

__all__ = [
    # Repository interfaces
    "WorkspaceRepository",
    "WorkspaceConfigRepository",
    
    # Workspace specifications
    "ByNameSpecification",
    "ByTagSpecification",
    "ActiveWorkspaceSpecification",
    "RecentlyAccessedSpecification",
    
    # Configuration specifications  
    "ByWorkspaceSpecification",
    "ByWorkspaceNameSpecification",
    "HasConfigKeySpecification",
    "HasConfigValueSpecification",
    "CustomConfigSpecification",
]