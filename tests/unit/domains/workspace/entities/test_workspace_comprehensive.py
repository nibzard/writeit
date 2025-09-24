"""Comprehensive unit tests for Workspace entity."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src.writeit.domains.workspace.entities.workspace import Workspace
from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from src.writeit.domains.workspace.value_objects.workspace_path import WorkspacePath

from tests.builders.workspace_builders import WorkspaceBuilder


class TestWorkspace:
    """Test cases for Workspace entity."""
    
    def test_workspace_creation_with_valid_data(self):
        """Test creating a workspace with valid data."""
        workspace = WorkspaceBuilder.default().build()
        
        assert isinstance(workspace.name, WorkspaceName)
        assert isinstance(workspace.path, WorkspacePath)
        assert workspace.name.value == "default"
        assert "/tmp/default" in str(workspace.path)
        assert workspace.is_active is False
        assert isinstance(workspace.created_at, datetime)
        assert isinstance(workspace.updated_at, datetime)
        assert workspace.last_accessed is None
        assert "Default test workspace" in workspace.metadata["description"]
    
    def test_workspace_creation_with_custom_data(self):
        """Test creating a workspace with custom data."""
        metadata = {
            "description": "Custom workspace for testing",
            "project": "TestProject",
            "version": "1.0.0"
        }
        
        workspace = (WorkspaceBuilder()
                    .with_name("custom_workspace")
                    .with_path("/custom/path")
                    .active()
                    .with_metadata(metadata)
                    .build())
        
        assert workspace.name.value == "custom_workspace"
        assert str(workspace.path) == "/custom/path"
        assert workspace.is_active is True
        assert workspace.metadata == metadata
        assert workspace.last_accessed is not None
    
    def test_workspace_activation_status(self):
        """Test workspace activation status."""
        # Inactive workspace
        inactive = WorkspaceBuilder.default().inactive().build()
        assert inactive.is_active is False
        assert inactive.last_accessed is None
        
        # Active workspace
        active = WorkspaceBuilder.default().active().build()
        assert active.is_active is True
        assert active.last_accessed is not None
        
        # Recently accessed
        recent = WorkspaceBuilder.default().recently_accessed().build()
        assert recent.last_accessed is not None
        assert abs((recent.last_accessed - datetime.now()).total_seconds()) < 1
    
    def test_workspace_project_configuration(self):
        """Test workspace with project configuration."""
        workspace = WorkspaceBuilder.project_workspace(
            "project_ws", "MyProject"
        ).build()
        
        assert workspace.name.value == "project_ws"
        assert "/projects/project_ws" in str(workspace.path)
        assert workspace.metadata["project_name"] == "MyProject"
        assert workspace.metadata["project_version"] == "1.0.0"
        assert "project" in workspace.metadata["tags"]
        assert "development" in workspace.metadata["tags"]
    
    def test_workspace_with_tags(self):
        """Test workspace with tags."""
        tags = ["development", "testing", "experimental"]
        workspace = (WorkspaceBuilder
                    .default()
                    .with_tags(tags)
                    .build())
        
        assert workspace.metadata["tags"] == tags
        assert "development" in workspace.metadata["tags"]
        assert "testing" in workspace.metadata["tags"]
        assert "experimental" in workspace.metadata["tags"]
    
    def test_workspace_with_description(self):
        """Test workspace with description."""
        description = "This is a test workspace for comprehensive testing"
        workspace = (WorkspaceBuilder
                    .default()
                    .with_description(description)
                    .build())
        
        assert workspace.metadata["description"] == description
    
    def test_workspace_temporary_configuration(self):
        """Test temporary workspace configuration."""
        workspace = WorkspaceBuilder.temporary().build()
        
        assert workspace.name.value == "temp"
        assert "/tmp/temp" in str(workspace.path)
        assert "temporary" in workspace.metadata["tags"]
        assert "test" in workspace.metadata["tags"]
        assert "Temporary test workspace" in workspace.metadata["description"]
    
    def test_workspace_archived_configuration(self):
        """Test archived workspace configuration."""
        workspace = WorkspaceBuilder.archived().build()
        
        assert workspace.name.value == "archived"
        assert "/archive/archived" in str(workspace.path)
        assert "archived" in workspace.metadata["tags"]
        assert workspace.created_at < datetime.now() - timedelta(days=300)
        assert workspace.last_accessed < datetime.now() - timedelta(days=300)
    
    def test_workspace_with_custom_path(self):
        """Test workspace with custom path."""
        custom_path = "/very/specific/custom/path"
        workspace = WorkspaceBuilder.with_custom_path(
            "custom", custom_path
        ).build()
        
        assert workspace.name.value == "custom"
        assert str(workspace.path) == custom_path
        assert "custom path" in workspace.metadata["description"]
    
    def test_workspace_timestamps(self):
        """Test workspace timestamps."""
        now = datetime.now()
        workspace = WorkspaceBuilder.default().build()
        
        # Created and updated should be close to now
        assert abs((workspace.created_at - now).total_seconds()) < 1
        assert abs((workspace.updated_at - now).total_seconds()) < 1
        
        # Test custom timestamps
        custom_time = datetime(2023, 6, 15, 10, 30, 0)
        custom_workspace = (WorkspaceBuilder
                           .default()
                           .with_timestamps(custom_time, custom_time)
                           .build())
        
        assert custom_workspace.created_at == custom_time
        assert custom_workspace.updated_at == custom_time
    
    def test_workspace_last_accessed_tracking(self):
        """Test last accessed tracking."""
        # Workspace without last accessed
        unaccessed = WorkspaceBuilder.default().build()
        assert unaccessed.last_accessed is None
        
        # Workspace with last accessed
        access_time = datetime.now() - timedelta(hours=2)
        accessed = (WorkspaceBuilder
                   .default()
                   .with_last_accessed(access_time)
                   .build())
        
        assert accessed.last_accessed == access_time
        
        # Recently accessed workspace
        recent = WorkspaceBuilder.default().recently_accessed().build()
        assert recent.last_accessed is not None
        assert abs((recent.last_accessed - datetime.now()).total_seconds()) < 1
    
    def test_workspace_metadata_extensibility(self):
        """Test workspace metadata extensibility."""
        complex_metadata = {
            "description": "Complex workspace",
            "project_info": {
                "name": "ComplexProject",
                "version": "2.1.0",
                "maintainer": "Test Team"
            },
            "settings": {
                "auto_backup": True,
                "backup_interval": 3600,
                "max_backups": 10
            },
            "tags": ["complex", "production"],
            "last_backup": datetime.now().isoformat(),
            "size_bytes": 1024000
        }
        
        workspace = (WorkspaceBuilder
                    .default()
                    .with_metadata(complex_metadata)
                    .build())
        
        assert workspace.metadata == complex_metadata
        assert workspace.metadata["project_info"]["name"] == "ComplexProject"
        assert workspace.metadata["settings"]["auto_backup"] is True
        assert len(workspace.metadata["tags"]) == 2


class TestWorkspaceBusinessLogic:
    """Test business logic and invariants for Workspace."""
    
    def test_workspace_name_path_consistency(self):
        """Test that workspace name and path are consistent."""
        workspace = WorkspaceBuilder.default("consistent_test").build()
        
        # Name should be reflected in the path (depending on implementation)
        assert workspace.name.value == "consistent_test"
        # Path logic depends on WorkspacePath implementation
        # This test ensures they're both set correctly
        assert workspace.path is not None
    
    def test_active_workspace_has_recent_access(self):
        """Test that active workspaces have recent access times."""
        active_workspace = WorkspaceBuilder.active().build()
        
        assert active_workspace.is_active is True
        assert active_workspace.last_accessed is not None
        # Active workspace should have been accessed recently
        time_diff = datetime.now() - active_workspace.last_accessed
        assert time_diff.total_seconds() < 5  # Very recent
    
    def test_inactive_workspace_properties(self):
        """Test properties of inactive workspaces."""
        inactive_workspace = WorkspaceBuilder.default().inactive().build()
        
        assert inactive_workspace.is_active is False
        # Inactive workspaces may or may not have last_accessed
        # This is a business decision
    
    def test_workspace_metadata_contains_required_fields(self):
        """Test that workspace metadata contains required fields."""
        workspace = WorkspaceBuilder.default().build()
        
        # At minimum, should have description
        assert "description" in workspace.metadata
        assert isinstance(workspace.metadata["description"], str)
        assert len(workspace.metadata["description"]) > 0
    
    def test_workspace_timestamps_are_ordered(self):
        """Test that workspace timestamps follow logical ordering."""
        workspace = WorkspaceBuilder.default().recently_accessed().build()
        
        # Created should be <= updated
        assert workspace.created_at <= workspace.updated_at
        
        # If last accessed exists, it should be >= created
        if workspace.last_accessed:
            assert workspace.created_at <= workspace.last_accessed
    
    def test_workspace_unique_identification(self):
        """Test that workspaces have unique identification."""
        workspace1 = WorkspaceBuilder.default("unique1").build()
        workspace2 = WorkspaceBuilder.default("unique2").build()
        
        # Names should be different
        assert workspace1.name != workspace2.name
        
        # Paths should be different
        assert workspace1.path != workspace2.path
        
        # Creation times should be different (even if slightly)
        assert workspace1.created_at != workspace2.created_at
    
    def test_workspace_project_info_consistency(self):
        """Test project workspace information consistency."""
        project_name = "TestProject"
        workspace = WorkspaceBuilder.project_workspace("test_proj", project_name).build()
        
        assert workspace.metadata["project_name"] == project_name
        assert "project" in workspace.metadata["tags"]
        assert workspace.name.value == "test_proj"
        # Description should mention the project
        assert project_name in workspace.metadata["description"]
    
    def test_workspace_archival_properties(self):
        """Test properties of archived workspaces."""
        archived = WorkspaceBuilder.archived().build()
        
        # Archived workspaces should have old timestamps
        age_days = (datetime.now() - archived.created_at).days
        assert age_days > 300  # Over 300 days old
        
        # Should be tagged as archived
        assert "archived" in archived.metadata["tags"]
        
        # Should be in archive path
        assert "archive" in str(archived.path).lower()
    
    def test_workspace_path_validity(self):
        """Test that workspace paths are valid."""
        workspace = WorkspaceBuilder.default().build()
        
        # Path should be a valid WorkspacePath
        assert isinstance(workspace.path, WorkspacePath)
        
        # Path should not be empty
        path_str = str(workspace.path)
        assert len(path_str) > 0
        assert path_str != "/"  # Should not be root
    
    def test_workspace_metadata_serialization(self):
        """Test that workspace metadata can be serialized."""
        import json
        
        workspace = WorkspaceBuilder.project_workspace().build()
        
        # Metadata should be JSON serializable
        try:
            json.dumps(workspace.metadata)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Workspace metadata not serializable: {e}")
    
    def test_workspace_state_immutability(self):
        """Test workspace state immutability."""
        workspace = WorkspaceBuilder.default().build()
        original_name = workspace.name
        
        # Direct modification should not be possible
        with pytest.raises(AttributeError):
            workspace.name = WorkspaceName("modified")  # type: ignore
        
        # Name should remain unchanged
        assert workspace.name == original_name
    
    def test_workspace_lifecycle_consistency(self):
        """Test workspace lifecycle state consistency."""
        # New workspace
        new_workspace = WorkspaceBuilder.default().build()
        assert new_workspace.created_at == new_workspace.updated_at
        assert new_workspace.last_accessed is None
        assert new_workspace.is_active is False
        
        # Active workspace
        active_workspace = WorkspaceBuilder.active().build()
        assert active_workspace.is_active is True
        assert active_workspace.last_accessed is not None
        
        # Archived workspace
        archived_workspace = WorkspaceBuilder.archived().build()
        assert archived_workspace.created_at < archived_workspace.updated_at
        assert archived_workspace.last_accessed is not None
        assert "archived" in archived_workspace.metadata.get("tags", [])


class TestWorkspaceEdgeCases:
    """Test edge cases and error conditions for Workspace."""
    
    def test_workspace_with_empty_metadata(self):
        """Test workspace with minimal metadata."""
        workspace = (WorkspaceBuilder()
                    .with_name("minimal")
                    .with_path("/tmp/minimal")
                    .with_metadata({})
                    .build())
        
        assert workspace.metadata == {}
        # Ensure it still functions properly
        assert workspace.name.value == "minimal"
    
    def test_workspace_with_large_metadata(self):
        """Test workspace with large metadata."""
        large_metadata = {}
        for i in range(100):
            large_metadata[f"key_{i}"] = f"value_{i}" * 100
        
        workspace = (WorkspaceBuilder
                    .default()
                    .with_metadata(large_metadata)
                    .build())
        
        assert len(workspace.metadata) == 100
        assert workspace.metadata["key_0"] == "value_0" * 100
    
    def test_workspace_timestamp_edge_cases(self):
        """Test workspace with edge case timestamps."""
        # Very old timestamp
        old_time = datetime(1900, 1, 1)
        # Future timestamp
        future_time = datetime(2100, 1, 1)
        
        old_workspace = (WorkspaceBuilder
                        .default()
                        .with_timestamps(old_time, old_time)
                        .build())
        
        future_workspace = (WorkspaceBuilder
                           .default()
                           .with_timestamps(future_time, future_time)
                           .build())
        
        assert old_workspace.created_at == old_time
        assert future_workspace.created_at == future_time
    
    def test_workspace_with_special_characters_in_metadata(self):
        """Test workspace with special characters in metadata."""
        special_metadata = {
            "description": "Workspace with émojis 🚀 and üñíçödé",
            "path_info": "/special/påth/wîth/characters",
            "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?"
        }
        
        workspace = (WorkspaceBuilder
                    .default()
                    .with_metadata(special_metadata)
                    .build())
        
        assert workspace.metadata == special_metadata
        assert "🚀" in workspace.metadata["description"]
        assert "üñíçödé" in workspace.metadata["description"]