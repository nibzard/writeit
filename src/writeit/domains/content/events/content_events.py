"""Content domain events.

Events related to template creation, content generation, validation, and lifecycle management."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List

from ....shared.events import DomainEvent
from ..value_objects.content_id import ContentId
from ..value_objects.template_name import TemplateName
from ..value_objects.style_name import StyleName
from ..value_objects.content_type import ContentType
from ..value_objects.content_format import ContentFormat


@dataclass(frozen=True)
class TemplateCreated(DomainEvent):
    """Event fired when a new template is created.
    
    This event is published when a content template is successfully
    created and saved to the system, ready for use in pipeline execution.
    """
    
    template_id: ContentId = field()
    template_name: TemplateName = field()
    content_type: ContentType = field()
    created_by: Optional[str] = field()
    created_at: datetime = field()
    version: str = field()
    description: Optional[str] = field()
    tags: List[str] = field()
    output_format: Optional[ContentFormat] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.template_created"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.template_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "template_id": str(self.template_id),
                "template_name": str(self.template_name),
                "content_type": str(self.content_type),
                "created_by": self.created_by,
                "created_at": self.created_at.isoformat(),
                "version": self.version,
                "description": self.description,
                "tags": self.tags,
                "output_format": str(self.output_format) if self.output_format else None
            }
        }


@dataclass(frozen=True)
class TemplateUpdated(DomainEvent):
    """Event fired when a template is updated.
    
    This event is published when template content, metadata, or
    configuration is modified, creating a new version.
    """
    
    template_id: ContentId = field()
    template_name: TemplateName = field()
    updated_by: Optional[str] = field()
    updated_at: datetime = field()
    old_version: str = field()
    new_version: str = field()
    change_summary: str = field()
    content_changed: bool = field()
    metadata_changes: Dict[str, Any] = field()
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.template_updated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.template_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "template_id": str(self.template_id),
                "template_name": str(self.template_name),
                "updated_by": self.updated_by,
                "updated_at": self.updated_at.isoformat(),
                "old_version": self.old_version,
                "new_version": self.new_version,
                "change_summary": self.change_summary,
                "content_changed": self.content_changed,
                "metadata_changes": self.metadata_changes
            }
        }


@dataclass(frozen=True)
class TemplatePublished(DomainEvent):
    """Event fired when a template is published.
    
    This event is published when a template is made available
    for use by other users or in production pipelines.
    """
    
    template_id: ContentId = field()
    template_name: TemplateName = field()
    published_by: Optional[str] = field()
    published_at: datetime = field()
    version: str = field()
    approval_required: bool = field()
    approved_by: Optional[str] = field()
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.template_published"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.template_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "template_id": str(self.template_id),
                "template_name": str(self.template_name),
                "published_by": self.published_by,
                "published_at": self.published_at.isoformat(),
                "version": self.version,
                "approval_required": self.approval_required,
                "approved_by": self.approved_by
            }
        }


@dataclass(frozen=True)
class TemplateDeprecated(DomainEvent):
    """Event fired when a template is deprecated.
    
    This event is published when a template is marked as deprecated
    and should no longer be used for new content generation.
    """
    
    template_id: ContentId = field()
    template_name: TemplateName = field()
    deprecated_by: Optional[str] = field()
    deprecated_at: datetime = field()
    reason: Optional[str] = field()
    replacement_template_id: Optional[ContentId] = field(default=None)
    migration_deadline: Optional[datetime] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.template_deprecated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.template_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "template_id": str(self.template_id),
                "template_name": str(self.template_name),
                "deprecated_by": self.deprecated_by,
                "deprecated_at": self.deprecated_at.isoformat(),
                "reason": self.reason,
                "replacement_template_id": str(self.replacement_template_id) if self.replacement_template_id else None,
                "migration_deadline": self.migration_deadline.isoformat() if self.migration_deadline else None
            }
        }


@dataclass(frozen=True)
class TemplateValidated(DomainEvent):
    """Event fired when template validation is completed.
    
    This event is published after template validation runs,
    containing validation results and any issues found.
    """
    
    template_id: ContentId = field()
    template_name: TemplateName = field()
    validated_at: datetime = field()
    validation_passed: bool = field()
    validator_version: str = field()
    validation_rules_checked: List[str] = field()
    errors: List[Dict[str, Any]] = field()
    warnings: List[Dict[str, Any]] = field()
    quality_score: Optional[float] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.template_validated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.template_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "template_id": str(self.template_id),
                "template_name": str(self.template_name),
                "validated_at": self.validated_at.isoformat(),
                "validation_passed": self.validation_passed,
                "validator_version": self.validator_version,
                "validation_rules_checked": self.validation_rules_checked,
                "errors": self.errors,
                "warnings": self.warnings,
                "quality_score": self.quality_score
            }
        }


@dataclass(frozen=True)
class ContentGenerated(DomainEvent):
    """Event fired when content is successfully generated.
    
    This event is published when a pipeline successfully generates
    content using a template, including generation metrics and quality data.
    """
    
    content_id: ContentId = field()
    template_id: ContentId = field()
    template_name: TemplateName = field()
    content_type: ContentType = field()
    generated_at: datetime = field()
    pipeline_run_id: Optional[str] = field()
    word_count: int = field()
    character_count: int = field()
    style_name: Optional[StyleName] = field(default=None)
    generation_time_seconds: float = field(default=0.0)
    llm_model_used: Optional[str] = field(default=None)
    tokens_used: int = field(default=0)
    generation_cost: float = field(default=0.0)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.content_generated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.content_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "content_id": str(self.content_id),
                "template_id": str(self.template_id),
                "template_name": str(self.template_name),
                "content_type": str(self.content_type),
                "generated_at": self.generated_at.isoformat(),
                "pipeline_run_id": self.pipeline_run_id,
                "word_count": self.word_count,
                "character_count": self.character_count,
                "style_name": str(self.style_name) if self.style_name else None,
                "generation_time_seconds": self.generation_time_seconds,
                "llm_model_used": self.llm_model_used,
                "tokens_used": self.tokens_used,
                "generation_cost": self.generation_cost
            }
        }


@dataclass(frozen=True)
class ContentValidated(DomainEvent):
    """Event fired when generated content is validated.
    
    This event is published after content validation runs,
    containing quality metrics and validation results.
    """
    
    content_id: ContentId = field()
    template_id: ContentId = field()
    validated_at: datetime = field()
    validation_passed: bool = field()
    validation_rules_applied: List[str] = field()
    quality_metrics: Dict[str, Any] = field()
    errors: List[Dict[str, Any]] = field()
    warnings: List[Dict[str, Any]] = field()
    overall_quality_score: Optional[float] = field(default=None)
    recommended_actions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.content_validated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.content_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "content_id": str(self.content_id),
                "template_id": str(self.template_id),
                "validated_at": self.validated_at.isoformat(),
                "validation_passed": self.validation_passed,
                "validation_rules_applied": self.validation_rules_applied,
                "quality_metrics": self.quality_metrics,
                "errors": self.errors,
                "warnings": self.warnings,
                "overall_quality_score": self.overall_quality_score,
                "recommended_actions": self.recommended_actions
            }
        }


@dataclass(frozen=True)
class ContentApproved(DomainEvent):
    """Event fired when content is approved for publication.
    
    This event is published when content passes review and
    is approved for publication or further use.
    """
    
    content_id: ContentId = field()
    template_id: ContentId = field()
    approved_by: str = field()
    approved_at: datetime = field()
    approval_level: str = field()  # draft, review, final, published
    feedback: Optional[str] = field()
    quality_rating: Optional[int] = field(default=None)  # 1-5 rating
    requires_revision: bool = field(default=False)
    revision_notes: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.content_approved"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.content_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "content_id": str(self.content_id),
                "template_id": str(self.template_id),
                "approved_by": self.approved_by,
                "approved_at": self.approved_at.isoformat(),
                "approval_level": self.approval_level,
                "feedback": self.feedback,
                "quality_rating": self.quality_rating,
                "requires_revision": self.requires_revision,
                "revision_notes": self.revision_notes
            }
        }


@dataclass(frozen=True)
class ContentRevised(DomainEvent):
    """Event fired when content is revised.
    
    This event is published when content is updated based on
    feedback, creating a new version or revision.
    """
    
    content_id: ContentId = field()
    template_id: ContentId = field()
    original_content_id: ContentId = field()
    revised_by: Optional[str] = field()
    revised_at: datetime = field()
    revision_reason: str = field()
    changes_made: List[str] = field()
    old_version: str = field()
    new_version: str = field()
    revision_count: int = field()
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.content_revised"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.content_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "content_id": str(self.content_id),
                "template_id": str(self.template_id),
                "original_content_id": str(self.original_content_id),
                "revised_by": self.revised_by,
                "revised_at": self.revised_at.isoformat(),
                "revision_reason": self.revision_reason,
                "changes_made": self.changes_made,
                "old_version": self.old_version,
                "new_version": self.new_version,
                "revision_count": self.revision_count
            }
        }


@dataclass(frozen=True)
class StylePrimerCreated(DomainEvent):
    """Event fired when a new style primer is created.
    
    This event is published when a style primer is successfully
    created and made available for content generation.
    """
    
    style_id: ContentId = field()
    style_name: StyleName = field()
    created_by: Optional[str] = field()
    created_at: datetime = field()
    content_types: List[ContentType] = field()
    description: Optional[str] = field()
    is_default: bool = field(default=False)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.style_primer_created"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.style_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "style_id": str(self.style_id),
                "style_name": str(self.style_name),
                "created_by": self.created_by,
                "created_at": self.created_at.isoformat(),
                "content_types": [str(ct) for ct in self.content_types],
                "description": self.description,
                "is_default": self.is_default
            }
        }


@dataclass(frozen=True)
class StylePrimerUpdated(DomainEvent):
    """Event fired when a style primer is updated.
    
    This event is published when style primer content,
    guidelines, or metadata is modified.
    """
    
    style_id: ContentId = field()
    style_name: StyleName = field()
    updated_by: Optional[str] = field()
    updated_at: datetime = field()
    change_summary: str = field()
    old_version: str = field()
    new_version: str = field()
    affects_existing_content: bool = field()
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "content.style_primer_updated"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.style_id)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "style_id": str(self.style_id),
                "style_name": str(self.style_name),
                "updated_by": self.updated_by,
                "updated_at": self.updated_at.isoformat(),
                "change_summary": self.change_summary,
                "old_version": self.old_version,
                "new_version": self.new_version,
                "affects_existing_content": self.affects_existing_content
            }
        }