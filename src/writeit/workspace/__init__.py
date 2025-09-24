# ABOUTME: WriteIt workspace management library
# ABOUTME: Handles centralized ~/.writeit directory structure and workspace operations
# DEPRECATED: This module is deprecated. Use writeit.domains.workspace and writeit.application.services instead.

from .workspace import Workspace, WorkspaceConfig, GlobalConfig
from .config import ConfigLoader, get_writeit_home, get_active_workspace
from .migration import WorkspaceMigrator, find_and_migrate_workspaces

__all__ = [
    "Workspace",
    "WorkspaceConfig",
    "GlobalConfig",
    "ConfigLoader",
    "get_writeit_home",
    "get_active_workspace",
    "WorkspaceMigrator",
    "find_and_migrate_workspaces",
]
