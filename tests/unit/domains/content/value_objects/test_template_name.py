"""Unit tests for TemplateName value object.

Tests value object behavior, validation, and immutability.
"""

import pytest
from writeit.domains.content.value_objects.template_name import TemplateName


class TestTemplateName:
    """Test TemplateName value object behavior and validation."""
    
    def test_create_valid_template_name(self):
        """Test creating a valid template name."""
        name = TemplateName("article-template")
        assert name.value == "article-template"
        assert str(name) == "article-template"
    
    def test_create_with_underscores(self):
        """Test creating template name with underscores."""
        name = TemplateName("blog_post_template")
        assert name.value == "blog_post_template"
    
    def test_create_with_numbers(self):
        """Test creating template name with numbers."""
        name = TemplateName("template123")
        assert name.value == "template123"
    
    def test_create_mixed_format(self):
        """Test creating template name with mixed format."""
        name = TemplateName("quick-article-v2_final")
        assert name.value == "quick-article-v2_final"
    
    def test_empty_value_raises_error(self):
        """Test that empty value raises ValueError."""
        with pytest.raises(ValueError, match="Template name cannot be empty"):
            TemplateName("")
    
    def test_none_value_raises_error(self):
        """Test that None value raises ValueError."""
        with pytest.raises(ValueError, match="Template name cannot be empty"):
            TemplateName(None)
    
    def test_non_string_type_raises_error(self):
        """Test that non-string type raises TypeError."""
        with pytest.raises(TypeError, match="Template name must be string"):
            TemplateName(123)
    
    def test_too_short_raises_error(self):
        """Test that too short name raises ValueError."""
        with pytest.raises(ValueError, match="Template name must be at least 2 characters long"):
            TemplateName("a")
    
    def test_too_long_raises_error(self):
        """Test that too long name raises ValueError."""
        long_name = "a" * 101  # 101 characters
        with pytest.raises(ValueError, match="Template name must be at most 100 characters long"):
            TemplateName(long_name)
    
    def test_invalid_characters_raises_error(self):
        """Test that invalid characters raise ValueError."""
        invalid_names = [
            "test@template",  # @ symbol
            "test template",  # space
            "test.template",  # dot
            "test/template",  # slash
            "test\\template",  # backslash
            "test$template",  # dollar sign
            "test%template",  # percent
            "test+template",  # plus
            "test=template",  # equals
            "test!template",  # exclamation
            "test?template",  # question mark
            "test#template",  # hash
            "test&template",  # ampersand
            "test(template)",  # parentheses
            "test[template]",  # brackets
            "test{template}",  # braces
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="must contain only alphanumeric characters"):
                TemplateName(invalid_name)
    
    def test_starts_with_hyphen_raises_error(self):
        """Test that starting with hyphen raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            TemplateName("-test-template")
    
    def test_ends_with_hyphen_raises_error(self):
        """Test that ending with hyphen raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            TemplateName("test-template-")
    
    def test_starts_with_underscore_raises_error(self):
        """Test that starting with underscore raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            TemplateName("_test_template")
    
    def test_ends_with_underscore_raises_error(self):
        """Test that ending with underscore raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            TemplateName("test_template_")
    
    def test_only_special_characters_raises_error(self):
        """Test that only special characters raises ValueError."""
        with pytest.raises(ValueError, match="cannot start or end with special characters"):
            TemplateName("---")
    
    def test_normalize_simple(self):
        """Test normalizing simple name."""
        normalized = TemplateName.normalize("Simple Template")
        assert normalized == "simple-template"
    
    def test_normalize_complex(self):
        """Test normalizing complex name."""
        normalized = TemplateName.normalize("   My  Article  Template  v2.0   ")
        assert normalized == "my-article-template-v2-0"
    
    def test_normalize_special_characters(self):
        """Test normalizing name with special characters."""
        normalized = TemplateName.normalize("User's Template!")
        assert normalized == "user-s-template"
    
    def test_normalize_empty_string(self):
        """Test normalizing empty string."""
        normalized = TemplateName.normalize("")
        assert normalized == "template"
    
    def test_normalize_whitespace_only(self):
        """Test normalizing whitespace-only string."""
        normalized = TemplateName.normalize("   ")
        assert normalized == "template"
    
    def test_normalize_too_long(self):
        """Test normalizing too long name."""
        long_name = "This is a very long template name that exceeds the maximum allowed length for template names"
        normalized = TemplateName.normalize(long_name)
        
        assert len(normalized) <= 100
        assert not normalized.endswith("-")  # Should not end with hyphen
    
    def test_normalize_consecutive_separators(self):
        """Test normalizing name with consecutive separators."""
        normalized = TemplateName.normalize("test---template___here")
        assert normalized == "test-template-here"
    
    def test_from_display_name(self):
        """Test creating template name from display name."""
        name = TemplateName.from_display_name("My Article Template")
        assert name.value == "my-article-template"
    
    def test_from_display_name_special_characters(self):
        """Test creating template name from display name with special characters."""
        name = TemplateName.from_display_name("User's Amazing Template v2.0!")
        assert name.value == "user-s-amazing-template-v2-0"
    
    def test_is_valid_format_true(self):
        """Test checking valid template name format."""
        valid_names = [
            "test",
            "test-template",
            "my_template",
            "template123",
            "ab",
            "test-name-here",
            "under_score_name",
            "mixed-under_score",
        ]
        
        for name in valid_names:
            assert TemplateName.is_valid_format(name) is True
    
    def test_is_valid_format_false(self):
        """Test checking invalid template name format."""
        invalid_names = [
            "",
            "a",  # Too short
            "a" * 101,  # Too long
            "-start-hyphen",  # Starts with hyphen
            "end-hyphen-",  # Ends with hyphen
            "_start_underscore",  # Starts with underscore
            "end_underscore_",  # Ends with underscore
            "test template",  # Contains space
            "test.name",  # Contains dot
            "test@name",  # Contains @
            "test/name",  # Contains slash
        ]
        
        for name in invalid_names:
            assert TemplateName.is_valid_format(name) is False
    
    def test_get_display_name(self):
        """Test getting display name from template name."""
        name = TemplateName("my-article-template")
        display_name = name.get_display_name()
        assert display_name == "My Article Template"
    
    def test_get_display_name_underscores(self):
        """Test getting display name with underscores."""
        name = TemplateName("my_blog_template")
        display_name = name.get_display_name()
        assert display_name == "My Blog Template"
    
    def test_get_display_name_mixed(self):
        """Test getting display name with mixed separators."""
        name = TemplateName("my-article_template")
        display_name = name.get_display_name()
        assert display_name == "My Article Template"
    
    def test_get_display_name_numbers(self):
        """Test getting display name with numbers."""
        name = TemplateName("template-v2-final")
        display_name = name.get_display_name()
        assert display_name == "Template V2 Final"
    
    def test_get_file_extension(self):
        """Test getting appropriate file extension for template."""
        name = TemplateName("article-template")
        extension = name.get_file_extension()
        assert extension == ".yaml"
    
    def test_get_filename(self):
        """Test getting filename with extension."""
        name = TemplateName("article-template")
        filename = name.get_filename()
        assert filename == "article-template.yaml"
    
    def test_is_builtin_template(self):
        """Test checking if template is a built-in template."""
        builtin_names = [
            "article",
            "blog-post",
            "technical-doc",
            "email",
            "summary"
        ]
        
        for builtin_name in builtin_names:
            name = TemplateName(builtin_name)
            assert name.is_builtin() is True
        
        custom_name = TemplateName("my-custom-template")
        assert custom_name.is_builtin() is False
    
    def test_get_category_from_name(self):
        """Test extracting category from template name."""
        name = TemplateName("article-formal")
        category = name.get_category()
        assert category == "article"
        
        name2 = TemplateName("blog-casual")
        category2 = name2.get_category()
        assert category2 == "blog"
        
        # Single word name returns itself as category
        name3 = TemplateName("email")
        category3 = name3.get_category()
        assert category3 == "email"
    
    def test_equality(self):
        """Test template name equality."""
        name1 = TemplateName("test-template")
        name2 = TemplateName("test-template")
        name3 = TemplateName("other-template")
        
        assert name1 == name2
        assert name1 != name3
        assert name2 != name3
    
    def test_hash_consistency(self):
        """Test that equal template names have equal hashes."""
        name1 = TemplateName("test-template")
        name2 = TemplateName("test-template")
        name3 = TemplateName("other-template")
        
        assert hash(name1) == hash(name2)
        assert hash(name1) != hash(name3)
    
    def test_use_in_set(self):
        """Test using template names in sets."""
        name1 = TemplateName("test-template")
        name2 = TemplateName("test-template")  # Same value
        name3 = TemplateName("other-template")
        
        name_set = {name1, name2, name3}
        
        # Should only have 2 unique names
        assert len(name_set) == 2
        assert name1 in name_set
        assert name3 in name_set
    
    def test_use_in_dict(self):
        """Test using template names as dictionary keys."""
        name1 = TemplateName("test-template")
        name2 = TemplateName("test-template")  # Same value
        name3 = TemplateName("other-template")
        
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
        """Test that template name is immutable."""
        name = TemplateName("test-template")
        
        # Should not be able to modify value
        with pytest.raises(AttributeError):
            name.value = "modified"
    
    def test_dataclass_frozen(self):
        """Test that dataclass is frozen."""
        name = TemplateName("test-template")
        
        # Should not be able to add new attributes
        with pytest.raises(AttributeError):
            name.new_attribute = "value"
    
    def test_boundary_conditions(self):
        """Test boundary conditions for length validation."""
        # Minimum valid length (2 characters)
        min_valid = TemplateName("ab")
        assert min_valid.value == "ab"
        
        # Maximum valid length (100 characters)
        max_valid = "a" * 98 + "bc"  # 100 chars total, starts and ends with letters
        max_name = TemplateName(max_valid)
        assert max_name.value == max_valid
        assert len(max_name.value) == 100
    
    def test_comparison_operators(self):
        """Test comparison operators for template names."""
        name1 = TemplateName("aaa")
        name2 = TemplateName("bbb")
        name3 = TemplateName("ccc")
        
        # Test ordering
        assert name1 < name2 < name3
        assert name3 > name2 > name1
        assert name1 <= name2 <= name3
        assert name3 >= name2 >= name1
        
        # Test equality
        name1_copy = TemplateName("aaa")
        assert name1 <= name1_copy
        assert name1 >= name1_copy
    
    def test_sorting(self):
        """Test sorting template names."""
        names = [
            TemplateName("zzz"),
            TemplateName("aaa"),
            TemplateName("mmm"),
            TemplateName("bbb")
        ]
        
        sorted_names = sorted(names)
        
        assert sorted_names[0].value == "aaa"
        assert sorted_names[1].value == "bbb"
        assert sorted_names[2].value == "mmm"
        assert sorted_names[3].value == "zzz"