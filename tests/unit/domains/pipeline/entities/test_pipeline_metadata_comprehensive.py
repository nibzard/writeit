"""Comprehensive unit tests for Pipeline Metadata entities.

Tests entity behavior, statistics calculations, and business rules for
PipelineMetadata and PipelineUsageStats domain entities.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from src.writeit.domains.pipeline.entities.pipeline_metadata import (
    PipelineMetadata,
    PipelineUsageStats,
    PipelineCategory,
    PipelineComplexity,
    PipelineStatus
)
from src.writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from src.writeit.domains.pipeline.value_objects.pipeline_name import PipelineName

from tests.builders.pipeline_builders import (
    PipelineMetadataBuilder, PipelineUsageStatsBuilder
)


class TestPipelineUsageStats:
    """Test cases for PipelineUsageStats entity."""
    
    def test_usage_stats_creation_with_defaults(self):
        """Test creating usage stats with default values."""
        stats = PipelineUsageStats()
        
        assert stats.total_runs == 0
        assert stats.successful_runs == 0
        assert stats.failed_runs == 0
        assert stats.average_execution_time == 0.0
        assert stats.total_tokens_used == 0
        assert stats.last_run_at is None
        assert stats.success_rate == 0.0
        assert stats.failure_rate == 0.0
    
    def test_usage_stats_creation_with_values(self):
        """Test creating usage stats with specific values."""
        last_run = datetime.now()
        stats = PipelineUsageStats(
            total_runs=100,
            successful_runs=85,
            failed_runs=15,
            average_execution_time=45.5,
            total_tokens_used=50000,
            last_run_at=last_run
        )
        
        assert stats.total_runs == 100
        assert stats.successful_runs == 85
        assert stats.failed_runs == 15
        assert stats.average_execution_time == 45.5
        assert stats.total_tokens_used == 50000
        assert stats.last_run_at == last_run
        assert stats.success_rate == 85.0
        assert stats.failure_rate == 15.0
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        # Zero runs
        stats_zero = PipelineUsageStats()
        assert stats_zero.success_rate == 0.0
        
        # Perfect success
        stats_perfect = PipelineUsageStats(total_runs=10, successful_runs=10)
        assert stats_perfect.success_rate == 100.0
        
        # Partial success
        stats_partial = PipelineUsageStats(total_runs=10, successful_runs=7)
        assert stats_partial.success_rate == 70.0
        
        # No success
        stats_none = PipelineUsageStats(total_runs=10, successful_runs=0)
        assert stats_none.success_rate == 0.0
    
    def test_failure_rate_calculation(self):
        """Test failure rate calculation."""
        # Zero runs
        stats_zero = PipelineUsageStats()
        assert stats_zero.failure_rate == 0.0
        
        # Perfect success (zero failures)
        stats_perfect = PipelineUsageStats(total_runs=10, successful_runs=10)
        assert stats_perfect.failure_rate == 0.0
        
        # Partial success
        stats_partial = PipelineUsageStats(total_runs=10, successful_runs=7)
        assert stats_partial.failure_rate == 30.0
        
        # All failures
        stats_all_fail = PipelineUsageStats(total_runs=10, successful_runs=0)
        assert stats_all_fail.failure_rate == 100.0
    
    def test_add_run_successful(self):
        """Test adding successful run to stats."""
        stats = PipelineUsageStats()
        
        # First run
        updated = stats.add_run(success=True, execution_time=30.0, tokens=1000)
        
        assert updated.total_runs == 1
        assert updated.successful_runs == 1
        assert updated.failed_runs == 0
        assert updated.average_execution_time == 30.0
        assert updated.total_tokens_used == 1000
        assert updated.last_run_at is not None
        assert updated.success_rate == 100.0
        
        # Second run
        second = updated.add_run(success=True, execution_time=60.0, tokens=2000)
        
        assert second.total_runs == 2
        assert second.successful_runs == 2
        assert second.failed_runs == 0
        assert second.average_execution_time == 45.0  # (30 + 60) / 2
        assert second.total_tokens_used == 3000
        assert second.success_rate == 100.0
    
    def test_add_run_failed(self):
        """Test adding failed run to stats."""
        stats = PipelineUsageStats()
        
        # First run - failed
        updated = stats.add_run(success=False, execution_time=15.0, tokens=500)
        
        assert updated.total_runs == 1
        assert updated.successful_runs == 0
        assert updated.failed_runs == 1
        assert updated.average_execution_time == 15.0
        assert updated.total_tokens_used == 500
        assert updated.success_rate == 0.0
        assert updated.failure_rate == 100.0
    
    def test_add_run_mixed_results(self):
        """Test adding runs with mixed success/failure."""
        stats = PipelineUsageStats()
        
        # Success
        stats = stats.add_run(success=True, execution_time=30.0, tokens=1000)
        # Failure
        stats = stats.add_run(success=False, execution_time=10.0, tokens=200)
        # Success
        stats = stats.add_run(success=True, execution_time=50.0, tokens=1500)
        
        assert stats.total_runs == 3
        assert stats.successful_runs == 2
        assert stats.failed_runs == 1
        assert stats.average_execution_time == 30.0  # (30 + 10 + 50) / 3
        assert stats.total_tokens_used == 2700
        assert stats.success_rate == pytest.approx(66.67, abs=0.01)
        assert stats.failure_rate == pytest.approx(33.33, abs=0.01)
    
    def test_usage_stats_immutability(self):
        """Test that add_run creates new instances."""
        original = PipelineUsageStats(total_runs=5, successful_runs=4)
        updated = original.add_run(success=True, execution_time=25.0, tokens=800)
        
        # Original unchanged
        assert original.total_runs == 5
        assert original.successful_runs == 4
        
        # Updated is different instance
        assert updated is not original
        assert updated.total_runs == 6
        assert updated.successful_runs == 5


class TestPipelineMetadata:
    """Test cases for PipelineMetadata entity."""
    
    def test_pipeline_metadata_creation_with_minimal_data(self):
        """Test creating pipeline metadata with minimal valid data."""
        metadata = PipelineMetadataBuilder.content_generation().build()
        
        assert isinstance(metadata.pipeline_id, PipelineId)
        assert isinstance(metadata.name, PipelineName)
        assert isinstance(metadata.category, PipelineCategory)
        assert isinstance(metadata.complexity, PipelineComplexity)
        assert isinstance(metadata.status, PipelineStatus)
        assert isinstance(metadata.usage_stats, PipelineUsageStats)
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)
        assert metadata.published_at is None
        assert metadata.deprecated_at is None
        assert isinstance(metadata.tags, list)
        assert isinstance(metadata.keywords, list)
        assert isinstance(metadata.requirements, list)
        assert isinstance(metadata.custom_metadata, dict)
    
    def test_pipeline_metadata_creation_with_all_fields(self):
        """Test creating pipeline metadata with all fields specified."""
        pipeline_id = PipelineId.from_name("comprehensive-test")
        name = PipelineName("Comprehensive Test Pipeline")
        tags = ["test", "comprehensive", "example"]
        keywords = ["testing", "validation", "comprehensive"]
        requirements = ["python>=3.8", "fastapi", "pydantic"]
        custom_metadata = {"custom_field": "custom_value"}
        
        metadata = (PipelineMetadataBuilder()
                   .with_pipeline_id(pipeline_id)
                   .with_name(name)
                   .with_version("2.1.0")
                   .with_category(PipelineCategory.UTILITY)
                   .with_complexity(PipelineComplexity.ADVANCED)
                   .with_status(PipelineStatus.EXPERIMENTAL)
                   .with_description("Comprehensive test pipeline description")
                   .with_author("Test Author")
                   .with_organization("Test Org")
                   .with_license("MIT")
                   .with_repository_url("https://github.com/test/repo")
                   .with_documentation_url("https://docs.test.com")
                   .with_tags(tags)
                   .with_keywords(keywords)
                   .with_requirements(requirements)
                   .with_custom_metadata(custom_metadata)
                   .build())
        
        assert metadata.pipeline_id == pipeline_id
        assert metadata.name == name
        assert metadata.version == "2.1.0"
        assert metadata.category == PipelineCategory.UTILITY
        assert metadata.complexity == PipelineComplexity.ADVANCED
        assert metadata.status == PipelineStatus.EXPERIMENTAL
        assert metadata.author == "Test Author"
        assert metadata.organization == "Test Org"
        assert metadata.license == "MIT"
        assert metadata.repository_url == "https://github.com/test/repo"
        assert metadata.documentation_url == "https://docs.test.com"
        assert metadata.tags == tags
        assert metadata.keywords == keywords
        assert metadata.requirements == requirements
        assert metadata.custom_metadata == custom_metadata
    
    def test_pipeline_metadata_invalid_types_raise_errors(self):
        """Test that invalid field types raise appropriate errors."""
        # Invalid pipeline_id
        with pytest.raises(TypeError, match="Pipeline id must be a PipelineId"):
            PipelineMetadata(
                pipeline_id="invalid",
                name=PipelineName("Test"),
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE
            )
        
        # Invalid name
        with pytest.raises(TypeError, match="Name must be a PipelineName"):
            PipelineMetadata(
                pipeline_id=PipelineId.from_name("test"),
                name="invalid",
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE
            )
        
        # Invalid category
        with pytest.raises(TypeError, match="Category must be a PipelineCategory"):
            PipelineMetadata(
                pipeline_id=PipelineId.from_name("test"),
                name=PipelineName("Test"),
                version="1.0.0",
                category="invalid",
                complexity=PipelineComplexity.SIMPLE
            )
        
        # Invalid complexity
        with pytest.raises(TypeError, match="Complexity must be a PipelineComplexity"):
            PipelineMetadata(
                pipeline_id=PipelineId.from_name("test"),
                name=PipelineName("Test"),
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity="invalid"
            )
        
        # Invalid status
        with pytest.raises(TypeError, match="Status must be a PipelineStatus"):
            PipelineMetadata(
                pipeline_id=PipelineId.from_name("test"),
                name=PipelineName("Test"),
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE,
                status="invalid"
            )
    
    def test_pipeline_metadata_validation_rules(self):
        """Test validation rules for pipeline metadata."""
        # Empty version
        with pytest.raises(ValueError, match="Version must be a non-empty string"):
            PipelineMetadata(
                pipeline_id=PipelineId.from_name("test"),
                name=PipelineName("Test"),
                version="",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE
            )
        
        # Invalid repository URL
        with pytest.raises(ValueError, match="Repository URL must be a valid URL"):
            PipelineMetadata(
                pipeline_id=PipelineId.from_name("test"),
                name=PipelineName("Test"),
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE,
                repository_url="invalid-url"
            )
        
        # Invalid documentation URL
        with pytest.raises(ValueError, match="Documentation URL must be a valid URL"):
            PipelineMetadata(
                pipeline_id=PipelineId.from_name("test"),
                name=PipelineName("Test"),
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE,
                documentation_url="invalid-url"
            )
        
        # Invalid tags type
        with pytest.raises(TypeError, match="Tags must be a list"):
            PipelineMetadata(
                pipeline_id=PipelineId.from_name("test"),
                name=PipelineName("Test"),
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE,
                tags="not-a-list"
            )
    
    def test_pipeline_metadata_status_properties(self):
        """Test status property methods."""
        # Active pipeline
        active = PipelineMetadataBuilder().with_status(PipelineStatus.ACTIVE).build()
        assert active.is_active is True
        assert active.is_deprecated is False
        assert active.is_experimental is False
        
        # Deprecated pipeline
        deprecated = (PipelineMetadataBuilder()
                     .with_status(PipelineStatus.DEPRECATED)
                     .with_deprecated_at(datetime.now())
                     .build())
        assert deprecated.is_active is False
        assert deprecated.is_deprecated is True
        assert deprecated.is_experimental is False
        
        # Experimental pipeline
        experimental = PipelineMetadataBuilder().with_status(PipelineStatus.EXPERIMENTAL).build()
        assert experimental.is_active is False
        assert experimental.is_deprecated is False
        assert experimental.is_experimental is True
        
        # Published pipeline
        published = (PipelineMetadataBuilder()
                    .with_published_at(datetime.now())
                    .build())
        assert published.is_published is True
        
        # Not published pipeline
        not_published = PipelineMetadataBuilder().build()
        assert not_published.is_published is False
    
    def test_pipeline_metadata_age_calculation(self):
        """Test age calculation properties."""
        # Recent pipeline
        recent_time = datetime.now() - timedelta(days=5)
        recent = (PipelineMetadataBuilder()
                 .with_created_at(recent_time)
                 .with_updated_at(recent_time)
                 .build())
        assert recent.age_days == 5
        assert recent.days_since_update == 5
        
        # Older pipeline
        old_time = datetime.now() - timedelta(days=30)
        updated_time = datetime.now() - timedelta(days=10)
        old = (PipelineMetadataBuilder()
              .with_created_at(old_time)
              .with_updated_at(updated_time)
              .build())
        assert old.age_days == 30
        assert old.days_since_update == 10
    
    def test_pipeline_metadata_popularity_score(self):
        """Test popularity score calculation."""
        # High usage, high success, recent
        high_usage = PipelineUsageStats(
            total_runs=150,  # Capped at 100 for base score
            successful_runs=140,  # 93.33% success rate
            failed_runs=10
        )
        recent_time = datetime.now() - timedelta(days=5)
        popular = (PipelineMetadataBuilder()
                  .with_usage_stats(high_usage)
                  .with_updated_at(recent_time)
                  .build())
        
        # Base: 100, Success bonus: ~9.3, Recency bonus: ~8.3
        expected_score = 100 + (93.33 / 10) + ((30 - 5) / 3)
        assert popular.popularity_score == pytest.approx(expected_score, abs=0.1)
        
        # Low usage, low success, old
        low_usage = PipelineUsageStats(
            total_runs=5,
            successful_runs=2,
            failed_runs=3
        )
        old_time = datetime.now() - timedelta(days=60)
        unpopular = (PipelineMetadataBuilder()
                    .with_usage_stats(low_usage)
                    .with_updated_at(old_time)
                    .build())
        
        # Base: 5, Success bonus: 4, Recency bonus: 0
        expected_low_score = 5 + (40.0 / 10) + 0
        assert unpopular.popularity_score == pytest.approx(expected_low_score, abs=0.1)
    
    def test_pipeline_metadata_tag_and_keyword_checks(self):
        """Test tag and keyword checking methods."""
        metadata = (PipelineMetadataBuilder()
                   .with_tags(["Content", "Generation", "AI"])
                   .with_keywords(["writing", "articles", "blog"])
                   .build())
        
        # Tag checks (case-insensitive)
        assert metadata.has_tag("content") is True
        assert metadata.has_tag("GENERATION") is True
        assert metadata.has_tag("nonexistent") is False
        
        # Keyword checks (case-insensitive)
        assert metadata.has_keyword("writing") is True
        assert metadata.has_keyword("ARTICLES") is True
        assert metadata.has_keyword("nonexistent") is False
    
    def test_pipeline_metadata_category_and_complexity_matching(self):
        """Test category and complexity matching."""
        metadata = (PipelineMetadataBuilder()
                   .with_category(PipelineCategory.CONTENT_GENERATION)
                   .with_complexity(PipelineComplexity.MODERATE)
                   .build())
        
        assert metadata.matches_category(PipelineCategory.CONTENT_GENERATION) is True
        assert metadata.matches_category(PipelineCategory.CODE_GENERATION) is False
        
        assert metadata.matches_complexity(PipelineComplexity.MODERATE) is True
        assert metadata.matches_complexity(PipelineComplexity.COMPLEX) is False
    
    def test_pipeline_metadata_search_relevance(self):
        """Test search relevance scoring."""
        metadata = (PipelineMetadataBuilder()
                   .with_name(PipelineName("Article Generator"))
                   .with_description("Generate high-quality articles with AI")
                   .with_tags(["content", "writing", "article"])
                   .with_keywords(["blog", "writing", "content"])
                   .with_category(PipelineCategory.CONTENT_GENERATION)
                   .build())
        
        # Name match (highest score)
        assert metadata.search_relevance("article") >= 0.4
        
        # Description match
        assert metadata.search_relevance("quality") >= 0.2
        
        # Tag match
        assert metadata.search_relevance("writing") >= 0.2
        
        # Keyword match
        assert metadata.search_relevance("blog") >= 0.15
        
        # Category match
        assert metadata.search_relevance("content_generation") >= 0.05
        
        # Multiple matches should accumulate (but cap at 1.0)
        combined_score = metadata.search_relevance("content")
        assert combined_score > 0.4  # Should match multiple criteria
        
        # No match
        assert metadata.search_relevance("nonexistent") == 0.0
    
    def test_pipeline_metadata_version_update(self):
        """Test version update functionality."""
        original = PipelineMetadataBuilder().with_version("1.0.0").build()
        original_updated_at = original.updated_at
        
        # Simple version update
        updated = original.update_version("1.1.0")
        
        assert updated.version == "1.1.0"
        assert updated.updated_at > original_updated_at
        assert original.version == "1.0.0"  # Original unchanged
        
        # Version update with change description
        with_description = original.update_version("2.0.0", "Major feature additions")
        
        assert with_description.version == "2.0.0"
        assert with_description.custom_metadata["last_change_description"] == "Major feature additions"
    
    def test_pipeline_metadata_status_update(self):
        """Test status update functionality."""
        original = PipelineMetadataBuilder().with_status(PipelineStatus.ACTIVE).build()
        
        # Update to deprecated
        deprecated = original.update_status(PipelineStatus.DEPRECATED)
        
        assert deprecated.status == PipelineStatus.DEPRECATED
        assert deprecated.deprecated_at is not None
        assert deprecated.updated_at > original.updated_at
        
        # Update to experimental
        experimental = original.update_status(PipelineStatus.EXPERIMENTAL)
        
        assert experimental.status == PipelineStatus.EXPERIMENTAL
        assert experimental.deprecated_at is None  # Not deprecated
    
    def test_pipeline_metadata_publish(self):
        """Test publishing functionality."""
        unpublished = PipelineMetadataBuilder().with_status(PipelineStatus.DRAFT).build()
        
        # First publish
        published = unpublished.publish()
        
        assert published.is_published is True
        assert published.status == PipelineStatus.ACTIVE
        assert published.published_at is not None
        assert published.updated_at > unpublished.updated_at
        
        # Already published (no change)
        already_published = published.publish()
        assert already_published is published  # Same instance returned
    
    def test_pipeline_metadata_deprecate(self):
        """Test deprecation functionality."""
        active = PipelineMetadataBuilder().with_status(PipelineStatus.ACTIVE).build()
        
        # Deprecate without reason
        deprecated = active.deprecate()
        
        assert deprecated.is_deprecated is True
        assert deprecated.status == PipelineStatus.DEPRECATED
        assert deprecated.deprecated_at is not None
        assert deprecated.updated_at > active.updated_at
        
        # Deprecate with reason
        with_reason = active.deprecate("Replaced by newer version")
        
        assert with_reason.custom_metadata["deprecation_reason"] == "Replaced by newer version"
    
    def test_pipeline_metadata_tag_management(self):
        """Test tag addition and removal."""
        metadata = PipelineMetadataBuilder().with_tags(["original", "tag"]).build()
        
        # Add new tags
        with_new_tags = metadata.add_tags(["new", "additional", "NEW"])  # Test deduplication
        
        assert "new" in with_new_tags.tags
        assert "additional" in with_new_tags.tags
        assert with_new_tags.tags.count("new") == 1  # No duplicates
        assert with_new_tags.updated_at > metadata.updated_at
        
        # Add existing tags (no change)
        no_change = metadata.add_tags(["original"])
        assert no_change is metadata  # Same instance returned
        
        # Remove tags
        removed = with_new_tags.remove_tags(["new", "ORIGINAL"])  # Case-insensitive
        
        assert "new" not in removed.tags
        assert "original" not in removed.tags
        assert "additional" in removed.tags
        assert "tag" in removed.tags
        assert removed.updated_at > with_new_tags.updated_at
        
        # Remove non-existent tags (no change)
        no_remove = metadata.remove_tags(["nonexistent"])
        assert no_remove is metadata  # Same instance returned
    
    def test_pipeline_metadata_keyword_management(self):
        """Test keyword addition."""
        metadata = PipelineMetadataBuilder().with_keywords(["original"]).build()
        
        # Add new keywords
        with_keywords = metadata.add_keywords(["new", "keyword", "NEW"])  # Test deduplication
        
        assert "new" in with_keywords.keywords
        assert "keyword" in with_keywords.keywords
        assert with_keywords.keywords.count("new") == 1  # No duplicates
        assert with_keywords.updated_at > metadata.updated_at
        
        # Add existing keywords (no change)
        no_change = metadata.add_keywords(["original"])
        assert no_change is metadata  # Same instance returned
    
    def test_pipeline_metadata_usage_recording(self):
        """Test usage recording functionality."""
        metadata = PipelineMetadataBuilder().build()
        original_stats = metadata.usage_stats
        
        # Record successful run
        after_success = metadata.record_usage(
            success=True,
            execution_time=30.0,
            tokens=1500
        )
        
        assert after_success.usage_stats.total_runs == 1
        assert after_success.usage_stats.successful_runs == 1
        assert after_success.usage_stats.failed_runs == 0
        assert after_success.usage_stats.average_execution_time == 30.0
        assert after_success.usage_stats.total_tokens_used == 1500
        assert after_success.updated_at > metadata.updated_at
        
        # Record failed run
        after_failure = after_success.record_usage(
            success=False,
            execution_time=10.0,
            tokens=200
        )
        
        assert after_failure.usage_stats.total_runs == 2
        assert after_failure.usage_stats.successful_runs == 1
        assert after_failure.usage_stats.failed_runs == 1
        assert after_failure.usage_stats.success_rate == 50.0
    
    def test_pipeline_metadata_custom_metadata_update(self):
        """Test custom metadata updates."""
        metadata = PipelineMetadataBuilder().with_custom_metadata({"existing": "value"}).build()
        
        # Update with new metadata
        updated = metadata.update_custom_metadata({
            "new_field": "new_value",
            "another_field": 42
        })
        
        assert updated.custom_metadata["existing"] == "value"  # Preserved
        assert updated.custom_metadata["new_field"] == "new_value"
        assert updated.custom_metadata["another_field"] == 42
        assert updated.updated_at > metadata.updated_at
        
        # Override existing field
        overridden = updated.update_custom_metadata({"existing": "new_value"})
        
        assert overridden.custom_metadata["existing"] == "new_value"
    
    def test_pipeline_metadata_class_methods(self):
        """Test specialized creation class methods."""
        pipeline_id = PipelineId.from_name("test")
        name = PipelineName("Test Pipeline")
        
        # Create method
        metadata = PipelineMetadata.create(
            pipeline_id=pipeline_id,
            name=name,
            version="1.0.0",
            category=PipelineCategory.UTILITY,
            complexity=PipelineComplexity.SIMPLE,
            description="A test pipeline for comprehensive testing",
            author="Test Author",
            tags=["test", "example"]
        )
        
        assert metadata.pipeline_id == pipeline_id
        assert metadata.name == name
        assert metadata.version == "1.0.0"
        assert metadata.category == PipelineCategory.UTILITY
        assert metadata.complexity == PipelineComplexity.SIMPLE
        assert metadata.author == "Test Author"
        assert metadata.tags == ["test", "example"]
        assert metadata.short_description == "A test pipeline for comprehensive testing"
        
        # Content generation method
        content_meta = PipelineMetadata.for_content_generation(
            pipeline_id=pipeline_id,
            name=name,
            version="2.0.0",
            description="Content generation pipeline"
        )
        
        assert content_meta.category == PipelineCategory.CONTENT_GENERATION
        assert content_meta.complexity == PipelineComplexity.MODERATE
        assert "content" in content_meta.tags
        assert "generation" in content_meta.tags
        
        # Code generation method
        code_meta = PipelineMetadata.for_code_generation(
            pipeline_id=pipeline_id,
            name=name,
            description="Code generation pipeline"
        )
        
        assert code_meta.category == PipelineCategory.CODE_GENERATION
        assert code_meta.complexity == PipelineComplexity.COMPLEX
        assert "code" in code_meta.tags
        assert "generation" in code_meta.tags
    
    def test_pipeline_metadata_serialization(self):
        """Test metadata serialization."""
        usage_stats = PipelineUsageStats(
            total_runs=10,
            successful_runs=8,
            failed_runs=2,
            average_execution_time=25.5,
            total_tokens_used=5000,
            last_run_at=datetime.now()
        )
        
        created_at = datetime.now() - timedelta(days=10)
        updated_at = datetime.now() - timedelta(days=1)
        published_at = datetime.now() - timedelta(days=5)
        
        metadata = (PipelineMetadataBuilder()
                   .with_version("1.5.0")
                   .with_category(PipelineCategory.CONTENT_GENERATION)
                   .with_complexity(PipelineComplexity.MODERATE)
                   .with_status(PipelineStatus.ACTIVE)
                   .with_description("Test description")
                   .with_author("Test Author")
                   .with_organization("Test Org")
                   .with_license("MIT")
                   .with_repository_url("https://github.com/test/repo")
                   .with_documentation_url("https://docs.test.com")
                   .with_tags(["test", "example"])
                   .with_keywords(["testing", "example"])
                   .with_requirements(["python>=3.8"])
                   .with_usage_stats(usage_stats)
                   .with_created_at(created_at)
                   .with_updated_at(updated_at)
                   .with_published_at(published_at)
                   .with_custom_metadata({"custom": "value"})
                   .build())
        
        data = metadata.to_dict()
        
        # Check all fields are serialized
        assert data["pipeline_id"] == str(metadata.pipeline_id)
        assert data["name"] == str(metadata.name)
        assert data["version"] == "1.5.0"
        assert data["category"] == "content_generation"
        assert data["complexity"] == "moderate"
        assert data["status"] == "active"
        assert data["description"] == "Test description"
        assert data["author"] == "Test Author"
        assert data["organization"] == "Test Org"
        assert data["license"] == "MIT"
        assert data["repository_url"] == "https://github.com/test/repo"
        assert data["documentation_url"] == "https://docs.test.com"
        assert data["tags"] == ["test", "example"]
        assert data["keywords"] == ["testing", "example"]
        assert data["requirements"] == ["python>=3.8"]
        assert data["custom_metadata"] == {"custom": "value"}
        
        # Check usage stats serialization
        usage_data = data["usage_stats"]
        assert usage_data["total_runs"] == 10
        assert usage_data["successful_runs"] == 8
        assert usage_data["failed_runs"] == 2
        assert usage_data["success_rate"] == 80.0
        assert usage_data["average_execution_time"] == 25.5
        assert usage_data["total_tokens_used"] == 5000
        assert usage_data["last_run_at"] is not None
        
        # Check datetime serialization
        assert data["created_at"] == created_at.isoformat()
        assert data["updated_at"] == updated_at.isoformat()
        assert data["published_at"] == published_at.isoformat()
        
        # Check computed fields
        assert "popularity_score" in data
    
    def test_pipeline_metadata_string_representations(self):
        """Test string representations."""
        metadata = (PipelineMetadataBuilder()
                   .with_name(PipelineName("Test Pipeline"))
                   .with_version("1.2.3")
                   .build())
        
        str_repr = str(metadata)
        assert "Test Pipeline" in str_repr
        assert "1.2.3" in str_repr
        
        debug_repr = repr(metadata)
        assert "PipelineMetadata" in debug_repr
        assert str(metadata.pipeline_id) in debug_repr
        assert "Test Pipeline" in debug_repr
        assert "1.2.3" in debug_repr
    
    def test_pipeline_metadata_hash(self):
        """Test metadata hashing for use in sets and dictionaries."""
        pipeline_id = PipelineId.from_name("test")
        
        metadata1 = (PipelineMetadataBuilder()
                     .with_pipeline_id(pipeline_id)
                     .with_version("1.0.0")
                     .build())
        
        metadata2 = (PipelineMetadataBuilder()
                     .with_pipeline_id(pipeline_id)
                     .with_version("1.0.0")
                     .build())
        
        metadata3 = (PipelineMetadataBuilder()
                     .with_pipeline_id(pipeline_id)
                     .with_version("2.0.0")
                     .build())
        
        # Same ID and version should have same hash
        assert hash(metadata1) == hash(metadata2)
        assert hash(metadata1) != hash(metadata3)
        
        # Can be used in sets
        metadata_set = {metadata1, metadata2, metadata3}
        assert len(metadata_set) == 2  # metadata1 and metadata2 are same


class TestPipelineMetadataBusinessRules:
    """Test business rules and invariants for Pipeline Metadata entities."""
    
    def test_usage_stats_consistency(self):
        """Test that usage statistics maintain consistency."""
        stats = PipelineUsageStats()
        
        # Add multiple runs and verify consistency
        stats = stats.add_run(success=True, execution_time=30.0, tokens=1000)
        stats = stats.add_run(success=False, execution_time=15.0, tokens=500)
        stats = stats.add_run(success=True, execution_time=45.0, tokens=2000)
        
        # Verify totals are consistent
        assert stats.total_runs == 3
        assert stats.successful_runs + stats.failed_runs == stats.total_runs
        assert stats.success_rate + stats.failure_rate == 100.0
        
        # Verify average calculation
        expected_avg = (30.0 + 15.0 + 45.0) / 3
        assert stats.average_execution_time == expected_avg
        
        # Verify token totals
        assert stats.total_tokens_used == 3500
    
    def test_metadata_version_consistency(self):
        """Test that metadata versions are handled consistently."""
        metadata = PipelineMetadataBuilder().with_version("1.0.0").build()
        
        # Version updates should create new instances
        updated = metadata.update_version("1.1.0")
        assert metadata is not updated
        assert metadata.version != updated.version
        
        # Updated timestamp should change
        assert updated.updated_at > metadata.updated_at
        
        # Hash should be different for different versions
        assert hash(metadata) != hash(updated)
    
    def test_metadata_status_transitions(self):
        """Test valid status transitions."""
        # Draft -> Active (publish)
        draft = PipelineMetadataBuilder().with_status(PipelineStatus.DRAFT).build()
        published = draft.publish()
        assert published.status == PipelineStatus.ACTIVE
        assert published.is_published is True
        
        # Active -> Deprecated
        deprecated = published.update_status(PipelineStatus.DEPRECATED)
        assert deprecated.is_deprecated is True
        assert deprecated.deprecated_at is not None
        
        # Status changes should update timestamps
        assert deprecated.updated_at > published.updated_at
    
    def test_metadata_tag_normalization(self):
        """Test that tags are normalized and deduplicated."""
        metadata = PipelineMetadataBuilder().build()
        
        # Add tags with duplicates and different cases
        updated = metadata.add_tags(["Tag1", "tag1", "TAG2", "  tag3  ", ""])
        
        # Should normalize and deduplicate
        assert "tag1" in updated.tags
        assert "tag2" in updated.tags
        assert "tag3" in updated.tags
        assert updated.tags.count("tag1") == 1  # No duplicates
        assert "" not in updated.tags  # Empty tags removed
        assert "Tag1" not in updated.tags  # Normalized to lowercase
    
    def test_metadata_immutability(self):
        """Test that metadata updates follow immutability patterns."""
        original = PipelineMetadataBuilder().build()
        
        # All update methods should create new instances
        versioned = original.update_version("2.0.0")
        published = original.publish()
        deprecated = original.deprecate()
        tagged = original.add_tags(["new"])
        
        # All should be different instances
        assert original is not versioned
        assert original is not published  
        assert original is not deprecated
        assert original is not tagged
        
        # Original should be unchanged
        assert original.version != versioned.version
        assert original.is_published != published.is_published
        assert original.is_deprecated != deprecated.is_deprecated
        assert len(original.tags) != len(tagged.tags)
    
    def test_search_relevance_scoring_rules(self):
        """Test that search relevance scoring follows business rules."""
        metadata = (PipelineMetadataBuilder()
                   .with_name(PipelineName("Content Generator"))
                   .with_description("Generate content automatically")
                   .with_tags(["content", "generator"])
                   .with_keywords(["automatic", "writing"])
                   .with_category(PipelineCategory.CONTENT_GENERATION)
                   .build())
        
        # Name matches should have highest relevance
        name_score = metadata.search_relevance("Content")
        desc_score = metadata.search_relevance("Generate")
        tag_score = metadata.search_relevance("generator")
        
        assert name_score >= 0.4  # Name match bonus
        assert desc_score >= 0.2  # Description match bonus
        assert tag_score >= 0.2   # Tag match bonus
        
        # Combined matches should not exceed 1.0
        combined_score = metadata.search_relevance("content")
        assert combined_score <= 1.0
        
        # Empty query should return 0
        assert metadata.search_relevance("") == 0.0
    
    def test_popularity_score_algorithm(self):
        """Test popularity score calculation algorithm."""
        # High usage should increase score
        high_usage = PipelineUsageStats(total_runs=200)  # Will be capped at 100
        high_metadata = (PipelineMetadataBuilder()
                        .with_usage_stats(high_usage)
                        .build())
        
        low_usage = PipelineUsageStats(total_runs=5)
        low_metadata = (PipelineMetadataBuilder()
                       .with_usage_stats(low_usage)
                       .build())
        
        assert high_metadata.popularity_score > low_metadata.popularity_score
        
        # Recent updates should increase score
        recent = PipelineMetadataBuilder().with_updated_at(datetime.now()).build()
        old = (PipelineMetadataBuilder()
              .with_updated_at(datetime.now() - timedelta(days=60))
              .build())
        
        assert recent.popularity_score > old.popularity_score
        
        # High success rate should increase score
        high_success = PipelineUsageStats(total_runs=10, successful_runs=10)
        low_success = PipelineUsageStats(total_runs=10, successful_runs=5)
        
        high_success_metadata = (PipelineMetadataBuilder()
                                .with_usage_stats(high_success)
                                .build())
        low_success_metadata = (PipelineMetadataBuilder()
                               .with_usage_stats(low_success)
                               .build())
        
        assert high_success_metadata.popularity_score > low_success_metadata.popularity_score