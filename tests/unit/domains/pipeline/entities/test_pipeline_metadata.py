"""Unit tests for PipelineMetadata and PipelineUsageStats entities.

Tests entity behavior, validation, and business rules for pipeline metadata domain entities.
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from writeit.domains.pipeline.entities.pipeline_metadata import (
    PipelineMetadata,
    PipelineUsageStats,
    PipelineCategory,
    PipelineComplexity,
    PipelineStatus
)
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.pipeline_name import PipelineName


class TestPipelineUsageStats:
    """Test PipelineUsageStats behavior and calculations."""
    
    def test_create_empty_usage_stats(self):
        """Test creating empty usage statistics."""
        stats = PipelineUsageStats()
        
        assert stats.total_runs == 0
        assert stats.successful_runs == 0
        assert stats.failed_runs == 0
        assert stats.average_execution_time == 0.0
        assert stats.total_tokens_used == 0
        assert stats.last_run_at is None
        assert stats.success_rate == 0.0
        assert stats.failure_rate == 0.0
    
    def test_create_usage_stats_with_data(self):
        """Test creating usage statistics with initial data."""
        last_run = datetime.now()
        stats = PipelineUsageStats(
            total_runs=10,
            successful_runs=8,
            failed_runs=2,
            average_execution_time=45.5,
            total_tokens_used=15000,
            last_run_at=last_run
        )
        
        assert stats.total_runs == 10
        assert stats.successful_runs == 8
        assert stats.failed_runs == 2
        assert stats.average_execution_time == 45.5
        assert stats.total_tokens_used == 15000
        assert stats.last_run_at == last_run
        assert stats.success_rate == 80.0
        assert stats.failure_rate == 20.0
    
    def test_success_rate_calculation(self):
        """Test success rate calculations."""
        # 100% success
        stats_perfect = PipelineUsageStats(total_runs=5, successful_runs=5, failed_runs=0)
        assert stats_perfect.success_rate == 100.0
        assert stats_perfect.failure_rate == 0.0
        
        # 0% success
        stats_failure = PipelineUsageStats(total_runs=3, successful_runs=0, failed_runs=3)
        assert stats_failure.success_rate == 0.0
        assert stats_failure.failure_rate == 100.0
        
        # 60% success
        stats_mixed = PipelineUsageStats(total_runs=10, successful_runs=6, failed_runs=4)
        assert stats_mixed.success_rate == 60.0
        assert stats_mixed.failure_rate == 40.0
    
    def test_add_successful_run(self):
        """Test adding a successful run."""
        stats = PipelineUsageStats()
        
        updated_stats = stats.add_run(success=True, execution_time=30.0, tokens=1000)
        
        # Original stats unchanged
        assert stats.total_runs == 0
        assert stats.successful_runs == 0
        
        # Updated stats reflect the new run
        assert updated_stats.total_runs == 1
        assert updated_stats.successful_runs == 1
        assert updated_stats.failed_runs == 0
        assert updated_stats.average_execution_time == 30.0
        assert updated_stats.total_tokens_used == 1000
        assert updated_stats.last_run_at is not None
        assert updated_stats.success_rate == 100.0
    
    def test_add_failed_run(self):
        """Test adding a failed run."""
        stats = PipelineUsageStats()
        
        updated_stats = stats.add_run(success=False, execution_time=15.0, tokens=500)
        
        assert updated_stats.total_runs == 1
        assert updated_stats.successful_runs == 0
        assert updated_stats.failed_runs == 1
        assert updated_stats.average_execution_time == 15.0
        assert updated_stats.total_tokens_used == 500
        assert updated_stats.success_rate == 0.0
        assert updated_stats.failure_rate == 100.0
    
    def test_add_multiple_runs(self):
        """Test adding multiple runs and average calculation."""
        stats = PipelineUsageStats()
        
        # Add first run: 30 seconds, 1000 tokens, success
        stats1 = stats.add_run(success=True, execution_time=30.0, tokens=1000)
        
        # Add second run: 60 seconds, 1500 tokens, success
        stats2 = stats1.add_run(success=True, execution_time=60.0, tokens=1500)
        
        # Add third run: 45 seconds, 800 tokens, failure
        stats3 = stats2.add_run(success=False, execution_time=45.0, tokens=800)
        
        assert stats3.total_runs == 3
        assert stats3.successful_runs == 2
        assert stats3.failed_runs == 1
        assert stats3.average_execution_time == 45.0  # (30 + 60 + 45) / 3
        assert stats3.total_tokens_used == 3300  # 1000 + 1500 + 800
        assert stats3.success_rate == pytest.approx(66.666666666666667, rel=1e-9)
        assert stats3.failure_rate == pytest.approx(33.333333333333333, rel=1e-9)
    
    def test_average_execution_time_calculation(self):
        """Test average execution time calculation with existing data."""
        # Start with existing stats
        stats = PipelineUsageStats(
            total_runs=2,
            successful_runs=2,
            failed_runs=0,
            average_execution_time=40.0,  # Average of 2 runs at 40s each
            total_tokens_used=2000
        )
        
        # Add a third run: 20 seconds
        updated_stats = stats.add_run(success=True, execution_time=20.0, tokens=1000)
        
        # New average should be (40*2 + 20) / 3 = 100/3 = 33.333...
        assert updated_stats.total_runs == 3
        assert updated_stats.average_execution_time == pytest.approx(33.333333333333336, rel=1e-9)
        assert updated_stats.total_tokens_used == 3000


class TestPipelineMetadata:
    """Test PipelineMetadata entity behavior and validation."""
    
    def test_create_minimal_metadata(self):
        """Test creating minimal valid pipeline metadata."""
        pipeline_id = PipelineId("test-pipeline")
        name = PipelineName("Test Pipeline")
        
        metadata = PipelineMetadata(
            pipeline_id=pipeline_id,
            name=name,
            version="1.0.0",
            category=PipelineCategory.UTILITY,
            complexity=PipelineComplexity.SIMPLE
        )
        
        assert metadata.pipeline_id == pipeline_id
        assert metadata.name == name
        assert metadata.version == "1.0.0"
        assert metadata.category == PipelineCategory.UTILITY
        assert metadata.complexity == PipelineComplexity.SIMPLE
        assert metadata.status == PipelineStatus.ACTIVE
        assert metadata.description == ""
        assert metadata.short_description == ""
        assert metadata.author is None
        assert len(metadata.tags) == 0
        assert len(metadata.keywords) == 0
        assert len(metadata.requirements) == 0
        assert isinstance(metadata.usage_stats, PipelineUsageStats)
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.updated_at, datetime)
    
    def test_create_complete_metadata(self):
        """Test creating complete pipeline metadata."""
        pipeline_id = PipelineId("content-generator")
        name = PipelineName("Advanced Content Generator")
        tags = ["content", "article", "blog"]
        keywords = ["writing", "generation", "AI"]
        requirements = ["openai>=1.0.0", "anthropic>=0.5.0"]
        custom_data = {"model_preference": "gpt-4o-mini", "temperature": 0.7}
        
        metadata = PipelineMetadata(
            pipeline_id=pipeline_id,
            name=name,
            version="2.1.0",
            category=PipelineCategory.CONTENT_GENERATION,
            complexity=PipelineComplexity.MODERATE,
            status=PipelineStatus.ACTIVE,
            description="Advanced pipeline for generating high-quality content",
            short_description="Generate content with AI",
            author="Jane Doe",
            organization="AI Corp",
            license="MIT",
            repository_url="https://github.com/ai-corp/content-gen",
            documentation_url="https://docs.ai-corp.com/content-gen",
            tags=tags,
            keywords=keywords,
            requirements=requirements,
            custom_metadata=custom_data
        )
        
        assert metadata.description == "Advanced pipeline for generating high-quality content"
        assert metadata.short_description == "Generate content with AI"
        assert metadata.author == "Jane Doe"
        assert metadata.organization == "AI Corp"
        assert metadata.license == "MIT"
        assert metadata.repository_url == "https://github.com/ai-corp/content-gen"
        assert metadata.documentation_url == "https://docs.ai-corp.com/content-gen"
        assert metadata.tags == tags
        assert metadata.keywords == keywords
        assert metadata.requirements == requirements
        assert metadata.custom_metadata == custom_data
    
    def test_invalid_pipeline_id_type_raises_error(self):
        """Test that invalid pipeline ID type raises TypeError."""
        with pytest.raises(TypeError, match="Pipeline id must be a PipelineId"):
            PipelineMetadata(
                pipeline_id="invalid",  # Should be PipelineId
                name=PipelineName("Test"),
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE
            )
    
    def test_invalid_name_type_raises_error(self):
        """Test that invalid name type raises TypeError."""
        with pytest.raises(TypeError, match="Name must be a PipelineName"):
            PipelineMetadata(
                pipeline_id=PipelineId("test"),
                name="invalid",  # Should be PipelineName
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE
            )
    
    def test_empty_version_raises_error(self):
        """Test that empty version raises ValueError."""
        with pytest.raises(ValueError, match="Version must be a non-empty string"):
            PipelineMetadata(
                pipeline_id=PipelineId("test"),
                name=PipelineName("Test"),
                version="",  # Empty version
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE
            )
    
    def test_invalid_category_type_raises_error(self):
        """Test that invalid category type raises TypeError."""
        with pytest.raises(TypeError, match="Category must be a PipelineCategory"):
            PipelineMetadata(
                pipeline_id=PipelineId("test"),
                name=PipelineName("Test"),
                version="1.0.0",
                category="invalid",  # Should be PipelineCategory
                complexity=PipelineComplexity.SIMPLE
            )
    
    def test_invalid_complexity_type_raises_error(self):
        """Test that invalid complexity type raises TypeError."""
        with pytest.raises(TypeError, match="Complexity must be a PipelineComplexity"):
            PipelineMetadata(
                pipeline_id=PipelineId("test"),
                name=PipelineName("Test"),
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity="invalid"  # Should be PipelineComplexity
            )
    
    def test_invalid_status_type_raises_error(self):
        """Test that invalid status type raises TypeError."""
        with pytest.raises(TypeError, match="Status must be a PipelineStatus"):
            PipelineMetadata(
                pipeline_id=PipelineId("test"),
                name=PipelineName("Test"),
                version="1.0.0",
                category=PipelineCategory.UTILITY,
                complexity=PipelineComplexity.SIMPLE,
                status="invalid"  # Should be PipelineStatus
            )
    
    def test_pipeline_metadata_properties(self):
        """Test pipeline metadata status properties."""
        metadata = PipelineMetadata(
            pipeline_id=PipelineId("test"),
            name=PipelineName("Test"),
            version="1.0.0",
            category=PipelineCategory.UTILITY,
            complexity=PipelineComplexity.SIMPLE,
            status=PipelineStatus.ACTIVE
        )
        
        # Test active status
        assert metadata.is_active is True
        assert metadata.is_deprecated is False
        assert metadata.is_experimental is False
        
        # Test deprecated status
        deprecated_metadata = PipelineMetadata(
            pipeline_id=PipelineId("test"),
            name=PipelineName("Test"),
            version="1.0.0",
            category=PipelineCategory.UTILITY,
            complexity=PipelineComplexity.SIMPLE,
            status=PipelineStatus.DEPRECATED
        )
        
        assert deprecated_metadata.is_active is False
        assert deprecated_metadata.is_deprecated is True
        assert deprecated_metadata.is_experimental is False
        
        # Test experimental status
        experimental_metadata = PipelineMetadata(
            pipeline_id=PipelineId("test"),
            name=PipelineName("Test"),
            version="1.0.0",
            category=PipelineCategory.UTILITY,
            complexity=PipelineComplexity.SIMPLE,
            status=PipelineStatus.EXPERIMENTAL
        )
        
        assert experimental_metadata.is_active is False
        assert experimental_metadata.is_deprecated is False
        assert experimental_metadata.is_experimental is True