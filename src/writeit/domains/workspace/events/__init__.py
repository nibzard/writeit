"""Workspace domain events.

This module contains all domain events for the Workspace bounded context.
Domain events represent significant business occurrences."""

from .workspace_events import (
    WorkspaceCreated,
    WorkspaceActivated,
    WorkspaceDeleted,
    WorkspaceConfigUpdated,
    WorkspaceInitialized,
    WorkspaceArchived,
    WorkspaceRestored
)

__all__ = [
    # Workspace lifecycle events
    "WorkspaceCreated",
    "WorkspaceActivated",
    "WorkspaceDeleted",
    "WorkspaceConfigUpdated",
    "WorkspaceInitialized",
    "WorkspaceArchived",
    "WorkspaceRestored",
]