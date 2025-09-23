"""LLM Provider Rate Limiter.

Implements rate limiting for LLM provider requests to comply with API limits.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window" 
    TOKEN_BUCKET = "token_bucket"
    ADAPTIVE = "adaptive"


@dataclass
class RateLimit:
    """Rate limit configuration."""
    
    requests_per_minute: int
    requests_per_hour: int
    tokens_per_minute: Optional[int] = None
    tokens_per_hour: Optional[int] = None
    
    # Burst allowances
    max_burst_requests: Optional[int] = None
    max_burst_tokens: Optional[int] = None
    
    # Strategy configuration
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    
    def __post_init__(self):
        """Validate rate limit configuration."""
        if self.requests_per_minute <= 0 or self.requests_per_hour <= 0:
            raise ValueError("Request limits must be positive")
        
        if self.requests_per_minute * 60 > self.requests_per_hour:
            raise ValueError("Per-minute limit cannot exceed hourly when extrapolated")


@dataclass
class RateLimitState:
    """Current rate limiting state for a provider."""
    
    provider_name: str
    rate_limit: RateLimit
    
    # Request tracking
    request_timestamps: List[float] = field(default_factory=list)
    token_usage_timestamps: List[tuple[float, int]] = field(default_factory=list)  # (timestamp, tokens)
    
    # Token bucket state (for token bucket strategy)
    token_bucket_capacity: int = 0
    token_bucket_tokens: float = 0.0
    token_bucket_last_refill: float = 0.0
    
    # Adaptive state
    recent_failures: int = 0
    adaptive_multiplier: float = 1.0
    last_failure_time: Optional[float] = None
    
    def cleanup_old_entries(self, current_time: float) -> None:
        """Remove timestamps older than the tracking window."""
        # Keep last hour of request timestamps
        cutoff_time = current_time - 3600
        self.request_timestamps = [ts for ts in self.request_timestamps if ts > cutoff_time]
        self.token_usage_timestamps = [(ts, tokens) for ts, tokens in self.token_usage_timestamps if ts > cutoff_time]
    
    def get_requests_in_window(self, window_seconds: int, current_time: float) -> int:
        """Get number of requests in the specified time window."""
        cutoff_time = current_time - window_seconds
        return len([ts for ts in self.request_timestamps if ts > cutoff_time])
    
    def get_tokens_in_window(self, window_seconds: int, current_time: float) -> int:
        """Get number of tokens used in the specified time window."""
        cutoff_time = current_time - window_seconds
        return sum(tokens for ts, tokens in self.token_usage_timestamps if ts > cutoff_time)


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[float] = None, provider: Optional[str] = None):
        super().__init__(message)
        self.retry_after = retry_after
        self.provider = provider


class LLMRateLimiter:
    """Rate limiter for LLM provider requests."""
    
    def __init__(self, default_strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW):
        """Initialize the rate limiter.
        
        Args:
            default_strategy: Default rate limiting strategy
        """
        self.default_strategy = default_strategy
        self._provider_limits: Dict[str, RateLimit] = {}
        self._provider_states: Dict[str, RateLimitState] = {}
        self._lock = asyncio.Lock()
    
    def configure_provider(
        self, 
        provider_name: str, 
        rate_limit: RateLimit
    ) -> None:
        """Configure rate limits for a provider.
        
        Args:
            provider_name: Name of the provider
            rate_limit: Rate limit configuration
        """
        self._provider_limits[provider_name] = rate_limit
        self._provider_states[provider_name] = RateLimitState(
            provider_name=provider_name,
            rate_limit=rate_limit
        )
        
        # Initialize token bucket if using that strategy
        if rate_limit.strategy == RateLimitStrategy.TOKEN_BUCKET:
            state = self._provider_states[provider_name]
            state.token_bucket_capacity = rate_limit.requests_per_minute
            state.token_bucket_tokens = float(rate_limit.requests_per_minute)
            state.token_bucket_last_refill = time.time()
        
        logger.info(f"Configured rate limits for provider '{provider_name}': {rate_limit}")
    
    def auto_configure_common_providers(self) -> None:
        """Auto-configure rate limits for common LLM providers."""
        # OpenAI rate limits (as of 2024)
        self.configure_provider("openai_default", RateLimit(
            requests_per_minute=3500,
            requests_per_hour=10000,
            tokens_per_minute=90000,
            tokens_per_hour=1000000,
            max_burst_requests=50,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        ))
        
        # Anthropic rate limits (as of 2024)
        self.configure_provider("anthropic_default", RateLimit(
            requests_per_minute=1000,
            requests_per_hour=10000,
            tokens_per_minute=50000,
            tokens_per_hour=1000000,
            max_burst_requests=20,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        ))
        
        # Conservative limits for unknown providers
        self.configure_provider("default", RateLimit(
            requests_per_minute=60,
            requests_per_hour=1000,
            tokens_per_minute=10000,
            tokens_per_hour=100000,
            max_burst_requests=5,
            strategy=RateLimitStrategy.ADAPTIVE
        ))
        
        logger.info("Auto-configured rate limits for common providers")
    
    async def acquire_request_quota(
        self, 
        provider_name: str, 
        estimated_tokens: Optional[int] = None
    ) -> None:
        """Acquire quota for a request.
        
        Args:
            provider_name: Name of the provider
            estimated_tokens: Estimated tokens for this request
            
        Raises:
            RateLimitExceededError: If rate limit would be exceeded
        """
        async with self._lock:
            current_time = time.time()
            
            # Get provider configuration
            rate_limit = self._provider_limits.get(provider_name)
            if not rate_limit:
                # Use default limits if provider not configured
                rate_limit = self._provider_limits.get("default")
                if not rate_limit:
                    # No limits configured, allow request
                    return
            
            state = self._provider_states.get(provider_name)
            if not state:
                state = RateLimitState(provider_name=provider_name, rate_limit=rate_limit)
                self._provider_states[provider_name] = state
            
            # Cleanup old entries
            state.cleanup_old_entries(current_time)
            
            # Apply strategy-specific logic
            if rate_limit.strategy == RateLimitStrategy.FIXED_WINDOW:
                await self._check_fixed_window(state, current_time, estimated_tokens)
            elif rate_limit.strategy == RateLimitStrategy.SLIDING_WINDOW:
                await self._check_sliding_window(state, current_time, estimated_tokens)
            elif rate_limit.strategy == RateLimitStrategy.TOKEN_BUCKET:
                await self._check_token_bucket(state, current_time, estimated_tokens)
            elif rate_limit.strategy == RateLimitStrategy.ADAPTIVE:
                await self._check_adaptive(state, current_time, estimated_tokens)
            
            # Record the request
            state.request_timestamps.append(current_time)
            if estimated_tokens:
                state.token_usage_timestamps.append((current_time, estimated_tokens))
    
    async def _check_sliding_window(
        self, 
        state: RateLimitState, 
        current_time: float, 
        estimated_tokens: Optional[int]
    ) -> None:
        """Check sliding window rate limits."""
        rate_limit = state.rate_limit
        
        # Check minute window
        requests_last_minute = state.get_requests_in_window(60, current_time)
        if requests_last_minute >= rate_limit.requests_per_minute:
            retry_after = 60 - (current_time - min(state.request_timestamps[-rate_limit.requests_per_minute:]))
            raise RateLimitExceededError(
                f"Rate limit exceeded: {requests_last_minute}/{rate_limit.requests_per_minute} requests per minute",
                retry_after=retry_after,
                provider=state.provider_name
            )
        
        # Check hour window
        requests_last_hour = state.get_requests_in_window(3600, current_time)
        if requests_last_hour >= rate_limit.requests_per_hour:
            retry_after = 3600 - (current_time - min(state.request_timestamps[-rate_limit.requests_per_hour:]))
            raise RateLimitExceededError(
                f"Rate limit exceeded: {requests_last_hour}/{rate_limit.requests_per_hour} requests per hour",
                retry_after=retry_after,
                provider=state.provider_name
            )
        
        # Check token limits if configured
        if estimated_tokens and rate_limit.tokens_per_minute:
            tokens_last_minute = state.get_tokens_in_window(60, current_time)
            if tokens_last_minute + estimated_tokens > rate_limit.tokens_per_minute:
                raise RateLimitExceededError(
                    f"Token rate limit exceeded: {tokens_last_minute + estimated_tokens}/{rate_limit.tokens_per_minute} tokens per minute",
                    retry_after=60.0,
                    provider=state.provider_name
                )
        
        if estimated_tokens and rate_limit.tokens_per_hour:
            tokens_last_hour = state.get_tokens_in_window(3600, current_time)
            if tokens_last_hour + estimated_tokens > rate_limit.tokens_per_hour:
                raise RateLimitExceededError(
                    f"Token rate limit exceeded: {tokens_last_hour + estimated_tokens}/{rate_limit.tokens_per_hour} tokens per hour",
                    retry_after=3600.0,
                    provider=state.provider_name
                )
    
    async def _check_fixed_window(
        self, 
        state: RateLimitState, 
        current_time: float, 
        estimated_tokens: Optional[int]
    ) -> None:
        """Check fixed window rate limits."""
        rate_limit = state.rate_limit
        
        # For fixed window, we track requests in discrete minute/hour windows
        current_minute = int(current_time // 60)
        current_hour = int(current_time // 3600)
        
        # Count requests in current minute
        minute_start = current_minute * 60
        requests_this_minute = len([ts for ts in state.request_timestamps if ts >= minute_start])
        
        if requests_this_minute >= rate_limit.requests_per_minute:
            retry_after = (current_minute + 1) * 60 - current_time
            raise RateLimitExceededError(
                f"Rate limit exceeded: {requests_this_minute}/{rate_limit.requests_per_minute} requests this minute",
                retry_after=retry_after,
                provider=state.provider_name
            )
        
        # Count requests in current hour
        hour_start = current_hour * 3600
        requests_this_hour = len([ts for ts in state.request_timestamps if ts >= hour_start])
        
        if requests_this_hour >= rate_limit.requests_per_hour:
            retry_after = (current_hour + 1) * 3600 - current_time
            raise RateLimitExceededError(
                f"Rate limit exceeded: {requests_this_hour}/{rate_limit.requests_per_hour} requests this hour",
                retry_after=retry_after,
                provider=state.provider_name
            )
    
    async def _check_token_bucket(
        self, 
        state: RateLimitState, 
        current_time: float, 
        estimated_tokens: Optional[int]
    ) -> None:
        """Check token bucket rate limits."""
        rate_limit = state.rate_limit
        
        # Refill tokens based on time elapsed
        time_elapsed = current_time - state.token_bucket_last_refill
        tokens_to_add = time_elapsed * (rate_limit.requests_per_minute / 60.0)
        
        state.token_bucket_tokens = min(
            state.token_bucket_capacity,
            state.token_bucket_tokens + tokens_to_add
        )
        state.token_bucket_last_refill = current_time
        
        # Check if we have enough tokens
        if state.token_bucket_tokens < 1.0:
            retry_after = (1.0 - state.token_bucket_tokens) * (60.0 / rate_limit.requests_per_minute)
            raise RateLimitExceededError(
                f"Rate limit exceeded: insufficient tokens in bucket",
                retry_after=retry_after,
                provider=state.provider_name
            )
        
        # Consume a token
        state.token_bucket_tokens -= 1.0
    
    async def _check_adaptive(
        self, 
        state: RateLimitState, 
        current_time: float, 
        estimated_tokens: Optional[int]
    ) -> None:
        """Check adaptive rate limits."""
        rate_limit = state.rate_limit
        
        # Apply adaptive multiplier based on recent failures
        if state.recent_failures > 0:
            time_since_failure = current_time - (state.last_failure_time or 0)
            if time_since_failure > 300:  # 5 minutes
                # Gradually recover
                state.recent_failures = max(0, state.recent_failures - 1)
                state.adaptive_multiplier = max(0.5, state.adaptive_multiplier * 0.9)
        
        # Calculate adjusted limits
        adjusted_per_minute = int(rate_limit.requests_per_minute * state.adaptive_multiplier)
        adjusted_per_hour = int(rate_limit.requests_per_hour * state.adaptive_multiplier)
        
        # Use sliding window logic with adjusted limits
        requests_last_minute = state.get_requests_in_window(60, current_time)
        if requests_last_minute >= adjusted_per_minute:
            retry_after = 60.0 / state.adaptive_multiplier
            raise RateLimitExceededError(
                f"Adaptive rate limit exceeded: {requests_last_minute}/{adjusted_per_minute} requests per minute",
                retry_after=retry_after,
                provider=state.provider_name
            )
        
        requests_last_hour = state.get_requests_in_window(3600, current_time)
        if requests_last_hour >= adjusted_per_hour:
            retry_after = 3600.0 / state.adaptive_multiplier
            raise RateLimitExceededError(
                f"Adaptive rate limit exceeded: {requests_last_hour}/{adjusted_per_hour} requests per hour",
                retry_after=retry_after,
                provider=state.provider_name
            )
    
    def record_failure(self, provider_name: str) -> None:
        """Record a failure for adaptive rate limiting.
        
        Args:
            provider_name: Name of the provider that failed
        """
        state = self._provider_states.get(provider_name)
        if state and state.rate_limit.strategy == RateLimitStrategy.ADAPTIVE:
            state.recent_failures += 1
            state.last_failure_time = time.time()
            state.adaptive_multiplier = max(0.1, state.adaptive_multiplier * 0.5)
            logger.warning(f"Recorded failure for '{provider_name}', adaptive multiplier: {state.adaptive_multiplier}")
    
    def record_success(self, provider_name: str) -> None:
        """Record a success for adaptive rate limiting.
        
        Args:
            provider_name: Name of the provider that succeeded
        """
        state = self._provider_states.get(provider_name)
        if state and state.rate_limit.strategy == RateLimitStrategy.ADAPTIVE:
            # Gradually increase multiplier on success
            state.adaptive_multiplier = min(1.0, state.adaptive_multiplier * 1.05)
    
    def get_rate_limit_status(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """Get current rate limit status for a provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Dictionary with rate limit status information
        """
        state = self._provider_states.get(provider_name)
        if not state:
            return None
        
        current_time = time.time()
        state.cleanup_old_entries(current_time)
        
        return {
            "provider_name": provider_name,
            "strategy": state.rate_limit.strategy.value,
            "requests_last_minute": state.get_requests_in_window(60, current_time),
            "requests_last_hour": state.get_requests_in_window(3600, current_time),
            "tokens_last_minute": state.get_tokens_in_window(60, current_time),
            "tokens_last_hour": state.get_tokens_in_window(3600, current_time),
            "limits": {
                "requests_per_minute": state.rate_limit.requests_per_minute,
                "requests_per_hour": state.rate_limit.requests_per_hour,
                "tokens_per_minute": state.rate_limit.tokens_per_minute,
                "tokens_per_hour": state.rate_limit.tokens_per_hour
            },
            "adaptive_multiplier": state.adaptive_multiplier if state.rate_limit.strategy == RateLimitStrategy.ADAPTIVE else None,
            "recent_failures": state.recent_failures if state.rate_limit.strategy == RateLimitStrategy.ADAPTIVE else None
        }
    
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get rate limit status for all configured providers."""
        return {
            provider_name: self.get_rate_limit_status(provider_name)
            for provider_name in self._provider_states.keys()
        }
    
    def reset_limits(self, provider_name: Optional[str] = None) -> None:
        """Reset rate limiting state.
        
        Args:
            provider_name: Specific provider to reset, or None for all
        """
        if provider_name:
            if provider_name in self._provider_states:
                rate_limit = self._provider_states[provider_name].rate_limit
                self._provider_states[provider_name] = RateLimitState(
                    provider_name=provider_name,
                    rate_limit=rate_limit
                )
                logger.info(f"Reset rate limits for provider '{provider_name}'")
        else:
            for name, state in self._provider_states.items():
                self._provider_states[name] = RateLimitState(
                    provider_name=name,
                    rate_limit=state.rate_limit
                )
            logger.info("Reset rate limits for all providers")