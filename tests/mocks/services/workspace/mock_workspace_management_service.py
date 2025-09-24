"""Mock workspace management service for testing."""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.workspace.services.workspace_management_service import (
    WorkspaceManagementService,
    WorkspaceCreationOptions,
    WorkspaceMigrationPlan,
    WorkspaceBackupInfo,
    WorkspaceValidationError,
    WorkspaceAccessError,
    WorkspaceMigrationError
)
from writeit.shared.repository import EntityAlreadyExistsError, EntityNotFoundError


class MockWorkspaceManagementService(WorkspaceManagementService):
    """Mock implementation of WorkspaceManagementService for testing."""
    
    def __init__(self):
        """Initialize mock service with test data."""
        # Don't call super().__init__ to avoid dependency injection
        self._workspaces: Dict[WorkspaceName, Workspace] = {}
        self._active_workspace: Optional[Workspace] = None
        self._backups: List[WorkspaceBackupInfo] = []
        self._migration_plans: List[WorkspaceMigrationPlan] = []
        
        # Mock state for testing
        self._validation_issues: Dict[WorkspaceName, List[str]] = {}
        self._storage_issues: Dict[WorkspaceName, List[str]] = {}
        self._should_fail_creation = False
        self._should_fail_migration = False
        self._should_fail_backup = False
        
        # Setup default test workspaces
        self._setup_test_data()
    
    def _setup_test_data(self):
        """Setup default test data."""
        # Create default workspace
        default_workspace = Workspace.create(
            name=WorkspaceName.from_user_input("default"),
            root_path=WorkspacePath.from_string("/tmp/writeit/default"),
            configuration=WorkspaceConfiguration.default(),
            metadata={"created_by": "test", "test_workspace": True}
        )
        self._workspaces[default_workspace.name] = default_workspace
        self._active_workspace = default_workspace
        
        # Create project workspace
        project_workspace = Workspace.create(
            name=WorkspaceName.from_user_input("project1"),
            root_path=WorkspacePath.from_string("/tmp/writeit/project1"),
            configuration=WorkspaceConfiguration.default(),
            metadata={"project_type": "development", "test_workspace": True}
        )
        self._workspaces[project_workspace.name] = project_workspace
    
    # Mock control methods for testing
    
    def set_should_fail_creation(self, should_fail: bool):
        """Control whether create_workspace should fail."""
        self._should_fail_creation = should_fail
    
    def set_should_fail_migration(self, should_fail: bool):
        """Control whether migrate_workspace should fail."""
        self._should_fail_migration = should_fail
    
    def set_should_fail_backup(self, should_fail: bool):
        """Control whether backup_workspace should fail."""
        self._should_fail_backup = should_fail
    
    def add_validation_issue(self, workspace_name: WorkspaceName, issue: str):
        """Add validation issue for testing."""
        if workspace_name not in self._validation_issues:
            self._validation_issues[workspace_name] = []
        self._validation_issues[workspace_name].append(issue)
    
    def add_storage_issue(self, workspace_name: WorkspaceName, issue: str):
        """Add storage issue for testing."""
        if workspace_name not in self._storage_issues:
            self._storage_issues[workspace_name] = []
        self._storage_issues[workspace_name].append(issue)
    
    def get_workspace(self, name: WorkspaceName) -> Optional[Workspace]:
        """Get workspace by name for testing."""
        return self._workspaces.get(name)
    
    def list_workspaces(self) -> List[Workspace]:
        """List all workspaces for testing."""
        return list(self._workspaces.values())
    
    def get_active_workspace(self) -> Optional[Workspace]:
        """Get active workspace for testing."""
        return self._active_workspace
    
    # Implementation of WorkspaceManagementService interface
    
    async def create_workspace(
        self,
        name: WorkspaceName,
        root_path: WorkspacePath,
        options: Optional[WorkspaceCreationOptions] = None
    ) -> Workspace:
        """Create a new workspace with full initialization."""
        if self._should_fail_creation:
            raise WorkspaceValidationError("Forced creation failure for testing")
        
        if name in self._workspaces:
            raise EntityAlreadyExistsError(f"Workspace '{name}' already exists")
        
        if options is None:
            options = WorkspaceCreationOptions()
        
        # Create workspace
        config = WorkspaceConfiguration.default()
        if not options.inherit_global_config:
            config = WorkspaceConfiguration.default()
        
        workspace = Workspace.create(
            name=name,
            root_path=root_path,
            configuration=config,
            metadata=options.metadata or {}
        )
        
        # Store workspace
        self._workspaces[name] = workspace
        
        # Set as active if requested
        if options.set_as_active:
            await self.set_active_workspace(workspace)
        
        return workspace
    
    async def validate_workspace_integrity(self, workspace: Workspace) -> List[str]:
        """Validate workspace integrity and consistency."""
        issues = []
        
        # Return predefined issues for testing
        workspace_issues = self._validation_issues.get(workspace.name, [])
        issues.extend(workspace_issues)
        
        storage_issues = self._storage_issues.get(workspace.name, [])
        issues.extend(storage_issues)
        
        # Add some default checks
        if not workspace.root_path.exists():
            issues.append(f"Workspace directory does not exist: {workspace.root_path}")
        
        return issues
    
    async def migrate_workspace(
        self,
        source_workspace: Workspace,
        target_workspace: Workspace,
        migration_plan: Optional[WorkspaceMigrationPlan] = None
    ) -> Workspace:
        """Migrate workspace data and configuration."""
        if self._should_fail_migration:
            raise WorkspaceMigrationError("Forced migration failure for testing")
        
        if migration_plan is None:
            migration_plan = await self.create_migration_plan(source_workspace, target_workspace)
        
        # Simulate migration by copying workspace
        migrated_workspace = Workspace.create(
            name=target_workspace.name,
            root_path=target_workspace.root_path,
            configuration=source_workspace.configuration,
            metadata={**source_workspace.metadata, "migrated_from": str(source_workspace.name)}
        )
        
        # Store migrated workspace
        self._workspaces[target_workspace.name] = migrated_workspace
        
        return migrated_workspace
    
    async def create_migration_plan(
        self,
        source_workspace: Workspace,
        target_workspace: Workspace
    ) -> WorkspaceMigrationPlan:
        """Create a migration plan for workspace transition."""
        migration_steps = [
            "backup_source_data",
            "copy_pipeline_data",
            "copy_cache_data",
            "migrate_storage_data",
            "update_configuration",
            "validate_migration"
        ]
        
        # Simulate conflicts for testing
        conflicts = []
        if source_workspace.name == target_workspace.name:
            conflicts.append("Source and target workspaces have the same name")
        
        # Estimate duration (1 minute for testing)
        estimated_duration = timedelta(minutes=1)
        
        plan = WorkspaceMigrationPlan(
            source_workspace=source_workspace,
            target_workspace=target_workspace,
            migration_steps=migration_steps,
            estimated_duration=estimated_duration,
            requires_backup=True,
            conflicts=conflicts
        )
        
        self._migration_plans.append(plan)
        return plan
    
    async def backup_workspace(
        self,
        workspace: Workspace,
        backup_path: Optional[WorkspacePath] = None
    ) -> WorkspaceBackupInfo:
        """Create a complete backup of workspace data."""
        if self._should_fail_backup:
            raise WorkspaceAccessError("Forced backup failure for testing")
        
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = WorkspacePath.from_string(
                f"/tmp/workspace_backups/{workspace.name}_{timestamp}"
            )
        
        # Create mock backup info
        backup_info = WorkspaceBackupInfo(
            workspace_name=workspace.name,
            backup_path=backup_path,
            created_at=datetime.now(),
            size_bytes=1024 * 1024,  # 1MB for testing
            checksum="test_checksum_123",
            metadata={
                "workspace_version": workspace.configuration.schema_version,
                "backup_type": "full",
                "source_path": str(workspace.root_path),
                "test_backup": True
            }
        )
        
        self._backups.append(backup_info)
        return backup_info
    
    async def restore_workspace(
        self,
        backup_info: WorkspaceBackupInfo,
        target_name: Optional[WorkspaceName] = None,
        target_path: Optional[WorkspacePath] = None
    ) -> Workspace:
        """Restore workspace from backup."""
        if target_name is None:
            target_name = backup_info.workspace_name
        
        if target_path is None:
            target_path = WorkspacePath.from_string(f"/tmp/writeit/restored_{target_name}")
        
        # Check if target already exists
        if target_name in self._workspaces:
            raise EntityAlreadyExistsError(f"Workspace '{target_name}' already exists")
        
        # Create restored workspace
        config = WorkspaceConfiguration.default()
        workspace = Workspace.create(
            name=target_name,
            root_path=target_path,
            configuration=config,
            metadata={"restored_from_backup": str(backup_info.backup_path)}
        )
        
        # Store restored workspace
        self._workspaces[target_name] = workspace
        
        return workspace
    
    async def set_active_workspace(self, workspace: Workspace) -> None:
        """Set the active workspace."""
        # Deactivate current active workspace
        if self._active_workspace:
            deactivated = self._active_workspace.deactivate()
            self._workspaces[deactivated.name] = deactivated
        
        # Activate target workspace
        activated = workspace.activate()
        self._workspaces[activated.name] = activated
        self._active_workspace = activated
    
    async def delete_workspace(
        self,
        workspace: Workspace,
        force: bool = False,
        backup_before_delete: bool = True
    ) -> bool:
        """Delete a workspace and its data."""
        if workspace.is_active and not force:
            raise WorkspaceAccessError("Cannot delete active workspace (use force=True)")
        
        # Create backup if requested
        if backup_before_delete:
            await self.backup_workspace(workspace)
        
        # Remove from storage
        if workspace.name in self._workspaces:
            del self._workspaces[workspace.name]
        
        # Clear active workspace if this was it
        if self._active_workspace and self._active_workspace.name == workspace.name:
            self._active_workspace = None
        
        return True
    
    async def cleanup_inactive_workspaces(
        self,
        inactive_since: Optional[datetime] = None,
        dry_run: bool = False
    ) -> List[WorkspaceName]:
        """Clean up workspaces inactive since a given date."""
        if inactive_since is None:
            inactive_since = datetime.now() - timedelta(days=90)
        
        # Find inactive workspaces
        inactive_workspaces = [
            ws for ws in self._workspaces.values()
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
            except Exception:
                # Skip workspaces that fail to delete
                continue
        
        return deleted_names
    
    # Additional helper methods for testing
    
    def clear_all_workspaces(self):
        """Clear all workspaces for testing."""
        self._workspaces.clear()
        self._active_workspace = None
        self._backups.clear()
        self._migration_plans.clear()
    
    def get_backups(self) -> List[WorkspaceBackupInfo]:
        """Get all backups for testing."""
        return self._backups.copy()
    
    def get_migration_plans(self) -> List[WorkspaceMigrationPlan]:
        """Get all migration plans for testing."""
        return self._migration_plans.copy()
    
    def reset_mock_state(self):
        """Reset mock state for testing."""
        self._should_fail_creation = False
        self._should_fail_migration = False
        self._should_fail_backup = False
        self._validation_issues.clear()
        self._storage_issues.clear()
        self.clear_all_workspaces()
        self._setup_test_data()