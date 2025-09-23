"""Token Usage entity for the Execution domain.

Tracks LLM token consumption, costs, and usage analytics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
from enum import Enum

from ..value_objects import ModelName, TokenCount


class UsageType(str, Enum):
    """Types of token usage."""
    INPUT = "input"
    OUTPUT = "output"
    TOTAL = "total"
    CACHED = "cached"


class UsageCategory(str, Enum):
    """Categories of usage for billing and analytics."""
    PIPELINE_EXECUTION = "pipeline_execution"
    TEMPLATE_VALIDATION = "template_validation"
    CONTENT_GENERATION = "content_generation"
    STYLE_PROCESSING = "style_processing"
    CACHE_WARMUP = "cache_warmup"
    TESTING = "testing"


@dataclass
class TokenMetrics:
    """Detailed token metrics for a usage session."""
    
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_tokens: int = 0
    
    def __post_init__(self):
        """Validate token metrics consistency."""
        if self.total_tokens != self.input_tokens + self.output_tokens:
            # Allow for slight discrepancies but log them
            calculated_total = self.input_tokens + self.output_tokens
            if abs(self.total_tokens - calculated_total) > 1:
                # Correct the total if significantly off
                self.total_tokens = calculated_total
    
    @property
    def cache_hit_ratio(self) -> float:
        """Calculate cache hit ratio."""
        if self.total_tokens == 0:
            return 0.0
        return self.cached_tokens / self.total_tokens
    
    @property
    def effective_tokens(self) -> int:
        """Tokens actually processed (excluding cached)."""
        return max(0, self.total_tokens - self.cached_tokens)


@dataclass
class CostBreakdown:
    """Cost breakdown for token usage."""
    
    input_cost: Decimal = field(default=Decimal('0.00'))
    output_cost: Decimal = field(default=Decimal('0.00'))
    total_cost: Decimal = field(default=Decimal('0.00'))
    currency: str = "USD"
    
    def __post_init__(self):
        """Validate cost consistency."""
        calculated_total = self.input_cost + self.output_cost
        if abs(self.total_cost - calculated_total) > Decimal('0.01'):
            self.total_cost = calculated_total


@dataclass
class TokenUsage:
    """
    Entity representing token usage for LLM operations.
    
    Tracks token consumption, costs, and provides analytics
    for billing, optimization, and monitoring purposes.
    """
    
    # Identity
    id: str
    session_id: str
    
    # Context
    model_name: ModelName
    workspace_name: Optional[str] = None
    pipeline_id: Optional[str] = None
    step_id: Optional[str] = None
    
    # Usage details
    usage_type: UsageType = UsageType.TOTAL
    usage_category: UsageCategory = UsageCategory.PIPELINE_EXECUTION
    token_metrics: TokenMetrics = field(default_factory=lambda: TokenMetrics(0, 0, 0))
    cost_breakdown: CostBreakdown = field(default_factory=CostBreakdown)
    
    # Timing and context
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: Optional[int] = None
    
    # Additional metadata
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    provider_response_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Aggregation support
    aggregated_from: List[str] = field(default_factory=list)
    is_aggregated: bool = False
    
    def __post_init__(self):
        """Validate entity state after initialization."""
        if not self.id:
            raise ValueError("TokenUsage ID cannot be empty")
        
        if not self.session_id:
            raise ValueError("Session ID is required")
        
        if self.token_metrics.total_tokens < 0:
            raise ValueError("Token counts cannot be negative")
        
        if self.cost_breakdown.total_cost < 0:
            raise ValueError("Costs cannot be negative")
    
    @classmethod
    def create(
        cls,
        session_id: str,
        model_name: ModelName,
        input_tokens: int,
        output_tokens: int,
        usage_category: UsageCategory = UsageCategory.PIPELINE_EXECUTION,
        workspace_name: Optional[str] = None,
        pipeline_id: Optional[str] = None,
        step_id: Optional[str] = None,
        cached_tokens: int = 0,
        **kwargs
    ) -> "TokenUsage":
        """Create a new token usage record."""
        
        import uuid
        usage_id = f"usage-{uuid.uuid4().hex[:12]}"
        
        metrics = TokenMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cached_tokens=cached_tokens
        )
        
        return cls(
            id=usage_id,
            session_id=session_id,
            model_name=model_name,
            workspace_name=workspace_name,
            pipeline_id=pipeline_id,
            step_id=step_id,
            usage_category=usage_category,
            token_metrics=metrics,
            **kwargs
        )
    
    def calculate_cost(
        self,
        input_price_per_token: Decimal,
        output_price_per_token: Decimal,
        currency: str = "USD"
    ) -> "TokenUsage":
        """Calculate and update cost breakdown."""
        
        input_cost = Decimal(str(self.token_metrics.input_tokens)) * input_price_per_token
        output_cost = Decimal(str(self.token_metrics.output_tokens)) * output_price_per_token
        
        self.cost_breakdown = CostBreakdown(
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost,
            currency=currency
        )
        
        return self
    
    def add_metadata(self, key: str, value: Any) -> "TokenUsage":
        """Add metadata to the usage record."""
        self.metadata[key] = value
        return self
    
    def mark_as_cached(self, cached_tokens: int) -> "TokenUsage":
        """Mark tokens as cached to track cache efficiency."""
        self.token_metrics.cached_tokens = min(cached_tokens, self.token_metrics.total_tokens)
        return self
    
    def aggregate_with(self, other: "TokenUsage") -> "TokenUsage":
        """Aggregate this usage with another usage record."""
        
        if self.model_name != other.model_name:
            raise ValueError("Cannot aggregate usage from different models")
        
        # Create aggregated metrics
        aggregated_metrics = TokenMetrics(
            input_tokens=self.token_metrics.input_tokens + other.token_metrics.input_tokens,
            output_tokens=self.token_metrics.output_tokens + other.token_metrics.output_tokens,
            total_tokens=self.token_metrics.total_tokens + other.token_metrics.total_tokens,
            cached_tokens=self.token_metrics.cached_tokens + other.token_metrics.cached_tokens
        )
        
        # Create aggregated cost breakdown
        aggregated_cost = CostBreakdown(
            input_cost=self.cost_breakdown.input_cost + other.cost_breakdown.input_cost,
            output_cost=self.cost_breakdown.output_cost + other.cost_breakdown.output_cost,
            total_cost=self.cost_breakdown.total_cost + other.cost_breakdown.total_cost,
            currency=self.cost_breakdown.currency  # Assume same currency
        )
        
        # Create new aggregated usage
        aggregated_id = f"agg-{self.id}-{other.id}"
        
        return TokenUsage(
            id=aggregated_id,
            session_id=f"{self.session_id}+{other.session_id}",
            model_name=self.model_name,
            workspace_name=self.workspace_name or other.workspace_name,
            pipeline_id=self.pipeline_id or other.pipeline_id,
            step_id=None,  # Aggregated across steps
            usage_category=self.usage_category,
            token_metrics=aggregated_metrics,
            cost_breakdown=aggregated_cost,
            timestamp=min(self.timestamp, other.timestamp),  # Earliest timestamp
            duration_ms=(self.duration_ms or 0) + (other.duration_ms or 0),
            is_aggregated=True,
            aggregated_from=[self.id, other.id] + self.aggregated_from + other.aggregated_from,
            metadata={
                "aggregated_sessions": [self.session_id, other.session_id],
                "aggregated_count": 2 + len(self.aggregated_from) + len(other.aggregated_from),
                **self.metadata,
                **other.metadata
            }
        )
    
    @property
    def tokens_per_second(self) -> Optional[float]:
        """Calculate tokens processed per second."""
        if not self.duration_ms or self.duration_ms <= 0:
            return None
        
        duration_seconds = self.duration_ms / 1000.0
        return self.token_metrics.total_tokens / duration_seconds
    
    @property
    def cost_per_token(self) -> Decimal:
        """Calculate average cost per token."""
        if self.token_metrics.total_tokens == 0:
            return Decimal('0.00')
        
        return self.cost_breakdown.total_cost / Decimal(str(self.token_metrics.total_tokens))
    
    @property
    def efficiency_score(self) -> float:
        """
        Calculate efficiency score based on cache usage and speed.
        
        Higher score = better efficiency (more cache hits, faster processing)
        """
        cache_score = self.token_metrics.cache_hit_ratio * 50  # 0-50 points
        
        # Speed score based on tokens per second (normalize to reasonable range)
        speed_score = 0
        if self.tokens_per_second:
            # Assume 100 tokens/sec is good performance
            speed_score = min(50, (self.tokens_per_second / 100) * 50)
        
        return cache_score + speed_score
    
    def to_analytics_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analytics and reporting."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "model_name": str(self.model_name),
            "workspace": self.workspace_name,
            "pipeline_id": self.pipeline_id,
            "step_id": self.step_id,
            "usage_category": self.usage_category.value,
            "timestamp": self.timestamp.isoformat(),
            "tokens": {
                "input": self.token_metrics.input_tokens,
                "output": self.token_metrics.output_tokens,
                "total": self.token_metrics.total_tokens,
                "cached": self.token_metrics.cached_tokens,
                "effective": self.token_metrics.effective_tokens,
                "cache_hit_ratio": self.token_metrics.cache_hit_ratio
            },
            "costs": {
                "input": float(self.cost_breakdown.input_cost),
                "output": float(self.cost_breakdown.output_cost),
                "total": float(self.cost_breakdown.total_cost),
                "currency": self.cost_breakdown.currency,
                "cost_per_token": float(self.cost_per_token)
            },
            "performance": {
                "duration_ms": self.duration_ms,
                "tokens_per_second": self.tokens_per_second,
                "efficiency_score": self.efficiency_score
            },
            "context": {
                "request_id": self.request_id,
                "user_id": self.user_id,
                "provider_response_id": self.provider_response_id,
                "is_aggregated": self.is_aggregated,
                "aggregated_count": len(self.aggregated_from)
            },
            "metadata": self.metadata
        }
    
    def __str__(self) -> str:
        """String representation for logging and debugging."""
        return (
            f"TokenUsage(id={self.id}, model={self.model_name}, "
            f"tokens={self.token_metrics.total_tokens}, "
            f"cost=${self.cost_breakdown.total_cost}, "
            f"category={self.usage_category.value})"
        )
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"TokenUsage(id='{self.id}', session_id='{self.session_id}', "
            f"model_name={self.model_name}, usage_category={self.usage_category}, "
            f"token_metrics={self.token_metrics}, cost_breakdown={self.cost_breakdown}, "
            f"timestamp={self.timestamp})"
        )