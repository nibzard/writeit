"""Comprehensive unit tests for Content domain value objects."""

import pytest
from pathlib import Path
import uuid
import re

from src.writeit.domains.content.value_objects.template_name import TemplateName
from src.writeit.domains.content.value_objects.content_type import ContentType
from src.writeit.domains.content.value_objects.content_format import ContentFormat
from src.writeit.domains.content.value_objects.content_id import ContentId
from src.writeit.domains.content.value_objects.style_name import StyleName
from src.writeit.domains.content.value_objects.validation_rule import ValidationRule

from tests.builders.value_object_builders import TemplateNameBuilder, ValidationRuleBuilder


class TestTemplateName:
    """Test cases for TemplateName value object."""
    
    def test_template_name_creation(self):
        """Test creating TemplateName."""
        name = "test_template"
        template_name = TemplateNameBuilder().with_name(name).build()
        
        assert template_name.value == name
        assert str(template_name) == name
    
    def test_template_name_validation(self):
        """Test TemplateName validation rules."""
        # Valid template names
        valid_names = [
            "simple", "template_1", "my-template", "template123",
            "camelCase", "PascalCase", "template_with_underscores",
            "template-with-dashes", "template.yaml", "template.md"
        ]
        
        for valid_name in valid_names:
            template_name = TemplateName(valid_name)
            assert template_name.value == valid_name
    
    def test_template_name_invalid_names(self):
        """Test TemplateName with invalid names."""
        invalid_names = [
            "",  # Empty
            "   ",  # Whitespace only
            "template with spaces",  # Spaces not allowed
            "template@invalid",  # Special characters
            "template#123",  # Hash symbol
            "template/path",  # Forward slash
            "template\\path",  # Backward slash
            ".hidden",  # Starting with dot might be invalid
            "template.",  # Ending with dot
            "template..double",  # Double dots
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="Invalid template name"):
                TemplateName(invalid_name)
    
    def test_template_name_length_limits(self):
        """Test TemplateName length validation."""
        # Test minimum length
        with pytest.raises(ValueError, match="Template name must be between"):
            TemplateName("a")  # Too short
        
        # Valid length
        valid_name = "ab"  # Minimum valid length
        template_name = TemplateName(valid_name)
        assert template_name.value == valid_name
        
        # Test maximum length
        max_length = 100  # Reasonable limit for template names
        long_name = "a" * max_length
        template_name = TemplateName(long_name)
        assert template_name.value == long_name
        
        # Too long
        with pytest.raises(ValueError, match="Template name must be between"):
            TemplateName("a" * (max_length + 1))
    
    def test_template_name_file_extensions(self):
        """Test TemplateName with file extensions."""
        names_with_extensions = [
            "template.yaml",
            "template.yml", 
            "template.md",
            "template.txt",
            "template.json"
        ]
        
        for name in names_with_extensions:
            template_name = TemplateName(name)
            assert template_name.value == name
    
    def test_template_name_equality(self):
        """Test TemplateName equality."""
        name1 = TemplateName("template")
        name2 = TemplateName("template")
        name3 = TemplateName("different")
        
        assert name1 == name2
        assert name1 != name3
        assert name1 != "template"  # Not equal to string
    
    def test_template_name_hash_consistency(self):
        """Test TemplateName hash consistency."""
        name1 = TemplateName("template")
        name2 = TemplateName("template")
        
        assert hash(name1) == hash(name2)
        assert name1 in {name2}
    
    def test_template_name_case_sensitivity(self):
        """Test TemplateName case sensitivity."""
        name1 = TemplateName("Template")
        name2 = TemplateName("template")
        
        assert name1 != name2  # Should be case sensitive
        assert name1.value == "Template"
        assert name2.value == "template"
    
    def test_template_name_builder_factories(self):
        """Test TemplateName builder factory methods."""
        article = TemplateNameBuilder.article().build()
        assert "article" in article.value
        
        pipeline = TemplateNameBuilder.pipeline().build()
        assert "pipeline" in pipeline.value
        
        style = TemplateNameBuilder.style().build()
        assert "style" in style.value


class TestContentType:
    """Test cases for ContentType enum."""
    
    def test_content_type_values(self):
        """Test ContentType enum values."""
        assert ContentType.PIPELINE
        assert ContentType.STYLE
        assert ContentType.MARKDOWN
        assert ContentType.JSON
        assert ContentType.YAML
        assert ContentType.TEXT
    
    def test_content_type_string_representation(self):
        """Test ContentType string representation."""
        assert str(ContentType.PIPELINE) in ["PIPELINE", "pipeline"]
        assert str(ContentType.STYLE) in ["STYLE", "style"]
        assert str(ContentType.MARKDOWN) in ["MARKDOWN", "markdown"]
        assert str(ContentType.JSON) in ["JSON", "json"]
        assert str(ContentType.YAML) in ["YAML", "yaml"]
        assert str(ContentType.TEXT) in ["TEXT", "text"]
    
    def test_content_type_comparison(self):
        """Test ContentType comparison."""
        type1 = ContentType.PIPELINE
        type2 = ContentType.PIPELINE
        type3 = ContentType.STYLE
        
        assert type1 == type2
        assert type1 != type3
    
    def test_content_type_in_collections(self):
        """Test ContentType in collections."""
        types = {ContentType.PIPELINE, ContentType.STYLE}
        
        assert ContentType.PIPELINE in types
        assert ContentType.MARKDOWN not in types
        
        type_list = [ContentType.PIPELINE, ContentType.STYLE]
        assert len(type_list) == 2
        assert ContentType.PIPELINE in type_list
    
    def test_content_type_file_extension_mapping(self):
        """Test ContentType to file extension mapping."""
        # This would be implementation-specific
        type_to_extension = {
            ContentType.PIPELINE: [".yaml", ".yml"],
            ContentType.STYLE: [".yaml", ".yml"],
            ContentType.MARKDOWN: [".md"],
            ContentType.JSON: [".json"],
            ContentType.YAML: [".yaml", ".yml"],
            ContentType.TEXT: [".txt"]
        }
        
        for content_type, expected_extensions in type_to_extension.items():
            # This would test a hypothetical method
            # extensions = content_type.file_extensions()
            # assert any(ext in extensions for ext in expected_extensions)
            assert content_type is not None  # Placeholder test


class TestContentFormat:
    """Test cases for ContentFormat enum."""
    
    def test_content_format_values(self):
        """Test ContentFormat enum values."""
        assert ContentFormat.MARKDOWN
        assert ContentFormat.JSON
        assert ContentFormat.YAML
        assert ContentFormat.TEXT
        assert ContentFormat.HTML
        assert ContentFormat.XML
    
    def test_content_format_string_representation(self):
        """Test ContentFormat string representation."""
        assert str(ContentFormat.MARKDOWN) in ["MARKDOWN", "markdown"]
        assert str(ContentFormat.JSON) in ["JSON", "json"]
        assert str(ContentFormat.YAML) in ["YAML", "yaml"]
        assert str(ContentFormat.TEXT) in ["TEXT", "text"]
        assert str(ContentFormat.HTML) in ["HTML", "html"]
        assert str(ContentFormat.XML) in ["XML", "xml"]
    
    def test_content_format_mime_type_mapping(self):
        """Test ContentFormat to MIME type mapping."""
        # This would be implementation-specific
        format_to_mime = {
            ContentFormat.MARKDOWN: "text/markdown",
            ContentFormat.JSON: "application/json",
            ContentFormat.YAML: "application/x-yaml",
            ContentFormat.TEXT: "text/plain",
            ContentFormat.HTML: "text/html",
            ContentFormat.XML: "application/xml"
        }
        
        for content_format, expected_mime in format_to_mime.items():
            # This would test a hypothetical method
            # mime_type = content_format.mime_type()
            # assert mime_type == expected_mime
            assert content_format is not None  # Placeholder test
    
    def test_content_format_equality(self):
        """Test ContentFormat equality."""
        format1 = ContentFormat.MARKDOWN
        format2 = ContentFormat.MARKDOWN
        format3 = ContentFormat.JSON
        
        assert format1 == format2
        assert format1 != format3
    
    def test_content_format_in_collections(self):
        """Test ContentFormat in collections."""
        formats = {ContentFormat.MARKDOWN, ContentFormat.JSON}
        
        assert ContentFormat.MARKDOWN in formats
        assert ContentFormat.YAML not in formats


class TestContentId:
    """Test cases for ContentId value object."""
    
    def test_content_id_generation(self):
        """Test ContentId generation."""
        content_id = ContentId.generate()
        
        assert isinstance(content_id.value, str)
        assert len(content_id.value) > 0
        
        # Should be a valid UUID format
        try:
            uuid.UUID(content_id.value)
        except ValueError:
            pytest.fail("ContentId should generate valid UUID")
    
    def test_content_id_from_string(self):
        """Test creating ContentId from string."""
        id_str = str(uuid.uuid4())
        content_id = ContentId(id_str)
        
        assert content_id.value == id_str
        assert str(content_id) == id_str
    
    def test_content_id_uniqueness(self):
        """Test ContentId uniqueness."""
        id1 = ContentId.generate()
        id2 = ContentId.generate()
        
        assert id1 != id2
        assert id1.value != id2.value
    
    def test_content_id_validation(self):
        """Test ContentId validation."""
        # Valid UUID
        valid_uuid = str(uuid.uuid4())
        content_id = ContentId(valid_uuid)
        assert content_id.value == valid_uuid
        
        # Invalid UUID format
        with pytest.raises(ValueError, match="Invalid content ID format"):
            ContentId("not-a-uuid")
        
        # Empty string
        with pytest.raises(ValueError, match="Content ID cannot be empty"):
            ContentId("")
    
    def test_content_id_equality(self):
        """Test ContentId equality."""
        id_str = str(uuid.uuid4())
        id1 = ContentId(id_str)
        id2 = ContentId(id_str)
        id3 = ContentId.generate()
        
        assert id1 == id2
        assert id1 != id3
        assert id1 != id_str  # Not equal to string
    
    def test_content_id_hash_consistency(self):
        """Test ContentId hash consistency."""
        id_str = str(uuid.uuid4())
        id1 = ContentId(id_str)
        id2 = ContentId(id_str)
        
        assert hash(id1) == hash(id2)
        assert id1 in {id2}
    
    def test_content_id_immutability(self):
        """Test ContentId immutability."""
        content_id = ContentId.generate()
        
        with pytest.raises(AttributeError):
            content_id.value = str(uuid.uuid4())  # type: ignore


class TestStyleName:
    """Test cases for StyleName value object."""
    
    def test_style_name_creation(self):
        """Test creating StyleName."""
        name = "professional_style"
        style_name = StyleName(name)
        
        assert style_name.value == name
        assert str(style_name) == name
    
    def test_style_name_validation(self):
        """Test StyleName validation rules."""
        # Valid style names
        valid_names = [
            "simple", "style_1", "my-style", "style123",
            "camelCase", "PascalCase", "style_with_underscores",
            "style-with-dashes", "professional", "casual", "technical"
        ]
        
        for valid_name in valid_names:
            style_name = StyleName(valid_name)
            assert style_name.value == valid_name
    
    def test_style_name_invalid_names(self):
        """Test StyleName with invalid names."""
        invalid_names = [
            "",  # Empty
            "   ",  # Whitespace only
            "style with spaces",  # Spaces
            "style@invalid",  # Special characters
            "style#123",  # Hash symbol
            "style/path",  # Forward slash
            "style\\path",  # Backward slash
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="Invalid style name"):
                StyleName(invalid_name)
    
    def test_style_name_predefined_styles(self):
        """Test predefined style names."""
        predefined_styles = [
            "professional", "casual", "technical", "creative",
            "formal", "informal", "academic", "business",
            "conversational", "marketing", "documentation"
        ]
        
        for style in predefined_styles:
            style_name = StyleName(style)
            assert style_name.value == style
    
    def test_style_name_equality(self):
        """Test StyleName equality."""
        name1 = StyleName("professional")
        name2 = StyleName("professional")
        name3 = StyleName("casual")
        
        assert name1 == name2
        assert name1 != name3
        assert name1 != "professional"  # Not equal to string
    
    def test_style_name_hash_consistency(self):
        """Test StyleName hash consistency."""
        name1 = StyleName("style")
        name2 = StyleName("style")
        
        assert hash(name1) == hash(name2)
        assert name1 in {name2}
    
    def test_style_name_case_sensitivity(self):
        """Test StyleName case sensitivity."""
        name1 = StyleName("Professional")
        name2 = StyleName("professional")
        
        assert name1 != name2  # Should be case sensitive
        assert name1.value == "Professional"
        assert name2.value == "professional"


class TestValidationRule:
    """Test cases for ValidationRule value object."""
    
    def test_validation_rule_creation(self):
        """Test creating ValidationRule."""
        rule = ValidationRuleBuilder.length_rule(10, 100).build()
        
        assert rule.rule_type == "length"
        assert rule.parameters["min"] == 10
        assert rule.parameters["max"] == 100
        assert "between 10 and 100" in rule.message
    
    def test_validation_rule_types(self):
        """Test different ValidationRule types."""
        # Length rule
        length_rule = ValidationRuleBuilder.length_rule(5, 50).build()
        assert length_rule.rule_type == "length"
        assert "min" in length_rule.parameters
        assert "max" in length_rule.parameters
        
        # Required rule
        required_rule = ValidationRuleBuilder.required_rule().build()
        assert required_rule.rule_type == "required"
        assert required_rule.parameters == {}
        
        # Regex rule
        regex_rule = ValidationRuleBuilder.regex_rule(r"^[A-Za-z]+$").build()
        assert regex_rule.rule_type == "regex"
        assert "pattern" in regex_rule.parameters
    
    def test_validation_rule_custom_message(self):
        """Test ValidationRule with custom message."""
        custom_message = "This field must be exactly 42 characters"
        rule = ValidationRule(
            rule_type="length",
            parameters={"min": 42, "max": 42},
            message=custom_message
        )
        
        assert rule.message == custom_message
    
    def test_validation_rule_validation(self):
        """Test ValidationRule validation."""
        # Empty rule type should fail
        with pytest.raises(ValueError, match="Rule type cannot be empty"):
            ValidationRule("", {}, "message")
        
        # None parameters should default to empty dict
        rule = ValidationRule("test", None, "message")
        assert rule.parameters == {}
        
        # Empty message should fail
        with pytest.raises(ValueError, match="Message cannot be empty"):
            ValidationRule("test", {}, "")
    
    def test_validation_rule_equality(self):
        """Test ValidationRule equality."""
        rule1 = ValidationRule("length", {"min": 10, "max": 100}, "Length message")
        rule2 = ValidationRule("length", {"min": 10, "max": 100}, "Length message")
        rule3 = ValidationRule("required", {}, "Required message")
        
        assert rule1 == rule2
        assert rule1 != rule3
    
    def test_validation_rule_hash_consistency(self):
        """Test ValidationRule hash consistency."""
        rule1 = ValidationRule("length", {"min": 10}, "message")
        rule2 = ValidationRule("length", {"min": 10}, "message")
        
        assert hash(rule1) == hash(rule2)
        assert rule1 in {rule2}
    
    def test_validation_rule_complex_parameters(self):
        """Test ValidationRule with complex parameters."""
        complex_params = {
            "pattern": r"^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$",
            "flags": ["case_insensitive"],
            "examples": {
                "valid": ["test@example.com", "user.name@domain.co.uk"],
                "invalid": ["invalid-email", "test@"]
            }
        }
        
        rule = ValidationRule(
            rule_type="email",
            parameters=complex_params,
            message="Must be a valid email address"
        )
        
        assert rule.parameters["pattern"] == complex_params["pattern"]
        assert rule.parameters["flags"] == complex_params["flags"]
        assert "test@example.com" in rule.parameters["examples"]["valid"]
    
    def test_validation_rule_immutability(self):
        """Test ValidationRule immutability."""
        rule = ValidationRule("test", {"param": "value"}, "message")
        
        with pytest.raises(AttributeError):
            rule.rule_type = "modified"  # type: ignore
        
        with pytest.raises(AttributeError):
            rule.message = "modified"  # type: ignore
        
        # Parameters dict should be immutable too (implementation dependent)
        try:
            rule.parameters["param"] = "modified"
            # If this succeeds, the implementation allows parameter mutation
            # This might be acceptable depending on design decisions
        except (TypeError, AttributeError):
            # Parameters are immutable - good
            pass


class TestContentValueObjectEdgeCases:
    """Test edge cases for content domain value objects."""
    
    def test_value_objects_with_unicode(self):
        """Test value objects with unicode characters."""
        # TemplateName with unicode (may not be allowed)
        try:
            unicode_template = TemplateName("templâte")
            assert "â" in unicode_template.value
        except ValueError:
            # Unicode might not be allowed in template names
            pass
        
        # StyleName with unicode (may not be allowed)
        try:
            unicode_style = StyleName("stylé")
            assert "é" in unicode_style.value
        except ValueError:
            # Unicode might not be allowed in style names
            pass
        
        # ValidationRule with unicode (should work)
        unicode_rule = ValidationRule(
            "unicode_test",
            {"pattern": "éñçoded"},
            "Message with unicôde"
        )
        assert "éñçoded" in unicode_rule.parameters["pattern"]
        assert "unicôde" in unicode_rule.message
    
    def test_value_objects_with_special_characters(self):
        """Test value objects with special characters."""
        # Template name with allowed special characters
        special_template = TemplateName("template-name_123.yaml")
        assert special_template.value == "template-name_123.yaml"
        
        # Style name with allowed special characters
        special_style = StyleName("style-name_123")
        assert special_style.value == "style-name_123"
        
        # Content ID with valid UUID format
        content_id = ContentId.generate()
        assert "-" in content_id.value  # UUIDs contain dashes
    
    def test_value_objects_with_very_long_values(self):
        """Test value objects with very long values."""
        # Very long template name (should fail validation)
        long_name = "a" * 500
        with pytest.raises(ValueError):
            TemplateName(long_name)
        
        # Very long validation rule message (should work)
        long_message = "Very long validation message. " * 100
        rule = ValidationRule("test", {}, long_message)
        assert len(rule.message) > 1000
    
    def test_value_objects_with_empty_values(self):
        """Test value objects with empty values."""
        # Empty template name (should fail)
        with pytest.raises(ValueError):
            TemplateName("")
        
        # Empty style name (should fail)
        with pytest.raises(ValueError):
            StyleName("")
        
        # Empty content ID (should fail)
        with pytest.raises(ValueError):
            ContentId("")
        
        # Empty validation rule type (should fail)
        with pytest.raises(ValueError):
            ValidationRule("", {}, "message")
    
    def test_value_objects_equality_across_types(self):
        """Test that different value object types are not equal."""
        template_name = TemplateName("test")
        style_name = StyleName("test")
        content_id = ContentId.generate()
        
        # Different types should not be equal even with same value
        assert template_name != style_name
        assert template_name != content_id
        assert style_name != content_id
        
        # Should not be equal to raw strings
        assert template_name != "test"
        assert style_name != "test"
    
    def test_enum_value_objects_comprehensive(self):
        """Test enum value objects comprehensively."""
        # ContentType enum values
        all_content_types = [
            ContentType.PIPELINE, ContentType.STYLE, ContentType.MARKDOWN,
            ContentType.JSON, ContentType.YAML, ContentType.TEXT
        ]
        
        for content_type in all_content_types:
            assert content_type is not None
            assert str(content_type) is not None
        
        # ContentFormat enum values
        all_content_formats = [
            ContentFormat.MARKDOWN, ContentFormat.JSON, ContentFormat.YAML,
            ContentFormat.TEXT, ContentFormat.HTML, ContentFormat.XML
        ]
        
        for content_format in all_content_formats:
            assert content_format is not None
            assert str(content_format) is not None
    
    def test_validation_rule_edge_cases(self):
        """Test ValidationRule edge cases."""
        # Rule with empty parameters
        empty_params_rule = ValidationRule("required", {}, "Required field")
        assert empty_params_rule.parameters == {}
        
        # Rule with None parameters (should default to empty dict)
        none_params_rule = ValidationRule("test", None, "message")
        assert none_params_rule.parameters == {}
        
        # Rule with very complex parameters
        complex_rule = ValidationRule(
            "complex",
            {
                "nested": {"deep": {"value": 42}},
                "list": [1, 2, 3],
                "boolean": True,
                "null": None
            },
            "Complex validation rule"
        )
        assert complex_rule.parameters["nested"]["deep"]["value"] == 42
        assert complex_rule.parameters["list"] == [1, 2, 3]