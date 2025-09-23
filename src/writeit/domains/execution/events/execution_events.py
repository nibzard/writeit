"""Execution domain events.

Events related to LLM operations, caching, token usage, and execution lifecycle management."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List

from ....shared.events import DomainEvent
from ..value_objects.model_name import ModelName
from ..value_objects.token_count import TokenCount
from ..value_objects.cache_key import CacheKey
from ..value_objects.execution_mode import ExecutionMode


@dataclass(frozen=True)
class LLMRequestStarted(DomainEvent):
    """Event fired when an LLM API request is initiated.
    
    This event is published when the system starts an LLM request,
    including request metadata and tracking information.
    """
    
    request_id: str = field()
    execution_context_id: str = field()
    model_name: ModelName = field()
    provider: str = field()
    started_at: datetime = field()
    prompt_tokens: int = field()
    max_tokens: Optional[int] = field()
    temperature: Optional[float] = field()
    cache_key: Optional[CacheKey] = field(default=None)
    workspace_name: str = field(default="")
    pipeline_id: Optional[str] = field(default=None)
    step_id: Optional[str] = field(default=None)
    is_streaming: bool = field(default=False)
    retry_attempt: int = field(default=0)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "execution.llm_request_started"
    
    @property
    def aggregate_id(self) -> str:
        return self.request_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "request_id": self.request_id,
                "execution_context_id": self.execution_context_id,
                "model_name": str(self.model_name),
                "provider": self.provider,
                "started_at": self.started_at.isoformat(),
                "prompt_tokens": self.prompt_tokens,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "cache_key": str(self.cache_key) if self.cache_key else None,
                "workspace_name": self.workspace_name,
                "pipeline_id": self.pipeline_id,
                "step_id": self.step_id,
                "is_streaming": self.is_streaming,
                "retry_attempt": self.retry_attempt
            }
        }


@dataclass(frozen=True)
class LLMResponseReceived(DomainEvent):
    """Event fired when an LLM API response is received.
    
    This event is published when the system receives a complete
    response from an LLM provider, including timing and usage metrics.
    """
    
    request_id: str = field()
    execution_context_id: str = field()
    model_name: ModelName = field()
    provider: str = field()
    completed_at: datetime = field()
    duration_seconds: float = field()
    success: bool = field()
    response_tokens: int = field()
    total_tokens: int = field()
    cost_estimate: Optional[float] = field(default=None)
    response_length: int = field(default=0)
    cache_key: Optional[CacheKey] = field(default=None)
    cached_response: bool = field(default=False)
    error_message: Optional[str] = field(default=None)
    error_code: Optional[str] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "execution.llm_response_received"
    
    @property
    def aggregate_id(self) -> str:
        return self.request_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "request_id": self.request_id,
                "execution_context_id": self.execution_context_id,
                "model_name": str(self.model_name),
                "provider": self.provider,
                "completed_at": self.completed_at.isoformat(),
                "duration_seconds": self.duration_seconds,
                "success": self.success,
                "response_tokens": self.response_tokens,
                "total_tokens": self.total_tokens,
                "cost_estimate": self.cost_estimate,
                "response_length": self.response_length,
                "cache_key": str(self.cache_key) if self.cache_key else None,
                "cached_response": self.cached_response,
                "error_message": self.error_message,
                "error_code": self.error_code
            }
        }


@dataclass(frozen=True)
class CacheHit(DomainEvent):
    """Event fired when a cache lookup succeeds.
    
    This event is published when the system successfully retrieves
    a cached LLM response, avoiding an API call.
    """
    
    cache_key: CacheKey = field()
    execution_context_id: str = field()
    model_name: ModelName = field()
    hit_at: datetime = field()
    cache_age_seconds: float = field()
    response_tokens: int = field()
    cost_saved: Optional[float] = field(default=None)
    time_saved_seconds: float = field(default=0.0)
    workspace_name: str = field(default="")
    pipeline_id: Optional[str] = field(default=None)
    step_id: Optional[str] = field(default=None)
    cache_namespace: Optional[str] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "execution.cache_hit"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.cache_key)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "cache_key": str(self.cache_key),
                "execution_context_id": self.execution_context_id,
                "model_name": str(self.model_name),
                "hit_at": self.hit_at.isoformat(),
                "cache_age_seconds": self.cache_age_seconds,
                "response_tokens": self.response_tokens,
                "cost_saved": self.cost_saved,
                "time_saved_seconds": self.time_saved_seconds,
                "workspace_name": self.workspace_name,
                "pipeline_id": self.pipeline_id,
                "step_id": self.step_id,
                "cache_namespace": self.cache_namespace
            }
        }


@dataclass(frozen=True)
class CacheMiss(DomainEvent):
    """Event fired when a cache lookup fails.
    
    This event is published when the system cannot find a cached
    response and must make an API call.
    """
    
    cache_key: CacheKey = field()
    execution_context_id: str = field()
    model_name: ModelName = field()
    missed_at: datetime = field()
    workspace_name: str = field(default="")
    pipeline_id: Optional[str] = field(default=None)
    step_id: Optional[str] = field(default=None)
    cache_namespace: Optional[str] = field(default=None)
    reason: str = field(default="not_found")  # not_found, expired, invalid
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "execution.cache_miss"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.cache_key)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "cache_key": str(self.cache_key),
                "execution_context_id": self.execution_context_id,
                "model_name": str(self.model_name),
                "missed_at": self.missed_at.isoformat(),
                "workspace_name": self.workspace_name,
                "pipeline_id": self.pipeline_id,
                "step_id": self.step_id,
                "cache_namespace": self.cache_namespace,
                "reason": self.reason
            }
        }


@dataclass(frozen=True)
class CacheStored(DomainEvent):
    """Event fired when a response is stored in cache.
    
    This event is published when the system caches an LLM response
    for future use.
    """
    
    cache_key: CacheKey = field()
    execution_context_id: str = field()
    model_name: ModelName = field()
    stored_at: datetime = field()
    response_tokens: int = field()
    cache_size_bytes: int = field()
    ttl_seconds: Optional[int] = field(default=None)
    workspace_name: str = field(default="")
    cache_namespace: Optional[str] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "execution.cache_stored"
    
    @property
    def aggregate_id(self) -> str:
        return str(self.cache_key)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "cache_key": str(self.cache_key),
                "execution_context_id": self.execution_context_id,
                "model_name": str(self.model_name),
                "stored_at": self.stored_at.isoformat(),
                "response_tokens": self.response_tokens,
                "cache_size_bytes": self.cache_size_bytes,
                "ttl_seconds": self.ttl_seconds,
                "workspace_name": self.workspace_name,
                "cache_namespace": self.cache_namespace
            }
        }


@dataclass(frozen=True)
class TokensConsumed(DomainEvent):
    """Event fired when tokens are consumed by an LLM request.
    
    This event is published to track token usage for billing,
    analytics, and optimization purposes.
    """
    
    execution_context_id: str = field()
    model_name: ModelName = field()
    provider: str = field()
    consumed_at: datetime = field()
    prompt_tokens: int = field()
    completion_tokens: int = field()
    total_tokens: int = field()
    cost_per_token: Optional[float] = field(default=None)
    total_cost: Optional[float] = field(default=None)
    workspace_name: str = field(default="")
    pipeline_id: Optional[str] = field(default=None)
    step_id: Optional[str] = field(default=None)
    request_id: Optional[str] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "execution.tokens_consumed"
    
    @property
    def aggregate_id(self) -> str:
        return self.execution_context_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "execution_context_id": self.execution_context_id,
                "model_name": str(self.model_name),
                "provider": self.provider,
                "consumed_at": self.consumed_at.isoformat(),
                "prompt_tokens": self.prompt_tokens,
                "completion_tokens": self.completion_tokens,
                "total_tokens": self.total_tokens,
                "cost_per_token": self.cost_per_token,
                "total_cost": self.total_cost,
                "workspace_name": self.workspace_name,
                "pipeline_id": self.pipeline_id,
                "step_id": self.step_id,
                "request_id": self.request_id
            }
        }


@dataclass(frozen=True)
class ProviderFailover(DomainEvent):
    """Event fired when there's a failover to a different LLM provider.
    
    This event is published when the primary provider fails and
    the system switches to a backup provider.
    """
    
    execution_context_id: str = field()
    failed_provider: str = field()
    backup_provider: str = field()
    failed_model: ModelName = field()
    backup_model: ModelName = field()
    failover_at: datetime = field()
    failure_reason: str = field()
    retry_attempt: int = field()
    workspace_name: str = field(default="")
    pipeline_id: Optional[str] = field(default=None)
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "execution.provider_failover"
    
    @property
    def aggregate_id(self) -> str:
        return self.execution_context_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "execution_context_id": self.execution_context_id,
                "failed_provider": self.failed_provider,
                "backup_provider": self.backup_provider,
                "failed_model": str(self.failed_model),
                "backup_model": str(self.backup_model),
                "failover_at": self.failover_at.isoformat(),
                "failure_reason": self.failure_reason,
                "retry_attempt": self.retry_attempt,
                "workspace_name": self.workspace_name,
                "pipeline_id": self.pipeline_id
            }
        }


@dataclass(frozen=True)
class ExecutionContextCreated(DomainEvent):
    """Event fired when a new execution context is created.
    
    This event is published when the system creates a new
    execution context for pipeline operations.
    """
    
    execution_context_id: str = field()
    workspace_name: str = field()
    pipeline_id: str = field()
    execution_mode: ExecutionMode = field()
    created_at: datetime = field()
    model_preferences: List[ModelName] = field()
    provider_preferences: List[str] = field()
    cache_enabled: bool = field()
    streaming_enabled: bool = field()
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "execution.context_created"
    
    @property
    def aggregate_id(self) -> str:
        return self.execution_context_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "execution_context_id": self.execution_context_id,
                "workspace_name": self.workspace_name,
                "pipeline_id": self.pipeline_id,
                "execution_mode": str(self.execution_mode),
                "created_at": self.created_at.isoformat(),
                "model_preferences": [str(model) for model in self.model_preferences],
                "provider_preferences": self.provider_preferences,
                "cache_enabled": self.cache_enabled,
                "streaming_enabled": self.streaming_enabled
            }
        }


@dataclass(frozen=True)
class RateLimitEncountered(DomainEvent):
    """Event fired when a rate limit is encountered.
    
    This event is published when the system hits provider
    rate limits and needs to handle throttling.
    """
    
    execution_context_id: str = field()
    provider: str = field()
    model_name: ModelName = field()
    encountered_at: datetime = field()
    retry_after_seconds: Optional[int] = field()
    limit_type: str = field()  # requests_per_minute, tokens_per_minute, etc.
    current_usage: int = field()
    limit_threshold: int = field()
    workspace_name: str = field(default="")
    
    def __post_init__(self):
        super().__init__()
    
    @property
    def event_type(self) -> str:
        return "execution.rate_limit_encountered"
    
    @property
    def aggregate_id(self) -> str:
        return self.execution_context_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "execution_context_id": self.execution_context_id,
                "provider": self.provider,
                "model_name": str(self.model_name),
                "encountered_at": self.encountered_at.isoformat(),
                "retry_after_seconds": self.retry_after_seconds,
                "limit_type": self.limit_type,
                "current_usage": self.current_usage,
                "limit_threshold": self.limit_threshold,
                "workspace_name": self.workspace_name
            }
        }