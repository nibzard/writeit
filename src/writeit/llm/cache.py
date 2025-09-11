# ABOUTME: LLM response caching layer for WriteIt
# ABOUTME: Provides workspace-aware caching to avoid repeated LLM calls

import hashlib
import json
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import asyncio

from writeit.storage.manager import StorageManager


@dataclass
class CacheEntry:
    """Represents a cached LLM response."""
    cache_key: str
    prompt: str
    model_name: str
    response: str
    tokens_used: Dict[str, int]
    created_at: datetime
    accessed_at: datetime
    access_count: int = 1
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            'cache_key': self.cache_key,
            'prompt': self.prompt,
            'model_name': self.model_name,
            'response': self.response,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat(),
            'accessed_at': self.accessed_at.isoformat(),
            'access_count': self.access_count,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create from dictionary."""
        return cls(
            cache_key=data['cache_key'],
            prompt=data['prompt'],
            model_name=data['model_name'],
            response=data['response'],
            tokens_used=data['tokens_used'],
            created_at=datetime.fromisoformat(data['created_at']),
            accessed_at=datetime.fromisoformat(data['accessed_at']),
            access_count=data.get('access_count', 1),
            metadata=data.get('metadata', {})
        )
    
    def update_access(self):
        """Update access statistics."""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1


class LLMCache:
    """LLM response cache with workspace awareness."""
    
    def __init__(self, storage: StorageManager, workspace_name: str):
        self.storage = storage
        self.workspace_name = workspace_name
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
        
        # Cache configuration
        self.max_memory_entries = 1000  # Maximum entries to keep in memory
        self.default_ttl = timedelta(hours=24)  # Default TTL for cache entries
        self.enable_memory_cache = True
        
    def _generate_cache_key(
        self, 
        prompt: str, 
        model_name: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a cache key for the given prompt and model."""
        # Create a deterministic hash of the prompt, model, and context
        content = {
            'prompt': prompt.strip(),
            'model': model_name,
            'context': context or {},
            'workspace': self.workspace_name
        }
        
        # Sort keys for deterministic hashing
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()[:16]
    
    async def get(
        self, 
        prompt: str, 
        model_name: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[CacheEntry]:
        """Get cached response if available."""
        cache_key = self._generate_cache_key(prompt, model_name, context)
        
        # Check memory cache first
        if self.enable_memory_cache and cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            
            # Check if entry has expired
            if self._is_expired(entry):
                await self._remove_entry(cache_key)
                self.cache_stats['misses'] += 1
                return None
            
            # Update access statistics
            entry.update_access()
            await self._store_entry(entry)  # Update persistent storage
            self.cache_stats['hits'] += 1
            return entry
        
        # Check persistent storage
        try:
            entry_data = await self.storage.get_json(
                f"llm_cache_{cache_key}", 
                db_name="llm_cache"
            )
            
            if entry_data:
                entry = CacheEntry.from_dict(entry_data)
                
                # Check if entry has expired
                if self._is_expired(entry):
                    await self._remove_entry(cache_key)
                    self.cache_stats['misses'] += 1
                    return None
                
                # Update access statistics and add to memory cache
                entry.update_access()
                
                if self.enable_memory_cache:
                    await self._add_to_memory_cache(entry)
                
                await self._store_entry(entry)
                self.cache_stats['hits'] += 1
                return entry
                
        except Exception as e:
            # Log error but don't fail the request
            print(f"Cache retrieval error: {e}")
        
        self.cache_stats['misses'] += 1
        return None
    
    async def put(
        self, 
        prompt: str, 
        model_name: str, 
        response: str, 
        tokens_used: Dict[str, int],
        context: Optional[Dict[str, Any]] = None,
        ttl: Optional[timedelta] = None
    ) -> str:
        """Cache an LLM response."""
        cache_key = self._generate_cache_key(prompt, model_name, context)
        now = datetime.utcnow()
        
        entry = CacheEntry(
            cache_key=cache_key,
            prompt=prompt,
            model_name=model_name,
            response=response,
            tokens_used=tokens_used,
            created_at=now,
            accessed_at=now,
            metadata={
                'ttl_hours': (ttl or self.default_ttl).total_seconds() / 3600,
                'context': context or {}
            }
        )
        
        # Store in persistent storage
        await self._store_entry(entry)
        
        # Add to memory cache
        if self.enable_memory_cache:
            await self._add_to_memory_cache(entry)
        
        return cache_key
    
    async def invalidate(
        self, 
        prompt: str, 
        model_name: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Invalidate a specific cache entry."""
        cache_key = self._generate_cache_key(prompt, model_name, context)
        return await self._remove_entry(cache_key)
    
    async def clear(self) -> int:
        """Clear all cache entries for this workspace."""
        cleared_count = len(self.memory_cache)
        
        # Clear memory cache
        self.memory_cache.clear()
        
        # Clear persistent cache (would need LMDB prefix scan)
        # For now, just reset stats
        self.cache_stats = {'hits': 0, 'misses': 0, 'evictions': 0}
        
        return cleared_count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests) if total_requests > 0 else 0
        
        return {
            'workspace': self.workspace_name,
            'memory_entries': len(self.memory_cache),
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'evictions': self.cache_stats['evictions'],
            'hit_rate': hit_rate,
            'total_requests': total_requests
        }
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries from cache."""
        expired_keys = []
        
        for cache_key, entry in self.memory_cache.items():
            if self._is_expired(entry):
                expired_keys.append(cache_key)
        
        for cache_key in expired_keys:
            await self._remove_entry(cache_key)
        
        return len(expired_keys)
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry has expired."""
        ttl_hours = entry.metadata.get('ttl_hours', self.default_ttl.total_seconds() / 3600)
        ttl = timedelta(hours=ttl_hours)
        return datetime.utcnow() > entry.created_at + ttl
    
    async def _add_to_memory_cache(self, entry: CacheEntry):
        """Add entry to memory cache with LRU eviction."""
        # Check if we need to evict entries
        if len(self.memory_cache) >= self.max_memory_entries:
            await self._evict_lru()
        
        self.memory_cache[entry.cache_key] = entry
    
    async def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.memory_cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self.memory_cache.keys(), 
            key=lambda k: self.memory_cache[k].accessed_at
        )
        
        del self.memory_cache[lru_key]
        self.cache_stats['evictions'] += 1
    
    async def _store_entry(self, entry: CacheEntry):
        """Store entry to persistent storage."""
        try:
            await self.storage.store_json(
                f"llm_cache_{entry.cache_key}",
                entry.to_dict(),
                db_name="llm_cache"
            )
        except Exception as e:
            print(f"Cache storage error: {e}")
    
    async def _remove_entry(self, cache_key: str) -> bool:
        """Remove entry from both memory and persistent storage."""
        removed = False
        
        # Remove from memory cache
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
            removed = True
        
        # Remove from persistent storage
        try:
            # TODO: Implement deletion in StorageManager
            # await self.storage.delete(f"llm_cache_{cache_key}", db_name="llm_cache")
            removed = True
        except Exception as e:
            print(f"Cache deletion error: {e}")
        
        return removed


class CachedLLMClient:
    """LLM client with caching support."""
    
    def __init__(self, cache: LLMCache):
        self.cache = cache
    
    async def prompt(
        self, 
        prompt: str, 
        model_name: str,
        context: Optional[Dict[str, Any]] = None,
        force_refresh: bool = False
    ) -> tuple[str, Dict[str, int]]:
        """Make an LLM request with caching."""
        # Check cache first (unless force refresh)
        if not force_refresh:
            cached = await self.cache.get(prompt, model_name, context)
            if cached:
                return cached.response, cached.tokens_used
        
        # Make actual LLM call
        import llm
        model = llm.get_model(model_name)
        response = model.prompt(prompt)
        response_text = str(response)
        
        # Extract token usage if available
        tokens_used = {}
        if hasattr(response, 'usage'):
            tokens_used = {
                'prompt_tokens': response.usage.get('prompt_tokens', 0),
                'completion_tokens': response.usage.get('completion_tokens', 0),
                'total_tokens': response.usage.get('total_tokens', 0)
            }
        
        # Cache the response
        await self.cache.put(
            prompt, 
            model_name, 
            response_text, 
            tokens_used, 
            context
        )
        
        return response_text, tokens_used
    
    async def prompt_stream(
        self, 
        prompt: str, 
        model_name: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Stream LLM response (bypasses cache for now)."""
        import llm
        model = llm.get_async_model(model_name)
        
        full_response = ""
        async for chunk in model.prompt(prompt, stream=True):
            full_response += chunk
            yield chunk
        
        # Cache the complete response
        tokens_used = {}  # TODO: Extract from streaming response
        await self.cache.put(prompt, model_name, full_response, tokens_used, context)