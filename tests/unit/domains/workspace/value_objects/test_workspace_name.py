"""Unit tests for WorkspaceName value object.

Tests value object behavior, validation, and immutability.
"""

import pytest
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName


class TestWorkspaceName:
    """Test WorkspaceName value object behavior and validation."""
    
    def test_create_valid_workspace_name(self):
        """Test creating a valid workspace name."""
        name = WorkspaceName("test-workspace")
        assert name.value == "test-workspace"
        assert str(name) == "test-workspace"
    
    def test_create_with_underscores(self):
        """Test creating workspace name with underscores."""
        name = WorkspaceName("my_project_workspace")
        assert name.value == "my_project_workspace"
    
    def test_create_with_numbers(self):
        """Test creating workspace name with numbers."""
        name = WorkspaceName("workspace123")
        assert name.value == "workspace123"
    
    def test_create_mixed_format(self):
        """Test creating workspace name with mixed format."""
        name = WorkspaceName("project-v2_final")
        assert name.value == "project-v2_final"
    
    def test_create_default_workspace(self):
        """Test creating the default workspace name."""
        name = WorkspaceName("default")
        assert name.value == "default"
        assert name.is_default() is True
    
    def test_empty_value_raises_error(self):
        """Test that empty value raises ValueError."""
        with pytest.raises(ValueError, match="Workspace name cannot be empty"):
            WorkspaceName("")
    
    def test_none_value_raises_error(self):
        """Test that None value raises ValueError."""
        with pytest.raises(ValueError, match="Workspace name cannot be empty"):
            WorkspaceName(None)
    
    def test_non_string_type_raises_error(self):
        """Test that non-string type raises TypeError."""
        with pytest.raises(TypeError, match="Workspace name must be string"):
            WorkspaceName(123)
    
    def test_too_short_raises_error(self):
        """Test that too short name raises ValueError."""
        with pytest.raises(ValueError, match="Workspace name must be at least 2 characters long"):
            WorkspaceName("a")
    
    def test_too_long_raises_error(self):
        """Test that too long name raises ValueError."""
        long_name = "a" * 51  # 51 characters
        with pytest.raises(ValueError, match="Workspace name must be at most 50 characters long"):
            WorkspaceName(long_name)
    
    def test_invalid_characters_raises_error(self):
        """Test that invalid characters raise ValueError."""
        invalid_names = [
            "test@workspace",  # @ symbol
            "test workspace",  # space
            "test.workspace",  # dot
            "test/workspace",  # slash
            "test\\workspace",  # backslash
            "test$workspace",  # dollar sign
            "test%workspace",  # percent
            "test+workspace",  # plus
            "test=workspace",  # equals
            "test!workspace",  # exclamation
            "test?workspace",  # question mark
            "test#workspace",  # hash
            "test&workspace",  # ampersand
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="must contain only alphanumeric characters"):
                WorkspaceName(invalid_name)
    
    def test_starts_with_hyphen_raises_error(self):
        """Test that starting with hyphen raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            WorkspaceName("-test-workspace")
    
    def test_ends_with_hyphen_raises_error(self):
        """Test that ending with hyphen raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            WorkspaceName("test-workspace-")
    
    def test_starts_with_underscore_raises_error(self):
        """Test that starting with underscore raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            WorkspaceName("_test_workspace")
    
    def test_ends_with_underscore_raises_error(self):
        """Test that ending with underscore raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            WorkspaceName("test_workspace_")
    
    def test_only_special_characters_raises_error(self):
        """Test that only special characters raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            WorkspaceName("---")
    
    def test_normalize_simple(self):
        """Test normalizing simple name."""
        normalized = WorkspaceName.normalize("Simple Name")
        assert normalized == "simple-name"
    
    def test_normalize_complex(self):
        """Test normalizing complex name."""
        normalized = WorkspaceName.normalize("   My  Project  Name  v2.0   ")
        assert normalized == "my-project-name-v2-0"
    
    def test_normalize_special_characters(self):
        """Test normalizing name with special characters."""
        normalized = WorkspaceName.normalize("User's Project!")
        assert normalized == "user-s-project"
    
    def test_normalize_empty_string(self):
        """Test normalizing empty string."""
        normalized = WorkspaceName.normalize("")
        assert normalized == "workspace"
    
    def test_normalize_whitespace_only(self):
        """Test normalizing whitespace-only string."""
        normalized = WorkspaceName.normalize("   ")
        assert normalized == "workspace"
    
    def test_normalize_too_long(self):
        """Test normalizing too long name."""
        long_name = "This is a very long workspace name that exceeds the maximum allowed length"
        normalized = WorkspaceName.normalize(long_name)
        
        assert len(normalized) <= 50
        assert not normalized.endswith("-")  # Should not end with hyphen
    
    def test_normalize_consecutive_separators(self):
        """Test normalizing name with consecutive separators."""
        normalized = WorkspaceName.normalize("test---name___here")
        assert normalized == "test-name-here"
    
    def test_from_display_name(self):
        """Test creating workspace name from display name."""
        name = WorkspaceName.from_display_name("My Project Workspace")
        assert name.value == "my-project-workspace"
    
    def test_from_display_name_special_characters(self):
        """Test creating workspace name from display name with special characters."""
        name = WorkspaceName.from_display_name("User's Amazing Project v2.0!")
        assert name.value == "user-s-amazing-project-v2-0"
    
    def test_is_default_true(self):
        """Test checking if workspace name is default."""
        default_name = WorkspaceName("default")
        assert default_name.is_default() is True
    
    def test_is_default_false(self):
        """Test checking if workspace name is not default."""
        other_name = WorkspaceName("my-workspace")
        assert other_name.is_default() is False
    
    def test_is_valid_format_true(self):
        """Test checking valid workspace name format."""
        valid_names = [
            "test",
            "test-workspace",
            "my_project",
            "workspace123",
            "a1",
            "test-name-here",
            "under_score_name",
            "mixed-under_score",
        ]
        
        for name in valid_names:
            assert WorkspaceName.is_valid_format(name) is True
    
    def test_is_valid_format_false(self):
        """Test checking invalid workspace name format."""
        invalid_names = [
            "",
            "a",  # Too short
            "a" * 51,  # Too long
            "-start-hyphen",  # Starts with hyphen
            "end-hyphen-",  # Ends with hyphen
            "_start_underscore",  # Starts with underscore
            "end_underscore_",  # Ends with underscore
            "test workspace",  # Contains space
            "test.name",  # Contains dot
            "test@name",  # Contains @
            "test/name",  # Contains slash
        ]
        
        for name in invalid_names:
            assert WorkspaceName.is_valid_format(name) is False
    
    def test_get_display_name(self):
        """Test getting display name from workspace name."""
        name = WorkspaceName("my-project-workspace")
        display_name = name.get_display_name()
        assert display_name == "My Project Workspace"
    
    def test_get_display_name_underscores(self):
        """Test getting display name with underscores."""
        name = WorkspaceName("my_project_workspace")
        display_name = name.get_display_name()
        assert display_name == "My Project Workspace"
    
    def test_get_display_name_mixed(self):
        """Test getting display name with mixed separators."""
        name = WorkspaceName("my-project_workspace")
        display_name = name.get_display_name()
        assert display_name == "My Project Workspace"
    
    def test_get_display_name_numbers(self):
        """Test getting display name with numbers."""
        name = WorkspaceName("project-v2-final")
        display_name = name.get_display_name()
        assert display_name == "Project V2 Final"
    
    def test_equality(self):
        """Test workspace name equality."""
        name1 = WorkspaceName("test-workspace")
        name2 = WorkspaceName("test-workspace")
        name3 = WorkspaceName("other-workspace")
        
        assert name1 == name2
        assert name1 != name3
        assert name2 != name3
    
    def test_hash_consistency(self):
        """Test that equal workspace names have equal hashes."""
        name1 = WorkspaceName("test-workspace")
        name2 = WorkspaceName("test-workspace")
        name3 = WorkspaceName("other-workspace")
        
        assert hash(name1) == hash(name2)
        assert hash(name1) != hash(name3)
    
    def test_use_in_set(self):
        """Test using workspace names in sets."""
        name1 = WorkspaceName("test-workspace")
        name2 = WorkspaceName("test-workspace")  # Same value
        name3 = WorkspaceName("other-workspace")
        
        name_set = {name1, name2, name3}
        
        # Should only have 2 unique names
        assert len(name_set) == 2
        assert name1 in name_set
        assert name3 in name_set
    
    def test_use_in_dict(self):
        """Test using workspace names as dictionary keys."""
        name1 = WorkspaceName("test-workspace")
        name2 = WorkspaceName("test-workspace")  # Same value
        name3 = WorkspaceName("other-workspace")
        
        name_dict = {
            name1: "first",
            name2: "second",  # Should overwrite first
            name3: "third"
        }
        
        # Should only have 2 entries
        assert len(name_dict) == 2
        assert name_dict[name1] == "second"  # Overwritten
        assert name_dict[name3] == "third"
    
    def test_immutability(self):
        """Test that workspace name is immutable."""
        name = WorkspaceName("test-workspace")
        
        # Should not be able to modify value
        with pytest.raises(AttributeError):
            name.value = "modified"
    
    def test_dataclass_frozen(self):
        """Test that dataclass is frozen."""
        name = WorkspaceName("test-workspace")
        
        # Should not be able to add new attributes
        with pytest.raises(AttributeError):
            name.new_attribute = "value"
    
    def test_boundary_conditions(self):
        """Test boundary conditions for length validation."""
        # Minimum valid length (2 characters)
        min_valid = WorkspaceName("ab")
        assert min_valid.value == "ab"
        
        # Maximum valid length (50 characters)
        max_valid = "a" * 48 + "bc"  # 50 chars total, starts and ends with letters
        max_name = WorkspaceName(max_valid)
        assert max_name.value == max_valid
        assert len(max_name.value) == 50
    
    def test_comparison_operators(self):
        """Test comparison operators for workspace names."""
        name1 = WorkspaceName("aaa")
        name2 = WorkspaceName("bbb")
        name3 = WorkspaceName("ccc")
        
        # Test ordering
        assert name1 < name2 < name3
        assert name3 > name2 > name1
        assert name1 <= name2 <= name3
        assert name3 >= name2 >= name1
        
        # Test equality
        name1_copy = WorkspaceName("aaa")
        assert name1 <= name1_copy
        assert name1 >= name1_copy
    
    def test_sorting(self):
        """Test sorting workspace names."""
        names = [
            WorkspaceName("zzz"),
            WorkspaceName("aaa"),
            WorkspaceName("mmm"),
            WorkspaceName("bbb")
        ]
        
        sorted_names = sorted(names)
        
        assert sorted_names[0].value == "aaa"
        assert sorted_names[1].value == "bbb"
        assert sorted_names[2].value == "mmm"
        assert sorted_names[3].value == "zzz"