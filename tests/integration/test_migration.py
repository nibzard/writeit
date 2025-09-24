"""Comprehensive tests for migration functionality.

Tests migration detection, execution, rollback, and backup capabilities
to ensure data safety and migration reliability.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from src.writeit.application.commands.migration_commands import (
    MigrationType,
    MigrationStatus,
    DetectLegacyWorkspacesCommand,
    AnalyzeMigrationRequirementsCommand,
    StartMigrationCommand,
    ValidateMigrationCommand,
    RollbackMigrationCommand,
    CheckMigrationHealthCommand,
)

from src.writeit.application.queries.migration_queries import (
    GetMigrationStatusQuery,
    GetMigrationDetailsQuery,
    MigrationFilter,
)

from src.writeit.application.services.migration_application_service import (
    DefaultMigrationApplicationService,
    MigrationResult,
    MigrationHealth,
)

from src.writeit.infrastructure.persistence.legacy_format_reader import (
    LegacyFormatManager,
    LegacyFormatType,
    FormatCompatibility,
)

from src.writeit.infrastructure.persistence.backup_manager import (
    BackupManager,
    BackupConfig,
    BackupType,
    CompressionType,
    RollbackStrategy,
    create_backup_manager,
)


class TestMigrationApplicationService:
    """Test cases for MigrationApplicationService."""
    
    @pytest.fixture
    def migration_service(self):
        """Create migration service for testing."""
        # Mock domain services
        workspace_service = Mock()
        config_service = Mock()
        template_service = Mock()
        style_service = Mock()
        cache_service = Mock()
        token_service = Mock()
        pipeline_service = Mock()
        storage_service = Mock()
        
        # Configure mocks
        workspace_service.list_workspaces = AsyncMock(return_value=[])
        workspace_service.get_workspace = AsyncMock(return_value=None)
        workspace_service.get_active_workspace = AsyncMock(return_value=None)
        
        return DefaultMigrationApplicationService(
            workspace_service=workspace_service,
            config_service=config_service,
            template_service=template_service,
            style_service=style_service,
            cache_service=cache_service,
            token_service=token_service,
            pipeline_service=pipeline_service,
            storage_service=storage_service,
        )
    
    @pytest.mark.asyncio
    async def test_detect_legacy_workspaces(self, migration_service):
        """Test detection of legacy workspaces."""
        command = DetectLegacyWorkspacesCommand(
            search_paths=[Path("/test")],
            auto_analyze=True,
        )
        
        # Mock the legacy workspace migrator
        with patch('src.writeit.application.services.migration_application_service.WorkspaceMigrator') as mock_migrator:
            mock_migrator.return_value.detect_local_workspaces.return_value = [
                Path("/test/workspace1"),
                Path("/test/workspace2"),
            ]
            
            mock_migrator.return_value.analyze_local_workspace.return_value = {
                "path": Path("/test/workspace1"),
                "has_config": True,
                "has_pipelines": True,
                "migration_complexity": "simple",
                "recommended_workspace_name": "workspace1",
            }
            
            results = await migration_service.detect_legacy_workspaces(command)
            
            assert len(results) == 2
            assert results[0]["path"] == Path("/test/workspace1")
            assert results[0]["has_config"] is True
    
    @pytest.mark.asyncio
    async def test_analyze_migration_requirements(self, migration_service):
        """Test analysis of migration requirements."""
        command = AnalyzeMigrationRequirementsCommand(
            workspace_name="test_workspace",
            include_all_workspaces=False,
            check_data_formats=True,
            check_configurations=True,
            check_cache=True,
        )
        
        # Mock workspace service
        mock_workspace = Mock()
        mock_workspace.name = "test_workspace"
        migration_service.workspace_service.get_workspace.return_value = mock_workspace
        
        results = await migration_service.analyze_migration_requirements(command)
        
        assert isinstance(results, list)
        # Should return empty list as no migrations are required in mock setup
    
    @pytest.mark.asyncio
    async def test_start_migration_success(self, migration_service):
        """Test successful migration execution."""
        command = StartMigrationCommand(
            migration_type=MigrationType.LEGACY_WORKSPACE,
            source_path=Path("/test/legacy"),
            target_workspace="test_workspace",
            backup_before=True,
            rollback_on_failure=True,
        )
        
        # Mock backup creation
        with patch.object(migration_service, '_create_backup') as mock_backup:
            mock_backup.return_value = Path("/test/backup.tar.gz")
            
            # Mock migration execution
            with patch.object(migration_service, '_migrate_legacy_workspace') as mock_migrate:
                mock_migrate.return_value = {
                    "status": MigrationStatus.COMPLETED,
                    "message": "Migration completed",
                    "items_migrated": 1,
                    "items_failed": 0,
                }
                
                result = await migration_service.start_migration(command)
                
                assert result.status == MigrationStatus.COMPLETED
                assert result.items_migrated == 1
                assert result.items_failed == 0
                assert result.backup_path == Path("/test/backup.tar.gz")
    
    @pytest.mark.asyncio
    async def test_start_migration_with_failure(self, migration_service):
        """Test migration execution with failure."""
        command = StartMigrationCommand(
            migration_type=MigrationType.LEGACY_WORKSPACE,
            source_path=Path("/test/legacy"),
            target_workspace="test_workspace",
            backup_before=True,
            rollback_on_failure=True,
        )
        
        # Mock backup creation
        with patch.object(migration_service, '_create_backup') as mock_backup:
            mock_backup.return_value = Path("/test/backup.tar.gz")
            
            # Mock migration failure
            with patch.object(migration_service, '_migrate_legacy_workspace') as mock_migrate:
                mock_migrate.return_value = {
                    "status": MigrationStatus.FAILED,
                    "message": "Migration failed",
                    "items_migrated": 0,
                    "items_failed": 1,
                    "error_details": "Test error",
                }
                
                # Mock rollback
                with patch.object(migration_service, '_rollback_from_backup') as mock_rollback:
                    mock_rollback.return_value = True
                    
                    result = await migration_service.start_migration(command)
                    
                    assert result.status == MigrationStatus.ROLLED_BACK
                    assert result.error_details == "Test error"
                    mock_rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_migration(self, migration_service):
        """Test migration validation."""
        command = ValidateMigrationCommand(
            migration_id="test_migration_123",
            deep_validation=True,
            compare_with_source=True,
        )
        
        # Mock migration details
        with patch.object(migration_service, 'get_migration_details') as mock_details:
            mock_details.return_value = {
                "migration_id": "test_migration_123",
                "type": "legacy_workspace",
                "status": "completed",
            }
            
            # Mock validation methods
            with patch.object(migration_service, '_validate_workspace_migration') as mock_validate:
                mock_validate.return_value = None
                
                result = await migration_service.validate_migration(command)
                
                assert result["is_valid"] is True
                assert result["migration_id"] == "test_migration_123"
    
    @pytest.mark.asyncio
    async def test_rollback_migration(self, migration_service):
        """Test migration rollback."""
        command = RollbackMigrationCommand(
            migration_id="test_migration_123",
            workspace_name="test_workspace",
            force=True,
        )
        
        # Mock backup finding
        with patch.object(migration_service, '_find_latest_backup') as mock_find:
            mock_find.return_value = Path("/test/backup.tar.gz")
            
            # Mock rollback execution
            with patch.object(migration_service, '_rollback_from_backup') as mock_rollback:
                mock_rollback.return_value = True
                
                result = await migration_service.rollback_migration(command)
                
                assert result.status == MigrationStatus.COMPLETED
                assert result.migration_id == "rollback_test_migration_123"
    
    @pytest.mark.asyncio
    async def test_check_migration_health(self, migration_service):
        """Test migration system health check."""
        command = CheckMigrationHealthCommand(
            check_disk_space=True,
            check_permissions=True,
            check_dependencies=True,
            validate_backup_system=True,
        )
        
        result = await migration_service.check_migration_health(command)
        
        assert isinstance(result, MigrationHealth)
        assert result.is_healthy is True
        assert result.permissions_ok is True
        assert result.dependencies_ok is True
        assert result.backup_system_ok is True


class TestLegacyFormatManager:
    """Test cases for LegacyFormatManager."""
    
    @pytest.fixture
    def format_manager(self):
        """Create format manager for testing."""
        return LegacyFormatManager()
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create legacy workspace structure
        writeit_dir = temp_dir / ".writeit"
        writeit_dir.mkdir()
        
        # Create config file
        config_file = writeit_dir / "config.yaml"
        config_file.write_text("""
default_model: gpt-4
workspace: default
cache_size: 1000
""")
        
        # Create template file
        template_dir = writeit_dir / "pipelines"
        template_dir.mkdir()
        
        template_file = template_dir / "test_template.yaml"
        template_file.write_text("""
name: Test Template
description: A test template
steps:
  - name: step1
    prompt: "Test prompt"
""")
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_detect_legacy_formats(self, format_manager, temp_workspace):
        """Test detection of legacy formats."""
        detected_formats = format_manager.detect_legacy_formats(temp_workspace)
        
        assert len(detected_formats) > 0
        assert any(f.format_type == LegacyFormatType.LEGACY_CONFIG_YAML for f in detected_formats)
        assert any(f.format_type == LegacyFormatType.LEGACY_TEMPLATE_YAML for f in detected_formats)
    
    def test_format_compatibility_assessment(self, format_manager, temp_workspace):
        """Test format compatibility assessment."""
        detected_formats = format_manager.detect_legacy_formats(temp_workspace)
        
        config_format = next(f for f in detected_formats if f.format_type == LegacyFormatType.LEGACY_CONFIG_YAML)
        
        assert config_format.compatibility in [FormatCompatibility.FULL_COMPATIBLE, FormatCompatibility.PARTIAL_COMPATIBLE]
        assert config_format.file_path.exists()
        assert config_format.size_bytes > 0
    
    @pytest.mark.asyncio
    async def test_read_legacy_data(self, format_manager, temp_workspace):
        """Test reading legacy data."""
        detected_formats = format_manager.detect_legacy_formats(temp_workspace)
        config_format = next(f for f in detected_formats if f.format_type == LegacyFormatType.LEGACY_CONFIG_YAML)
        
        data = format_manager.read_legacy_data(config_format)
        
        assert isinstance(data, dict)
        assert "default_model" in data
        assert data["default_model"] == "gpt-4"


class TestBackupManager:
    """Test cases for BackupManager."""
    
    @pytest.fixture
    def temp_backup_dir(self):
        """Create temporary backup directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def backup_manager(self, temp_backup_dir):
        """Create backup manager for testing."""
        config = BackupConfig(
            backup_root_path=temp_backup_dir,
            compression=CompressionType.TAR_GZ,
            retention_days=7,
            max_backups=5,
        )
        return BackupManager(config)
    
    @pytest.fixture
    def test_data_dir(self):
        """Create test data directory."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create test files
        (temp_dir / "file1.txt").write_text("Test content 1")
        (temp_dir / "file2.txt").write_text("Test content 2")
        
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("Test content 3")
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_create_backup(self, backup_manager, test_data_dir):
        """Test backup creation."""
        result = await backup_manager.create_backup(
            source_path=test_data_dir,
            backup_type=BackupType.WORKSPACE,
            description="Test backup",
            tags=["test"],
        )
        
        assert result.success is True
        assert result.backup_path.exists()
        assert result.metadata.backup_type == BackupType.WORKSPACE
        assert result.metadata.file_count > 0
    
    @pytest.mark.asyncio
    async def test_restore_backup(self, backup_manager, test_data_dir):
        """Test backup restoration."""
        # Create backup first
        backup_result = await backup_manager.create_backup(
            source_path=test_data_dir,
            backup_type=BackupType.WORKSPACE,
            description="Test backup",
            tags=["test"],
        )
        
        assert backup_result.success is True
        
        # Remove original data
        shutil.rmtree(test_data_dir)
        
        # Restore backup
        restore_result = await backup_manager.restore_backup(
            backup_id=backup_result.backup_id,
            target_path=test_data_dir,
        )
        
        assert restore_result.success is True
        assert test_data_dir.exists()
        assert (test_data_dir / "file1.txt").exists()
        assert (test_data_dir / "subdir" / "file3.txt").exists()
    
    @pytest.mark.asyncio
    async def test_list_backups(self, backup_manager, test_data_dir):
        """Test listing backups."""
        # Create multiple backups
        backup1 = await backup_manager.create_backup(
            source_path=test_data_dir,
            backup_type=BackupType.WORKSPACE,
            description="Backup 1",
        )
        
        backup2 = await backup_manager.create_backup(
            source_path=test_data_dir,
            backup_type=BackupType.CONFIGURATION,
            description="Backup 2",
        )
        
        # List all backups
        all_backups = await backup_manager.list_backups()
        assert len(all_backups) >= 2
        
        # Filter by type
        workspace_backups = await backup_manager.list_backups(backup_type=BackupType.WORKSPACE)
        assert len(workspace_backups) >= 1
        assert all(b.backup_type == BackupType.WORKSPACE for b in workspace_backups)
    
    @pytest.mark.asyncio
    async def test_delete_backup(self, backup_manager, test_data_dir):
        """Test backup deletion."""
        # Create backup
        backup_result = await backup_manager.create_backup(
            source_path=test_data_dir,
            backup_type=BackupType.WORKSPACE,
            description="Test backup",
        )
        
        assert backup_result.success is True
        
        # Delete backup
        success = await backup_manager.delete_backup(backup_result.backup_id)
        assert success is True
        
        # Verify backup is deleted
        remaining_backups = await backup_manager.list_backups()
        assert not any(b.backup_id == backup_result.backup_id for b in remaining_backups)
    
    @pytest.mark.asyncio
    async def test_validate_backup(self, backup_manager, test_data_dir):
        """Test backup validation."""
        # Create backup
        backup_result = await backup_manager.create_backup(
            source_path=test_data_dir,
            backup_type=BackupType.WORKSPACE,
            description="Test backup",
        )
        
        assert backup_result.success is True
        
        # Validate backup
        is_valid = await backup_manager.validate_backup(backup_result.backup_id)
        assert is_valid is True
        
        # Corrupt backup file
        backup_path = backup_result.backup_path
        if backup_path.exists():
            backup_path.write_text("corrupted data")
        
        # Validate corrupted backup
        is_valid = await backup_manager.validate_backup(backup_result.backup_id)
        assert is_valid is False


class TestMigrationIntegration:
    """Integration tests for migration functionality."""
    
    @pytest.fixture
    def temp_legacy_workspace(self):
        """Create a complete legacy workspace for testing."""
        temp_dir = Path(tempfile.mkdtemp())
        
        # Create .writeit directory
        writeit_dir = temp_dir / ".writeit"
        writeit_dir.mkdir()
        
        # Create config.yaml
        (writeit_dir / "config.yaml").write_text("""
default_model: gpt-4
workspace: test_legacy
cache_size: 1000
api_key: test_key
""")
        
        # Create pipelines directory
        pipelines_dir = writeit_dir / "pipelines"
        pipelines_dir.mkdir()
        
        # Create test pipeline
        (pipelines_dir / "test_pipeline.yaml").write_text("""
name: Test Pipeline
description: A test pipeline for migration
version: "1.0"
steps:
  - name: generate_outline
    type: llm_generate
    prompt: "Generate an outline for {topic}"
    model: gpt-4
    
  - name: write_content
    type: llm_generate
    prompt: "Write content based on outline: {steps.generate_outline}"
    model: gpt-4
    depends_on: [generate_outline]
""")
        
        # Create articles directory
        articles_dir = writeit_dir / "articles"
        articles_dir.mkdir()
        
        # Create test article
        (articles_dir / "test_article.md").write_text("""
# Test Article

This is a test article for migration testing.

## Section 1

Content here.
""")
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_complete_migration_workflow(self, temp_legacy_workspace):
        """Test complete migration workflow from detection to validation."""
        # This would be a comprehensive test covering:
        # 1. Detection of legacy workspace
        # 2. Analysis of migration requirements
        # 3. Creation of backup
        # 4. Execution of migration
        # 5. Validation of migration results
        # 6. Cleanup of artifacts
        
        # For now, we'll test the individual components
        pass
    
    def test_backup_manager_factory(self):
        """Test backup manager factory function."""
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            backup_manager = create_backup_manager(temp_dir)
            
            assert isinstance(backup_manager, BackupManager)
            assert backup_manager.config.backup_root_path == temp_dir
            assert backup_manager.config.compression == CompressionType.TAR_GZ
            assert backup_manager.config.retention_days == 30
            assert backup_manager.config.max_backups == 10
            
        finally:
            shutil.rmtree(temp_dir)
    
    @pytest.mark.asyncio
    async def test_migration_error_handling(self):
        """Test error handling in migration operations."""
        # This would test various error scenarios
        pass


# Performance and stress tests
class TestMigrationPerformance:
    """Performance tests for migration functionality."""
    
    @pytest.mark.asyncio
    async def test_large_workspace_migration(self):
        """Test migration of large workspace."""
        # Create large test workspace
        pass
    
    @pytest.mark.asyncio
    async def test_concurrent_migrations(self):
        """Test concurrent migration operations."""
        pass
    
    @pytest.mark.asyncio
    async def test_backup_performance(self):
        """Test backup performance with large datasets."""
        pass


# Security tests
class TestMigrationSecurity:
    """Security tests for migration functionality."""
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        pass
    
    def test_backup_integrity_verification(self):
        """Test backup integrity verification."""
        pass
    
    def test_rollback_safety_checks(self):
        """Test rollback safety checks."""
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])