"""Tests for data migration service."""

import asyncio
import json
import tempfile
import shutil
import yaml
from pathlib import Path
from datetime import datetime
from decimal import Decimal
import pytest

from writeit.application.services.data_migration_service import (
    DataMigrationService, 
    MigrationResult, 
    MigrationContext
)


class TestDataMigrationService:
    """Test suite for data migration service."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.migration_service = DataMigrationService()
        
    def teardown_method(self):
        """Clean up test environment."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def create_legacy_workspace(self, workspace_name: str) -> Path:
        """Create a legacy workspace for testing."""
        workspace_path = self.temp_dir / workspace_name
        
        # Create basic directory structure
        (workspace_path / "pipelines").mkdir(parents=True, exist_ok=True)
        (workspace_path / "templates").mkdir(parents=True, exist_ok=True)
        (workspace_path / "styles").mkdir(parents=True, exist_ok=True)
        
        # Create legacy config
        legacy_config = {
            "default_model": "gpt-4o-mini",
            "cache_enabled": True,
            "cache_ttl_hours": 24,
            "max_cache_entries": 1000
        }
        
        with open(workspace_path / "config.yaml", 'w') as f:
            yaml.dump(legacy_config, f)
        
        # Create legacy pipeline
        legacy_pipeline = {
            "name": "test-pipeline",
            "description": "Test pipeline for migration",
            "version": "1.0.0",
            "steps": [
                {
                    "name": "outline",
                    "description": "Create outline",
                    "type": "llm_generate",
                    "prompt_template": "Create outline for {{ inputs.topic }}"
                }
            ]
        }
        
        with open(workspace_path / "pipelines" / "test.yaml", 'w') as f:
            yaml.dump(legacy_pipeline, f)
        
        # Create legacy token usage data
        legacy_token_data = {
            "runs": [
                {
                    "pipeline_name": "test-pipeline",
                    "run_id": "test-run-123",
                    "start_time": datetime.now().isoformat(),
                    "steps": [
                        {
                            "step_key": "outline",
                            "step_name": "Create outline",
                            "model_name": "gpt-4o-mini",
                            "timestamp": datetime.now().isoformat(),
                            "regeneration_count": 0,
                            "usage": {
                                "input_tokens": 150,
                                "output_tokens": 300,
                                "total_tokens": 450,
                                "details": {"model": "gpt-4o-mini"}
                            }
                        }
                    ]
                }
            ]
        }
        
        with open(workspace_path / "token_usage.json", 'w') as f:
            json.dump(legacy_token_data, f)
        
        return workspace_path
    
    def test_migrate_workspace_structure_dry_run(self):
        """Test workspace structure migration in dry run mode."""
        # Arrange
        legacy_path = self.create_legacy_workspace("legacy-test")
        
        # Act
        context = MigrationContext(
            source_path=legacy_path,
            target_path=self.temp_dir / "target",
            workspace_name="test-workspace",
            dry_run=True
        )
        
        result = asyncio.run(self.migration_service._migrate_workspace_structure(context))
        
        # Assert
        assert result.success
        assert "dry run" in result.message.lower()
        assert result.migrated_count >= 1
        assert not context.target_path.exists()  # Should not create files in dry run
    
    def test_migrate_workspace_structure_real(self):
        """Test actual workspace structure migration."""
        # Arrange
        legacy_path = self.create_legacy_workspace("legacy-test")
        
        # Act
        context = MigrationContext(
            source_path=legacy_path,
            target_path=self.temp_dir / "target",
            workspace_name="test-workspace",
            dry_run=False
        )
        
        result = asyncio.run(self.migration_service._migrate_workspace_structure(context))
        
        # Assert
        assert result.success
        assert result.migrated_count >= 1
        assert context.target_path.exists()
        assert (context.target_path / "pipelines").exists()
        assert (context.target_path / "templates").exists()
        assert (context.target_path / "cache").exists()
        assert (context.target_path / "storage").exists()
    
    def test_migrate_configuration_dry_run(self):
        """Test configuration migration in dry run mode."""
        # Arrange
        legacy_path = self.create_legacy_workspace("legacy-test")
        
        # Act
        context = MigrationContext(
            source_path=legacy_path,
            target_path=self.temp_dir / "target",
            workspace_name="test-workspace",
            dry_run=True
        )
        
        result = asyncio.run(self.migration_service._migrate_configuration(context))
        
        # Assert
        assert result.success
        assert "dry run" in result.message.lower()
        assert not (context.target_path / "config.yaml").exists()
    
    def test_migrate_configuration_real(self):
        """Test actual configuration migration."""
        # Arrange
        legacy_path = self.create_legacy_workspace("legacy-test")
        
        # Act
        context = MigrationContext(
            source_path=legacy_path,
            target_path=self.temp_dir / "target",
            workspace_name="test-workspace",
            dry_run=False
        )
        
        result = asyncio.run(self.migration_service._migrate_configuration(context))
        
        # Assert
        assert result.success
        assert result.migrated_count >= 1
        assert (context.target_path / "config.yaml").exists()
        
        # Verify migrated config
        with open(context.target_path / "config.yaml", 'r') as f:
            migrated_config = yaml.safe_load(f)
        
        assert "default_model" in migrated_config
        assert "enable_cache" in migrated_config
    
    def test_migrate_token_usage_dry_run(self):
        """Test token usage migration in dry run mode."""
        # Arrange
        legacy_path = self.create_legacy_workspace("legacy-test")
        
        # Act
        context = MigrationContext(
            source_path=legacy_path,
            target_path=self.temp_dir / "target",
            workspace_name="test-workspace",
            dry_run=True
        )
        
        result = asyncio.run(self.migration_service._migrate_token_usage(context))
        
        # Assert
        assert result.success
        assert result.migrated_count >= 1  # Should count items even in dry run
    
    def test_migrate_token_usage_no_data(self):
        """Test token usage migration with no legacy data."""
        # Arrange
        empty_workspace = self.temp_dir / "empty"
        empty_workspace.mkdir()
        
        context = MigrationContext(
            source_path=empty_workspace,
            target_path=self.temp_dir / "target",
            workspace_name="test-workspace",
            dry_run=False
        )
        
        # Act
        result = asyncio.run(self.migration_service._migrate_token_usage(context))
        
        # Assert
        assert result.success
        assert result.migrated_count == 0
        assert "0 records migrated" in result.message
    
    def test_convert_legacy_step_usage(self):
        """Test conversion of legacy step usage to new TokenUsage entity."""
        # Arrange
        legacy_step = {
            "step_key": "outline",
            "step_name": "Create outline", 
            "model_name": "gpt-4o-mini",
            "timestamp": datetime.now().isoformat(),
            "regeneration_count": 0,
            "usage": {
                "input_tokens": 150,
                "output_tokens": 300,
                "total_tokens": 450,
                "details": {"model": "gpt-4o-mini"}
            }
        }
        
        # Act
        token_usage = self.migration_service._convert_legacy_step_usage(
            legacy_step, "test-pipeline", "test-workspace"
        )
        
        # Assert
        assert token_usage.model_name.value == "gpt-4o-mini"
        assert token_usage.token_metrics.input_tokens == 150
        assert token_usage.token_metrics.output_tokens == 300
        assert token_usage.workspace_name == "test-workspace"
        assert token_usage.pipeline_id == "test-pipeline"
        assert token_usage.step_id == "outline"
    
    def test_convert_legacy_cache_entry(self):
        """Test conversion of legacy cache entry to new format."""
        # Arrange
        legacy_entry = {
            "cache_key": "test-key-123",
            "prompt": "Test prompt",
            "model_name": "gpt-4o-mini",
            "response": "Test response",
            "tokens_used": {"input": 10, "output": 20},
            "created_at": datetime.now().isoformat(),
            "accessed_at": datetime.now().isoformat(),
            "access_count": 5,
            "metadata": {"legacy": True}
        }
        
        # Act
        new_entry = self.migration_service._convert_legacy_cache_entry(legacy_entry)
        
        # Assert
        assert new_entry["cache_key"] == "test-key-123"
        assert new_entry["prompt"] == "Test prompt"
        assert new_entry["model_name"] == "gpt-4o-mini"
        assert new_entry["response"] == "Test response"
        assert new_entry["metadata"]["migrated_from_legacy"] is True
        assert "migration_timestamp" in new_entry["metadata"]
    
    def test_full_migration_dry_run(self):
        """Test full migration process in dry run mode."""
        # Arrange
        legacy_path = self.create_legacy_workspace("legacy-full-test")
        
        # Act
        result = asyncio.run(
            self.migration_service.migrate_all_data(
                source_workspace_path=legacy_path,
                workspace_name="full-test-workspace",
                dry_run=True,
                create_backup=False
            )
        )
        
        # Assert
        assert result.success
        assert result.migrated_count >= 1
        assert result.error_count == 0
        assert result.backup_path is None  # No backup in dry run
        assert result.duration_seconds > 0
    
    def test_full_migration_with_backup(self):
        """Test full migration process with backup creation."""
        # Arrange
        legacy_path = self.create_legacy_workspace("legacy-backup-test")
        
        # Act
        result = asyncio.run(
            self.migration_service.migrate_all_data(
                source_workspace_path=legacy_path,
                workspace_name="backup-test-workspace",
                dry_run=False,
                create_backup=True
            )
        )
        
        # Assert
        assert result.success
        assert result.migrated_count >= 1
        assert result.backup_path is not None
        assert result.backup_path.exists()
        assert result.backup_path.name.startswith("migration_backup_")
    
    def test_migration_nonexistent_source(self):
        """Test migration with non-existent source path."""
        # Arrange
        nonexistent_path = self.temp_dir / "does-not-exist"
        
        # Act
        result = asyncio.run(
            self.migration_service.migrate_all_data(
                source_workspace_path=nonexistent_path,
                workspace_name="test-workspace",
                dry_run=True,
                create_backup=False
            )
        )
        
        # Assert
        assert not result.success
        assert "does not exist" in result.message
        assert result.error_count == 1
    
    def test_get_migration_report(self):
        """Test migration report generation."""
        # Act
        report = self.migration_service.get_migration_report()
        
        # Assert
        assert isinstance(report, dict)
        assert "migration_log" in report
        assert "total_migrations" in report
        assert "success_count" in report
        assert "error_count" in report
        assert "last_migration" in report
        assert isinstance(report["migration_log"], list)
    
    def test_migration_context_validation(self):
        """Test MigrationContext validation."""
        # Arrange
        legacy_path = self.create_legacy_workspace("legacy-context-test")
        
        # Act
        context = MigrationContext(
            source_path=legacy_path,
            target_path=self.temp_dir / "target",
            workspace_name="context-test",
            dry_run=True,
            verbose=True
        )
        
        # Assert
        assert context.source_path == legacy_path
        assert context.target_path == self.temp_dir / "target"
        assert context.workspace_name == "context-test"
        assert context.dry_run is True
        assert context.verbose is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])