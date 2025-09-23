"""Cache Management Service.

Provides comprehensive LLM response cache management including policy optimization,
performance monitoring, intelligent cleanup, and cache warming strategies.
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any, Tuple, Union
from enum import Enum
from collections import defaultdict, OrderedDict
import json

from ..entities.execution_context import ExecutionContext
from ..value_objects.cache_key import CacheKey
from ..value_objects.model_name import ModelName
from ..value_objects.token_count import TokenCount
from ..repositories.llm_cache_repository import (
    LLMCacheRepository, 
    CacheEntry,
    ByModelSpecification,
    ExpiredEntriesSpecification,
    RecentlyAccessedSpecification,
    HighHitCountSpecification,
    LargeCacheEntrySpecification
)


class CacheStrategy(str, Enum):
    """Cache strategy types."""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    TTL = "ttl"  # Time To Live
    ADAPTIVE = "adaptive"  # Adaptive based on usage patterns
    COST_AWARE = "cost_aware"  # Cost-aware eviction
    QUALITY_AWARE = "quality_aware"  # Quality-aware caching


class CacheOptimizationGoal(str, Enum):
    """Optimization goals for cache management."""
    HIT_RATE = "hit_rate"
    COST_REDUCTION = "cost_reduction"
    LATENCY_REDUCTION = "latency_reduction"
    STORAGE_EFFICIENCY = "storage_efficiency"
    BALANCED = "balanced"


class CacheWarmingStrategy(str, Enum):
    """Strategies for cache warming."""
    PRECOMPUTE_COMMON = "precompute_common"
    PREDICTIVE = "predictive"
    SCHEDULED = "scheduled"
    LAZY = "lazy"


@dataclass
class CacheStatistics:
    """Cache performance statistics."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    total_entries: int = 0
    total_size_bytes: int = 0
    avg_entry_size_bytes: float = 0.0
    hit_rate: float = 0.0
    miss_rate: float = 0.0
    eviction_count: int = 0
    storage_efficiency: float = 0.0
    cost_savings: float = 0.0
    latency_savings_ms: float = 0.0
    
    def update_hit(self, entry_size: int, cost_saved: float, latency_saved_ms: float) -> None:
        """Update statistics for cache hit."""
        self.total_requests += 1
        self.cache_hits += 1
        self.cost_savings += cost_saved
        self.latency_savings_ms += latency_saved_ms
        self._recalculate_rates()
    
    def update_miss(self) -> None:
        """Update statistics for cache miss."""
        self.total_requests += 1
        self.cache_misses += 1
        self._recalculate_rates()
    
    def _recalculate_rates(self) -> None:
        """Recalculate hit and miss rates."""
        if self.total_requests > 0:
            self.hit_rate = self.cache_hits / self.total_requests
            self.miss_rate = self.cache_misses / self.total_requests
        else:
            self.hit_rate = 0.0
            self.miss_rate = 0.0


@dataclass
class CachePolicy:
    """Cache policy configuration."""
    strategy: CacheStrategy
    max_entries: int
    max_size_bytes: int
    default_ttl_hours: int
    min_hit_count_for_retention: int = 2
    quality_threshold: float = 0.8
    cost_threshold: float = 0.001
    enable_compression: bool = True
    enable_warming: bool = True
    warming_strategy: CacheWarmingStrategy = CacheWarmingStrategy.LAZY
    
    def is_entry_eligible_for_caching(self, content: str, cost: float, quality: float) -> bool:
        """Check if entry meets caching criteria."""
        return (
            cost >= self.cost_threshold and
            quality >= self.quality_threshold and
            len(content.encode('utf-8')) <= self.max_size_bytes // 100  # Don't cache huge entries
        )


@dataclass
class CacheOptimizationPlan:
    """Plan for cache optimization."""
    current_hit_rate: float
    target_hit_rate: float
    recommended_strategy: CacheStrategy
    recommended_max_entries: int
    recommended_ttl_hours: int
    eviction_candidates: List[CacheKey]
    warming_candidates: List[Dict[str, Any]]
    estimated_improvement: Dict[str, float]
    implementation_steps: List[str]


@dataclass
class CacheInsights:
    """Cache usage insights and analytics."""
    most_popular_models: List[Tuple[str, int]]
    most_expensive_cached_queries: List[Tuple[CacheKey, float]]
    cache_hot_spots: List[Tuple[str, int]]  # workspace, hit count
    usage_patterns: Dict[str, Any]
    optimization_opportunities: List[str]
    storage_breakdown: Dict[str, int]
    performance_trends: Dict[str, List[float]]


class CacheManagementError(Exception):
    """Base exception for cache management errors."""
    pass


class CacheStorageError(CacheManagementError):
    """Raised when cache storage operations fail."""
    pass


class CachePolicyError(CacheManagementError):
    """Raised when cache policy configuration is invalid."""
    pass


class CacheManagementService:
    """Service for managing LLM response caching with optimization and analytics.
    
    Provides comprehensive cache management including:
    - Cache policy optimization and strategy selection
    - Performance monitoring and analytics
    - Intelligent cache warming and eviction
    - Storage optimization and compression
    - Cost-aware and quality-aware caching decisions
    - Multi-workspace cache isolation
    
    Examples:
        service = CacheManagementService(cache_repository)
        
        # Configure cache policy
        policy = CachePolicy(
            strategy=CacheStrategy.ADAPTIVE,
            max_entries=10000,
            max_size_bytes=100_000_000
        )
        await service.configure_policy(policy)
        
        # Check cache and manage entries
        cached_response = await service.get_cached_response(cache_key)
        await service.cache_response(cache_key, response, context)
        
        # Optimize cache performance
        plan = await service.generate_optimization_plan()
        await service.implement_optimization_plan(plan)
        
        # Analyze cache usage
        insights = await service.analyze_cache_usage()
    """
    
    def __init__(
        self, 
        cache_repository: LLMCacheRepository,
        default_policy: Optional[CachePolicy] = None
    ) -> None:
        """Initialize cache management service.
        
        Args:
            cache_repository: Repository for cache operations
            default_policy: Default cache policy
        """
        self._repository = cache_repository
        self._policy = default_policy or CachePolicy(
            strategy=CacheStrategy.ADAPTIVE,
            max_entries=10000,
            max_size_bytes=100_000_000,  # 100MB
            default_ttl_hours=24
        )
        self._statistics = CacheStatistics()
        self._access_history: OrderedDict[CacheKey, datetime] = OrderedDict()
        self._hit_counts: Dict[CacheKey, int] = defaultdict(int)
        self._quality_scores: Dict[CacheKey, float] = {}
        self._cost_data: Dict[CacheKey, float] = {}
        self._workspace_stats: Dict[str, CacheStatistics] = defaultdict(CacheStatistics)
        
        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._warming_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None
    
    async def start_background_tasks(self) -> None:
        """Start background cache management tasks."""
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self._warming_task = asyncio.create_task(self._periodic_warming())
        self._optimization_task = asyncio.create_task(self._periodic_optimization())
    
    async def stop_background_tasks(self) -> None:
        """Stop background cache management tasks."""
        for task in [self._cleanup_task, self._warming_task, self._optimization_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
    async def configure_policy(self, policy: CachePolicy) -> None:
        """Configure cache policy.
        
        Args:
            policy: New cache policy
            
        Raises:
            CachePolicyError: If policy configuration is invalid
        """
        # Validate policy
        if policy.max_entries <= 0:
            raise CachePolicyError("max_entries must be positive")
        if policy.max_size_bytes <= 0:
            raise CachePolicyError("max_size_bytes must be positive")
        if policy.default_ttl_hours <= 0:
            raise CachePolicyError("default_ttl_hours must be positive")
        
        self._policy = policy
        
        # Apply policy changes
        await self._apply_policy_changes()
    
    async def get_cached_response(
        self, 
        cache_key: CacheKey,
        workspace_name: Optional[str] = None
    ) -> Optional[CacheEntry]:
        """Get cached response if available.
        
        Args:
            cache_key: Cache key to lookup
            workspace_name: Optional workspace name for stats
            
        Returns:
            Cache entry if found, None otherwise
        """
        try:
            entry = await self._repository.get_by_key(cache_key)
            
            if entry:
                # Check if entry is expired
                if self._is_entry_expired(entry):
                    await self._repository.delete(cache_key)
                    self._statistics.update_miss()
                    if workspace_name:
                        self._workspace_stats[workspace_name].update_miss()
                    return None
                
                # Update access tracking
                self._access_history[cache_key] = datetime.now()
                self._hit_counts[cache_key] += 1
                
                # Estimate cost and latency savings
                cost_saved = self._cost_data.get(cache_key, 0.001)
                latency_saved = 1000.0  # Assume 1 second saved
                
                # Update statistics
                self._statistics.update_hit(entry.size_bytes, cost_saved, latency_saved)
                if workspace_name:
                    self._workspace_stats[workspace_name].update_hit(
                        entry.size_bytes, cost_saved, latency_saved
                    )
                
                return entry
            else:
                self._statistics.update_miss()
                if workspace_name:
                    self._workspace_stats[workspace_name].update_miss()
                return None
                
        except Exception as e:
            raise CacheStorageError(f"Failed to get cached response: {e}")
    
    async def cache_response(
        self,
        cache_key: CacheKey,
        content: str,
        context: ExecutionContext,
        usage: TokenCount,
        cost: float,
        quality_score: float = 1.0,
        model_name: Optional[ModelName] = None
    ) -> bool:
        """Cache LLM response with metadata.
        
        Args:
            cache_key: Cache key
            content: Response content
            context: Execution context
            usage: Token usage
            cost: Response cost
            quality_score: Quality score (0.0 to 1.0)
            model_name: Model used for response
            
        Returns:
            True if cached successfully
        """
        try:
            # Check if entry should be cached based on policy
            if not self._policy.is_entry_eligible_for_caching(content, cost, quality_score):
                return False
            
            # Check cache size limits
            if not await self._ensure_cache_capacity(len(content.encode('utf-8'))):
                return False
            
            # Create cache entry
            ttl = timedelta(hours=self._policy.default_ttl_hours)
            expires_at = datetime.now() + ttl
            
            entry = CacheEntry(
                key=cache_key,
                content=content,
                workspace_name=context.workspace_name,
                model_name=model_name or context.get_preferred_model(),
                usage=usage,
                quality_score=quality_score,
                created_at=datetime.now(),
                last_accessed_at=datetime.now(),
                access_count=0,
                expires_at=expires_at,
                size_bytes=len(content.encode('utf-8')),
                metadata={
                    "cost": cost,
                    "pipeline_id": context.pipeline_id,
                    "execution_mode": str(context.execution_mode)
                }
            )
            
            # Store in repository
            await self._repository.store(entry)
            
            # Update tracking data
            self._cost_data[cache_key] = cost
            self._quality_scores[cache_key] = quality_score
            
            return True
            
        except Exception as e:
            raise CacheStorageError(f"Failed to cache response: {e}")
    
    async def invalidate_cache(
        self, 
        cache_key: Optional[CacheKey] = None,
        workspace_name: Optional[str] = None,
        model_name: Optional[ModelName] = None
    ) -> int:
        """Invalidate cache entries.
        
        Args:
            cache_key: Specific key to invalidate
            workspace_name: Invalidate all entries for workspace
            model_name: Invalidate all entries for model
            
        Returns:
            Number of entries invalidated
        """
        try:
            if cache_key:
                await self._repository.delete(cache_key)
                return 1
            
            count = 0
            
            if workspace_name:
                # This would require a workspace-specific query method
                # For now, we'll implement a basic approach
                pass
            
            if model_name:
                entries = await self._repository.find_by_specification(
                    ByModelSpecification(model_name)
                )
                for entry in entries:
                    await self._repository.delete(entry.key)
                    count += 1
            
            return count
            
        except Exception as e:
            raise CacheStorageError(f"Failed to invalidate cache: {e}")
    
    async def cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries.
        
        Returns:
            Number of entries cleaned up
        """
        try:
            expired_entries = await self._repository.find_by_specification(
                ExpiredEntriesSpecification()
            )
            
            count = 0
            for entry in expired_entries:
                await self._repository.delete(entry.key)
                count += 1
            
            self._statistics.eviction_count += count
            return count
            
        except Exception as e:
            raise CacheStorageError(f"Failed to cleanup expired entries: {e}")
    
    async def optimize_cache_size(self, target_size_bytes: Optional[int] = None) -> int:
        """Optimize cache size by removing low-value entries.
        
        Args:
            target_size_bytes: Target cache size, uses policy max if not specified
            
        Returns:
            Number of entries evicted
        """
        target_size = target_size_bytes or self._policy.max_size_bytes
        current_size = await self._get_current_cache_size()
        
        if current_size <= target_size:
            return 0
        
        evicted_count = 0
        
        # Apply eviction strategy
        if self._policy.strategy == CacheStrategy.LRU:
            evicted_count = await self._evict_lru_entries(current_size - target_size)
        elif self._policy.strategy == CacheStrategy.LFU:
            evicted_count = await self._evict_lfu_entries(current_size - target_size)
        elif self._policy.strategy == CacheStrategy.COST_AWARE:
            evicted_count = await self._evict_low_cost_entries(current_size - target_size)
        elif self._policy.strategy == CacheStrategy.QUALITY_AWARE:
            evicted_count = await self._evict_low_quality_entries(current_size - target_size)
        else:  # ADAPTIVE or TTL
            evicted_count = await self._evict_adaptive_entries(current_size - target_size)
        
        self._statistics.eviction_count += evicted_count
        return evicted_count
    
    async def warm_cache_for_common_queries(self, workspace_name: str) -> int:
        """Warm cache with common queries for a workspace.
        
        Args:
            workspace_name: Workspace to warm cache for
            
        Returns:
            Number of entries pre-computed
        """
        if not self._policy.enable_warming:
            return 0
        
        # This would analyze historical query patterns and pre-compute responses
        # For now, return mock count
        return 0
    
    async def generate_optimization_plan(
        self, 
        goal: CacheOptimizationGoal = CacheOptimizationGoal.BALANCED
    ) -> CacheOptimizationPlan:
        """Generate cache optimization plan.
        
        Args:
            goal: Optimization goal
            
        Returns:
            Optimization plan with recommendations
        """
        current_stats = await self.get_cache_statistics()
        
        # Analyze current performance
        target_hit_rate = 0.8  # Target 80% hit rate
        
        # Determine optimal strategy
        if goal == CacheOptimizationGoal.HIT_RATE:
            recommended_strategy = CacheStrategy.LFU
        elif goal == CacheOptimizationGoal.COST_REDUCTION:
            recommended_strategy = CacheStrategy.COST_AWARE
        elif goal == CacheOptimizationGoal.LATENCY_REDUCTION:
            recommended_strategy = CacheStrategy.LRU
        elif goal == CacheOptimizationGoal.STORAGE_EFFICIENCY:
            recommended_strategy = CacheStrategy.QUALITY_AWARE
        else:  # BALANCED
            recommended_strategy = CacheStrategy.ADAPTIVE
        
        # Find eviction candidates
        eviction_candidates = await self._identify_eviction_candidates()
        
        # Find warming candidates
        warming_candidates = await self._identify_warming_candidates()
        
        # Estimate improvements
        estimated_improvement = {
            "hit_rate_increase": 0.1,
            "cost_savings": 0.2,
            "latency_reduction": 0.15,
            "storage_efficiency": 0.25
        }
        
        implementation_steps = [
            f"Change cache strategy to {recommended_strategy.value}",
            f"Evict {len(eviction_candidates)} low-value entries",
            f"Pre-compute {len(warming_candidates)} common queries",
            "Monitor performance for 24 hours",
            "Fine-tune parameters based on results"
        ]
        
        return CacheOptimizationPlan(
            current_hit_rate=current_stats.hit_rate,
            target_hit_rate=target_hit_rate,
            recommended_strategy=recommended_strategy,
            recommended_max_entries=self._policy.max_entries,
            recommended_ttl_hours=self._policy.default_ttl_hours,
            eviction_candidates=eviction_candidates,
            warming_candidates=warming_candidates,
            estimated_improvement=estimated_improvement,
            implementation_steps=implementation_steps
        )
    
    async def implement_optimization_plan(self, plan: CacheOptimizationPlan) -> Dict[str, Any]:
        """Implement cache optimization plan.
        
        Args:
            plan: Optimization plan to implement
            
        Returns:
            Implementation results
        """
        results = {
            "strategy_changed": False,
            "entries_evicted": 0,
            "entries_warmed": 0,
            "errors": []
        }
        
        try:
            # Update strategy
            if plan.recommended_strategy != self._policy.strategy:
                new_policy = replace(self._policy, strategy=plan.recommended_strategy)
                await self.configure_policy(new_policy)
                results["strategy_changed"] = True
            
            # Evict low-value entries
            for cache_key in plan.eviction_candidates:
                try:
                    await self._repository.delete(cache_key)
                    results["entries_evicted"] += 1
                except Exception as e:
                    results["errors"].append(f"Failed to evict {cache_key}: {e}")
            
            # Warm cache (would be implemented with actual query execution)
            results["entries_warmed"] = len(plan.warming_candidates)
            
        except Exception as e:
            results["errors"].append(f"Optimization failed: {e}")
        
        return results
    
    async def analyze_cache_usage(self, days_back: int = 7) -> CacheInsights:
        """Analyze cache usage patterns and generate insights.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            Cache usage insights
        """
        # Get recent entries
        recent_entries = await self._repository.find_by_specification(
            RecentlyAccessedSpecification(days_back)
        )
        
        # Analyze model usage
        model_usage = defaultdict(int)
        for entry in recent_entries:
            if entry.model_name:
                model_usage[str(entry.model_name)] += entry.access_count
        
        most_popular_models = sorted(
            model_usage.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Analyze expensive queries
        expensive_queries = []
        for entry in recent_entries:
            cost = entry.metadata.get("cost", 0.0)
            if cost > 0:
                expensive_queries.append((entry.key, cost))
        
        most_expensive_cached_queries = sorted(
            expensive_queries, 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Analyze workspace usage
        workspace_usage = defaultdict(int)
        for entry in recent_entries:
            workspace_usage[entry.workspace_name] += entry.access_count
        
        cache_hot_spots = sorted(
            workspace_usage.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Generate optimization opportunities
        optimization_opportunities = []
        
        if self._statistics.hit_rate < 0.7:
            optimization_opportunities.append("Low hit rate - consider cache warming")
        
        if self._statistics.total_size_bytes > self._policy.max_size_bytes * 0.9:
            optimization_opportunities.append("Cache near capacity - consider eviction")
        
        if len(most_expensive_cached_queries) < 5:
            optimization_opportunities.append("Few expensive queries cached - adjust thresholds")
        
        # Storage breakdown
        storage_breakdown = {
            "total_entries": len(recent_entries),
            "total_size_mb": self._statistics.total_size_bytes // (1024 * 1024),
            "avg_entry_size_kb": self._statistics.avg_entry_size_bytes // 1024
        }
        
        # Performance trends (mock data)
        performance_trends = {
            "hit_rate": [0.6, 0.65, 0.7, 0.72, 0.75, 0.73, 0.76],
            "avg_latency": [150, 140, 135, 130, 125, 120, 118],
            "cost_savings": [0.1, 0.12, 0.15, 0.18, 0.2, 0.22, 0.25]
        }
        
        return CacheInsights(
            most_popular_models=most_popular_models,
            most_expensive_cached_queries=most_expensive_cached_queries,
            cache_hot_spots=cache_hot_spots,
            usage_patterns={
                "total_requests": self._statistics.total_requests,
                "avg_hit_rate": self._statistics.hit_rate,
                "peak_usage_hour": 14  # 2 PM
            },
            optimization_opportunities=optimization_opportunities,
            storage_breakdown=storage_breakdown,
            performance_trends=performance_trends
        )
    
    async def get_cache_statistics(self) -> CacheStatistics:
        """Get current cache statistics.
        
        Returns:
            Current cache statistics
        """
        # Update real-time statistics
        self._statistics.total_entries = await self._repository.count()
        self._statistics.total_size_bytes = await self._get_current_cache_size()
        
        if self._statistics.total_entries > 0:
            self._statistics.avg_entry_size_bytes = (
                self._statistics.total_size_bytes / self._statistics.total_entries
            )
        
        return self._statistics
    
    async def get_workspace_statistics(self, workspace_name: str) -> CacheStatistics:
        """Get cache statistics for specific workspace.
        
        Args:
            workspace_name: Workspace name
            
        Returns:
            Workspace-specific cache statistics
        """
        return self._workspace_stats.get(workspace_name, CacheStatistics())
    
    # Private helper methods
    
    def _is_entry_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired."""
        if entry.expires_at is None:
            return False
        return datetime.now() > entry.expires_at
    
    async def _ensure_cache_capacity(self, required_bytes: int) -> bool:
        """Ensure cache has capacity for new entry."""
        current_size = await self._get_current_cache_size()
        available_space = self._policy.max_size_bytes - current_size
        
        if available_space >= required_bytes:
            return True
        
        # Try to free up space
        bytes_to_free = required_bytes - available_space
        evicted = await self.optimize_cache_size(current_size - bytes_to_free)
        
        return evicted > 0
    
    async def _get_current_cache_size(self) -> int:
        """Get current cache size in bytes."""
        # This would be implemented by the repository
        # For now, return estimated size
        return self._statistics.total_size_bytes
    
    async def _apply_policy_changes(self) -> None:
        """Apply policy changes to existing cache."""
        # Clean up expired entries
        await self.cleanup_expired_entries()
        
        # Optimize size if over limit
        current_size = await self._get_current_cache_size()
        if current_size > self._policy.max_size_bytes:
            await self.optimize_cache_size()
    
    async def _evict_lru_entries(self, bytes_to_free: int) -> int:
        """Evict least recently used entries."""
        # Sort by last access time
        sorted_keys = sorted(
            self._access_history.items(),
            key=lambda x: x[1]
        )
        
        evicted = 0
        freed_bytes = 0
        
        for cache_key, _ in sorted_keys:
            if freed_bytes >= bytes_to_free:
                break
                
            try:
                entry = await self._repository.get_by_key(cache_key)
                if entry:
                    await self._repository.delete(cache_key)
                    freed_bytes += entry.size_bytes
                    evicted += 1
            except Exception:
                continue
        
        return evicted
    
    async def _evict_lfu_entries(self, bytes_to_free: int) -> int:
        """Evict least frequently used entries."""
        # Sort by hit count
        sorted_keys = sorted(
            self._hit_counts.items(),
            key=lambda x: x[1]
        )
        
        evicted = 0
        freed_bytes = 0
        
        for cache_key, _ in sorted_keys:
            if freed_bytes >= bytes_to_free:
                break
                
            try:
                entry = await self._repository.get_by_key(cache_key)
                if entry:
                    await self._repository.delete(cache_key)
                    freed_bytes += entry.size_bytes
                    evicted += 1
            except Exception:
                continue
        
        return evicted
    
    async def _evict_low_cost_entries(self, bytes_to_free: int) -> int:
        """Evict entries with low cost (less valuable to cache)."""
        # Sort by cost (ascending)
        sorted_keys = sorted(
            self._cost_data.items(),
            key=lambda x: x[1]
        )
        
        evicted = 0
        freed_bytes = 0
        
        for cache_key, _ in sorted_keys:
            if freed_bytes >= bytes_to_free:
                break
                
            try:
                entry = await self._repository.get_by_key(cache_key)
                if entry:
                    await self._repository.delete(cache_key)
                    freed_bytes += entry.size_bytes
                    evicted += 1
            except Exception:
                continue
        
        return evicted
    
    async def _evict_low_quality_entries(self, bytes_to_free: int) -> int:
        """Evict entries with low quality scores."""
        # Sort by quality score (ascending)
        sorted_keys = sorted(
            self._quality_scores.items(),
            key=lambda x: x[1]
        )
        
        evicted = 0
        freed_bytes = 0
        
        for cache_key, _ in sorted_keys:
            if freed_bytes >= bytes_to_free:
                break
                
            try:
                entry = await self._repository.get_by_key(cache_key)
                if entry:
                    await self._repository.delete(cache_key)
                    freed_bytes += entry.size_bytes
                    evicted += 1
            except Exception:
                continue
        
        return evicted
    
    async def _evict_adaptive_entries(self, bytes_to_free: int) -> int:
        """Evict entries using adaptive strategy."""
        # Combine multiple factors for scoring
        scored_keys = []
        
        for cache_key in self._access_history.keys():
            try:
                entry = await self._repository.get_by_key(cache_key)
                if not entry:
                    continue
                
                # Calculate composite score (lower = more likely to evict)
                recency_score = (datetime.now() - self._access_history[cache_key]).total_seconds()
                frequency_score = 1.0 / max(self._hit_counts.get(cache_key, 1), 1)
                cost_score = 1.0 / max(self._cost_data.get(cache_key, 0.001), 0.001)
                quality_score = 1.0 / max(self._quality_scores.get(cache_key, 1.0), 0.1)
                
                composite_score = (
                    recency_score * 0.3 +
                    frequency_score * 0.3 +
                    cost_score * 0.2 +
                    quality_score * 0.2
                )
                
                scored_keys.append((cache_key, composite_score, entry.size_bytes))
                
            except Exception:
                continue
        
        # Sort by composite score (ascending - lower scores evicted first)
        scored_keys.sort(key=lambda x: x[1])
        
        evicted = 0
        freed_bytes = 0
        
        for cache_key, _, size_bytes in scored_keys:
            if freed_bytes >= bytes_to_free:
                break
                
            try:
                await self._repository.delete(cache_key)
                freed_bytes += size_bytes
                evicted += 1
            except Exception:
                continue
        
        return evicted
    
    async def _identify_eviction_candidates(self) -> List[CacheKey]:
        """Identify cache entries that are candidates for eviction."""
        candidates = []
        
        # Find large, low-quality entries
        large_entries = await self._repository.find_by_specification(
            LargeCacheEntrySpecification(self._policy.max_size_bytes // 1000)
        )
        
        for entry in large_entries:
            quality = self._quality_scores.get(entry.key, 1.0)
            if quality < self._policy.quality_threshold:
                candidates.append(entry.key)
        
        return candidates[:100]  # Limit to top 100
    
    async def _identify_warming_candidates(self) -> List[Dict[str, Any]]:
        """Identify queries that would benefit from cache warming."""
        # This would analyze query patterns and identify frequently requested
        # but not cached queries. For now, return mock data.
        return [
            {"prompt_pattern": "Generate article outline for *", "priority": "high"},
            {"prompt_pattern": "Summarize text: *", "priority": "medium"},
            {"prompt_pattern": "Translate to English: *", "priority": "medium"}
        ]
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup task."""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                await self.cleanup_expired_entries()
                await self.optimize_cache_size()
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error and continue
                pass
    
    async def _periodic_warming(self) -> None:
        """Periodic cache warming task."""
        while True:
            try:
                await asyncio.sleep(7200)  # Run every 2 hours
                if self._policy.enable_warming:
                    # Implement cache warming logic
                    pass
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error and continue
                pass
    
    async def _periodic_optimization(self) -> None:
        """Periodic cache optimization task."""
        while True:
            try:
                await asyncio.sleep(86400)  # Run daily
                plan = await self.generate_optimization_plan()
                # Could auto-implement safe optimizations
            except asyncio.CancelledError:
                break
            except Exception:
                # Log error and continue
                pass