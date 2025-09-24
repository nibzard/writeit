"""Unit tests for WorkspaceManagementService.

Tests comprehensive workspace management operations including creation,
validation, migration, backup/restore, and lifecycle management.
"""

import pytest
import asyncio
import tempfile
import shutil
from typing import Dict, Any, List
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from writeit.domains.workspace.services.workspace_management_service import (
    WorkspaceManagementService,
    WorkspaceCreationOptions,
    WorkspaceMigrationPlan,
    WorkspaceBackupInfo,
    WorkspaceValidationError,
    WorkspaceAccessError,
    WorkspaceMigrationError
)
from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.shared.repository import EntityAlreadyExistsError, EntityNotFoundError, RepositoryError


class TestWorkspaceManagementService:
    """Test WorkspaceManagementService core functionality."""
    
    def test_create_service(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test creating workspace management service."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        assert service._workspace_repo == mock_workspace_repository
        assert service._config_repo == mock_workspace_config_repository
        assert service._backup_retention_days == 30
        assert "quick-article.yaml" in service._default_templates
        assert "tech-documentation.yaml" in service._default_templates
        assert "code-review.yaml" in service._default_templates
    
    @pytest.mark.asyncio
    async def test_create_workspace_success(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test successful workspace creation."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Setup mocks
        mock_workspace_repository.is_name_available = AsyncMock(return_value=True)
        mock_workspace_repository.is_path_available = AsyncMock(return_value=True)
        mock_workspace_repository.save = AsyncMock()
        mock_workspace_repository.set_active_workspace = AsyncMock()
        mock_config_repo_instance = Mock()
        mock_config_repo_instance.get_global_config = AsyncMock(return_value=WorkspaceConfiguration.default())
        mock_workspace_config_repository.get_global_config = AsyncMock(return_value=WorkspaceConfiguration.default())
        
        name = WorkspaceName("test-workspace")
        root_path = WorkspacePath.from_string(str(temp_dir / "test-workspace"))
        options = WorkspaceCreationOptions(set_as_active=True)
        
        # Configure the saved workspace to return from save
        saved_workspace = Mock()
        saved_workspace.name = name
        saved_workspace.root_path = root_path
        saved_workspace.is_active = True
        mock_workspace_repository.save.return_value = saved_workspace
        
        with patch.object(service, '_initialize_workspace_structure', new_callable=AsyncMock) as mock_init:
            workspace = await service.create_workspace(name, root_path, options)
            
            # Verify workspace was created correctly
            assert workspace == saved_workspace
            mock_workspace_repository.is_name_available.assert_called_once_with(name)
            mock_workspace_repository.is_path_available.assert_called_once_with(root_path)
            mock_workspace_repository.save.assert_called_once()
            mock_init.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_workspace_name_not_available(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test workspace creation fails when name not available."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Setup mocks
        mock_workspace_repository.is_name_available = AsyncMock(return_value=False)
        
        name = WorkspaceName("taken-workspace")
        root_path = WorkspacePath.from_string(str(temp_dir / "taken-workspace"))
        
        with pytest.raises(WorkspaceValidationError, match="already taken"):
            await service.create_workspace(name, root_path)
    
    @pytest.mark.asyncio
    async def test_create_workspace_path_not_available(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test workspace creation fails when path not available."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Setup mocks
        mock_workspace_repository.is_name_available = AsyncMock(return_value=True)
        mock_workspace_repository.is_path_available = AsyncMock(return_value=False)
        
        name = WorkspaceName("test-workspace")
        root_path = WorkspacePath.from_string(str(temp_dir / "taken-path"))
        
        with pytest.raises(WorkspaceValidationError, match="already in use"):
            await service.create_workspace(name, root_path)
    
    @pytest.mark.asyncio
    async def test_validate_workspace_integrity_success(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test successful workspace integrity validation."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create test workspace with valid structure
        workspace_path = temp_dir / "valid-workspace"
        workspace_path.mkdir()
        (workspace_path / "templates").mkdir()
        (workspace_path / "storage").mkdir()
        (workspace_path / "cache").mkdir()
        
        workspace = Mock()
        workspace.root_path = WorkspacePath.from_string(str(workspace_path))
        workspace.get_templates_path.return_value = WorkspacePath.from_string(str(workspace_path / "templates"))
        workspace.get_storage_path.return_value = WorkspacePath.from_string(str(workspace_path / "storage"))
        workspace.get_cache_path.return_value = WorkspacePath.from_string(str(workspace_path / "cache"))
        
        # Setup config repo mock
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=None)
        
        issues = await service.validate_workspace_integrity(workspace)
        
        # Should have no issues for valid workspace
        assert isinstance(issues, list)
        # Allow for some potential warnings but no critical errors
        if issues:
            assert all("ERROR" not in str(issue).upper() for issue in issues)
    
    @pytest.mark.asyncio
    async def test_validate_workspace_integrity_missing_directories(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test workspace validation detects missing directories."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create workspace with missing directories
        workspace_path = temp_dir / "incomplete-workspace" 
        # Don't create the directory to simulate missing structure
        
        workspace = Mock()
        workspace.root_path = WorkspacePath.from_string(str(workspace_path))
        workspace.get_templates_path.return_value = WorkspacePath.from_string(str(workspace_path / "templates"))
        workspace.get_storage_path.return_value = WorkspacePath.from_string(str(workspace_path / "storage"))
        workspace.get_cache_path.return_value = WorkspacePath.from_string(str(workspace_path / "cache"))
        
        # Setup config repo mock
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=None)
        
        issues = await service.validate_workspace_integrity(workspace)
        
        # Should detect missing directories
        assert len(issues) > 0
        assert any("missing" in issue.lower() for issue in issues)
    
    @pytest.mark.asyncio
    async def test_create_migration_plan(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test creating migration plan between workspaces."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create source and target workspaces
        source_path = temp_dir / "source"
        target_path = temp_dir / "target"
        source_path.mkdir()
        target_path.mkdir()
        
        source_workspace = Mock()
        source_workspace.name = WorkspaceName("source-workspace")
        source_workspace.get_size_on_disk.return_value = 1024 * 1024  # 1MB
        source_workspace.get_templates_path.return_value = WorkspacePath.from_string(str(source_path / "templates"))
        
        target_workspace = Mock()
        target_workspace.name = WorkspaceName("target-workspace")
        target_workspace.get_templates_path.return_value = WorkspacePath.from_string(str(target_path / "templates"))
        
        # Setup config mocks
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=None)
        
        plan = await service.create_migration_plan(source_workspace, target_workspace)
        
        assert isinstance(plan, WorkspaceMigrationPlan)
        assert plan.source_workspace == source_workspace
        assert plan.target_workspace == target_workspace
        assert isinstance(plan.migration_steps, list)
        assert len(plan.migration_steps) > 0
        assert isinstance(plan.estimated_duration, timedelta)
        assert plan.requires_backup is True
        assert isinstance(plan.conflicts, list)
    
    @pytest.mark.asyncio
    async def test_backup_workspace(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test workspace backup functionality."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create test workspace
        workspace_path = temp_dir / "backup-test"
        workspace_path.mkdir()
        (workspace_path / "templates").mkdir()
        (workspace_path / "test_file.txt").write_text("test content")
        
        workspace = Mock()
        workspace.name = WorkspaceName("backup-test")
        workspace.root_path = WorkspacePath.from_string(str(workspace_path))
        workspace.configuration = Mock()
        workspace.configuration.schema_version = "1.0.0"
        
        # Mock config repository
        mock_workspace_config_repository.find_by_workspace = AsyncMock(return_value=None)
        mock_workspace_config_repository.export_config = AsyncMock(return_value={"test": "config"})
        
        backup_path = WorkspacePath.from_string(str(temp_dir / "backup"))
        
        with patch.object(service, '_store_backup_metadata', new_callable=AsyncMock) as mock_store_meta:
            backup_info = await service.backup_workspace(workspace, backup_path)
            
            assert isinstance(backup_info, WorkspaceBackupInfo)
            assert backup_info.workspace_name == workspace.name
            assert backup_info.backup_path == backup_path
            assert isinstance(backup_info.created_at, datetime)
            assert backup_info.size_bytes > 0
            assert len(backup_info.checksum) > 0
            assert isinstance(backup_info.metadata, dict)
            mock_store_meta.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restore_workspace(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test workspace restore functionality."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create backup directory structure
        backup_path = temp_dir / "backup"
        backup_path.mkdir()
        workspace_data_path = backup_path / "workspace_data"
        workspace_data_path.mkdir()
        (workspace_data_path / "test_file.txt").write_text("restored content")
        
        backup_info = WorkspaceBackupInfo(
            workspace_name=WorkspaceName("restored-workspace"),
            backup_path=WorkspacePath.from_string(str(backup_path)),
            created_at=datetime.now(),
            size_bytes=1024,
            checksum="test-checksum",
            metadata={"test": "metadata"}
        )
        
        # Setup mocks
        mock_workspace_repository.find_by_name = AsyncMock(return_value=None)
        mock_workspace_repository.save = AsyncMock()
        saved_workspace = Mock()
        saved_workspace.name = backup_info.workspace_name
        mock_workspace_repository.save.return_value = saved_workspace
        
        target_path = WorkspacePath.from_string(str(temp_dir / "restored"))
        
        with patch.object(service, '_validate_backup_integrity', new_callable=AsyncMock):
            workspace = await service.restore_workspace(backup_info, target_path=target_path)
            
            assert workspace == saved_workspace
            mock_workspace_repository.find_by_name.assert_called_once_with(backup_info.workspace_name)
            mock_workspace_repository.save.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_restore_workspace_already_exists(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test workspace restore fails when target already exists."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        backup_info = WorkspaceBackupInfo(
            workspace_name=WorkspaceName("existing-workspace"),
            backup_path=WorkspacePath.from_string(str(temp_dir / "backup")),
            created_at=datetime.now(),
            size_bytes=1024,
            checksum="test-checksum",
            metadata={}
        )
        
        # Setup mock to return existing workspace
        existing_workspace = Mock()
        mock_workspace_repository.find_by_name = AsyncMock(return_value=existing_workspace)
        
        with patch.object(service, '_validate_backup_integrity', new_callable=AsyncMock):
            with pytest.raises(EntityAlreadyExistsError):
                await service.restore_workspace(backup_info)
    
    @pytest.mark.asyncio
    async def test_set_active_workspace(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test setting active workspace."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create test workspaces
        current_active = Mock()
        current_active.name = WorkspaceName("old-active")
        current_active.deactivate.return_value = Mock()
        
        new_active = Mock()
        new_active.name = WorkspaceName("new-active")
        new_active.activate.return_value = Mock()
        
        # Setup mocks
        mock_workspace_repository.find_active_workspace = AsyncMock(return_value=current_active)
        mock_workspace_repository.update = AsyncMock()
        mock_workspace_repository.set_active_workspace = AsyncMock()
        
        await service.set_active_workspace(new_active)
        
        # Verify deactivation of old workspace
        current_active.deactivate.assert_called_once()
        
        # Verify activation of new workspace
        new_active.activate.assert_called_once()
        
        # Verify repository calls
        assert mock_workspace_repository.update.call_count == 2  # Deactivate old, activate new
        mock_workspace_repository.set_active_workspace.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_workspace_success(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test successful workspace deletion."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create workspace directory
        workspace_path = temp_dir / "to-delete"
        workspace_path.mkdir()
        (workspace_path / "test_file.txt").write_text("content")
        
        workspace = Mock()
        workspace.name = WorkspaceName("to-delete")
        workspace.is_active = False
        workspace.root_path = WorkspacePath.from_string(str(workspace_path))
        
        mock_workspace_repository.delete = AsyncMock()
        
        with patch.object(service, 'backup_workspace', new_callable=AsyncMock) as mock_backup:
            result = await service.delete_workspace(workspace, backup_before_delete=True)
            
            assert result is True
            mock_backup.assert_called_once_with(workspace)
            mock_workspace_repository.delete.assert_called_once_with(workspace)
            assert not workspace_path.exists()
    
    @pytest.mark.asyncio
    async def test_delete_workspace_active_without_force(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test deletion fails for active workspace without force."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        workspace = Mock()
        workspace.is_active = True
        
        with pytest.raises(WorkspaceAccessError, match="Cannot delete active workspace"):
            await service.delete_workspace(workspace, force=False)
    
    @pytest.mark.asyncio
    async def test_cleanup_inactive_workspaces(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test cleanup of inactive workspaces."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create test workspaces
        old_inactive = Mock()
        old_inactive.name = WorkspaceName("old-inactive")
        old_inactive.is_active = False
        old_inactive.last_accessed = datetime.now() - timedelta(days=100)
        
        recent_inactive = Mock()
        recent_inactive.name = WorkspaceName("recent-inactive")
        recent_inactive.is_active = False
        recent_inactive.last_accessed = datetime.now() - timedelta(days=30)
        
        active_workspace = Mock()
        active_workspace.name = WorkspaceName("active")
        active_workspace.is_active = True
        
        all_workspaces = [old_inactive, recent_inactive, active_workspace]
        mock_workspace_repository.find_all = AsyncMock(return_value=all_workspaces)
        
        # Test dry run
        inactive_since = datetime.now() - timedelta(days=90)
        deleted_names = await service.cleanup_inactive_workspaces(
            inactive_since=inactive_since,
            dry_run=True
        )
        
        assert len(deleted_names) == 1
        assert deleted_names[0] == old_inactive.name
    
    @pytest.mark.asyncio
    async def test_migrate_workspace_success(self, mock_workspace_repository, mock_workspace_config_repository):
        """Test successful workspace migration."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        source_workspace = Mock()
        source_workspace.name = WorkspaceName("source")
        
        target_workspace = Mock() 
        target_workspace.name = WorkspaceName("target")
        
        migration_plan = WorkspaceMigrationPlan(
            source_workspace=source_workspace,
            target_workspace=target_workspace,
            migration_steps=["backup_source_data", "validate_migration"],
            estimated_duration=timedelta(minutes=5),
            requires_backup=True,
            conflicts=[]
        )
        
        with patch.object(service, 'backup_workspace', new_callable=AsyncMock) as mock_backup, \
             patch.object(service, 'validate_workspace_integrity', new_callable=AsyncMock) as mock_validate, \
             patch.object(service, '_execute_migration_steps', new_callable=AsyncMock) as mock_execute:
            
            mock_validate.return_value = []  # No validation issues
            mock_execute.return_value = target_workspace
            
            result = await service.migrate_workspace(source_workspace, target_workspace, migration_plan)
            
            assert result == target_workspace
            mock_backup.assert_called_once_with(source_workspace)
            mock_execute.assert_called_once_with(migration_plan)
            mock_validate.assert_called_once_with(target_workspace)


class TestWorkspaceCreationOptions:
    """Test WorkspaceCreationOptions behavior."""
    
    def test_default_options(self):
        """Test default workspace creation options."""
        options = WorkspaceCreationOptions()
        
        assert options.inherit_global_config is True
        assert options.create_default_templates is True
        assert options.initialize_storage is True
        assert options.set_as_active is False
        assert options.metadata is None
        assert options.permissions is None
    
    def test_custom_options(self):
        """Test custom workspace creation options."""
        metadata = {"key": "value"}
        permissions = {"read": True, "write": False}
        
        options = WorkspaceCreationOptions(
            inherit_global_config=False,
            create_default_templates=False,
            initialize_storage=False,
            set_as_active=True,
            metadata=metadata,
            permissions=permissions
        )
        
        assert options.inherit_global_config is False
        assert options.create_default_templates is False
        assert options.initialize_storage is False
        assert options.set_as_active is True
        assert options.metadata == metadata
        assert options.permissions == permissions


class TestWorkspaceMigrationPlan:
    """Test WorkspaceMigrationPlan behavior."""
    
    def test_create_migration_plan(self):
        """Test creating migration plan."""
        source = Mock()
        target = Mock()
        steps = ["step1", "step2"]
        duration = timedelta(minutes=10)
        
        plan = WorkspaceMigrationPlan(
            source_workspace=source,
            target_workspace=target,
            migration_steps=steps,
            estimated_duration=duration,
            requires_backup=True
        )
        
        assert plan.source_workspace == source
        assert plan.target_workspace == target
        assert plan.migration_steps == steps
        assert plan.estimated_duration == duration
        assert plan.requires_backup is True
        assert plan.conflicts == []  # Default empty list
    
    def test_migration_plan_with_conflicts(self):
        """Test migration plan with conflicts."""
        source = Mock()
        target = Mock()
        conflicts = ["conflict1", "conflict2"]
        
        plan = WorkspaceMigrationPlan(
            source_workspace=source,
            target_workspace=target,
            migration_steps=[],
            estimated_duration=timedelta(minutes=5),
            conflicts=conflicts
        )
        
        assert plan.conflicts == conflicts


class TestWorkspaceBackupInfo:
    """Test WorkspaceBackupInfo behavior."""
    
    def test_create_backup_info(self):
        """Test creating backup info."""
        name = WorkspaceName("test-backup")
        path = WorkspacePath.from_string("/backup/path")
        created_at = datetime.now()
        metadata = {"version": "1.0.0"}
        
        backup_info = WorkspaceBackupInfo(
            workspace_name=name,
            backup_path=path,
            created_at=created_at,
            size_bytes=1024,
            checksum="abc123",
            metadata=metadata
        )
        
        assert backup_info.workspace_name == name
        assert backup_info.backup_path == path
        assert backup_info.created_at == created_at
        assert backup_info.size_bytes == 1024
        assert backup_info.checksum == "abc123"
        assert backup_info.metadata == metadata


class TestWorkspaceManagementServicePrivateMethods:
    """Test private helper methods of WorkspaceManagementService."""
    
    def test_calculate_directory_size(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test directory size calculation."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create test directory with files
        test_dir = temp_dir / "size_test"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("Hello")  # 5 bytes
        (test_dir / "file2.txt").write_text("World")  # 5 bytes
        
        size = service._calculate_directory_size(WorkspacePath.from_string(str(test_dir)))
        
        assert size == 10  # 5 + 5 bytes
    
    @pytest.mark.asyncio
    async def test_calculate_directory_checksum(self, mock_workspace_repository, mock_workspace_config_repository, temp_dir):
        """Test directory checksum calculation."""
        service = WorkspaceManagementService(
            workspace_repository=mock_workspace_repository,
            config_repository=mock_workspace_config_repository
        )
        
        # Create test directory with files
        test_dir = temp_dir / "checksum_test"
        test_dir.mkdir()
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.txt").write_text("content2")
        
        checksum = await service._calculate_directory_checksum(WorkspacePath.from_string(str(test_dir)))
        
        assert isinstance(checksum, str)
        assert len(checksum) == 32  # MD5 hash length
        
        # Same directory should produce same checksum
        checksum2 = await service._calculate_directory_checksum(WorkspacePath.from_string(str(test_dir)))
        assert checksum == checksum2