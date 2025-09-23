"""Workspace lifecycle domain events.

Events related to workspace creation, activation, modification, and deletion."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from ....shared.events import DomainEvent
from ..value_objects.workspace_name import WorkspaceName
from ..value_objects.workspace_path import WorkspacePath


@dataclass(frozen=True)
class WorkspaceCreated(DomainEvent):
    """Event fired when a new workspace is created.
    
    This event is published when a workspace is successfully
    created with its directory structure and initial configuration.
    """
    
    workspace_name: WorkspaceName = field()
    workspace_path: WorkspacePath = field()
    created_by: Optional[str] = field()
    created_at: datetime = field()
    initial_config: Dict[str, Any] = field()
    is_default: bool = field(default=False)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "workspace.created"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.workspace_name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "workspace_name": str(self.workspace_name),
                "workspace_path": str(self.workspace_path),
                "created_by": self.created_by,
                "created_at": self.created_at.isoformat(),
                "initial_config": self.initial_config,
                "is_default": self.is_default
            }
        }


@dataclass(frozen=True)
class WorkspaceActivated(DomainEvent):
    """Event fired when a workspace becomes the active workspace.
    
    This event is published when a user switches to a workspace,
    making it the current working workspace for operations.
    """
    
    workspace_name: WorkspaceName = field()
    workspace_path: WorkspacePath = field()
    activated_by: Optional[str] = field()
    activated_at: datetime = field()
    previous_workspace: Optional[WorkspaceName] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "workspace.activated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.workspace_name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "workspace_name": str(self.workspace_name),
                "workspace_path": str(self.workspace_path),
                "activated_by": self.activated_by,
                "activated_at": self.activated_at.isoformat(),
                "previous_workspace": str(self.previous_workspace) if self.previous_workspace else None
            }
        }


@dataclass(frozen=True)
class WorkspaceDeleted(DomainEvent):
    """Event fired when a workspace is deleted.
    
    This event is published when a workspace and its contents
    are permanently removed from the system.
    """
    
    workspace_name: WorkspaceName = field()
    workspace_path: WorkspacePath = field()
    deleted_by: Optional[str] = field()
    deleted_at: datetime = field()
    reason: Optional[str] = field()
    backup_created: bool = field(default=False)
    backup_location: Optional[WorkspacePath] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "workspace.deleted"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.workspace_name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "workspace_name": str(self.workspace_name),
                "workspace_path": str(self.workspace_path),
                "deleted_by": self.deleted_by,
                "deleted_at": self.deleted_at.isoformat(),
                "reason": self.reason,
                "backup_created": self.backup_created,
                "backup_location": str(self.backup_location) if self.backup_location else None
            }
        }


@dataclass(frozen=True)
class WorkspaceConfigUpdated(DomainEvent):
    """Event fired when workspace configuration is modified.
    
    This event is published when workspace settings, preferences,
    or configuration files are updated.
    """
    
    workspace_name: WorkspaceName = field()
    workspace_path: WorkspacePath = field()
    updated_by: Optional[str] = field()
    updated_at: datetime = field()
    config_changes: Dict[str, Any] = field()
    old_config: Dict[str, Any] = field()
    new_config: Dict[str, Any] = field()
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "workspace.config_updated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.workspace_name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "workspace_name": str(self.workspace_name),
                "workspace_path": str(self.workspace_path),
                "updated_by": self.updated_by,
                "updated_at": self.updated_at.isoformat(),
                "config_changes": self.config_changes,
                "old_config": self.old_config,
                "new_config": self.new_config
            }
        }


@dataclass(frozen=True)
class WorkspaceInitialized(DomainEvent):
    """Event fired when a workspace is initialized with default structure.
    
    This event is published after workspace creation when the initial
    directory structure, templates, and configuration are set up.
    """
    
    workspace_name: WorkspaceName = field()
    workspace_path: WorkspacePath = field()
    initialized_by: Optional[str] = field()
    initialized_at: datetime = field()
    directories_created: list[str] = field()
    templates_installed: list[str] = field()
    config_file_path: str = field()
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "workspace.initialized"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.workspace_name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "workspace_name": str(self.workspace_name),
                "workspace_path": str(self.workspace_path),
                "initialized_by": self.initialized_by,
                "initialized_at": self.initialized_at.isoformat(),
                "directories_created": self.directories_created,
                "templates_installed": self.templates_installed,
                "config_file_path": self.config_file_path
            }
        }


@dataclass(frozen=True)
class WorkspaceArchived(DomainEvent):
    """Event fired when a workspace is archived for long-term storage.
    
    This event is published when a workspace is moved to archive
    storage, typically for inactive projects or backup purposes.
    """
    
    workspace_name: WorkspaceName = field()
    workspace_path: WorkspacePath = field()
    archived_by: Optional[str] = field()
    archived_at: datetime = field()
    archive_location: WorkspacePath = field()
    archive_format: str = field()  # e.g., "tar.gz", "zip"
    reason: Optional[str] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "workspace.archived"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.workspace_name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "workspace_name": str(self.workspace_name),
                "workspace_path": str(self.workspace_path),
                "archived_by": self.archived_by,
                "archived_at": self.archived_at.isoformat(),
                "archive_location": str(self.archive_location),
                "archive_format": self.archive_format,
                "reason": self.reason
            }
        }


@dataclass(frozen=True)
class WorkspaceRestored(DomainEvent):
    """Event fired when a workspace is restored from archive.
    
    This event is published when a workspace is successfully
    restored from an archive file to active use.
    """
    
    workspace_name: WorkspaceName = field()
    workspace_path: WorkspacePath = field()
    restored_by: Optional[str] = field()
    restored_at: datetime = field()
    archive_source: WorkspacePath = field()
    restoration_mode: str = field(default="full")  # "full", "partial", "config_only"
    overwrite_existing: bool = field(default=False)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "workspace.restored"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.workspace_name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "workspace_name": str(self.workspace_name),
                "workspace_path": str(self.workspace_path),
                "restored_by": self.restored_by,
                "restored_at": self.restored_at.isoformat(),
                "archive_source": str(self.archive_source),
                "restoration_mode": self.restoration_mode,
                "overwrite_existing": self.overwrite_existing
            }
        }