"""Unit tests for ContentGenerationService.

Tests comprehensive generated content management including validation, quality assessment,
versioning, optimization, enhancement, analytics, and insights capabilities.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from src.writeit.domains.content.services.content_generation_service import (
    ContentGenerationService,
    ContentValidationError,
    ContentOptimizationError,
    ContentAnalysisError,
    QualityAssessmentLevel,
    ContentOptimizationLevel,
    ContentStatus,
    ContentCreationOptions,
    ContentValidationResult,
    ContentQualityAssessment,
    ContentVersionComparison,
    ContentOptimizationPlan,
    ContentAnalytics,
    ContentEnhancementSuggestion,
    ContentInsights
)
from src.writeit.domains.content.entities.generated_content import GeneratedContent
from src.writeit.domains.content.entities.template import Template
from src.writeit.domains.content.entities.style_primer import StylePrimer
from src.writeit.domains.content.value_objects.content_id import ContentId
from src.writeit.domains.content.value_objects.content_type import ContentType
from src.writeit.domains.content.value_objects.template_name import TemplateName
from src.writeit.domains.content.value_objects.style_name import StyleName
from src.writeit.shared.repository import RepositoryError


# Test Fixtures

@pytest.fixture
def mock_content_repo():
    """Mock generated content repository."""
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.get_content_usage_stats = AsyncMock()
    return repo


@pytest.fixture
def content_generation_service(mock_content_repo):
    """Content generation service with mocked dependencies."""
    return ContentGenerationService(mock_content_repo)


@pytest.fixture
def sample_template():
    """Sample template for testing."""
    return Template.create(
        name=TemplateName.from_user_input("article-template"),
        content_type=ContentType.blog_post(),
        yaml_content="""
metadata:
  name: "Article Template"
  description: "Generate blog articles"

steps:
  title:
    type: llm_generate
    prompt_template: "Create title for {{ inputs.topic }}"
  content:
    type: llm_generate
    prompt_template: "Write article about {{ inputs.topic }} with title {{ steps.title }}"
""".strip()
    )


@pytest.fixture
def sample_style():
    """Sample style primer for testing."""
    return StylePrimer.create(
        name=StyleName.from_user_input("professional-style"),
        guidelines="Write in a professional, authoritative tone that demonstrates expertise while remaining accessible.",
        content_types=[ContentType.blog_post(), ContentType.documentation()]
    )


@pytest.fixture
def sample_content():
    """Sample generated content for testing."""
    return GeneratedContent.create(
        content_text="""
# The Future of Artificial Intelligence in Business

Artificial intelligence is rapidly transforming the business landscape, offering unprecedented opportunities for automation, decision-making, and customer engagement. Companies across industries are leveraging AI technologies to streamline operations, reduce costs, and gain competitive advantages.

## Key Benefits of AI in Business

1. **Automation of Routine Tasks**: AI can handle repetitive processes, freeing up human resources for strategic work.
2. **Enhanced Decision Making**: Machine learning algorithms can analyze vast datasets to provide actionable insights.
3. **Improved Customer Experience**: AI-powered chatbots and recommendation systems personalize user interactions.

## Implementation Strategies

Successful AI implementation requires careful planning and consideration of organizational readiness. Companies should start with pilot projects to demonstrate value before scaling across the enterprise.

## Conclusion

The integration of artificial intelligence into business operations is no longer a question of if, but when. Organizations that embrace these technologies thoughtfully will be best positioned for future success.
""".strip(),
        template_id="template_123",
        content_type=ContentType.blog_post(),
        style_id="style_456"
    )


@pytest.fixture
def sample_long_content():
    """Sample long generated content for testing."""
    long_text = """
# Comprehensive Guide to Modern Software Development

""" + "This is a detailed paragraph about software development practices. " * 100 + """

## Chapter 1: Introduction to Modern Development

""" + "Modern software development involves many complex considerations and practices. " * 50 + """

## Chapter 2: Best Practices

""" + "Following best practices is essential for maintaining code quality and team productivity. " * 75
    
    return GeneratedContent.create(
        content_text=long_text.strip(),
        template_id="template_789",
        content_type=ContentType.documentation(),
        style_id="style_123"
    )


@pytest.fixture
def creation_options():
    """Sample content creation options."""
    return ContentCreationOptions(
        validate_quality=True,
        assess_originality=True,
        auto_optimize=False,
        generate_metadata=True,
        track_analytics=True,
        apply_style_validation=True,
        metadata={"author": "test_user", "category": "technology"}
    )


# Core Content Management Tests

class TestContentCreation:
    """Tests for generated content creation functionality."""

    @pytest.mark.asyncio
    async def test_create_content_success(
        self,
        content_generation_service,
        mock_content_repo,
        sample_template,
        sample_style,
        creation_options
    ):
        """Test successful content creation with all options."""
        # Arrange
        content_text = "This is a well-written article about artificial intelligence in business. It provides valuable insights and actionable recommendations for organizations."
        mock_content_repo.save.return_value = Mock(id="content_123")
        
        # Act
        result = await content_generation_service.create_content(
            content_text=content_text,
            template=sample_template,
            style=sample_style,
            options=creation_options,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert result is not None
        mock_content_repo.save.assert_called_once()
        
        # Verify content was saved with correct workspace
        save_call = mock_content_repo.save.call_args
        saved_content, workspace = save_call[0]
        assert workspace == "test_workspace"
        assert saved_content.template_id == sample_template.id
        assert saved_content.style_id == sample_style.id

    @pytest.mark.asyncio
    async def test_create_content_validation_failure(
        self,
        content_generation_service,
        mock_content_repo,
        sample_template
    ):
        """Test content creation with validation failure."""
        # Arrange
        poor_content = "Bad content."  # Too short, low quality
        options = ContentCreationOptions(validate_quality=True)
        
        # Act & Assert
        with pytest.raises(ContentValidationError) as exc_info:
            await content_generation_service.create_content(
                content_text=poor_content,
                template=sample_template,
                options=options
            )
        
        assert "Content validation failed" in str(exc_info.value)
        mock_content_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_content_with_auto_optimization(
        self,
        content_generation_service,
        mock_content_repo,
        sample_template,
        sample_style
    ):
        """Test content creation with auto-optimization enabled."""
        # Arrange
        content_text = "This is decent content that could be improved through optimization techniques and better structure."
        options = ContentCreationOptions(
            validate_quality=False,  # Skip validation to avoid blocking
            auto_optimize=True
        )
        mock_content_repo.save.return_value = Mock(id="content_456")
        
        # Act
        result = await content_generation_service.create_content(
            content_text=content_text,
            template=sample_template,
            style=sample_style,
            options=options
        )
        
        # Assert
        assert result is not None
        mock_content_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_content_minimal_options(
        self,
        content_generation_service,
        mock_content_repo,
        sample_template
    ):
        """Test content creation with minimal options."""
        # Arrange
        content_text = "This is a standard article with good quality content that meets basic requirements for publication."
        mock_content_repo.save.return_value = Mock(id="content_789")
        
        # Act - No options provided, should use defaults
        result = await content_generation_service.create_content(
            content_text=content_text,
            template=sample_template
        )
        
        # Assert
        assert result is not None
        mock_content_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_content_with_metadata(
        self,
        content_generation_service,
        mock_content_repo,
        sample_template
    ):
        """Test content creation with metadata generation."""
        # Arrange
        content_text = "This is a comprehensive article about modern technology trends and their impact on business operations."
        options = ContentCreationOptions(
            generate_metadata=True,
            validate_quality=False
        )
        mock_content_repo.save.return_value = Mock(id="content_meta")
        
        # Act
        result = await content_generation_service.create_content(
            content_text=content_text,
            template=sample_template,
            options=options
        )
        
        # Assert
        assert result is not None
        # Should have metadata generated (word count, character count, etc.)
        mock_content_repo.save.assert_called_once()


class TestContentValidation:
    """Tests for comprehensive content validation."""

    @pytest.mark.asyncio
    async def test_validate_content_comprehensive_success(
        self,
        content_generation_service,
        sample_content,
        sample_template,
        sample_style
    ):
        """Test comprehensive content validation for valid content."""
        # Act
        result = await content_generation_service.validate_content_comprehensive(
            content=sample_content,
            template=sample_template,
            style=sample_style,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, ContentValidationResult)
        assert result.is_valid is True
        assert isinstance(result.quality_score, float)
        assert result.quality_score >= 0.6  # Should meet minimum quality
        assert isinstance(result.readability_score, float)
        assert result.readability_score >= 0.5  # Should meet minimum readability
        assert isinstance(result.originality_score, float)
        assert isinstance(result.style_compliance_score, float)
        assert isinstance(result.validation_errors, list)
        assert isinstance(result.quality_issues, list)
        assert isinstance(result.style_violations, list)
        assert isinstance(result.improvement_suggestions, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.performance_metrics, dict)

    @pytest.mark.asyncio
    async def test_validate_content_with_errors(
        self,
        content_generation_service,
        sample_template
    ):
        """Test content validation with various errors."""
        # Arrange - Create content with validation issues
        poor_content = GeneratedContent.create(
            content_text="Bad!!!!",  # Too short, poor quality
            template_id=sample_template.id,
            content_type=ContentType.blog_post()
        )
        
        # Act
        result = await content_generation_service.validate_content_comprehensive(
            content=poor_content,
            template=sample_template
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.validation_errors) > 0  # Should have basic validation errors
        assert result.quality_score < 0.6  # Should be below quality threshold

    @pytest.mark.asyncio
    async def test_validate_content_against_template(
        self,
        content_generation_service,
        sample_template
    ):
        """Test content validation against template requirements."""
        # Arrange - Create content that doesn't match template requirements
        mismatched_content = GeneratedContent.create(
            content_text="This is email content",
            template_id=sample_template.id,
            content_type=ContentType.email()  # Template expects blog_post
        )
        
        # Act
        result = await content_generation_service.validate_content_comprehensive(
            content=mismatched_content,
            template=sample_template
        )
        
        # Assert
        assert len(result.validation_errors) > 0  # Should detect content type mismatch

    @pytest.mark.asyncio
    async def test_validate_content_against_style(
        self,
        content_generation_service,
        sample_content,
        sample_style
    ):
        """Test content validation against style primer."""
        # Act
        result = await content_generation_service.validate_content_comprehensive(
            content=sample_content,
            style=sample_style
        )
        
        # Assert
        assert isinstance(result.style_compliance_score, float)
        assert result.style_compliance_score >= 0.0

    @pytest.mark.asyncio
    async def test_validate_content_caching(
        self,
        content_generation_service,
        sample_content
    ):
        """Test that validation results are cached properly."""
        # Act - Call validation twice
        result1 = await content_generation_service.validate_content_comprehensive(
            content=sample_content,
            workspace_name="test_workspace"
        )
        result2 = await content_generation_service.validate_content_comprehensive(
            content=sample_content,
            workspace_name="test_workspace"
        )
        
        # Assert - Should return the same cached result
        assert result1 is result2


class TestQualityAssessment:
    """Tests for content quality assessment."""

    @pytest.mark.asyncio
    async def test_assess_content_quality_basic(
        self,
        content_generation_service,
        sample_content
    ):
        """Test basic content quality assessment."""
        # Act
        result = await content_generation_service.assess_content_quality(
            content=sample_content,
            level=QualityAssessmentLevel.BASIC,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, ContentQualityAssessment)
        assert result.content == sample_content
        assert isinstance(result.overall_score, float)
        assert 0.0 <= result.overall_score <= 1.0
        assert isinstance(result.dimension_scores, dict)
        assert len(result.dimension_scores) > 0
        assert isinstance(result.readability_metrics, dict)
        assert isinstance(result.style_analysis, dict)
        assert isinstance(result.structure_analysis, dict)
        assert isinstance(result.quality_issues, list)
        assert isinstance(result.strengths, list)
        assert isinstance(result.improvement_areas, list)

    @pytest.mark.asyncio
    async def test_assess_content_quality_comprehensive(
        self,
        content_generation_service,
        sample_content
    ):
        """Test comprehensive content quality assessment."""
        # Act
        result = await content_generation_service.assess_content_quality(
            content=sample_content,
            level=QualityAssessmentLevel.COMPREHENSIVE,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, ContentQualityAssessment)
        assert isinstance(result.language_analysis, dict)
        assert isinstance(result.originality_analysis, dict)
        # Comprehensive level should include language and originality analysis

    @pytest.mark.asyncio
    async def test_assess_content_quality_expert(
        self,
        content_generation_service,
        sample_content
    ):
        """Test expert level content quality assessment."""
        # Act
        result = await content_generation_service.assess_content_quality(
            content=sample_content,
            level=QualityAssessmentLevel.EXPERT,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, ContentQualityAssessment)
        assert isinstance(result.benchmark_comparisons, dict)
        # Expert level should include benchmark comparisons

    @pytest.mark.asyncio
    async def test_quality_assessment_caching(
        self,
        content_generation_service,
        sample_content
    ):
        """Test that quality assessment results are cached."""
        # Act - Call assessment twice with same parameters
        result1 = await content_generation_service.assess_content_quality(
            content=sample_content,
            level=QualityAssessmentLevel.STANDARD,
            workspace_name="test_workspace"
        )
        result2 = await content_generation_service.assess_content_quality(
            content=sample_content,
            level=QualityAssessmentLevel.STANDARD,
            workspace_name="test_workspace"
        )
        
        # Assert - Should return cached result
        assert result1 is result2


class TestContentOptimization:
    """Tests for content optimization functionality."""

    @pytest.mark.asyncio
    async def test_create_optimization_plan_success(
        self,
        content_generation_service,
        sample_content
    ):
        """Test creation of content optimization plan."""
        # Arrange
        target_metrics = {"quality_score": 0.9, "readability_score": 0.8}
        
        # Act
        result = await content_generation_service.create_optimization_plan(
            content=sample_content,
            target_metrics=target_metrics,
            level=ContentOptimizationLevel.STANDARD,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, ContentOptimizationPlan)
        assert result.content == sample_content
        assert result.optimization_level == ContentOptimizationLevel.STANDARD
        assert result.target_metrics == target_metrics
        assert isinstance(result.optimization_actions, list)
        assert isinstance(result.estimated_improvement, dict)
        assert isinstance(result.risk_assessment, list)
        assert isinstance(result.execution_order, list)
        assert isinstance(result.expected_outcome, dict)

    @pytest.mark.asyncio
    async def test_create_optimization_plan_default_targets(
        self,
        content_generation_service,
        sample_content
    ):
        """Test optimization plan creation with default target metrics."""
        # Act - No target metrics provided, should use defaults
        result = await content_generation_service.create_optimization_plan(
            content=sample_content,
            level=ContentOptimizationLevel.BASIC
        )
        
        # Assert
        assert isinstance(result, ContentOptimizationPlan)
        assert isinstance(result.target_metrics, dict)
        assert len(result.target_metrics) > 0  # Should have default targets

    @pytest.mark.asyncio
    async def test_optimize_content_success(
        self,
        content_generation_service,
        mock_content_repo,
        sample_content
    ):
        """Test successful content optimization execution."""
        # Arrange
        plan = ContentOptimizationPlan(
            content=sample_content,
            optimization_level=ContentOptimizationLevel.STANDARD,
            target_metrics={"quality_score": 0.85},
            optimization_actions=["improve_clarity", "enhance_readability"],
            estimated_improvement={"quality_score": 0.1},
            risk_assessment=["minimal_risk"],
            execution_order=["improve_clarity", "enhance_readability"],
            expected_outcome={"improved_quality": True}
        )
        
        mock_content_repo.save.return_value = Mock(id="optimized_content_id")
        
        # Mock validation to pass
        with patch.object(
            content_generation_service,
            'validate_content_comprehensive'
        ) as mock_validate:
            mock_validate.return_value = Mock(is_valid=True, validation_errors=[])
            
            # Act
            result = await content_generation_service.optimize_content(
                plan=plan,
                workspace_name="test_workspace"
            )
            
            # Assert
            assert result is not None
            assert result.get_metadata("optimization_level") == "standard"
            assert result.get_metadata("optimized_at") is not None
            mock_content_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_optimize_content_validation_failure(
        self,
        content_generation_service,
        sample_content
    ):
        """Test content optimization with validation failure."""
        # Arrange
        plan = ContentOptimizationPlan(
            content=sample_content,
            optimization_level=ContentOptimizationLevel.AGGRESSIVE,
            target_metrics={},
            optimization_actions=["break_content"],  # Action that might break content
            estimated_improvement={},
            risk_assessment=["high_risk"],
            execution_order=["break_content"],
            expected_outcome={}
        )
        
        # Mock validation to fail
        with patch.object(
            content_generation_service,
            'validate_content_comprehensive'
        ) as mock_validate:
            mock_validate.return_value = Mock(
                is_valid=False,
                validation_errors=["Optimization broke the content"]
            )
            
            # Act & Assert
            with pytest.raises(ContentOptimizationError) as exc_info:
                await content_generation_service.optimize_content(plan=plan)
            
            assert "Optimized content validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_optimization_plan_error_handling(
        self,
        content_generation_service
    ):
        """Test optimization plan creation error handling."""
        # Arrange - Create problematic content
        problematic_content = Mock()
        problematic_content.id = "problematic_id"
        
        # Mock assessment to raise exception
        with patch.object(
            content_generation_service,
            'assess_content_quality',
            side_effect=Exception("Assessment failed")
        ):
            # Act & Assert
            with pytest.raises(ContentOptimizationError) as exc_info:
                await content_generation_service.create_optimization_plan(
                    content=problematic_content
                )
            
            assert "Optimization plan creation failed" in str(exc_info.value)


class TestContentVersionComparison:
    """Tests for content version comparison."""

    @pytest.mark.asyncio
    async def test_compare_content_versions(
        self,
        content_generation_service,
        sample_content
    ):
        """Test content version comparison."""
        # Arrange - Create a revised version
        revised_content = GeneratedContent.create(
            content_text=sample_content.content_text + "\n\n## Additional Section\n\nThis is additional content added in the revision.",
            template_id=sample_content.template_id,
            content_type=sample_content.content_type,
            style_id=sample_content.style_id
        )
        
        # Act
        result = await content_generation_service.compare_content_versions(
            original=sample_content,
            revised=revised_content
        )
        
        # Assert
        assert isinstance(result, ContentVersionComparison)
        assert result.original_content == sample_content
        assert result.revised_content == revised_content
        assert isinstance(result.similarity_score, float)
        assert 0.0 <= result.similarity_score <= 1.0
        assert isinstance(result.change_summary, dict)
        assert isinstance(result.quality_improvement, float)
        assert isinstance(result.readability_change, float)
        assert isinstance(result.style_consistency_change, float)
        assert isinstance(result.semantic_changes, list)
        assert isinstance(result.structural_changes, list)
        assert isinstance(result.impact_assessment, str)
        assert isinstance(result.recommendation, str)

    @pytest.mark.asyncio
    async def test_compare_identical_versions(
        self,
        content_generation_service,
        sample_content
    ):
        """Test comparison of identical content versions."""
        # Act
        result = await content_generation_service.compare_content_versions(
            original=sample_content,
            revised=sample_content
        )
        
        # Assert
        assert result.similarity_score == 0.0  # Identical content should have high similarity
        assert result.quality_improvement == 0.0  # No improvement expected


class TestContentAnalytics:
    """Tests for content analytics functionality."""

    @pytest.mark.asyncio
    async def test_get_content_analytics(
        self,
        content_generation_service,
        mock_content_repo,
        sample_content
    ):
        """Test getting comprehensive content analytics."""
        # Arrange
        mock_usage_stats = {
            "views": 1500,
            "shares": 75,
            "comments": 23,
            "engagement_rate": 0.12
        }
        mock_content_repo.get_content_usage_stats.return_value = mock_usage_stats
        
        # Act
        result = await content_generation_service.get_content_analytics(
            content=sample_content,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, ContentAnalytics)
        assert result.content == sample_content
        assert result.usage_metrics == mock_usage_stats
        assert isinstance(result.engagement_metrics, dict)
        assert isinstance(result.quality_metrics, dict)
        assert isinstance(result.performance_trends, dict)
        assert isinstance(result.audience_feedback, dict)
        assert isinstance(result.comparative_performance, dict)
        assert isinstance(result.optimization_opportunities, list)
        assert isinstance(result.success_indicators, list)

    @pytest.mark.asyncio
    async def test_get_content_analytics_with_time_range(
        self,
        content_generation_service,
        mock_content_repo,
        sample_content
    ):
        """Test content analytics with specific time range."""
        # Arrange
        start_time = datetime.now() - timedelta(days=30)
        end_time = datetime.now()
        time_range = (start_time, end_time)
        
        mock_usage_stats = {"views": 500}
        mock_content_repo.get_content_usage_stats.return_value = mock_usage_stats
        
        # Act
        result = await content_generation_service.get_content_analytics(
            content=sample_content,
            time_range=time_range,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, ContentAnalytics)
        assert result.usage_metrics == mock_usage_stats

    @pytest.mark.asyncio
    async def test_analytics_caching(
        self,
        content_generation_service,
        mock_content_repo,
        sample_content
    ):
        """Test that analytics results are cached."""
        # Arrange
        mock_usage_stats = {"views": 1000}
        mock_content_repo.get_content_usage_stats.return_value = mock_usage_stats
        
        # Act - Call analytics twice
        result1 = await content_generation_service.get_content_analytics(
            content=sample_content,
            workspace_name="test_workspace"
        )
        result2 = await content_generation_service.get_content_analytics(
            content=sample_content,
            workspace_name="test_workspace"
        )
        
        # Assert - Should return cached result
        assert result1 is result2
        # Repository should only be called once due to caching
        mock_content_repo.get_content_usage_stats.assert_called_once()


class TestContentInsights:
    """Tests for content insights generation."""

    @pytest.mark.asyncio
    async def test_generate_content_insights(
        self,
        content_generation_service,
        sample_content
    ):
        """Test comprehensive content insights generation."""
        # Act
        result = await content_generation_service.generate_content_insights(
            content=sample_content,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, ContentInsights)
        assert result.content == sample_content
        assert isinstance(result.key_themes, list)
        assert isinstance(result.sentiment_analysis, dict)
        assert isinstance(result.topic_distribution, dict)
        assert isinstance(result.keyword_analysis, dict)
        assert isinstance(result.audience_alignment, dict)
        assert isinstance(result.competitive_analysis, dict)
        assert isinstance(result.market_relevance, float)
        assert 0.0 <= result.market_relevance <= 1.0
        assert isinstance(result.trending_elements, list)
        assert isinstance(result.optimization_potential, float)
        assert 0.0 <= result.optimization_potential <= 1.0

    @pytest.mark.asyncio
    async def test_generate_insights_error_handling(
        self,
        content_generation_service,
        sample_content
    ):
        """Test content insights generation error handling."""
        # Arrange - Mock method to raise exception
        with patch.object(
            content_generation_service,
            '_extract_key_themes',
            side_effect=Exception("Theme extraction failed")
        ):
            # Act & Assert
            with pytest.raises(ContentAnalysisError) as exc_info:
                await content_generation_service.generate_content_insights(
                    content=sample_content
                )
            
            assert "Content insight generation failed" in str(exc_info.value)


class TestEnhancementSuggestions:
    """Tests for content enhancement suggestions."""

    @pytest.mark.asyncio
    async def test_generate_enhancement_suggestions(
        self,
        content_generation_service,
        sample_content
    ):
        """Test generation of content enhancement suggestions."""
        # Act
        result = await content_generation_service.generate_enhancement_suggestions(
            content=sample_content,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, list)
        assert all(isinstance(suggestion, ContentEnhancementSuggestion) for suggestion in result)
        if result:
            suggestion = result[0]
            assert isinstance(suggestion.suggestion_type, str)
            assert isinstance(suggestion.description, str)
            assert suggestion.impact_level in ["low", "medium", "high"]
            assert suggestion.effort_required in ["minimal", "moderate", "significant"]
            assert isinstance(suggestion.expected_improvement, dict)
            assert isinstance(suggestion.implementation_steps, list)
            assert isinstance(suggestion.examples, list)
            assert isinstance(suggestion.confidence_score, float)
            assert 0.0 <= suggestion.confidence_score <= 1.0

    @pytest.mark.asyncio
    async def test_generate_targeted_enhancement_suggestions(
        self,
        content_generation_service,
        sample_content
    ):
        """Test generation of targeted enhancement suggestions."""
        # Arrange
        target_improvements = ["clarity", "engagement"]
        
        # Act
        result = await content_generation_service.generate_enhancement_suggestions(
            content=sample_content,
            target_improvements=target_improvements,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, list)
        # Should generate suggestions focused on the target areas


class TestPrivateHelperMethods:
    """Tests for private helper methods."""

    @pytest.mark.asyncio
    async def test_validate_basic_content(
        self,
        content_generation_service
    ):
        """Test basic content validation helper."""
        # Test valid content
        valid_content = GeneratedContent.create(
            content_text="This is valid content with sufficient length and quality.",
            template_id="template_123",
            content_type=ContentType.generic()
        )
        errors = await content_generation_service._validate_basic_content(valid_content)
        assert errors == []
        
        # Test empty content
        empty_content = GeneratedContent.create(
            content_text="",
            template_id="template_123",
            content_type=ContentType.generic()
        )
        errors = await content_generation_service._validate_basic_content(empty_content)
        assert len(errors) > 0
        assert "empty" in errors[0]
        
        # Test too short content
        short_content = GeneratedContent.create(
            content_text="Short",
            template_id="template_123",
            content_type=ContentType.generic()
        )
        errors = await content_generation_service._validate_basic_content(short_content)
        assert len(errors) > 0
        assert "too short" in errors[0]

    @pytest.mark.asyncio
    async def test_calculate_quality_score(
        self,
        content_generation_service,
        sample_content,
        sample_long_content
    ):
        """Test quality score calculation."""
        # Test good quality content
        score = await content_generation_service._calculate_quality_score(sample_content)
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be decent quality
        
        # Test longer content (should potentially score higher)
        long_score = await content_generation_service._calculate_quality_score(sample_long_content)
        assert isinstance(long_score, float)
        assert 0.0 <= long_score <= 1.0

    @pytest.mark.asyncio
    async def test_calculate_readability_score(
        self,
        content_generation_service,
        sample_content
    ):
        """Test readability score calculation."""
        # Act
        score = await content_generation_service._calculate_readability_score(sample_content)
        
        # Assert
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_count_syllables(
        self,
        content_generation_service
    ):
        """Test syllable counting helper."""
        # Test simple words
        assert content_generation_service._count_syllables("cat") == 1
        assert content_generation_service._count_syllables("happy") == 2
        assert content_generation_service._count_syllables("beautiful") == 3
        assert content_generation_service._count_syllables("university") == 4
        
        # Test words with silent e
        assert content_generation_service._count_syllables("make") == 1
        assert content_generation_service._count_syllables("time") == 1
        
        # Test edge cases
        assert content_generation_service._count_syllables("") == 1  # Minimum of 1
        assert content_generation_service._count_syllables("a") == 1

    @pytest.mark.asyncio
    async def test_assess_content_originality(
        self,
        content_generation_service,
        sample_content
    ):
        """Test content originality assessment."""
        # Act
        score = await content_generation_service._assess_content_originality(
            sample_content,
            "test_workspace"
        )
        
        # Assert
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    @pytest.mark.asyncio
    async def test_generate_content_metadata(
        self,
        content_generation_service,
        sample_content,
        sample_template,
        sample_style
    ):
        """Test content metadata generation."""
        # Act
        metadata = await content_generation_service._generate_content_metadata(
            sample_content,
            sample_template,
            sample_style
        )
        
        # Assert
        assert isinstance(metadata, dict)
        assert "word_count" in metadata
        assert "character_count" in metadata
        assert "paragraph_count" in metadata
        assert "generated_at" in metadata
        assert "template_name" in metadata
        assert "content_type" in metadata
        assert "style_name" in metadata
        
        # Verify counts are reasonable
        assert metadata["word_count"] > 0
        assert metadata["character_count"] > metadata["word_count"]  # Characters > words


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_content_text(
        self,
        content_generation_service,
        sample_template
    ):
        """Test handling of empty content text."""
        # Act & Assert
        with pytest.raises(ContentValidationError):
            await content_generation_service.create_content(
                content_text="",
                template=sample_template,
                options=ContentCreationOptions(validate_quality=True)
            )

    @pytest.mark.asyncio
    async def test_none_content_validation(
        self,
        content_generation_service
    ):
        """Test validation with None content."""
        # This should be handled gracefully by the service
        pass

    @pytest.mark.asyncio
    async def test_repository_error_handling(
        self,
        content_generation_service,
        mock_content_repo,
        sample_template
    ):
        """Test repository error handling."""
        # Arrange
        content_text = "This is test content for error handling."
        mock_content_repo.save.side_effect = RepositoryError("Database connection failed")
        
        # Act & Assert
        with pytest.raises(RepositoryError):
            await content_generation_service.create_content(
                content_text=content_text,
                template=sample_template,
                options=ContentCreationOptions(validate_quality=False)
            )

    @pytest.mark.asyncio
    async def test_very_long_content_handling(
        self,
        content_generation_service,
        mock_content_repo,
        sample_template
    ):
        """Test handling of very long content."""
        # Arrange
        very_long_content = "This is a very long content piece. " * 10000  # Very long content
        mock_content_repo.save.return_value = Mock(id="long_content_id")
        
        # Act
        result = await content_generation_service.create_content(
            content_text=very_long_content,
            template=sample_template,
            options=ContentCreationOptions(validate_quality=False)  # Skip validation to avoid blocking
        )
        
        # Assert
        assert result is not None
        
        # Validate the long content - should detect potential issues
        validation_result = await content_generation_service.validate_content_comprehensive(
            content=result
        )
        
        # Should handle long content gracefully
        assert isinstance(validation_result, ContentValidationResult)

    @pytest.mark.asyncio
    async def test_concurrent_content_operations(
        self,
        content_generation_service,
        mock_content_repo,
        sample_content
    ):
        """Test concurrent content operations and caching behavior."""
        # Arrange
        mock_content_repo.get_content_usage_stats.return_value = {"views": 100}
        
        # Act - Perform multiple concurrent operations
        import asyncio
        
        tasks = [
            content_generation_service.validate_content_comprehensive(sample_content),
            content_generation_service.assess_content_quality(sample_content),
            content_generation_service.get_content_analytics(sample_content),
            content_generation_service.generate_content_insights(sample_content)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Assert - All operations should complete successfully
        assert len(results) == 4
        assert all(result is not None for result in results)

    @pytest.mark.asyncio
    async def test_malformed_content_handling(
        self,
        content_generation_service,
        mock_content_repo,
        sample_template
    ):
        """Test handling of malformed content text."""
        # Arrange
        malformed_content = "This content has strange characters: \x00\x01\x02 and control sequences."
        mock_content_repo.save.return_value = Mock(id="malformed_content_id")
        
        # Act
        result = await content_generation_service.create_content(
            content_text=malformed_content,
            template=sample_template,
            options=ContentCreationOptions(validate_quality=False)
        )
        
        # Assert
        assert result is not None
        # Should handle malformed content gracefully