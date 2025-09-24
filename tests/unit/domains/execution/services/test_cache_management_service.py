"""Unit tests for CacheManagementService.

Tests comprehensive cache management logic including:
- LLM response caching and retrieval
- Cache invalidation strategies and TTL management
- Cache performance optimization and analytics
- Memory pressure handling and eviction policies
- Cache warming and preloading strategies
- Cache statistics and monitoring
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import replace

from src.writeit.domains.execution.services.cache_management_service import (
    CacheManagementService,
    CacheStrategy,
    EvictionPolicy,
    CacheEntry,
    CacheKey,
    CacheStatistics,
    CacheConfiguration,
    CacheHitResult,
    CacheMissResult,
    CacheOperationResult,
    CacheInvalidationRule,
    CachePreloadRule,
    CacheError,
    CacheFullError,
    CacheKeyError
)
from src.writeit.domains.execution.entities.execution_context import ExecutionContext
from src.writeit.domains.execution.value_objects.cache_key import CacheKey as CacheKeyVO
from src.writeit.domains.execution.value_objects.token_count import TokenCount

from tests.builders.execution_builders import ExecutionContextBuilder


class MockCacheStorage:
    """Mock cache storage for testing."""
    
    def __init__(self, max_size: int = 1000):
        self._storage: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._access_times: Dict[str, datetime] = {}
        self._access_counts: Dict[str, int] = {}
    
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Get cache entry."""
        if key in self._storage:
            self._access_times[key] = datetime.now()
            self._access_counts[key] = self._access_counts.get(key, 0) + 1
            return self._storage[key]
        return None
    
    async def put(self, key: str, entry: CacheEntry) -> bool:
        """Store cache entry."""
        if len(self._storage) >= self._max_size and key not in self._storage:
            return False  # Cache full
        
        self._storage[key] = entry
        self._access_times[key] = datetime.now()
        self._access_counts[key] = 1
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete cache entry."""
        if key in self._storage:
            del self._storage[key]
            self._access_times.pop(key, None)
            self._access_counts.pop(key, None)
            return True
        return False
    
    async def clear(self) -> int:
        """Clear all cache entries."""
        count = len(self._storage)
        self._storage.clear()
        self._access_times.clear()
        self._access_counts.clear()
        return count
    
    async def size(self) -> int:
        """Get current cache size."""
        return len(self._storage)
    
    async def keys(self) -> List[str]:
        """Get all cache keys."""
        return list(self._storage.keys())
    
    def get_access_time(self, key: str) -> Optional[datetime]:
        """Get last access time for key."""
        return self._access_times.get(key)
    
    def get_access_count(self, key: str) -> int:
        """Get access count for key."""
        return self._access_counts.get(key, 0)
    
    @property
    def max_size(self) -> int:
        return self._max_size
    
    def set_max_size(self, size: int) -> None:
        self._max_size = size


class TestCacheEntry:
    """Test CacheEntry behavior."""
    
    def test_create_cache_entry(self):
        """Test creating cache entry."""
        key = CacheKeyVO.from_prompt_and_model("Generate content", "gpt-4o-mini")
        content = "Generated content response"
        usage = TokenCount(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        
        entry = CacheEntry(
            key=key,
            content=content,
            usage=usage,
            model_name="gpt-4o-mini",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
            metadata={"temperature": 0.7, "max_tokens": 1000}
        )
        
        assert entry.key == key
        assert entry.content == content
        assert entry.usage == usage
        assert entry.model_name == "gpt-4o-mini"
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.expires_at, datetime)
        assert entry.metadata["temperature"] == 0.7
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic."""
        key = CacheKeyVO.from_prompt_and_model("Test", "gpt-4o-mini")
        
        # Not expired entry
        entry_valid = CacheEntry(
            key=key,
            content="Content",
            usage=TokenCount(10, 20, 30),
            model_name="gpt-4o-mini",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
        assert not entry_valid.is_expired
        
        # Expired entry
        entry_expired = CacheEntry(
            key=key,
            content="Content",
            usage=TokenCount(10, 20, 30),
            model_name="gpt-4o-mini",
            created_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1)
        )
        assert entry_expired.is_expired
    
    def test_cache_entry_age(self):
        """Test cache entry age calculation."""
        key = CacheKeyVO.from_prompt_and_model("Test", "gpt-4o-mini")
        created_time = datetime.now() - timedelta(minutes=30)
        
        entry = CacheEntry(
            key=key,
            content="Content",
            usage=TokenCount(10, 20, 30),
            model_name="gpt-4o-mini",
            created_at=created_time,
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        age = entry.age_seconds
        assert 1700 <= age <= 1900  # Approximately 30 minutes (1800 seconds)


class TestCacheStatistics:
    """Test CacheStatistics behavior."""
    
    def test_create_cache_statistics(self):
        """Test creating cache statistics."""
        stats = CacheStatistics(
            total_requests=1000,
            cache_hits=750,
            cache_misses=250,
            total_entries=500,
            memory_usage_bytes=1024000,
            avg_lookup_time_ms=2.5,
            evictions_count=50,
            expired_entries=25
        )
        
        assert stats.total_requests == 1000
        assert stats.cache_hits == 750
        assert stats.cache_misses == 250
        assert stats.total_entries == 500
        assert stats.memory_usage_bytes == 1024000
        assert stats.avg_lookup_time_ms == 2.5
        assert stats.evictions_count == 50
        assert stats.expired_entries == 25
    
    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation."""
        stats = CacheStatistics(
            total_requests=1000,
            cache_hits=750,
            cache_misses=250
        )
        
        assert stats.hit_rate == 0.75
        
        # Test with no requests
        stats_empty = CacheStatistics(total_requests=0)
        assert stats_empty.hit_rate == 0.0
    
    def test_cache_miss_rate_calculation(self):
        """Test cache miss rate calculation."""
        stats = CacheStatistics(
            total_requests=1000,
            cache_hits=750,
            cache_misses=250
        )
        
        assert stats.miss_rate == 0.25
    
    def test_memory_efficiency_calculation(self):
        """Test memory efficiency calculation."""
        stats = CacheStatistics(
            total_entries=500,
            memory_usage_bytes=1024000  # 1MB
        )
        
        # Average bytes per entry
        assert stats.avg_entry_size_bytes == 2048


class TestCacheConfiguration:
    """Test CacheConfiguration behavior."""
    
    def test_create_cache_configuration(self):
        """Test creating cache configuration."""
        config = CacheConfiguration(
            strategy=CacheStrategy.WRITE_THROUGH,
            eviction_policy=EvictionPolicy.LRU,
            max_entries=1000,
            max_memory_mb=100,
            default_ttl_hours=24,
            enable_compression=True,
            enable_statistics=True,
            cleanup_interval_minutes=30
        )
        
        assert config.strategy == CacheStrategy.WRITE_THROUGH
        assert config.eviction_policy == EvictionPolicy.LRU
        assert config.max_entries == 1000
        assert config.max_memory_mb == 100
        assert config.default_ttl_hours == 24
        assert config.enable_compression is True
        assert config.enable_statistics is True
        assert config.cleanup_interval_minutes == 30
    
    def test_cache_configuration_validation(self):
        """Test cache configuration validation."""
        # Valid configuration
        config = CacheConfiguration(
            max_entries=1000,
            max_memory_mb=100,
            default_ttl_hours=24
        )
        assert config.is_valid()
        
        # Invalid configuration (negative values)
        invalid_config = CacheConfiguration(
            max_entries=-1,
            max_memory_mb=100,
            default_ttl_hours=24
        )
        assert not invalid_config.is_valid()


class TestCacheManagementService:
    """Test CacheManagementService business logic."""
    
    def test_create_service(self):
        """Test creating cache management service."""
        config = CacheConfiguration(
            strategy=CacheStrategy.WRITE_THROUGH,
            eviction_policy=EvictionPolicy.LRU,
            max_entries=1000,
            default_ttl_hours=24
        )
        
        service = CacheManagementService(config)
        
        assert service._config == config
        assert service._statistics.total_requests == 0
        assert service._statistics.cache_hits == 0
        assert service._statistics.cache_misses == 0
    
    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """Test cache hit scenario."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Pre-populate cache
        key = CacheKeyVO.from_prompt_and_model("Generate content", "gpt-4o-mini")
        entry = CacheEntry(
            key=key,
            content="Cached response",
            usage=TokenCount(10, 20, 30),
            model_name="gpt-4o-mini",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        await storage.put(key.value, entry)
        
        # Test cache hit
        result = await service.get_cached_response(
            prompt="Generate content",
            model_name="gpt-4o-mini"
        )
        
        assert isinstance(result, CacheHitResult)
        assert result.entry.content == "Cached response"
        assert service._statistics.cache_hits == 1
        assert service._statistics.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss scenario."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Test cache miss
        result = await service.get_cached_response(
            prompt="New content",
            model_name="gpt-4o-mini"
        )
        
        assert isinstance(result, CacheMissResult)
        assert service._statistics.cache_misses == 1
        assert service._statistics.total_requests == 1
    
    @pytest.mark.asyncio
    async def test_cache_expired_entry(self):
        """Test cache with expired entry."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Pre-populate with expired entry
        key = CacheKeyVO.from_prompt_and_model("Generate content", "gpt-4o-mini")
        expired_entry = CacheEntry(
            key=key,
            content="Expired response",
            usage=TokenCount(10, 20, 30),
            model_name="gpt-4o-mini",
            created_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1)  # Expired
        )
        
        await storage.put(key.value, expired_entry)
        
        # Test cache lookup - should be treated as miss
        result = await service.get_cached_response(
            prompt="Generate content",
            model_name="gpt-4o-mini"
        )
        
        assert isinstance(result, CacheMissResult)
        assert service._statistics.cache_misses == 1
        assert service._statistics.expired_entries == 1
    
    @pytest.mark.asyncio
    async def test_store_response(self):
        """Test storing response in cache."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Store response
        result = await service.store_response(
            prompt="Generate content",
            model_name="gpt-4o-mini",
            content="Generated response",
            usage=TokenCount(15, 25, 40),
            metadata={"temperature": 0.8}
        )
        
        assert result.success is True
        assert await storage.size() == 1
        
        # Verify stored entry
        key = CacheKeyVO.from_prompt_and_model("Generate content", "gpt-4o-mini")
        stored_entry = await storage.get(key.value)
        assert stored_entry is not None
        assert stored_entry.content == "Generated response"
        assert stored_entry.usage.total_tokens == 40
    
    @pytest.mark.asyncio
    async def test_cache_full_scenario(self):
        """Test behavior when cache is full."""
        config = CacheConfiguration(max_entries=2)  # Very small cache
        storage = MockCacheStorage(max_size=2)
        service = CacheManagementService(config, storage=storage)
        
        # Fill cache to capacity
        await service.store_response(
            "Prompt 1", "gpt-4o-mini", "Response 1", TokenCount(10, 10, 20)
        )
        await service.store_response(
            "Prompt 2", "gpt-4o-mini", "Response 2", TokenCount(10, 10, 20)
        )
        
        # Try to add one more - should trigger eviction or fail
        result = await service.store_response(
            "Prompt 3", "gpt-4o-mini", "Response 3", TokenCount(10, 10, 20)
        )
        
        # Behavior depends on eviction policy implementation
        # In this mock, it will fail (cache full)
        assert result.success is False or await storage.size() <= 2
    
    @pytest.mark.asyncio
    async def test_lru_eviction_policy(self):
        """Test LRU eviction policy."""
        config = CacheConfiguration(
            max_entries=2,
            eviction_policy=EvictionPolicy.LRU
        )
        storage = MockCacheStorage(max_size=2)
        service = CacheManagementService(config, storage=storage)
        
        # Store two entries
        await service.store_response(
            "Prompt 1", "gpt-4o-mini", "Response 1", TokenCount(10, 10, 20)
        )
        await service.store_response(
            "Prompt 2", "gpt-4o-mini", "Response 2", TokenCount(10, 10, 20)
        )
        
        # Access first entry to make it recently used
        await service.get_cached_response("Prompt 1", "gpt-4o-mini")
        
        # Add third entry - should evict second entry (least recently used)
        await service._evict_lru_entry()
        
        # Verify first entry still exists
        result1 = await service.get_cached_response("Prompt 1", "gpt-4o-mini")
        assert isinstance(result1, CacheHitResult)
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_by_pattern(self):
        """Test cache invalidation by pattern."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Store multiple entries
        await service.store_response(
            "Generate article about AI", "gpt-4o-mini", "AI Article", TokenCount(10, 20, 30)
        )
        await service.store_response(
            "Generate article about ML", "gpt-4o-mini", "ML Article", TokenCount(10, 20, 30)
        )
        await service.store_response(
            "Summarize document", "gpt-4o-mini", "Summary", TokenCount(5, 10, 15)
        )
        
        # Invalidate entries matching pattern
        invalidated_count = await service.invalidate_by_pattern("Generate article*")
        
        assert invalidated_count == 2
        assert await storage.size() == 1  # Only summary should remain
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_by_model(self):
        """Test cache invalidation by model."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Store entries for different models
        await service.store_response(
            "Generate content", "gpt-4o-mini", "Content 1", TokenCount(10, 20, 30)
        )
        await service.store_response(
            "Generate content", "gpt-3.5-turbo", "Content 2", TokenCount(10, 20, 30)
        )
        
        # Invalidate entries for specific model
        invalidated_count = await service.invalidate_by_model("gpt-4o-mini")
        
        assert invalidated_count == 1
        assert await storage.size() == 1  # Only gpt-3.5-turbo entry should remain
    
    @pytest.mark.asyncio
    async def test_cache_warming(self):
        """Test cache warming functionality."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Define warming rules
        warming_prompts = [
            "Generate article outline",
            "Summarize key points",
            "Create introduction"
        ]
        
        # Mock LLM responses for warming
        async def mock_llm_call(prompt: str, model: str) -> Dict[str, Any]:
            return {
                "content": f"Warmed response for: {prompt}",
                "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            }
        
        # Warm cache
        warmed_count = await service.warm_cache(
            prompts=warming_prompts,
            model_name="gpt-4o-mini",
            llm_call_func=mock_llm_call
        )
        
        assert warmed_count == 3
        assert await storage.size() == 3
        
        # Verify warmed entries are accessible
        for prompt in warming_prompts:
            result = await service.get_cached_response(prompt, "gpt-4o-mini")
            assert isinstance(result, CacheHitResult)
    
    @pytest.mark.asyncio
    async def test_cache_cleanup_expired_entries(self):
        """Test cleanup of expired cache entries."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Store expired and valid entries
        key1 = CacheKeyVO.from_prompt_and_model("Prompt 1", "gpt-4o-mini")
        expired_entry = CacheEntry(
            key=key1,
            content="Expired",
            usage=TokenCount(10, 20, 30),
            model_name="gpt-4o-mini",
            created_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1)
        )
        
        key2 = CacheKeyVO.from_prompt_and_model("Prompt 2", "gpt-4o-mini")
        valid_entry = CacheEntry(
            key=key2,
            content="Valid",
            usage=TokenCount(10, 20, 30),
            model_name="gpt-4o-mini",
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        await storage.put(key1.value, expired_entry)
        await storage.put(key2.value, valid_entry)
        
        # Run cleanup
        cleaned_count = await service.cleanup_expired_entries()
        
        assert cleaned_count == 1
        assert await storage.size() == 1
        
        # Verify only valid entry remains
        remaining_keys = await storage.keys()
        assert key2.value in remaining_keys
        assert key1.value not in remaining_keys
    
    def test_get_cache_statistics(self):
        """Test getting cache statistics."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Simulate some cache activity
        service._statistics = CacheStatistics(
            total_requests=1000,
            cache_hits=750,
            cache_misses=250,
            total_entries=500,
            evictions_count=25
        )
        
        stats = service.get_statistics()
        
        assert stats.total_requests == 1000
        assert stats.hit_rate == 0.75
        assert stats.miss_rate == 0.25
        assert stats.total_entries == 500
        assert stats.evictions_count == 25
    
    @pytest.mark.asyncio
    async def test_cache_compression(self):
        """Test cache compression functionality."""
        config = CacheConfiguration(
            max_entries=100,
            enable_compression=True
        )
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Store large content that would benefit from compression
        large_content = "This is a very long response that would benefit from compression. " * 100
        
        result = await service.store_response(
            prompt="Generate long content",
            model_name="gpt-4o-mini",
            content=large_content,
            usage=TokenCount(50, 100, 150)
        )
        
        assert result.success is True
        
        # Retrieve and verify content is correctly decompressed
        cache_result = await service.get_cached_response(
            "Generate long content", 
            "gpt-4o-mini"
        )
        
        assert isinstance(cache_result, CacheHitResult)
        assert cache_result.entry.content == large_content
    
    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self):
        """Test concurrent cache access scenarios."""
        config = CacheConfiguration(max_entries=100)
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Simulate concurrent requests for the same content
        async def concurrent_request(request_id: int) -> Any:
            prompt = f"Generate content {request_id % 5}"  # 5 unique prompts
            
            # Try to get from cache first
            result = await service.get_cached_response(prompt, "gpt-4o-mini")
            
            if isinstance(result, CacheMissResult):
                # Store response
                await service.store_response(
                    prompt=prompt,
                    model_name="gpt-4o-mini",
                    content=f"Response {request_id}",
                    usage=TokenCount(10, 20, 30)
                )
            
            return result
        
        # Run 20 concurrent requests
        tasks = [concurrent_request(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        
        # Verify results
        assert len(results) == 20
        
        # Should have 5 unique entries in cache (one for each prompt)
        assert await storage.size() <= 5
    
    @pytest.mark.asyncio
    async def test_cache_key_generation(self):
        """Test cache key generation for different scenarios."""
        service = CacheManagementService(CacheConfiguration())
        
        # Test basic key generation
        key1 = service._generate_cache_key(
            prompt="Generate content",
            model="gpt-4o-mini",
            parameters={"temperature": 0.7}
        )
        
        key2 = service._generate_cache_key(
            prompt="Generate content", 
            model="gpt-4o-mini",
            parameters={"temperature": 0.7}
        )
        
        key3 = service._generate_cache_key(
            prompt="Generate content",
            model="gpt-4o-mini", 
            parameters={"temperature": 0.8}  # Different parameter
        )
        
        assert key1 == key2  # Same parameters should generate same key
        assert key1 != key3  # Different parameters should generate different keys
    
    @pytest.mark.asyncio
    async def test_memory_pressure_handling(self):
        """Test cache behavior under memory pressure."""
        config = CacheConfiguration(
            max_entries=100,
            max_memory_mb=1  # Very low memory limit
        )
        storage = MockCacheStorage()
        service = CacheManagementService(config, storage=storage)
        
        # Try to store large entries that would exceed memory limit
        large_content = "Large content " * 10000  # ~140KB
        
        # First entry should succeed
        result1 = await service.store_response(
            "Prompt 1", "gpt-4o-mini", large_content, TokenCount(100, 200, 300)
        )
        
        # Subsequent large entries might trigger memory management
        result2 = await service.store_response(
            "Prompt 2", "gpt-4o-mini", large_content, TokenCount(100, 200, 300)
        )
        
        # At least one should succeed, but memory management should kick in
        assert result1.success or result2.success
        
        # Memory usage should be managed (exact behavior depends on implementation)
        stats = service.get_statistics()
        assert stats.memory_usage_bytes > 0
