"""LLM Orchestration Service.

Provides comprehensive LLM management including multi-provider orchestration,
intelligent fallback management, rate limiting, and performance optimization.
"""

import asyncio
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple, AsyncIterator
from enum import Enum
from collections import defaultdict, deque

from ..entities.execution_context import ExecutionContext
from ..entities.llm_provider import LLMProvider, ProviderStatus, ProviderType
from ..value_objects.model_name import ModelName
from ..value_objects.token_count import TokenCount
from ....infrastructure.llm.provider_factory import ProviderFactory
from ....infrastructure.llm.base_provider import LLMRequest, LLMResponse, StreamingChunk


class ProviderSelectionStrategy(str, Enum):
    """Strategy for selecting LLM providers."""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    PERFORMANCE_BASED = "performance_based"
    COST_OPTIMIZED = "cost_optimized"
    LATENCY_OPTIMIZED = "latency_optimized"


class FallbackTrigger(str, Enum):
    """Triggers for provider fallback."""
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    QUALITY_THRESHOLD = "quality_threshold"
    COST_THRESHOLD = "cost_threshold"


class RequestPriority(str, Enum):
    """Priority levels for LLM requests."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ProviderMetrics:
    """Real-time provider performance metrics."""
    provider_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    avg_tokens_per_second: float = 0.0
    avg_cost_per_request: float = 0.0
    error_rate: float = 0.0
    current_load: int = 0
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset_time: Optional[datetime] = None
    last_request_time: Optional[datetime] = None
    last_error_time: Optional[datetime] = None
    last_error_message: Optional[str] = None
    quality_score: float = 1.0  # 0.0 to 1.0
    availability_score: float = 1.0  # 0.0 to 1.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def is_available(self) -> bool:
        """Check if provider is available for requests."""
        # Check rate limits
        if (self.rate_limit_remaining is not None and 
            self.rate_limit_remaining <= 0 and
            self.rate_limit_reset_time and
            datetime.now() < self.rate_limit_reset_time):
            return False
        
        # Check if too many recent errors
        if self.error_rate > 0.5:  # More than 50% error rate
            return False
            
        return True
    
    @property
    def load_factor(self) -> float:
        """Calculate current load factor (0.0 to 1.0)."""
        # Simple load calculation based on current requests
        max_concurrent = 10  # Assume max 10 concurrent requests per provider
        return min(self.current_load / max_concurrent, 1.0)


@dataclass
class RequestContext:
    """Context for a specific LLM request."""
    request_id: str
    execution_context: ExecutionContext
    prompt: str
    model_preference: List[ModelName]
    priority: RequestPriority = RequestPriority.NORMAL
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    streaming: bool = False
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    stop_sequences: Optional[List[str]] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM response with metadata."""
    request_id: str
    provider_name: str
    model_name: ModelName
    content: str
    usage: TokenCount
    latency_ms: float
    cost: float
    quality_score: float
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderLoadBalancer:
    """Load balancer for provider selection."""
    strategy: ProviderSelectionStrategy
    provider_metrics: Dict[str, ProviderMetrics] = field(default_factory=dict)
    round_robin_index: int = 0
    
    def select_provider(
        self, 
        providers: List[LLMProvider], 
        model: ModelName,
        priority: RequestPriority = RequestPriority.NORMAL
    ) -> Optional[LLMProvider]:
        """Select best provider based on strategy."""
        # Filter providers that support the model and are available
        available_providers = [
            p for p in providers 
            if p.supports_model(model) and p.is_available
            and self.provider_metrics.get(p.name, ProviderMetrics(p.name)).is_available
        ]
        
        if not available_providers:
            return None
            
        if self.strategy == ProviderSelectionStrategy.ROUND_ROBIN:
            return self._round_robin_selection(available_providers)
        elif self.strategy == ProviderSelectionStrategy.LEAST_LOADED:
            return self._least_loaded_selection(available_providers)
        elif self.strategy == ProviderSelectionStrategy.PERFORMANCE_BASED:
            return self._performance_based_selection(available_providers)
        elif self.strategy == ProviderSelectionStrategy.COST_OPTIMIZED:
            return self._cost_optimized_selection(available_providers)
        elif self.strategy == ProviderSelectionStrategy.LATENCY_OPTIMIZED:
            return self._latency_optimized_selection(available_providers)
        else:
            return available_providers[0]
    
    def _round_robin_selection(self, providers: List[LLMProvider]) -> LLMProvider:
        """Round-robin provider selection."""
        provider = providers[self.round_robin_index % len(providers)]
        self.round_robin_index = (self.round_robin_index + 1) % len(providers)
        return provider
    
    def _least_loaded_selection(self, providers: List[LLMProvider]) -> LLMProvider:
        """Select provider with least current load."""
        return min(providers, key=lambda p: self._get_metrics(p.name).load_factor)
    
    def _performance_based_selection(self, providers: List[LLMProvider]) -> LLMProvider:
        """Select provider based on overall performance score."""
        def performance_score(provider: LLMProvider) -> float:
            metrics = self._get_metrics(provider.name)
            # Combine success rate, latency, and availability
            return (metrics.success_rate * 0.4 + 
                   (1.0 - metrics.load_factor) * 0.3 + 
                   metrics.availability_score * 0.3)
        
        return max(providers, key=performance_score)
    
    def _cost_optimized_selection(self, providers: List[LLMProvider]) -> LLMProvider:
        """Select provider with lowest cost per request."""
        return min(providers, key=lambda p: self._get_metrics(p.name).avg_cost_per_request)
    
    def _latency_optimized_selection(self, providers: List[LLMProvider]) -> LLMProvider:
        """Select provider with lowest latency."""
        return min(providers, key=lambda p: self._get_metrics(p.name).avg_latency_ms)
    
    def _get_metrics(self, provider_name: str) -> ProviderMetrics:
        """Get or create metrics for provider."""
        if provider_name not in self.provider_metrics:
            self.provider_metrics[provider_name] = ProviderMetrics(provider_name)
        return self.provider_metrics[provider_name]


class LLMOrchestrationError(Exception):
    """Base exception for LLM orchestration errors."""
    pass


class ProviderUnavailableError(LLMOrchestrationError):
    """Raised when no providers are available."""
    pass


class ModelNotSupportedError(LLMOrchestrationError):
    """Raised when requested model is not supported by any provider."""
    pass


class RateLimitExceededError(LLMOrchestrationError):
    """Raised when rate limits are exceeded."""
    pass


class ProviderExecutionError(LLMOrchestrationError):
    """Raised when provider execution fails."""
    pass


class LLMOrchestrationService:
    """Service for orchestrating LLM providers and managing execution.
    
    Provides comprehensive LLM management including:
    - Multi-provider integration and orchestration
    - Intelligent fallback management
    - Load balancing and request routing
    - Rate limiting and quota management
    - Performance monitoring and optimization
    - Quality assessment and provider ranking
    
    Examples:
        service = LLMOrchestrationService()
        
        # Register providers
        await service.register_provider(openai_provider)
        await service.register_provider(anthropic_provider)
        
        # Execute request with automatic provider selection
        response = await service.execute_request(
            context=execution_context,
            prompt="Generate article outline",
            model_preference=[ModelName.from_string("gpt-4o-mini")]
        )
        
        # Get provider analytics
        metrics = service.get_provider_metrics()
        performance = service.analyze_provider_performance()
    """
    
    def __init__(
        self,
        provider_factory: Optional[ProviderFactory] = None,
        selection_strategy: ProviderSelectionStrategy = ProviderSelectionStrategy.PERFORMANCE_BASED,
        default_timeout: int = 30,
        max_retries: int = 3,
        enable_metrics: bool = True
    ) -> None:
        """Initialize LLM orchestration service.
        
        Args:
            provider_factory: Factory for creating LLM providers
            selection_strategy: Strategy for provider selection
            default_timeout: Default request timeout in seconds
            max_retries: Maximum retry attempts
            enable_metrics: Whether to collect performance metrics
        """
        self._provider_factory = provider_factory or ProviderFactory()
        self._providers: Dict[str, LLMProvider] = {}
        self._infrastructure_providers: Dict[str, Any] = {}  # Actual provider instances
        self._load_balancer = ProviderLoadBalancer(selection_strategy)
        self._default_timeout = default_timeout
        self._max_retries = max_retries
        self._enable_metrics = enable_metrics
        self._request_queue: Dict[RequestPriority, deque] = {
            priority: deque() for priority in RequestPriority
        }
        self._active_requests: Dict[str, RequestContext] = {}
        self._rate_limiters: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._health_check_interval = 60  # seconds
        self._last_health_check: Optional[datetime] = None
    
    async def register_provider(self, provider: LLMProvider) -> None:
        """Register a new LLM provider.
        
        Args:
            provider: Provider to register
            
        Raises:
            ValueError: If provider name already exists
        """
        if provider.name in self._providers:
            raise ValueError(f"Provider '{provider.name}' already registered")
        
        self._providers[provider.name] = provider
        
        # Create and register infrastructure provider
        try:
            infrastructure_provider = self._provider_factory.create_provider(
                provider.provider_type, 
                provider.configuration or {}
            )
            await infrastructure_provider.initialize()
            self._infrastructure_providers[provider.name] = infrastructure_provider
        except Exception as e:
            raise ValueError(f"Failed to initialize provider '{provider.name}': {e}")
        
        # Initialize metrics
        if self._enable_metrics:
            self._load_balancer.provider_metrics[provider.name] = ProviderMetrics(provider.name)
        
        # Perform initial health check
        await self._health_check_provider(provider)
    
    async def unregister_provider(self, provider_name: str) -> None:
        """Unregister an LLM provider.
        
        Args:
            provider_name: Name of provider to unregister
        """
        if provider_name in self._providers:
            del self._providers[provider_name]
            
        if provider_name in self._infrastructure_providers:
            del self._infrastructure_providers[provider_name]
            
        if provider_name in self._load_balancer.provider_metrics:
            del self._load_balancer.provider_metrics[provider_name]
    
    async def execute_request(
        self,
        context: ExecutionContext,
        prompt: str,
        model_preference: List[ModelName],
        priority: RequestPriority = RequestPriority.NORMAL,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        streaming: bool = False,
        timeout_seconds: Optional[int] = None
    ) -> LLMResponse:
        """Execute LLM request with automatic provider selection.
        
        Args:
            context: Execution context
            prompt: Prompt text
            model_preference: Preferred models in order
            priority: Request priority
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            streaming: Whether to stream response
            timeout_seconds: Request timeout
            
        Returns:
            LLM response with metadata
            
        Raises:
            ProviderUnavailableError: If no providers available
            ModelNotSupportedError: If model not supported
            RateLimitExceededError: If rate limits exceeded
        """
        request_id = f"req_{int(time.time() * 1000)}"
        
        request_ctx = RequestContext(
            request_id=request_id,
            execution_context=context,
            prompt=prompt,
            model_preference=model_preference,
            priority=priority,
            max_tokens=max_tokens,
            temperature=temperature,
            streaming=streaming,
            timeout_seconds=timeout_seconds or self._default_timeout
        )
        
        try:
            self._active_requests[request_id] = request_ctx
            return await self._execute_with_fallback(request_ctx)
        finally:
            self._active_requests.pop(request_id, None)
    
    async def execute_streaming_request(
        self,
        context: ExecutionContext,
        prompt: str,
        model_preference: List[ModelName],
        priority: RequestPriority = RequestPriority.NORMAL,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout_seconds: Optional[int] = None
    ) -> AsyncIterator[str]:
        """Execute streaming LLM request.
        
        Args:
            context: Execution context
            prompt: Prompt text
            model_preference: Preferred models in order
            priority: Request priority
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            timeout_seconds: Request timeout
            
        Yields:
            Response chunks as they arrive
            
        Raises:
            ProviderUnavailableError: If no providers available
            ModelNotSupportedError: If model not supported
        """
        request_id = f"stream_{int(time.time() * 1000)}"
        
        request_ctx = RequestContext(
            request_id=request_id,
            execution_context=context,
            prompt=prompt,
            model_preference=model_preference,
            priority=priority,
            max_tokens=max_tokens,
            temperature=temperature,
            streaming=True,
            timeout_seconds=timeout_seconds or self._default_timeout
        )
        
        try:
            self._active_requests[request_id] = request_ctx
            async for chunk in self._execute_streaming_with_fallback(request_ctx):
                yield chunk
        finally:
            self._active_requests.pop(request_id, None)
    
    async def _execute_with_fallback(self, request_ctx: RequestContext) -> LLMResponse:
        """Execute request with automatic fallback."""
        last_error = None
        
        for model in request_ctx.model_preference:
            try:
                provider = self._load_balancer.select_provider(
                    list(self._providers.values()),
                    model,
                    request_ctx.priority
                )
                
                if not provider:
                    continue
                
                # Check rate limits
                if not await self._check_rate_limits(provider):
                    await self._record_rate_limit_hit(provider)
                    continue
                
                start_time = time.time()
                response = await self._execute_on_provider(request_ctx, provider, model)
                latency_ms = (time.time() - start_time) * 1000
                
                # Update metrics
                if self._enable_metrics:
                    await self._update_success_metrics(provider, latency_ms, response)
                
                return response
                
            except Exception as e:
                last_error = e
                if self._enable_metrics:
                    await self._update_error_metrics(provider, str(e))
                continue
        
        # All providers failed
        if last_error:
            raise last_error
        else:
            raise ProviderUnavailableError("No available providers for requested models")
    
    async def _execute_streaming_with_fallback(self, request_ctx: RequestContext) -> AsyncIterator[str]:
        """Execute streaming request with fallback."""
        for model in request_ctx.model_preference:
            try:
                provider = self._load_balancer.select_provider(
                    list(self._providers.values()),
                    model,
                    request_ctx.priority
                )
                
                if not provider:
                    continue
                
                if not await self._check_rate_limits(provider):
                    continue
                
                async for chunk in self._execute_streaming_on_provider(request_ctx, provider, model):
                    yield chunk
                return
                
            except Exception:
                continue
        
        raise ProviderUnavailableError("No available providers for streaming request")
    
    async def _execute_on_provider(
        self, 
        request_ctx: RequestContext, 
        provider: LLMProvider, 
        model: ModelName
    ) -> LLMResponse:
        """Execute request on specific provider."""
        infrastructure_provider = self._infrastructure_providers.get(provider.name)
        if not infrastructure_provider:
            raise ProviderUnavailableError(f"Infrastructure provider '{provider.name}' not available")
        
        start_time = time.time()
        
        try:
            # Create infrastructure request
            llm_request = LLMRequest(
                prompt=request_ctx.prompt,
                model=str(model),
                max_tokens=request_ctx.max_tokens,
                temperature=request_ctx.temperature,
                stop_sequences=request_ctx.stop_sequences
            )
            
            # Execute request through infrastructure provider
            infra_response = await infrastructure_provider.generate(llm_request)
            
            # Convert to domain response
            latency_ms = (time.time() - start_time) * 1000
            
            usage = TokenCount.create(
                prompt_tokens=infra_response.token_usage.prompt_tokens,
                completion_tokens=infra_response.token_usage.completion_tokens,
                total_tokens=infra_response.token_usage.total_tokens
            )
            
            # Calculate cost if available
            model_info = infrastructure_provider.get_model_info(str(model))
            cost = 0.0
            if model_info:
                cost = (
                    (infra_response.token_usage.prompt_tokens / 1000) * model_info.input_cost_per_1k +
                    (infra_response.token_usage.completion_tokens / 1000) * model_info.output_cost_per_1k
                )
            
            return LLMResponse(
                request_id=request_ctx.request_id,
                provider_name=provider.name,
                model_name=model,
                content=infra_response.content,
                usage=usage,
                latency_ms=latency_ms,
                cost=cost,
                quality_score=0.9  # TODO: Implement quality scoring
            )
            
        except Exception as e:
            raise ProviderExecutionError(f"Execution failed on provider '{provider.name}': {e}")
    
    async def _execute_streaming_on_provider(
        self, 
        request_ctx: RequestContext, 
        provider: LLMProvider, 
        model: ModelName
    ) -> AsyncIterator[str]:
        """Execute streaming request on specific provider."""
        infrastructure_provider = self._infrastructure_providers.get(provider.name)
        if not infrastructure_provider:
            raise ProviderUnavailableError(f"Infrastructure provider '{provider.name}' not available")
        
        try:
            # Create infrastructure request
            llm_request = LLMRequest(
                prompt=request_ctx.prompt,
                model=str(model),
                max_tokens=request_ctx.max_tokens,
                temperature=request_ctx.temperature,
                stop_sequences=request_ctx.stop_sequences
            )
            
            # Execute streaming request through infrastructure provider
            async for chunk in infrastructure_provider.generate_stream(llm_request):
                if chunk.content:
                    yield chunk.content
                    
        except Exception as e:
            raise ProviderExecutionError(f"Streaming execution failed on provider '{provider.name}': {e}")
    
    async def _check_rate_limits(self, provider: LLMProvider) -> bool:
        """Check if provider is within rate limits."""
        provider_limits = self._rate_limiters.get(provider.name, {})
        
        # Simple rate limiting check
        requests_per_minute = provider.get_rate_limit("requests_per_minute")
        if requests_per_minute:
            current_minute = int(time.time() // 60)
            minute_key = f"requests_{current_minute}"
            
            current_count = provider_limits.get(minute_key, 0)
            if current_count >= requests_per_minute:
                return False
            
            provider_limits[minute_key] = current_count + 1
            self._rate_limiters[provider.name] = provider_limits
        
        return True
    
    async def _record_rate_limit_hit(self, provider: LLMProvider) -> None:
        """Record rate limit hit for provider."""
        if self._enable_metrics:
            metrics = self._load_balancer._get_metrics(provider.name)
            metrics.rate_limit_remaining = 0
            metrics.rate_limit_reset_time = datetime.now() + timedelta(minutes=1)
    
    async def _update_success_metrics(
        self, 
        provider: LLMProvider, 
        latency_ms: float, 
        response: LLMResponse
    ) -> None:
        """Update provider success metrics."""
        metrics = self._load_balancer._get_metrics(provider.name)
        
        metrics.total_requests += 1
        metrics.successful_requests += 1
        
        # Update moving average latency
        if metrics.avg_latency_ms == 0:
            metrics.avg_latency_ms = latency_ms
        else:
            metrics.avg_latency_ms = (metrics.avg_latency_ms * 0.9) + (latency_ms * 0.1)
        
        # Update cost
        metrics.avg_cost_per_request = (metrics.avg_cost_per_request * 0.9) + (response.cost * 0.1)
        
        # Update quality score
        metrics.quality_score = (metrics.quality_score * 0.9) + (response.quality_score * 0.1)
        
        metrics.last_request_time = datetime.now()
        metrics.error_rate = 1.0 - metrics.success_rate
    
    async def _update_error_metrics(self, provider: LLMProvider, error_message: str) -> None:
        """Update provider error metrics."""
        metrics = self._load_balancer._get_metrics(provider.name)
        
        metrics.total_requests += 1
        metrics.failed_requests += 1
        metrics.last_error_time = datetime.now()
        metrics.last_error_message = error_message
        metrics.error_rate = 1.0 - metrics.success_rate
    
    async def _health_check_provider(self, provider: LLMProvider) -> None:
        """Perform health check on provider."""
        try:
            # Simple health check - could be enhanced with actual API calls
            if provider.status == ProviderStatus.ACTIVE:
                metrics = self._load_balancer._get_metrics(provider.name)
                metrics.availability_score = 1.0
            else:
                metrics = self._load_balancer._get_metrics(provider.name)
                metrics.availability_score = 0.0
        except Exception:
            metrics = self._load_balancer._get_metrics(provider.name)
            metrics.availability_score = 0.0
    
    async def health_check_all_providers(self) -> Dict[str, bool]:
        """Perform health check on all providers.
        
        Returns:
            Dict mapping provider names to health status
        """
        results = {}
        
        for provider in self._providers.values():
            try:
                await self._health_check_provider(provider)
                results[provider.name] = provider.is_healthy
            except Exception:
                results[provider.name] = False
        
        self._last_health_check = datetime.now()
        return results
    
    def get_provider_metrics(self) -> Dict[str, ProviderMetrics]:
        """Get current provider metrics.
        
        Returns:
            Dict mapping provider names to their metrics
        """
        return dict(self._load_balancer.provider_metrics)
    
    def get_active_requests(self) -> List[RequestContext]:
        """Get currently active requests.
        
        Returns:
            List of active request contexts
        """
        return list(self._active_requests.values())
    
    def analyze_provider_performance(self) -> Dict[str, Dict[str, Any]]:
        """Analyze provider performance and generate insights.
        
        Returns:
            Dict with performance analysis for each provider
        """
        analysis = {}
        
        for provider_name, metrics in self._load_balancer.provider_metrics.items():
            analysis[provider_name] = {
                "performance_score": (
                    metrics.success_rate * 0.4 + 
                    (1.0 - metrics.load_factor) * 0.3 + 
                    metrics.availability_score * 0.3
                ),
                "reliability": metrics.success_rate,
                "efficiency": 1.0 / max(metrics.avg_latency_ms, 1.0) * 1000,
                "cost_effectiveness": 1.0 / max(metrics.avg_cost_per_request, 0.001),
                "quality": metrics.quality_score,
                "availability": metrics.availability_score,
                "recommendation": self._generate_provider_recommendation(metrics)
            }
        
        return analysis
    
    def _generate_provider_recommendation(self, metrics: ProviderMetrics) -> str:
        """Generate recommendation for provider usage."""
        if metrics.success_rate < 0.8:
            return "Consider reducing usage due to high error rate"
        elif metrics.avg_latency_ms > 5000:
            return "High latency - consider for background tasks only"
        elif metrics.avg_cost_per_request > 0.01:
            return "High cost - use for high-value requests only"
        elif metrics.quality_score > 0.9 and metrics.success_rate > 0.95:
            return "Excellent performance - recommended for critical tasks"
        else:
            return "Good performance - suitable for general use"
    
    def optimize_provider_selection(self) -> Dict[str, Any]:
        """Optimize provider selection strategy based on historical data.
        
        Returns:
            Optimization recommendations
        """
        metrics = self._load_balancer.provider_metrics
        
        if not metrics:
            return {"recommendation": "No data available for optimization"}
        
        # Analyze current strategy effectiveness
        best_performers = sorted(
            metrics.items(),
            key=lambda x: x[1].success_rate * x[1].quality_score,
            reverse=True
        )
        
        recommendations = {
            "current_strategy": self._load_balancer.strategy.value,
            "best_performers": [name for name, _ in best_performers[:3]],
            "optimization_suggestions": []
        }
        
        # Cost optimization
        avg_cost = sum(m.avg_cost_per_request for m in metrics.values()) / len(metrics)
        high_cost_providers = [
            name for name, m in metrics.items() 
            if m.avg_cost_per_request > avg_cost * 1.5
        ]
        
        if high_cost_providers:
            recommendations["optimization_suggestions"].append({
                "type": "cost_optimization",
                "message": f"Consider reducing usage of high-cost providers: {high_cost_providers}",
                "potential_savings": f"{len(high_cost_providers) * 0.001:.3f} per request"
            })
        
        # Performance optimization
        slow_providers = [
            name for name, m in metrics.items() 
            if m.avg_latency_ms > 2000
        ]
        
        if slow_providers:
            recommendations["optimization_suggestions"].append({
                "type": "latency_optimization",
                "message": f"High latency providers: {slow_providers}",
                "suggestion": "Use for non-time-critical requests only"
            })
        
        return recommendations
    
    def set_provider_weights(self, weights: Dict[str, float]) -> None:
        """Set custom weights for provider selection.
        
        Args:
            weights: Dict mapping provider names to selection weights
        """
        # This would modify the load balancer's selection logic
        # Implementation would depend on the specific strategy
        pass
    
    def get_rate_limit_status(self) -> Dict[str, Dict[str, Any]]:
        """Get current rate limit status for all providers.
        
        Returns:
            Dict mapping provider names to rate limit info
        """
        status = {}
        
        for provider_name, provider in self._providers.items():
            metrics = self._load_balancer.provider_metrics.get(provider_name)
            
            status[provider_name] = {
                "requests_per_minute_limit": provider.get_rate_limit("requests_per_minute"),
                "tokens_per_minute_limit": provider.get_rate_limit("tokens_per_minute"),
                "remaining": metrics.rate_limit_remaining if metrics else None,
                "reset_time": metrics.rate_limit_reset_time if metrics else None,
                "is_available": metrics.is_available if metrics else True
            }
        
        return status