"""LMDB implementation of LLMCacheRepository.

Provides concrete LMDB-backed storage for LLM response caching with
workspace isolation and cache management capabilities.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta

from ...domains.execution.repositories.llm_cache_repository import LLMCacheRepository
from ...domains.execution.value_objects.cache_key import CacheKey
from ...domains.execution.value_objects.model_name import ModelName
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError, EntityNotFoundError
from ..base.repository_base import LMDBRepositoryBase
from ..base.storage_manager import LMDBStorageManager
from ..base.serialization import DomainEntitySerializer


class CachedResponse:
    """Cached LLM response entity."""
    
    def __init__(
        self,
        cache_key: CacheKey,
        model_name: ModelName,
        prompt: str,
        response: str,
        created_at: datetime,
        expires_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.cache_key = cache_key
        self.model_name = model_name
        self.prompt = prompt
        self.response = response
        self.created_at = created_at
        self.expires_at = expires_at
        self.metadata = metadata or {}
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at


class LMDBLLMCacheRepository(LMDBRepositoryBase[CachedResponse], LLMCacheRepository):
    """LMDB implementation of LLMCacheRepository.
    
    Stores LLM response cache with workspace isolation and provides
    cache management with TTL and eviction capabilities.
    """
    
    def __init__(
        self, 
        storage_manager: LMDBStorageManager,
        workspace_name: WorkspaceName
    ):
        """Initialize repository.
        
        Args:
            storage_manager: LMDB storage manager
            workspace_name: Workspace for data isolation
        """
        super().__init__(
            storage_manager=storage_manager,
            workspace_name=workspace_name,
            entity_type=CachedResponse,
            db_name="llm_cache",
            db_key="responses"
        )
    
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with cache-specific types."""
        serializer.register_value_object(CacheKey)
        serializer.register_value_object(ModelName)
        serializer.register_value_object(WorkspaceName)
        serializer.register_type("CachedResponse", CachedResponse)
    
    def _get_entity_id(self, entity: CachedResponse) -> Any:
        """Extract entity ID for storage key."""
        return entity.cache_key
    
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID."""
        workspace_prefix = self._get_workspace_prefix()
        if isinstance(entity_id, CacheKey):
            return f"{workspace_prefix}cache:{entity_id.value}"
        else:
            return f"{workspace_prefix}cache:{str(entity_id)}"
    
    async def get_cached_response(
        self, 
        cache_key: CacheKey
    ) -> Optional[str]:
        """Get cached response for the given key."""
        cached = await self.find_by_id(cache_key)
        if cached is None or cached.is_expired:
            return None
        return cached.response
    
    async def store_response(
        self,
        cache_key: CacheKey,
        model_name: ModelName,
        prompt: str,
        response: str,
        ttl_hours: Optional[int] = None
    ) -> None:
        """Store LLM response in cache."""
        expires_at = None
        if ttl_hours:
            expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        cached_response = CachedResponse(
            cache_key=cache_key,
            model_name=model_name,
            prompt=prompt,
            response=response,
            created_at=datetime.now(),
            expires_at=expires_at
        )
        
        await self.save(cached_response)
    
    async def invalidate_cache(self, cache_key: CacheKey) -> bool:
        """Remove specific cache entry."""
        return await self.delete_by_id(cache_key)
    
    async def invalidate_model_cache(self, model_name: ModelName) -> int:
        """Remove all cache entries for a specific model."""
        all_cached = await self.find_by_workspace()
        model_cached = [c for c in all_cached if c.model_name == model_name]
        
        deleted_count = 0
        for cached in model_cached:
            if await self.delete_by_id(cached.cache_key):
                deleted_count += 1
        
        return deleted_count
    
    async def cleanup_expired_entries(self) -> int:
        """Remove expired cache entries."""
        all_cached = await self.find_by_workspace()
        expired = [c for c in all_cached if c.is_expired]
        
        deleted_count = 0
        for cached in expired:
            if await self.delete_by_id(cached.cache_key):
                deleted_count += 1
        
        return deleted_count
    
    async def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache usage statistics."""
        all_cached = await self.find_by_workspace()
        
        if not all_cached:
            return {
                "total_entries": 0,
                "expired_entries": 0,
                "models": {},
                "hit_rate": 0.0,
                "average_age_hours": 0.0
            }
        
        expired = [c for c in all_cached if c.is_expired]
        
        # Count by model
        models = {}
        total_age = timedelta(0)
        
        for cached in all_cached:
            model = str(cached.model_name)
            models[model] = models.get(model, 0) + 1
            total_age += datetime.now() - cached.created_at
        
        avg_age_hours = total_age.total_seconds() / 3600 / len(all_cached) if all_cached else 0
        
        return {
            "total_entries": len(all_cached),
            "expired_entries": len(expired),
            "models": models,
            "average_age_hours": avg_age_hours
        }
    
    async def find_by_model(self, model_name: ModelName) -> List[CachedResponse]:
        """Find all cache entries for a specific model."""
        all_cached = await self.find_by_workspace()
        return [c for c in all_cached if c.model_name == model_name]