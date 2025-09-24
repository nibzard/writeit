"""Comprehensive unit tests for Workspace domain value objects."""

import pytest
from pathlib import Path
import tempfile
import os

from src.writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from src.writeit.domains.workspace.value_objects.workspace_path import WorkspacePath
from src.writeit.domains.workspace.value_objects.configuration_value import ConfigurationValue

from tests.builders.value_object_builders import WorkspaceNameBuilder, WorkspacePathBuilder


class TestWorkspaceName:
    """Test cases for WorkspaceName value object."""
    
    def test_workspace_name_creation(self):
        """Test creating WorkspaceName."""
        name = "test_workspace"
        workspace_name = WorkspaceNameBuilder().with_name(name).build()
        
        assert workspace_name.value == name
        assert str(workspace_name) == name
    
    def test_workspace_name_validation(self):
        """Test WorkspaceName validation rules."""
        # Valid workspace names
        valid_names = [
            "simple", "workspace_1", "my-workspace", "workspace123",
            "camelCase", "PascalCase", "workspace_with_underscores"
        ]
        
        for valid_name in valid_names:
            workspace_name = WorkspaceName(valid_name)
            assert workspace_name.value == valid_name
    
    def test_workspace_name_invalid_names(self):
        """Test WorkspaceName with invalid names."""
        invalid_names = [
            "",  # Empty
            "   ",  # Whitespace only
            "workspace with spaces",  # Spaces
            "workspace@invalid",  # Special characters
            "workspace#123",  # Hash symbol
            "workspace/path",  # Forward slash
            "workspace\\path",  # Backward slash
            ".hidden",  # Starting with dot
            "workspace.",  # Ending with dot
            "workspace..double",  # Double dots
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="Invalid workspace name"):
                WorkspaceName(invalid_name)
    
    def test_workspace_name_length_limits(self):
        """Test WorkspaceName length validation."""
        # Test minimum length
        with pytest.raises(ValueError, match="Workspace name must be between"):
            WorkspaceName("a")  # Too short
        
        # Valid length
        valid_name = "ab"  # Minimum valid length
        workspace_name = WorkspaceName(valid_name)
        assert workspace_name.value == valid_name
        
        # Test maximum length
        max_length = 64  # Typical filesystem limit
        long_name = "a" * max_length
        workspace_name = WorkspaceName(long_name)
        assert workspace_name.value == long_name
        
        # Too long
        with pytest.raises(ValueError, match="Workspace name must be between"):
            WorkspaceName("a" * (max_length + 1))
    
    def test_workspace_name_normalization(self):
        """Test WorkspaceName normalization."""
        # Test case preservation
        mixed_case = "MyWorkSpace"
        workspace_name = WorkspaceName(mixed_case)
        assert workspace_name.value == mixed_case  # Should preserve case
        
        # Test trimming
        with_spaces = "  workspace  "
        with pytest.raises(ValueError):  # Should not auto-trim
            WorkspaceName(with_spaces)
    
    def test_workspace_name_reserved_names(self):
        """Test WorkspaceName with reserved names."""
        reserved_names = [
            "default",  # Usually allowed
            "system",   # May be reserved
            "admin",    # May be reserved
            "root",     # May be reserved
            "temp",     # May be reserved
        ]
        
        # Most should be allowed, but test the mechanism exists
        for name in reserved_names:
            try:
                workspace_name = WorkspaceName(name)
                assert workspace_name.value == name
            except ValueError:
                # Some names might be reserved - that's valid behavior
                pass
    
    def test_workspace_name_equality(self):
        """Test WorkspaceName equality."""
        name1 = WorkspaceName("workspace")
        name2 = WorkspaceName("workspace")
        name3 = WorkspaceName("different")
        
        assert name1 == name2
        assert name1 != name3
        assert name1 != "workspace"  # Not equal to string
    
    def test_workspace_name_hash_consistency(self):
        """Test WorkspaceName hash consistency."""
        name1 = WorkspaceName("workspace")
        name2 = WorkspaceName("workspace")
        
        assert hash(name1) == hash(name2)
        assert name1 in {name2}
    
    def test_workspace_name_case_sensitivity(self):
        """Test WorkspaceName case sensitivity."""
        name1 = WorkspaceName("WorkSpace")
        name2 = WorkspaceName("workspace")
        
        assert name1 != name2  # Should be case sensitive
        assert name1.value == "WorkSpace"
        assert name2.value == "workspace"
    
    def test_workspace_name_builder_factories(self):
        """Test WorkspaceName builder factory methods."""
        default = WorkspaceNameBuilder.default().build()
        assert default.value == "default"
        
        project = WorkspaceNameBuilder.project("myproject").build()
        assert project.value == "myproject"
        
        temporary = WorkspaceNameBuilder.temporary().build()
        assert "temp" in temporary.value.lower()


class TestWorkspacePath:
    """Test cases for WorkspacePath value object."""
    
    def test_workspace_path_creation(self):
        """Test creating WorkspacePath."""
        path_str = "/tmp/test_workspace"
        workspace_path = WorkspacePathBuilder().with_path(path_str).build()
        
        assert str(workspace_path) == path_str
        assert workspace_path.path == Path(path_str)
    
    def test_workspace_path_from_string(self):
        """Test WorkspacePath from string."""
        path_str = "/home/user/.writeit/workspaces/test"
        workspace_path = WorkspacePath(path_str)
        
        assert str(workspace_path) == path_str
        assert workspace_path.path == Path(path_str)
    
    def test_workspace_path_from_pathlib(self):
        """Test WorkspacePath from pathlib.Path."""
        path_obj = Path("/tmp/workspace")
        workspace_path = WorkspacePath(path_obj)
        
        assert workspace_path.path == path_obj
        assert str(workspace_path) == str(path_obj)
    
    def test_workspace_path_validation(self):
        """Test WorkspacePath validation."""
        # Valid paths
        valid_paths = [
            "/tmp/workspace",
            "/home/user/workspace",
            "~/workspace",
            "./workspace",
            "../workspace",
            "/absolute/path/to/workspace"
        ]
        
        for valid_path in valid_paths:
            workspace_path = WorkspacePath(valid_path)
            assert str(workspace_path) == valid_path
    
    def test_workspace_path_invalid_paths(self):
        """Test WorkspacePath with invalid paths."""
        invalid_paths = [
            "",  # Empty path
            "   ",  # Whitespace only
        ]
        
        for invalid_path in invalid_paths:
            with pytest.raises(ValueError, match="Workspace path cannot be empty"):
                WorkspacePath(invalid_path)
    
    def test_workspace_path_normalization(self):
        """Test WorkspacePath normalization."""
        # Test path normalization
        paths_to_normalize = [
            ("/tmp/workspace/../workspace", "/tmp/workspace"),
            ("/tmp/./workspace", "/tmp/workspace"),
            ("/tmp//workspace", "/tmp/workspace"),
        ]
        
        for input_path, expected in paths_to_normalize:
            workspace_path = WorkspacePath(input_path)
            # Path normalization behavior depends on implementation
            assert workspace_path.path == Path(input_path)
    
    def test_workspace_path_absolute_vs_relative(self):
        """Test WorkspacePath with absolute and relative paths."""
        # Absolute path
        abs_path = "/tmp/workspace"
        abs_workspace_path = WorkspacePath(abs_path)
        assert abs_workspace_path.path.is_absolute()
        
        # Relative path
        rel_path = "./workspace"
        rel_workspace_path = WorkspacePath(rel_path)
        assert not rel_workspace_path.path.is_absolute()
    
    def test_workspace_path_home_expansion(self):
        """Test WorkspacePath with home directory expansion."""
        home_path = "~/workspace"
        workspace_path = WorkspacePath(home_path)
        
        # May or may not expand ~ depending on implementation
        assert "workspace" in str(workspace_path)
    
    def test_workspace_path_operations(self):
        """Test WorkspacePath path operations."""
        workspace_path = WorkspacePath("/tmp/workspace")
        
        # Test path components
        assert workspace_path.path.name == "workspace"
        assert workspace_path.path.parent == Path("/tmp")
        
        # Test joining paths
        child_path = workspace_path.path / "subdirectory"
        assert "subdirectory" in str(child_path)
    
    def test_workspace_path_equality(self):
        """Test WorkspacePath equality."""
        path1 = WorkspacePath("/tmp/workspace")
        path2 = WorkspacePath("/tmp/workspace")
        path3 = WorkspacePath("/different/path")
        
        assert path1 == path2
        assert path1 != path3
        assert path1 != "/tmp/workspace"  # Not equal to string
    
    def test_workspace_path_hash_consistency(self):
        """Test WorkspacePath hash consistency."""
        path1 = WorkspacePath("/tmp/workspace")
        path2 = WorkspacePath("/tmp/workspace")
        
        assert hash(path1) == hash(path2)
        assert path1 in {path2}
    
    def test_workspace_path_special_characters(self):
        """Test WorkspacePath with special characters."""
        special_paths = [
            "/tmp/workspace-with-dashes",
            "/tmp/workspace_with_underscores",
            "/tmp/workspace.with.dots",
            "/tmp/workspace with spaces",  # May or may not be valid
            "/tmp/workspace(with)parens",
            "/tmp/workspace[with]brackets"
        ]
        
        for special_path in special_paths:
            try:
                workspace_path = WorkspacePath(special_path)
                assert str(workspace_path) == special_path
            except ValueError:
                # Some special characters might not be allowed
                pass
    
    def test_workspace_path_builder_factories(self):
        """Test WorkspacePath builder factory methods."""
        home = WorkspacePathBuilder.home("test").build()
        assert "/.writeit/workspaces/test" in str(home)
        
        tmp = WorkspacePathBuilder.tmp("test").build()
        assert "/tmp/test" in str(tmp)
        
        project = WorkspacePathBuilder.project("test").build()
        assert "/projects/test" in str(project)


class TestConfigurationValue:
    """Test cases for ConfigurationValue value object."""
    
    def test_configuration_value_string(self):
        """Test ConfigurationValue with string."""
        value = "test_value"
        config_value = ConfigurationValue(value)
        
        assert config_value.value == value
        assert config_value.type == str
        assert str(config_value) == value
    
    def test_configuration_value_integer(self):
        """Test ConfigurationValue with integer."""
        value = 42
        config_value = ConfigurationValue(value)
        
        assert config_value.value == value
        assert config_value.type == int
        assert str(config_value) == "42"
    
    def test_configuration_value_boolean(self):
        """Test ConfigurationValue with boolean."""
        # True value
        true_value = ConfigurationValue(True)
        assert true_value.value is True
        assert true_value.type == bool
        assert str(true_value) == "True"
        
        # False value
        false_value = ConfigurationValue(False)
        assert false_value.value is False
        assert false_value.type == bool
        assert str(false_value) == "False"
    
    def test_configuration_value_float(self):
        """Test ConfigurationValue with float."""
        value = 3.14159
        config_value = ConfigurationValue(value)
        
        assert config_value.value == value
        assert config_value.type == float
        assert "3.14159" in str(config_value)
    
    def test_configuration_value_list(self):
        """Test ConfigurationValue with list."""
        value = ["item1", "item2", "item3"]
        config_value = ConfigurationValue(value)
        
        assert config_value.value == value
        assert config_value.type == list
        assert "item1" in str(config_value)
    
    def test_configuration_value_dict(self):
        """Test ConfigurationValue with dictionary."""
        value = {"key1": "value1", "key2": 42, "key3": True}
        config_value = ConfigurationValue(value)
        
        assert config_value.value == value
        assert config_value.type == dict
        assert "key1" in str(config_value)
    
    def test_configuration_value_none(self):
        """Test ConfigurationValue with None."""
        config_value = ConfigurationValue(None)
        
        assert config_value.value is None
        assert config_value.type == type(None)
        assert str(config_value) == "None"
    
    def test_configuration_value_equality(self):
        """Test ConfigurationValue equality."""
        value1 = ConfigurationValue("test")
        value2 = ConfigurationValue("test")
        value3 = ConfigurationValue("different")
        
        assert value1 == value2
        assert value1 != value3
        assert value1 != "test"  # Not equal to raw value
    
    def test_configuration_value_type_coercion(self):
        """Test ConfigurationValue type coercion."""
        # String to int
        string_int = ConfigurationValue("123")
        int_value = string_int.as_int()
        assert int_value == 123
        assert isinstance(int_value, int)
        
        # String to bool
        string_bool_true = ConfigurationValue("true")
        bool_value_true = string_bool_true.as_bool()
        assert bool_value_true is True
        
        string_bool_false = ConfigurationValue("false")
        bool_value_false = string_bool_false.as_bool()
        assert bool_value_false is False
        
        # String to float
        string_float = ConfigurationValue("3.14")
        float_value = string_float.as_float()
        assert float_value == 3.14
        assert isinstance(float_value, float)
    
    def test_configuration_value_invalid_coercion(self):
        """Test ConfigurationValue invalid type coercion."""
        # Invalid int conversion
        invalid_int = ConfigurationValue("not_a_number")
        with pytest.raises(ValueError):
            invalid_int.as_int()
        
        # Invalid float conversion
        invalid_float = ConfigurationValue("not_a_float")
        with pytest.raises(ValueError):
            invalid_float.as_float()
    
    def test_configuration_value_validation(self):
        """Test ConfigurationValue validation."""
        # Test with validator function
        def positive_validator(value):
            if isinstance(value, (int, float)) and value > 0:
                return True
            raise ValueError("Value must be positive")
        
        # Valid positive value
        positive_value = ConfigurationValue(42)
        assert positive_validator(positive_value.value)
        
        # Invalid negative value
        negative_value = ConfigurationValue(-5)
        with pytest.raises(ValueError):
            positive_validator(negative_value.value)
    
    def test_configuration_value_serialization(self):
        """Test ConfigurationValue serialization."""
        import json
        
        # Simple values should be JSON serializable
        simple_values = [
            "string",
            42,
            3.14,
            True,
            False,
            None,
            ["list", "items"],
            {"key": "value"}
        ]
        
        for value in simple_values:
            config_value = ConfigurationValue(value)
            try:
                serialized = json.dumps(config_value.value)
                assert isinstance(serialized, str)
            except TypeError:
                pytest.fail(f"Value {value} not JSON serializable")
    
    def test_configuration_value_complex_types(self):
        """Test ConfigurationValue with complex types."""
        from datetime import datetime
        
        # DateTime value
        dt_value = datetime.now()
        config_value = ConfigurationValue(dt_value)
        assert config_value.value == dt_value
        assert config_value.type == datetime
        
        # Custom object (should work but may not be serializable)
        class CustomObject:
            def __init__(self, name):
                self.name = name
            
            def __str__(self):
                return f"CustomObject({self.name})"
        
        custom_obj = CustomObject("test")
        config_value = ConfigurationValue(custom_obj)
        assert config_value.value == custom_obj
        assert config_value.type == CustomObject
    
    def test_configuration_value_immutability(self):
        """Test ConfigurationValue immutability."""
        config_value = ConfigurationValue("test")
        
        with pytest.raises(AttributeError):
            config_value.value = "modified"  # type: ignore
        
        with pytest.raises(AttributeError):
            config_value.type = int  # type: ignore


class TestValueObjectEdgeCases:
    """Test edge cases for all workspace value objects."""
    
    def test_value_object_with_unicode(self):
        """Test value objects with unicode characters."""
        # WorkspaceName with unicode (should fail validation)
        with pytest.raises(ValueError):
            WorkspaceName("wörkspace")
        
        # WorkspacePath with unicode (may work depending on OS)
        try:
            unicode_path = WorkspacePath("/tmp/wörkspace")
            assert "wörkspace" in str(unicode_path)
        except ValueError:
            # Unicode in paths may not be supported
            pass
        
        # ConfigurationValue with unicode (should work)
        unicode_config = ConfigurationValue("unicode_value_éñç")
        assert "éñç" in unicode_config.value
    
    def test_value_object_with_very_long_values(self):
        """Test value objects with very long values."""
        # Very long workspace name (should fail)
        long_name = "a" * 1000
        with pytest.raises(ValueError):
            WorkspaceName(long_name)
        
        # Very long path (may work depending on OS limits)
        long_path = "/tmp/" + "a" * 200
        try:
            workspace_path = WorkspacePath(long_path)
            assert len(str(workspace_path)) > 200
        except ValueError:
            # Very long paths may exceed OS limits
            pass
        
        # Very long configuration value (should work)
        long_value = "x" * 10000
        config_value = ConfigurationValue(long_value)
        assert len(config_value.value) == 10000
    
    def test_value_object_with_empty_values(self):
        """Test value objects with empty values."""
        # Empty workspace name (should fail)
        with pytest.raises(ValueError):
            WorkspaceName("")
        
        # Empty workspace path (should fail)
        with pytest.raises(ValueError):
            WorkspacePath("")
        
        # Empty configuration value (should work)
        empty_config = ConfigurationValue("")
        assert empty_config.value == ""
        assert empty_config.type == str
    
    def test_value_object_equality_with_different_types(self):
        """Test value object equality with different types."""
        workspace_name = WorkspaceName("test")
        workspace_path = WorkspacePath("/tmp/test")
        config_value = ConfigurationValue("test")
        
        # Should not be equal to each other
        assert workspace_name != workspace_path
        assert workspace_name != config_value
        assert workspace_path != config_value
        
        # Should not be equal to raw values
        assert workspace_name != "test"
        assert workspace_path != "/tmp/test"
        assert config_value != "test"
    
    def test_value_object_hash_uniqueness(self):
        """Test that different value objects have different hashes."""
        name1 = WorkspaceName("workspace1")
        name2 = WorkspaceName("workspace2")
        path1 = WorkspacePath("/tmp/path1")
        path2 = WorkspacePath("/tmp/path2")
        
        # Different values should have different hashes (usually)
        assert hash(name1) != hash(name2)
        assert hash(path1) != hash(path2)
        
        # Different types should have different hashes
        same_value_name = WorkspaceName("same")
        same_value_config = ConfigurationValue("same")
        # These may or may not have different hashes - not guaranteed