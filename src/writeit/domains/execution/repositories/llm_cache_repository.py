"""LLM cache repository interface.

Provides data access operations for LLM response caching including
cache management, TTL handling, and cache analytics.
"""

from abc import abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union

from ....shared.repository import Repository, Specification
from ..value_objects.cache_key import CacheKey
from ..value_objects.model_name import ModelName


class CacheEntry:
    """Value object representing a cached LLM response.
    
    Contains response data, metadata, and cache management information.
    """
    
    def __init__(
        self,
        cache_key: CacheKey,
        model_name: ModelName,
        prompt: str,
        response: str,
        created_at: datetime,
        expires_at: Optional[datetime] = None,
        hit_count: int = 0,
        last_accessed: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tokens_used: Optional[int] = None,
        response_time_ms: Optional[int] = None
    ):
        self.cache_key = cache_key
        self.model_name = model_name
        self.prompt = prompt
        self.response = response
        self.created_at = created_at
        self.expires_at = expires_at
        self.hit_count = hit_count
        self.last_accessed = last_accessed
        self.metadata = metadata or {}
        self.tokens_used = tokens_used
        self.response_time_ms = response_time_ms
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() >= self.expires_at
    
    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()
    
    @property
    def time_to_live_seconds(self) -> Optional[float]:
        """Get remaining time to live in seconds."""
        if self.expires_at is None:
            return None
        remaining = self.expires_at - datetime.now()
        return max(0, remaining.total_seconds())


class LLMCacheRepository(Repository[CacheEntry]):
    """Repository for LLM response cache persistence and retrieval.
    
    Handles CRUD operations for cached LLM responses with TTL management,
    eviction policies, and cache analytics.
    """
    
    @abstractmethod
    async def get_cached_response(
        self, 
        cache_key: CacheKey
    ) -> Optional[CacheEntry]:
        """Get cached response by key.
        
        Args:
            cache_key: Cache key to look up
            
        Returns:
            Cache entry if found and not expired, None otherwise
            
        Raises:
            RepositoryError: If cache lookup fails
        """
        pass
    
    @abstractmethod
    async def store_response(
        self,
        cache_key: CacheKey,
        model_name: ModelName,
        prompt: str,
        response: str,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tokens_used: Optional[int] = None,
        response_time_ms: Optional[int] = None
    ) -> CacheEntry:
        """Store LLM response in cache.
        
        Args:
            cache_key: Cache key for the response
            model_name: Model that generated the response
            prompt: Input prompt
            response: LLM response
            ttl_seconds: Time to live in seconds
            metadata: Additional metadata
            tokens_used: Number of tokens consumed
            response_time_ms: Response time in milliseconds
            
        Returns:
            Created cache entry
            
        Raises:
            RepositoryError: If cache storage fails
        """
        pass
    
    @abstractmethod
    async def invalidate_cache(self, cache_key: CacheKey) -> bool:
        """Invalidate (delete) cached response.
        
        Args:
            cache_key: Cache key to invalidate
            
        Returns:
            True if entry was invalidated, False if not found
            
        Raises:
            RepositoryError: If invalidation fails
        """
        pass
    
    @abstractmethod
    async def find_by_model(self, model_name: ModelName) -> List[CacheEntry]:
        """Find all cache entries for a specific model.
        
        Args:
            model_name: Model to filter by
            
        Returns:
            List of cache entries for the model
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_expired_entries(
        self, 
        as_of: Optional[datetime] = None
    ) -> List[CacheEntry]:
        """Find all expired cache entries.
        
        Args:
            as_of: Check expiration as of this time, defaults to now
            
        Returns:
            List of expired cache entries
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_least_recently_used(
        self, 
        limit: int = 100
    ) -> List[CacheEntry]:
        """Find least recently used cache entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of LRU cache entries
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def cleanup_expired_entries(self) -> int:
        """Remove all expired cache entries.
        
        Returns:
            Number of entries removed
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        pass
    
    @abstractmethod
    async def evict_lru_entries(
        self, 
        target_count: int
    ) -> int:
        """Evict least recently used entries to reach target count.
        
        Args:
            target_count: Target number of entries to keep
            
        Returns:
            Number of entries evicted
            
        Raises:
            RepositoryError: If eviction operation fails
        """
        pass
    
    @abstractmethod
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and performance metrics.
        
        Returns:
            Dictionary with cache statistics:
            - total_entries: Total number of cached entries
            - total_size_bytes: Total cache size in bytes
            - hit_rate: Cache hit rate percentage
            - average_age_seconds: Average age of entries
            - expired_entries: Number of expired entries
            - most_popular_models: Most cached models
            - memory_usage: Cache memory usage statistics
            
        Raises:
            RepositoryError: If stats calculation fails
        """
        pass
    
    @abstractmethod
    async def get_hit_rate_stats(
        self, 
        since: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get cache hit rate statistics.
        
        Args:
            since: Calculate stats since this time
            
        Returns:
            Dictionary with hit rate statistics:
            - overall_hit_rate: Overall cache hit rate
            - model_hit_rates: Hit rates by model
            - hourly_hit_rates: Hit rates by hour
            
        Raises:
            RepositoryError: If stats calculation fails
        """
        pass
    
    @abstractmethod
    async def record_cache_hit(self, cache_key: CacheKey) -> None:
        """Record a cache hit for analytics.
        
        Args:
            cache_key: Cache key that was hit
            
        Raises:
            RepositoryError: If recording fails
        """
        pass
    
    @abstractmethod
    async def record_cache_miss(
        self, 
        cache_key: CacheKey, 
        model_name: ModelName
    ) -> None:
        """Record a cache miss for analytics.
        
        Args:
            cache_key: Cache key that was missed
            model_name: Model that was requested
            
        Raises:
            RepositoryError: If recording fails
        """
        pass
    
    @abstractmethod
    async def update_ttl(
        self, 
        cache_key: CacheKey, 
        new_ttl_seconds: int
    ) -> bool:
        """Update TTL for a cache entry.
        
        Args:
            cache_key: Cache key to update
            new_ttl_seconds: New TTL in seconds
            
        Returns:
            True if TTL was updated, False if entry not found
            
        Raises:
            RepositoryError: If update operation fails
        """
        pass
    
    @abstractmethod
    async def get_memory_usage(self) -> Dict[str, int]:
        """Get cache memory usage information.
        
        Returns:
            Dictionary with memory usage:
            - total_bytes: Total memory used
            - entries_count: Number of cached entries
            - average_entry_size: Average size per entry
            - largest_entry_size: Size of largest entry
            
        Raises:
            RepositoryError: If memory calculation fails
        """
        pass
    
    @abstractmethod
    async def optimize_cache(self) -> Dict[str, int]:
        """Optimize cache by removing expired entries and compacting storage.
        
        Returns:
            Dictionary with optimization results:
            - expired_removed: Number of expired entries removed
            - space_reclaimed: Bytes of space reclaimed
            - entries_remaining: Number of entries after optimization
            
        Raises:
            RepositoryError: If optimization fails
        """
        pass


# Specifications for cache entry queries

class ByModelSpecification(Specification[CacheEntry]):
    """Specification for filtering cache entries by model."""
    
    def __init__(self, model_name: ModelName):
        self.model_name = model_name
    
    def is_satisfied_by(self, entry: CacheEntry) -> bool:
        return entry.model_name == self.model_name


class ExpiredEntriesSpecification(Specification[CacheEntry]):
    """Specification for filtering expired cache entries."""
    
    def __init__(self, as_of: Optional[datetime] = None):
        self.as_of = as_of or datetime.now()
    
    def is_satisfied_by(self, entry: CacheEntry) -> bool:
        if entry.expires_at is None:
            return False
        return entry.expires_at <= self.as_of


class RecentlyAccessedSpecification(Specification[CacheEntry]):
    """Specification for filtering recently accessed entries."""
    
    def __init__(self, hours: int = 24):
        self.cutoff = datetime.now() - timedelta(hours=hours)
    
    def is_satisfied_by(self, entry: CacheEntry) -> bool:
        if entry.last_accessed is None:
            return False
        return entry.last_accessed >= self.cutoff


class HighHitCountSpecification(Specification[CacheEntry]):
    """Specification for filtering entries with high hit counts."""
    
    def __init__(self, min_hits: int = 5):
        self.min_hits = min_hits
    
    def is_satisfied_by(self, entry: CacheEntry) -> bool:
        return entry.hit_count >= self.min_hits


class LargeCacheEntrySpecification(Specification[CacheEntry]):
    """Specification for filtering large cache entries."""
    
    def __init__(self, min_size_bytes: int = 10000):
        self.min_size_bytes = min_size_bytes
    
    def is_satisfied_by(self, entry: CacheEntry) -> bool:
        # Estimate size based on response length
        estimated_size = len(entry.response.encode('utf-8'))
        return estimated_size >= self.min_size_bytes
