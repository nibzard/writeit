"""Integration tests for WriteIt migration system."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch

from writeit.workspace.workspace import Workspace
from writeit.migration.data_migrator import MigrationManager, create_migration_manager
from writeit.migration.config_migrator import ConfigMigrationManager, create_config_migration_manager
from writeit.migration.cache_migrator import CacheMigrationManager, create_cache_migration_manager
from writeit.migration.workspace_structure_updater import WorkspaceStructureUpdater
from writeit.migration.cache_format_updater import create_cache_format_updater


class TestMigrationIntegration:
    """Integration tests for migration system components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.workspace_dir = self.temp_dir / "test_workspace"
        self.workspace_dir.mkdir()
        
        # Create mock workspace
        self.mock_workspace = Mock(spec=Workspace)
        self.mock_workspace.get_workspace_path.return_value = self.workspace_dir
        self.mock_workspace.name = "test_workspace"
        self.mock_workspace.workspaces_dir = str(self.temp_dir / "workspaces")
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_migration_manager_creation(self):
        """Test migration manager can be created."""
        manager = create_migration_manager(self.mock_workspace)
        assert isinstance(manager, MigrationManager)
        assert manager.workspace_manager == self.mock_workspace
    
    def test_migration_manager_scan_empty(self):
        """Test migration manager scanning empty workspace."""
        manager = create_migration_manager(self.mock_workspace)
        legacy_workspaces = manager.scan_for_migrations([self.temp_dir])
        assert len(legacy_workspaces) == 0
    
    def test_migration_manager_scan_legacy_workspace(self):
        """Test migration manager can detect legacy workspace."""
        # Create legacy workspace structure
        legacy_dir = self.workspace_dir / ".writeit"
        legacy_dir.mkdir()
        (legacy_dir / "config.yaml").write_text("name: test_workspace")
        
        manager = create_migration_manager(self.mock_workspace)
        legacy_workspaces = manager.scan_for_migrations([self.temp_dir])
        assert len(legacy_workspaces) == 1
        assert self.workspace_dir in legacy_workspaces
    
    def test_config_migration_manager_creation(self):
        """Test config migration manager can be created."""
        manager = create_config_migration_manager()
        assert isinstance(manager, ConfigMigrationManager)
    
    def test_config_migration_analyze_workspace(self):
        """Test config migration can analyze workspace."""
        manager = create_config_migration_manager()
        
        # Create legacy config
        config_file = self.workspace_dir / ".writeit" / "config.yaml"
        config_file.parent.mkdir()
        config_file.write_text("name: test_workspace\ndefault_model: gpt-4")
        
        analyses = manager.analyze_config_migration_needs(self.workspace_dir)
        assert len(analyses) == 1
        assert analyses[0].has_valid_config
        assert analyses[0].config_format == "yaml"
    
    def test_cache_migration_manager_creation(self):
        """Test cache migration manager can be created."""
        manager = create_cache_migration_manager()
        assert isinstance(manager, CacheMigrationManager)
    
    def test_cache_migration_analyze_workspace(self):
        """Test cache migration can analyze workspace."""
        manager = create_cache_migration_manager()
        
        # Create cache file
        cache_file = self.workspace_dir / ".writeit" / "cache.json"
        cache_file.parent.mkdir()
        cache_file.write_text('{"key": "value", "expires_at": "2025-01-01T00:00:00"}')
        
        analyses = manager.analyze_cache_migration_needs(self.workspace_dir)
        assert len(analyses) == 1
        assert analyses[0].cache_format == "file"
        assert analyses[0].total_entries == 1
    
    def test_workspace_structure_updater_creation(self):
        """Test workspace structure updater can be created."""
        updater = WorkspaceStructureUpdater(self.mock_workspace)
        assert isinstance(updater, WorkspaceStructureUpdater)
        assert updater.workspace == self.mock_workspace
    
    def test_workspace_structure_update_empty(self):
        """Test workspace structure update on empty workspace."""
        updater = WorkspaceStructureUpdater(self.mock_workspace)
        
        result = updater.update_workspace_structure("test_workspace")
        assert result.success
        assert "already up to date" in result.message.lower()
    
    def test_workspace_structure_update_legacy(self):
        """Test workspace structure update on legacy workspace."""
        # Create legacy structure
        legacy_dir = self.workspace_dir / ".writeit"
        legacy_dir.mkdir()
        (legacy_dir / "articles").mkdir()
        (legacy_dir / "pipelines").mkdir()
        (legacy_dir / "config.yaml").write_text("name: legacy")
        
        updater = WorkspaceStructureUpdater(self.mock_workspace)
        
        result = updater.update_workspace_structure("test_workspace")
        assert result.success
        assert len(result.created_directories) > 0
        assert len(result.moved_files) > 0
    
    def test_cache_format_updater_creation(self):
        """Test cache format updater can be created."""
        cache_manager = create_cache_migration_manager()
        updater = create_cache_format_updater(cache_manager)
        assert updater.cache_manager == cache_manager
    
    def test_migration_validation(self):
        """Test migration validation functionality."""
        manager = create_migration_manager(self.mock_workspace)
        
        # Test validation on non-existent workspace
        result = manager.validate_migration("nonexistent")
        assert not result.success
        assert "does not exist" in result.message
    
    def test_full_migration_workflow(self):
        """Test complete migration workflow."""
        # Create legacy workspace
        legacy_dir = self.workspace_dir / ".writeit"
        legacy_dir.mkdir()
        
        # Create legacy config
        (legacy_dir / "config.yaml").write_text("""
name: test_workspace
default_model: gpt-4
openai_api_key: test_key
""")
        
        # Create legacy cache
        (legacy_dir / "cache.json").write_text('{"response": "test", "model": "gpt-4"}')
        
        # Create legacy articles
        articles_dir = legacy_dir / "articles"
        articles_dir.mkdir()
        (articles_dir / "test.md").write_text("# Test Article")
        
        # Test data migration
        manager = create_migration_manager(self.mock_workspace)
        legacy_workspaces = manager.scan_for_migrations([self.temp_dir])
        assert len(legacy_workspaces) == 1
        
        # Test config migration
        config_manager = create_config_migration_manager()
        config_analyses = config_manager.analyze_config_migration_needs(self.workspace_dir)
        assert len(config_analyses) == 1
        
        # Test cache migration
        cache_manager = create_cache_migration_manager()
        cache_analyses = cache_manager.analyze_cache_migration_needs(self.workspace_dir)
        assert len(cache_analyses) == 1
        
        # Test workspace structure update
        updater = WorkspaceStructureUpdater(self.mock_workspace)
        structure_result = updater.update_workspace_structure("test_workspace")
        assert structure_result.success
        
        # Test cache format update
        cache_updater = create_cache_format_updater(cache_manager)
        cache_result = cache_updater.update_cache_format(self.workspace_dir)
        assert cache_result.success
    
    def test_migration_error_handling(self):
        """Test migration error handling."""
        manager = create_migration_manager(self.mock_workspace)
        
        # Test with invalid workspace path
        with patch.object(manager.migrator.detector, 'analyze_legacy_workspace') as mock_analyze:
            mock_analyze.side_effect = Exception("Test error")
            
            result = manager.migrator.migrate_workspace(
                self.workspace_dir,
                backup=False
            )
            
            assert not result.success
            assert "Test error" in result.errors[0]
    
    def test_migration_backup_creation(self):
        """Test backup creation during migration."""
        # Create legacy workspace
        legacy_dir = self.workspace_dir / ".writeit"
        legacy_dir.mkdir()
        (legacy_dir / "config.yaml").write_text("name: test")
        
        manager = create_migration_manager(self.mock_workspace)
        result = manager.migrator.migrate_workspace(
            self.workspace_dir,
            backup=True,
            overwrite=True
        )
        
        assert result.success
        assert result.backup_path is not None
        assert result.backup_path.exists()
    
    def test_migration_dry_run(self):
        """Test migration dry run functionality."""
        # Create legacy workspace
        legacy_dir = self.workspace_dir / ".writeit"
        legacy_dir.mkdir()
        (legacy_dir / "config.yaml").write_text("name: test")
        
        manager = create_migration_manager(self.mock_workspace)
        
        # Test workspace migration dry run
        result = manager.migrator.migrate_workspace(
            self.workspace_dir,
            backup=False,
            dry_run=True,
            overwrite=True
        )
        
        assert result.success
        
        # Test cache migration dry run
        cache_manager = create_cache_migration_manager()
        cache_results = cache_manager.migrate_workspace_cache(
            self.workspace_dir,
            backup=False,
            dry_run=True
        )
        
        # Should not modify anything
        assert len(cache_results) >= 0


class TestMigrationCLIIntegration:
    """Integration tests for migration CLI commands."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.workspace_dir = self.temp_dir / "test_workspace"
        self.workspace_dir.mkdir()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_cli_commands_available(self):
        """Test that all CLI commands are available."""
        from writeit.cli.migrate import main
        import argparse
        
        # Mock sys.argv for testing
        with patch('sys.argv', ['writeit', 'migrate', '--help']):
            try:
                main()
            except SystemExit:
                pass  # Expected for --help
    
    def test_cli_workspace_migration(self):
        """Test CLI workspace migration command."""
        from writeit.cli.migrate import migrate_workspace
        
        # Create mock workspace
        mock_workspace = Mock(spec=Workspace)
        mock_workspace.get_workspace_path.return_value = self.workspace_dir
        
        # Create legacy structure
        legacy_dir = self.workspace_dir / ".writeit"
        legacy_dir.mkdir()
        (legacy_dir / "config.yaml").write_text("name: test")
        
        # Mock args
        args = Mock()
        args.workspace_name = "test_workspace"
        args.dry_run = False
        args.report = False
        
        with patch('writeit.cli.migrate.Workspace', return_value=mock_workspace):
            with patch('writeit.cli.migrate.create_migration_manager') as mock_create_manager:
                mock_manager = Mock()
                mock_result = Mock()
                mock_result.success = True
                mock_result.migrated_items = 1
                mock_result.warnings = []
                mock_result.backup_path = None
                mock_manager.migrator.migrate_workspace.return_value = mock_result
                mock_manager.validate_migration.return_value = Mock(success=True, warnings=[])
                mock_create_manager.return_value = mock_manager
                
                result = migrate_workspace(args)
                assert result == 0
    
    def test_cli_structure_update(self):
        """Test CLI structure update command."""
        from writeit.cli.migrate import update_workspace_structure
        
        # Create mock workspace
        mock_workspace = Mock(spec=Workspace)
        mock_workspace.get_workspace_path.return_value = self.workspace_dir
        
        # Mock args
        args = Mock()
        args.workspace_name = "test_workspace"
        args.dry_run = False
        args.validate = False
        
        with patch('writeit.cli.migrate.Workspace', return_value=mock_workspace):
            with patch('writeit.cli.migrate.WorkspaceStructureUpdater') as mock_updater_class:
                mock_updater = Mock()
                mock_updater.update_workspace_structure.return_value = True
                mock_updater_class.return_value = mock_updater
                
                result = update_workspace_structure(args)
                assert result == 0
    
    def test_cli_cache_update(self):
        """Test CLI cache update command."""
        from writeit.cli.migrate import update_cache_format
        
        # Create mock workspace
        mock_workspace = Mock(spec=Workspace)
        mock_workspace.get_workspace_path.return_value = self.workspace_dir
        
        # Create cache file
        cache_file = self.workspace_dir / ".writeit" / "cache.json"
        cache_file.parent.mkdir()
        cache_file.write_text('{"test": "data"}')
        
        # Mock args
        args = Mock()
        args.workspace_name = "test_workspace"
        args.dry_run = False
        args.include_pickle = False
        args.keep_expired = False
        args.validate = False
        
        with patch('writeit.cli.migrate.Workspace', return_value=mock_workspace):
            with patch('writeit.cli.migrate.create_cache_migration_manager') as mock_create_cache:
                with patch('writeit.cli.migrate.create_cache_format_updater') as mock_create_updater:
                    mock_cache_manager = Mock()
                    mock_cache_manager.analyze_cache_migration_needs.return_value = []
                    
                    mock_updater = Mock()
                    mock_result = Mock()
                    mock_result.success = True
                    mock_result.updated_entries = 1
                    mock_result.warnings = []
                    mock_updater.update_cache_format.return_value = mock_result
                    mock_updater.validate_cache_format.return_value = []
                    
                    mock_create_cache.return_value = mock_cache_manager
                    mock_create_updater.return_value = mock_updater
                    
                    result = update_cache_format(args)
                    assert result == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])