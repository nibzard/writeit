"""Concrete implementations of Pipeline Template command handlers.

These handlers implement the business logic for pipeline template operations,
coordinating between domain services, repositories, and the event bus.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ....shared.command import CommandHandler
from ....shared.events import EventBus
from ....domains.pipeline.entities import PipelineTemplate
from ....domains.pipeline.repositories import PipelineTemplateRepository
from ....domains.pipeline.services import PipelineValidationService, PipelineExecutionService
from ....domains.pipeline.value_objects import PipelineId, PipelineName
from ....domains.workspace.value_objects import WorkspaceName
from ....domains.pipeline.events import PipelineCreated, PipelineUpdated, PipelineDeleted, PipelinePublished

from ..pipeline_commands import (
    CreatePipelineTemplateCommand,
    UpdatePipelineTemplateCommand,
    DeletePipelineTemplateCommand,
    PublishPipelineTemplateCommand,
    ValidatePipelineTemplateCommand,
    PipelineTemplateCommandResult,
    CreatePipelineTemplateCommandHandler,
    UpdatePipelineTemplateCommandHandler,
    DeletePipelineTemplateCommandHandler,
    PublishPipelineTemplateCommandHandler,
    ValidatePipelineTemplateCommandHandler,
)

logger = logging.getLogger(__name__)


class ConcretePipelineTemplateCommandHandler(CommandHandler[PipelineTemplateCommandResult]):
    """Base class for concrete pipeline template command handlers."""
    
    def __init__(
        self,
        template_repository: PipelineTemplateRepository,
        validation_service: PipelineValidationService,
        event_bus: EventBus,
    ):
        """Initialize handler with dependencies.
        
        Args:
            template_repository: Repository for pipeline templates
            validation_service: Service for template validation
            event_bus: Event bus for publishing domain events
        """
        self._template_repository = template_repository
        self._validation_service = validation_service
        self._event_bus = event_bus


class ConcreteCreatePipelineTemplateCommandHandler(
    ConcretePipelineTemplateCommandHandler,
    CreatePipelineTemplateCommandHandler
):
    """Concrete handler for creating pipeline templates."""
    
    async def handle(self, command: CreatePipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template creation."""
        logger.info(f"Creating pipeline template: {command.name}")
        
        try:
            # Parse workspace
            workspace_name = None
            if command.workspace_name:
                workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Validate template name is available
            pipeline_name = PipelineName.from_string(command.name)
            
            # Check if name is already taken
            existing_template = await self._template_repository.find_by_name(pipeline_name)
            if existing_template:
                return PipelineTemplateCommandResult(
                    success=False,
                    message=f"Pipeline template with name '{command.name}' already exists",
                    validation_errors=[f"Template name '{command.name}' is not available"]
                )
            
            # Load template content
            content = command.content
            if command.template_path and not content:
                try:
                    content = Path(command.template_path).read_text(encoding='utf-8')
                except Exception as e:
                    return PipelineTemplateCommandResult(
                        success=False,
                        message=f"Failed to read template file: {e}",
                        errors=[str(e)]
                    )
            
            if not content:
                return PipelineTemplateCommandResult(
                    success=False,
                    message="Template content is required",
                    validation_errors=["Either content or template_path must be provided"]
                )
            
            # Validate template content
            validation_result = await self._validation_service.validate_template_content(
                content=content,
                validation_level=command.validation_level
            )
            
            if not validation_result.is_valid:
                return PipelineTemplateCommandResult(
                    success=False,
                    message="Template validation failed",
                    validation_errors=validation_result.errors,
                    warnings=validation_result.warnings
                )
            
            # Create template entity
            pipeline_id = PipelineId.generate()
            template = PipelineTemplate.create(
                id=pipeline_id,
                name=pipeline_name,
                description=command.description,
                content=content,
                author=command.author,
                tags=command.tags or [],
                workspace_name=workspace_name,
            )
            
            # Save template
            await self._template_repository.save(template)
            
            # Publish domain event
            event = PipelineCreated(
                pipeline_id=pipeline_id,
                pipeline_name=pipeline_name,
                version=template.version,
                author=command.author,
                category=template.category,
                complexity=template.complexity,
                step_count=len(template.steps),
                created_at=datetime.now(),
                metadata={
                    "workspace": command.workspace_name,
                    "validation_level": command.validation_level,
                    "source": "command_handler"
                }
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully created pipeline template: {pipeline_id}")
            
            return PipelineTemplateCommandResult(
                success=True,
                message=f"Pipeline template '{command.name}' created successfully",
                pipeline_id=pipeline_id,
                template=template,
                warnings=validation_result.warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to create pipeline template: {e}", exc_info=True)
            return PipelineTemplateCommandResult(
                success=False,
                message=f"Failed to create pipeline template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: CreatePipelineTemplateCommand) -> List[str]:
        """Validate create pipeline template command."""
        errors = []
        
        # Validate required fields
        if not command.name or not command.name.strip():
            errors.append("Pipeline name is required")
        
        if not command.description or not command.description.strip():
            errors.append("Pipeline description is required")
        
        if not command.content and not command.template_path:
            errors.append("Either content or template_path must be provided")
        
        # Validate name format
        if command.name:
            try:
                PipelineName.from_string(command.name)
            except ValueError as e:
                errors.append(f"Invalid pipeline name: {e}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        # Validate template path if provided
        if command.template_path:
            path = Path(command.template_path)
            if not path.exists():
                errors.append(f"Template file does not exist: {command.template_path}")
            elif not path.is_file():
                errors.append(f"Template path is not a file: {command.template_path}")
        
        return errors


class ConcreteUpdatePipelineTemplateCommandHandler(
    ConcretePipelineTemplateCommandHandler,
    UpdatePipelineTemplateCommandHandler
):
    """Concrete handler for updating pipeline templates."""
    
    async def handle(self, command: UpdatePipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template update."""
        logger.info(f"Updating pipeline template: {command.pipeline_id}")
        
        try:
            # Find existing template
            template = await self._template_repository.find_by_id(command.pipeline_id)
            if not template:
                return PipelineTemplateCommandResult(
                    success=False,
                    message=f"Pipeline template not found: {command.pipeline_id}",
                    errors=[f"Template with ID {command.pipeline_id} does not exist"]
                )
            
            # Create updated template
            updated_template = template
            
            # Update fields if provided
            if command.name:
                pipeline_name = PipelineName.from_string(command.name)
                
                # Check if new name conflicts with existing template
                if pipeline_name != template.name:
                    existing = await self._template_repository.find_by_name(pipeline_name)
                    if existing and existing.id != template.id:
                        return PipelineTemplateCommandResult(
                            success=False,
                            message=f"Pipeline name '{command.name}' is already taken",
                            validation_errors=[f"Template name '{command.name}' conflicts with existing template"]
                        )
                
                updated_template = updated_template.update_name(pipeline_name)
            
            if command.description:
                updated_template = updated_template.update_description(command.description)
            
            if command.content:
                # Validate new content
                validation_result = await self._validation_service.validate_template_content(
                    content=command.content,
                    validation_level=command.validation_level
                )
                
                if not validation_result.is_valid:
                    return PipelineTemplateCommandResult(
                        success=False,
                        message="Template content validation failed",
                        validation_errors=validation_result.errors,
                        warnings=validation_result.warnings
                    )
                
                updated_template = updated_template.update_content(command.content)
            
            if command.author is not None:
                updated_template = updated_template.update_author(command.author)
            
            if command.tags is not None:
                updated_template = updated_template.update_tags(command.tags)
            
            # Save updated template
            await self._template_repository.save(updated_template)
            
            # Publish domain event
            event = PipelineUpdated(
                pipeline_id=command.pipeline_id,
                pipeline_name=updated_template.name,
                old_version=template.version,
                new_version=updated_template.version,
                author=command.author,
                changes={
                    "name_changed": command.name is not None,
                    "description_changed": command.description is not None,
                    "content_changed": command.content is not None,
                    "author_changed": command.author is not None,
                    "tags_changed": command.tags is not None,
                },
                updated_at=datetime.now()
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully updated pipeline template: {command.pipeline_id}")
            
            return PipelineTemplateCommandResult(
                success=True,
                message=f"Pipeline template updated successfully",
                pipeline_id=command.pipeline_id,
                template=updated_template
            )
            
        except Exception as e:
            logger.error(f"Failed to update pipeline template: {e}", exc_info=True)
            return PipelineTemplateCommandResult(
                success=False,
                message=f"Failed to update pipeline template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: UpdatePipelineTemplateCommand) -> List[str]:
        """Validate update pipeline template command."""
        errors = []
        
        # Validate pipeline ID
        if not command.pipeline_id:
            errors.append("Pipeline ID is required")
        
        # At least one field must be provided for update
        if not any([
            command.name,
            command.description,
            command.content,
            command.author is not None,
            command.tags is not None
        ]):
            errors.append("At least one field must be provided for update")
        
        # Validate name format if provided
        if command.name:
            try:
                PipelineName.from_string(command.name)
            except ValueError as e:
                errors.append(f"Invalid pipeline name: {e}")
        
        return errors


class ConcreteDeletePipelineTemplateCommandHandler(
    ConcretePipelineTemplateCommandHandler,
    DeletePipelineTemplateCommandHandler
):
    """Concrete handler for deleting pipeline templates."""
    
    async def handle(self, command: DeletePipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template deletion."""
        logger.info(f"Deleting pipeline template: {command.pipeline_id}")
        
        try:
            # Find existing template
            template = await self._template_repository.find_by_id(command.pipeline_id)
            if not template:
                return PipelineTemplateCommandResult(
                    success=False,
                    message=f"Pipeline template not found: {command.pipeline_id}",
                    errors=[f"Template with ID {command.pipeline_id} does not exist"]
                )
            
            # Check if template is being used (unless force delete)
            if not command.force:
                # TODO: Check for active pipeline runs using this template
                # This would require checking the pipeline run repository
                pass
            
            # Delete template
            await self._template_repository.delete(command.pipeline_id)
            
            # Publish domain event
            event = PipelineDeleted(
                pipeline_id=command.pipeline_id,
                pipeline_name=template.name,
                version=template.version,
                deleted_by=None,  # TODO: Extract from command context
                deleted_at=datetime.now(),
                reason="User requested deletion"
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully deleted pipeline template: {command.pipeline_id}")
            
            return PipelineTemplateCommandResult(
                success=True,
                message=f"Pipeline template deleted successfully",
                pipeline_id=command.pipeline_id
            )
            
        except Exception as e:
            logger.error(f"Failed to delete pipeline template: {e}", exc_info=True)
            return PipelineTemplateCommandResult(
                success=False,
                message=f"Failed to delete pipeline template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: DeletePipelineTemplateCommand) -> List[str]:
        """Validate delete pipeline template command."""
        errors = []
        
        if not command.pipeline_id:
            errors.append("Pipeline ID is required")
        
        return errors


class ConcretePublishPipelineTemplateCommandHandler(
    ConcretePipelineTemplateCommandHandler,
    PublishPipelineTemplateCommandHandler
):
    """Concrete handler for publishing pipeline templates."""
    
    async def handle(self, command: PublishPipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template publishing."""
        logger.info(f"Publishing pipeline template: {command.pipeline_id}")
        
        try:
            # Find existing template
            template = await self._template_repository.find_by_id(command.pipeline_id)
            if not template:
                return PipelineTemplateCommandResult(
                    success=False,
                    message=f"Pipeline template not found: {command.pipeline_id}",
                    errors=[f"Template with ID {command.pipeline_id} does not exist"]
                )
            
            # Validate template before publishing
            validation_result = await self._validation_service.validate_template_content(
                content=template.content,
                validation_level="strict"
            )
            
            if not validation_result.is_valid:
                return PipelineTemplateCommandResult(
                    success=False,
                    message="Template validation failed - cannot publish invalid template",
                    validation_errors=validation_result.errors,
                    warnings=validation_result.warnings
                )
            
            # Check target scope
            if command.target_scope == "global":
                # Publishing to global scope requires additional validation
                # TODO: Add global scope validation (permissions, naming conventions, etc.)
                pass
            
            # Publish template (mark as published)
            published_template = template.publish(target_scope=command.target_scope)
            
            # Save published template
            await self._template_repository.save(published_template)
            
            # Publish domain event
            event = PipelinePublished(
                pipeline_id=command.pipeline_id,
                pipeline_name=template.name,
                version=published_template.version,
                target_scope=command.target_scope,
                published_by=None,  # TODO: Extract from command context
                published_at=datetime.now(),
                metadata={
                    "workspace": command.workspace_name,
                    "validation_passed": True
                }
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully published pipeline template: {command.pipeline_id}")
            
            return PipelineTemplateCommandResult(
                success=True,
                message=f"Pipeline template published to {command.target_scope} scope successfully",
                pipeline_id=command.pipeline_id,
                template=published_template,
                warnings=validation_result.warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to publish pipeline template: {e}", exc_info=True)
            return PipelineTemplateCommandResult(
                success=False,
                message=f"Failed to publish pipeline template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: PublishPipelineTemplateCommand) -> List[str]:
        """Validate publish pipeline template command."""
        errors = []
        
        if not command.pipeline_id:
            errors.append("Pipeline ID is required")
        
        if command.target_scope not in ["workspace", "global"]:
            errors.append("Target scope must be 'workspace' or 'global'")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteValidatePipelineTemplateCommandHandler(
    ConcretePipelineTemplateCommandHandler,
    ValidatePipelineTemplateCommandHandler
):
    """Concrete handler for validating pipeline templates."""
    
    async def handle(self, command: ValidatePipelineTemplateCommand) -> PipelineTemplateCommandResult:
        """Handle pipeline template validation."""
        logger.info(f"Validating pipeline template")
        
        try:
            content = command.content
            
            # Load content from template if ID provided
            if command.pipeline_id and not content:
                template = await self._template_repository.find_by_id(command.pipeline_id)
                if not template:
                    return PipelineTemplateCommandResult(
                        success=False,
                        message=f"Pipeline template not found: {command.pipeline_id}",
                        errors=[f"Template with ID {command.pipeline_id} does not exist"]
                    )
                content = template.content
            
            # Load content from file if path provided
            if command.template_path and not content:
                try:
                    content = Path(command.template_path).read_text(encoding='utf-8')
                except Exception as e:
                    return PipelineTemplateCommandResult(
                        success=False,
                        message=f"Failed to read template file: {e}",
                        errors=[str(e)]
                    )
            
            if not content:
                return PipelineTemplateCommandResult(
                    success=False,
                    message="No content to validate",
                    validation_errors=["Content, pipeline_id, or template_path must be provided"]
                )
            
            # Validate content
            validation_result = await self._validation_service.validate_template_content(
                content=content,
                validation_level=command.validation_level
            )
            
            logger.info(f"Template validation completed: valid={validation_result.is_valid}")
            
            return PipelineTemplateCommandResult(
                success=True,
                message="Template validation completed",
                validation_errors=validation_result.errors,
                warnings=validation_result.warnings
            )
            
        except Exception as e:
            logger.error(f"Failed to validate pipeline template: {e}", exc_info=True)
            return PipelineTemplateCommandResult(
                success=False,
                message=f"Failed to validate pipeline template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: ValidatePipelineTemplateCommand) -> List[str]:
        """Validate the validation command itself."""
        errors = []
        
        # Must provide one source of content
        if not any([command.pipeline_id, command.content, command.template_path]):
            errors.append("Must provide either pipeline_id, content, or template_path")
        
        # Validate template path if provided
        if command.template_path:
            path = Path(command.template_path)
            if not path.exists():
                errors.append(f"Template file does not exist: {command.template_path}")
            elif not path.is_file():
                errors.append(f"Template path is not a file: {command.template_path}")
        
        return errors