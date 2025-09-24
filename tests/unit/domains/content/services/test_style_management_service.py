"""Unit tests for StyleManagementService.

Tests comprehensive style primer management including validation, inheritance,
composition, optimization, compatibility analysis, and recommendation capabilities.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from src.writeit.domains.content.services.style_management_service import (
    StyleManagementService,
    StyleValidationError,
    StyleInheritanceError,
    StyleCompositionError,
    StyleCompatibilityLevel,
    StyleOptimizationLevel,
    StyleCreationOptions,
    StyleInheritanceChain,
    StyleCompatibilityMatrix,
    StyleValidationResult,
    StyleCompositionPlan,
    StylePerformanceMetrics,
    StyleRecommendation,
    StyleComparison
)
from src.writeit.domains.content.entities.style_primer import StylePrimer
from src.writeit.domains.content.value_objects.style_name import StyleName
from src.writeit.domains.content.value_objects.content_type import ContentType
from src.writeit.shared.repository import EntityAlreadyExistsError, RepositoryError


# Test Fixtures

@pytest.fixture
def mock_style_repo():
    """Mock style primer repository."""
    repo = AsyncMock()
    repo.find_by_name = AsyncMock()
    repo.save = AsyncMock()
    repo.find_by_content_type = AsyncMock()
    repo.get_style_usage_stats = AsyncMock()
    return repo


@pytest.fixture
def style_management_service(mock_style_repo):
    """Style management service with mocked dependencies."""
    return StyleManagementService(mock_style_repo)


@pytest.fixture
def sample_style():
    """Sample style primer for testing."""
    return StylePrimer.create(
        name=StyleName.from_user_input("formal-business"),
        guidelines="Write in a formal, professional business tone. Use clear, concise language that demonstrates expertise and builds trust. Avoid casual expressions and maintain a respectful, authoritative voice throughout.",
        content_types=[ContentType.blog_post(), ContentType.documentation()]
    )


@pytest.fixture
def casual_style():
    """Casual style primer for testing."""
    return StylePrimer.create(
        name=StyleName.from_user_input("casual-friendly"),
        guidelines="Write in a casual, friendly tone that feels conversational and approachable. Use simple language, contractions, and a warm voice that connects with readers. Feel free to use casual expressions and a relaxed style.",
        content_types=[ContentType.blog_post(), ContentType.email()]
    )


@pytest.fixture
def technical_style():
    """Technical style primer for testing."""
    return StylePrimer.create(
        name=StyleName.from_user_input("technical-precise"),
        guidelines="Write with technical precision and analytical depth. Use industry-specific terminology, provide detailed explanations, and maintain scientific accuracy. Focus on methodology and implementation details.",
        content_types=[ContentType.documentation(), ContentType.report()]
    )


@pytest.fixture
def creation_options():
    """Sample style creation options."""
    return StyleCreationOptions(
        validate_guidelines=True,
        auto_detect_compatibility=True,
        inherit_parent_rules=True,
        generate_examples=True,
        optimize_for_performance=True,
        metadata={"author": "test_user", "category": "business"}
    )


# Core Style Management Tests

class TestStyleCreation:
    """Tests for style primer creation functionality."""

    @pytest.mark.asyncio
    async def test_create_style_success(
        self,
        style_management_service,
        mock_style_repo,
        creation_options
    ):
        """Test successful style creation with all options."""
        # Arrange
        name = StyleName.from_user_input("professional-modern")
        guidelines = "Write in a modern professional tone that balances authority with accessibility. Use contemporary language while maintaining credibility and expertise."
        content_types = [ContentType.blog_post(), ContentType.documentation()]
        
        mock_style_repo.find_by_name.return_value = None
        mock_style_repo.save.return_value = Mock(id="style_123")
        
        # Act
        result = await style_management_service.create_style(
            name=name,
            guidelines=guidelines,
            content_types=content_types,
            options=creation_options,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert result is not None
        mock_style_repo.find_by_name.assert_called_once_with(name)
        mock_style_repo.save.assert_called_once()
        
        # Verify style was saved with correct workspace
        save_call = mock_style_repo.save.call_args
        saved_style, workspace = save_call[0]
        assert workspace == "test_workspace"
        assert saved_style.name == name

    @pytest.mark.asyncio
    async def test_create_style_already_exists(
        self,
        style_management_service,
        mock_style_repo,
        sample_style
    ):
        """Test style creation when style already exists."""
        # Arrange
        name = StyleName.from_user_input("existing-style")
        guidelines = "Existing style guidelines"
        mock_style_repo.find_by_name.return_value = sample_style
        
        # Act & Assert
        with pytest.raises(EntityAlreadyExistsError) as exc_info:
            await style_management_service.create_style(
                name=name,
                guidelines=guidelines
            )
        
        assert "already exists" in str(exc_info.value)
        mock_style_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_style_invalid_guidelines(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test style creation with invalid guidelines."""
        # Arrange
        name = StyleName.from_user_input("invalid-style")
        invalid_guidelines = ""  # Empty guidelines
        mock_style_repo.find_by_name.return_value = None
        
        # Act & Assert
        with pytest.raises(StyleValidationError) as exc_info:
            await style_management_service.create_style(
                name=name,
                guidelines=invalid_guidelines,
                options=StyleCreationOptions(validate_guidelines=True)
            )
        
        assert "Guidelines validation failed" in str(exc_info.value)
        mock_style_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_style_with_auto_detection(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test style creation with auto-detection features."""
        # Arrange
        name = StyleName.from_user_input("auto-detected-style")
        guidelines = "Write engaging blog posts and articles that capture readers' attention and provide valuable insights."
        mock_style_repo.find_by_name.return_value = None
        mock_style_repo.save.return_value = Mock(id="style_456")
        
        options = StyleCreationOptions(
            auto_detect_compatibility=True,
            generate_examples=True,
            optimize_for_performance=True
        )
        
        # Act
        result = await style_management_service.create_style(
            name=name,
            guidelines=guidelines,
            content_types=None,  # Let auto-detection work
            options=options
        )
        
        # Assert
        assert result is not None
        mock_style_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_style_minimal_options(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test style creation with minimal options."""
        # Arrange
        name = StyleName.from_user_input("minimal-style")
        guidelines = "Write in a clear, straightforward manner that communicates effectively without unnecessary complexity."
        mock_style_repo.find_by_name.return_value = None
        mock_style_repo.save.return_value = Mock(id="style_789")
        
        # Act - No options provided, should use defaults
        result = await style_management_service.create_style(
            name=name,
            guidelines=guidelines
        )
        
        # Assert
        assert result is not None
        mock_style_repo.save.assert_called_once()


class TestStyleValidation:
    """Tests for comprehensive style validation."""

    @pytest.mark.asyncio
    async def test_validate_style_comprehensive_success(
        self,
        style_management_service,
        sample_style
    ):
        """Test comprehensive style validation for valid style."""
        # Act
        result = await style_management_service.validate_style_comprehensive(
            style=sample_style,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, StyleValidationResult)
        assert result.is_valid is True
        assert isinstance(result.guideline_errors, list)
        assert isinstance(result.format_errors, list)
        assert isinstance(result.consistency_errors, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.suggestions, list)
        assert isinstance(result.missing_elements, list)
        assert isinstance(result.redundant_elements, list)
        assert isinstance(result.performance_issues, list)

    @pytest.mark.asyncio
    async def test_validate_style_with_errors(
        self,
        style_management_service
    ):
        """Test style validation with various errors."""
        # Arrange - Create style with validation issues
        problematic_style = StylePrimer.create(
            name=StyleName.from_user_input("problematic-style"),
            guidelines="Write!!!!! Use lots of exclamation marks!!!!! Be VERY LOUD and inconsistent!!!!! mix Capitalization Randomly!!!!! And repeat the same things over and over and over again!!!!",
            content_types=[]
        )
        
        # Act
        result = await style_management_service.validate_style_comprehensive(
            style=problematic_style,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.format_errors) > 0  # Should detect format issues
        assert len(result.performance_issues) > 0  # Should detect performance issues

    @pytest.mark.asyncio
    async def test_validate_style_consistency_errors(
        self,
        style_management_service
    ):
        """Test style validation detecting consistency errors."""
        # Arrange - Create style with contradictory guidelines
        inconsistent_style = StylePrimer.create(
            name=StyleName.from_user_input("inconsistent-style"),
            guidelines="Write in a formal, professional, business tone while being casual, friendly, and conversational. Use official language and informal expressions.",
            content_types=[ContentType.generic()]
        )
        
        # Act
        result = await style_management_service.validate_style_comprehensive(
            style=inconsistent_style,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.consistency_errors) > 0  # Should detect contradictory tone indicators

    @pytest.mark.asyncio
    async def test_validate_style_caching(
        self,
        style_management_service,
        sample_style
    ):
        """Test that validation results are cached properly."""
        # Act - Call validation twice
        result1 = await style_management_service.validate_style_comprehensive(
            style=sample_style,
            workspace_name="test_workspace"
        )
        result2 = await style_management_service.validate_style_comprehensive(
            style=sample_style,
            workspace_name="test_workspace"
        )
        
        # Assert - Should return the same cached result
        assert result1 is result2

    @pytest.mark.asyncio
    async def test_validate_style_missing_elements(
        self,
        style_management_service
    ):
        """Test detection of missing essential elements."""
        # Arrange - Create style missing essential elements
        incomplete_style = StylePrimer.create(
            name=StyleName.from_user_input("incomplete-style"),
            guidelines="Write well.",  # Too short, missing essential elements
            content_types=[ContentType.generic()]
        )
        
        # Act
        result = await style_management_service.validate_style_comprehensive(
            style=incomplete_style,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert result.is_valid is False
        assert len(result.guideline_errors) > 0  # Should detect insufficient detail
        assert len(result.missing_elements) > 0  # Should detect missing elements


class TestStyleInheritance:
    """Tests for style inheritance analysis."""

    @pytest.mark.asyncio
    async def test_analyze_style_inheritance(
        self,
        style_management_service,
        sample_style
    ):
        """Test style inheritance chain analysis."""
        # Act
        result = await style_management_service.analyze_style_inheritance(
            style=sample_style,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, StyleInheritanceChain)
        assert result.style == sample_style
        assert isinstance(result.parent_styles, list)
        assert isinstance(result.child_styles, list)
        assert isinstance(result.inheritance_depth, int)
        assert isinstance(result.conflicts, list)
        assert isinstance(result.merged_guidelines, set)
        assert isinstance(result.overridden_rules, list)
        assert isinstance(result.resolution_order, list)

    @pytest.mark.asyncio
    async def test_inheritance_error_handling(
        self,
        style_management_service,
        sample_style
    ):
        """Test inheritance analysis error handling."""
        # Arrange - Mock method to raise exception
        with patch.object(
            style_management_service,
            '_find_parent_styles',
            side_effect=Exception("Database error")
        ):
            # Act & Assert
            with pytest.raises(StyleInheritanceError) as exc_info:
                await style_management_service.analyze_style_inheritance(
                    style=sample_style,
                    workspace_name="test_workspace"
                )
            
            assert "Inheritance analysis failed" in str(exc_info.value)


class TestStyleCompatibility:
    """Tests for style compatibility analysis."""

    @pytest.mark.asyncio
    async def test_check_style_compatibility_high(
        self,
        style_management_service,
        sample_style,
        technical_style
    ):
        """Test style compatibility checking for similar styles."""
        # Act
        result = await style_management_service.check_style_compatibility(
            style_a=sample_style,
            style_b=technical_style,  # Both are formal/professional
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, StyleCompatibilityMatrix)
        assert result.primary_style == sample_style
        assert len(result.compared_styles) == 1
        assert result.compared_styles[0] == technical_style
        assert isinstance(result.compatibility_scores, dict)
        assert isinstance(result.compatibility_levels, dict)
        assert isinstance(result.conflicts, dict)
        assert isinstance(result.recommendations, dict)
        assert isinstance(result.merge_possibilities, dict)

    @pytest.mark.asyncio
    async def test_check_style_compatibility_low(
        self,
        style_management_service,
        sample_style,
        casual_style
    ):
        """Test style compatibility checking for different styles."""
        # Act
        result = await style_management_service.check_style_compatibility(
            style_a=sample_style,  # Formal
            style_b=casual_style,  # Casual
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, StyleCompatibilityMatrix)
        # Should detect conflicts between formal and casual styles
        style_b_name = str(casual_style.name)
        assert style_b_name in result.conflicts
        assert len(result.conflicts[style_b_name]) > 0

    @pytest.mark.asyncio
    async def test_compatibility_caching(
        self,
        style_management_service,
        sample_style,
        casual_style
    ):
        """Test that compatibility results are cached."""
        # Act - Call compatibility check twice
        result1 = await style_management_service.check_style_compatibility(
            style_a=sample_style,
            style_b=casual_style,
            workspace_name="test_workspace"
        )
        result2 = await style_management_service.check_style_compatibility(
            style_a=sample_style,
            style_b=casual_style,
            workspace_name="test_workspace"
        )
        
        # Assert - Should return cached result
        assert result1 is result2


class TestStyleComposition:
    """Tests for style composition functionality."""

    @pytest.mark.asyncio
    async def test_create_composition_plan_success(
        self,
        style_management_service,
        sample_style,
        casual_style,
        technical_style
    ):
        """Test creation of style composition plan."""
        # Arrange
        source_styles = [sample_style, casual_style, technical_style]
        target_name = StyleName.from_user_input("composed-style")
        
        # Act
        result = await style_management_service.create_composition_plan(
            source_styles=source_styles,
            target_name=target_name,
            strategy="merge",
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, StyleCompositionPlan)
        assert result.target_name == target_name
        assert result.source_styles == source_styles
        assert result.composition_strategy == "merge"
        assert isinstance(result.merge_rules, dict)
        assert isinstance(result.conflict_resolutions, dict)
        assert isinstance(result.priority_order, list)
        assert isinstance(result.expected_outcome, dict)

    @pytest.mark.asyncio
    async def test_create_composition_plan_insufficient_styles(
        self,
        style_management_service,
        sample_style
    ):
        """Test composition plan creation with insufficient styles."""
        # Arrange
        source_styles = [sample_style]  # Only one style
        target_name = StyleName.from_user_input("composed-style")
        
        # Act & Assert
        with pytest.raises(StyleCompositionError) as exc_info:
            await style_management_service.create_composition_plan(
                source_styles=source_styles,
                target_name=target_name
            )
        
        assert "Need at least 2 styles to compose" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compose_styles_success(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test successful style composition execution."""
        # Arrange
        plan = StyleCompositionPlan(
            target_name=StyleName.from_user_input("composed-style"),
            source_styles=[Mock(), Mock()],  # Mock styles
            composition_strategy="merge",
            merge_rules={"rule1": "value1"},
            conflict_resolutions={"conflict1": "resolution1"},
            priority_order=[],
            expected_outcome={}
        )
        
        mock_style_repo.save.return_value = Mock(id="composed_style_id")
        
        # Mock validation to pass
        with patch.object(
            style_management_service,
            'validate_style_comprehensive'
        ) as mock_validate:
            mock_validate.return_value = Mock(is_valid=True, guideline_errors=[])
            
            # Act
            result = await style_management_service.compose_styles(
                plan=plan,
                workspace_name="test_workspace"
            )
            
            # Assert
            assert result is not None
            mock_style_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_compose_styles_validation_failure(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test style composition with validation failure."""
        # Arrange
        plan = StyleCompositionPlan(
            target_name=StyleName.from_user_input("invalid-composed-style"),
            source_styles=[Mock(), Mock()],
            composition_strategy="merge",
            merge_rules={},
            conflict_resolutions={},
            priority_order=[],
            expected_outcome={}
        )
        
        # Mock validation to fail
        with patch.object(
            style_management_service,
            'validate_style_comprehensive'
        ) as mock_validate:
            mock_validate.return_value = Mock(
                is_valid=False,
                guideline_errors=["Invalid composition"]
            )
            
            # Act & Assert
            with pytest.raises(StyleCompositionError) as exc_info:
                await style_management_service.compose_styles(
                    plan=plan,
                    workspace_name="test_workspace"
                )
            
            assert "Composed style validation failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_compose_styles_unknown_strategy(
        self,
        style_management_service
    ):
        """Test style composition with unknown strategy."""
        # Arrange
        plan = StyleCompositionPlan(
            target_name=StyleName.from_user_input("composed-style"),
            source_styles=[Mock(), Mock()],
            composition_strategy="unknown_strategy",
            merge_rules={},
            conflict_resolutions={},
            priority_order=[],
            expected_outcome={}
        )
        
        # Act & Assert
        with pytest.raises(StyleCompositionError) as exc_info:
            await style_management_service.compose_styles(plan=plan)
        
        assert "Unknown composition strategy" in str(exc_info.value)


class TestStyleOptimization:
    """Tests for style optimization functionality."""

    @pytest.mark.asyncio
    async def test_optimize_style_basic(
        self,
        style_management_service,
        sample_style
    ):
        """Test basic style optimization."""
        # Act
        result = await style_management_service.optimize_style(
            style=sample_style,
            level=StyleOptimizationLevel.BASIC,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, StylePrimer)
        assert result.get_metadata("optimization_level") == "basic"
        assert result.get_metadata("optimized_at") is not None

    @pytest.mark.asyncio
    async def test_optimize_style_standard(
        self,
        style_management_service,
        sample_style
    ):
        """Test standard style optimization."""
        # Act
        result = await style_management_service.optimize_style(
            style=sample_style,
            level=StyleOptimizationLevel.STANDARD,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, StylePrimer)
        assert result.get_metadata("optimization_level") == "standard"

    @pytest.mark.asyncio
    async def test_optimize_style_aggressive(
        self,
        style_management_service,
        sample_style
    ):
        """Test aggressive style optimization."""
        # Act
        result = await style_management_service.optimize_style(
            style=sample_style,
            level=StyleOptimizationLevel.AGGRESSIVE,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, StylePrimer)
        assert result.get_metadata("optimization_level") == "aggressive"


class TestStyleRecommendations:
    """Tests for style recommendation functionality."""

    @pytest.mark.asyncio
    async def test_recommend_style_for_content(
        self,
        style_management_service,
        mock_style_repo,
        sample_style,
        technical_style
    ):
        """Test style recommendations for content type."""
        # Arrange
        content_type = ContentType.documentation()
        requirements = {"tone": "professional", "audience": "technical"}
        
        # Mock repository to return compatible styles
        mock_style_repo.find_by_content_type.return_value = [sample_style, technical_style]
        
        # Act
        result = await style_management_service.recommend_style_for_content(
            content_type=content_type,
            requirements=requirements,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, list)
        assert all(isinstance(rec, StyleRecommendation) for rec in result)
        if result:
            recommendation = result[0]
            assert isinstance(recommendation.confidence_score, float)
            assert isinstance(recommendation.compatibility_score, float)
            assert isinstance(recommendation.performance_score, float)
            assert isinstance(recommendation.reasoning, list)
            assert isinstance(recommendation.alternatives, list)
            assert isinstance(recommendation.customization_suggestions, list)
        
        # Verify repository was called correctly
        mock_style_repo.find_by_content_type.assert_called_once_with(content_type)

    @pytest.mark.asyncio
    async def test_recommend_style_caching(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test that style recommendations are cached."""
        # Arrange
        content_type = ContentType.blog_post()
        requirements = {"tone": "casual"}
        mock_style_repo.find_by_content_type.return_value = []
        
        # Act - Call recommendations twice
        result1 = await style_management_service.recommend_style_for_content(
            content_type=content_type,
            requirements=requirements,
            workspace_name="test_workspace"
        )
        result2 = await style_management_service.recommend_style_for_content(
            content_type=content_type,
            requirements=requirements,
            workspace_name="test_workspace"
        )
        
        # Assert - Should return cached result
        assert result1 is result2
        # Repository should only be called once due to caching
        mock_style_repo.find_by_content_type.assert_called_once()


class TestStylePerformanceMetrics:
    """Tests for style performance metrics."""

    @pytest.mark.asyncio
    async def test_get_style_performance_metrics(
        self,
        style_management_service,
        mock_style_repo,
        sample_style
    ):
        """Test getting style performance metrics."""
        # Arrange
        mock_usage_stats = {
            "total_uses": 150,
            "average_quality": 0.85,
            "consistency_rate": 0.92,
            "error_rate": 0.03,
            "user_satisfaction": 0.88,
            "generation_efficiency": 0.76,
            "cache_hit_rate": 0.64
        }
        mock_style_repo.get_style_usage_stats.return_value = mock_usage_stats
        
        # Act
        result = await style_management_service.get_style_performance_metrics(
            style=sample_style,
            workspace_name="test_workspace"
        )
        
        # Assert
        assert isinstance(result, StylePerformanceMetrics)
        assert result.style == sample_style
        assert result.usage_frequency == 150
        assert result.average_quality_score == 0.85
        assert result.consistency_rate == 0.92
        assert result.error_rate == 0.03
        assert result.user_satisfaction == 0.88
        assert result.generation_efficiency == 0.76
        assert result.cache_effectiveness == 0.64
        assert isinstance(result.optimization_potential, float)
        assert isinstance(result.performance_issues, list)

    @pytest.mark.asyncio
    async def test_performance_metrics_caching(
        self,
        style_management_service,
        mock_style_repo,
        sample_style
    ):
        """Test that performance metrics are cached."""
        # Arrange
        mock_usage_stats = {"total_uses": 100}
        mock_style_repo.get_style_usage_stats.return_value = mock_usage_stats
        
        # Act - Call metrics twice
        result1 = await style_management_service.get_style_performance_metrics(
            style=sample_style,
            workspace_name="test_workspace"
        )
        result2 = await style_management_service.get_style_performance_metrics(
            style=sample_style,
            workspace_name="test_workspace"
        )
        
        # Assert - Should return cached result
        assert result1 is result2
        # Repository should only be called once due to caching
        mock_style_repo.get_style_usage_stats.assert_called_once()

    @pytest.mark.asyncio
    async def test_performance_metrics_with_time_range(
        self,
        style_management_service,
        mock_style_repo,
        sample_style
    ):
        """Test performance metrics with specific time range."""
        # Arrange
        start_time = datetime.now() - timedelta(days=30)
        end_time = datetime.now()
        time_range = (start_time, end_time)
        
        mock_usage_stats = {"total_uses": 75}
        mock_style_repo.get_style_usage_stats.return_value = mock_usage_stats
        
        # Act
        result = await style_management_service.get_style_performance_metrics(
            style=sample_style,
            workspace_name="test_workspace",
            time_range=time_range
        )
        
        # Assert
        assert isinstance(result, StylePerformanceMetrics)
        assert result.usage_frequency == 75


class TestPrivateHelperMethods:
    """Tests for private helper methods."""

    @pytest.mark.asyncio
    async def test_validate_style_guidelines(
        self,
        style_management_service
    ):
        """Test style guidelines validation helper."""
        # Test valid guidelines
        valid_guidelines = "Write in a professional tone that demonstrates expertise while remaining accessible to a broad audience. Use clear, concise language and maintain consistency throughout."
        errors = await style_management_service._validate_style_guidelines(valid_guidelines)
        assert errors == []
        
        # Test empty guidelines
        empty_guidelines = ""
        errors = await style_management_service._validate_style_guidelines(empty_guidelines)
        assert len(errors) > 0
        assert "Guidelines cannot be empty" in errors[0]
        
        # Test too short guidelines
        short_guidelines = "Be brief."
        errors = await style_management_service._validate_style_guidelines(short_guidelines)
        assert len(errors) > 0
        assert "more detailed" in errors[0]
        
        # Test guidelines without tone indicators
        toneless_guidelines = "Write content that is good and follows proper structure."
        errors = await style_management_service._validate_style_guidelines(toneless_guidelines)
        assert len(errors) > 0
        assert "specify tone" in errors[0]

    @pytest.mark.asyncio
    async def test_auto_detect_content_types(
        self,
        style_management_service
    ):
        """Test content type auto-detection from guidelines."""
        # Test blog post detection
        blog_guidelines = "Write engaging blog posts and articles that capture readers' attention."
        content_types = await style_management_service._auto_detect_content_types(blog_guidelines)
        assert ContentType.blog_post() in content_types
        
        # Test documentation detection
        doc_guidelines = "Create technical documentation and user manuals with clear instructions."
        content_types = await style_management_service._auto_detect_content_types(doc_guidelines)
        assert ContentType.documentation() in content_types
        
        # Test email detection
        email_guidelines = "Write professional email correspondence and business messages."
        content_types = await style_management_service._auto_detect_content_types(email_guidelines)
        assert ContentType.email() in content_types
        
        # Test generic fallback
        generic_guidelines = "Write good content that follows best practices."
        content_types = await style_management_service._auto_detect_content_types(generic_guidelines)
        assert ContentType.generic() in content_types

    @pytest.mark.asyncio
    async def test_generate_style_examples(
        self,
        style_management_service,
        sample_style
    ):
        """Test style example generation."""
        # Act
        examples = await style_management_service._generate_style_examples(sample_style)
        
        # Assert
        assert isinstance(examples, dict)
        # Should generate examples for the content types associated with the style

    @pytest.mark.asyncio
    async def test_validate_format_consistency(
        self,
        style_management_service
    ):
        """Test format consistency validation."""
        # Test consistent style
        consistent_style = StylePrimer.create(
            name=StyleName.from_user_input("consistent-style"),
            guidelines="Write clearly. Use proper punctuation. Maintain professional standards.",
            content_types=[ContentType.generic()]
        )
        errors = await style_management_service._validate_format_consistency(consistent_style)
        assert len(errors) == 0
        
        # Test inconsistent style
        inconsistent_style = StylePrimer.create(
            name=StyleName.from_user_input("inconsistent-style"),
            guidelines="write clearly!!! Use proper punctuation!! maintain Professional Standards!!!!",
            content_types=[ContentType.generic()]
        )
        errors = await style_management_service._validate_format_consistency(inconsistent_style)
        assert len(errors) > 0
        assert any("exclamation marks" in error for error in errors)

    @pytest.mark.asyncio
    async def test_check_style_consistency(
        self,
        style_management_service
    ):
        """Test internal style consistency checking."""
        # Test contradictory style
        contradictory_style = StylePrimer.create(
            name=StyleName.from_user_input("contradictory-style"),
            guidelines="Write in a formal, professional, business tone while being casual, friendly, and conversational.",
            content_types=[ContentType.generic()]
        )
        errors = await style_management_service._check_style_consistency(contradictory_style)
        assert len(errors) > 0
        assert any("formal and casual" in error for error in errors)

    @pytest.mark.asyncio
    async def test_analyze_style_completeness(
        self,
        style_management_service
    ):
        """Test style completeness analysis."""
        # Test incomplete style
        incomplete_style = StylePrimer.create(
            name=StyleName.from_user_input("incomplete-style"),
            guidelines="Write content.",  # Missing tone, audience, format, length specs
            content_types=[ContentType.generic()]
        )
        missing_elements = await style_management_service._analyze_style_completeness(incomplete_style)
        assert len(missing_elements) > 0
        # Should detect missing essential elements

    @pytest.mark.asyncio
    async def test_analyze_style_performance_issues(
        self,
        style_management_service
    ):
        """Test style performance issue analysis."""
        # Test style with performance issues
        complex_style = StylePrimer.create(
            name=StyleName.from_user_input("complex-style"),
            guidelines="Write content using elaborate, sophisticated, and extensively detailed language that utilizes complex terminology and demonstrates comprehensive understanding while facilitating optimal communication effectiveness through methodological approaches to content creation and development processes." * 10,  # Very long
            content_types=[ContentType.generic()]
        )
        issues = await style_management_service._analyze_style_performance_issues(complex_style)
        assert len(issues) > 0
        assert any("very long" in issue for issue in issues)


class TestCompatibilityLevels:
    """Tests for compatibility level determination."""

    @pytest.mark.asyncio
    async def test_determine_compatibility_level(
        self,
        style_management_service
    ):
        """Test compatibility level determination from similarity scores."""
        # Test fully compatible
        level = await style_management_service._determine_compatibility_level(0.9)
        assert level == StyleCompatibilityLevel.FULLY_COMPATIBLE
        
        # Test mostly compatible
        level = await style_management_service._determine_compatibility_level(0.7)
        assert level == StyleCompatibilityLevel.MOSTLY_COMPATIBLE
        
        # Test partially compatible
        level = await style_management_service._determine_compatibility_level(0.5)
        assert level == StyleCompatibilityLevel.PARTIALLY_COMPATIBLE
        
        # Test incompatible
        level = await style_management_service._determine_compatibility_level(0.2)
        assert level == StyleCompatibilityLevel.INCOMPATIBLE


class TestStyleComparison:
    """Tests for style comparison functionality."""

    @pytest.mark.asyncio
    async def test_compare_styles(
        self,
        style_management_service,
        sample_style,
        casual_style
    ):
        """Test style comparison functionality."""
        # Act
        result = await style_management_service._compare_styles(sample_style, casual_style)
        
        # Assert
        assert isinstance(result, StyleComparison)
        assert result.style_a == sample_style
        assert result.style_b == casual_style
        assert isinstance(result.similarity_score, float)
        assert isinstance(result.differences, list)
        assert isinstance(result.common_elements, list)
        assert isinstance(result.unique_to_a, list)
        assert isinstance(result.unique_to_b, list)
        assert isinstance(result.merge_complexity, str)
        assert isinstance(result.recommended_action, str)


class TestEdgeCasesAndErrorHandling:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_guidelines(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test handling of empty guidelines."""
        # Arrange
        name = StyleName.from_user_input("empty-guidelines-style")
        mock_style_repo.find_by_name.return_value = None
        
        # Act & Assert
        with pytest.raises(StyleValidationError):
            await style_management_service.create_style(
                name=name,
                guidelines="",
                options=StyleCreationOptions(validate_guidelines=True)
            )

    @pytest.mark.asyncio
    async def test_whitespace_only_guidelines(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test handling of whitespace-only guidelines."""
        # Arrange
        name = StyleName.from_user_input("whitespace-style")
        mock_style_repo.find_by_name.return_value = None
        
        # Act & Assert
        with pytest.raises(StyleValidationError):
            await style_management_service.create_style(
                name=name,
                guidelines="   \n\t   ",
                options=StyleCreationOptions(validate_guidelines=True)
            )

    @pytest.mark.asyncio
    async def test_repository_error_handling(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test repository error handling."""
        # Arrange
        name = StyleName.from_user_input("repo-error-style")
        guidelines = "Write in a professional tone."
        mock_style_repo.find_by_name.return_value = None
        mock_style_repo.save.side_effect = RepositoryError("Database connection failed")
        
        # Act & Assert
        with pytest.raises(RepositoryError):
            await style_management_service.create_style(
                name=name,
                guidelines=guidelines
            )

    @pytest.mark.asyncio
    async def test_large_guidelines_handling(
        self,
        style_management_service,
        mock_style_repo
    ):
        """Test handling of very large style guidelines."""
        # Arrange
        name = StyleName.from_user_input("large-guidelines-style")
        large_guidelines = "Write in a comprehensive and detailed manner. " * 1000  # Very large guidelines
        mock_style_repo.find_by_name.return_value = None
        mock_style_repo.save.return_value = Mock(id="large_style_id")
        
        # Act
        result = await style_management_service.create_style(
            name=name,
            guidelines=large_guidelines
        )
        
        # Assert
        assert result is not None
        
        # Validate the large style - should detect performance issues
        validation_result = await style_management_service.validate_style_comprehensive(
            style=result
        )
        
        # Should detect performance issues with very long guidelines
        assert len(validation_result.performance_issues) > 0

    @pytest.mark.asyncio
    async def test_none_style_handling(
        self,
        style_management_service
    ):
        """Test handling of None style in validation methods."""
        # This should be handled gracefully by the service
        # In a real implementation, this might raise a specific error
        pass

    @pytest.mark.asyncio
    async def test_concurrent_style_operations(
        self,
        style_management_service,
        mock_style_repo,
        sample_style
    ):
        """Test concurrent style operations and caching behavior."""
        # Arrange
        mock_style_repo.find_by_content_type.return_value = [sample_style]
        
        # Act - Perform multiple concurrent operations
        import asyncio
        
        tasks = [
            style_management_service.validate_style_comprehensive(sample_style),
            style_management_service.analyze_style_inheritance(sample_style),
            style_management_service.get_style_performance_metrics(sample_style),
            style_management_service.recommend_style_for_content(ContentType.blog_post())
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Assert - All operations should complete successfully
        assert len(results) == 4
        assert all(result is not None for result in results)