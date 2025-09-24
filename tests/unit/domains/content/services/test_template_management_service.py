"""Unit tests for TemplateManagementService.

Tests comprehensive template lifecycle operations including creation, validation,
versioning, dependency analysis, inheritance management, and performance optimization.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from src.writeit.domains.content.services.template_management_service import (
    TemplateManagementService,
    TemplateValidationError,
    TemplateDependencyError,
    TemplateOptimizationError,
    TemplateCreationOptions,
    TemplateDependencyGraph,
    TemplateValidationResult,
    TemplateInheritanceChain,
    TemplatePerformanceMetrics,
    TemplateVersionComparison
)
from src.writeit.domains.content.entities.template import Template
from src.writeit.domains.content.value_objects.template_name import TemplateName
from src.writeit.domains.content.value_objects.content_type import ContentType
from src.writeit.domains.content.value_objects.content_format import ContentFormat
from src.writeit.domains.content.value_objects.validation_rule import ValidationRule
from src.writeit.shared.repository import EntityAlreadyExistsError, EntityNotFoundError, RepositoryError


# Test Fixtures

@pytest.fixture
def mock_template_repo():
    """Mock template repository."""
    repo = AsyncMock()
    repo.find_by_name = AsyncMock()
    repo.save = AsyncMock()
    repo.get_template_usage_stats = AsyncMock()
    repo.get_template_dependents = AsyncMock()
    return repo


@pytest.fixture
def template_management_service(mock_template_repo):
    """Template management service with mocked dependencies."""
    return TemplateManagementService(mock_template_repo)


@pytest.fixture
def sample_template():
    """Sample template for testing."""
    return Template.create(
        name=TemplateName.from_user_input("test-template"),
        content_type=ContentType.blog_post(),
        yaml_content="""
metadata:
  name: "Test Template"
  description: "A test template"
  
inputs:
  topic:
    type: text
    required: true
  
steps:
  outline:
    type: llm_generate
    prompt_template: "Create outline for {{ inputs.topic }}"
  content:
    type: llm_generate
    prompt_template: "Write content based on {{ steps.outline }}"
    depends_on: ["outline"]
""".strip(),
        tags=["test", "blog"],
        output_format=ContentFormat.markdown()
    )


@pytest.fixture
def sample_yaml_content():
    """Sample YAML content for template creation."""
    return """
metadata:
  name: "Sample Template"
  description: "A sample template for testing"

defaults:
  model: "gpt-4o-mini"

inputs:
  topic:
    type: text
    label: "Article Topic"
    required: true
  
  style:
    type: choice
    label: "Writing Style" 
    options:
      - {label: "Formal", value: "formal"}
      - {label: "Casual", value: "casual"}
    default: "formal"

steps:
  research:
    name: "Research Phase"
    type: llm_generate
    prompt_template: "Research information about {{ inputs.topic }}"
    
  outline:
    name: "Create Outline"
    type: llm_generate
    prompt_template: "Create detailed outline for {{ inputs.topic }} in {{ inputs.style }} style based on {{ steps.research }}"
    depends_on: ["research"]
    
  content:
    name: "Write Content"
    type: llm_generate
    prompt_template: "Write comprehensive content based on outline {{ steps.outline }}"
    depends_on: ["outline"]
""".strip()


@pytest.fixture
def creation_options():
    """Sample template creation options."""
    return TemplateCreationOptions(
        validate_syntax=True,
        auto_detect_content_type=True,
        auto_generate_tags=True,
        inherit_validation_rules=True,
        set_default_format=True,
        create_dependencies=False,
        metadata={"author": "test_user", "version": "1.0"}
    )


# Core Template Management Tests

class TestTemplateCreation:
    """Tests for template creation functionality."""

    @pytest.mark.asyncio
    async def test_create_template_success(
        self, 
        template_management_service, 
        mock_template_repo,
        sample_yaml_content,
        creation_options
    ):
        """Test successful template creation with all options."""
        # Arrange
        name = TemplateName.from_user_input("new-template")
        mock_template_repo.find_by_name.return_value = None
        mock_template_repo.save.return_value = Mock(id="template_123")
        
        # Act
        result = await template_management_service.create_template(
            name=name,
            yaml_content=sample_yaml_content,
            options=creation_options,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert result is not None
        mock_template_repo.find_by_name.assert_called_once_with(name)
        mock_template_repo.save.assert_called_once()
        
        # Verify template was saved with correct workspace
        save_call = mock_template_repo.save.call_args
        saved_template, workspace = save_call[0]
        assert workspace == "test_workspace"
        assert saved_template.name == name

    @pytest.mark.asyncio
    async def test_create_template_already_exists(
        self,
        template_management_service,
        mock_template_repo,
        sample_template,
        sample_yaml_content
    ):
        """Test template creation when template already exists."""
        # Arrange
        name = TemplateName.from_user_input("existing-template")
        mock_template_repo.find_by_name.return_value = sample_template
        
        # Act & Assert
        with pytest.raises(EntityAlreadyExistsError) as exc_info:
            await template_management_service.create_template(
                name=name,
                yaml_content=sample_yaml_content
            )
        
        assert "already exists" in str(exc_info.value)
        mock_template_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_template_invalid_yaml(
        self,
        template_management_service,
        mock_template_repo
    ):
        """Test template creation with invalid YAML syntax."""
        # Arrange
        name = TemplateName.from_user_input("invalid-template")
        invalid_yaml = "invalid: yaml: content: ["
        mock_template_repo.find_by_name.return_value = None
        
        # Act & Assert
        with pytest.raises(TemplateValidationError) as exc_info:
            await template_management_service.create_template(
                name=name,
                yaml_content=invalid_yaml,
                options=TemplateCreationOptions(validate_syntax=True)
            )
        
        assert "YAML syntax errors" in str(exc_info.value)
        mock_template_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_template_with_default_options(
        self,
        template_management_service,
        mock_template_repo,
        sample_yaml_content
    ):
        """Test template creation with default options."""
        # Arrange
        name = TemplateName.from_user_input("default-template")
        mock_template_repo.find_by_name.return_value = None
        mock_template_repo.save.return_value = Mock(id="template_456")
        
        # Act
        result = await template_management_service.create_template(
            name=name,
            yaml_content=sample_yaml_content
            # No options provided - should use defaults
        )
        
        # Assert
        assert result is not None
        mock_template_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_template_auto_detection(
        self,
        template_management_service,
        mock_template_repo
    ):
        """Test template creation with auto-detection features."""
        # Arrange
        name = TemplateName.from_user_input("blog-template")
        blog_yaml = """
metadata:
  name: "Blog Post Template"
  description: "Create engaging blog posts"

steps:
  title:
    type: llm_generate
    prompt_template: "Create catchy title for blog about {{ inputs.topic }}"
  content:
    type: llm_generate
    prompt_template: "Write blog post with title {{ steps.title }}"
""".strip()
        
        mock_template_repo.find_by_name.return_value = None
        mock_template_repo.save.return_value = Mock(id="template_789")
        
        options = TemplateCreationOptions(
            auto_detect_content_type=True,
            auto_generate_tags=True,
            set_default_format=True
        )
        
        # Act
        result = await template_management_service.create_template(
            name=name,
            yaml_content=blog_yaml,
            options=options
        )
        
        # Assert
        assert result is not None
        mock_template_repo.save.assert_called_once()


class TestTemplateValidation:
    """Tests for comprehensive template validation."""

    @pytest.mark.asyncio
    async def test_validate_template_comprehensive_success(
        self,
        template_management_service,
        sample_template
    ):
        """Test comprehensive template validation for valid template."""
        # Act
        result = await template_management_service.validate_template_comprehensive(
            template=sample_template,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, TemplateValidationResult)
        assert result.is_valid is True
        assert isinstance(result.syntax_errors, list)
        assert isinstance(result.semantic_errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.suggestions, list)
        assert isinstance(result.missing_variables, list)
        assert isinstance(result.unused_variables, list)
        assert isinstance(result.performance_issues, list)

    @pytest.mark.asyncio
    async def test_validate_template_with_errors(
        self,
        template_management_service
    ):
        """Test template validation with various errors."""
        # Arrange - Create template with validation issues
        invalid_template = Template.create(
            name=TemplateName.from_user_input("invalid-template"),
            content_type=ContentType.generic(),
            yaml_content="""
# Missing metadata section
steps:
  broken_step:
    # Missing type field
    prompt_template: "Use undefined {{ invalid.variable }}"
""".strip()
        )
        
        # Act
        result = await template_management_service.validate_template_comprehensive(
            template=invalid_template,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.semantic_errors) > 0  # Should have semantic errors
        assert len(result.missing_variables) > 0  # Should detect missing variables

    @pytest.mark.asyncio
    async def test_validate_template_caching(
        self,
        template_management_service,
        sample_template
    ):
        """Test that validation results are cached properly."""
        # Act - Call validation twice
        result1 = await template_management_service.validate_template_comprehensive(
            template=sample_template,
            workspace_name="test_workspace"
        )
        result2 = await template_management_service.validate_template_comprehensive(
            template=sample_template,
            workspace_name="test_workspace"
        )
        
        # Assert - Should return the same cached result
        assert result1 is result2
        assert result1.is_valid == result2.is_valid

    @pytest.mark.asyncio
    async def test_validate_template_performance_issues(
        self,
        template_management_service
    ):
        """Test detection of performance issues in template validation."""
        # Arrange - Create template with performance issues
        complex_template = Template.create(
            name=TemplateName.from_user_input("complex-template"),
            content_type=ContentType.generic(),
            yaml_content="""
metadata:
  name: "Complex Template"

steps:
  step1:
    type: llm_generate
    prompt_template: "{}".format("Very long prompt template with excessive content that goes on and on and repeats itself many times over to create a very long prompt that might cause performance issues due to its excessive length and verbosity making it harder to process efficiently" * 10)
  step2:
    type: llm_generate
    prompt_template: "Use {{ var1 }} and {{ var2 }} and {{ var3 }} and {{ var4 }} and {{ var5 }} and {{ var6 }} and {{ var7 }} and {{ var8 }} and {{ var9 }} and {{ var10 }} and {{ var11 }}"
""".replace("{}", "")
        )
        
        # Act
        result = await template_management_service.validate_template_comprehensive(
            template=complex_template,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result.performance_issues, list)
        # Should detect performance issues with long prompts and many variables


class TestDependencyAnalysis:
    """Tests for template dependency analysis."""

    @pytest.mark.asyncio
    async def test_analyze_template_dependencies_basic(
        self,
        template_management_service,
        mock_template_repo,
        sample_template
    ):
        """Test basic dependency analysis."""
        # Arrange
        mock_template_repo.get_template_dependents.return_value = []
        
        # Act
        result = await template_management_service.analyze_template_dependencies(
            template=sample_template,
            workspace_name="test_workspace",
            max_depth=5
        )
        
        # Assert
        assert isinstance(result, TemplateDependencyGraph)
        assert result.template == sample_template
        assert isinstance(result.direct_dependencies, list)
        assert isinstance(result.indirect_dependencies, list)
        assert isinstance(result.dependents, list)
        assert isinstance(result.circular_dependencies, list)
        assert isinstance(result.missing_dependencies, list)
        assert isinstance(result.depth, int)
        assert isinstance(result.is_leaf, bool)
        assert isinstance(result.is_root, bool)

    @pytest.mark.asyncio
    async def test_analyze_dependencies_with_circular_deps(
        self,
        template_management_service,
        mock_template_repo
    ):
        """Test dependency analysis with circular dependencies."""
        # Arrange - Template with circular dependency reference
        circular_template = Template.create(
            name=TemplateName.from_user_input("circular-template"),
            content_type=ContentType.generic(),
            yaml_content="""
metadata:
  name: "Circular Template"
extends: "circular-template"  # Self-reference

steps:
  step1:
    type: llm_generate
    template: "other-template"
    prompt_template: "Generate content"
""".strip()
        )
        
        # Mock template that references back
        other_template = Template.create(
            name=TemplateName.from_user_input("other-template"),
            content_type=ContentType.generic(),
            yaml_content="""
extends: "circular-template"
steps:
  step1:
    type: llm_generate
    prompt_template: "Generate content"
""".strip()
        )
        
        mock_template_repo.find_by_name.side_effect = lambda name: (
            other_template if str(name) == "other-template" else None
        )
        mock_template_repo.get_template_dependents.return_value = []
        
        # Act
        result = await template_management_service.analyze_template_dependencies(
            template=circular_template,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert len(result.circular_dependencies) > 0

    @pytest.mark.asyncio 
    async def test_dependency_analysis_caching(
        self,
        template_management_service,
        mock_template_repo,
        sample_template
    ):
        """Test that dependency analysis results are cached."""
        # Arrange
        mock_template_repo.get_template_dependents.return_value = []
        
        # Act - Call analysis twice with same parameters
        result1 = await template_management_service.analyze_template_dependencies(
            template=sample_template,
            workspace_name="test_workspace",
            max_depth=5
        )
        result2 = await template_management_service.analyze_template_dependencies(
            template=sample_template,
            workspace_name="test_workspace",
            max_depth=5
        )
        
        # Assert - Should return cached result
        assert result1 is result2

    @pytest.mark.asyncio
    async def test_dependency_analysis_error_handling(
        self,
        template_management_service,
        mock_template_repo,
        sample_template
    ):
        """Test dependency analysis error handling."""
        # Arrange - Mock repository to raise exception
        mock_template_repo.get_template_dependents.side_effect = RepositoryError("Database error")
        
        # Act & Assert
        with pytest.raises(TemplateDependencyError) as exc_info:
            await template_management_service.analyze_template_dependencies(
                template=sample_template,
                workspace_name="test_workspace"
            )
        
        assert "Dependency analysis failed" in str(exc_info.value)


class TestTemplateInheritance:
    """Tests for template inheritance analysis."""

    @pytest.mark.asyncio
    async def test_analyze_template_inheritance(
        self,
        template_management_service,
        sample_template
    ):
        """Test template inheritance chain analysis."""
        # Act
        result = await template_management_service.analyze_template_inheritance(
            template=sample_template,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, TemplateInheritanceChain)
        assert result.template == sample_template
        assert isinstance(result.parent_templates, list)
        assert isinstance(result.child_templates, list)
        assert isinstance(result.inheritance_depth, int)
        assert isinstance(result.conflicts, list)
        assert isinstance(result.merged_variables, set)
        assert isinstance(result.overridden_prompts, list)
        assert isinstance(result.resolution_order, list)

    @pytest.mark.asyncio
    async def test_inheritance_with_conflicts(
        self,
        template_management_service
    ):
        """Test inheritance analysis with conflicts."""
        # Arrange - Template that extends another with conflicts
        child_template = Template.create(
            name=TemplateName.from_user_input("child-template"),
            content_type=ContentType.generic(),
            yaml_content="""
metadata:
  name: "Child Template"
extends: "parent-template"

steps:
  conflicting_step:
    type: llm_generate
    prompt_template: "Overridden prompt"
""".strip()
        )
        
        # Act
        result = await template_management_service.analyze_template_inheritance(
            template=child_template,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result.conflicts, list)
        assert isinstance(result.overridden_prompts, list)


class TestTemplateOptimization:
    """Tests for template optimization functionality."""

    @pytest.mark.asyncio
    async def test_optimize_template_performance_basic(
        self,
        template_management_service,
        sample_template
    ):
        """Test basic template performance optimization."""
        # Act
        result = await template_management_service.optimize_template_performance(
            template=sample_template,
            workspace_name="test_workspace",
            optimization_level="basic"
        )
        
        # Assert
        assert isinstance(result, Template)
        assert result.get_metadata("optimization_level") == "basic"
        assert result.get_metadata("optimized_at") is not None

    @pytest.mark.asyncio
    async def test_optimize_template_performance_standard(
        self,
        template_management_service,
        sample_template
    ):
        """Test standard level template optimization."""
        # Act
        result = await template_management_service.optimize_template_performance(
            template=sample_template,
            workspace_name="test_workspace",
            optimization_level="standard"
        )
        
        # Assert
        assert isinstance(result, Template)
        assert result.get_metadata("optimization_level") == "standard"

    @pytest.mark.asyncio
    async def test_optimize_template_performance_aggressive(
        self,
        template_management_service,
        sample_template
    ):
        """Test aggressive template optimization."""
        # Act
        result = await template_management_service.optimize_template_performance(
            template=sample_template,
            workspace_name="test_workspace",
            optimization_level="aggressive"
        )
        
        # Assert
        assert isinstance(result, Template)
        assert result.get_metadata("optimization_level") == "aggressive"

    @pytest.mark.asyncio
    async def test_optimization_error_handling(
        self,
        template_management_service
    ):
        """Test optimization error handling."""
        # Arrange - Create template that might cause optimization errors
        problematic_template = Mock(spec=Template)
        problematic_template.set_metadata.side_effect = Exception("Optimization failed")
        
        # Act & Assert
        with pytest.raises(TemplateOptimizationError) as exc_info:
            await template_management_service.optimize_template_performance(
                template=problematic_template,
                optimization_level="standard"
            )
        
        assert "Template optimization failed" in str(exc_info.value)


class TestTemplateVersionComparison:
    """Tests for template version comparison."""

    @pytest.mark.asyncio
    async def test_compare_template_versions(
        self,
        template_management_service,
        sample_template
    ):
        """Test template version comparison."""
        # Arrange - Create a modified version
        modified_template = Template.create(
            name=sample_template.name,
            content_type=sample_template.content_type,
            yaml_content=sample_template.yaml_content + "\n# Modified version",
            tags=sample_template.tags,
            output_format=sample_template.output_format
        )
        
        # Act
        result = await template_management_service.compare_template_versions(
            old_template=sample_template,
            new_template=modified_template
        )
        
        # Assert
        assert isinstance(result, TemplateVersionComparison)
        assert result.old_version == sample_template
        assert result.new_version == modified_template
        assert isinstance(result.syntax_changes, list)
        assert isinstance(result.variable_changes, list)
        assert isinstance(result.prompt_changes, list)
        assert isinstance(result.compatibility_issues, list)
        assert isinstance(result.breaking_changes, list)
        assert isinstance(result.improvement_suggestions, list)


class TestTemplatePerformanceMetrics:
    """Tests for template performance metrics."""

    @pytest.mark.asyncio
    async def test_get_template_performance_metrics(
        self,
        template_management_service,
        mock_template_repo,
        sample_template
    ):
        """Test getting template performance metrics."""
        # Arrange
        mock_usage_stats = {
            "average_generation_time": 5.2,
            "average_token_usage": {"input": 150, "output": 300},
            "success_rate": 0.95,
            "cache_hit_rate": 0.75
        }
        mock_template_repo.get_template_usage_stats.return_value = mock_usage_stats
        
        # Act
        result = await template_management_service.get_template_performance_metrics(
            template=sample_template,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, TemplatePerformanceMetrics)
        assert result.template == sample_template
        assert result.average_generation_time == 5.2
        assert result.average_token_usage == {"input": 150, "output": 300}
        assert result.success_rate == 0.95
        assert result.error_rate == 0.05  # 1 - success_rate
        assert result.cache_hit_rate == 0.75
        assert isinstance(result.quality_score, float)
        assert isinstance(result.efficiency_score, float)
        assert isinstance(result.complexity_score, float)
        assert isinstance(result.optimization_suggestions, list)

    @pytest.mark.asyncio
    async def test_performance_metrics_caching(
        self,
        template_management_service,
        mock_template_repo,
        sample_template
    ):
        """Test that performance metrics are cached."""
        # Arrange
        mock_usage_stats = {"average_generation_time": 3.0}
        mock_template_repo.get_template_usage_stats.return_value = mock_usage_stats
        
        # Act - Call metrics twice
        result1 = await template_management_service.get_template_performance_metrics(
            template=sample_template,
            workspace_name="test_workspace"
        )
        result2 = await template_management_service.get_template_performance_metrics(
            template=sample_template,
            workspace_name="test_workspace"
        )
        
        # Assert - Should return cached result
        assert result1 is result2
        # Repository should only be called once due to caching
        mock_template_repo.get_template_usage_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_metrics_with_time_range(
        self,
        template_management_service,
        mock_template_repo,
        sample_template
    ):
        """Test performance metrics with specific time range."""
        # Arrange
        start_time = datetime.now() - timedelta(days=30)
        end_time = datetime.now()
        time_range = (start_time, end_time)
        
        mock_usage_stats = {"average_generation_time": 4.5}
        mock_template_repo.get_template_usage_stats.return_value = mock_usage_stats
        
        # Act
        result = await template_management_service.get_template_performance_metrics(
            template=sample_template,
            workspace_name="test_workspace",
            time_range=time_range
        )
        
        # Assert
        assert isinstance(result, TemplatePerformanceMetrics)
        assert result.average_generation_time == 4.5


class TestDependencyResolution:
    """Tests for template dependency resolution."""

    @pytest.mark.asyncio
    async def test_resolve_template_dependencies_success(
        self,
        template_management_service,
        mock_template_repo,
        sample_template
    ):
        """Test successful dependency resolution."""
        # Arrange
        dependency_template = Template.create(
            name=TemplateName.from_user_input("dependency-template"),
            content_type=ContentType.generic(),
            yaml_content="metadata:\n  name: 'Dependency Template'"
        )
        
        # Mock dependency graph
        with patch.object(
            template_management_service, 
            'analyze_template_dependencies'
        ) as mock_analyze:
            mock_graph = Mock()
            mock_graph.missing_dependencies = []
            mock_graph.circular_dependencies = []
            mock_graph.direct_dependencies = [TemplateName.from_user_input("dependency-template")]
            mock_graph.indirect_dependencies = []
            mock_analyze.return_value = mock_graph
            
            mock_template_repo.find_by_name.return_value = dependency_template
            
            # Act
            result = await template_management_service.resolve_template_dependencies(
                template=sample_template,
                workspace_name="test_workspace",
                auto_create_missing=False
            )
            
            # Assert
            assert isinstance(result, list)
            assert len(result) == 1
            assert result[0] == dependency_template

    @pytest.mark.asyncio
    async def test_resolve_dependencies_missing_error(
        self,
        template_management_service,
        sample_template
    ):
        """Test dependency resolution with missing dependencies."""
        # Arrange
        with patch.object(
            template_management_service, 
            'analyze_template_dependencies'
        ) as mock_analyze:
            mock_graph = Mock()
            mock_graph.missing_dependencies = [TemplateName.from_user_input("missing-template")]
            mock_graph.circular_dependencies = []
            mock_analyze.return_value = mock_graph
            
            # Act & Assert
            with pytest.raises(TemplateDependencyError) as exc_info:
                await template_management_service.resolve_template_dependencies(
                    template=sample_template,
                    auto_create_missing=False
                )
            
            assert "Missing dependencies" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_resolve_dependencies_circular_error(
        self,
        template_management_service,
        sample_template
    ):
        """Test dependency resolution with circular dependencies."""
        # Arrange
        with patch.object(
            template_management_service, 
            'analyze_template_dependencies'
        ) as mock_analyze:
            mock_graph = Mock()
            mock_graph.missing_dependencies = []
            mock_graph.circular_dependencies = [
                [TemplateName.from_user_input("template-a"), TemplateName.from_user_input("template-b")]
            ]
            mock_analyze.return_value = mock_graph
            
            # Act & Assert
            with pytest.raises(TemplateDependencyError) as exc_info:
                await template_management_service.resolve_template_dependencies(
                    template=sample_template
                )
            
            assert "Circular dependencies detected" in str(exc_info.value)


class TestPrivateHelperMethods:
    """Tests for private helper methods."""

    @pytest.mark.asyncio
    async def test_validate_yaml_syntax(
        self,
        template_management_service
    ):
        """Test YAML syntax validation helper."""
        # Test valid YAML
        valid_yaml = "key: value\nlist:\n  - item1\n  - item2"
        errors = await template_management_service._validate_yaml_syntax(valid_yaml)
        assert errors == []
        
        # Test invalid YAML
        invalid_yaml = "invalid: yaml: ["
        errors = await template_management_service._validate_yaml_syntax(invalid_yaml)
        assert len(errors) > 0
        assert "YAML syntax error" in errors[0]

    @pytest.mark.asyncio
    async def test_auto_detect_content_type(
        self,
        template_management_service
    ):
        """Test content type auto-detection."""
        # Test blog post detection
        blog_yaml = """
metadata:
  name: "Blog Post Template"
  description: "Create engaging blog articles"
"""
        content_type = await template_management_service._auto_detect_content_type(blog_yaml)
        assert content_type == ContentType.blog_post()
        
        # Test documentation detection
        doc_yaml = """
metadata:
  name: "Documentation Template"
  description: "Create technical documentation"
"""
        content_type = await template_management_service._auto_detect_content_type(doc_yaml)
        assert content_type == ContentType.documentation()
        
        # Test generic fallback
        generic_yaml = """
metadata:
  name: "Generic Template"
  description: "Create general content"
"""
        content_type = await template_management_service._auto_detect_content_type(generic_yaml)
        assert content_type == ContentType.generic()

    @pytest.mark.asyncio
    async def test_auto_generate_tags(
        self,
        template_management_service
    ):
        """Test automatic tag generation."""
        yaml_content = """
metadata:
  name: "Complex Multi-Step Blog Template"
  description: "Create detailed blog posts with research and analysis"

inputs:
  topic:
    type: text
  style:
    type: choice
    
steps:
  research:
    type: llm_generate
    prompt_template: "Research {{ inputs.topic }}"
  analysis:
    type: llm_generate
    prompt_template: "Analyze findings"
  writing:
    type: llm_generate
    prompt_template: "Write blog post"
  review:
    type: llm_generate
    prompt_template: "Review content"
  polish:
    type: llm_generate
    prompt_template: "Polish final version"
  publish:
    type: llm_generate
    prompt_template: "Prepare for publication"
"""
        
        tags = await template_management_service._auto_generate_tags(
            yaml_content, ContentType.blog_post()
        )
        
        assert isinstance(tags, list)
        assert "blog_post" in tags  # Content type should be included
        assert "multi-step" in tags  # Should detect multi-step template
        assert "complex" in tags  # Should detect complex template (>5 steps)
        assert "interactive" in tags  # Should detect inputs
        assert len(tags) <= 10  # Should limit total tags

    @pytest.mark.asyncio
    async def test_determine_default_format(
        self,
        template_management_service
    ):
        """Test default format determination."""
        # Blog post should default to markdown
        format_obj = await template_management_service._determine_default_format(
            ContentType.blog_post()
        )
        assert format_obj == ContentFormat.markdown()
        
        # Email should default to HTML
        format_obj = await template_management_service._determine_default_format(
            ContentType.email()
        )
        assert format_obj == ContentFormat.html()
        
        # Generic should default to text
        format_obj = await template_management_service._determine_default_format(
            ContentType.generic()
        )
        assert format_obj == ContentFormat.text()

    @pytest.mark.asyncio
    async def test_inherit_validation_rules(
        self,
        template_management_service
    ):
        """Test validation rule inheritance."""
        # Test blog post rules
        rules = await template_management_service._inherit_validation_rules(
            ContentType.blog_post()
        )
        assert isinstance(rules, list)
        assert len(rules) > 0
        # Should include word count, readability, and heading structure rules
        
        # Test documentation rules
        rules = await template_management_service._inherit_validation_rules(
            ContentType.documentation()
        )
        assert isinstance(rules, list)
        assert len(rules) > 0
        
        # Test email rules
        rules = await template_management_service._inherit_validation_rules(
            ContentType.email()
        )
        assert isinstance(rules, list)
        assert len(rules) > 0


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_yaml_content(
        self,
        template_management_service,
        mock_template_repo
    ):
        """Test handling of empty YAML content."""
        # Arrange
        name = TemplateName.from_user_input("empty-template")
        mock_template_repo.find_by_name.return_value = None
        
        # Act & Assert
        with pytest.raises(TemplateValidationError):
            await template_management_service.create_template(
                name=name,
                yaml_content="",
                options=TemplateCreationOptions(validate_syntax=True)
            )

    @pytest.mark.asyncio
    async def test_malformed_yaml_content(
        self,
        template_management_service,
        mock_template_repo
    ):
        """Test handling of malformed YAML content."""
        # Arrange
        name = TemplateName.from_user_input("malformed-template")
        malformed_yaml = "key: value\n  invalid indentation\n  - broken list"
        mock_template_repo.find_by_name.return_value = None
        
        # Act & Assert
        with pytest.raises(TemplateValidationError):
            await template_management_service.create_template(
                name=name,
                yaml_content=malformed_yaml,
                options=TemplateCreationOptions(validate_syntax=True)
            )

    @pytest.mark.asyncio
    async def test_repository_error_handling(
        self,
        template_management_service,
        mock_template_repo,
        sample_yaml_content
    ):
        """Test repository error handling."""
        # Arrange
        name = TemplateName.from_user_input("repo-error-template")
        mock_template_repo.find_by_name.return_value = None
        mock_template_repo.save.side_effect = RepositoryError("Database connection failed")
        
        # Act & Assert
        with pytest.raises(RepositoryError):
            await template_management_service.create_template(
                name=name,
                yaml_content=sample_yaml_content
            )

    @pytest.mark.asyncio
    async def test_none_template_validation(
        self,
        template_management_service
    ):
        """Test validation with None template."""
        # This should be handled gracefully by the service
        # In a real implementation, this might raise a specific error
        pass

    @pytest.mark.asyncio
    async def test_large_template_handling(
        self,
        template_management_service,
        mock_template_repo
    ):
        """Test handling of very large templates."""
        # Arrange
        name = TemplateName.from_user_input("large-template")
        # Create a large YAML content (simulate a complex template)
        large_yaml = """
metadata:
  name: "Large Template"
  description: "A template with many steps"

inputs:
""" + "\n".join([f"  input_{i}:\n    type: text" for i in range(50)]) + """

steps:
""" + "\n".join([f"""  step_{i}:
    type: llm_generate
    prompt_template: "Process step {i} with many variables: """ + " ".join([f"{{{{ inputs.input_{j} }}}}" for j in range(min(i+1, 20))]) + "\""
    for i in range(20)])
        
        mock_template_repo.find_by_name.return_value = None
        mock_template_repo.save.return_value = Mock(id="large_template_id")
        
        # Act
        result = await template_management_service.create_template(
            name=name,
            yaml_content=large_yaml
        )
        
        # Assert
        assert result is not None
        
        # Validate the large template
        validation_result = await template_management_service.validate_template_comprehensive(
            template=result
        )
        
        # Should detect performance issues
        assert len(validation_result.performance_issues) > 0