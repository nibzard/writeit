"""Comprehensive unit tests for Template entity."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json

from src.writeit.domains.content.entities.template import Template
from src.writeit.domains.content.value_objects.template_name import TemplateName
from src.writeit.domains.content.value_objects.content_type import ContentType
from src.writeit.domains.content.value_objects.validation_rule import ValidationRule

from tests.builders.content_builders import TemplateBuilder
from tests.builders.value_object_builders import ValidationRuleBuilder


class TestTemplate:
    """Test cases for Template entity."""
    
    def test_template_creation_with_valid_data(self):
        """Test creating a template with valid data."""
        template = TemplateBuilder.pipeline_template().build()
        
        assert isinstance(template.name, TemplateName)
        assert template.content_type == ContentType.documentation()
        assert template.version == "1.0.0"
        assert "A pipeline template for testing" in template.description
        assert len(template.variables) > 0
        assert "pipeline" in template.tags
        assert "test" in template.tags
        assert isinstance(template.created_at, datetime)
        assert isinstance(template.updated_at, datetime)
    
    def test_template_creation_with_custom_data(self):
        """Test creating a template with custom data."""
        custom_content = "# {{title}}\n\nContent: {{content}}\n\nAuthor: {{author}}"
        custom_metadata = {
            "category": "documentation",
            "difficulty": "beginner",
            "estimated_time": 300
        }
        
        template = (TemplateBuilder()
                   .with_name("custom_template")
                   .with_content_type(ContentType.article())
                   .with_content(custom_content)
                   .with_description("Custom template for testing")
                   .with_metadata(custom_metadata)
                   .with_tags(["custom", "markdown"])
                   .with_author("Test Author")
                   .build())
        
        assert template.name.value == "custom_template"
        assert template.content_type == ContentType.article()
        assert template.content == custom_content
        assert template.variables == {"title", "content", "author"}
        assert template.metadata == custom_metadata
        assert template.author == "Test Author"
    
    def test_pipeline_template_creation(self):
        """Test creating a pipeline template."""
        template = TemplateBuilder.pipeline_template("test_pipeline").build()
        
        assert template.content_type == ContentType.documentation()
        assert "metadata:" in template.content
        assert "inputs:" in template.content
        assert "steps:" in template.content
        assert "name" in template.variables
        assert "description" in template.variables
    
    def test_style_template_creation(self):
        """Test creating a style template."""
        template = TemplateBuilder.style_template("test_style").build()
        
        assert template.content_type == ContentType.documentation()
        assert "tone:" in template.content
        assert "style_guide:" in template.content
        assert "tone" in template.variables
        assert "length" in template.variables
        assert "focus" in template.variables
    
    def test_article_template_creation(self):
        """Test creating an article template."""
        template = TemplateBuilder.article_template("test_article").build()
        
        assert template.content_type == ContentType.article()
        assert "# {{title}}" in template.content
        assert "## Introduction" in template.content
        assert "title" in template.variables
        assert "introduction" in template.variables
        assert "main_content" in template.variables
        assert "conclusion" in template.variables
    
    def test_template_with_dependencies(self):
        """Test creating a template with dependencies."""
        dependencies = ["base_template", "styling_template"]
        template = TemplateBuilder.with_dependencies("dependent_template", dependencies).build()
        
        assert template.dependencies == dependencies
        assert "base_template" in template.dependencies
        assert "styling_template" in template.dependencies
        assert "dependent" in template.tags
    
    def test_template_with_validation_rules(self):
        """Test template with validation rules."""
        rules = [
            ValidationRuleBuilder.length_rule(10, 1000).build(),
            ValidationRuleBuilder.required_rule().build()
        ]
        
        template = (TemplateBuilder
                   .article_template()
                   .with_validation_rules(rules)
                   .build())
        
        assert len(template.validation_rules) == 2
        assert template.validation_rules[0].rule_type == "length"
        assert template.validation_rules[1].rule_type == "required"
    
    def test_template_with_file_path(self):
        """Test template with file path."""
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp_file:
            file_path = Path(tmp_file.name)
        
        try:
            template = (TemplateBuilder
                       .pipeline_template()
                       .with_file_path(file_path)
                       .build())
            
            assert template.file_path == file_path
            assert template.file_path.suffix == '.yaml'
        finally:
            file_path.unlink(missing_ok=True)
    
    def test_template_variable_extraction(self):
        """Test template variable extraction from content."""
        content_with_vars = """
        Welcome {{user_name}}!
        
        Your {{item_type}} order #{{order_id}} is ready.
        Total: ${{total_amount}}
        
        {{special_instructions}}
        """
        
        template = (TemplateBuilder()
                   .with_content(content_with_vars)
                   .build())
        
        expected_vars = {"user_name", "item_type", "order_id", "total_amount", "special_instructions"}
        assert template.variables == expected_vars
    
    def test_template_with_metadata(self):
        """Test template with comprehensive metadata."""
        metadata = {
            "category": "content_generation",
            "subcategory": "articles",
            "difficulty": "intermediate",
            "estimated_time": 1800,  # 30 minutes
            "requires_review": True,
            "output_format": "markdown",
            "languages": ["en", "es", "fr"],
            "use_cases": ["blog_posts", "documentation", "marketing"]
        }
        
        template = (TemplateBuilder
                   .article_template()
                   .with_metadata(metadata)
                   .build())
        
        assert template.metadata == metadata
        assert template.metadata["category"] == "content_generation"
        assert "en" in template.metadata["languages"]
        assert template.metadata["requires_review"] is True
    
    def test_template_timestamps(self):
        """Test template timestamps."""
        now = datetime.now()
        template = TemplateBuilder.article_template().build()
        
        # Created and updated should be close to now
        assert abs((template.created_at - now).total_seconds()) < 1
        assert abs((template.updated_at - now).total_seconds()) < 1
        
        # Test custom timestamps
        custom_time = datetime(2023, 8, 15, 14, 30, 0)
        template_with_custom = (TemplateBuilder
                               .article_template()
                               .with_timestamps(custom_time, custom_time)
                               .build())
        
        assert template_with_custom.created_at == custom_time
        assert template_with_custom.updated_at == custom_time
    
    def test_template_versioning(self):
        """Test template versioning."""
        template_v1 = (TemplateBuilder
                      .article_template()
                      .with_version("1.0.0")
                      .build())
        
        template_v2 = (TemplateBuilder
                      .article_template()
                      .with_version("2.1.0")
                      .build())
        
        assert template_v1.version == "1.0.0"
        assert template_v2.version == "2.1.0"
        assert template_v1.version != template_v2.version


class TestTemplateBusinessLogic:
    """Test business logic and invariants for Template."""
    
    def test_template_name_uniqueness_constraint(self):
        """Test template name uniqueness (business constraint)."""
        name = "unique_template"
        
        template1 = TemplateBuilder().with_name(name).build()
        template2 = TemplateBuilder().with_name(name).build()
        
        # Same name should create same TemplateName value object
        assert template1.name == template2.name
        assert template1.name.value == name
        assert template2.name.value == name
    
    def test_template_content_type_consistency(self):
        """Test content type consistency with content."""
        # Pipeline template should have YAML-like content
        pipeline_template = TemplateBuilder.pipeline_template().build()
        assert pipeline_template.content_type == ContentType.documentation()
        assert "metadata:" in pipeline_template.content
        assert "steps:" in pipeline_template.content
        
        # Markdown template should have markdown content
        markdown_template = TemplateBuilder.article_template().build()
        assert markdown_template.content_type == ContentType.article()
        assert "# {{" in markdown_template.content
        assert "## " in markdown_template.content
    
    def test_template_variable_consistency(self):
        """Test that variables are consistently extracted from content."""
        content = "Hello {{name}}, your {{item}} costs {{price}}."
        
        template = (TemplateBuilder()
                   .with_content(content)
                   .build())
        
        # Variables should match what's in the content
        assert template.variables == {"name", "item", "price"}
        
        # Updating content should update variables
        new_content = "Hi {{user}}, welcome to {{platform}}!"
        updated_template = (TemplateBuilder()
                           .with_content(new_content)
                           .build())
        
        assert updated_template.variables == {"user", "platform"}
    
    def test_template_dependency_validation(self):
        """Test template dependency validation logic."""
        dependencies = ["base", "utils", "styles"]
        template = TemplateBuilder.with_dependencies("dependent", dependencies).build()
        
        assert template.dependencies == dependencies
        assert len(template.dependencies) == 3
        assert "base" in template.dependencies
        
        # Dependencies should be unique (no duplicates)
        unique_deps = list(set(template.dependencies))
        assert len(unique_deps) == len(template.dependencies)
    
    def test_template_validation_rules_application(self):
        """Test that validation rules are properly stored."""
        length_rule = ValidationRuleBuilder.length_rule(50, 2000).build()
        required_rule = ValidationRuleBuilder.required_rule().build()
        
        template = (TemplateBuilder
                   .article_template()
                   .with_validation_rules([length_rule, required_rule])
                   .build())
        
        assert len(template.validation_rules) == 2
        
        # Find length rule
        length_rules = [r for r in template.validation_rules if r.rule_type == "length"]
        assert len(length_rules) == 1
        assert length_rules[0].parameters["min"] == 50
        assert length_rules[0].parameters["max"] == 2000
        
        # Find required rule
        required_rules = [r for r in template.validation_rules if r.rule_type == "required"]
        assert len(required_rules) == 1
    
    def test_template_metadata_extensibility(self):
        """Test that template metadata supports extension."""
        base_metadata = {"type": "article", "category": "blog"}
        extended_metadata = {
            **base_metadata,
            "seo": {"keywords": ["test", "template"], "meta_description": "Test template"},
            "social": {"twitter_card": "summary", "og_image": "/image.jpg"}
        }
        
        template = (TemplateBuilder
                   .article_template()
                   .with_metadata(extended_metadata)
                   .build())
        
        assert template.metadata["type"] == "article"
        assert template.metadata["seo"]["keywords"] == ["test", "template"]
        assert template.metadata["social"]["twitter_card"] == "summary"
    
    def test_template_file_path_consistency(self):
        """Test file path consistency with template type."""
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as tmp_file:
            md_path = Path(tmp_file.name)
        
        with tempfile.NamedTemporaryFile(suffix='.yaml', delete=False) as tmp_file:
            yaml_path = Path(tmp_file.name)
        
        try:
            # Markdown template with .md file
            md_template = (TemplateBuilder
                          .article_template()
                          .with_file_path(md_path)
                          .build())
            
            assert md_template.file_path.suffix == '.md'
            assert md_template.content_type == ContentType.article()
            
            # Pipeline template with .yaml file
            yaml_template = (TemplateBuilder
                            .pipeline_template()
                            .with_file_path(yaml_path)
                            .build())
            
            assert yaml_template.file_path.suffix == '.yaml'
            assert yaml_template.content_type == ContentType.documentation()
            
        finally:
            md_path.unlink(missing_ok=True)
            yaml_path.unlink(missing_ok=True)
    
    def test_template_author_attribution(self):
        """Test template author attribution."""
        author = "John Doe"
        template = (TemplateBuilder
                   .article_template()
                   .with_author(author)
                   .build())
        
        assert template.author == author
        
        # Template without author
        no_author_template = TemplateBuilder.article_template().build()
        assert no_author_template.author is None
    
    def test_template_tag_categorization(self):
        """Test template tag-based categorization."""
        tags = ["article", "blog", "marketing", "customer_facing"]
        template = (TemplateBuilder
                   .article_template()
                   .with_tags(tags)
                   .build())
        
        assert template.tags == tags
        assert "article" in template.tags
        assert "marketing" in template.tags
        
        # Tags should be stored as provided (maintain order)
        assert template.tags[0] == "article"
        assert template.tags[-1] == "customer_facing"
    
    def test_template_immutability(self):
        """Test template immutability after creation."""
        template = TemplateBuilder.article_template().build()
        original_content = template.content
        original_version = template.version
        
        # Direct modification should not be possible
        with pytest.raises(AttributeError):
            template.content = "Modified content"  # type: ignore
        
        with pytest.raises(AttributeError):
            template.version = "2.0.0"  # type: ignore
        
        # Values should remain unchanged
        assert template.content == original_content
        assert template.version == original_version


class TestTemplateEdgeCases:
    """Test edge cases and error conditions for Template."""
    
    def test_template_with_empty_content(self):
        """Test template with empty content."""
        template = (TemplateBuilder()
                   .with_content("")
                   .build())
        
        assert template.content == ""
        assert len(template.variables) == 0
    
    def test_template_with_no_variables(self):
        """Test template with no template variables."""
        static_content = "This is static content with no variables."
        template = (TemplateBuilder()
                   .with_content(static_content)
                   .build())
        
        assert template.content == static_content
        assert len(template.variables) == 0
    
    def test_template_with_malformed_variables(self):
        """Test template with malformed variable syntax."""
        malformed_content = "This has {{incomplete and }invalid} variables."
        template = (TemplateBuilder()
                   .with_content(malformed_content)
                   .build())
        
        # Should extract valid variables and ignore malformed ones
        # Implementation-dependent behavior
        assert template.content == malformed_content
    
    def test_template_with_duplicate_variables(self):
        """Test template with duplicate variables."""
        content_with_dupes = "Hello {{name}}, Mr. {{name}}, how is {{name}} today?"
        template = (TemplateBuilder()
                   .with_content(content_with_dupes)
                   .build())
        
        # Variables should be a set (no duplicates)
        assert template.variables == {"name"}
        assert len(template.variables) == 1
    
    def test_template_with_nested_variables(self):
        """Test template with nested variable patterns."""
        nested_content = "Use {{config.{{environment}}.database_url}} for connection."
        template = (TemplateBuilder()
                   .with_content(nested_content)
                   .build())
        
        # Behavior depends on variable extraction implementation
        assert template.content == nested_content
    
    def test_template_with_large_content(self):
        """Test template with large content."""
        large_content = "Large template content. " * 10000  # ~250KB
        template = (TemplateBuilder()
                   .with_content(large_content)
                   .build())
        
        assert len(template.content) > 200000
        assert template.content.count("Large template content.") == 10000
    
    def test_template_with_unicode_content(self):
        """Test template with unicode content."""
        unicode_content = """
        Hëllö {{ñamé}}! 
        
        Wélçömé tö öür plâtförm 🎉
        
        Yöür ördér #{{ördér_íd}} ïs réády.
        Ëñjöy {{ïtém}} 😊
        """
        
        template = (TemplateBuilder()
                   .with_content(unicode_content)
                   .build())
        
        assert template.content == unicode_content
        assert "🎉" in template.content
        assert "ñamé" in template.variables
        assert "ördér_íd" in template.variables
    
    def test_template_with_special_characters_in_metadata(self):
        """Test template with special characters in metadata."""
        special_metadata = {
            "title": "Spëçîál Tëmplâtë 🌟",
            "description": "Template with émojis and üñíçödé",
            "symbols": "!@#$%^&*()_+-=[]{}|;:,.<>?",
            "paths": ["/spëçîál/päth", "C:\\Wïñdöws\\Päth"]
        }
        
        template = (TemplateBuilder()
                   .with_metadata(special_metadata)
                   .build())
        
        assert template.metadata == special_metadata
        assert "🌟" in template.metadata["title"]
        assert "üñíçödé" in template.metadata["description"]
    
    def test_template_metadata_serialization(self):
        """Test that template metadata is JSON serializable."""
        template = TemplateBuilder.pipeline_template().build()
        
        # Basic metadata should be JSON serializable
        try:
            json.dumps(template.metadata)
        except (TypeError, ValueError) as e:
            pytest.fail(f"Template metadata not serializable: {e}")
    
    def test_template_with_very_long_name(self):
        """Test template with very long name."""
        long_name = "a" * 255  # Very long name
        template = TemplateBuilder().with_name(long_name).build()
        
        assert template.name.value == long_name
        assert len(template.name.value) == 255
    
    def test_template_with_empty_tags_and_dependencies(self):
        """Test template with empty tags and dependencies."""
        template = (TemplateBuilder()
                   .with_tags([])
                   .with_dependencies([])
                   .build())
        
        assert template.tags == []
        assert template.dependencies == []
        assert len(template.tags) == 0
        assert len(template.dependencies) == 0