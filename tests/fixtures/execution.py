"""Execution domain entity fixtures for testing.

Provides comprehensive test fixtures for execution domain entities including
LLM providers, execution contexts, token usage, and execution scenarios.
"""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from typing import Dict, Any, List, Optional

from writeit.domains.execution.entities.llm_provider import (
    LLMProvider, ProviderType, ProviderStatus
)
from writeit.domains.execution.entities.execution_context import (
    ExecutionContext, ExecutionPriority
)
from writeit.domains.execution.entities.token_usage import (
    TokenUsage, TokenMetrics, CostBreakdown, UsageCategory
)
from writeit.domains.execution.value_objects.model_name import ModelName
from writeit.domains.execution.value_objects.token_count import TokenCount
from writeit.domains.execution.value_objects.cache_key import CacheKey
from writeit.domains.execution.value_objects.execution_mode import ExecutionMode


# ============================================================================
# Basic Execution Entity Fixtures
# ============================================================================

@pytest.fixture
def model_name_fixture():
    """Valid model name for testing."""
    return ModelName.from_string("gpt-4o-mini")

@pytest.fixture
def token_count_fixture():
    """Valid token count for testing."""
    return TokenCount.create(input_tokens=100, output_tokens=50)

@pytest.fixture
def cache_key_fixture():
    """Valid cache key for testing."""
    return CacheKey.generate()

@pytest.fixture
def execution_mode_fixture():
    """Valid execution mode for testing."""
    return ExecutionMode.cli()

@pytest.fixture
def llm_provider_fixture():
    """Valid LLM provider with OpenAI configuration."""
    models = [
        ModelName.from_string("gpt-4o-mini"),
        ModelName.from_string("gpt-4o"),
        ModelName.from_string("gpt-3.5-turbo")
    ]
    
    provider = LLMProvider.create(
        name="OpenAI Test Provider",
        provider_type=ProviderType.OPENAI,
        api_key_ref="test_openai_key",
        base_url="https://api.openai.com/v1",
        supported_models=models,
        capabilities={
            "streaming": True,
            "function_calling": True,
            "vision": True
        }
    )
    
    # Set model-specific metadata
    provider = provider.update_metadata("max_tokens_gpt-4o-mini", 128000)
    provider = provider.update_metadata("max_tokens_gpt-4o", 128000)
    provider = provider.update_metadata("max_tokens_gpt-3.5-turbo", 16384)
    
    # Set rate limits
    provider = provider.set_rate_limit("requests_per_minute", 3500)
    provider = provider.set_rate_limit("tokens_per_minute", 500000)
    
    return provider

@pytest.fixture
def execution_context_fixture():
    """Valid execution context for testing."""
    return ExecutionContext.create(
        workspace_name="test-workspace",
        pipeline_id="test-pipeline-123",
        execution_mode=ExecutionMode.cli(),
        priority=ExecutionPriority.NORMAL
    )

@pytest.fixture
def token_usage_fixture():
    """Valid token usage record for testing."""
    return TokenUsage.create(
        session_id="session-123",
        model_name=ModelName.from_string("gpt-4o-mini"),
        input_tokens=150,
        output_tokens=75,
        usage_category=UsageCategory.PIPELINE_EXECUTION,
        workspace_name="test-workspace",
        pipeline_id="pipeline-123",
        step_id="step-content",
        cached_tokens=25
    ).calculate_cost(
        input_price_per_token=Decimal("0.00015"),
        output_price_per_token=Decimal("0.0006"),
        currency="USD"
    )


# ============================================================================
# LLM Provider Variants
# ============================================================================

@pytest.fixture
def openai_provider():
    """OpenAI provider with default configuration."""
    return LLMProvider.openai_provider(
        api_key_ref="openai_test_key",
        name="OpenAI Provider"
    ).mark_healthy()

@pytest.fixture
def anthropic_provider():
    """Anthropic provider with default configuration."""
    return LLMProvider.anthropic_provider(
        api_key_ref="anthropic_test_key",
        name="Anthropic Provider"
    ).mark_healthy()

@pytest.fixture
def local_provider():
    """Local LLM provider for testing."""
    models = [
        ModelName.from_string("llama-2-7b"),
        ModelName.from_string("mistral-7b")
    ]
    
    return LLMProvider.create(
        name="Local LLM Provider",
        provider_type=ProviderType.LOCAL,
        base_url="http://localhost:8080",
        supported_models=models,
        capabilities={
            "streaming": False,
            "function_calling": False,
            "vision": False
        }
    ).update_metadata("max_tokens_llama-2-7b", 4096).update_metadata("max_tokens_mistral-7b", 8192)

@pytest.fixture
def mock_provider():
    """Mock provider for testing."""
    return LLMProvider.mock_provider("Test Mock Provider")

@pytest.fixture
def inactive_provider():
    """Inactive LLM provider."""
    provider = LLMProvider.openai_provider("inactive_key", "Inactive Provider")
    return provider.mark_inactive()

@pytest.fixture
def maintenance_provider():
    """Provider under maintenance."""
    provider = LLMProvider.anthropic_provider("maintenance_key", "Maintenance Provider")
    return provider.mark_maintenance("Scheduled maintenance")

@pytest.fixture
def error_provider():
    """Provider with error status."""
    provider = LLMProvider.openai_provider("error_key", "Error Provider")
    return provider.mark_error("API key invalid")


# ============================================================================
# Execution Context Variants
# ============================================================================

@pytest.fixture
def cli_execution_context():
    """CLI execution context."""
    return ExecutionContext.for_cli(
        workspace_name="cli-workspace",
        pipeline_id="cli-pipeline"
    )

@pytest.fixture
def tui_execution_context():
    """TUI execution context."""
    return ExecutionContext.for_tui(
        workspace_name="tui-workspace",
        pipeline_id="tui-pipeline"
    )

@pytest.fixture
def api_execution_context():
    """API execution context."""
    return ExecutionContext.for_api(
        workspace_name="api-workspace",
        pipeline_id="api-pipeline",
        user_id="user-123",
        request_id="req-456"
    )

@pytest.fixture
def batch_execution_context():
    """Batch execution context."""
    return ExecutionContext.for_batch(
        workspace_name="batch-workspace",
        pipeline_id="batch-pipeline",
        batch_id="batch-789"
    )

@pytest.fixture
def high_priority_context():
    """High priority execution context."""
    return ExecutionContext.create(
        workspace_name="priority-workspace",
        pipeline_id="urgent-pipeline",
        execution_mode=ExecutionMode.api(),
        priority=ExecutionPriority.HIGH
    )

@pytest.fixture
def low_priority_context():
    """Low priority execution context."""
    return ExecutionContext.create(
        workspace_name="background-workspace",
        pipeline_id="background-pipeline",
        execution_mode=ExecutionMode.batch(),
        priority=ExecutionPriority.LOW
    )


# ============================================================================
# Token Usage Variants
# ============================================================================

@pytest.fixture
def pipeline_token_usage():
    """Token usage for pipeline execution."""
    return TokenUsage.create(
        session_id="pipeline-session-123",
        model_name=ModelName.from_string("gpt-4o-mini"),
        input_tokens=500,
        output_tokens=300,
        usage_category=UsageCategory.PIPELINE_EXECUTION,
        workspace_name="content-workspace",
        pipeline_id="article-pipeline",
        step_id="generate-content"
    )

@pytest.fixture
def validation_token_usage():
    """Token usage for validation."""
    return TokenUsage.create(
        session_id="validation-session-456",
        model_name=ModelName.from_string("gpt-3.5-turbo"),
        input_tokens=200,
        output_tokens=50,
        usage_category=UsageCategory.VALIDATION,
        workspace_name="quality-workspace"
    )

@pytest.fixture
def template_rendering_token_usage():
    """Token usage for template rendering."""
    return TokenUsage.create(
        session_id="template-session-789",
        model_name=ModelName.from_string("gpt-4o-mini"),
        input_tokens=100,
        output_tokens=25,
        usage_category=UsageCategory.TEMPLATE_RENDERING,
        workspace_name="template-workspace"
    )

@pytest.fixture
def content_generation_token_usage():
    """Token usage for content generation."""
    return TokenUsage.create(
        session_id="content-session-101",
        model_name=ModelName.from_string("gpt-4o"),
        input_tokens=800,
        output_tokens=600,
        usage_category=UsageCategory.CONTENT_GENERATION,
        workspace_name="publishing-workspace",
        pipeline_id="blog-pipeline",
        step_id="write-article"
    ).calculate_cost(
        input_price_per_token=Decimal("0.00025"),
        output_price_per_token=Decimal("0.001"),
        currency="USD"
    )

@pytest.fixture
def cached_token_usage():
    """Token usage with high cache hit rate."""
    return TokenUsage.create(
        session_id="cached-session-202",
        model_name=ModelName.from_string("gpt-4o-mini"),
        input_tokens=1000,
        output_tokens=500,
        usage_category=UsageCategory.PIPELINE_EXECUTION,
        cached_tokens=400,  # 40% cache hit rate
        workspace_name="cached-workspace"
    )


# ============================================================================
# Complex Execution Scenarios
# ============================================================================

@pytest.fixture
def multi_provider_scenario():
    """Scenario with multiple LLM providers."""
    providers = {
        "primary": LLMProvider.openai_provider("primary_key", "Primary OpenAI").mark_healthy(),
        "fallback": LLMProvider.anthropic_provider("fallback_key", "Fallback Anthropic").mark_healthy(),
        "local": LLMProvider.create(
            name="Local Backup",
            provider_type=ProviderType.LOCAL,
            supported_models=[ModelName.from_string("llama-2-7b")]
        ).mark_healthy(),
        "maintenance": LLMProvider.openai_provider("maint_key", "Maintenance Provider").mark_maintenance()
    }
    
    return providers

@pytest.fixture
def execution_with_retries():
    """Execution context with retry configuration."""
    context = ExecutionContext.create(
        workspace_name="retry-workspace",
        pipeline_id="retry-pipeline",
        execution_mode=ExecutionMode.cli()
    )
    
    # Configure retries
    context = context.configure_retries(max_attempts=5, base_delay=1.0, max_delay=30.0)
    
    # Simulate some retry attempts
    for i in range(3):
        context = context.record_retry_attempt(f"Attempt {i+1} failed", delay=2.0 ** i)
    
    return context

@pytest.fixture
def token_usage_analytics():
    """Collection of token usage for analytics."""
    usages = []
    
    # Different models and usage patterns
    models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "claude-3-haiku"]
    categories = [
        UsageCategory.PIPELINE_EXECUTION,
        UsageCategory.CONTENT_GENERATION,
        UsageCategory.VALIDATION,
        UsageCategory.TEMPLATE_RENDERING
    ]
    
    for i in range(20):
        model = ModelName.from_string(models[i % len(models)])
        category = categories[i % len(categories)]
        
        usage = TokenUsage.create(
            session_id=f"analytics-session-{i}",
            model_name=model,
            input_tokens=100 + (i * 50),
            output_tokens=50 + (i * 25),
            usage_category=category,
            workspace_name=f"workspace-{i % 3}",
            cached_tokens=(i * 10) if i % 3 == 0 else 0
        )
        
        # Calculate costs with different pricing tiers
        if "gpt-4o" in str(model):
            input_price = Decimal("0.00025")
            output_price = Decimal("0.001")
        elif "claude" in str(model):
            input_price = Decimal("0.0008")
            output_price = Decimal("0.024")
        else:
            input_price = Decimal("0.00015")
            output_price = Decimal("0.0006")
        
        usage = usage.calculate_cost(input_price, output_price)
        usages.append(usage)
    
    return usages


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def high_throughput_context():
    """Execution context optimized for high throughput."""
    context = ExecutionContext.create(
        workspace_name="throughput-workspace",
        pipeline_id="batch-processing",
        execution_mode=ExecutionMode.batch(),
        priority=ExecutionPriority.HIGH
    )
    
    # Configure for high throughput
    context = context.set_concurrency_limit(10)
    context = context.set_batch_size(100)
    context = context.enable_aggressive_caching(True)
    
    return context

@pytest.fixture
def low_latency_context():
    """Execution context optimized for low latency."""
    context = ExecutionContext.create(
        workspace_name="latency-workspace",
        pipeline_id="real-time-processing",
        execution_mode=ExecutionMode.api(),
        priority=ExecutionPriority.HIGH
    )
    
    # Configure for low latency
    context = context.set_timeout(5.0)  # 5 second timeout
    context = context.enable_aggressive_caching(True)
    context = context.prefer_cached_results(True)
    
    return context

@pytest.fixture
def resource_constrained_context():
    """Execution context for resource-constrained environment."""
    context = ExecutionContext.create(
        workspace_name="constrained-workspace",
        pipeline_id="efficient-processing",
        execution_mode=ExecutionMode.cli(),
        priority=ExecutionPriority.LOW
    )
    
    # Configure for efficiency
    context = context.set_concurrency_limit(2)
    context = context.set_max_tokens(1000)
    context = context.enable_token_conservation(True)
    
    return context


# ============================================================================
# Error/Edge Case Fixtures
# ============================================================================

@pytest.fixture
def invalid_providers():
    """Invalid LLM provider configurations for negative testing."""
    return {
        "empty_name": {
            "name": "",
            "provider_type": ProviderType.OPENAI,
            "error": "Provider name cannot be empty"
        },
        "invalid_api_key": {
            "name": "Invalid Key Provider",
            "provider_type": ProviderType.OPENAI,
            "api_key_ref": "",
            "error": "API key reference cannot be empty"
        },
        "no_supported_models": {
            "name": "No Models Provider",
            "provider_type": ProviderType.OPENAI,
            "supported_models": [],
            "error": "Provider must support at least one model"
        },
        "invalid_base_url": {
            "name": "Invalid URL Provider",
            "provider_type": ProviderType.LOCAL,
            "base_url": "not-a-valid-url",
            "error": "Invalid base URL format"
        }
    }

@pytest.fixture
def invalid_execution_contexts():
    """Invalid execution context configurations for negative testing."""
    return {
        "empty_workspace": {
            "workspace_name": "",
            "pipeline_id": "test-pipeline",
            "error": "Workspace name cannot be empty"
        },
        "empty_pipeline_id": {
            "workspace_name": "test-workspace",
            "pipeline_id": "",
            "error": "Pipeline ID cannot be empty"
        },
        "invalid_priority": {
            "workspace_name": "test-workspace",
            "pipeline_id": "test-pipeline",
            "priority": "invalid",
            "error": "Invalid execution priority"
        }
    }

@pytest.fixture
def edge_case_token_usage():
    """Edge case token usage for boundary testing."""
    return {
        "zero_tokens": {
            "input_tokens": 0,
            "output_tokens": 0,
            "error": "Token counts cannot be zero"
        },
        "negative_tokens": {
            "input_tokens": -10,
            "output_tokens": 50,
            "error": "Token counts cannot be negative"
        },
        "excessive_tokens": {
            "input_tokens": 1000000,
            "output_tokens": 1000000,
            "error": "Token counts exceed model limits"
        },
        "invalid_cached_tokens": {
            "input_tokens": 100,
            "output_tokens": 50,
            "cached_tokens": 200,  # More cached than total
            "error": "Cached tokens cannot exceed total tokens"
        }
    }


# ============================================================================
# Factory Fixtures
# ============================================================================

@pytest.fixture
def execution_factory():
    """Factory for creating execution entities with custom parameters."""
    class ExecutionFactory:
        @staticmethod
        def create_provider(
            provider_type: str = "openai",
            status: str = "active",
            **kwargs
        ) -> LLMProvider:
            """Create LLM provider with specified characteristics."""
            if provider_type == "openai":
                provider = LLMProvider.openai_provider("test_key", "Test OpenAI")
            elif provider_type == "anthropic":
                provider = LLMProvider.anthropic_provider("test_key", "Test Anthropic")
            elif provider_type == "local":
                provider = LLMProvider.create(
                    name="Test Local",
                    provider_type=ProviderType.LOCAL,
                    supported_models=[ModelName.from_string("local-model")]
                )
            else:  # mock
                provider = LLMProvider.mock_provider("Test Mock")
            
            # Set status
            if status == "inactive":
                provider = provider.mark_inactive()
            elif status == "maintenance":
                provider = provider.mark_maintenance("Test maintenance")
            elif status == "error":
                provider = provider.mark_error("Test error")
            # active is default
            
            return provider
        
        @staticmethod
        def create_context(
            mode: str = "cli",
            priority: str = "normal",
            **kwargs
        ) -> ExecutionContext:
            """Create execution context with specified characteristics."""
            workspace_name = kwargs.get("workspace_name", f"test-workspace-{uuid4().hex[:8]}")
            pipeline_id = kwargs.get("pipeline_id", f"test-pipeline-{uuid4().hex[:8]}")
            
            if mode == "cli":
                execution_mode = ExecutionMode.cli()
            elif mode == "tui":
                execution_mode = ExecutionMode.tui()
            elif mode == "api":
                execution_mode = ExecutionMode.api()
            else:  # batch
                execution_mode = ExecutionMode.batch()
            
            if priority == "high":
                exec_priority = ExecutionPriority.HIGH
            elif priority == "low":
                exec_priority = ExecutionPriority.LOW
            else:  # normal
                exec_priority = ExecutionPriority.NORMAL
            
            return ExecutionContext.create(
                workspace_name=workspace_name,
                pipeline_id=pipeline_id,
                execution_mode=execution_mode,
                priority=exec_priority
            )
        
        @staticmethod
        def create_token_usage(
            model: str = "gpt-4o-mini",
            category: str = "pipeline",
            tokens_scale: str = "small",
            **kwargs
        ) -> TokenUsage:
            """Create token usage with specified characteristics."""
            model_name = ModelName.from_string(model)
            
            if category == "pipeline":
                usage_category = UsageCategory.PIPELINE_EXECUTION
            elif category == "validation":
                usage_category = UsageCategory.VALIDATION
            elif category == "content":
                usage_category = UsageCategory.CONTENT_GENERATION
            else:  # template
                usage_category = UsageCategory.TEMPLATE_RENDERING
            
            if tokens_scale == "small":
                input_tokens, output_tokens = 100, 50
            elif tokens_scale == "medium":
                input_tokens, output_tokens = 500, 250
            else:  # large
                input_tokens, output_tokens = 2000, 1000
            
            return TokenUsage.create(
                session_id=f"session-{uuid4().hex[:8]}",
                model_name=model_name,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                usage_category=usage_category,
                **kwargs
            )
    
    return ExecutionFactory()


# ============================================================================
# Valid/Invalid Entity Collections
# ============================================================================

@pytest.fixture
def valid_llm_provider(llm_provider_fixture):
    """Valid LLM provider for positive testing."""
    return llm_provider_fixture

@pytest.fixture
def invalid_llm_provider():
    """Invalid LLM provider data for negative testing."""
    return {
        "missing_name": None,
        "empty_name": "",
        "invalid_provider_type": "invalid_type",
        "missing_models": []
    }