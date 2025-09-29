"""Concrete implementations of Workspace command handlers.

These handlers implement the business logic for workspace operations,
coordinating between domain services, repositories, and the event bus.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import zipfile
import tempfile

from ....shared.command import CommandHandler, Command
from ....shared.events import EventBus
from ....domains.workspace.entities import Workspace, WorkspaceConfiguration
from ....domains.workspace.repositories import WorkspaceRepository, WorkspaceConfigRepository
from ....domains.workspace.services import WorkspaceIsolationService, WorkspaceTemplateService
from ....domains.workspace.value_objects import WorkspaceName, WorkspacePath
from ....domains.workspace.events import (
    WorkspaceCreated, 
    WorkspaceActivated, 
    WorkspaceDeleted, 
    WorkspaceConfigUpdated,
    WorkspaceInitialized,
    WorkspaceArchived,
    WorkspaceRestored
)

from ..workspace_commands import (
    CreateWorkspaceCommand,
    SwitchWorkspaceCommand,
    DeleteWorkspaceCommand,
    ConfigureWorkspaceCommand,
    InitializeWorkspaceCommand,
    ArchiveWorkspaceCommand,
    RestoreWorkspaceCommand,
    CreateWorkspaceTemplateCommand,
    ApplyWorkspaceTemplateCommand,
    WorkspaceCommandResult,
    CreateWorkspaceCommandHandler,
    SwitchWorkspaceCommandHandler,
    DeleteWorkspaceCommandHandler,
    ConfigureWorkspaceCommandHandler,
    InitializeWorkspaceCommandHandler,
    ArchiveWorkspaceCommandHandler,
    RestoreWorkspaceCommandHandler,
    CreateWorkspaceTemplateCommandHandler,
    ApplyWorkspaceTemplateCommandHandler,
)

logger = logging.getLogger(__name__)


class ConcreteWorkspaceCommandHandler(CommandHandler[Command, WorkspaceCommandResult]):
    """Base class for concrete workspace command handlers."""
    
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        config_repository: WorkspaceConfigRepository,
        isolation_service: WorkspaceIsolationService,
        template_service: WorkspaceTemplateService,
        event_bus: EventBus,
    ):
        """Initialize handler with dependencies.
        
        Args:
            workspace_repository: Repository for workspace management
            config_repository: Repository for workspace configuration
            isolation_service: Service for workspace isolation
            template_service: Service for workspace template operations
            event_bus: Event bus for publishing domain events
        """
        self._workspace_repository = workspace_repository
        self._config_repository = config_repository
        self._isolation_service = isolation_service
        self._template_service = template_service
        self._event_bus = event_bus


class ConcreteCreateWorkspaceCommandHandler(
    ConcreteWorkspaceCommandHandler,
    CreateWorkspaceCommandHandler
):
    """Concrete handler for creating workspaces."""
    
    async def handle(self, command: CreateWorkspaceCommand) -> WorkspaceCommandResult:
        """Handle workspace creation."""
        logger.info(f"Creating workspace: {command.name}")
        
        try:
            # Validate workspace name
            workspace_name = WorkspaceName.from_string(command.name)
            
            # Check if workspace already exists
            existing_workspace = await self._workspace_repository.find_by_name(workspace_name)
            if existing_workspace:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Workspace '{command.name}' already exists",
                    errors=[f"Workspace name '{command.name}' is not available"]
                )
            
            # Create workspace entity
            workspace = Workspace.create(
                name=workspace_name,
                description=command.description,
                base_path=command.base_path,
                configuration=command.configuration or {}
            )
            
            # Save workspace
            await self._workspace_repository.save(workspace)
            
            # Initialize workspace if requested
            if command.initialize_storage:
                await self._isolation_service.initialize_workspace_storage(workspace)
            
            # Copy global templates if requested
            if command.copy_global_templates:
                await self._template_service.copy_global_templates_to_workspace(workspace)
            
            # Apply initial template if provided
            if command.template_name:
                await self._template_service.apply_template_to_workspace(
                    workspace, command.template_name
                )
            
            # Publish domain event
            workspace_path = WorkspacePath.from_path(workspace.base_path) if workspace.base_path else WorkspacePath.from_path(Path.home() / ".writeit" / "workspaces" / str(workspace_name))
            
            event = WorkspaceCreated(
                workspace_name=workspace_name,
                workspace_path=workspace_path,
                created_by=None,  # TODO: Add user context
                created_at=datetime.now(),
                initial_config=command.configuration or {},
                is_default=False
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully created workspace: {workspace_name}")
            
            return WorkspaceCommandResult(
                success=True,
                message=f"Workspace '{command.name}' created successfully",
                workspace_id=str(workspace.id),
                workspace_name=command.name,
                workspace=workspace
            )
            
        except Exception as e:
            logger.error(f"Failed to create workspace: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to create workspace: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: CreateWorkspaceCommand) -> List[str]:
        """Validate create workspace command."""
        errors = []
        
        # Validate required fields
        if not command.name or not command.name.strip():
            errors.append("Workspace name is required")
        
        # Validate workspace name format
        if command.name:
            try:
                WorkspaceName.from_string(command.name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        # Validate base path if provided
        if command.base_path:
            if not command.base_path.exists():
                errors.append(f"Base path does not exist: {command.base_path}")
            elif not command.base_path.is_dir():
                errors.append(f"Base path is not a directory: {command.base_path}")
        
        return errors


class ConcreteSwitchWorkspaceCommandHandler(
    ConcreteWorkspaceCommandHandler,
    SwitchWorkspaceCommandHandler
):
    """Concrete handler for switching workspaces."""
    
    async def handle(self, command: SwitchWorkspaceCommand) -> WorkspaceCommandResult:
        """Handle workspace switching."""
        logger.info(f"Switching to workspace: {command.workspace_name}")
        
        try:
            # Get current active workspace
            current_workspace = await self._workspace_repository.get_active_workspace()
            
            # Parse target workspace name
            target_workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find target workspace
            target_workspace = await self._workspace_repository.find_by_name(target_workspace_name)
            if not target_workspace:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Workspace '{command.workspace_name}' not found",
                    errors=[f"Workspace '{command.workspace_name}' does not exist"]
                )
            
            # Validate workspace if requested
            if command.validate_workspace:
                validation_result = await self._isolation_service.validate_workspace_integrity(target_workspace)
                if not validation_result.is_valid:
                    return WorkspaceCommandResult(
                        success=False,
                        message=f"Workspace validation failed: {validation_result.error_message}",
                        errors=validation_result.errors
                    )
            
            # Save current workspace state if requested
            if command.save_current_state and current_workspace:
                await self._workspace_repository.save(current_workspace)
            
            # Switch active workspace
            await self._workspace_repository.set_active_workspace(target_workspace)
            
            # Publish domain event
            target_workspace_path = WorkspacePath.from_path(target_workspace.base_path) if target_workspace.base_path else WorkspacePath.from_path(Path.home() / ".writeit" / "workspaces" / str(target_workspace_name))
            
            event = WorkspaceActivated(
                workspace_name=target_workspace_name,
                workspace_path=target_workspace_path,
                activated_by=None,  # TODO: Add user context
                activated_at=datetime.now(),
                previous_workspace=current_workspace.name if current_workspace else None
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully switched to workspace: {target_workspace_name}")
            
            return WorkspaceCommandResult(
                success=True,
                message=f"Switched to workspace '{command.workspace_name}' successfully",
                workspace_id=str(target_workspace.id),
                workspace_name=command.workspace_name,
                workspace=target_workspace
            )
            
        except Exception as e:
            logger.error(f"Failed to switch workspace: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to switch workspace: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: SwitchWorkspaceCommand) -> List[str]:
        """Validate switch workspace command."""
        errors = []
        
        if not command.workspace_name or not command.workspace_name.strip():
            errors.append("Workspace name is required")
        
        # Validate workspace name format
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteDeleteWorkspaceCommandHandler(
    ConcreteWorkspaceCommandHandler,
    DeleteWorkspaceCommandHandler
):
    """Concrete handler for deleting workspaces."""
    
    async def handle(self, command: DeleteWorkspaceCommand) -> WorkspaceCommandResult:
        """Handle workspace deletion."""
        logger.info(f"Deleting workspace: {command.workspace_name}")
        
        try:
            # Parse workspace name
            workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find workspace
            workspace = await self._workspace_repository.find_by_name(workspace_name)
            if not workspace:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Workspace '{command.workspace_name}' not found",
                    errors=[f"Workspace '{command.workspace_name}' does not exist"]
                )
            
            # Check if workspace is currently active
            is_active = await self._workspace_repository.is_active_workspace(workspace)
            if is_active and not command.force:
                return WorkspaceCommandResult(
                    success=False,
                    message="Cannot delete active workspace",
                    errors=["Workspace is currently active. Switch to another workspace first."]
                )
            
            # Backup workspace if requested
            if command.backup_before_delete:
                backup_result = await self._backup_workspace(workspace)
                if not backup_result.success:
                    return WorkspaceCommandResult(
                        success=False,
                        message="Failed to backup workspace before deletion",
                        errors=backup_result.errors
                    )
            
            # Delete workspace storage
            await self._isolation_service.cleanup_workspace_storage(workspace)
            
            # Delete workspace configuration
            await self._config_repository.delete_by_workspace(workspace_name)
            
            # Delete workspace
            await self._workspace_repository.delete(workspace.id)
            
            # Publish domain event
            workspace_path = WorkspacePath.from_path(workspace.base_path) if workspace.base_path else WorkspacePath.from_path(Path.home() / ".writeit" / "workspaces" / str(workspace_name))
            
            event = WorkspaceDeleted(
                workspace_name=workspace_name,
                workspace_path=workspace_path,
                deleted_by=None,  # TODO: Add user context
                deleted_at=datetime.now(),
                reason="User requested deletion",
                backup_created=command.backup_before_delete,
                backup_location=None  # TODO: Add backup location if backup was created
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully deleted workspace: {workspace_name}")
            
            return WorkspaceCommandResult(
                success=True,
                message=f"Workspace '{command.workspace_name}' deleted successfully",
                workspace_id=str(workspace.id),
                workspace_name=command.workspace_name
            )
            
        except Exception as e:
            logger.error(f"Failed to delete workspace: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to delete workspace: {str(e)}",
                errors=[str(e)]
            )
    
    async def _backup_workspace(self, workspace: Workspace) -> WorkspaceCommandResult:
        """Create backup of workspace before deletion."""
        try:
            # Create backup directory
            backup_dir = Path.home() / ".writeit" / "backups" / f"{workspace.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Backup workspace data
            await self._isolation_service.backup_workspace_storage(workspace, backup_dir)
            
            logger.info(f"Workspace backup created: {backup_dir}")
            return WorkspaceCommandResult(
                success=True,
                message=f"Workspace backup created at {backup_dir}"
            )
            
        except Exception as e:
            logger.error(f"Failed to backup workspace: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to backup workspace: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: DeleteWorkspaceCommand) -> List[str]:
        """Validate delete workspace command."""
        errors = []
        
        if not command.workspace_name or not command.workspace_name.strip():
            errors.append("Workspace name is required")
        
        # Validate workspace name format
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteConfigureWorkspaceCommandHandler(
    ConcreteWorkspaceCommandHandler,
    ConfigureWorkspaceCommandHandler
):
    """Concrete handler for configuring workspaces."""
    
    async def handle(self, command: ConfigureWorkspaceCommand) -> WorkspaceCommandResult:
        """Handle workspace configuration."""
        logger.info(f"Configuring workspace: {command.workspace_name}")
        
        try:
            # Parse workspace name
            workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find workspace
            workspace = await self._workspace_repository.find_by_name(workspace_name)
            if not workspace:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Workspace '{command.workspace_name}' not found",
                    errors=[f"Workspace '{command.workspace_name}' does not exist"]
                )
            
            # Get current configuration
            current_config = await self._config_repository.find_by_workspace(workspace_name)
            
            # Create updated configuration
            if command.merge_with_existing and current_config:
                updated_config = current_config.merge_updates(command.configuration_updates)
            else:
                updated_config = WorkspaceConfiguration(
                    workspace_name=workspace_name,
                    settings=command.configuration_updates
                )
            
            # Validate configuration if requested
            if command.validate_configuration:
                validation_result = await self._isolation_service.validate_workspace_configuration(updated_config)
                if not validation_result.is_valid:
                    return WorkspaceCommandResult(
                        success=False,
                        message=f"Configuration validation failed: {validation_result.error_message}",
                        errors=validation_result.errors
                    )
            
            # Save configuration
            await self._config_repository.save(updated_config)
            
            # Update workspace with new configuration
            updated_workspace = workspace.update_configuration(updated_config.settings)
            await self._workspace_repository.save(updated_workspace)
            
            # Publish domain event
            workspace_path = WorkspacePath.from_path(workspace.base_path) if workspace.base_path else WorkspacePath.from_path(Path.home() / ".writeit" / "workspaces" / str(workspace_name))
            
            # Calculate config changes
            old_settings = current_config.settings if current_config else {}
            new_settings = updated_config.settings
            config_changes = {k: v for k, v in new_settings.items() if k not in old_settings or old_settings[k] != v}
            
            event = WorkspaceConfigUpdated(
                workspace_name=workspace_name,
                workspace_path=workspace_path,
                updated_by=None,  # TODO: Add user context
                updated_at=datetime.now(),
                config_changes=config_changes,
                old_config=old_settings,
                new_config=new_settings
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully configured workspace: {workspace_name}")
            
            return WorkspaceCommandResult(
                success=True,
                message=f"Workspace '{command.workspace_name}' configured successfully",
                workspace_id=str(workspace.id),
                workspace_name=command.workspace_name,
                workspace=updated_workspace,
                configuration=updated_config
            )
            
        except Exception as e:
            logger.error(f"Failed to configure workspace: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to configure workspace: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: ConfigureWorkspaceCommand) -> List[str]:
        """Validate configure workspace command."""
        errors = []
        
        if not command.workspace_name or not command.workspace_name.strip():
            errors.append("Workspace name is required")
        
        if not command.configuration_updates:
            errors.append("Configuration updates are required")
        
        # Validate workspace name format
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteInitializeWorkspaceCommandHandler(
    ConcreteWorkspaceCommandHandler,
    InitializeWorkspaceCommandHandler
):
    """Concrete handler for initializing workspaces."""
    
    async def handle(self, command: InitializeWorkspaceCommand) -> WorkspaceCommandResult:
        """Handle workspace initialization."""
        logger.info(f"Initializing workspace: {command.workspace_name}")
        
        try:
            # Parse workspace name
            workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find workspace
            workspace = await self._workspace_repository.find_by_name(workspace_name)
            if not workspace:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Workspace '{command.workspace_name}' not found",
                    errors=[f"Workspace '{command.workspace_name}' does not exist"]
                )
            
            # Create workspace directories if requested
            if command.create_directories:
                await self._isolation_service.create_workspace_directories(workspace)
            
            # Setup storage if requested
            if command.setup_storage:
                await self._isolation_service.initialize_workspace_storage(workspace)
            
            # Apply initial configuration if provided
            if command.configuration:
                config = WorkspaceConfiguration(
                    workspace_name=workspace_name,
                    settings=command.configuration
                )
                await self._config_repository.save(config)
            
            # Apply initial template if provided
            if command.template_name:
                await self._template_service.apply_template_to_workspace(
                    workspace, command.template_name
                )
            
            # Publish domain event
            workspace_path = WorkspacePath.from_path(workspace.base_path) if workspace.base_path else WorkspacePath.from_path(Path.home() / ".writeit" / "workspaces" / str(workspace_name))
            
            event = WorkspaceInitialized(
                workspace_name=workspace_name,
                workspace_path=workspace_path,
                initialized_by=None,  # TODO: Add user context
                initialized_at=datetime.now(),
                directories_created=["templates", "storage", "config"] if command.create_directories else [],
                templates_installed=[command.template_name] if command.template_name else [],
                config_file_path=str(workspace_path / "config" / "workspace.yaml")
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully initialized workspace: {workspace_name}")
            
            return WorkspaceCommandResult(
                success=True,
                message=f"Workspace '{command.workspace_name}' initialized successfully",
                workspace_id=str(workspace.id),
                workspace_name=command.workspace_name,
                workspace=workspace
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize workspace: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to initialize workspace: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: InitializeWorkspaceCommand) -> List[str]:
        """Validate initialize workspace command."""
        errors = []
        
        if not command.workspace_name or not command.workspace_name.strip():
            errors.append("Workspace name is required")
        
        # Validate workspace name format
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteArchiveWorkspaceCommandHandler(
    ConcreteWorkspaceCommandHandler,
    ArchiveWorkspaceCommandHandler
):
    """Concrete handler for archiving workspaces."""
    
    async def handle(self, command: ArchiveWorkspaceCommand) -> WorkspaceCommandResult:
        """Handle workspace archiving."""
        logger.info(f"Archiving workspace: {command.workspace_name}")
        
        try:
            # Parse workspace name
            workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find workspace
            workspace = await self._workspace_repository.find_by_name(workspace_name)
            if not workspace:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Workspace '{command.workspace_name}' not found",
                    errors=[f"Workspace '{command.workspace_name}' does not exist"]
                )
            
            # Determine archive path
            if command.archive_path:
                archive_path = command.archive_path
            else:
                archive_dir = Path.home() / ".writeit" / "archives"
                archive_dir.mkdir(parents=True, exist_ok=True)
                archive_path = archive_dir / f"{workspace.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            
            # Create archive
            await self._create_workspace_archive(
                workspace, 
                archive_path, 
                command.include_storage, 
                command.include_config,
                command.compression_level
            )
            
            # Publish domain event
            workspace_path = WorkspacePath.from_path(workspace.base_path) if workspace.base_path else WorkspacePath.from_path(Path.home() / ".writeit" / "workspaces" / str(workspace_name))
            archive_location = WorkspacePath.from_path(archive_path)
            
            event = WorkspaceArchived(
                workspace_name=workspace_name,
                workspace_path=workspace_path,
                archived_by=None,  # TODO: Add user context
                archived_at=datetime.now(),
                archive_location=archive_location,
                archive_format="zip",
                reason="User requested archive"
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully archived workspace: {workspace_name} -> {archive_path}")
            
            return WorkspaceCommandResult(
                success=True,
                message=f"Workspace '{command.workspace_name}' archived successfully",
                workspace_id=str(workspace.id),
                workspace_name=command.workspace_name
            )
            
        except Exception as e:
            logger.error(f"Failed to archive workspace: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to archive workspace: {str(e)}",
                errors=[str(e)]
            )
    
    async def _create_workspace_archive(
        self, 
        workspace: Workspace, 
        archive_path: Path, 
        include_storage: bool, 
        include_config: bool,
        compression_level: int
    ) -> None:
        """Create a zip archive of the workspace."""
        with zipfile.ZipFile(
            archive_path, 
            'w', 
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=compression_level
        ) as zipf:
            # Archive workspace metadata
            if workspace.base_path and workspace.base_path.exists():
                for file_path in workspace.base_path.rglob("*"):
                    if file_path.is_file():
                        arc_name = file_path.relative_to(workspace.base_path)
                        zipf.write(file_path, arc_name)
            
            # Archive storage if requested
            if include_storage:
                storage_path = await self._isolation_service.get_workspace_storage_path(workspace)
                if storage_path and storage_path.exists():
                    for file_path in storage_path.rglob("*"):
                        if file_path.is_file():
                            arc_name = f"storage/{file_path.relative_to(storage_path)}"
                            zipf.write(file_path, arc_name)
            
            # Archive configuration if requested
            if include_config:
                config = await self._config_repository.find_by_workspace(workspace.name)
                if config:
                    import json
                    zipf.writestr("config/workspace_config.json", json.dumps(config.settings, indent=2))
    
    async def validate(self, command: ArchiveWorkspaceCommand) -> List[str]:
        """Validate archive workspace command."""
        errors = []
        
        if not command.workspace_name or not command.workspace_name.strip():
            errors.append("Workspace name is required")
        
        # Validate workspace name format
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        # Validate archive path if provided
        if command.archive_path:
            if command.archive_path.exists() and not command.archive_path.is_file():
                errors.append(f"Archive path already exists and is not a file: {command.archive_path}")
        
        # Validate compression level
        if not 0 <= command.compression_level <= 9:
            errors.append("Compression level must be between 0 and 9")
        
        return errors


class ConcreteRestoreWorkspaceCommandHandler(
    ConcreteWorkspaceCommandHandler,
    RestoreWorkspaceCommandHandler
):
    """Concrete handler for restoring workspaces."""
    
    async def handle(self, command: RestoreWorkspaceCommand) -> WorkspaceCommandResult:
        """Handle workspace restoration."""
        logger.info(f"Restoring workspace from archive: {command.archive_path}")
        
        try:
            # Validate archive path
            if not command.archive_path.exists():
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Archive file not found: {command.archive_path}",
                    errors=[f"Archive file does not exist: {command.archive_path}"]
                )
            
            # Extract workspace name from archive or command
            workspace_name = command.workspace_name
            if not workspace_name:
                workspace_name = command.archive_path.stem.split('_')[0]  # Extract name from filename
            
            workspace_name_obj = WorkspaceName.from_string(workspace_name)
            
            # Check if workspace already exists
            existing_workspace = await self._workspace_repository.find_by_name(workspace_name_obj)
            if existing_workspace and not command.overwrite_existing:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Workspace '{workspace_name}' already exists",
                    errors=[f"Workspace name '{workspace_name}' is not available. Use overwrite_existing=True to replace."]
                )
            
            # Extract archive
            restore_path = command.restore_path or Path.home() / ".writeit" / "workspaces" / workspace_name
            await self._extract_workspace_archive(command.archive_path, restore_path)
            
            # Create or update workspace entity
            if existing_workspace and command.overwrite_existing:
                workspace = existing_workspace.update_base_path(restore_path)
            else:
                workspace = Workspace.create(
                    name=workspace_name_obj,
                    base_path=restore_path,
                    description="Restored from archive"
                )
            
            # Save workspace
            await self._workspace_repository.save(workspace)
            
            # Initialize workspace storage
            await self._isolation_service.initialize_workspace_storage(workspace)
            
            # Publish domain event
            workspace_path = WorkspacePath.from_path(restore_path)
            archive_source = WorkspacePath.from_path(command.archive_path)
            
            event = WorkspaceRestored(
                workspace_name=workspace_name_obj,
                workspace_path=workspace_path,
                restored_by=None,  # TODO: Add user context
                restored_at=datetime.now(),
                archive_source=archive_source,
                restoration_mode="full",
                overwrite_existing=command.overwrite_existing
            )
            await self._event_bus.publish(event)
            
            logger.info(f"Successfully restored workspace: {workspace_name}")
            
            return WorkspaceCommandResult(
                success=True,
                message=f"Workspace '{workspace_name}' restored successfully",
                workspace_id=str(workspace.id),
                workspace_name=workspace_name,
                workspace=workspace
            )
            
        except Exception as e:
            logger.error(f"Failed to restore workspace: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to restore workspace: {str(e)}",
                errors=[str(e)]
            )
    
    async def _extract_workspace_archive(self, archive_path: Path, restore_path: Path) -> None:
        """Extract workspace archive to restore path."""
        with zipfile.ZipFile(archive_path, 'r') as zipf:
            # Extract all files
            zipf.extractall(restore_path)
    
    async def validate(self, command: RestoreWorkspaceCommand) -> List[str]:
        """Validate restore workspace command."""
        errors = []
        
        if not command.archive_path:
            errors.append("Archive path is required")
        
        # Validate archive path
        if command.archive_path:
            if not command.archive_path.exists():
                errors.append(f"Archive file does not exist: {command.archive_path}")
            elif not command.archive_path.is_file():
                errors.append(f"Archive path is not a file: {command.archive_path}")
            elif not command.archive_path.suffix.lower() == '.zip':
                errors.append(f"Archive file must be a zip file: {command.archive_path}")
        
        # Validate workspace name if provided
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteCreateWorkspaceTemplateCommandHandler(
    ConcreteWorkspaceCommandHandler,
    CreateWorkspaceTemplateCommandHandler
):
    """Concrete handler for creating workspace templates."""
    
    async def handle(self, command: CreateWorkspaceTemplateCommand) -> WorkspaceCommandResult:
        """Handle workspace template creation."""
        logger.info(f"Creating workspace template from: {command.workspace_name}")
        
        try:
            # Parse workspace name
            workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find workspace
            workspace = await self._workspace_repository.find_by_name(workspace_name)
            if not workspace:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Workspace '{command.workspace_name}' not found",
                    errors=[f"Workspace '{command.workspace_name}' does not exist"]
                )
            
            # Create workspace template
            template_result = await self._template_service.create_workspace_template(
                workspace=workspace,
                template_name=command.template_name,
                description=command.description,
                include_configuration=command.include_configuration,
                include_templates=command.include_templates,
                include_storage_schema=command.include_storage_schema,
                is_global=command.is_global
            )
            
            if not template_result.success:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Failed to create workspace template: {template_result.message}",
                    errors=template_result.errors
                )
            
            logger.info(f"Successfully created workspace template: {command.template_name}")
            
            return WorkspaceCommandResult(
                success=True,
                message=f"Workspace template '{command.template_name}' created successfully",
                workspace_id=str(workspace.id),
                workspace_name=command.workspace_name,
                workspace=workspace
            )
            
        except Exception as e:
            logger.error(f"Failed to create workspace template: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to create workspace template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: CreateWorkspaceTemplateCommand) -> List[str]:
        """Validate create workspace template command."""
        errors = []
        
        if not command.workspace_name or not command.workspace_name.strip():
            errors.append("Workspace name is required")
        
        if not command.template_name or not command.template_name.strip():
            errors.append("Template name is required")
        
        # Validate workspace name format
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors


class ConcreteApplyWorkspaceTemplateCommandHandler(
    ConcreteWorkspaceCommandHandler,
    ApplyWorkspaceTemplateCommandHandler
):
    """Concrete handler for applying workspace templates."""
    
    async def handle(self, command: ApplyWorkspaceTemplateCommand) -> WorkspaceCommandResult:
        """Handle workspace template application."""
        logger.info(f"Applying template '{command.template_name}' to workspace: {command.workspace_name}")
        
        try:
            # Parse workspace name
            workspace_name = WorkspaceName.from_string(command.workspace_name)
            
            # Find workspace
            workspace = await self._workspace_repository.find_by_name(workspace_name)
            if not workspace:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Workspace '{command.workspace_name}' not found",
                    errors=[f"Workspace '{command.workspace_name}' does not exist"]
                )
            
            # Apply template to workspace
            template_result = await self._template_service.apply_template_to_workspace(
                workspace=workspace,
                template_name=command.template_name,
                merge_existing=command.merge_existing,
                override_conflicts=command.override_conflicts,
                apply_configuration=command.apply_configuration,
                apply_templates=command.apply_templates
            )
            
            if not template_result.success:
                return WorkspaceCommandResult(
                    success=False,
                    message=f"Failed to apply workspace template: {template_result.message}",
                    errors=template_result.errors
                )
            
            logger.info(f"Successfully applied template to workspace: {command.workspace_name}")
            
            return WorkspaceCommandResult(
                success=True,
                message=f"Template '{command.template_name}' applied to workspace '{command.workspace_name}' successfully",
                workspace_id=str(workspace.id),
                workspace_name=command.workspace_name,
                workspace=workspace
            )
            
        except Exception as e:
            logger.error(f"Failed to apply workspace template: {e}", exc_info=True)
            return WorkspaceCommandResult(
                success=False,
                message=f"Failed to apply workspace template: {str(e)}",
                errors=[str(e)]
            )
    
    async def validate(self, command: ApplyWorkspaceTemplateCommand) -> List[str]:
        """Validate apply workspace template command."""
        errors = []
        
        if not command.workspace_name or not command.workspace_name.strip():
            errors.append("Workspace name is required")
        
        if not command.template_name or not command.template_name.strip():
            errors.append("Template name is required")
        
        # Validate workspace name format
        if command.workspace_name:
            try:
                WorkspaceName.from_string(command.workspace_name)
            except ValueError as e:
                errors.append(f"Invalid workspace name: {e}")
        
        return errors