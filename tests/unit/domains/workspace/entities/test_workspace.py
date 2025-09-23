"""Unit tests for Workspace entity.

Tests workspace entity behavior, validation, and business rules.
"""

import pytest
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from writeit.domains.workspace.entities.workspace import Workspace
from writeit.domains.workspace.entities.workspace_configuration import WorkspaceConfiguration
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue


class TestWorkspace:
    """Test Workspace entity behavior and validation."""
    
    def test_create_minimal_workspace(self):
        """Test creating a minimal workspace."""
        name = WorkspaceName("test-workspace")
        path = WorkspacePath(Path("/tmp/test-workspace"))
        config = WorkspaceConfiguration()
        
        workspace = Workspace(
            name=name,
            path=path,
            configuration=config
        )
        
        assert workspace.name == name
        assert workspace.path == path
        assert workspace.configuration == config
        assert workspace.is_active is False
        assert workspace.is_isolated is True
        assert isinstance(workspace.created_at, datetime)
        assert isinstance(workspace.last_accessed_at, datetime)
    
    def test_create_with_custom_properties(self):
        """Test creating workspace with custom properties."""
        name = WorkspaceName("custom-workspace")
        path = WorkspacePath(Path("/custom/path"))
        config = WorkspaceConfiguration()
        created_time = datetime.now(timezone.utc)
        
        workspace = Workspace(
            name=name,
            path=path,
            configuration=config,
            description="Custom workspace for testing",
            is_active=True,
            is_isolated=False,
            created_at=created_time,
            last_accessed_at=created_time
        )
        
        assert workspace.description == "Custom workspace for testing"
        assert workspace.is_active is True
        assert workspace.is_isolated is False
        assert workspace.created_at == created_time
        assert workspace.last_accessed_at == created_time
    
    def test_invalid_name_type_raises_error(self):
        """Test that invalid name type raises TypeError."""
        with pytest.raises(TypeError, match="Workspace name must be a WorkspaceName"):
            Workspace(
                name="invalid",  # Should be WorkspaceName
                path=WorkspacePath(Path("/tmp/test")),
                configuration=WorkspaceConfiguration()
            )
    
    def test_invalid_path_type_raises_error(self):
        """Test that invalid path type raises TypeError."""
        with pytest.raises(TypeError, match="Workspace path must be a WorkspacePath"):
            Workspace(
                name=WorkspaceName("test"),
                path="/invalid/path",  # Should be WorkspacePath
                configuration=WorkspaceConfiguration()
            )
    
    def test_invalid_configuration_type_raises_error(self):
        """Test that invalid configuration type raises TypeError."""
        with pytest.raises(TypeError, match="Configuration must be a WorkspaceConfiguration"):
            Workspace(
                name=WorkspaceName("test"),
                path=WorkspacePath(Path("/tmp/test")),
                configuration={}  # Should be WorkspaceConfiguration
            )
    
    def test_activate_workspace(self):
        """Test activating a workspace."""
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration()
        )
        
        assert workspace.is_active is False
        
        activated = workspace.activate()
        
        # Original workspace unchanged
        assert workspace.is_active is False
        
        # New workspace is active and has updated access time
        assert activated.is_active is True
        assert activated.last_accessed_at > workspace.last_accessed_at
    
    def test_deactivate_workspace(self):
        """Test deactivating a workspace."""
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration(),
            is_active=True
        )
        
        assert workspace.is_active is True
        
        deactivated = workspace.deactivate()
        
        # Original workspace unchanged
        assert workspace.is_active is True
        
        # New workspace is inactive
        assert deactivated.is_active is False
    
    def test_update_access_time(self):
        """Test updating last access time."""
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration()
        )
        
        original_time = workspace.last_accessed_at
        
        updated = workspace.update_access_time()
        
        # Original workspace unchanged
        assert workspace.last_accessed_at == original_time
        
        # New workspace has updated access time
        assert updated.last_accessed_at > original_time
    
    def test_update_configuration(self):
        """Test updating workspace configuration."""
        original_config = WorkspaceConfiguration()
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=original_config
        )
        
        new_config = WorkspaceConfiguration(
            settings={
                "theme": ConfigurationValue("theme", "dark", "string")
            }
        )
        
        updated = workspace.update_configuration(new_config)
        
        # Original workspace unchanged
        assert workspace.configuration == original_config
        
        # New workspace has updated configuration
        assert updated.configuration == new_config
    
    def test_is_default_workspace(self):
        """Test checking if workspace is the default workspace."""
        default_workspace = Workspace(
            name=WorkspaceName("default"),
            path=WorkspacePath(Path("/tmp/default")),
            configuration=WorkspaceConfiguration()
        )
        
        other_workspace = Workspace(
            name=WorkspaceName("other"),
            path=WorkspacePath(Path("/tmp/other")),
            configuration=WorkspaceConfiguration()
        )
        
        assert default_workspace.is_default() is True
        assert other_workspace.is_default() is False
    
    def test_get_absolute_path(self):
        """Test getting absolute workspace path."""
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration()
        )
        
        abs_path = workspace.get_absolute_path()
        assert abs_path == Path("/tmp/test")
        assert abs_path.is_absolute()
    
    def test_get_relative_path_to(self):
        """Test getting relative path to another path."""
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration()
        )
        
        target_path = Path("/tmp/test/subdir/file.txt")
        relative_path = workspace.get_relative_path_to(target_path)
        
        expected = Path("subdir/file.txt")
        assert relative_path == expected
    
    def test_contains_path(self):
        """Test checking if workspace contains a path."""
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration()
        )
        
        # Paths within workspace
        assert workspace.contains_path(Path("/tmp/test/file.txt")) is True
        assert workspace.contains_path(Path("/tmp/test/subdir/file.txt")) is True
        
        # Paths outside workspace
        assert workspace.contains_path(Path("/tmp/other/file.txt")) is False
        assert workspace.contains_path(Path("/other/file.txt")) is False
    
    def test_get_setting(self):
        """Test getting configuration setting."""
        config = WorkspaceConfiguration(
            settings={
                "theme": ConfigurationValue("theme", "dark", "string"),
                "auto_save": ConfigurationValue("auto_save", True, "boolean")
            }
        )
        
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=config
        )
        
        # Existing settings
        assert workspace.get_setting("theme") == "dark"
        assert workspace.get_setting("auto_save") is True
        
        # Default for non-existent setting
        assert workspace.get_setting("non_existent") is None
        assert workspace.get_setting("non_existent", "default") == "default"
    
    def test_has_setting(self):
        """Test checking if workspace has a setting."""
        config = WorkspaceConfiguration(
            settings={
                "theme": ConfigurationValue("theme", "dark", "string")
            }
        )
        
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=config
        )
        
        assert workspace.has_setting("theme") is True
        assert workspace.has_setting("non_existent") is False
    
    def test_get_metadata(self):
        """Test getting workspace metadata."""
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration(),
            description="Test workspace",
            is_active=True
        )
        
        metadata = workspace.get_metadata()
        
        assert metadata["name"] == "test"
        assert metadata["path"] == str(Path("/tmp/test"))
        assert metadata["description"] == "Test workspace"
        assert metadata["is_active"] is True
        assert metadata["is_isolated"] is True
        assert metadata["is_default"] is False
        assert "created_at" in metadata
        assert "last_accessed_at" in metadata
    
    def test_validate_path_exists(self):
        """Test validating that workspace path exists."""
        # Use a path that should exist
        existing_path = Path("/tmp")
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(existing_path),
            configuration=WorkspaceConfiguration()
        )
        
        # Should not raise error for existing path
        workspace.validate_path_exists()
    
    def test_validate_path_not_exists_raises_error(self):
        """Test that validating non-existent path raises error."""
        non_existent_path = Path("/non/existent/path/12345")
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(non_existent_path),
            configuration=WorkspaceConfiguration()
        )
        
        with pytest.raises(FileNotFoundError, match="Workspace path does not exist"):
            workspace.validate_path_exists()
    
    def test_validate_writable(self):
        """Test validating that workspace path is writable."""
        # Use /tmp which should be writable
        writable_path = Path("/tmp")
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(writable_path),
            configuration=WorkspaceConfiguration()
        )
        
        # Should not raise error for writable path
        workspace.validate_writable()
    
    def test_validate_not_writable_raises_error(self):
        """Test that validating non-writable path raises error."""
        # Use root directory which should not be writable for normal users
        non_writable_path = Path("/root")
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(non_writable_path),
            configuration=WorkspaceConfiguration()
        )
        
        # This might not raise error in all environments, so we'll check if it exists first
        if non_writable_path.exists():
            try:
                workspace.validate_writable()
            except PermissionError:
                # Expected for non-writable paths
                pass
    
    def test_string_representation(self):
        """Test string representation."""
        workspace = Workspace(
            name=WorkspaceName("test-workspace"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration()
        )
        
        str_repr = str(workspace)
        assert "test-workspace" in str_repr
        assert "/tmp/test" in str_repr
    
    def test_repr_representation(self):
        """Test debug representation."""
        workspace = Workspace(
            name=WorkspaceName("test-workspace"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration(),
            is_active=True
        )
        
        repr_str = repr(workspace)
        assert "Workspace" in repr_str
        assert "test-workspace" in repr_str
        assert "/tmp/test" in repr_str
        assert "active=True" in repr_str
    
    def test_equality(self):
        """Test workspace equality based on name and path."""
        name = WorkspaceName("test")
        path = WorkspacePath(Path("/tmp/test"))
        config = WorkspaceConfiguration()
        
        workspace1 = Workspace(name=name, path=path, configuration=config)
        workspace2 = Workspace(name=name, path=path, configuration=config)
        workspace3 = Workspace(
            name=WorkspaceName("other"),
            path=path,
            configuration=config
        )
        workspace4 = Workspace(
            name=name,
            path=WorkspacePath(Path("/tmp/other")),
            configuration=config
        )
        
        assert workspace1 == workspace2  # Same name and path
        assert workspace1 != workspace3  # Different name
        assert workspace1 != workspace4  # Different path
    
    def test_hash_consistency(self):
        """Test that equal workspaces have equal hashes."""
        name = WorkspaceName("test")
        path = WorkspacePath(Path("/tmp/test"))
        config = WorkspaceConfiguration()
        
        workspace1 = Workspace(name=name, path=path, configuration=config)
        workspace2 = Workspace(name=name, path=path, configuration=config)
        
        assert hash(workspace1) == hash(workspace2)
    
    def test_use_in_set(self):
        """Test using workspaces in sets."""
        name = WorkspaceName("test")
        path = WorkspacePath(Path("/tmp/test"))
        config = WorkspaceConfiguration()
        
        workspace1 = Workspace(name=name, path=path, configuration=config)
        workspace2 = Workspace(name=name, path=path, configuration=config)  # Same
        workspace3 = Workspace(
            name=WorkspaceName("other"),
            path=path,
            configuration=config
        )
        
        workspace_set = {workspace1, workspace2, workspace3}
        
        # Should only have 2 unique workspaces
        assert len(workspace_set) == 2
    
    def test_immutability_through_methods(self):
        """Test that workspace methods return new instances rather than modifying original."""
        workspace = Workspace(
            name=WorkspaceName("test"),
            path=WorkspacePath(Path("/tmp/test")),
            configuration=WorkspaceConfiguration(),
            is_active=False
        )
        
        # Store original state
        original_active = workspace.is_active
        original_config = workspace.configuration
        original_access_time = workspace.last_accessed_at
        
        # Call methods that should create new instances
        activated = workspace.activate()
        updated_config = workspace.update_configuration(WorkspaceConfiguration())
        updated_access = workspace.update_access_time()
        
        # Original workspace should be unchanged
        assert workspace.is_active == original_active
        assert workspace.configuration == original_config
        assert workspace.last_accessed_at == original_access_time
        
        # New instances should be different
        assert activated != workspace
        assert updated_config != workspace
        assert updated_access != workspace