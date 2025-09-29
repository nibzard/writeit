"""Content CQRS Commands.

Commands for write operations related to content management,
templates, style primers, and generated content.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from enum import Enum

from ...shared.command import Command, CommandHandler, CommandResult
from ...domains.content.entities import Template, StylePrimer, GeneratedContent
from ...domains.content.value_objects import ContentType, ContentFormat


class ContentValidationLevel(str, Enum):
    """Content validation levels."""
    BASIC = "basic"
    STRICT = "strict"
    COMPREHENSIVE = "comprehensive"


class TemplateScope(str, Enum):
    """Template scope levels."""
    LOCAL = "local"
    WORKSPACE = "workspace"
    GLOBAL = "global"


# Content Command Results

@dataclass(frozen=True)
class ContentCommandResult(CommandResult):
    """Base result for content commands."""
    
    content_id: Optional[str] = None
    template_name: Optional[str] = None
    style_name: Optional[str] = None
    template: Optional[Template] = None
    style_primer: Optional[StylePrimer] = None
    content: Optional[GeneratedContent] = None
    validation_errors: Optional[List[str]] = None
    validation_warnings: Optional[List[str]] = None


# Template Management Commands

@dataclass(frozen=True)
class CreateTemplateCommand(Command):
    """Command to create a new template."""
    
    name: str = ""
    content: str = ""
    description: Optional[str] = None
    template_type: str = "pipeline"
    scope: TemplateScope = TemplateScope.WORKSPACE
    workspace_name: Optional[str] = None
    file_path: Optional[Path] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    validation_level: ContentValidationLevel = ContentValidationLevel.STRICT
    
    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, 'tags', [])


@dataclass(frozen=True)
class UpdateTemplateCommand(Command):
    """Command to update an existing template."""
    
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    file_path: Optional[Path] = None
    validation_level: ContentValidationLevel = ContentValidationLevel.STRICT
    workspace_name: Optional[str] = None


@dataclass(frozen=True)
class DeleteTemplateCommand(Command):
    """Command to delete a template."""
    
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    workspace_name: Optional[str] = None
    scope: TemplateScope = TemplateScope.WORKSPACE
    force: bool = False


@dataclass(frozen=True)
class ValidateTemplateCommand(Command):
    """Command to validate a template."""
    
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    content: Optional[str] = None
    file_path: Optional[Path] = None
    workspace_name: Optional[str] = None
    validation_level: ContentValidationLevel = ContentValidationLevel.STRICT
    scope: TemplateScope = TemplateScope.WORKSPACE


# Style Primer Commands

@dataclass(frozen=True)
class CreateStylePrimerCommand(Command):
    """Command to create a new style primer."""
    
    name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    scope: TemplateScope = TemplateScope.WORKSPACE
    file_path: Optional[Path] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    parent_style: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, 'tags', [])


@dataclass(frozen=True)
class UpdateStylePrimerCommand(Command):
    """Command to update an existing style primer."""
    
    style_id: Optional[str] = None
    style_name: Optional[str] = None
    content: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    parent_style: Optional[str] = None
    file_path: Optional[Path] = None
    workspace_name: Optional[str] = None


@dataclass(frozen=True)
class DeleteStylePrimerCommand(Command):
    """Command to delete a style primer."""
    
    style_id: Optional[str] = None
    style_name: Optional[str] = None
    workspace_name: Optional[str] = None
    scope: TemplateScope = TemplateScope.WORKSPACE
    force: bool = False


# Generated Content Commands

@dataclass(frozen=True)
class CreateGeneratedContentCommand(Command):
    """Command to create generated content."""
    
    content_type: Optional[ContentType] = None
    content_format: Optional[ContentFormat] = None
    raw_content: Optional[str] = None
    template_id: Optional[str] = None
    pipeline_run_id: Optional[str] = None
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            object.__setattr__(self, 'tags', [])


@dataclass(frozen=True)
class UpdateGeneratedContentCommand(Command):
    """Command to update generated content."""
    
    content_id: Optional[str] = None
    raw_content: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


@dataclass(frozen=True)
class DeleteGeneratedContentCommand(Command):
    """Command to delete generated content."""
    
    content_id: Optional[str] = None
    force: bool = False


# Content Validation Commands

@dataclass(frozen=True)
class ValidateContentCommand(Command):
    """Command to validate generated content."""
    
    content_id: Optional[str] = None
    content: Optional[str] = None
    content_type: Optional[ContentType] = None
    validation_rules: Optional[List[str]] = None
    workspace_name: Optional[str] = None


# Template Publishing Commands

@dataclass(frozen=True)
class PublishTemplateCommand(Command):
    """Command to publish a template."""
    
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    target_scope: TemplateScope = TemplateScope.GLOBAL
    workspace_name: Optional[str] = None
    version_notes: Optional[str] = None


@dataclass(frozen=True)
class DeprecateTemplateCommand(Command):
    """Command to deprecate a template."""
    
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    workspace_name: Optional[str] = None
    reason: Optional[str] = None
    replacement_template: Optional[str] = None


# Content Command Handler Interfaces

class CreateTemplateCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for creating templates."""
    pass


class UpdateTemplateCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for updating templates."""
    pass


class DeleteTemplateCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for deleting templates."""
    pass


class ValidateTemplateCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for validating templates."""
    pass


class CreateStylePrimerCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for creating style primers."""
    pass


class UpdateStylePrimerCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for updating style primers."""
    pass


class DeleteStylePrimerCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for deleting style primers."""
    pass


class CreateGeneratedContentCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for creating generated content."""
    pass


class UpdateGeneratedContentCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for updating generated content."""
    pass


class DeleteGeneratedContentCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for deleting generated content."""
    pass


class ValidateContentCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for validating content."""
    pass


class PublishTemplateCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for publishing templates."""
    pass


class DeprecateTemplateCommandHandler(CommandHandler[Command, ContentCommandResult]):
    """Handler interface for deprecating templates."""
    pass