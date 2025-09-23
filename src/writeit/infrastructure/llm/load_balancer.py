"""LLM Provider Load Balancer.

Distributes requests across multiple LLM providers with failover and load balancing.
"""

import asyncio
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, AsyncGenerator
from enum import Enum

from .base_provider import BaseLLMProvider, LLMRequest, LLMResponse, StreamingChunk, ProviderError, RateLimitError
from .provider_factory import ProviderFactory
from .health_checker import LLMHealthChecker, HealthStatus
from .rate_limiter import LLMRateLimiter, RateLimitExceededError

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(str, Enum):
    """Load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    FASTEST_RESPONSE = "fastest_response"
    HEALTH_WEIGHTED = "health_weighted"
    RANDOM = "random"
    PRIORITY_FAILOVER = "priority_failover"


@dataclass
class ProviderConfig:
    """Configuration for a provider in the load balancer."""
    
    name: str
    weight: float = 1.0
    priority: int = 1  # Lower number = higher priority
    max_concurrent_requests: int = 100
    timeout: float = 30.0
    enabled: bool = True
    
    # Health and performance tracking
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    active_requests: int = 0
    last_used: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if self.successful_requests == 0:
            return 0.0
        return self.total_response_time / self.successful_requests
    
    def record_request_start(self) -> None:
        """Record that a request has started."""
        self.active_requests += 1
        self.total_requests += 1
        self.last_used = time.time()
    
    def record_request_success(self, response_time: float) -> None:
        """Record a successful request."""
        self.active_requests = max(0, self.active_requests - 1)
        self.successful_requests += 1
        self.total_response_time += response_time
    
    def record_request_failure(self) -> None:
        """Record a failed request."""
        self.active_requests = max(0, self.active_requests - 1)
        self.failed_requests += 1


@dataclass
class LoadBalancerMetrics:
    """Metrics for the load balancer."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    fallback_requests: int = 0
    rate_limited_requests: int = 0
    
    provider_metrics: Dict[str, ProviderConfig] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests


class LLMLoadBalancer:
    """Load balancer for LLM provider requests."""
    
    def __init__(
        self,
        provider_factory: ProviderFactory,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.HEALTH_WEIGHTED,
        health_checker: Optional[LLMHealthChecker] = None,
        rate_limiter: Optional[LLMRateLimiter] = None
    ):
        """Initialize the load balancer.
        
        Args:
            provider_factory: Factory for creating provider instances
            strategy: Load balancing strategy to use
            health_checker: Optional health checker for provider monitoring
            rate_limiter: Optional rate limiter for request throttling
        """
        self.provider_factory = provider_factory
        self.strategy = strategy
        self.health_checker = health_checker
        self.rate_limiter = rate_limiter
        
        self._providers: Dict[str, ProviderConfig] = {}
        self._provider_instances: Dict[str, BaseLLMProvider] = {}
        self._metrics = LoadBalancerMetrics()
        self._round_robin_index = 0
        self._lock = asyncio.Lock()
    
    def add_provider(
        self,
        provider_name: str,
        weight: float = 1.0,
        priority: int = 1,
        max_concurrent_requests: int = 100,
        timeout: float = 30.0
    ) -> None:
        """Add a provider to the load balancer.
        
        Args:
            provider_name: Name of the provider
            weight: Weight for weighted strategies
            priority: Priority for priority-based strategies (lower = higher priority)
            max_concurrent_requests: Maximum concurrent requests for this provider
            timeout: Request timeout for this provider
        """
        config = ProviderConfig(
            name=provider_name,
            weight=weight,
            priority=priority,
            max_concurrent_requests=max_concurrent_requests,
            timeout=timeout
        )
        
        self._providers[provider_name] = config
        self._metrics.provider_metrics[provider_name] = config
        
        # Add to health checker if available
        if self.health_checker:
            self.health_checker.add_provider(provider_name)
        
        logger.info(f"Added provider '{provider_name}' to load balancer with weight {weight}")
    
    def remove_provider(self, provider_name: str) -> None:
        """Remove a provider from the load balancer.
        
        Args:
            provider_name: Name of the provider to remove
        """
        if provider_name in self._providers:
            del self._providers[provider_name]
            if provider_name in self._provider_instances:
                del self._provider_instances[provider_name]
            
            # Remove from health checker if available
            if self.health_checker:
                self.health_checker.remove_provider(provider_name)
            
            logger.info(f"Removed provider '{provider_name}' from load balancer")
    
    def set_provider_enabled(self, provider_name: str, enabled: bool) -> None:
        """Enable or disable a provider.
        
        Args:
            provider_name: Name of the provider
            enabled: Whether the provider should be enabled
        """
        if provider_name in self._providers:
            self._providers[provider_name].enabled = enabled
            logger.info(f"Set provider '{provider_name}' enabled={enabled}")
    
    async def _get_provider_instance(self, provider_name: str) -> BaseLLMProvider:
        """Get or create a provider instance.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Provider instance
        """
        if provider_name not in self._provider_instances:
            provider = self.provider_factory.get_provider(provider_name)
            if not provider._initialized:
                await provider.initialize()
            self._provider_instances[provider_name] = provider
        
        return self._provider_instances[provider_name]
    
    def _get_available_providers(self) -> List[str]:
        """Get list of currently available providers."""
        available = []
        
        for provider_name, config in self._providers.items():
            if not config.enabled:
                continue
            
            # Check if provider has capacity
            if config.active_requests >= config.max_concurrent_requests:
                continue
            
            # Check health if health checker is available
            if self.health_checker:
                if not self.health_checker.is_provider_healthy(provider_name):
                    continue
            
            available.append(provider_name)
        
        return available
    
    def _select_provider(self, available_providers: List[str]) -> Optional[str]:
        """Select a provider based on the configured strategy.
        
        Args:
            available_providers: List of available provider names
            
        Returns:
            Selected provider name, or None if no providers available
        """
        if not available_providers:
            return None
        
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._select_round_robin(available_providers)
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._select_weighted_round_robin(available_providers)
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._select_least_connections(available_providers)
        elif self.strategy == LoadBalancingStrategy.FASTEST_RESPONSE:
            return self._select_fastest_response(available_providers)
        elif self.strategy == LoadBalancingStrategy.HEALTH_WEIGHTED:
            return self._select_health_weighted(available_providers)
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(available_providers)
        elif self.strategy == LoadBalancingStrategy.PRIORITY_FAILOVER:
            return self._select_priority_failover(available_providers)
        else:
            return available_providers[0]
    
    def _select_round_robin(self, available_providers: List[str]) -> str:
        """Select provider using round-robin strategy."""
        provider = available_providers[self._round_robin_index % len(available_providers)]
        self._round_robin_index = (self._round_robin_index + 1) % len(available_providers)
        return provider
    
    def _select_weighted_round_robin(self, available_providers: List[str]) -> str:
        """Select provider using weighted round-robin strategy."""
        total_weight = sum(self._providers[name].weight for name in available_providers)
        target = random.uniform(0, total_weight)
        
        current_weight = 0
        for provider_name in available_providers:
            current_weight += self._providers[provider_name].weight
            if current_weight >= target:
                return provider_name
        
        return available_providers[0]
    
    def _select_least_connections(self, available_providers: List[str]) -> str:
        """Select provider with least active connections."""
        return min(available_providers, key=lambda name: self._providers[name].active_requests)
    
    def _select_fastest_response(self, available_providers: List[str]) -> str:
        """Select provider with fastest average response time."""
        return min(available_providers, key=lambda name: self._providers[name].average_response_time or float('inf'))
    
    def _select_health_weighted(self, available_providers: List[str]) -> str:
        """Select provider based on health and performance metrics."""
        scores = []
        
        for provider_name in available_providers:
            config = self._providers[provider_name]
            
            # Base score from success rate
            score = config.success_rate * 100
            
            # Adjust for response time (lower is better)
            avg_response = config.average_response_time
            if avg_response > 0:
                score -= min(avg_response / 1000, 50)  # Cap penalty at 50 points
            
            # Adjust for active connections (fewer is better)
            utilization = config.active_requests / config.max_concurrent_requests
            score -= utilization * 20  # Up to 20 point penalty for high utilization
            
            # Apply weight multiplier
            score *= config.weight
            
            scores.append((score, provider_name))
        
        # Select provider with highest score
        return max(scores)[1]
    
    def _select_priority_failover(self, available_providers: List[str]) -> str:
        """Select provider with highest priority (lowest priority number)."""
        return min(available_providers, key=lambda name: self._providers[name].priority)
    
    async def _attempt_request(
        self,
        provider_name: str,
        request: LLMRequest
    ) -> LLMResponse:
        """Attempt a request with a specific provider.
        
        Args:
            provider_name: Name of the provider
            request: LLM request
            
        Returns:
            LLM response
            
        Raises:
            ProviderError: If the request fails
        """
        config = self._providers[provider_name]
        start_time = time.time()
        
        try:
            config.record_request_start()
            
            # Check rate limits if rate limiter is available
            if self.rate_limiter:
                estimated_tokens = len(request.prompt) // 4 if request.prompt else None
                await self.rate_limiter.acquire_request_quota(provider_name, estimated_tokens)
            
            # Get provider instance and make request
            provider = await self._get_provider_instance(provider_name)
            
            response = await asyncio.wait_for(
                provider.generate(request),
                timeout=config.timeout
            )
            
            # Record success
            response_time = time.time() - start_time
            config.record_request_success(response_time)
            
            if self.rate_limiter:
                self.rate_limiter.record_success(provider_name)
            
            return response
            
        except RateLimitExceededError:
            config.record_request_failure()
            self._metrics.rate_limited_requests += 1
            raise
            
        except Exception as e:
            config.record_request_failure()
            
            if self.rate_limiter:
                self.rate_limiter.record_failure(provider_name)
            
            raise ProviderError(f"Request failed with provider '{provider_name}': {str(e)}")
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text using load balanced providers.
        
        Args:
            request: LLM request
            
        Returns:
            LLM response
            
        Raises:
            ProviderError: If all providers fail
        """
        async with self._lock:
            self._metrics.total_requests += 1
            
            available_providers = self._get_available_providers()
            if not available_providers:
                self._metrics.failed_requests += 1
                raise ProviderError("No available providers")
            
            # Try providers in order
            last_error = None
            for attempt, provider_name in enumerate(available_providers):
                try:
                    response = await self._attempt_request(provider_name, request)
                    self._metrics.successful_requests += 1
                    
                    if attempt > 0:
                        self._metrics.fallback_requests += 1
                    
                    return response
                    
                except RateLimitExceededError as e:
                    last_error = e
                    logger.warning(f"Rate limit exceeded for provider '{provider_name}', trying next")
                    continue
                    
                except ProviderError as e:
                    last_error = e
                    logger.warning(f"Provider '{provider_name}' failed: {str(e)}, trying next")
                    continue
            
            # All providers failed
            self._metrics.failed_requests += 1
            raise ProviderError(f"All providers failed. Last error: {str(last_error)}")
    
    async def generate_stream(self, request: LLMRequest) -> AsyncGenerator[StreamingChunk, None]:
        """Generate streaming text using load balanced providers.
        
        Args:
            request: LLM request with stream=True
            
        Yields:
            Streaming chunks
            
        Raises:
            ProviderError: If all providers fail
        """
        async with self._lock:
            self._metrics.total_requests += 1
            
            available_providers = self._get_available_providers()
            if not available_providers:
                self._metrics.failed_requests += 1
                raise ProviderError("No available providers")
            
            # For streaming, we only try the first selected provider
            provider_name = self._select_provider(available_providers)
            if not provider_name:
                self._metrics.failed_requests += 1
                raise ProviderError("No suitable provider selected")
            
            config = self._providers[provider_name]
            
            try:
                config.record_request_start()
                
                # Check rate limits if rate limiter is available
                if self.rate_limiter:
                    estimated_tokens = len(request.prompt) // 4 if request.prompt else None
                    await self.rate_limiter.acquire_request_quota(provider_name, estimated_tokens)
                
                # Get provider instance and make streaming request
                provider = await self._get_provider_instance(provider_name)
                
                start_time = time.time()
                chunk_count = 0
                
                async for chunk in provider.generate_stream(request):
                    chunk_count += 1
                    yield chunk
                
                # Record success
                response_time = time.time() - start_time
                config.record_request_success(response_time)
                self._metrics.successful_requests += 1
                
                if self.rate_limiter:
                    self.rate_limiter.record_success(provider_name)
                
            except Exception as e:
                config.record_request_failure()
                self._metrics.failed_requests += 1
                
                if self.rate_limiter:
                    self.rate_limiter.record_failure(provider_name)
                
                raise ProviderError(f"Streaming request failed with provider '{provider_name}': {str(e)}")
    
    def get_metrics(self) -> LoadBalancerMetrics:
        """Get load balancer metrics."""
        return self._metrics
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all providers."""
        stats = {}
        
        for provider_name, config in self._providers.items():
            stats[provider_name] = {
                "enabled": config.enabled,
                "weight": config.weight,
                "priority": config.priority,
                "max_concurrent_requests": config.max_concurrent_requests,
                "active_requests": config.active_requests,
                "total_requests": config.total_requests,
                "successful_requests": config.successful_requests,
                "failed_requests": config.failed_requests,
                "success_rate": config.success_rate,
                "average_response_time": config.average_response_time,
                "last_used": config.last_used
            }
            
            # Add health status if health checker is available
            if self.health_checker:
                health_stats = self.health_checker.get_provider_stats(provider_name)
                if health_stats:
                    stats[provider_name]["health_status"] = health_stats.current_status.value
                    stats[provider_name]["health_success_rate"] = health_stats.success_rate
        
        return stats
    
    def reset_metrics(self) -> None:
        """Reset all metrics."""
        self._metrics = LoadBalancerMetrics()
        self._round_robin_index = 0
        
        for config in self._providers.values():
            config.total_requests = 0
            config.successful_requests = 0
            config.failed_requests = 0
            config.total_response_time = 0.0
            config.active_requests = 0
            config.last_used = None
        
        logger.info("Reset load balancer metrics")
    
    def set_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """Change the load balancing strategy.
        
        Args:
            strategy: New load balancing strategy
        """
        self.strategy = strategy
        self._round_robin_index = 0  # Reset round-robin state
        logger.info(f"Changed load balancing strategy to {strategy.value}")
    
    def get_fallback_chain(self, primary_provider: str) -> List[str]:
        """Get a fallback chain for requests.
        
        Args:
            primary_provider: Primary provider name
            
        Returns:
            List of provider names in fallback order
        """
        available = self._get_available_providers()
        
        if self.strategy == LoadBalancingStrategy.PRIORITY_FAILOVER:
            # Sort by priority
            return sorted(available, key=lambda name: self._providers[name].priority)
        else:
            # Move primary to front, then sort others by success rate
            chain = [primary_provider] if primary_provider in available else []
            others = [name for name in available if name != primary_provider]
            others.sort(key=lambda name: self._providers[name].success_rate, reverse=True)
            chain.extend(others)
            return chain