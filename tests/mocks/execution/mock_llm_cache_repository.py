"""Mock implementation of LLMCacheRepository for testing."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from writeit.domains.execution.repositories.llm_cache_repository import (
    LLMCacheRepository, CacheEntry
)
from writeit.domains.execution.value_objects.cache_key import CacheKey
from writeit.domains.execution.value_objects.model_name import ModelName
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError


class MockLLMCacheRepository(BaseMockRepository[CacheEntry], LLMCacheRepository):
    """Mock implementation of LLMCacheRepository.
    
    Provides in-memory LLM response caching with TTL management,
    eviction policies, and cache analytics.
    """
    
    def __init__(self):
        # Cache repository doesn't have workspace isolation
        super().__init__(None)
        self._cache_hits = 0
        self._cache_misses = 0
        
    def _get_entity_id(self, entity: CacheEntry) -> Any:
        """Extract entity ID from cache entry."""
        return str(entity.cache_key.value)
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "CacheEntry"
        
    # Repository interface implementation
    
    async def save(self, entity: CacheEntry) -> None:
        """Save or update a cache entry."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id, workspace="global")
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: CacheKey) -> Optional[CacheEntry]:
        """Find cache entry by cache key."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        entry = self._get_entity(str(entity_id.value), workspace="global")
        
        # Check expiration
        if entry and entry.is_expired:
            self._delete_entity(str(entity_id.value), workspace="global")
            entry = None
            
        self._log_event("find_by_id", self._get_entity_type_name(), 
                       str(entity_id.value), found=entry is not None)
        return entry
        
    async def find_all(self) -> List[CacheEntry]:
        """Find all cache entries."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        entries = self._get_all_entities(workspace="global")
        
        # Filter out expired entries
        valid_entries = [e for e in entries if not e.is_expired]
        
        self._log_event("find_all", self._get_entity_type_name(), count=len(valid_entries))
        return valid_entries
        
    async def find_by_specification(self, spec: Specification[CacheEntry]) -> List[CacheEntry]:
        """Find cache entries matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        entries = self._find_entities_by_specification(spec, workspace="global")
        
        # Filter out expired entries
        valid_entries = [e for e in entries if not e.is_expired]
        
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(valid_entries))
        return valid_entries
        
    async def exists(self, entity_id: CacheKey) -> bool:
        """Check if cache entry exists and is not expired."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        entry = await self.find_by_id(entity_id)
        exists = entry is not None
        self._log_event("exists", self._get_entity_type_name(), str(entity_id.value), exists=exists)
        return exists
        
    async def delete(self, entity: CacheEntry) -> None:
        """Delete a cache entry."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id, workspace="global"):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: CacheKey) -> bool:
        """Delete cache entry by cache key."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(str(entity_id.value), workspace="global")
        self._log_event("delete_by_id", self._get_entity_type_name(), 
                       str(entity_id.value), deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total non-expired cache entries."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        entries = await self.find_all()
        total = len(entries)
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    # LLMCacheRepository-specific methods
    
    async def get_cached_response(
        self, 
        cache_key: CacheKey
    ) -> Optional[CacheEntry]:
        """Get cached response by key."""
        entry = await self.find_by_id(cache_key)
        if entry:
            self._cache_hits += 1
            # Update last accessed time and hit count
            updated_entry = CacheEntry(
                cache_key=entry.cache_key,
                model_name=entry.model_name,
                prompt=entry.prompt,
                response=entry.response,
                created_at=entry.created_at,
                expires_at=entry.expires_at,
                hit_count=entry.hit_count + 1,
                last_accessed=datetime.now(),
                metadata=entry.metadata,
                tokens_used=entry.tokens_used,
                response_time_ms=entry.response_time_ms
            )
            await self.save(updated_entry)
            return updated_entry
        else:
            self._cache_misses += 1
            return None
            
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
        """Store LLM response in cache."""
        await self._check_error_condition("store_response")
        self._increment_call_count("store_response")
        await self._apply_call_delay("store_response")
        
        created_at = datetime.now()
        expires_at = None
        if ttl_seconds:
            expires_at = created_at + timedelta(seconds=ttl_seconds)
            
        entry = CacheEntry(
            cache_key=cache_key,
            model_name=model_name,
            prompt=prompt,
            response=response,
            created_at=created_at,
            expires_at=expires_at,
            hit_count=0,
            last_accessed=None,
            metadata=metadata,
            tokens_used=tokens_used,
            response_time_ms=response_time_ms
        )
        
        await self.save(entry)
        self._log_event("store_response", self._get_entity_type_name(), 
                       str(cache_key.value), ttl_seconds=ttl_seconds)
        return entry
        
    async def invalidate_cache(self, cache_key: CacheKey) -> bool:
        """Invalidate (delete) cached response."""
        return await self.delete_by_id(cache_key)
        
    async def find_by_model(self, model_name: ModelName) -> List[CacheEntry]:
        """Find all cache entries for a specific model."""
        await self._check_error_condition("find_by_model")
        self._increment_call_count("find_by_model")
        await self._apply_call_delay("find_by_model")
        
        entries = await self.find_all()
        matching_entries = [e for e in entries if e.model_name == model_name]
        
        self._log_event("find_by_model", self._get_entity_type_name(), 
                       count=len(matching_entries), model_name=str(model_name.value))
        return matching_entries
        
    async def find_expired_entries(
        self, 
        as_of: Optional[datetime] = None
    ) -> List[CacheEntry]:
        """Find all expired cache entries."""
        await self._check_error_condition("find_expired_entries")
        self._increment_call_count("find_expired_entries")
        await self._apply_call_delay("find_expired_entries")
        
        check_time = as_of or datetime.now()
        entries = self._get_all_entities(workspace="global")
        
        expired_entries = []
        for entry in entries:
            if entry.expires_at and entry.expires_at <= check_time:
                expired_entries.append(entry)
                
        self._log_event("find_expired_entries", self._get_entity_type_name(), 
                       count=len(expired_entries), as_of=check_time)
        return expired_entries
        
    async def find_least_recently_used(
        self, 
        limit: int = 100
    ) -> List[CacheEntry]:
        """Find least recently used cache entries."""
        await self._check_error_condition("find_least_recently_used")
        self._increment_call_count("find_least_recently_used")
        await self._apply_call_delay("find_least_recently_used")
        
        entries = await self.find_all()
        
        # Sort by last accessed time (None values last)
        entries.sort(key=lambda e: e.last_accessed or datetime.min)
        lru_entries = entries[:limit]
        
        self._log_event("find_least_recently_used", self._get_entity_type_name(), 
                       count=len(lru_entries), limit=limit)
        return lru_entries
        
    async def cleanup_expired_entries(self) -> int:
        """Remove all expired cache entries."""
        await self._check_error_condition("cleanup_expired_entries")
        self._increment_call_count("cleanup_expired_entries")
        await self._apply_call_delay("cleanup_expired_entries")
        
        expired_entries = await self.find_expired_entries()
        
        deleted_count = 0
        for entry in expired_entries:
            await self.delete(entry)
            deleted_count += 1
            
        self._log_event("cleanup_expired_entries", self._get_entity_type_name(), 
                       deleted_count=deleted_count)
        return deleted_count
        
    async def evict_lru_entries(
        self, 
        target_count: int
    ) -> int:
        """Evict least recently used entries to reach target count."""
        await self._check_error_condition("evict_lru_entries")
        self._increment_call_count("evict_lru_entries")
        await self._apply_call_delay("evict_lru_entries")
        
        current_count = await self.count()
        if current_count <= target_count:
            return 0
            
        entries_to_evict = current_count - target_count
        lru_entries = await self.find_least_recently_used(entries_to_evict)
        
        evicted_count = 0
        for entry in lru_entries:
            await self.delete(entry)
            evicted_count += 1
            
        self._log_event("evict_lru_entries", self._get_entity_type_name(), 
                       evicted_count=evicted_count, target_count=target_count)
        return evicted_count
        
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and performance metrics."""
        await self._check_error_condition("get_cache_stats")
        self._increment_call_count("get_cache_stats")
        await self._apply_call_delay("get_cache_stats")
        
        entries = await self.find_all()
        expired_entries = await self.find_expired_entries()
        
        total_size = sum(len(e.response.encode('utf-8')) for e in entries)
        total_hits = sum(e.hit_count for e in entries)
        
        # Calculate hit rate
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        # Average age
        now = datetime.now()
        avg_age = sum(e.age_seconds for e in entries) / len(entries) if entries else 0
        
        # Most popular models
        model_counts = {}
        for entry in entries:
            model = str(entry.model_name.value)
            model_counts[model] = model_counts.get(model, 0) + 1
            
        most_popular_models = sorted(model_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        stats = {
            "total_entries": len(entries),
            "total_size_bytes": total_size,
            "hit_rate": hit_rate,
            "average_age_seconds": avg_age,
            "expired_entries": len(expired_entries),
            "most_popular_models": [{"model": model, "count": count} for model, count in most_popular_models],
            "memory_usage": {
                "total_bytes": total_size,
                "entries_count": len(entries),
                "average_entry_size": total_size / len(entries) if entries else 0
            }
        }
        
        self._log_event("get_cache_stats", self._get_entity_type_name(), **stats)
        return stats
        
    async def get_hit_rate_stats(
        self, 
        since: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get cache hit rate statistics."""
        await self._check_error_condition("get_hit_rate_stats")
        self._increment_call_count("get_hit_rate_stats")
        await self._apply_call_delay("get_hit_rate_stats")
        
        # Mock hit rate statistics
        total_requests = self._cache_hits + self._cache_misses
        overall_hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            "overall_hit_rate": overall_hit_rate,
            "model_hit_rates": self._behavior.return_values.get("model_hit_rates", {
                "gpt-4o-mini": 75.5,
                "claude-3-haiku": 68.2,
                "gemini-pro": 72.1
            }),
            "hourly_hit_rates": self._behavior.return_values.get("hourly_hit_rates", {
                "00": 45.0, "06": 55.0, "12": 85.0, "18": 70.0
            })
        }
        
        self._log_event("get_hit_rate_stats", self._get_entity_type_name(), 
                       since=since, **stats)
        return stats
        
    async def record_cache_hit(self, cache_key: CacheKey) -> None:
        """Record a cache hit for analytics."""
        await self._check_error_condition("record_cache_hit")
        self._increment_call_count("record_cache_hit")
        await self._apply_call_delay("record_cache_hit")
        
        self._cache_hits += 1
        self._log_event("record_cache_hit", self._get_entity_type_name(), 
                       str(cache_key.value))
        
    async def record_cache_miss(
        self, 
        cache_key: CacheKey, 
        model_name: ModelName
    ) -> None:
        """Record a cache miss for analytics."""
        await self._check_error_condition("record_cache_miss")
        self._increment_call_count("record_cache_miss")
        await self._apply_call_delay("record_cache_miss")
        
        self._cache_misses += 1
        self._log_event("record_cache_miss", self._get_entity_type_name(), 
                       str(cache_key.value), model_name=str(model_name.value))
        
    async def update_ttl(
        self, 
        cache_key: CacheKey, 
        new_ttl_seconds: int
    ) -> bool:
        """Update TTL for a cache entry."""
        await self._check_error_condition("update_ttl")
        self._increment_call_count("update_ttl")
        await self._apply_call_delay("update_ttl")
        
        entry = await self.find_by_id(cache_key)
        if not entry:
            return False
            
        new_expires_at = datetime.now() + timedelta(seconds=new_ttl_seconds)
        updated_entry = CacheEntry(
            cache_key=entry.cache_key,
            model_name=entry.model_name,
            prompt=entry.prompt,
            response=entry.response,
            created_at=entry.created_at,
            expires_at=new_expires_at,
            hit_count=entry.hit_count,
            last_accessed=entry.last_accessed,
            metadata=entry.metadata,
            tokens_used=entry.tokens_used,
            response_time_ms=entry.response_time_ms
        )
        
        await self.save(updated_entry)
        self._log_event("update_ttl", self._get_entity_type_name(), 
                       str(cache_key.value), new_ttl_seconds=new_ttl_seconds)
        return True
        
    async def get_memory_usage(self) -> Dict[str, int]:
        """Get cache memory usage information."""
        await self._check_error_condition("get_memory_usage")
        self._increment_call_count("get_memory_usage")
        await self._apply_call_delay("get_memory_usage")
        
        entries = await self.find_all()
        
        if not entries:
            usage = {
                "total_bytes": 0,
                "entries_count": 0,
                "average_entry_size": 0,
                "largest_entry_size": 0
            }
        else:
            entry_sizes = [len(e.response.encode('utf-8')) for e in entries]
            total_bytes = sum(entry_sizes)
            
            usage = {
                "total_bytes": total_bytes,
                "entries_count": len(entries),
                "average_entry_size": total_bytes // len(entries),
                "largest_entry_size": max(entry_sizes)
            }
            
        self._log_event("get_memory_usage", self._get_entity_type_name(), **usage)
        return usage
        
    async def optimize_cache(self) -> Dict[str, int]:
        """Optimize cache by removing expired entries and compacting storage."""
        await self._check_error_condition("optimize_cache")
        self._increment_call_count("optimize_cache")
        await self._apply_call_delay("optimize_cache")
        
        # Clean up expired entries
        expired_removed = await self.cleanup_expired_entries()
        
        # Calculate space reclaimed (mock)
        space_reclaimed = expired_removed * 1024  # Assume 1KB per expired entry
        
        # Count remaining entries
        entries_remaining = await self.count()
        
        results = {
            "expired_removed": expired_removed,
            "space_reclaimed": space_reclaimed,
            "entries_remaining": entries_remaining
        }
        
        self._log_event("optimize_cache", self._get_entity_type_name(), **results)
        return results