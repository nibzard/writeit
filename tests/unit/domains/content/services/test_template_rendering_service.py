"""Unit tests for TemplateRenderingService.

Tests the template rendering domain service for variable substitution,
validation, and context-aware template processing.
"""

import pytest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock

from writeit.domains.content.entities.template import Template
from writeit.domains.content.services.template_rendering_service import (
    TemplateRenderingService,
    RenderingMode,
    VariableType,
    VariableDefinition,
    RenderingContext,
    RenderingResult,
    TemplateRenderingError,
    VariableValidationError,
    MissingVariableError,
    TemplateCompilationError,
)
from writeit.domains.content.value_objects.content_id import ContentId
from writeit.domains.content.value_objects.template_name import TemplateName
from writeit.domains.content.value_objects.content_type import ContentType


@pytest.fixture
def rendering_service():
    """Create template rendering service."""
    return TemplateRenderingService()


@pytest.fixture
def simple_template():
    """Create simple test template."""
    yaml_content = """
metadata:
  name: "Simple Article"
  description: "Basic article template"

inputs:
  topic:
    type: text
    label: "Article Topic"
    required: true
  
  style:
    type: choice
    label: "Writing Style"
    options:
      - formal
      - casual
    default: formal

steps:
  outline:
    name: "Create Outline"
    prompt_template: |
      Create an outline for an article about {{ topic }} 
      in {{ style }} style.
    
  content:
    name: "Write Article"
    prompt_template: |
      Based on the outline: {{ steps.outline }}
      
      Write a comprehensive article about {{ topic }} 
      in {{ style }} style for {{ inputs.audience }}.
"""
    
    return Template(
        id=ContentId.generate(),
        name=TemplateName.from_user_input("simple-article"),
        content_type=ContentType.from_string("article"),
        yaml_content=yaml_content,
        version="1.0.0",
        author="test@example.com"
    )


@pytest.fixture
def complex_template():
    """Create complex test template with nested variables."""
    yaml_content = """
metadata:
  name: "Complex Report"

variables:
  - title: string
  - author: string
  - sections: list
  - config: dict

inputs:
  report_type:
    type: choice
    options: ["technical", "business", "academic"]
    required: true
  
  audience:
    type: text
    default: "general"

steps:
  introduction:
    prompt_template: |
      Title: {{ title }}
      Author: {{ author }}
      Type: {{ inputs.report_type }}
      
      Create introduction for {{ inputs.audience }} audience.
      
  sections:
    prompt_template: |
      Generate sections: {{ sections }}
      Configuration: {{ config.format }}
"""
    
    return Template(
        id=ContentId.generate(),
        name=TemplateName.from_user_input("complex-report"),
        content_type=ContentType.from_string("report"),
        yaml_content=yaml_content,
        version="1.0.0"
    )


@pytest.fixture
def basic_context():
    """Create basic rendering context."""
    return RenderingContext(
        variables={
            "topic": "Machine Learning",
            "style": "formal",
            "inputs": {
                "audience": "developers"
            },
            "steps": {
                "outline": "1. Introduction\n2. Core Concepts\n3. Applications"
            }
        },
        mode=RenderingMode.STRICT
    )


@pytest.fixture
def complex_context():
    """Create complex rendering context."""
    return RenderingContext(
        variables={
            "title": "AI Research Report",
            "author": "Dr. Smith",
            "sections": ["introduction", "methodology", "results"],
            "config": {
                "format": "markdown",
                "style": "academic"
            },
            "inputs": {
                "report_type": "technical",
                "audience": "researchers"
            },
            # Also provide input variables at top level for validation
            "report_type": "technical",
            "audience": "researchers"
        },
        mode=RenderingMode.STRICT
    )


class TestTemplateRenderingService:
    """Test suite for TemplateRenderingService."""
    
    @pytest.mark.asyncio
    async def test_init(self, rendering_service):
        """Test service initialization."""
        assert rendering_service._variable_cache == {}
        assert rendering_service._compiled_templates == {}
    
    @pytest.mark.asyncio
    async def test_render_template_success(
        self, 
        rendering_service, 
        simple_template, 
        basic_context
    ):
        """Test successful template rendering."""
        result = await rendering_service.render_template(simple_template, basic_context)
        
        assert result.success is True
        assert result.validation_errors == []
        assert len(result.missing_variables) == 0
        
        # Check that variables were substituted
        assert "Machine Learning" in result.rendered_content
        assert "formal" in result.rendered_content
        assert "developers" in result.rendered_content
        
        # Check used variables tracking
        assert "topic" in result.used_variables
        assert "style" in result.used_variables
    
    @pytest.mark.asyncio
    async def test_render_template_missing_variables_strict_mode(
        self, 
        rendering_service, 
        simple_template
    ):
        """Test rendering with missing variables in strict mode."""
        incomplete_context = RenderingContext(
            variables={"topic": "AI"},  # Missing style
            mode=RenderingMode.STRICT
        )
        
        with pytest.raises(MissingVariableError) as exc_info:
            await rendering_service.render_template(simple_template, incomplete_context)
        
        assert "style" in exc_info.value.missing_variables
    
    @pytest.mark.asyncio
    async def test_render_template_missing_variables_permissive_mode(
        self, 
        rendering_service, 
        simple_template
    ):
        """Test rendering with missing variables in permissive mode."""
        incomplete_context = RenderingContext(
            variables={"topic": "AI"},  # Missing style
            mode=RenderingMode.PERMISSIVE
        )
        
        result = await rendering_service.render_template(simple_template, incomplete_context)
        
        assert result.success is True
        assert "style" in result.missing_variables
        assert "AI" in result.rendered_content
    
    @pytest.mark.asyncio
    async def test_render_template_preview_mode(
        self, 
        rendering_service, 
        simple_template
    ):
        """Test rendering in preview mode."""
        incomplete_context = RenderingContext(
            variables={"topic": "AI"},  # Missing style
            mode=RenderingMode.PREVIEW
        )
        
        result = await rendering_service.render_template(simple_template, incomplete_context)
        
        assert result.success is True
        assert "AI" in result.rendered_content
        # Missing variables should remain as placeholders
        assert "{{ style }}" in result.rendered_content
    
    @pytest.mark.asyncio
    async def test_render_complex_template(
        self, 
        rendering_service, 
        complex_template, 
        complex_context
    ):
        """Test rendering complex template with nested variables."""
        result = await rendering_service.render_template(complex_template, complex_context)
        
        assert result.success is True
        
        # Check nested variable access
        assert "AI Research Report" in result.rendered_content
        assert "Dr. Smith" in result.rendered_content
        assert "technical" in result.rendered_content
        assert "markdown" in result.rendered_content
        
        # Check list variable
        assert "introduction" in result.rendered_content or str(["introduction", "methodology", "results"]) in result.rendered_content
    
    @pytest.mark.asyncio
    async def test_extract_variable_definitions(
        self, 
        rendering_service, 
        simple_template
    ):
        """Test variable definition extraction."""
        definitions = await rendering_service.extract_variable_definitions(simple_template)
        
        # Should find variables from inputs section
        assert "topic" in definitions
        assert "style" in definitions
        
        assert definitions["topic"].name == "topic"
        assert definitions["topic"].required is True
    
    @pytest.mark.asyncio
    async def test_extract_template_variables(
        self, 
        rendering_service, 
        simple_template
    ):
        """Test template variable extraction."""
        variables = await rendering_service.extract_template_variables(simple_template)
        
        # Should find all {{ variable }} patterns
        assert "topic" in variables
        assert "style" in variables
        assert "inputs" in variables  # From {{ inputs.audience }}
        assert "steps" in variables   # From {{ steps.outline }}
    
    @pytest.mark.asyncio
    async def test_validate_rendering_context(
        self, 
        rendering_service, 
        simple_template, 
        basic_context
    ):
        """Test rendering context validation."""
        errors = await rendering_service.validate_rendering_context(
            simple_template, 
            basic_context
        )
        
        assert errors == []  # No validation errors
    
    @pytest.mark.asyncio
    async def test_validate_rendering_context_with_errors(
        self, 
        rendering_service, 
        simple_template
    ):
        """Test rendering context validation with errors."""
        invalid_context = RenderingContext(
            variables={},  # Missing required variables
            mode=RenderingMode.STRICT
        )
        
        errors = await rendering_service.validate_rendering_context(
            simple_template, 
            invalid_context
        )
        
        assert len(errors) > 0
        assert any("topic" in error for error in errors)
    
    @pytest.mark.asyncio
    async def test_create_rendering_context(
        self, 
        rendering_service, 
        simple_template
    ):
        """Test rendering context creation."""
        variables = {"topic": "AI", "style": "casual"}
        
        context = await rendering_service.create_rendering_context(
            variables=variables,
            mode=RenderingMode.PERMISSIVE,
            template=simple_template
        )
        
        assert context.variables == variables
        assert context.mode == RenderingMode.PERMISSIVE
        assert context.template_name == simple_template.name
        assert context.content_type == simple_template.content_type
        assert context.metadata["template_version"] == simple_template.version
    
    @pytest.mark.asyncio
    async def test_create_rendering_context_without_template(
        self, 
        rendering_service
    ):
        """Test rendering context creation without template."""
        variables = {"topic": "AI"}
        
        context = await rendering_service.create_rendering_context(
            variables=variables,
            mode=RenderingMode.STRICT
        )
        
        assert context.variables == variables
        assert context.mode == RenderingMode.STRICT
        assert context.template_name is None
        assert context.content_type is None
        assert context.metadata == {}
    
    def test_clear_cache(self, rendering_service):
        """Test cache clearing."""
        # Add some dummy cache data
        rendering_service._variable_cache["test"] = {"var1", "var2"}
        rendering_service._compiled_templates["test"] = Mock()
        
        rendering_service.clear_cache()
        
        assert rendering_service._variable_cache == {}
        assert rendering_service._compiled_templates == {}
    
    def test_get_cache_stats(self, rendering_service):
        """Test cache statistics."""
        # Add some dummy cache data
        rendering_service._variable_cache["test1"] = {"var1"}
        rendering_service._variable_cache["test2"] = {"var2"}
        rendering_service._compiled_templates["template1"] = Mock()
        
        stats = rendering_service.get_cache_stats()
        
        assert stats["variable_cache_size"] == 2
        assert stats["compiled_templates_size"] == 1


class TestVariableDefinition:
    """Test suite for VariableDefinition."""
    
    def test_variable_definition_creation(self):
        """Test variable definition creation."""
        var_def = VariableDefinition(
            name="topic",
            type=VariableType.STRING,
            required=True,
            description="Article topic"
        )
        
        assert var_def.name == "topic"
        assert var_def.type == VariableType.STRING
        assert var_def.required is True
        assert var_def.description == "Article topic"
    
    def test_validate_value_string_type(self):
        """Test string type validation."""
        var_def = VariableDefinition(name="test", type=VariableType.STRING)
        
        assert var_def.validate_value("hello") is True
        assert var_def.validate_value(123) is False
        assert var_def.validate_value(None) is False  # Required by default
    
    def test_validate_value_integer_type(self):
        """Test integer type validation."""
        var_def = VariableDefinition(name="test", type=VariableType.INTEGER)
        
        assert var_def.validate_value(123) is True
        assert var_def.validate_value(123.45) is False
        assert var_def.validate_value("123") is False
    
    def test_validate_value_float_type(self):
        """Test float type validation."""
        var_def = VariableDefinition(name="test", type=VariableType.FLOAT)
        
        assert var_def.validate_value(123.45) is True
        assert var_def.validate_value(123) is True  # Integers allowed
        assert var_def.validate_value("123.45") is False
    
    def test_validate_value_boolean_type(self):
        """Test boolean type validation."""
        var_def = VariableDefinition(name="test", type=VariableType.BOOLEAN)
        
        assert var_def.validate_value(True) is True
        assert var_def.validate_value(False) is True
        assert var_def.validate_value("true") is False
        assert var_def.validate_value(1) is False
    
    def test_validate_value_list_type(self):
        """Test list type validation."""
        var_def = VariableDefinition(name="test", type=VariableType.LIST)
        
        assert var_def.validate_value([1, 2, 3]) is True
        assert var_def.validate_value([]) is True
        assert var_def.validate_value("not a list") is False
    
    def test_validate_value_dict_type(self):
        """Test dict type validation."""
        var_def = VariableDefinition(name="test", type=VariableType.DICT)
        
        assert var_def.validate_value({"key": "value"}) is True
        assert var_def.validate_value({}) is True
        assert var_def.validate_value("not a dict") is False
    
    def test_validate_value_any_type(self):
        """Test any type validation."""
        var_def = VariableDefinition(name="test", type=VariableType.ANY)
        
        assert var_def.validate_value("string") is True
        assert var_def.validate_value(123) is True
        assert var_def.validate_value([1, 2, 3]) is True
        assert var_def.validate_value({"key": "value"}) is True
    
    def test_validate_value_optional(self):
        """Test optional variable validation."""
        var_def = VariableDefinition(
            name="test", 
            type=VariableType.STRING, 
            required=False
        )
        
        assert var_def.validate_value("hello") is True
        assert var_def.validate_value(None) is True  # None allowed for optional
    
    def test_validate_value_with_pattern(self):
        """Test validation with regex pattern."""
        var_def = VariableDefinition(
            name="email",
            type=VariableType.STRING,
            validation_pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        assert var_def.validate_value("test@example.com") is True
        assert var_def.validate_value("invalid-email") is False
        assert var_def.validate_value("user@domain") is False


class TestRenderingContext:
    """Test suite for RenderingContext."""
    
    def test_rendering_context_creation(self):
        """Test rendering context creation."""
        variables = {"topic": "AI", "style": "formal"}
        context = RenderingContext(
            variables=variables,
            mode=RenderingMode.PERMISSIVE
        )
        
        assert context.variables == variables
        assert context.mode == RenderingMode.PERMISSIVE
        assert context.template_name is None
        assert context.content_type is None
        assert context.metadata == {}
    
    def test_get_variable(self):
        """Test getting variable value."""
        context = RenderingContext(variables={"topic": "AI"})
        
        assert context.get_variable("topic") == "AI"
        assert context.get_variable("missing") is None
        assert context.get_variable("missing", "default") == "default"
    
    def test_has_variable(self):
        """Test checking variable existence."""
        context = RenderingContext(variables={"topic": "AI"})
        
        assert context.has_variable("topic") is True
        assert context.has_variable("missing") is False
    
    def test_set_variable(self):
        """Test setting variable value."""
        context = RenderingContext(variables={})
        
        context.set_variable("topic", "AI")
        assert context.variables["topic"] == "AI"
    
    def test_merge_variables(self):
        """Test merging additional variables."""
        context = RenderingContext(variables={"topic": "AI"})
        
        additional = {"style": "formal", "topic": "ML"}  # Override existing
        context.merge_variables(additional)
        
        assert context.variables["topic"] == "ML"  # Overridden
        assert context.variables["style"] == "formal"  # Added


class TestRenderingResult:
    """Test suite for RenderingResult."""
    
    def test_rendering_result_creation(self):
        """Test rendering result creation."""
        result = RenderingResult(
            rendered_content="Hello AI",
            used_variables={"topic"},
            missing_variables={"style"},
            validation_errors=["Error 1"],
            success=False
        )
        
        assert result.rendered_content == "Hello AI"
        assert result.used_variables == {"topic"}
        assert result.missing_variables == {"style"}
        assert result.validation_errors == ["Error 1"]
        assert result.success is False
    
    def test_has_errors_property(self):
        """Test has_errors property."""
        # With errors
        result_with_errors = RenderingResult(
            rendered_content="", 
            used_variables=set(), 
            missing_variables=set(),
            validation_errors=["Error 1"],
            success=False
        )
        assert result_with_errors.has_errors is True
        
        # Without errors
        result_without_errors = RenderingResult(
            rendered_content="",
            used_variables=set(),
            missing_variables=set(),
            validation_errors=[],
            success=True
        )
        assert result_without_errors.has_errors is False
    
    def test_has_missing_variables_property(self):
        """Test has_missing_variables property."""
        # With missing variables
        result_with_missing = RenderingResult(
            rendered_content="",
            used_variables=set(),
            missing_variables={"var1"},
            validation_errors=[],
            success=False
        )
        assert result_with_missing.has_missing_variables is True
        
        # Without missing variables
        result_without_missing = RenderingResult(
            rendered_content="",
            used_variables=set(),
            missing_variables=set(),
            validation_errors=[],
            success=True
        )
        assert result_without_missing.has_missing_variables is False


class TestTemplateRenderingError:
    """Test suite for TemplateRenderingError."""
    
    def test_template_rendering_error_creation(self):
        """Test TemplateRenderingError creation."""
        template_name = TemplateName.from_user_input("test-template")
        context_info = {"key": "value"}
        
        error = TemplateRenderingError(
            "Rendering failed",
            template_name,
            context_info
        )
        
        assert str(error) == "Rendering failed"
        assert error.template_name == template_name
        assert error.context_info == context_info
    
    def test_template_rendering_error_minimal(self):
        """Test TemplateRenderingError creation with minimal arguments."""
        error = TemplateRenderingError("Rendering failed")
        
        assert str(error) == "Rendering failed"
        assert error.template_name is None
        assert error.context_info == {}


class TestVariableValidationError:
    """Test suite for VariableValidationError."""
    
    def test_variable_validation_error_creation(self):
        """Test VariableValidationError creation."""
        template_name = TemplateName.from_user_input("test-template")
        
        error = VariableValidationError(
            "Invalid variable",
            "topic",
            VariableType.STRING,
            123,
            template_name
        )
        
        assert str(error) == "Invalid variable"
        assert error.variable_name == "topic"
        assert error.expected_type == VariableType.STRING
        assert error.actual_value == 123
        assert error.template_name == template_name
        assert error.context_info["actual_type"] == "int"


class TestMissingVariableError:
    """Test suite for MissingVariableError."""
    
    def test_missing_variable_error_creation(self):
        """Test MissingVariableError creation."""
        missing_vars = {"topic", "style"}
        template_name = TemplateName.from_user_input("test-template")
        
        error = MissingVariableError(missing_vars, template_name)
        
        assert "Missing required variables:" in str(error)
        assert "style" in str(error)
        assert "topic" in str(error)
        assert error.missing_variables == missing_vars
        assert error.template_name == template_name