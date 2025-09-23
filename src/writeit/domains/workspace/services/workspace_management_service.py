"""Workspace management service.

Provides comprehensive workspace lifecycle operations including
creation, validation, migration, backup/restore, and access control.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import shutil
import os

from ....shared.repository import EntityAlreadyExistsError, EntityNotFoundError, RepositoryError
from ..entities.workspace import Workspace
from ..entities.workspace_configuration import WorkspaceConfiguration
from ..value_objects.workspace_name import WorkspaceName
from ..value_objects.workspace_path import WorkspacePath
from ..repositories.workspace_repository import WorkspaceRepository
from ..repositories.workspace_config_repository import WorkspaceConfigRepository


class WorkspaceValidationError(Exception):
    """Raised when workspace validation fails."""
    pass


class WorkspaceAccessError(Exception):
    """Raised when workspace access is denied."""
    pass


class WorkspaceMigrationError(Exception):
    """Raised when workspace migration fails."""
    pass


@dataclass
class WorkspaceCreationOptions:
    """Options for workspace creation."""
    inherit_global_config: bool = True
    create_default_templates: bool = True
    initialize_storage: bool = True
    set_as_active: bool = False
    metadata: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, Any]] = None


@dataclass
class WorkspaceMigrationPlan:
    """Plan for workspace migration."""
    source_workspace: Workspace
    target_workspace: Workspace
    migration_steps: List[str]
    estimated_duration: timedelta
    requires_backup: bool = True
    conflicts: List[str] = None
    
    def __post_init__(self):
        if self.conflicts is None:
            self.conflicts = []


@dataclass
class WorkspaceBackupInfo:
    """Information about workspace backup."""
    workspace_name: WorkspaceName
    backup_path: WorkspacePath
    created_at: datetime
    size_bytes: int
    checksum: str
    metadata: Dict[str, Any]


class WorkspaceManagementService:
    """Service for managing workspace lifecycle operations.
    
    Provides comprehensive workspace management including creation,
    validation, migration, backup/restore, and access control.
    
    Examples:
        service = WorkspaceManagementService(workspace_repo, config_repo)
        
        # Create new workspace
        workspace = await service.create_workspace(
            name=WorkspaceName.from_user_input("my-project"),
            root_path=WorkspacePath.from_string("/path/to/workspace"),
            options=WorkspaceCreationOptions(set_as_active=True)
        )
        
        # Validate workspace integrity
        issues = await service.validate_workspace_integrity(workspace)
        
        # Migrate workspace
        plan = await service.create_migration_plan(old_workspace, new_workspace)
        await service.execute_migration(plan)
    """
    
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        config_repository: WorkspaceConfigRepository
    ) -> None:
        """Initialize workspace management service.
        
        Args:
            workspace_repository: Repository for workspace persistence
            config_repository: Repository for configuration management
        """
        self._workspace_repo = workspace_repository
        self._config_repo = config_repository
        self._default_templates = {
            "quick-article.yaml",
            "tech-documentation.yaml", 
            "code-review.yaml"
        }
        self._migration_handlers = {}
        self._backup_retention_days = 30
    
    async def create_workspace(
        self,
        name: WorkspaceName,
        root_path: WorkspacePath,
        options: Optional[WorkspaceCreationOptions] = None
    ) -> Workspace:
        """Create a new workspace with full initialization.
        
        Args:
            name: Workspace name
            root_path: Root directory path
            options: Creation options
            
        Returns:
            Created workspace
            
        Raises:
            WorkspaceValidationError: If workspace parameters are invalid
            WorkspaceAccessError: If workspace path is not accessible
            EntityAlreadyExistsError: If workspace name or path already exists
            RepositoryError: If creation operation fails
        """
        if options is None:
            options = WorkspaceCreationOptions()
        
        # Validate workspace parameters
        await self._validate_workspace_creation(name, root_path)
        
        # Create initial configuration
        if options.inherit_global_config:
            config = await self._config_repo.get_global_config()
        else:
            config = WorkspaceConfiguration.default()
        
        # Create workspace entity
        workspace = Workspace.create(
            name=name,
            root_path=root_path,
            configuration=config,
            metadata=options.metadata or {}
        )
        
        # Initialize workspace structure
        await self._initialize_workspace_structure(workspace, options)
        
        # Store workspace
        workspace = await self._workspace_repo.save(workspace)
        
        # Set as active if requested
        if options.set_as_active:
            await self.set_active_workspace(workspace)
        
        return workspace
    
    async def validate_workspace_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace integrity and consistency.
        
        Args:
            workspace: Workspace to validate
            
        Returns:
            List of validation issues, empty if valid
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If validation operation fails
        """
        issues = []
        
        # Basic structure validation
        issues.extend(await self._validate_directory_structure(workspace))
        
        # Configuration validation
        issues.extend(await self._validate_configuration_integrity(workspace))
        
        # Storage validation
        issues.extend(await self._validate_storage_integrity(workspace))
        
        # Template validation
        issues.extend(await self._validate_template_integrity(workspace))
        
        # Permission validation
        issues.extend(await self._validate_permissions(workspace))
        
        return issues
    
    async def migrate_workspace(
        self,
        source_workspace: Workspace,
        target_workspace: Workspace,
        migration_plan: Optional[WorkspaceMigrationPlan] = None
    ) -> Workspace:
        """Migrate workspace data and configuration.
        
        Args:
            source_workspace: Source workspace
            target_workspace: Target workspace
            migration_plan: Optional migration plan
            
        Returns:
            Migrated workspace
            
        Raises:
            WorkspaceMigrationError: If migration fails
            WorkspaceValidationError: If target workspace is invalid
            RepositoryError: If migration operation fails
        """
        if migration_plan is None:
            migration_plan = await self.create_migration_plan(source_workspace, target_workspace)
        
        # Validate migration plan
        await self._validate_migration_plan(migration_plan)
        
        # Create backup if required
        backup_info = None
        if migration_plan.requires_backup:
            backup_info = await self.backup_workspace(source_workspace)
        
        try:
            # Execute migration steps
            migrated_workspace = await self._execute_migration_steps(migration_plan)
            
            # Validate migrated workspace
            issues = await self.validate_workspace_integrity(migrated_workspace)
            if issues:
                raise WorkspaceMigrationError(f"Migration validation failed: {issues}")
            
            return migrated_workspace
            
        except Exception as e:
            # Restore from backup if migration fails
            if backup_info:
                await self._restore_from_backup(backup_info)
            raise WorkspaceMigrationError(f"Migration failed: {e}") from e
    
    async def create_migration_plan(
        self,
        source_workspace: Workspace,
        target_workspace: Workspace
    ) -> WorkspaceMigrationPlan:
        """Create a migration plan for workspace transition.
        
        Args:
            source_workspace: Source workspace
            target_workspace: Target workspace
            
        Returns:
            Migration plan with steps and analysis
            
        Raises:
            WorkspaceValidationError: If workspaces are invalid for migration
        """
        # Analyze workspace differences
        migration_steps = []
        conflicts = []
        
        # Check configuration differences
        source_config = await self._config_repo.find_by_workspace(source_workspace)
        target_config = await self._config_repo.find_by_workspace(target_workspace)
        
        if source_config and target_config:
            config_conflicts = await self._analyze_config_conflicts(source_config, target_config)
            conflicts.extend(config_conflicts)
            if config_conflicts:
                migration_steps.append("resolve_configuration_conflicts")
        
        # Check template conflicts
        template_conflicts = await self._analyze_template_conflicts(source_workspace, target_workspace)
        conflicts.extend(template_conflicts)
        if template_conflicts:
            migration_steps.append("merge_templates")
        
        # Add standard migration steps
        migration_steps.extend([
            "backup_source_data",
            "copy_pipeline_data",
            "copy_cache_data",
            "migrate_storage_data",
            "update_configuration",
            "validate_migration"
        ])
        
        # Estimate duration based on workspace size
        source_size = source_workspace.get_size_on_disk()
        estimated_duration = timedelta(minutes=max(5, source_size // (1024 * 1024 * 10)))  # ~10MB per minute
        
        return WorkspaceMigrationPlan(
            source_workspace=source_workspace,
            target_workspace=target_workspace,
            migration_steps=migration_steps,
            estimated_duration=estimated_duration,
            requires_backup=True,
            conflicts=conflicts
        )
    
    async def backup_workspace(
        self,
        workspace: Workspace,
        backup_path: Optional[WorkspacePath] = None
    ) -> WorkspaceBackupInfo:
        """Create a complete backup of workspace data.
        
        Args:
            workspace: Workspace to backup
            backup_path: Optional custom backup path
            
        Returns:
            Backup information
            
        Raises:
            WorkspaceAccessError: If backup operation fails
            RepositoryError: If backup metadata storage fails
        """
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = WorkspacePath.from_string(
                f"/tmp/workspace_backups/{workspace.name}_{timestamp}"
            )
        
        # Create backup directory
        backup_path.create_directories(exist_ok=True)
        
        # Backup workspace data
        await self._backup_workspace_data(workspace, backup_path)
        
        # Calculate backup size and checksum
        size_bytes = self._calculate_directory_size(backup_path)
        checksum = await self._calculate_directory_checksum(backup_path)
        
        # Create backup metadata
        backup_info = WorkspaceBackupInfo(
            workspace_name=workspace.name,
            backup_path=backup_path,
            created_at=datetime.now(),
            size_bytes=size_bytes,
            checksum=checksum,
            metadata={
                "workspace_version": workspace.configuration.schema_version,
                "backup_type": "full",
                "source_path": str(workspace.root_path)
            }
        )
        
        # Store backup metadata
        await self._store_backup_metadata(backup_info)
        
        return backup_info
    
    async def restore_workspace(
        self,
        backup_info: WorkspaceBackupInfo,
        target_name: Optional[WorkspaceName] = None,
        target_path: Optional[WorkspacePath] = None
    ) -> Workspace:
        """Restore workspace from backup.
        
        Args:
            backup_info: Backup information
            target_name: Optional target workspace name
            target_path: Optional target path
            
        Returns:
            Restored workspace
            
        Raises:
            WorkspaceValidationError: If backup is invalid
            EntityAlreadyExistsError: If target workspace exists
            RepositoryError: If restore operation fails
        """
        # Validate backup integrity
        await self._validate_backup_integrity(backup_info)
        
        # Determine target workspace details
        if target_name is None:
            target_name = backup_info.workspace_name
        
        if target_path is None:
            target_path = WorkspacePath.home_directory() / "workspaces" / str(target_name)
        
        # Check if target already exists
        existing_workspace = await self._workspace_repo.find_by_name(target_name)
        if existing_workspace:
            raise EntityAlreadyExistsError(f"Workspace '{target_name}' already exists")
        
        # Restore workspace data
        await self._restore_workspace_data(backup_info, target_path)
        
        # Create workspace entity
        config = WorkspaceConfiguration.default()
        workspace = Workspace.create(
            name=target_name,
            root_path=target_path,
            configuration=config
        )
        
        # Store restored workspace
        workspace = await self._workspace_repo.save(workspace)
        
        return workspace
    
    async def set_active_workspace(self, workspace: Workspace) -> None:
        """Set the active workspace.
        
        Args:
            workspace: Workspace to activate
            
        Raises:
            EntityNotFoundError: If workspace not found
            RepositoryError: If activation fails
        """
        # Deactivate current active workspace
        current_active = await self._workspace_repo.find_active_workspace()
        if current_active and current_active.name != workspace.name:
            deactivated = current_active.deactivate()
            await self._workspace_repo.update(deactivated)
        
        # Activate target workspace
        activated = workspace.activate()
        await self._workspace_repo.update(activated)
        await self._workspace_repo.set_active_workspace(activated)
    
    async def delete_workspace(
        self,
        workspace: Workspace,
        force: bool = False,
        backup_before_delete: bool = True
    ) -> bool:
        """Delete a workspace and its data.
        
        Args:
            workspace: Workspace to delete
            force: Force deletion even if workspace is active
            backup_before_delete: Create backup before deletion
            
        Returns:
            True if deletion successful
            
        Raises:
            WorkspaceAccessError: If workspace is active and force=False
            RepositoryError: If deletion operation fails
        """
        # Check if workspace is active
        if workspace.is_active and not force:
            raise WorkspaceAccessError("Cannot delete active workspace (use force=True)")
        
        # Create backup if requested
        if backup_before_delete:
            await self.backup_workspace(workspace)
        
        # Delete workspace data from filesystem
        if workspace.root_path.exists():
            shutil.rmtree(workspace.root_path.value)
        
        # Remove from repository
        await self._workspace_repo.delete(workspace)
        
        return True
    
    async def cleanup_inactive_workspaces(
        self,
        inactive_since: Optional[datetime] = None,
        dry_run: bool = False
    ) -> List[WorkspaceName]:
        """Clean up workspaces inactive since a given date.
        
        Args:
            inactive_since: Delete workspaces not accessed since this date
            dry_run: If True, only return names without deleting
            
        Returns:
            List of workspace names that were/would be deleted
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        if inactive_since is None:
            inactive_since = datetime.now() - timedelta(days=90)  # 3 months
        
        # Find inactive workspaces
        all_workspaces = await self._workspace_repo.find_all()
        inactive_workspaces = [
            ws for ws in all_workspaces
            if not ws.is_active and (
                ws.last_accessed is None or ws.last_accessed < inactive_since
            )
        ]
        
        if dry_run:
            return [ws.name for ws in inactive_workspaces]
        
        # Delete inactive workspaces
        deleted_names = []
        for workspace in inactive_workspaces:
            try:
                await self.delete_workspace(workspace, force=True, backup_before_delete=True)
                deleted_names.append(workspace.name)
            except Exception as e:
                # Log error but continue with other workspaces
                print(f"Failed to delete workspace {workspace.name}: {e}")
        
        return deleted_names
    
    # Private helper methods
    
    async def _validate_workspace_creation(
        self,
        name: WorkspaceName,
        root_path: WorkspacePath
    ) -> None:
        """Validate workspace creation parameters."""
        # Check name availability
        if not await self._workspace_repo.is_name_available(name):
            raise WorkspaceValidationError(f"Workspace name '{name}' is already taken")
        
        # Check path availability
        if not await self._workspace_repo.is_path_available(root_path):
            raise WorkspaceValidationError(f"Workspace path '{root_path}' is already in use")
        
        # Check path accessibility
        try:
            root_path.create_directories(exist_ok=True)
        except (OSError, PermissionError) as e:
            raise WorkspaceAccessError(f"Cannot create workspace directory: {e}")
    
    async def _initialize_workspace_structure(
        self,
        workspace: Workspace,
        options: WorkspaceCreationOptions
    ) -> None:
        """Initialize workspace directory structure and files."""
        # Create directory structure
        workspace.ensure_directory_structure()
        
        # Initialize storage if requested
        if options.initialize_storage:
            await self._initialize_storage(workspace)
        
        # Create default templates if requested
        if options.create_default_templates:
            await self._create_default_templates(workspace)
        
        # Set permissions if specified
        if options.permissions:
            await self._set_workspace_permissions(workspace, options.permissions)
    
    async def _initialize_storage(self, workspace: Workspace) -> None:
        """Initialize workspace storage directories."""
        storage_path = workspace.get_storage_path()
        
        # Create storage subdirectories
        subdirs = ["pipelines", "runs", "cache", "logs"]
        for subdir in subdirs:
            (storage_path.value / subdir).mkdir(exist_ok=True)
    
    async def _create_default_templates(self, workspace: Workspace) -> None:
        """Create default template files in workspace."""
        templates_path = workspace.get_templates_path()
        
        # Template content for quick article
        quick_article_content = """metadata:
  name: "Quick Article"
  description: "Generate a quick article on any topic"
  version: "1.0.0"

defaults:
  model: "gpt-4o-mini"

inputs:
  topic:
    type: text
    label: "Article Topic"
    required: true
    placeholder: "Enter the topic you want to write about..."

steps:
  content:
    name: "Generate Article"
    description: "Generate a comprehensive article"
    type: llm_generate
    prompt_template: |
      Write a comprehensive, well-structured article about {{ inputs.topic }}.
      
      The article should be:
      - Informative and engaging
      - Well-organized with clear sections
      - Approximately 800-1200 words
      - Include relevant examples where appropriate
      
      Format the article with proper headings and structure.
    model_preference: ["{{ defaults.model }}"]
"""
        
        # Write template file
        template_file = templates_path.value / "quick-article.yaml"
        template_file.write_text(quick_article_content)
    
    async def _validate_directory_structure(self, workspace: Workspace) -> List[str]:
        """Validate workspace directory structure."""
        issues = []
        
        required_dirs = [
            workspace.root_path,
            workspace.get_templates_path(),
            workspace.get_storage_path(),
            workspace.get_cache_path()
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                issues.append(f"Required directory missing: {dir_path}")
            elif not dir_path.is_directory():
                issues.append(f"Path is not a directory: {dir_path}")
        
        return issues
    
    async def _validate_configuration_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace configuration integrity."""
        issues = []
        
        try:
            config = await self._config_repo.find_by_workspace(workspace)
            if config:
                config_issues = await self._config_repo.validate_config(config)
                issues.extend(config_issues)
        except Exception as e:
            issues.append(f"Configuration validation failed: {e}")
        
        return issues
    
    async def _validate_storage_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace storage integrity."""
        issues = []
        
        storage_path = workspace.get_storage_path()
        if storage_path.exists():
            # Check for corrupted files
            try:
                for file_path in storage_path.value.rglob('*'):
                    if file_path.is_file() and file_path.suffix in ['.lmdb', '.db']:
                        # Basic file integrity check
                        if file_path.stat().st_size == 0:
                            issues.append(f"Empty storage file: {file_path}")
            except Exception as e:
                issues.append(f"Storage integrity check failed: {e}")
        
        return issues
    
    async def _validate_template_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace template integrity."""
        issues = []
        
        templates_path = workspace.get_templates_path()
        if templates_path.exists():
            try:
                for template_file in templates_path.value.glob('*.yaml'):
                    # Basic YAML syntax check
                    try:
                        import yaml
                        with open(template_file, 'r') as f:
                            yaml.safe_load(f)
                    except yaml.YAMLError as e:
                        issues.append(f"Invalid YAML in template {template_file.name}: {e}")
            except Exception as e:
                issues.append(f"Template validation failed: {e}")
        
        return issues
    
    async def _validate_permissions(self, workspace: Workspace) -> List[str]:
        """Validate workspace permissions."""
        issues = []
        
        # Check directory permissions
        if not os.access(workspace.root_path.value, os.R_OK | os.W_OK):
            issues.append(f"Insufficient permissions for workspace directory: {workspace.root_path}")
        
        return issues
    
    def _calculate_directory_size(self, directory: WorkspacePath) -> int:
        """Calculate total size of directory in bytes."""
        total_size = 0
        for file_path in directory.value.rglob('*'):
            if file_path.is_file():
                total_size += file_path.stat().st_size
        return total_size
    
    async def _calculate_directory_checksum(self, directory: WorkspacePath) -> str:
        """Calculate checksum for directory contents."""
        import hashlib
        
        hash_obj = hashlib.md5()
        for file_path in sorted(directory.value.rglob('*')):
            if file_path.is_file():
                with open(file_path, 'rb') as f:
                    hash_obj.update(f.read())
        
        return hash_obj.hexdigest()
    
    async def _backup_workspace_data(
        self,
        workspace: Workspace,
        backup_path: WorkspacePath
    ) -> None:
        """Backup workspace data to target path."""
        # Copy entire workspace directory
        shutil.copytree(
            workspace.root_path.value,
            backup_path.value / "workspace_data",
            dirs_exist_ok=True
        )
        
        # Export configuration
        config = await self._config_repo.find_by_workspace(workspace)
        if config:
            config_data = await self._config_repo.export_config(workspace)
            config_file = backup_path.value / "config.json"
            import json
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
    
    async def _restore_workspace_data(
        self,
        backup_info: WorkspaceBackupInfo,
        target_path: WorkspacePath
    ) -> None:
        """Restore workspace data from backup."""
        backup_data_path = backup_info.backup_path.value / "workspace_data"
        
        # Copy workspace data
        shutil.copytree(
            backup_data_path,
            target_path.value,
            dirs_exist_ok=True
        )
    
    async def _validate_backup_integrity(self, backup_info: WorkspaceBackupInfo) -> None:
        """Validate backup integrity."""
        if not backup_info.backup_path.exists():
            raise WorkspaceValidationError(f"Backup path does not exist: {backup_info.backup_path}")
        
        # Verify checksum
        current_checksum = await self._calculate_directory_checksum(backup_info.backup_path)
        if current_checksum != backup_info.checksum:
            raise WorkspaceValidationError("Backup checksum verification failed")
    
    async def _store_backup_metadata(self, backup_info: WorkspaceBackupInfo) -> None:
        """Store backup metadata for tracking."""
        metadata_file = backup_info.backup_path.value / "backup_metadata.json"
        
        metadata = {
            "workspace_name": str(backup_info.workspace_name),
            "created_at": backup_info.created_at.isoformat(),
            "size_bytes": backup_info.size_bytes,
            "checksum": backup_info.checksum,
            "metadata": backup_info.metadata
        }
        
        import json
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    async def _analyze_config_conflicts(
        self,
        source_config: WorkspaceConfiguration,
        target_config: WorkspaceConfiguration
    ) -> List[str]:
        """Analyze configuration conflicts between workspaces."""
        conflicts = []
        
        source_values = source_config.get_non_default_values()
        target_values = target_config.get_non_default_values()
        
        for key, source_value in source_values.items():
            if key in target_values and target_values[key] != source_value:
                conflicts.append(f"Configuration conflict for '{key}': {source_value} vs {target_values[key]}")
        
        return conflicts
    
    async def _analyze_template_conflicts(
        self,
        source_workspace: Workspace,
        target_workspace: Workspace
    ) -> List[str]:
        """Analyze template conflicts between workspaces."""
        conflicts = []
        
        source_templates = set()
        target_templates = set()
        
        # Get template lists
        source_templates_path = source_workspace.get_templates_path()
        if source_templates_path.exists():
            source_templates = {f.name for f in source_templates_path.value.glob('*.yaml')}
        
        target_templates_path = target_workspace.get_templates_path()
        if target_templates_path.exists():
            target_templates = {f.name for f in target_templates_path.value.glob('*.yaml')}
        
        # Find conflicts
        common_templates = source_templates & target_templates
        for template_name in common_templates:
            conflicts.append(f"Template conflict: {template_name} exists in both workspaces")
        
        return conflicts
    
    async def _validate_migration_plan(self, plan: WorkspaceMigrationPlan) -> None:
        """Validate migration plan."""
        if plan.source_workspace.name == plan.target_workspace.name:
            raise WorkspaceMigrationError("Source and target workspaces cannot be the same")
        
        if plan.conflicts and not any("resolve" in step for step in plan.migration_steps):
            raise WorkspaceMigrationError("Migration plan has conflicts but no resolution steps")
    
    async def _execute_migration_steps(self, plan: WorkspaceMigrationPlan) -> Workspace:
        """Execute migration steps."""
        for step in plan.migration_steps:
            if step == "backup_source_data":
                await self.backup_workspace(plan.source_workspace)
            elif step == "copy_pipeline_data":
                await self._copy_pipeline_data(plan.source_workspace, plan.target_workspace)
            elif step == "copy_cache_data":
                await self._copy_cache_data(plan.source_workspace, plan.target_workspace)
            elif step == "migrate_storage_data":
                await self._migrate_storage_data(plan.source_workspace, plan.target_workspace)
            elif step == "update_configuration":
                await self._merge_configurations(plan.source_workspace, plan.target_workspace)
            elif step == "validate_migration":
                issues = await self.validate_workspace_integrity(plan.target_workspace)
                if issues:
                    raise WorkspaceMigrationError(f"Migration validation failed: {issues}")
        
        return plan.target_workspace
    
    async def _copy_pipeline_data(self, source: Workspace, target: Workspace) -> None:
        """Copy pipeline data between workspaces."""
        source_pipelines = source.get_pipelines_path()
        target_pipelines = target.get_pipelines_path()
        
        if source_pipelines.exists():
            shutil.copytree(
                source_pipelines.value,
                target_pipelines.value,
                dirs_exist_ok=True
            )
    
    async def _copy_cache_data(self, source: Workspace, target: Workspace) -> None:
        """Copy cache data between workspaces."""
        source_cache = source.get_cache_path()
        target_cache = target.get_cache_path()
        
        if source_cache.exists():
            shutil.copytree(
                source_cache.value,
                target_cache.value,
                dirs_exist_ok=True
            )
    
    async def _migrate_storage_data(self, source: Workspace, target: Workspace) -> None:
        """Migrate storage data between workspaces."""
        source_storage = source.get_storage_path()
        target_storage = target.get_storage_path()
        
        if source_storage.exists():
            shutil.copytree(
                source_storage.value,
                target_storage.value,
                dirs_exist_ok=True
            )
    
    async def _merge_configurations(self, source: Workspace, target: Workspace) -> None:
        """Merge configurations between workspaces."""
        source_config = await self._config_repo.find_by_workspace(source)
        target_config = await self._config_repo.find_by_workspace(target)
        
        if source_config and target_config:
            merged_config = target_config.merge_with(source_config)
            await self._config_repo.update(merged_config)
    
    async def _set_workspace_permissions(
        self,
        workspace: Workspace,
        permissions: Dict[str, Any]
    ) -> None:
        """Set workspace permissions."""
        # Implementation would depend on the specific permission system
        # For now, just set basic directory permissions
        if "directory_mode" in permissions:
            os.chmod(workspace.root_path.value, permissions["directory_mode"])
    
    async def _restore_from_backup(self, backup_info: WorkspaceBackupInfo) -> None:
        """Restore workspace from backup after failed migration."""
        # This would implement the restore logic for migration rollback
        pass