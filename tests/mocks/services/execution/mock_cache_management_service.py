"""Mock implementation of CacheManagementService for testing."""

from typing import Dict, List, Any, Optional
from unittest.mock import Mock
from datetime import datetime, timedelta

from writeit.domains.execution.services.cache_management_service import (
    CacheManagementService,
    CacheEntry,
    CacheStrategy,
    CacheStatistics,
    CacheEvictionPolicy
)
from writeit.domains.execution.value_objects.cache_key import CacheKey


class MockCacheManagementService(CacheManagementService):
    """Mock implementation of CacheManagementService.
    
    Provides configurable cache management behavior for testing
    cache management scenarios without actual business logic execution.
    """
    
    def __init__(self):
        """Initialize mock cache management service."""
        self._mock = Mock()
        self._cache_entries: Dict[str, CacheEntry] = {}
        self._cache_statistics = CacheStatistics(
            hit_count=0,
            miss_count=0,
            eviction_count=0,
            total_size=0,
            average_access_time=0.0
        )
        self._should_fail = False
        self._cache_hit_rate = 0.8  # 80% hit rate by default
        
    def configure_cache_entry(self, key: str, entry: CacheEntry) -> None:
        """Configure cache entry for specific key."""
        self._cache_entries[key] = entry
        
    def configure_cache_statistics(self, stats: CacheStatistics) -> None:
        """Configure cache statistics."""
        self._cache_statistics = stats
        
    def configure_cache_hit_rate(self, hit_rate: float) -> None:
        """Configure cache hit rate (0.0 to 1.0)."""
        self._cache_hit_rate = max(0.0, min(1.0, hit_rate))
        
    def configure_failure(self, should_fail: bool) -> None:
        """Configure if cache operations should fail."""
        self._should_fail = should_fail
        
    def clear_configuration(self) -> None:
        """Clear all configuration."""
        self._cache_entries.clear()
        self._cache_statistics = CacheStatistics(
            hit_count=0,
            miss_count=0,
            eviction_count=0,
            total_size=0,
            average_access_time=0.0
        )
        self._should_fail = False
        self._cache_hit_rate = 0.8
        self._mock.reset_mock()
        
    @property
    def mock(self) -> Mock:
        """Get underlying mock for assertion."""
        return self._mock
        
    # Service interface implementation
    
    async def get_cached_value(
        self,
        cache_key: CacheKey,
        default: Optional[Any] = None
    ) -> Any:
        """Get value from cache."""
        self._mock.get_cached_value(cache_key, default)
        
        if self._should_fail:
            raise Exception("Mock cache retrieval error")
            
        key_str = str(cache_key.value)
        
        # Simulate cache hit/miss based on configured hit rate
        import random
        if random.random() < self._cache_hit_rate:
            # Cache hit
            if key_str in self._cache_entries:
                entry = self._cache_entries[key_str]
                if entry.expires_at and entry.expires_at < datetime.now():
                    # Expired entry
                    return default
                return entry.value
            else:
                # Return mock cached value
                return f"Mock cached value for {key_str}"
        else:
            # Cache miss
            return default
            
    async def set_cached_value(
        self,
        cache_key: CacheKey,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Set value in cache."""
        self._mock.set_cached_value(cache_key, value, ttl_seconds)
        
        if self._should_fail:
            raise Exception("Mock cache storage error")
            
        key_str = str(cache_key.value)
        expires_at = None
        if ttl_seconds:
            expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
            
        self._cache_entries[key_str] = CacheEntry(
            key=cache_key,
            value=value,
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            expires_at=expires_at,
            access_count=1
        )
        
    async def invalidate_cache_key(self, cache_key: CacheKey) -> bool:
        """Invalidate specific cache key."""
        self._mock.invalidate_cache_key(cache_key)
        
        if self._should_fail:
            return False
            
        key_str = str(cache_key.value)
        if key_str in self._cache_entries:
            del self._cache_entries[key_str]
            return True
        return False
        
    async def invalidate_cache_pattern(self, pattern: str) -> int:
        """Invalidate cache keys matching pattern."""
        self._mock.invalidate_cache_pattern(pattern)
        
        if self._should_fail:
            return 0
            
        # Simple pattern matching for mock
        invalidated_count = 0
        keys_to_remove = []
        
        for key in self._cache_entries.keys():
            if pattern in key or pattern == "*":
                keys_to_remove.append(key)
                
        for key in keys_to_remove:
            del self._cache_entries[key]
            invalidated_count += 1
            
        return invalidated_count
        
    async def clear_cache(self) -> None:
        """Clear entire cache."""
        self._mock.clear_cache()
        
        if not self._should_fail:
            self._cache_entries.clear()
            
    async def get_cache_statistics(self) -> CacheStatistics:
        """Get cache performance statistics."""
        self._mock.get_cache_statistics()
        
        # Update statistics based on current state
        total_size = len(self._cache_entries)
        
        return CacheStatistics(
            hit_count=int(self._cache_statistics.hit_count + total_size * self._cache_hit_rate),
            miss_count=int(self._cache_statistics.miss_count + total_size * (1 - self._cache_hit_rate)),
            eviction_count=self._cache_statistics.eviction_count,
            total_size=total_size,
            average_access_time=self._cache_statistics.average_access_time
        )
        
    async def optimize_cache(
        self,
        strategy: Optional[CacheStrategy] = None
    ) -> Dict[str, Any]:
        """Optimize cache performance."""
        self._mock.optimize_cache(strategy)
        
        if self._should_fail:
            return {"success": False, "error": "Mock optimization error"}
            
        return {
            "success": True,
            "optimized_entries": len(self._cache_entries),
            "space_freed": "10MB",
            "performance_improvement": "15%"
        }
        
    async def configure_eviction_policy(
        self,
        policy: CacheEvictionPolicy,
        parameters: Optional[Dict[str, Any]] = None
    ) -> None:
        """Configure cache eviction policy."""
        self._mock.configure_eviction_policy(policy, parameters)
        
        # Mock configuration - just track the call
        pass
        
    async def get_cache_size_info(self) -> Dict[str, Any]:
        """Get cache size information."""
        self._mock.get_cache_size_info()
        
        return {
            "total_entries": len(self._cache_entries),
            "memory_usage_bytes": len(self._cache_entries) * 1024,  # Mock 1KB per entry
            "disk_usage_bytes": len(self._cache_entries) * 2048,  # Mock 2KB per entry
            "max_size_entries": 10000,
            "max_memory_bytes": 100 * 1024 * 1024  # 100MB
        }
        
    async def preload_cache(
        self,
        cache_keys: List[CacheKey],
        value_loader: Any  # Callable to load values
    ) -> int:
        """Preload cache with values."""
        self._mock.preload_cache(cache_keys, value_loader)
        
        if self._should_fail:
            return 0
            
        # Mock preloading
        loaded_count = 0
        for cache_key in cache_keys:
            key_str = str(cache_key.value)
            if key_str not in self._cache_entries:
                self._cache_entries[key_str] = CacheEntry(
                    key=cache_key,
                    value=f"Preloaded value for {key_str}",
                    created_at=datetime.now(),
                    accessed_at=datetime.now(),
                    expires_at=None,
                    access_count=0
                )
                loaded_count += 1
                
        return loaded_count
        
    async def export_cache_data(
        self,
        export_format: str = "json"
    ) -> Dict[str, Any]:
        """Export cache data for backup or analysis."""
        self._mock.export_cache_data(export_format)
        
        if self._should_fail:
            return {"success": False, "error": "Mock export error"}
            
        return {
            "success": True,
            "format": export_format,
            "entries_count": len(self._cache_entries),
            "export_timestamp": datetime.now().isoformat(),
            "data_size_bytes": len(self._cache_entries) * 1024
        }
        
    async def import_cache_data(
        self,
        cache_data: Dict[str, Any]
    ) -> bool:
        """Import cache data from backup."""
        self._mock.import_cache_data(cache_data)
        
        return not self._should_fail
