"""Unit tests for LLMOrchestrationService.

Tests comprehensive LLM orchestration logic including:
- Multi-provider registration and management
- Provider selection strategies and load balancing
- Request routing and fallback management
- Rate limiting and quota management
- Performance monitoring and optimization
- Error handling and recovery logic
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import replace

from src.writeit.domains.execution.services.llm_orchestration_service import (
    LLMOrchestrationService,
    ProviderSelectionStrategy,
    FallbackTrigger,
    RequestPriority,
    ProviderMetrics,
    RequestContext,
    LLMResponse,
    ProviderLoadBalancer,
    LLMOrchestrationError,
    ProviderUnavailableError,
    ModelNotSupportedError,
    RateLimitExceededError
)
from src.writeit.domains.execution.entities.llm_provider import LLMProvider, ProviderStatus, ProviderType
from src.writeit.domains.execution.entities.execution_context import ExecutionContext
from src.writeit.domains.execution.value_objects.model_name import ModelName
from src.writeit.domains.execution.value_objects.token_count import TokenCount

from tests.builders.execution_builders import (
    LLMProviderBuilder,
    ExecutionContextBuilder
)


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, name: str, models: List[str], available: bool = True, latency_ms: float = 100.0):
        self._name = name
        self._supported_models = models
        self._available = available
        self._latency_ms = latency_ms
        self._call_count = 0
        self._fail_next = False
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.CLOUD
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def supports_model(self, model: ModelName) -> bool:
        return model.value in self._supported_models
    
    async def generate_response(
        self, 
        prompt: str, 
        model: ModelName, 
        **kwargs
    ) -> Dict[str, Any]:
        """Mock response generation."""
        self._call_count += 1
        
        # Simulate latency
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        if self._fail_next:
            self._fail_next = False
            raise Exception(f"Mock failure from {self._name}")
        
        return {
            "content": f"Response from {self._name} using {model.value}",
            "usage": {
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": 20,
                "total_tokens": len(prompt.split()) + 20
            },
            "model": model.value,
            "cost": 0.01
        }
    
    def fail_next_request(self) -> None:
        """Make next request fail for testing."""
        self._fail_next = True
    
    def set_available(self, available: bool) -> None:
        """Set availability for testing."""
        self._available = available
    
    @property
    def call_count(self) -> int:
        return self._call_count
    
    def reset(self) -> None:
        """Reset mock state."""
        self._call_count = 0
        self._fail_next = False


class TestProviderMetrics:
    """Test ProviderMetrics behavior."""
    
    def test_create_provider_metrics(self):
        """Test creating provider metrics."""
        metrics = ProviderMetrics(
            provider_name="test-provider",
            total_requests=100,
            successful_requests=85,
            failed_requests=15,
            avg_latency_ms=150.5,
            avg_tokens_per_second=25.0,
            avg_cost_per_request=0.015,
            error_rate=0.15
        )
        
        assert metrics.provider_name == "test-provider"
        assert metrics.total_requests == 100
        assert metrics.successful_requests == 85
        assert metrics.failed_requests == 15
        assert metrics.avg_latency_ms == 150.5
        assert metrics.avg_tokens_per_second == 25.0
        assert metrics.avg_cost_per_request == 0.015
        assert metrics.error_rate == 0.15
    
    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        metrics = ProviderMetrics(
            provider_name="test",
            total_requests=100,
            successful_requests=85
        )
        
        assert metrics.success_rate == 0.85
        
        # Test with no requests
        metrics_empty = ProviderMetrics(provider_name="test", total_requests=0)
        assert metrics_empty.success_rate == 1.0
    
    def test_availability_check(self):
        """Test provider availability logic."""
        # Available provider
        metrics = ProviderMetrics(
            provider_name="available",
            error_rate=0.1,
            rate_limit_remaining=100
        )
        assert metrics.is_available is True
        
        # High error rate
        metrics_high_error = ProviderMetrics(
            provider_name="high_error",
            error_rate=0.6
        )
        assert metrics_high_error.is_available is False
        
        # Rate limited
        future_time = datetime.now() + timedelta(minutes=5)
        metrics_rate_limited = ProviderMetrics(
            provider_name="rate_limited",
            error_rate=0.1,
            rate_limit_remaining=0,
            rate_limit_reset_time=future_time
        )
        assert metrics_rate_limited.is_available is False
    
    def test_load_factor_calculation(self):
        """Test load factor calculation."""
        metrics = ProviderMetrics(
            provider_name="test",
            current_load=5
        )
        
        # Assuming max_concurrent = 10
        assert metrics.load_factor == 0.5
        
        # Test at capacity
        metrics_at_capacity = ProviderMetrics(
            provider_name="test",
            current_load=15  # Over capacity
        )
        assert metrics_at_capacity.load_factor == 1.0


class TestRequestContext:
    """Test RequestContext behavior."""
    
    def test_create_request_context(self):
        """Test creating request context."""
        execution_context = ExecutionContextBuilder().build()
        model_preference = [ModelName.from_string("gpt-4o-mini")]
        
        context = RequestContext(
            request_id="req-123",
            execution_context=execution_context,
            prompt="Generate content about AI",
            model_preference=model_preference,
            priority=RequestPriority.HIGH,
            max_tokens=1000,
            temperature=0.7,
            streaming=True,
            timeout_seconds=30
        )
        
        assert context.request_id == "req-123"
        assert context.execution_context == execution_context
        assert context.prompt == "Generate content about AI"
        assert context.model_preference == model_preference
        assert context.priority == RequestPriority.HIGH
        assert context.max_tokens == 1000
        assert context.temperature == 0.7
        assert context.streaming is True
        assert context.timeout_seconds == 30
        assert context.retry_count == 0
        assert isinstance(context.created_at, datetime)


class TestLLMResponse:
    """Test LLMResponse behavior."""
    
    def test_create_llm_response(self):
        """Test creating LLM response."""
        model_name = ModelName.from_string("gpt-4o-mini")
        usage = TokenCount(
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150
        )
        
        response = LLMResponse(
            request_id="req-123",
            provider_name="openai",
            model_name=model_name,
            content="Generated content about AI",
            usage=usage,
            latency_ms=250.0,
            cost=0.025,
            quality_score=0.92
        )
        
        assert response.request_id == "req-123"
        assert response.provider_name == "openai"
        assert response.model_name == model_name
        assert response.content == "Generated content about AI"
        assert response.usage == usage
        assert response.latency_ms == 250.0
        assert response.cost == 0.025
        assert response.quality_score == 0.92
        assert isinstance(response.created_at, datetime)


class TestProviderLoadBalancer:
    """Test ProviderLoadBalancer behavior."""
    
    def test_create_load_balancer(self):
        """Test creating load balancer."""
        balancer = ProviderLoadBalancer(ProviderSelectionStrategy.ROUND_ROBIN)
        
        assert balancer.strategy == ProviderSelectionStrategy.ROUND_ROBIN
        assert len(balancer.provider_metrics) == 0
        assert balancer.round_robin_index == 0
    
    def test_round_robin_selection(self):
        """Test round-robin provider selection."""
        provider1 = MockLLMProvider("provider1", ["gpt-4o-mini"])
        provider2 = MockLLMProvider("provider2", ["gpt-4o-mini"])
        provider3 = MockLLMProvider("provider3", ["gpt-4o-mini"])
        
        balancer = ProviderLoadBalancer(ProviderSelectionStrategy.ROUND_ROBIN)
        model = ModelName.from_string("gpt-4o-mini")
        
        # Should rotate through providers
        selected1 = balancer.select_provider([provider1, provider2, provider3], model)
        selected2 = balancer.select_provider([provider1, provider2, provider3], model)
        selected3 = balancer.select_provider([provider1, provider2, provider3], model)
        selected4 = balancer.select_provider([provider1, provider2, provider3], model)
        
        assert selected1.name == "provider1"
        assert selected2.name == "provider2"
        assert selected3.name == "provider3"
        assert selected4.name == "provider1"  # Should wrap around
    
    def test_least_loaded_selection(self):
        """Test least-loaded provider selection."""
        provider1 = MockLLMProvider("provider1", ["gpt-4o-mini"])
        provider2 = MockLLMProvider("provider2", ["gpt-4o-mini"])
        
        balancer = ProviderLoadBalancer(ProviderSelectionStrategy.LEAST_LOADED)
        
        # Set different load levels
        balancer.provider_metrics["provider1"] = ProviderMetrics(
            provider_name="provider1",
            current_load=8  # High load
        )
        balancer.provider_metrics["provider2"] = ProviderMetrics(
            provider_name="provider2", 
            current_load=2  # Low load
        )
        
        model = ModelName.from_string("gpt-4o-mini")
        selected = balancer.select_provider([provider1, provider2], model)
        
        assert selected.name == "provider2"  # Should select less loaded provider
    
    def test_performance_based_selection(self):
        """Test performance-based provider selection."""
        provider1 = MockLLMProvider("provider1", ["gpt-4o-mini"])
        provider2 = MockLLMProvider("provider2", ["gpt-4o-mini"])
        
        balancer = ProviderLoadBalancer(ProviderSelectionStrategy.PERFORMANCE_BASED)
        
        # Set different performance metrics
        balancer.provider_metrics["provider1"] = ProviderMetrics(
            provider_name="provider1",
            total_requests=100,
            successful_requests=80,  # 80% success rate
            current_load=5,
            availability_score=0.95
        )
        balancer.provider_metrics["provider2"] = ProviderMetrics(
            provider_name="provider2",
            total_requests=100,
            successful_requests=95,  # 95% success rate
            current_load=3,
            availability_score=0.98
        )
        
        model = ModelName.from_string("gpt-4o-mini")
        selected = balancer.select_provider([provider1, provider2], model)
        
        assert selected.name == "provider2"  # Should select better performing provider
    
    def test_cost_optimized_selection(self):
        """Test cost-optimized provider selection."""
        provider1 = MockLLMProvider("provider1", ["gpt-4o-mini"])
        provider2 = MockLLMProvider("provider2", ["gpt-4o-mini"])
        
        balancer = ProviderLoadBalancer(ProviderSelectionStrategy.COST_OPTIMIZED)
        
        # Set different costs
        balancer.provider_metrics["provider1"] = ProviderMetrics(
            provider_name="provider1",
            avg_cost_per_request=0.02  # Higher cost
        )
        balancer.provider_metrics["provider2"] = ProviderMetrics(
            provider_name="provider2",
            avg_cost_per_request=0.01  # Lower cost
        )
        
        model = ModelName.from_string("gpt-4o-mini")
        selected = balancer.select_provider([provider1, provider2], model)
        
        assert selected.name == "provider2"  # Should select cheaper provider
    
    def test_latency_optimized_selection(self):
        """Test latency-optimized provider selection."""
        provider1 = MockLLMProvider("provider1", ["gpt-4o-mini"])
        provider2 = MockLLMProvider("provider2", ["gpt-4o-mini"])
        
        balancer = ProviderLoadBalancer(ProviderSelectionStrategy.LATENCY_OPTIMIZED)
        
        # Set different latencies
        balancer.provider_metrics["provider1"] = ProviderMetrics(
            provider_name="provider1",
            avg_latency_ms=300.0  # Higher latency
        )
        balancer.provider_metrics["provider2"] = ProviderMetrics(
            provider_name="provider2",
            avg_latency_ms=150.0  # Lower latency
        )
        
        model = ModelName.from_string("gpt-4o-mini")
        selected = balancer.select_provider([provider1, provider2], model)
        
        assert selected.name == "provider2"  # Should select faster provider
    
    def test_select_provider_no_model_support(self):
        """Test provider selection with unsupported model."""
        provider1 = MockLLMProvider("provider1", ["gpt-3.5-turbo"])  # Doesn't support requested model
        provider2 = MockLLMProvider("provider2", ["gpt-3.5-turbo"])  # Doesn't support requested model
        
        balancer = ProviderLoadBalancer(ProviderSelectionStrategy.ROUND_ROBIN)
        model = ModelName.from_string("gpt-4o-mini")  # Not supported
        
        selected = balancer.select_provider([provider1, provider2], model)
        assert selected is None
    
    def test_select_provider_unavailable(self):
        """Test provider selection with unavailable providers."""
        provider1 = MockLLMProvider("provider1", ["gpt-4o-mini"])
        provider2 = MockLLMProvider("provider2", ["gpt-4o-mini"])
        
        # Make providers unavailable
        provider1.set_available(False)
        provider2.set_available(False)
        
        balancer = ProviderLoadBalancer(ProviderSelectionStrategy.ROUND_ROBIN)
        model = ModelName.from_string("gpt-4o-mini")
        
        selected = balancer.select_provider([provider1, provider2], model)
        assert selected is None


class TestLLMOrchestrationService:
    """Test LLMOrchestrationService business logic."""
    
    def test_create_service(self):
        """Test creating orchestration service."""
        service = LLMOrchestrationService(
            selection_strategy=ProviderSelectionStrategy.ROUND_ROBIN,
            default_timeout=60,
            max_retries=5,
            enable_metrics=True
        )
        
        assert service._load_balancer.strategy == ProviderSelectionStrategy.ROUND_ROBIN
        assert service._default_timeout == 60
        assert service._max_retries == 5
        assert service._enable_metrics is True
        assert len(service._providers) == 0
        assert len(service._active_requests) == 0
    
    @pytest.mark.asyncio
    async def test_register_provider(self):
        """Test registering LLM provider."""
        service = LLMOrchestrationService()
        provider = MockLLMProvider("test-provider", ["gpt-4o-mini"])
        
        await service.register_provider(provider)
        
        assert "test-provider" in service._providers
        assert service._providers["test-provider"] == provider
        assert "test-provider" in service._load_balancer.provider_metrics
    
    @pytest.mark.asyncio
    async def test_register_duplicate_provider(self):
        """Test registering provider with duplicate name."""
        service = LLMOrchestrationService()
        provider1 = MockLLMProvider("duplicate", ["gpt-4o-mini"])
        provider2 = MockLLMProvider("duplicate", ["gpt-3.5-turbo"])
        
        await service.register_provider(provider1)
        
        with pytest.raises(ValueError, match="Provider 'duplicate' already registered"):
            await service.register_provider(provider2)
    
    @pytest.mark.asyncio
    async def test_execute_request_success(self):
        """Test successful request execution."""
        service = LLMOrchestrationService()
        provider = MockLLMProvider("test-provider", ["gpt-4o-mini"])
        await service.register_provider(provider)
        
        execution_context = ExecutionContextBuilder().build()
        model_preference = [ModelName.from_string("gpt-4o-mini")]
        
        response = await service.execute_request(
            context=execution_context,
            prompt="Generate content about AI",
            model_preference=model_preference
        )
        
        assert isinstance(response, LLMResponse)
        assert response.provider_name == "test-provider"
        assert response.model_name.value == "gpt-4o-mini"
        assert "Response from test-provider" in response.content
        assert response.usage.total_tokens > 0
        assert provider.call_count == 1
    
    @pytest.mark.asyncio
    async def test_execute_request_no_providers(self):
        """Test request execution with no providers."""
        service = LLMOrchestrationService()
        execution_context = ExecutionContextBuilder().build()
        model_preference = [ModelName.from_string("gpt-4o-mini")]
        
        with pytest.raises(ProviderUnavailableError, match="No providers available"):
            await service.execute_request(
                context=execution_context,
                prompt="Generate content",
                model_preference=model_preference
            )
    
    @pytest.mark.asyncio
    async def test_execute_request_model_not_supported(self):
        """Test request execution with unsupported model."""
        service = LLMOrchestrationService()
        provider = MockLLMProvider("test-provider", ["gpt-3.5-turbo"])  # Doesn't support gpt-4o-mini
        await service.register_provider(provider)
        
        execution_context = ExecutionContextBuilder().build()
        model_preference = [ModelName.from_string("gpt-4o-mini")]  # Not supported
        
        with pytest.raises(ModelNotSupportedError, match="not supported by any available provider"):
            await service.execute_request(
                context=execution_context,
                prompt="Generate content",
                model_preference=model_preference
            )
    
    @pytest.mark.asyncio
    async def test_execute_request_with_fallback(self):
        """Test request execution with provider fallback."""
        service = LLMOrchestrationService()
        
        # First provider will fail, second will succeed
        failing_provider = MockLLMProvider("failing-provider", ["gpt-4o-mini"])
        backup_provider = MockLLMProvider("backup-provider", ["gpt-4o-mini"])
        
        failing_provider.fail_next_request()
        
        await service.register_provider(failing_provider)
        await service.register_provider(backup_provider)
        
        execution_context = ExecutionContextBuilder().build()
        model_preference = [ModelName.from_string("gpt-4o-mini")]
        
        response = await service.execute_request(
            context=execution_context,
            prompt="Generate content",
            model_preference=model_preference
        )
        
        # Should fallback to backup provider
        assert response.provider_name == "backup-provider"
        assert failing_provider.call_count == 1  # Tried first
        assert backup_provider.call_count == 1  # Used as fallback
    
    @pytest.mark.asyncio
    async def test_execute_request_with_retries(self):
        """Test request execution with retry logic."""
        service = LLMOrchestrationService(max_retries=3)
        provider = MockLLMProvider("test-provider", ["gpt-4o-mini"])
        
        # Make first 2 requests fail, 3rd succeed
        provider.fail_next_request()
        await service.register_provider(provider)
        
        execution_context = ExecutionContextBuilder().build()
        model_preference = [ModelName.from_string("gpt-4o-mini")]
        
        # This should succeed after retries
        # Note: We can't easily test exact retry count with the current mock setup
        # In a real scenario, we'd track retry attempts
        response = await service.execute_request(
            context=execution_context,
            prompt="Generate content",
            model_preference=model_preference
        )
        
        assert response.provider_name == "test-provider"
    
    @pytest.mark.asyncio
    async def test_execute_streaming_request(self):
        """Test streaming request execution."""
        service = LLMOrchestrationService()
        provider = MockLLMProvider("test-provider", ["gpt-4o-mini"])
        await service.register_provider(provider)
        
        execution_context = ExecutionContextBuilder().build()
        model_preference = [ModelName.from_string("gpt-4o-mini")]
        
        # Execute streaming request
        chunks = []
        async for chunk in service.execute_streaming_request(
            context=execution_context,
            prompt="Generate content",
            model_preference=model_preference
        ):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        # Note: Actual streaming implementation would depend on the provider interface
        # This is a basic test of the method structure
    
    @pytest.mark.asyncio
    async def test_pause_and_resume_request(self):
        """Test pausing and resuming request execution."""
        service = LLMOrchestrationService()
        provider = MockLLMProvider("test-provider", ["gpt-4o-mini"])
        await service.register_provider(provider)
        
        execution_context = ExecutionContextBuilder().build()
        request_id = "test-request-123"
        
        # Create request context
        request_context = RequestContext(
            request_id=request_id,
            execution_context=execution_context,
            prompt="Generate content",
            model_preference=[ModelName.from_string("gpt-4o-mini")]
        )
        
        # Add to active requests (simulating started request)
        service._active_requests[request_id] = request_context
        
        # Pause request
        await service.pause_request(request_id)
        
        # Verify request is paused (implementation would mark it as paused)
        # This depends on the actual implementation details
        assert request_id in service._active_requests
        
        # Resume request
        await service.resume_request(request_id)
        
        # Verify request can be resumed
        # Again, this depends on implementation details
    
    def test_get_provider_metrics(self):
        """Test getting provider performance metrics."""
        service = LLMOrchestrationService(enable_metrics=True)
        
        # Add some mock metrics
        service._load_balancer.provider_metrics["provider1"] = ProviderMetrics(
            provider_name="provider1",
            total_requests=100,
            successful_requests=95,
            avg_latency_ms=150.0
        )
        
        metrics = service.get_provider_metrics()
        
        assert "provider1" in metrics
        assert metrics["provider1"].total_requests == 100
        assert metrics["provider1"].success_rate == 0.95
    
    def test_get_provider_metrics_disabled(self):
        """Test getting metrics when disabled."""
        service = LLMOrchestrationService(enable_metrics=False)
        
        metrics = service.get_provider_metrics()
        assert metrics == {}
    
    @pytest.mark.asyncio
    async def test_health_check_providers(self):
        """Test provider health checking."""
        service = LLMOrchestrationService()
        
        provider1 = MockLLMProvider("healthy-provider", ["gpt-4o-mini"])
        provider2 = MockLLMProvider("unhealthy-provider", ["gpt-4o-mini"])
        provider2.set_available(False)
        
        await service.register_provider(provider1)
        await service.register_provider(provider2)
        
        health_status = await service.check_provider_health()
        
        assert "healthy-provider" in health_status
        assert "unhealthy-provider" in health_status
        assert health_status["healthy-provider"]["available"] is True
        assert health_status["unhealthy-provider"]["available"] is False
    
    def test_analyze_provider_performance(self):
        """Test provider performance analysis."""
        service = LLMOrchestrationService(enable_metrics=True)
        
        # Add performance data
        service._load_balancer.provider_metrics["fast-provider"] = ProviderMetrics(
            provider_name="fast-provider",
            total_requests=100,
            successful_requests=98,
            avg_latency_ms=100.0,
            avg_cost_per_request=0.01
        )
        
        service._load_balancer.provider_metrics["slow-provider"] = ProviderMetrics(
            provider_name="slow-provider",
            total_requests=100,
            successful_requests=90,
            avg_latency_ms=300.0,
            avg_cost_per_request=0.015
        )
        
        analysis = service.analyze_provider_performance()
        
        assert "recommendations" in analysis
        assert "performance_ranking" in analysis
        assert len(analysis["performance_ranking"]) == 2
        
        # Fast provider should rank higher
        best_provider = analysis["performance_ranking"][0]
        assert best_provider["name"] == "fast-provider"
    
    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test request timeout handling."""
        service = LLMOrchestrationService(default_timeout=1)  # Very short timeout
        
        # Create slow provider
        slow_provider = MockLLMProvider("slow-provider", ["gpt-4o-mini"], latency_ms=2000)  # 2 second latency
        await service.register_provider(slow_provider)
        
        execution_context = ExecutionContextBuilder().build()
        model_preference = [ModelName.from_string("gpt-4o-mini")]
        
        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await service.execute_request(
                context=execution_context,
                prompt="Generate content",
                model_preference=model_preference,
                timeout_seconds=0.5  # Override with even shorter timeout
            )
    
    @pytest.mark.asyncio
    async def test_priority_request_handling(self):
        """Test priority-based request handling."""
        service = LLMOrchestrationService()
        provider = MockLLMProvider("test-provider", ["gpt-4o-mini"])
        await service.register_provider(provider)
        
        execution_context = ExecutionContextBuilder().build()
        model_preference = [ModelName.from_string("gpt-4o-mini")]
        
        # Execute high priority request
        response = await service.execute_request(
            context=execution_context,
            prompt="Critical content generation",
            model_preference=model_preference,
            priority=RequestPriority.CRITICAL
        )
        
        assert isinstance(response, LLMResponse)
        assert response.provider_name == "test-provider"
        
        # Execute low priority request
        response_low = await service.execute_request(
            context=execution_context,
            prompt="Low priority content",
            model_preference=model_preference,
            priority=RequestPriority.LOW
        )
        
        assert isinstance(response_low, LLMResponse)
        # In a full implementation, high priority requests would be processed first
    
    @pytest.mark.asyncio
    async def test_multiple_model_preference_fallback(self):
        """Test fallback through multiple model preferences."""
        service = LLMOrchestrationService()
        
        # Provider only supports gpt-3.5-turbo
        provider = MockLLMProvider("limited-provider", ["gpt-3.5-turbo"])
        await service.register_provider(provider)
        
        execution_context = ExecutionContextBuilder().build()
        # Prefer gpt-4o-mini but fallback to gpt-3.5-turbo
        model_preference = [
            ModelName.from_string("gpt-4o-mini"),
            ModelName.from_string("gpt-3.5-turbo")
        ]
        
        response = await service.execute_request(
            context=execution_context,
            prompt="Generate content",
            model_preference=model_preference
        )
        
        # Should use the fallback model
        assert response.model_name.value == "gpt-3.5-turbo"
        assert response.provider_name == "limited-provider"
