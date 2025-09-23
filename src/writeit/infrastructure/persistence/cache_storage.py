"""Cache Storage Implementation for WriteIt Infrastructure.

Provides high-performance caching with LRU eviction, TTL-based expiration,
memory pressure handling, and multi-tier storage support.
"""

import asyncio
import time
import json
import hashlib
from typing import Optional, Dict, Any, List, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict
from threading import RLock
import logging
from pathlib import Path
import weakref
import psutil
from contextlib import asynccontextmanager

from ..base.exceptions import CacheError, CapacityError
from .lmdb_storage import LMDBStorage

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached item with metadata."""
    
    key: str
    value: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: Optional[int] = None
    size_bytes: int = 0
    
    def __post_init__(self):
        """Calculate entry size after initialization."""
        if self.size_bytes == 0:
            self.size_bytes = self._calculate_size()
    
    def _calculate_size(self) -> int:
        """Estimate memory size of the cache entry.
        
        Returns:
            Estimated size in bytes
        """
        try:
            # Rough estimation of memory usage
            key_size = len(self.key.encode('utf-8'))
            value_size = len(str(self.value).encode('utf-8'))  # Simplified
            metadata_size = 200  # Rough estimate for datetime objects and counters
            return key_size + value_size + metadata_size
        except Exception:
            return 1024  # Fallback estimate
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired based on TTL.
        
        Returns:
            True if entry is expired, False otherwise
        """
        if self.ttl_seconds is None:
            return False
        
        age_seconds = (datetime.now() - self.created_at).total_seconds()
        return age_seconds > self.ttl_seconds
    
    def touch(self) -> None:
        """Update access metadata."""
        self.last_accessed = datetime.now()
        self.access_count += 1


@dataclass
class CacheStats:
    """Cache statistics for monitoring and optimization."""
    
    total_gets: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_sets: int = 0
    evictions: int = 0
    expirations: int = 0
    current_size: int = 0
    current_entries: int = 0
    memory_usage_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate.
        
        Returns:
            Hit rate as percentage (0.0 to 1.0)
        """
        if self.total_gets == 0:
            return 0.0
        return self.cache_hits / self.total_gets
    
    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate.
        
        Returns:
            Miss rate as percentage (0.0 to 1.0)
        """
        return 1.0 - self.hit_rate


class LRUCache:
    """Thread-safe LRU cache with TTL support.
    
    Implements Least Recently Used eviction policy with optional
    time-to-live expiration and memory pressure handling.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        max_memory_mb: int = 100,
        default_ttl_seconds: Optional[int] = None,
        cleanup_interval_seconds: int = 300  # 5 minutes
    ):
        """Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries
            max_memory_mb: Maximum memory usage in MB
            default_ttl_seconds: Default TTL for entries (None = no expiration)
            cleanup_interval_seconds: Interval for background cleanup
        """
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.default_ttl_seconds = default_ttl_seconds
        self.cleanup_interval_seconds = cleanup_interval_seconds
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = RLock()
        self._stats = CacheStats()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stopped = False
        
        logger.debug(f"Initialized LRU cache with max_size={max_size}, max_memory={max_memory_mb}MB")
    
    async def start(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._background_cleanup())
            logger.info("Started cache background cleanup")
    
    async def stop(self) -> None:
        """Stop background cleanup and clear cache."""
        self._stopped = True
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        
        with self._lock:
            self._cache.clear()
            self._stats = CacheStats()
        
        logger.info("Stopped cache and cleared all entries")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            self._stats.total_gets += 1
            
            entry = self._cache.get(key)
            if entry is None:
                self._stats.cache_misses += 1
                return None
            
            # Check expiration
            if entry.is_expired:
                self._cache.pop(key)
                self._stats.cache_misses += 1
                self._stats.expirations += 1
                self._update_memory_stats()
                return None
            
            # Move to end (most recently used)
            entry.touch()
            self._cache.move_to_end(key)
            
            self._stats.cache_hits += 1
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL for this entry (uses default if None)
        """
        with self._lock:
            self._stats.total_sets += 1
            
            # Use default TTL if not specified
            if ttl_seconds is None:
                ttl_seconds = self.default_ttl_seconds
            
            # Create new entry
            now = datetime.now()
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                last_accessed=now,
                access_count=1,
                ttl_seconds=ttl_seconds
            )
            
            # Remove existing entry if present
            if key in self._cache:
                self._cache.pop(key)
            
            # Add new entry
            self._cache[key] = entry
            
            # Enforce size limits
            self._enforce_limits()
            self._update_memory_stats()
    
    def delete(self, key: str) -> bool:
        """Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was found and deleted, False otherwise
        """
        with self._lock:
            entry = self._cache.pop(key, None)
            if entry is not None:
                self._update_memory_stats()
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._cache.clear()
            self._stats.current_entries = 0
            self._stats.current_size = 0
            self._stats.memory_usage_bytes = 0
    
    def _enforce_limits(self) -> None:
        """Enforce size and memory limits by evicting entries."""
        # Evict expired entries first
        self._evict_expired()
        
        # Evict by count limit
        while len(self._cache) > self.max_size:
            self._evict_lru()
        
        # Evict by memory limit (rough estimation)
        while self._estimate_memory_usage() > self.max_memory_bytes:
            if not self._evict_lru():
                break  # No more entries to evict
    
    def _evict_expired(self) -> int:
        """Evict all expired entries.
        
        Returns:
            Number of entries evicted
        """
        expired_keys = []
        
        for key, entry in self._cache.items():
            if entry.is_expired:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._cache.pop(key)
            self._stats.expirations += 1
        
        return len(expired_keys)
    
    def _evict_lru(self) -> bool:
        """Evict least recently used entry.
        
        Returns:
            True if an entry was evicted, False if cache is empty
        """
        if not self._cache:
            return False
        
        # Remove first item (least recently used)
        self._cache.popitem(last=False)
        self._stats.evictions += 1
        return True
    
    def _estimate_memory_usage(self) -> int:
        """Estimate total memory usage of cache.
        
        Returns:
            Estimated memory usage in bytes
        """
        return sum(entry.size_bytes for entry in self._cache.values())
    
    def _update_memory_stats(self) -> None:
        """Update memory statistics."""
        self._stats.current_entries = len(self._cache)
        self._stats.memory_usage_bytes = self._estimate_memory_usage()
    
    async def _background_cleanup(self) -> None:
        """Background task for periodic cleanup."""
        while not self._stopped:
            try:
                await asyncio.sleep(self.cleanup_interval_seconds)
                
                with self._lock:
                    expired_count = self._evict_expired()
                    if expired_count > 0:
                        logger.debug(f"Background cleanup removed {expired_count} expired entries")
                        self._update_memory_stats()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cache background cleanup: {e}")
                await asyncio.sleep(60)  # Back off on error
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics.
        
        Returns:
            Current cache statistics
        """
        with self._lock:
            self._update_memory_stats()
            return CacheStats(
                total_gets=self._stats.total_gets,
                cache_hits=self._stats.cache_hits,
                cache_misses=self._stats.cache_misses,
                total_sets=self._stats.total_sets,
                evictions=self._stats.evictions,
                expirations=self._stats.expirations,
                current_size=len(self._cache),
                current_entries=len(self._cache),
                memory_usage_bytes=self._stats.memory_usage_bytes
            )
    
    def get_keys(self) -> List[str]:
        """Get all cache keys.
        
        Returns:
            List of cache keys
        """
        with self._lock:
            return list(self._cache.keys())
    
    def __len__(self) -> int:
        """Get number of entries in cache."""
        return len(self._cache)
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            entry = self._cache.get(key)
            return entry is not None and not entry.is_expired


class MultiTierCacheStorage:
    """Multi-tier cache storage with memory and persistent layers.
    
    Combines fast in-memory LRU cache with persistent LMDB storage
    for scalable caching with memory pressure handling.
    """
    
    def __init__(
        self,
        memory_cache_size: int = 1000,
        memory_cache_mb: int = 100,
        persistent_storage: Optional[LMDBStorage] = None,
        enable_persistent: bool = True,
        default_ttl_seconds: Optional[int] = 3600  # 1 hour
    ):
        """Initialize multi-tier cache.
        
        Args:
            memory_cache_size: Max entries in memory cache
            memory_cache_mb: Max memory usage for memory cache
            persistent_storage: LMDB storage for persistent tier
            enable_persistent: Whether to enable persistent caching
            default_ttl_seconds: Default TTL for cache entries
        """
        self.enable_persistent = enable_persistent
        self.default_ttl_seconds = default_ttl_seconds
        
        # Memory tier (L1 cache)
        self.memory_cache = LRUCache(
            max_size=memory_cache_size,
            max_memory_mb=memory_cache_mb,
            default_ttl_seconds=default_ttl_seconds
        )
        
        # Persistent tier (L2 cache)
        self.persistent_storage = persistent_storage
        self._persistent_db = "cache"
        
        # Combined statistics
        self._total_stats = CacheStats()
        
        logger.info(f"Initialized multi-tier cache (memory: {memory_cache_size} entries, persistent: {enable_persistent})")
    
    async def start(self) -> None:
        """Start cache components."""
        await self.memory_cache.start()
        
        if self.enable_persistent and self.persistent_storage:
            await self.persistent_storage.initialize()
        
        logger.info("Multi-tier cache started")
    
    async def stop(self) -> None:
        """Stop cache components."""
        await self.memory_cache.stop()
        
        if self.persistent_storage:
            await self.persistent_storage.close()
        
        logger.info("Multi-tier cache stopped")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache (checks memory first, then persistent).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        self._total_stats.total_gets += 1
        
        # Try memory cache first (L1)
        value = self.memory_cache.get(key)
        if value is not None:
            self._total_stats.cache_hits += 1
            return value
        
        # Try persistent cache (L2)
        if self.enable_persistent and self.persistent_storage:
            try:
                cache_entry = await self.persistent_storage.load_entity(
                    self._make_persistent_key(key),
                    CacheEntry,
                    self._persistent_db
                )
                
                if cache_entry is not None and not cache_entry.is_expired:
                    # Promote to memory cache
                    self.memory_cache.set(key, cache_entry.value, cache_entry.ttl_seconds)
                    self._total_stats.cache_hits += 1
                    return cache_entry.value
                elif cache_entry is not None:
                    # Expired entry - clean up
                    await self.persistent_storage.delete_entity(
                        self._make_persistent_key(key),
                        self._persistent_db
                    )
            
            except Exception as e:
                logger.warning(f"Failed to read from persistent cache: {e}")
        
        self._total_stats.cache_misses += 1
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache (stores in both tiers).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL for this entry
        """
        self._total_stats.total_sets += 1
        
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl_seconds
        
        # Store in memory cache (L1)
        self.memory_cache.set(key, value, ttl_seconds)
        
        # Store in persistent cache (L2)
        if self.enable_persistent and self.persistent_storage:
            try:
                now = datetime.now()
                cache_entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=now,
                    last_accessed=now,
                    access_count=1,
                    ttl_seconds=ttl_seconds
                )
                
                await self.persistent_storage.store_entity(
                    cache_entry,
                    self._make_persistent_key(key),
                    self._persistent_db
                )
                
            except Exception as e:
                logger.warning(f"Failed to write to persistent cache: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete entry from cache (removes from both tiers).
        
        Args:
            key: Cache key
            
        Returns:
            True if key was found in any tier, False otherwise
        """
        found_memory = self.memory_cache.delete(key)
        found_persistent = False
        
        if self.enable_persistent and self.persistent_storage:
            try:
                found_persistent = await self.persistent_storage.delete_entity(
                    self._make_persistent_key(key),
                    self._persistent_db
                )
            except Exception as e:
                logger.warning(f"Failed to delete from persistent cache: {e}")
        
        return found_memory or found_persistent
    
    async def clear(self) -> None:
        """Clear all entries from cache."""
        self.memory_cache.clear()
        
        if self.enable_persistent and self.persistent_storage:
            try:
                # Clear persistent cache by deleting all entries with cache prefix
                # This is a simplified approach - in production you might want
                # a more efficient bulk delete operation
                pass  # TODO: Implement bulk delete for LMDB
            except Exception as e:
                logger.warning(f"Failed to clear persistent cache: {e}")
        
        self._total_stats = CacheStats()
    
    def _make_persistent_key(self, key: str) -> str:
        """Create a persistent storage key.
        
        Args:
            key: Original cache key
            
        Returns:
            Persistent storage key
        """
        return f"cache:{key}"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get combined cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        memory_stats = self.memory_cache.get_stats()
        
        return {
            'total': {
                'gets': self._total_stats.total_gets,
                'hits': self._total_stats.cache_hits,
                'misses': self._total_stats.cache_misses,
                'sets': self._total_stats.total_sets,
                'hit_rate': self._total_stats.hit_rate,
            },
            'memory': {
                'entries': memory_stats.current_entries,
                'memory_bytes': memory_stats.memory_usage_bytes,
                'evictions': memory_stats.evictions,
                'expirations': memory_stats.expirations,
                'hit_rate': memory_stats.hit_rate,
            },
            'persistent': {
                'enabled': self.enable_persistent,
                'storage_available': self.persistent_storage is not None,
            },
            'config': {
                'default_ttl_seconds': self.default_ttl_seconds,
            }
        }
    
    @asynccontextmanager
    async def lifespan(self):
        """Context manager for cache lifecycle."""
        await self.start()
        try:
            yield self
        finally:
            await self.stop()
    
    def __str__(self) -> str:
        """String representation."""
        return f"MultiTierCacheStorage(memory_entries={len(self.memory_cache)}, persistent={self.enable_persistent})"
