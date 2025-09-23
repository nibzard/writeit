"""Execution domain repositories.

Repository interfaces for execution domain entities providing
data access operations for LLM caching and token usage tracking.
"""

from .llm_cache_repository import (
    LLMCacheRepository,
    CacheEntry,
    ByModelSpecification,
    ExpiredEntriesSpecification,
    RecentlyAccessedSpecification,
    HighHitCountSpecification,
    LargeCacheEntrySpecification,
)

from .token_usage_repository import (
    TokenUsageRepository,
    TokenUsageRecord,
    ByWorkspaceSpecification,
    DateRangeSpecification,
    ByPipelineRunSpecification,
    CacheHitSpecification,
    HighCostSpecification,
    HighTokenUsageSpecification,
)

__all__ = [
    # Repository interfaces
    "LLMCacheRepository",
    "TokenUsageRepository",
    
    # Value objects
    "CacheEntry",
    "TokenUsageRecord",
    
    # Cache specifications
    "ByModelSpecification",
    "ExpiredEntriesSpecification",
    "RecentlyAccessedSpecification",
    "HighHitCountSpecification",
    "LargeCacheEntrySpecification",
    
    # Usage specifications
    "ByWorkspaceSpecification",
    "DateRangeSpecification",
    "ByPipelineRunSpecification",
    "CacheHitSpecification",
    "HighCostSpecification",
    "HighTokenUsageSpecification",
]