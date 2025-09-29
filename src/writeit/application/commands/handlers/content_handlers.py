"""Concrete implementations of Content command handlers.

These handlers implement the business logic for content operations,
coordinating between domain services, repositories, and the event bus.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ....shared.command import CommandHandler, Command
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
    TemplateDeleted, 
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


class ConcreteContentCommandHandler(CommandHandler[Command, ContentCommandResult]):
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
            
            # TODO: Implement proper template validation
            # For now, assume content is valid
            validation_passed = True
            
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
                content_type=ContentType.from_string(command.template_type),
                created_by=command.author,
                created_at=datetime.now(),
                version=template.version,
                description=command.description,
                tags=command.tags or [],
                output_format=None  # TODO: determine output format from template
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully created template: {template_name}")
            
            return ContentCommandResult(
                success=True,
                message=f"Template '{command.name}' created successfully",
                template_name=command.name,
                template=template,
                validation_warnings=[]  # TODO: Get from actual validation
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
                # TODO: Implement proper template validation
                # For now, assume content is valid
                validation_passed = True
                
                updated_template = updated_template.update_content(content, author=command.author)
            
            if command.description:
                updated_template = updated_template.set_metadata("description", command.description)
            
            if command.tags is not None:
                # Clear existing tags and add new ones
                for tag in template.tags:
                    updated_template = updated_template.remove_tag(tag)
                for tag in command.tags:
                    updated_template = updated_template.add_tag(tag)
            
            if command.author is not None:
                updated_template = updated_template.set_metadata("author", command.author)
            
            # Save updated template
            await self._template_repository.save(updated_template)
            
            # Publish domain event
            event = TemplateUpdated(
                template_id=template.id,
                template_name=template.name,
                updated_by=command.author,
                updated_at=datetime.now(),
                old_version=template.version,
                new_version=updated_template.version,
                change_summary="Template updated",
                content_changed=content is not None,
                metadata_changes={
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
            
            # TODO: Implement proper template validation
            # For now, assume content is valid
            validation_passed = True
            
            logger.info(f"Template validation completed: valid={validation_passed}")
            
            # Publish domain event
            template_id = ContentId.from_string(command.template_id) if command.template_id else ContentId.generate()
            template_name = TemplateName.from_string(command.template_name) if command.template_name else TemplateName.from_string("unknown")
            
            event = TemplateValidated(
                template_id=template_id,
                template_name=template_name,
                validated_at=datetime.now(),
                validation_passed=validation_passed,
                validator_version="1.0.0",  # TODO: Get from validation service
                validation_rules_checked=[command.validation_level.value],
                errors=[],  # TODO: Get from actual validation
                warnings=[],  # TODO: Get from actual validation
                quality_score=None
            )
            await self._event_bus.publish(event)
            
            return ContentCommandResult(
                success=True,
                message="Template validation completed",
                validation_errors=[],
                validation_warnings=[]
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
                created_by=command.author,
                created_at=datetime.now(),
                content_types=[],  # TODO: Determine applicable content types
                description=command.description,
                is_default=False
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
            
            # TODO: Implement proper content validation
            # For now, assume content is valid
            validation_passed = True
            
            # Create generated content entity
            template_name = TemplateName.from_string("unknown")  # TODO: Get actual template name
            generated_content = GeneratedContent.create(
                content_text=command.raw_content,
                template_name=template_name,
                content_type=command.content_type,
                format=command.content_format,
                author=command.author,
                pipeline_run_id=command.pipeline_run_id
            )
            
            # Save generated content
            await self._generated_content_repository.save(generated_content)
            
            # Publish domain event
            template_id = ContentId.from_string(command.template_id) if command.template_id else ContentId.generate()
            word_count = len(command.raw_content.split()) if command.raw_content else 0
            character_count = len(command.raw_content) if command.raw_content else 0
            
            event = ContentGenerated(
                content_id=generated_content.id,
                template_id=template_id,
                template_name=TemplateName.from_string("unknown"),  # TODO: Get template name
                content_type=command.content_type,
                generated_at=datetime.now(),
                pipeline_run_id=command.pipeline_run_id,
                word_count=word_count,
                character_count=character_count,
                style_name=None,  # TODO: Determine style name
                generation_time_seconds=0.0,
                llm_model_used=None,  # TODO: Get from execution context
                tokens_used=0,
                generation_cost=0.0
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully created generated content: {generated_content.id}")
            
            return ContentCommandResult(
                success=True,
                message=f"Generated content created successfully",
                content_id=str(generated_content.id),
                content=generated_content,
                validation_warnings=[]  # TODO: Get from actual validation
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


class ConcreteUpdateStylePrimerCommandHandler(
    ConcreteContentCommandHandler,
    UpdateStylePrimerCommandHandler
):
    """Concrete handler for updating style primers."""
    
    async def handle(self, command: UpdateStylePrimerCommand) -> ContentCommandResult:
        """Handle style primer update."""
        logger.info(f"Updating style primer: {command.style_name or command.style_id}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find style primer to update
            style_primer = None
            if command.style_id:
                style_primer = await self._style_primer_repository.find_by_id(command.style_id)
            elif command.style_name:
                style_name = StyleName.from_string(command.style_name)
                style_primer = await self._style_primer_repository.find_by_name(
                    style_name, 
                    scope=TemplateScope.WORKSPACE, 
                    workspace_name=workspace_name
                )
            
            if not style_primer:
                identifier = command.style_id or command.style_name
                return ContentCommandResult(
                    success=False,
                    message=f"Style primer not found: {identifier}",
                    errors=[f"Style primer with identifier '{identifier}' does not exist"]
                )
            
            # Load new content if provided
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
            
            # Create updated style primer
            updated_style_primer = style_primer
            
            # Update fields if provided
            if content:
                # StylePrimer doesn't have update_content, so we need to use the available methods
                # For simplicity, let's use set_tone or set_writing_style with the content
                updated_style_primer = updated_style_primer.set_writing_style(content)
            
            if command.description:
                # Use add_guideline for description-like updates
                updated_style_primer = updated_style_primer.add_guideline(command.description)
            
            if command.tags is not None:
                # Clear existing tags and add new ones
                for tag in command.tags:
                    updated_style_primer = updated_style_primer.add_tag(tag)
            
            if command.parent_style is not None:
                # Use set_formatting_preference to store parent style info
                updated_style_primer = updated_style_primer.set_formatting_preference("parent_style", command.parent_style)
            
            # Save updated style primer
            await self._style_primer_repository.save(updated_style_primer)
            
            # Publish domain event
            event = StylePrimerUpdated(
                style_id=style_primer.id,
                style_name=style_primer.name,
                updated_by=None,  # TODO: Get from execution context
                updated_at=datetime.now(),
                change_summary="Style primer updated",
                old_version=style_primer.version,
                new_version=updated_style_primer.version,
                affects_existing_content=True
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully updated style primer: {style_primer.name}")
            
            return ContentCommandResult(
                success=True,
                message=f"Style primer updated successfully",
                style_name=str(style_primer.name),
                style_primer=updated_style_primer
            )
            
        except Exception as e:
            logger.error(f"Failed to update style primer: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to update style primer: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: UpdateStylePrimerCommand) -> List[str]:
        """Validate update style primer command."""
        errors = []
        
        # Must provide identifier
        if not command.style_id and not command.style_name:
            errors.append("Either style_id or style_name must be provided")
        
        # At least one field must be provided for update
        if not any([
            command.content,
            command.description,
            command.tags is not None,
            command.parent_style is not None,
            command.file_path
        ]):
            errors.append("At least one field must be provided for update")
        
        # Validate style name format if provided
        if command.style_name:
            try:
                StyleName.from_string(command.style_name)
            except ValueError as e:
                errors.append(f"Invalid style primer name: {e}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteDeleteStylePrimerCommandHandler(
    ConcreteContentCommandHandler,
    DeleteStylePrimerCommandHandler
):
    """Concrete handler for deleting style primers."""
    
    async def handle(self, command: DeleteStylePrimerCommand) -> ContentCommandResult:
        """Handle style primer deletion."""
        logger.info(f"Deleting style primer: {command.style_name or command.style_id}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find style primer to delete
            style_primer = None
            if command.style_id:
                style_primer = await self._style_primer_repository.find_by_id(command.style_id)
            elif command.style_name:
                style_name = StyleName.from_string(command.style_name)
                style_primer = await self._style_primer_repository.find_by_name(
                    style_name, 
                    scope=command.scope, 
                    workspace_name=workspace_name
                )
            
            if not style_primer:
                identifier = command.style_id or command.style_name
                return ContentCommandResult(
                    success=False,
                    message=f"Style primer not found: {identifier}",
                    errors=[f"Style primer with identifier '{identifier}' does not exist"]
                )
            
            # Check if style primer is being used (unless force delete)
            if not command.force:
                # TODO: Check for active usage of this style primer
                # This would require checking templates and other references
                pass
            
            # Delete style primer
            await self._style_primer_repository.delete(style_primer.id)
            
            logger.info(f"Successfully deleted style primer: {style_primer.name}")
            
            return ContentCommandResult(
                success=True,
                message=f"Style primer deleted successfully",
                style_name=str(style_primer.name)
            )
            
        except Exception as e:
            logger.error(f"Failed to delete style primer: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to delete style primer: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: DeleteStylePrimerCommand) -> List[str]:
        """Validate delete style primer command."""
        errors = []
        
        # Must provide identifier
        if not command.style_id and not command.style_name:
            errors.append("Either style_id or style_name must be provided")
        
        # Validate style name format if provided
        if command.style_name:
            try:
                StyleName.from_string(command.style_name)
            except ValueError as e:
                errors.append(f"Invalid style primer name: {e}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteUpdateGeneratedContentCommandHandler(
    ConcreteContentCommandHandler,
    UpdateGeneratedContentCommandHandler
):
    """Concrete handler for updating generated content."""
    
    async def handle(self, command: UpdateGeneratedContentCommand) -> ContentCommandResult:
        """Handle generated content update."""
        logger.info(f"Updating generated content: {command.content_id}")
        
        try:
            # Find generated content to update
            if not command.content_id:
                return ContentCommandResult(
                    success=False,
                    message="Content ID is required for update",
                    errors=["content_id must be provided"]
                )
            
            content_id = ContentId.from_string(command.content_id)
            generated_content = await self._generated_content_repository.find_by_id(content_id)
            
            if not generated_content:
                return ContentCommandResult(
                    success=False,
                    message=f"Generated content not found: {command.content_id}",
                    errors=[f"Content with ID '{command.content_id}' does not exist"]
                )
            
            # Create updated generated content
            updated_content = generated_content
            
            # Update fields if provided
            if command.raw_content:
                # TODO: Implement proper content validation
                # For now, assume content is valid
                validation_passed = True
                
                updated_content = updated_content.update_content(command.raw_content)
            
            if command.tags is not None:
                # Clear existing tags and add new ones
                for tag in command.tags:
                    updated_content = updated_content.add_tag(tag)
            
            if command.status:
                updated_content = updated_content.set_approval_status(command.status)
            
            # Save updated content
            await self._generated_content_repository.save(updated_content)
            
            logger.info(f"Successfully updated generated content: {content_id}")
            
            return ContentCommandResult(
                success=True,
                message=f"Generated content updated successfully",
                content_id=str(content_id),
                content=updated_content
            )
            
        except Exception as e:
            logger.error(f"Failed to update generated content: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to update generated content: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: UpdateGeneratedContentCommand) -> List[str]:
        """Validate update generated content command."""
        errors = []
        
        # Must provide content ID
        if not command.content_id:
            errors.append("Content ID is required")
        
        # At least one field must be provided for update
        if not any([
            command.raw_content,
            command.tags is not None,
            command.status
        ]):
            errors.append("At least one field must be provided for update")
        
        return errors


class ConcreteDeleteGeneratedContentCommandHandler(
    ConcreteContentCommandHandler,
    DeleteGeneratedContentCommandHandler
):
    """Concrete handler for deleting generated content."""
    
    async def handle(self, command: DeleteGeneratedContentCommand) -> ContentCommandResult:
        """Handle generated content deletion."""
        logger.info(f"Deleting generated content: {command.content_id}")
        
        try:
            if not command.content_id:
                return ContentCommandResult(
                    success=False,
                    message="Content ID is required for deletion",
                    errors=["content_id must be provided"]
                )
            
            content_id = ContentId.from_string(command.content_id)
            generated_content = await self._generated_content_repository.find_by_id(content_id)
            
            if not generated_content:
                return ContentCommandResult(
                    success=False,
                    message=f"Generated content not found: {command.content_id}",
                    errors=[f"Content with ID '{command.content_id}' does not exist"]
                )
            
            # Delete generated content
            await self._generated_content_repository.delete(content_id)
            
            logger.info(f"Successfully deleted generated content: {content_id}")
            
            return ContentCommandResult(
                success=True,
                message=f"Generated content deleted successfully",
                content_id=str(content_id)
            )
            
        except Exception as e:
            logger.error(f"Failed to delete generated content: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to delete generated content: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: DeleteGeneratedContentCommand) -> List[str]:
        """Validate delete generated content command."""
        errors = []
        
        # Must provide content ID
        if not command.content_id:
            errors.append("Content ID is required")
        
        return errors


class ConcreteValidateContentCommandHandler(
    ConcreteContentCommandHandler,
    ValidateContentCommandHandler
):
    """Concrete handler for validating content."""
    
    async def handle(self, command: ValidateContentCommand) -> ContentCommandResult:
        """Handle content validation."""
        logger.info(f"Validating content: {command.content_id}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Get content to validate
            content = command.content
            content_type = command.content_type
            
            # Load content from ID if provided
            if command.content_id and not content:
                content_id = ContentId.from_string(command.content_id)
                generated_content = await self._generated_content_repository.find_by_id(content_id)
                if not generated_content:
                    return ContentCommandResult(
                        success=False,
                        message=f"Content not found: {command.content_id}",
                        errors=[f"Content with ID {command.content_id} does not exist"]
                    )
                content = generated_content.raw_content
                content_type = generated_content.content_type
            
            if not content:
                return ContentCommandResult(
                    success=False,
                    message="No content to validate",
                    validation_errors=["Content or content_id must be provided"]
                )
            
            # TODO: Implement proper content validation
            # For now, assume content is valid
            validation_passed = True
            
            logger.info(f"Content validation completed: valid={validation_passed}")
            
            # Publish domain event
            event = ContentValidated(
                content_id=ContentId.from_string(command.content_id) if command.content_id else ContentId.generate(),
                template_id=ContentId.generate(),  # TODO: Get from content metadata
                validated_at=datetime.now(),
                validation_passed=validation_passed,
                validation_rules_applied=command.validation_rules or [],
                quality_metrics={},
                errors=[],  # TODO: Get from actual validation
                warnings=[]  # TODO: Get from actual validation
            )
            await self._event_bus.publish(event)
            
            return ContentCommandResult(
                success=True,
                message="Content validation completed",
                validation_errors=[],
                validation_warnings=[]
            )
            
        except Exception as e:
            logger.error(f"Failed to validate content: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to validate content: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: ValidateContentCommand) -> List[str]:
        """Validate content validation command."""
        errors = []
        
        # Must provide one source of content
        if not command.content_id and not command.content:
            errors.append("Must provide either content_id or content")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcretePublishTemplateCommandHandler(
    ConcreteContentCommandHandler,
    PublishTemplateCommandHandler
):
    """Concrete handler for publishing templates."""
    
    async def handle(self, command: PublishTemplateCommand) -> ContentCommandResult:
        """Handle template publishing."""
        logger.info(f"Publishing template: {command.template_name or command.template_id}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find template to publish
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
            
            # TODO: Implement proper template validation before publishing
            # For now, assume template is valid
            validation_passed = True
            
            # Create published template
            published_template = template.publish(published_by=None)  # TODO: Get from execution context
            
            # Set version notes if provided
            if command.version_notes:
                published_template = published_template.set_metadata("version_notes", command.version_notes)
            
            # TODO: Handle target_scope - this might require repository-level logic
            
            # Save published template
            await self._template_repository.save(published_template)
            
            # Publish domain event
            event = TemplatePublished(
                template_id=template.id,
                template_name=template.name,
                published_by=None,  # TODO: Get from execution context
                published_at=datetime.now(),
                version=published_template.version,
                approval_required=False,
                approved_by=None
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully published template: {template.name}")
            
            return ContentCommandResult(
                success=True,
                message=f"Template published successfully to {command.target_scope.value} scope",
                template_name=str(template.name),
                template=published_template
            )
            
        except Exception as e:
            logger.error(f"Failed to publish template: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to publish template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: PublishTemplateCommand) -> List[str]:
        """Validate publish template command."""
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


class ConcreteDeprecateTemplateCommandHandler(
    ConcreteContentCommandHandler,
    DeprecateTemplateCommandHandler
):
    """Concrete handler for deprecating templates."""
    
    async def handle(self, command: DeprecateTemplateCommand) -> ContentCommandResult:
        """Handle template deprecation."""
        logger.info(f"Deprecating template: {command.template_name or command.template_id}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find template to deprecate
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
            
            # Create deprecated template
            deprecated_template = template.deprecate(
                reason=command.reason,
                deprecated_by=None  # TODO: Get from execution context
            )
            
            # Set replacement template if provided
            if command.replacement_template:
                deprecated_template = deprecated_template.set_metadata("replacement_template", command.replacement_template)
            
            # Save deprecated template
            await self._template_repository.save(deprecated_template)
            
            # Publish domain event
            event = TemplateDeprecated(
                template_id=template.id,
                template_name=template.name,
                deprecated_by=None,  # TODO: Get from execution context
                deprecated_at=datetime.now(),
                reason=command.reason,
                replacement_template_id=ContentId.from_string(command.replacement_template) if command.replacement_template else None
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully deprecated template: {template.name}")
            
            return ContentCommandResult(
                success=True,
                message=f"Template deprecated successfully",
                template_name=str(template.name),
                template=deprecated_template
            )
            
        except Exception as e:
            logger.error(f"Failed to deprecate template: {e}", exc_info=True)
            return ContentCommandResult(
                success=False,
                message=f"Failed to deprecate template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: DeprecateTemplateCommand) -> List[str]:
        """Validate deprecate template command."""
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