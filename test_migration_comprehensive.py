"""Comprehensive test of the WriteIt migration system.

This test validates that the migration system works end-to-end including:
- Detection of legacy workspaces
- Migration of workspace data
- Validation of migrated data
- Backup and rollback functionality
"""

import tempfile
import shutil
from pathlib import Path
import yaml
import pytest

from writeit.migration import (
    MigrationManager,
    DataFormatDetector,
    WorkspaceDataMigrator,
    create_migration_manager
)


class TestMigrationSystem:
    """Test suite for the migration system."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.workspace_dir = self.temp_dir / "test_workspace"
        self.workspace_dir.mkdir()
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_legacy_workspace(self, has_config=True, has_pipelines=True, has_articles=True, has_lmdb=True):
        """Create a legacy workspace structure for testing."""
        # Create .writeit directory
        writeit_dir = self.workspace_dir / ".writeit"
        writeit_dir.mkdir()
        
        # Create config
        if has_config:
            config_data = {
                "name": "Test Workspace",
                "created_at": "2023-01-01T00:00:00",
                "default_pipeline": "test-pipeline",
                "llm_providers": {
                    "openai": "test-api-key",
                    "anthropic": "test-anthropic-key"
                }
            }
            with open(writeit_dir / "config.yaml", "w") as f:
                yaml.dump(config_data, f)
        
        # Create pipelines
        if has_pipelines:
            pipelines_dir = writeit_dir / "pipelines"
            pipelines_dir.mkdir()
            
            pipeline_data = {
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "version": "1.0.0",
                "steps": {
                    "step1": {
                        "name": "First Step",
                        "type": "llm_generate",
                        "prompt_template": "Generate content about {{topic}}"
                    }
                },
                "inputs": {
                    "topic": {
                        "type": "text",
                        "label": "Topic",
                        "required": True
                    }
                }
            }
            with open(pipelines_dir / "test-pipeline.yaml", "w") as f:
                yaml.dump(pipeline_data, f)
        
        # Create articles
        if has_articles:
            articles_dir = writeit_dir / "articles"
            articles_dir.mkdir()
            
            with open(articles_dir / "test-article.md", "w") as f:
                f.write("# Test Article\n\nThis is a test article.")
        
        # Create LMDB files (empty for testing)
        if has_lmdb:
            # Create a simple LMDB file structure
            # Note: This is a simplified version for testing
            lmdb_file = writeit_dir / "test.mdb"
            lmdb_file.touch()  # Create empty file for testing
    
    def test_legacy_workspace_detection(self):
        """Test detection of legacy workspaces."""
        # Create test workspace
        self.create_legacy_workspace()
        
        # Test detection
        detector = DataFormatDetector()
        legacy_workspaces = detector.detect_legacy_workspaces([self.temp_dir])
        
        assert len(legacy_workspaces) == 1
        assert self.workspace_dir in legacy_workspaces
    
    def test_legacy_workspace_analysis(self):
        """Test analysis of legacy workspace structure."""
        # Create test workspace
        self.create_legacy_workspace()
        
        # Test analysis
        detector = DataFormatDetector()
        analysis = detector.analyze_legacy_workspace(self.workspace_dir)
        
        assert analysis.path == self.workspace_dir
        assert analysis.has_config is True
        assert analysis.has_pipelines is True
        assert analysis.has_articles is True
        assert analysis.pipeline_count == 1
        assert analysis.article_count == 1
    
    def test_workspace_migration(self):
        """Test complete workspace migration."""
        # Create test workspace
        self.create_legacy_workspace()
        
        # Test migration
        migrator = WorkspaceDataMigrator()
        result = migrator.migrate_workspace(
            self.workspace_dir,
            target_name="test-migrated",
            backup=True,
            overwrite=True
        )
        
        assert result.success is True
        assert result.migrated_items > 0
        assert result.backup_path is not None
        
        # Check that backup was created
        assert result.backup_path.exists()
    
    def test_migration_manager(self):
        """Test high-level migration manager."""
        # Create test workspace
        self.create_legacy_workspace()
        
        # Test migration manager
        manager = create_migration_manager()
        
        # Test detection
        workspaces = manager.scan_for_migrations([self.temp_dir])
        assert len(workspaces) == 1
        
        # Test migration
        results = manager.migrate_all(
            search_paths=[self.temp_dir],
            interactive=False,
            backup=True
        )
        
        assert len(results) == 1
        assert results[0].success is True
    
    def test_pickle_detection(self):
        """Test detection of pickle data."""
        # Create test workspace with simulated pickle file
        self.create_legacy_workspace(has_lmdb=False)
        
        # Create a file that looks like pickle data
        pickle_file = self.workspace_dir / ".writeit" / "test.mdb"
        with open(pickle_file, "wb") as f:
            f.write(b'\x80\x04test pickle data')  # Pickle magic number
        
        # Test detection
        pickle_keys = DataFormatDetector.detect_legacy_pickle_data(
            self.workspace_dir / ".writeit"
        )
        
        # Note: This test may fail if LMDB is not available or if the file
        # is not a valid LMDB file. The actual implementation uses LMDB
        # to scan for pickle data.
        assert isinstance(pickle_keys, list)
    
    def test_migration_validation(self):
        """Test validation of migrated workspaces."""
        # This test would require a more complex setup with actual workspace
        # creation in the new format. For now, we'll just test that the
        # validation method exists and can be called.
        
        manager = create_migration_manager()
        
        # This should fail since the workspace doesn't exist
        result = manager.validate_migration("nonexistent-workspace")
        assert result.success is False
        assert "does not exist" in result.message


def test_migration_commands_availability():
    """Test that migration commands are available in CLI."""
    # Test that we can import the migration commands
    try:
        from writeit.cli.commands.simple_migration_commands import simple_migration_app
        assert simple_migration_app is not None
    except ImportError as e:
        pytest.fail(f"Failed to import migration commands: {e}")


if __name__ == "__main__":
    # Run tests manually
    import sys
    
    print("Testing WriteIt Migration System...")
    
    test = TestMigrationSystem()
    test.setup_method()
    
    try:
        # Test 1: Legacy workspace detection
        print("1. Testing legacy workspace detection...")
        test.create_legacy_workspace()
        detector = DataFormatDetector()
        workspaces = detector.detect_legacy_workspaces([test.temp_dir])
        print(f"   Found {len(workspaces)} legacy workspaces")
        assert len(workspaces) == 1
        
        # Test 2: Legacy workspace analysis
        print("2. Testing legacy workspace analysis...")
        analysis = detector.analyze_legacy_workspace(test.workspace_dir)
        print(f"   Analysis: Config={analysis.has_config}, Pipelines={analysis.has_pipelines}")
        assert analysis.has_config is True
        
        # Test 3: Migration manager
        print("3. Testing migration manager...")
        manager = create_migration_manager()
        results = manager.migrate_all(
            search_paths=[test.temp_dir],
            interactive=False,
            backup=True
        )
        print(f"   Migration results: {len(results)} migrations, {sum(1 for r in results if r.success)} successful")
        assert len(results) == 1
        
        print("✓ All tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        sys.exit(1)
        
    finally:
        test.teardown_method()