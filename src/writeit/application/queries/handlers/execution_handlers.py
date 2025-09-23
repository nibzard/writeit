"""Concrete implementations of execution domain query handlers.

This module provides concrete implementations for all execution domain
query handlers, integrating with repositories and domain services.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from ....domains.execution.entities import (
    LLMProvider,
    ExecutionContext,
    TokenUsage
)
from ....domains.execution.repositories import (
    LLMCacheRepository,
    TokenUsageRepository
)
from ....domains.execution.services import (
    LLMOrchestrationService,
    CacheManagementService,
    TokenAnalyticsService
)
from ....domains.execution.value_objects import ExecutionMode
from ..execution_queries import (
    # Query classes
    GetLLMProvidersQuery,
    GetLLMProviderQuery,
    GetLLMProviderHealthQuery,
    SearchLLMProvidersQuery,
    GetTokenUsageQuery,
    ListTokenUsageQuery,
    GetTokenAnalyticsQuery,
    GetTopTokenConsumersQuery,
    GetCacheStatsQuery,
    GetCacheEntryQuery,
    SearchCacheEntriesQuery,
    GetExecutionContextQuery,
    ListExecutionContextsQuery,
    GetActiveExecutionContextsQuery,
    GetLLMRequestHistoryQuery,
    GetLLMRequestPerformanceQuery,
    # Handler interfaces
    GetLLMProvidersQueryHandler,
    GetLLMProviderQueryHandler,
    GetLLMProviderHealthQueryHandler,
    SearchLLMProvidersQueryHandler,
    GetTokenUsageQueryHandler,
    ListTokenUsageQueryHandler,
    GetTokenAnalyticsQueryHandler,
    GetTopTokenConsumersQueryHandler,
    GetCacheStatsQueryHandler,
    GetCacheEntryQueryHandler,
    SearchCacheEntriesQueryHandler,
    GetExecutionContextQueryHandler,
    ListExecutionContextsQueryHandler,
    GetActiveExecutionContextsQueryHandler,
    GetLLMRequestHistoryQueryHandler,
    GetLLMRequestPerformanceQueryHandler,
)

logger = logging.getLogger(__name__)


class ConcreteGetLLMProvidersQueryHandler(GetLLMProvidersQueryHandler):
    """Concrete implementation of GetLLMProvidersQueryHandler."""
    
    def __init__(self, llm_orchestration_service: LLMOrchestrationService):
        self.llm_orchestration_service = llm_orchestration_service
    
    async def handle(self, query: GetLLMProvidersQuery) -> List[LLMProvider]:
        """Get all available LLM providers."""
        logger.info(f"Getting LLM providers, include_disabled={query.include_disabled}")
        
        try:
            providers = await self.llm_orchestration_service.get_available_providers()
            
            if not query.include_disabled:
                providers = [p for p in providers if p.is_enabled]
            
            logger.info(f"Retrieved {len(providers)} LLM providers")
            return providers
            
        except Exception as e:
            logger.error(f"Error getting LLM providers: {e}")
            raise


class ConcreteGetLLMProviderQueryHandler(GetLLMProviderQueryHandler):
    """Concrete implementation of GetLLMProviderQueryHandler."""
    
    def __init__(self, llm_orchestration_service: LLMOrchestrationService):
        self.llm_orchestration_service = llm_orchestration_service
    
    async def handle(self, query: GetLLMProviderQuery) -> Optional[LLMProvider]:
        """Get a specific LLM provider by name."""
        logger.info(f"Getting LLM provider: {query.provider_name}")
        
        try:
            provider = await self.llm_orchestration_service.get_provider_by_name(query.provider_name)
            
            if provider:
                logger.info(f"Found LLM provider: {query.provider_name}")
            else:
                logger.info(f"LLM provider not found: {query.provider_name}")
            
            return provider
            
        except Exception as e:
            logger.error(f"Error getting LLM provider {query.provider_name}: {e}")
            raise


class ConcreteGetLLMProviderHealthQueryHandler(GetLLMProviderHealthQueryHandler):
    """Concrete implementation of GetLLMProviderHealthQueryHandler."""
    
    def __init__(self, llm_orchestration_service: LLMOrchestrationService):
        self.llm_orchestration_service = llm_orchestration_service
    
    async def handle(self, query: GetLLMProviderHealthQuery) -> Dict[str, Any]:
        """Get health status of LLM providers."""
        logger.info(f"Getting LLM provider health for: {query.provider_name or 'all providers'}")
        
        try:
            if query.provider_name:
                health = await self.llm_orchestration_service.check_provider_health(query.provider_name)
                result = {query.provider_name: health}
            else:
                result = await self.llm_orchestration_service.check_all_providers_health()
            
            logger.info(f"Retrieved health status for {len(result)} providers")
            return result
            
        except Exception as e:
            logger.error(f"Error getting LLM provider health: {e}")
            raise


class ConcreteSearchLLMProvidersQueryHandler(SearchLLMProvidersQueryHandler):
    """Concrete implementation of SearchLLMProvidersQueryHandler."""
    
    def __init__(self, llm_orchestration_service: LLMOrchestrationService):
        self.llm_orchestration_service = llm_orchestration_service
    
    async def handle(self, query: SearchLLMProvidersQuery) -> List[LLMProvider]:
        """Search LLM providers by criteria."""
        logger.info(f"Searching LLM providers with criteria: {query}")
        
        try:
            providers = await self.llm_orchestration_service.search_providers(
                search_term=query.search_term,
                model_names=query.model_names,
                capabilities=query.capabilities,
                enabled_only=query.enabled_only
            )
            
            logger.info(f"Found {len(providers)} providers matching criteria")
            return providers
            
        except Exception as e:
            logger.error(f"Error searching LLM providers: {e}")
            raise


class ConcreteGetTokenUsageQueryHandler(GetTokenUsageQueryHandler):
    """Concrete implementation of GetTokenUsageQueryHandler."""
    
    def __init__(self, token_usage_repository: TokenUsageRepository):
        self.token_usage_repository = token_usage_repository
    
    async def handle(self, query: GetTokenUsageQuery) -> Optional[TokenUsage]:
        """Get token usage by execution context."""
        logger.info(f"Getting token usage for context: {query.execution_context_id}")
        
        try:
            token_usage = await self.token_usage_repository.get_by_context_id(query.execution_context_id)
            
            if token_usage:
                logger.info(f"Found token usage for context: {query.execution_context_id}")
            else:
                logger.info(f"No token usage found for context: {query.execution_context_id}")
            
            return token_usage
            
        except Exception as e:
            logger.error(f"Error getting token usage: {e}")
            raise


class ConcreteListTokenUsageQueryHandler(ListTokenUsageQueryHandler):
    """Concrete implementation of ListTokenUsageQueryHandler."""
    
    def __init__(self, token_usage_repository: TokenUsageRepository):
        self.token_usage_repository = token_usage_repository
    
    async def handle(self, query: ListTokenUsageQuery) -> List[TokenUsage]:
        """List token usage records with filtering."""
        logger.info(f"Listing token usage with filters: {query}")
        
        try:
            token_usages = await self.token_usage_repository.list_with_filters(
                workspace_name=query.workspace_name,
                model_name=query.model_name,
                start_date=query.start_date,
                end_date=query.end_date,
                limit=query.limit,
                offset=query.offset
            )
            
            logger.info(f"Retrieved {len(token_usages)} token usage records")
            return token_usages
            
        except Exception as e:
            logger.error(f"Error listing token usage: {e}")
            raise


class ConcreteGetTokenAnalyticsQueryHandler(GetTokenAnalyticsQueryHandler):
    """Concrete implementation of GetTokenAnalyticsQueryHandler."""
    
    def __init__(self, token_analytics_service: TokenAnalyticsService):
        self.token_analytics_service = token_analytics_service
    
    async def handle(self, query: GetTokenAnalyticsQuery) -> Dict[str, Any]:
        """Get token usage analytics and statistics."""
        logger.info(f"Getting token analytics with parameters: {query}")
        
        try:
            analytics = await self.token_analytics_service.get_analytics(
                workspace_name=query.workspace_name,
                model_name=query.model_name,
                period=query.period,
                start_date=query.start_date,
                end_date=query.end_date
            )
            
            logger.info("Retrieved token analytics")
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting token analytics: {e}")
            raise


class ConcreteGetTopTokenConsumersQueryHandler(GetTopTokenConsumersQueryHandler):
    """Concrete implementation of GetTopTokenConsumersQueryHandler."""
    
    def __init__(self, token_analytics_service: TokenAnalyticsService):
        self.token_analytics_service = token_analytics_service
    
    async def handle(self, query: GetTopTokenConsumersQuery) -> List[Dict[str, Any]]:
        """Get top token consumers."""
        logger.info(f"Getting top token consumers by {query.dimension}")
        
        try:
            consumers = await self.token_analytics_service.get_top_consumers(
                dimension=query.dimension,
                limit=query.limit,
                period=query.period,
                start_date=query.start_date,
                end_date=query.end_date
            )
            
            logger.info(f"Retrieved {len(consumers)} top token consumers")
            return consumers
            
        except Exception as e:
            logger.error(f"Error getting top token consumers: {e}")
            raise


class ConcreteGetCacheStatsQueryHandler(GetCacheStatsQueryHandler):
    """Concrete implementation of GetCacheStatsQueryHandler."""
    
    def __init__(self, cache_management_service: CacheManagementService):
        self.cache_management_service = cache_management_service
    
    async def handle(self, query: GetCacheStatsQuery) -> Dict[str, Any]:
        """Get cache statistics and performance metrics."""
        logger.info(f"Getting cache stats for workspace: {query.workspace_name}")
        
        try:
            stats = await self.cache_management_service.get_cache_stats(
                workspace_name=query.workspace_name,
                model_name=query.model_name
            )
            
            logger.info("Retrieved cache statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            raise


class ConcreteGetCacheEntryQueryHandler(GetCacheEntryQueryHandler):
    """Concrete implementation of GetCacheEntryQueryHandler."""
    
    def __init__(self, llm_cache_repository: LLMCacheRepository):
        self.llm_cache_repository = llm_cache_repository
    
    async def handle(self, query: GetCacheEntryQuery) -> Optional[Dict[str, Any]]:
        """Get a specific cache entry."""
        logger.info(f"Getting cache entry: {query.cache_key}")
        
        try:
            cache_entry = await self.llm_cache_repository.get(query.cache_key)
            
            if cache_entry:
                logger.info(f"Found cache entry: {query.cache_key}")
                return {
                    "key": cache_entry.cache_key,
                    "response": cache_entry.response_data,
                    "created_at": cache_entry.created_at,
                    "expires_at": cache_entry.expires_at,
                    "hit_count": cache_entry.hit_count,
                    "last_accessed": cache_entry.last_accessed
                }
            else:
                logger.info(f"Cache entry not found: {query.cache_key}")
                return None
            
        except Exception as e:
            logger.error(f"Error getting cache entry: {e}")
            raise


class ConcreteSearchCacheEntriesQueryHandler(SearchCacheEntriesQueryHandler):
    """Concrete implementation of SearchCacheEntriesQueryHandler."""
    
    def __init__(self, llm_cache_repository: LLMCacheRepository):
        self.llm_cache_repository = llm_cache_repository
    
    async def handle(self, query: SearchCacheEntriesQuery) -> List[Dict[str, Any]]:
        """Search cache entries by criteria."""
        logger.info(f"Searching cache entries with criteria: {query}")
        
        try:
            cache_entries = await self.llm_cache_repository.search(
                workspace_name=query.workspace_name,
                model_name=query.model_name,
                search_term=query.search_term,
                include_expired=query.include_expired,
                limit=query.limit,
                offset=query.offset
            )
            
            result = []
            for entry in cache_entries:
                result.append({
                    "key": entry.cache_key,
                    "model_name": entry.model_name,
                    "workspace_name": entry.workspace_name,
                    "created_at": entry.created_at,
                    "expires_at": entry.expires_at,
                    "hit_count": entry.hit_count,
                    "last_accessed": entry.last_accessed,
                    "response_preview": str(entry.response_data)[:100] + "..." if len(str(entry.response_data)) > 100 else str(entry.response_data)
                })
            
            logger.info(f"Found {len(result)} cache entries matching criteria")
            return result
            
        except Exception as e:
            logger.error(f"Error searching cache entries: {e}")
            raise


class ConcreteGetExecutionContextQueryHandler(GetExecutionContextQueryHandler):
    """Concrete implementation of GetExecutionContextQueryHandler."""
    
    def __init__(self, llm_orchestration_service: LLMOrchestrationService):
        self.llm_orchestration_service = llm_orchestration_service
    
    async def handle(self, query: GetExecutionContextQuery) -> Optional[ExecutionContext]:
        """Get an execution context by ID."""
        logger.info(f"Getting execution context: {query.context_id}")
        
        try:
            context = await self.llm_orchestration_service.get_execution_context(query.context_id)
            
            if context:
                logger.info(f"Found execution context: {query.context_id}")
            else:
                logger.info(f"Execution context not found: {query.context_id}")
            
            return context
            
        except Exception as e:
            logger.error(f"Error getting execution context: {e}")
            raise


class ConcreteListExecutionContextsQueryHandler(ListExecutionContextsQueryHandler):
    """Concrete implementation of ListExecutionContextsQueryHandler."""
    
    def __init__(self, llm_orchestration_service: LLMOrchestrationService):
        self.llm_orchestration_service = llm_orchestration_service
    
    async def handle(self, query: ListExecutionContextsQuery) -> List[ExecutionContext]:
        """List execution contexts with filtering."""
        logger.info(f"Listing execution contexts with filters: {query}")
        
        try:
            contexts = await self.llm_orchestration_service.list_execution_contexts(
                workspace_name=query.workspace_name,
                execution_mode=query.execution_mode,
                active_only=query.active_only,
                limit=query.limit,
                offset=query.offset
            )
            
            logger.info(f"Retrieved {len(contexts)} execution contexts")
            return contexts
            
        except Exception as e:
            logger.error(f"Error listing execution contexts: {e}")
            raise


class ConcreteGetActiveExecutionContextsQueryHandler(GetActiveExecutionContextsQueryHandler):
    """Concrete implementation of GetActiveExecutionContextsQueryHandler."""
    
    def __init__(self, llm_orchestration_service: LLMOrchestrationService):
        self.llm_orchestration_service = llm_orchestration_service
    
    async def handle(self, query: GetActiveExecutionContextsQuery) -> List[ExecutionContext]:
        """Get currently active execution contexts."""
        logger.info(f"Getting active execution contexts for workspace: {query.workspace_name}")
        
        try:
            contexts = await self.llm_orchestration_service.get_active_contexts(
                workspace_name=query.workspace_name
            )
            
            logger.info(f"Found {len(contexts)} active execution contexts")
            return contexts
            
        except Exception as e:
            logger.error(f"Error getting active execution contexts: {e}")
            raise


class ConcreteGetLLMRequestHistoryQueryHandler(GetLLMRequestHistoryQueryHandler):
    """Concrete implementation of GetLLMRequestHistoryQueryHandler."""
    
    def __init__(self, token_usage_repository: TokenUsageRepository):
        self.token_usage_repository = token_usage_repository
    
    async def handle(self, query: GetLLMRequestHistoryQuery) -> List[Dict[str, Any]]:
        """Get LLM request history."""
        logger.info(f"Getting LLM request history with filters: {query}")
        
        try:
            history = await self.token_usage_repository.get_request_history(
                execution_context_id=query.execution_context_id,
                workspace_name=query.workspace_name,
                model_name=query.model_name,
                start_date=query.start_date,
                end_date=query.end_date,
                limit=query.limit,
                offset=query.offset
            )
            
            logger.info(f"Retrieved {len(history)} request history records")
            return history
            
        except Exception as e:
            logger.error(f"Error getting LLM request history: {e}")
            raise


class ConcreteGetLLMRequestPerformanceQueryHandler(GetLLMRequestPerformanceQueryHandler):
    """Concrete implementation of GetLLMRequestPerformanceQueryHandler."""
    
    def __init__(self, token_analytics_service: TokenAnalyticsService):
        self.token_analytics_service = token_analytics_service
    
    async def handle(self, query: GetLLMRequestPerformanceQuery) -> Dict[str, Any]:
        """Get LLM request performance metrics."""
        logger.info(f"Getting LLM request performance for model: {query.model_name}")
        
        try:
            performance = await self.token_analytics_service.get_request_performance(
                model_name=query.model_name,
                workspace_name=query.workspace_name,
                period=query.period
            )
            
            logger.info("Retrieved LLM request performance metrics")
            return performance
            
        except Exception as e:
            logger.error(f"Error getting LLM request performance: {e}")
            raise
