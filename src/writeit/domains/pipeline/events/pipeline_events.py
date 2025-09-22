"""Pipeline lifecycle domain events.

Events related to pipeline template creation, modification, and lifecycle changes."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

from ....shared.events import DomainEvent
from ..value_objects.pipeline_id import PipelineId
from ..value_objects.pipeline_name import PipelineName


@dataclass(frozen=True)
class PipelineCreated(DomainEvent):
    """Event fired when a new pipeline template is created.
    
    This event is published when a pipeline template is successfully
    created and persisted to the system.
    """
    
    pipeline_id: PipelineId
    pipeline_name: PipelineName
    version: str
    author: Optional[str]
    category: str
    complexity: str
    step_count: int
    created_at: datetime
    metadata: Dict[str, Any]
    
    @property
    def event_type(self) -> str:
        return "pipeline.created"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.pipeline_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "pipeline_id": str(self.pipeline_id),
                "pipeline_name": str(self.pipeline_name),
                "version": self.version,
                "author": self.author,
                "category": self.category,
                "complexity": self.complexity,
                "step_count": self.step_count,
                "created_at": self.created_at.isoformat(),
                "metadata": self.metadata
            }
        }


@dataclass(frozen=True)
class PipelineUpdated(DomainEvent):
    """Event fired when a pipeline template is updated.
    
    This event is published when a pipeline template is modified,
    including changes to metadata, steps, or configuration.
    """
    
    pipeline_id: PipelineId
    pipeline_name: PipelineName
    old_version: str
    new_version: str
    author: Optional[str]
    changes: Dict[str, Any]
    updated_at: datetime
    
    @property
    def event_type(self) -> str:
        return "pipeline.updated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.pipeline_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "pipeline_id": str(self.pipeline_id),
                "pipeline_name": str(self.pipeline_name),
                "old_version": self.old_version,
                "new_version": self.new_version,
                "author": self.author,
                "changes": self.changes,
                "updated_at": self.updated_at.isoformat()
            }
        }


@dataclass(frozen=True)
class PipelineDeleted(DomainEvent):
    """Event fired when a pipeline template is deleted.
    
    This event is published when a pipeline template is permanently
    removed from the system.
    """
    
    pipeline_id: PipelineId
    pipeline_name: PipelineName
    version: str
    deleted_by: Optional[str]
    deleted_at: datetime
    reason: Optional[str]
    
    @property
    def event_type(self) -> str:
        return "pipeline.deleted"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.pipeline_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "pipeline_id": str(self.pipeline_id),
                "pipeline_name": str(self.pipeline_name),
                "version": self.version,
                "deleted_by": self.deleted_by,
                "deleted_at": self.deleted_at.isoformat(),
                "reason": self.reason
            }
        }


@dataclass(frozen=True)
class PipelinePublished(DomainEvent):
    """Event fired when a pipeline template is published.
    
    This event is published when a pipeline template is made
    publicly available or moved from draft to active status.
    """
    
    pipeline_id: PipelineId
    pipeline_name: PipelineName
    version: str
    published_by: Optional[str]
    published_at: datetime
    previous_status: str
    
    @property
    def event_type(self) -> str:
        return "pipeline.published"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.pipeline_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "pipeline_id": str(self.pipeline_id),
                "pipeline_name": str(self.pipeline_name),
                "version": self.version,
                "published_by": self.published_by,
                "published_at": self.published_at.isoformat(),
                "previous_status": self.previous_status
            }
        }


@dataclass(frozen=True)
class PipelineDeprecated(DomainEvent):
    """Event fired when a pipeline template is deprecated.
    
    This event is published when a pipeline template is marked
    as deprecated, typically when a newer version is available.
    """
    
    pipeline_id: PipelineId
    pipeline_name: PipelineName
    version: str
    deprecated_by: Optional[str]
    deprecated_at: datetime
    reason: Optional[str]
    replacement_version: Optional[str]
    
    @property
    def event_type(self) -> str:
        return "pipeline.deprecated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.pipeline_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "pipeline_id": str(self.pipeline_id),
                "pipeline_name": str(self.pipeline_name),
                "version": self.version,
                "deprecated_by": self.deprecated_by,
                "deprecated_at": self.deprecated_at.isoformat(),
                "reason": self.reason,
                "replacement_version": self.replacement_version
            }
        }