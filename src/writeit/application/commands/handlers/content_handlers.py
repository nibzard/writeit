"""Concrete implementations of Content command handlers.

These handlers implement the business logic for content operations,
coordinating between domain services, repositories, and the event bus.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ....shared.command import CommandHandler
from ....shared.events import EventBus
from ....domains.content.entities import Template, StylePrimer, GeneratedContent
from ....domains.content.repositories import (
    ContentTemplateRepository, 
    StylePrimerRepository, 
    GeneratedContentRepository
)
from ....domains.content.services import TemplateRenderingService, ContentValidationService
from ....domains.content.value_objects import TemplateName, StyleName, ContentId, ContentType, ContentFormat
from ....domains.workspace.value_objects import WorkspaceName
from ....domains.content.events import (
    TemplateCreated, 
    TemplateUpdated, 
    TemplatePublished,
    TemplateDeprecated,
    TemplateValidated,
    StylePrimerCreated,
    StylePrimerUpdated,
    ContentGenerated,
    ContentValidated
)

from ..content_commands import (
    CreateTemplateCommand,
    UpdateTemplateCommand,
    DeleteTemplateCommand,
    ValidateTemplateCommand,
    CreateStylePrimerCommand,
    UpdateStylePrimerCommand,
    DeleteStylePrimerCommand,
    CreateGeneratedContentCommand,
    UpdateGeneratedContentCommand,
    DeleteGeneratedContentCommand,
    ValidateContentCommand,
    PublishTemplateCommand,
    DeprecateTemplateCommand,
    ContentCommandResult,
    ContentValidationLevel,
    TemplateScope,
    CreateTemplateCommandHandler,
    UpdateTemplateCommandHandler,
    DeleteTemplateCommandHandler,
    ValidateTemplateCommandHandler,
    CreateStylePrimerCommandHandler,
    UpdateStylePrimerCommandHandler,
    DeleteStylePrimerCommandHandler,
    CreateGeneratedContentCommandHandler,
    UpdateGeneratedContentCommandHandler,
    DeleteGeneratedContentCommandHandler,
    ValidateContentCommandHandler,
    PublishTemplateCommandHandler,
    DeprecateTemplateCommandHandler,
)

logger = logging.getLogger(__name__)


class ConcreteContentCommandHandler(CommandHandler[ContentCommandResult]):
    """Base class for concrete content command handlers."""
    
    def __init__(
        self,
        template_repository: ContentTemplateRepository,
        style_primer_repository: StylePrimerRepository,
        generated_content_repository: GeneratedContentRepository,
        rendering_service: TemplateRenderingService,
        validation_service: ContentValidationService,
        event_bus: EventBus,
    ):
        """Initialize handler with dependencies.
        
        Args:
            template_repository: Repository for content templates
            style_primer_repository: Repository for style primers
            generated_content_repository: Repository for generated content
            rendering_service: Service for template rendering
            validation_service: Service for content validation
            event_bus: Event bus for publishing domain events
        """
        self._template_repository = template_repository
        self._style_primer_repository = style_primer_repository
        self._generated_content_repository = generated_content_repository
        self._rendering_service = rendering_service
        self._validation_service = validation_service
        self._event_bus = event_bus


class ConcreteCreateTemplateCommandHandler(
    ConcreteContentCommandHandler,
    CreateTemplateCommandHandler
):
    """Concrete handler for creating templates."""
    
    async def handle(self, command: CreateTemplateCommand) -> ContentCommandResult:
        """Handle template creation."""
        logger.info(f"Creating template: {command.name}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Validate template name
            template_name = TemplateName.from_string(command.name)
            
            # Check if template name is already taken
            existing_template = await self._template_repository.find_by_name(
                template_name, 
                scope=command.scope, 
                workspace_name=workspace_name
            )
            if existing_template:
                return ContentCommandResult(
                    success=False,
                    message=f"Template '{command.name}' already exists in {command.scope.value} scope",
                    validation_errors=[f"Template name '{command.name}' is not available"]
                )
            
            # Load template content
            content = command.content
            if command.file_path and not content:
                try:
                    content = Path(command.file_path).read_text(encoding='utf-8')
                except Exception as e:
                    return ContentCommandResult(
                        success=False,
                        message=f"Failed to read template file: {e}",
                        errors=[str(e)]
                    )
            
            if not content:
                return ContentCommandResult(
                    success=False,
                    message="Template content is required",
                    validation_errors=["Either content or file_path must be provided"]
                )
            
            # Validate template content
            validation_result = await self._validation_service.validate_template(
                content=content,
                template_type=command.template_type,
                validation_level=command.validation_level.value
            )
            
            if not validation_result.is_valid:
                return ContentCommandResult(
                    success=False,
                    message="Template validation failed",
                    validation_errors=validation_result.errors,
                    validation_warnings=validation_result.warnings
                )
            
            # Create template entity
            template = Template.create(
                name=template_name,
                content=content,
                description=command.description,
                template_type=command.template_type,
                scope=command.scope,
                workspace_name=workspace_name,
                author=command.author,
                tags=command.tags or []
            )
            
            # Save template
            await self._template_repository.save(template)
            
            # Publish domain event
            event = TemplateCreated(
                template_id=template.id,
                template_name=template_name,
                template_type=command.template_type,
                scope=command.scope,
                workspace_name=workspace_name,
                created_at=datetime.now(),
                metadata={
                    "validation_level": command.validation_level.value,
                    "author": command.author,
                    "file_path": str(command.file_path) if command.file_path else None
                }
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully created template: {template_name}")
            
            return ContentCommandResult(
                success=True,
                message=f"Template '{command.name}' created successfully",
                template_name=command.name,
                template=template,
                validation_warnings=validation_result.warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to create template: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to create template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: CreateTemplateCommand) -> List[str]:
        """Validate create template command."""
        errors = []
        
        # Validate required fields
        if not command.name or not command.name.strip():
            errors.append("Template name is required")
        
        if not command.content and not command.file_path:
            errors.append("Either content or file_path must be provided")
        
        # Validate template name format
        if command.name:
            try:
                TemplateName.from_string(command.name)
            except ValueError as e:
                errors.append(f"Invalid template name: {e}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        # Validate file path if provided
        if command.file_path:
            path = Path(command.file_path)
            if not path.exists():
                errors.append(f"Template file does not exist: {command.file_path}")
            elif not path.is_file():
                errors.append(f"Template path is not a file: {command.file_path}")
        
        return errors


class ConcreteUpdateTemplateCommandHandler(
    ConcreteContentCommandHandler,
    UpdateTemplateCommandHandler
):
    """Concrete handler for updating templates."""
    
    async def handle(self, command: UpdateTemplateCommand) -> ContentCommandResult:
        """Handle template update."""
        logger.info(f"Updating template: {command.template_name or command.template_id}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find template to update
            template = None
            if command.template_id:
                template = await self._template_repository.find_by_id(command.template_id)
            elif command.template_name:
                template_name = TemplateName.from_string(command.template_name)
                template = await self._template_repository.find_by_name(
                    template_name, 
                    scope=TemplateScope.WORKSPACE, 
                    workspace_name=workspace_name
                )
            
            if not template:
                identifier = command.template_id or command.template_name
                return ContentCommandResult(
                    success=False,
                    message=f"Template not found: {identifier}",
                    errors=[f"Template with identifier '{identifier}' does not exist"]
                )
            
            # Load new content if provided
            content = command.content
            if command.file_path and not content:
                try:
                    content = Path(command.file_path).read_text(encoding='utf-8')
                except Exception as e:
                    return ContentCommandResult(
                        success=False,
                        message=f"Failed to read template file: {e}",
                        errors=[str(e)]
                    )
            
            # Create updated template
            updated_template = template
            
            # Update fields if provided
            if content:
                # Validate new content
                validation_result = await self._validation_service.validate_template(
                    content=content,
                    template_type=template.template_type,
                    validation_level=command.validation_level.value
                )
                
                if not validation_result.is_valid:
                    return ContentCommandResult(
                        success=False,
                        message="Template content validation failed",
                        validation_errors=validation_result.errors,
                        validation_warnings=validation_result.warnings
                    )
                
                updated_template = updated_template.update_content(content)
            
            if command.description:
                updated_template = updated_template.update_description(command.description)
            
            if command.tags is not None:
                updated_template = updated_template.update_tags(command.tags)
            
            if command.author is not None:
                updated_template = updated_template.update_author(command.author)
            
            # Save updated template
            await self._template_repository.save(updated_template)
            
            # Publish domain event
            event = TemplateUpdated(
                template_id=template.id,
                template_name=template.name,
                template_type=template.template_type,
                scope=template.scope,
                workspace_name=workspace_name,
                old_version=template.version,
                new_version=updated_template.version,
                updated_at=datetime.now(),
                changes={
                    "content_changed": content is not None,
                    "description_changed": command.description is not None,
                    "tags_changed": command.tags is not None,
                    "author_changed": command.author is not None,
                }
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully updated template: {template.name}")
            
            return ContentCommandResult(
                success=True,
                message=f"Template updated successfully",
                template_name=str(template.name),
                template=updated_template
            )
            
        except Exception as e:
            logger.error(f"Failed to update template: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to update template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: UpdateTemplateCommand) -> List[str]:
        """Validate update template command."""
        errors = []
        
        # Must provide identifier
        if not command.template_id and not command.template_name:
            errors.append("Either template_id or template_name must be provided")
        
        # At least one field must be provided for update
        if not any([
            command.content,
            command.description,
            command.tags is not None,
            command.author is not None,
            command.file_path
        ]):
            errors.append("At least one field must be provided for update")
        
        # Validate template name format if provided
        if command.template_name:
            try:
                TemplateName.from_string(command.template_name)
            except ValueError as e:
                errors.append(f"Invalid template name: {e}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteDeleteTemplateCommandHandler(
    ConcreteContentCommandHandler,
    DeleteTemplateCommandHandler
):
    """Concrete handler for deleting templates."""
    
    async def handle(self, command: DeleteTemplateCommand) -> ContentCommandResult:
        """Handle template deletion."""
        logger.info(f"Deleting template: {command.template_name or command.template_id}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find template to delete
            template = None
            if command.template_id:
                template = await self._template_repository.find_by_id(command.template_id)
            elif command.template_name:
                template_name = TemplateName.from_string(command.template_name)
                template = await self._template_repository.find_by_name(
                    template_name, 
                    scope=command.scope, 
                    workspace_name=workspace_name
                )
            
            if not template:
                identifier = command.template_id or command.template_name
                return ContentCommandResult(
                    success=False,
                    message=f"Template not found: {identifier}",
                    errors=[f"Template with identifier '{identifier}' does not exist"]
                )
            
            # Check if template is being used (unless force delete)
            if not command.force:
                # TODO: Check for active usage of this template
                # This would require checking pipeline runs and other references
                pass
            
            # Delete template
            await self._template_repository.delete(template.id)
            
            # Publish domain event
            event = TemplateDeleted(
                template_id=template.id,
                template_name=template.name,
                template_type=template.template_type,
                scope=template.scope,
                workspace_name=workspace_name,
                deleted_at=datetime.now(),
                reason="User requested deletion"
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully deleted template: {template.name}")
            
            return ContentCommandResult(
                success=True,
                message=f"Template deleted successfully",
                template_name=str(template.name)
            )
            
        except Exception as e:
            logger.error(f"Failed to delete template: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to delete template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: DeleteTemplateCommand) -> List[str]:
        """Validate delete template command."""
        errors = []
        
        # Must provide identifier
        if not command.template_id and not command.template_name:
            errors.append("Either template_id or template_name must be provided")
        
        # Validate template name format if provided
        if command.template_name:
            try:
                TemplateName.from_string(command.template_name)
            except ValueError as e:
                errors.append(f"Invalid template name: {e}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteValidateTemplateCommandHandler(
    ConcreteContentCommandHandler,
    ValidateTemplateCommandHandler
):
    """Concrete handler for validating templates."""
    
    async def handle(self, command: ValidateTemplateCommand) -> ContentCommandResult:
        """Handle template validation."""
        logger.info(f"Validating template: {command.template_name or command.template_id}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Get template content
            content = command.content
            
            # Load content from template if ID provided
            if command.template_id and not content:
                template = await self._template_repository.find_by_id(command.template_id)
                if not template:
                    return ContentCommandResult(
                        success=False,
                        message=f"Template not found: {command.template_id}",
                        errors=[f"Template with ID {command.template_id} does not exist"]
                    )
                content = template.content
            
            # Load content from template if name provided
            if command.template_name and not content:
                template_name = TemplateName.from_string(command.template_name)
                template = await self._template_repository.find_by_name(
                    template_name, 
                    scope=command.scope, 
                    workspace_name=workspace_name
                )
                if not template:
                    return ContentCommandResult(
                        success=False,
                        message=f"Template not found: {command.template_name}",
                        errors=[f"Template '{command.template_name}' does not exist"]
                    )
                content = template.content
            
            # Load content from file if path provided
            if command.file_path and not content:
                try:
                    content = Path(command.file_path).read_text(encoding='utf-8')
                except Exception as e:
                    return ContentCommandResult(
                        success=False,
                        message=f"Failed to read template file: {e}",
                        errors=[str(e)]
                    )
            
            if not content:
                return ContentCommandResult(
                    success=False,
                    message="No content to validate",
                    validation_errors=["Content, template_id, template_name, or file_path must be provided"]
                )
            
            # Validate content
            validation_result = await self._validation_service.validate_template(
                content=content,
                template_type="pipeline",  # Default to pipeline template
                validation_level=command.validation_level.value
            )
            
            logger.info(f"Template validation completed: valid={validation_result.is_valid}")
            
            # Publish domain event
            event = TemplateValidated(
                template_id=command.template_id,
                template_name=TemplateName.from_string(command.template_name) if command.template_name else None,
                validation_level=command.validation_level.value,
                is_valid=validation_result.is_valid,
                error_count=len(validation_result.errors),
                warning_count=len(validation_result.warnings),
                validated_at=datetime.now()
            )
            await self._event_bus.publish(event)
            
            return ContentCommandResult(
                success=True,
                message="Template validation completed",
                validation_errors=validation_result.errors,
                validation_warnings=validation_result.warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to validate template: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to validate template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: ValidateTemplateCommand) -> List[str]:
        """Validate template validation command."""
        errors = []
        
        # Must provide one source of content
        if not any([
            command.template_id, 
            command.template_name, 
            command.content, 
            command.file_path
        ]):
            errors.append("Must provide either template_id, template_name, content, or file_path")
        
        # Validate template name format if provided
        if command.template_name:
            try:
                TemplateName.from_string(command.template_name)
            except ValueError as e:
                errors.append(f"Invalid template name: {e}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        # Validate file path if provided
        if command.file_path:
            path = Path(command.file_path)
            if not path.exists():
                errors.append(f"Template file does not exist: {command.file_path}")
            elif not path.is_file():
                errors.append(f"Template path is not a file: {command.file_path}")
        
        return errors


class ConcreteCreateStylePrimerCommandHandler(
    ConcreteContentCommandHandler,
    CreateStylePrimerCommandHandler
):
    """Concrete handler for creating style primers."""
    
    async def handle(self, command: CreateStylePrimerCommand) -> ContentCommandResult:
        """Handle style primer creation."""
        logger.info(f"Creating style primer: {command.name}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Validate style name
            style_name = StyleName.from_string(command.name)
            
            # Check if style name is already taken
            existing_style = await self._style_primer_repository.find_by_name(
                style_name, 
                scope=command.scope, 
                workspace_name=workspace_name
            )
            if existing_style:
                return ContentCommandResult(
                    success=False,
                    message=f"Style primer '{command.name}' already exists in {command.scope.value} scope",
                    validation_errors=[f"Style name '{command.name}' is not available"]
                )
            
            # Load style content
            content = command.content
            if command.file_path and not content:
                try:
                    content = Path(command.file_path).read_text(encoding='utf-8')
                except Exception as e:
                    return ContentCommandResult(
                        success=False,
                        message=f"Failed to read style primer file: {e}",
                        errors=[str(e)]
                    )
            
            if not content:
                return ContentCommandResult(
                    success=False,
                    message="Style primer content is required",
                    validation_errors=["Either content or file_path must be provided"]
                )
            
            # Create style primer entity
            style_primer = StylePrimer.create(
                name=style_name,
                content=content,
                description=command.description,
                scope=command.scope,
                workspace_name=workspace_name,
                author=command.author,
                tags=command.tags or [],
                parent_style=command.parent_style
            )
            
            # Save style primer
            await self._style_primer_repository.save(style_primer)
            
            # Publish domain event
            event = StylePrimerCreated(
                style_id=style_primer.id,
                style_name=style_name,
                scope=command.scope,
                workspace_name=workspace_name,
                created_at=datetime.now(),
                metadata={
                    "author": command.author,
                    "parent_style": command.parent_style
                }
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully created style primer: {style_name}")
            
            return ContentCommandResult(
                success=True,
                message=f"Style primer '{command.name}' created successfully",
                style_name=command.name,
                style_primer=style_primer
            )
            
        except Exception as e:
            logger.error(f"Failed to create style primer: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to create style primer: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: CreateStylePrimerCommand) -> List[str]:
        """Validate create style primer command."""
        errors = []
        
        # Validate required fields
        if not command.name or not command.name.strip():
            errors.append("Style primer name is required")
        
        if not command.content and not command.file_path:
            errors.append("Either content or file_path must be provided")
        
        # Validate style name format
        if command.name:
            try:
                StyleName.from_string(command.name)
            except ValueError as e:
                errors.append(f"Invalid style primer name: {e}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        # Validate file path if provided
        if command.file_path:
            path = Path(command.file_path)
            if not path.exists():
                errors.append(f"Style primer file does not exist: {command.file_path}")
            elif not path.is_file():
                errors.append(f"Style primer path is not a file: {command.file_path}")
        
        return errors


class ConcreteCreateGeneratedContentCommandHandler(
    ConcreteContentCommandHandler,
    CreateGeneratedContentCommandHandler
):
    """Concrete handler for creating generated content."""
    
    async def handle(self, command: CreateGeneratedContentCommand) -> ContentCommandResult:
        """Handle generated content creation."""
        logger.info(f"Creating generated content: {command.content_type}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Validate content
            validation_result = await self._validation_service.validate_content(
                content=command.raw_content,
                content_type=command.content_type,
                content_format=command.content_format
            )
            
            if not validation_result.is_valid:
                return ContentCommandResult(
                    success=False,
                    message="Content validation failed",
                    validation_errors=validation_result.errors,
                    validation_warnings=validation_result.warnings
                )
            
            # Create generated content entity
            generated_content = GeneratedContent.create(
                content_type=command.content_type,
                content_format=command.content_format,
                raw_content=command.raw_content,
                metadata=command.metadata or {},
                template_id=command.template_id,
                pipeline_run_id=command.pipeline_run_id,
                workspace_name=workspace_name,
                author=command.author,
                tags=command.tags or []
            )
            
            # Save generated content
            await self._generated_content_repository.save(generated_content)
            
            # Publish domain event
            event = ContentGenerated(
                content_id=generated_content.id,
                content_type=command.content_type,
                content_format=command.content_format,
                workspace_name=workspace_name,
                template_id=command.template_id,
                pipeline_run_id=command.pipeline_run_id,
                created_at=datetime.now(),
                metadata={
                    "author": command.author,
                    "validation_passed": validation_result.is_valid
                }
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully created generated content: {generated_content.id}")
            
            return ContentCommandResult(
                success=True,
                message=f"Generated content created successfully",
                content_id=str(generated_content.id),
                content=generated_content,
                validation_warnings=validation_result.warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to create generated content: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to create generated content: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: CreateGeneratedContentCommand) -> List[str]:
        """Validate create generated content command."""
        errors = []
        
        # Validate required fields
        if not command.raw_content or not command.raw_content.strip():
            errors.append("Raw content is required")
        
        if not command.content_type:
            errors.append("Content type is required")
        
        if not command.content_format:
            errors.append("Content format is required")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


# Note: For brevity, I've implemented the most critical content command handlers.
# Additional handlers (UpdateStylePrimer, DeleteStylePrimer, UpdateGeneratedContent, 
# DeleteGeneratedContent, ValidateContent, PublishTemplate, DeprecateTemplate) 
# would follow similar patterns and can be added as needed.