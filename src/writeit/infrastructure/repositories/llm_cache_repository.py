"""Multi-tier implementation of LLMCacheRepository.

Provides LLM response caching using multi-tier cache storage
with TTL management and analytics.
"""

import asyncio
import hashlib
import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ...domains.execution.repositories.llm_cache_repository import LLMCacheRepository
from ...domains.execution.entities.cache_entry import CacheEntry
from ...domains.execution.value_objects.cache_key import CacheKey
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError
from ..persistence.cache_storage import MultiTierCacheStorage
from ..base.exceptions import StorageError, CacheError


class MultiTierLLMCacheRepository(LLMCacheRepository):
    """Multi-tier cache implementation of LLMCacheRepository.
    
    Uses memory and persistent cache tiers for optimal performance
    with TTL management and cache analytics.
    """
    
    def __init__(
        self,
        cache_storage: MultiTierCacheStorage,
        workspace: Optional[WorkspaceName] = None,
        default_ttl_hours: int = 24
    ):
        """Initialize repository.
        
        Args:
            cache_storage: Multi-tier cache storage instance
            workspace: Current workspace (if None, uses global scope)
            default_ttl_hours: Default TTL for cache entries
        """
        super().__init__(workspace)
        self.cache_storage = cache_storage
        self.default_ttl_hours = default_ttl_hours
        self._key_prefix = "llm_cache"
    
    async def save(self, entry: CacheEntry) -> None:
        """Save a cache entry.
        
        Args:
            entry: Cache entry to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        try:
            cache_key = self._make_cache_key(entry.key)
            ttl_seconds = self._calculate_ttl_seconds(entry)
            
            await self.cache_storage.set(
                cache_key,
                entry,
                ttl_seconds=ttl_seconds
            )
            
        except Exception as e:
            raise RepositoryError(f"Failed to save cache entry {entry.key}: {e}") from e
    
    async def find_by_id(self, entry_id: str) -> Optional[CacheEntry]:
        """Find cache entry by ID.
        
        Args:
            entry_id: Entry ID to search for
            
        Returns:
            Cache entry if found, None otherwise
        """
        try:
            cache_key = self._make_cache_key(CacheKey(entry_id))
            return await self.cache_storage.get(cache_key)
        except Exception as e:
            raise RepositoryError(f"Failed to find cache entry {entry_id}: {e}") from e
    
    async def find_by_key(self, key: CacheKey) -> Optional[CacheEntry]:
        """Find cache entry by cache key.
        
        Args:
            key: Cache key to search for
            
        Returns:
            Cache entry if found, None otherwise
        """
        try:
            cache_key = self._make_cache_key(key)
            return await self.cache_storage.get(cache_key)
        except Exception as e:
            raise RepositoryError(f"Failed to find cache entry by key {key}: {e}") from e
    
    async def find_by_content_hash(self, content_hash: str) -> Optional[CacheEntry]:
        """Find cache entry by content hash.
        
        Args:
            content_hash: Content hash to search for
            
        Returns:
            Cache entry if found, None otherwise
        """
        try:
            # For multi-tier cache, we need to search through entries
            # This is less efficient but provides the functionality
            # In production, you might maintain a separate hash index
            
            # Since we can't easily search by content hash in our cache,
            # we'll return None for now. This could be enhanced with indexing.
            return None
            
        except Exception as e:
            raise RepositoryError(f"Failed to find cache entry by hash {content_hash}: {e}") from e
    
    async def find_by_model(self, model_name: str) -> List[CacheEntry]:
        """Find cache entries by model name.
        
        Args:
            model_name: Model name to search for
            
        Returns:
            List of cache entries for the model
        """
        try:
            # For multi-tier cache, this would require scanning entries
            # In production, this could be optimized with proper indexing
            return []
            
        except Exception as e:
            raise RepositoryError(f"Failed to find cache entries by model {model_name}: {e}") from e
    
    async def find_recent_entries(self, limit: int = 50) -> List[CacheEntry]:
        """Find recent cache entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent cache entries
        """
        try:
            # For multi-tier cache, this would require scanning entries
            # In production, this could be optimized with proper indexing
            return []
            
        except Exception as e:
            raise RepositoryError(f"Failed to find recent cache entries: {e}") from e
    
    async def find_expired_entries(self) -> List[CacheEntry]:
        """Find expired cache entries.
        
        Returns:
            List of expired cache entries
        """
        try:
            # Multi-tier cache handles expiration automatically
            # Return empty list as expired entries are automatically cleaned
            return []
            
        except Exception as e:
            raise RepositoryError(f"Failed to find expired cache entries: {e}") from e
    
    async def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries.
        
        Returns:
            Number of entries cleaned up
        """
        try:
            # Multi-tier cache handles cleanup automatically
            # Return 0 as cleanup is handled by the cache itself
            return 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to cleanup expired entries: {e}") from e
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics and metrics.
        
        Returns:
            Dictionary with cache statistics
        """
        try:
            stats = self.cache_storage.get_stats()
            
            # Add LLM-specific statistics
            llm_stats = {
                "repository_type": "MultiTierLLMCache",
                "workspace": self.workspace.value if self.workspace else "global",
                "default_ttl_hours": self.default_ttl_hours,
                "key_prefix": self._key_prefix
            }
            
            # Merge with cache storage stats
            llm_stats.update(stats)
            
            return llm_stats
            
        except Exception as e:
            raise RepositoryError(f"Failed to get cache statistics: {e}") from e
    
    async def get_hit_rate(self, hours: int = 24) -> float:
        """Get cache hit rate for specified time period.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Hit rate as percentage (0.0 to 1.0)
        """
        try:
            stats = self.cache_storage.get_stats()
            
            # Extract hit rate from total stats
            total_stats = stats.get("total", {})
            return total_stats.get("hit_rate", 0.0)
            
        except Exception as e:
            raise RepositoryError(f"Failed to get hit rate: {e}") from e
    
    async def get_size_metrics(self) -> Dict[str, Any]:
        """Get cache size and memory metrics.
        
        Returns:
            Dictionary with size metrics
        """
        try:
            stats = self.cache_storage.get_stats()
            
            memory_stats = stats.get("memory", {})
            
            return {
                "entries_count": memory_stats.get("entries", 0),
                "memory_usage_bytes": memory_stats.get("memory_bytes", 0),
                "memory_usage_mb": memory_stats.get("memory_bytes", 0) / (1024 * 1024),
                "evictions": memory_stats.get("evictions", 0),
                "expirations": memory_stats.get("expirations", 0)
            }
            
        except Exception as e:
            raise RepositoryError(f"Failed to get size metrics: {e}") from e
    
    async def clear_cache(self) -> None:
        """Clear all cache entries.
        
        Raises:
            RepositoryError: If clear operation fails
        """
        try:
            await self.cache_storage.clear()
        except Exception as e:
            raise RepositoryError(f"Failed to clear cache: {e}") from e
    
    async def clear_model_cache(self, model_name: str) -> int:
        """Clear cache entries for specific model.
        
        Args:
            model_name: Model name to clear
            
        Returns:
            Number of entries cleared
        """
        try:
            # For multi-tier cache, this would require scanning and removing entries
            # In production, this could be optimized with proper indexing
            # For now, return 0 as we can't efficiently implement this
            return 0
            
        except Exception as e:
            raise RepositoryError(f"Failed to clear model cache for {model_name}: {e}") from e
    
    async def invalidate_key(self, key: CacheKey) -> bool:
        """Invalidate specific cache key.
        
        Args:
            key: Cache key to invalidate
            
        Returns:
            True if key was invalidated, False if not found
        """
        try:
            cache_key = self._make_cache_key(key)
            return await self.cache_storage.delete(cache_key)
        except Exception as e:
            raise RepositoryError(f"Failed to invalidate cache key {key}: {e}") from e
    
    async def find_all(self) -> List[CacheEntry]:
        """Find all cache entries.
        
        Returns:
            List of all cache entries
        """
        try:
            # Multi-tier cache doesn't support finding all entries efficiently
            # Return empty list for now
            return []
        except Exception as e:
            raise RepositoryError(f"Failed to find all cache entries: {e}") from e
    
    async def delete(self, entry_id: str) -> bool:
        """Delete a cache entry.
        
        Args:
            entry_id: ID of entry to delete
            
        Returns:
            True if entry was deleted, False if not found
        """
        try:
            cache_key = self._make_cache_key(CacheKey(entry_id))
            return await self.cache_storage.delete(cache_key)
        except Exception as e:
            raise RepositoryError(f"Failed to delete cache entry {entry_id}: {e}") from e
    
    async def count(self) -> int:
        """Count cache entries.
        
        Returns:
            Number of cache entries
        """
        try:
            stats = self.cache_storage.get_stats()
            memory_stats = stats.get("memory", {})
            return memory_stats.get("entries", 0)
        except Exception as e:
            raise RepositoryError(f"Failed to count cache entries: {e}") from e
    
    def _make_cache_key(self, key: CacheKey) -> str:
        """Create cache storage key.
        
        Args:
            key: Cache key
            
        Returns:
            Storage key
        """
        if self.workspace:
            return f"{self._key_prefix}:{self.workspace.value}:{key.value}"
        else:
            return f"{self._key_prefix}:global:{key.value}"
    
    def _calculate_ttl_seconds(self, entry: CacheEntry) -> Optional[int]:
        """Calculate TTL in seconds for cache entry.
        
        Args:
            entry: Cache entry
            
        Returns:
            TTL in seconds, or None for no expiration
        """
        if entry.ttl_hours is not None:
            return entry.ttl_hours * 3600
        else:
            return self.default_ttl_hours * 3600
