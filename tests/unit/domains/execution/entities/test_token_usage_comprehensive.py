"""Comprehensive unit tests for TokenUsage entity."""

import pytest
from datetime import datetime
from decimal import Decimal
from src.writeit.domains.execution.entities.token_usage import TokenUsage
from src.writeit.domains.execution.value_objects.model_name import ModelName
from tests.builders.execution_builders import TokenUsageBuilder


class TestTokenUsage:
    """Test cases for TokenUsage entity."""
    
    def test_token_usage_creation(self):
        """Test creating token usage with valid data."""
        usage = TokenUsageBuilder.small_request().build()
        
        assert usage.model_name.value == "gpt-4o-mini"
        assert usage.workspace_name == "test_workspace"
        assert usage.token_metrics.input_tokens == 50
        assert usage.token_metrics.output_tokens == 25
        assert usage.token_metrics.total_tokens == 75
        assert usage.cost_breakdown.total_cost == Decimal('0.0001')
        assert isinstance(usage.timestamp, datetime)

    def test_medium_request_usage(self):
        """Test creating medium token usage."""
        usage = TokenUsageBuilder.medium_request().build()
        
        assert usage.model_name.value == "gpt-4o"
        assert usage.token_metrics.input_tokens == 500
        assert usage.token_metrics.output_tokens == 250
        assert usage.cost_breakdown.total_cost == Decimal('0.001')

    def test_large_request_usage(self):
        """Test creating large token usage."""
        usage = TokenUsageBuilder.large_request().build()
        
        assert usage.model_name.value == "claude-3-opus"
        assert usage.token_metrics.input_tokens == 2000
        assert usage.token_metrics.output_tokens == 1000
        assert usage.cost_breakdown.total_cost == Decimal('0.01')

    def test_pipeline_step_usage(self):
        """Test creating pipeline step usage."""
        usage = TokenUsageBuilder.pipeline_step_usage("run-123", "step-456").build()
        
        assert usage.pipeline_id == "run-123"
        assert usage.step_id == "step-456"
        assert usage.metadata["step_type"] == "llm_generate"
        assert usage.metadata["execution_time_ms"] == 1500


class TestTokenUsageEdgeCases:
    """Test edge cases for TokenUsage."""
    
    def test_batch_usage_creation(self):
        """Test creating batch token usage records."""
        batch = TokenUsageBuilder.batch_usage(3)
        
        assert len(batch) == 3
        for i, usage_builder in enumerate(batch):
            usage = usage_builder.build()
            assert usage.request_id == f"req_{i}"