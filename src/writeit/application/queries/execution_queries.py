"""Execution domain query definitions for CQRS implementation.

This module defines queries and query handlers for the execution domain,
covering LLM requests, caching, token usage, and provider management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from ...domains.execution.value_objects import (
    ModelName,
    TokenCount,
    CacheKey,
    ExecutionMode
)
from ...domains.execution.entities import (
    LLMProvider,
    ExecutionContext,
    TokenUsage
)
from ...shared.events.domain_event import Query, QueryHandler


# LLM Provider Queries
@dataclass(frozen=True)
class GetLLMProvidersQuery(Query):
    """Query to get all available LLM providers."""
    include_disabled: bool = False
    

@dataclass(frozen=True)
class GetLLMProviderQuery(Query):
    """Query to get a specific LLM provider by name."""
    provider_name: str
    

@dataclass(frozen=True)
class GetLLMProviderHealthQuery(Query):
    """Query to get health status of LLM providers."""
    provider_name: Optional[str] = None  # If None, get health for all providers
    

@dataclass(frozen=True)
class SearchLLMProvidersQuery(Query):
    """Query to search LLM providers by criteria."""
    search_term: Optional[str] = None
    model_names: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    enabled_only: bool = True
    

# Token Usage Queries
@dataclass(frozen=True)
class GetTokenUsageQuery(Query):
    """Query to get token usage by execution context."""
    execution_context_id: UUID
    

@dataclass(frozen=True)
class ListTokenUsageQuery(Query):
    """Query to list token usage records with filtering."""
    workspace_name: Optional[str] = None
    model_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
    

@dataclass(frozen=True)
class GetTokenAnalyticsQuery(Query):
    """Query to get token usage analytics and statistics."""
    workspace_name: Optional[str] = None
    model_name: Optional[str] = None
    period: str = "day"  # "hour", "day", "week", "month"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    

@dataclass(frozen=True)
class GetTopTokenConsumersQuery(Query):
    """Query to get top token consumers (models, workspaces, etc.)."""
    dimension: str = "model"  # "model", "workspace", "user"
    limit: int = 10
    period: str = "day"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    

# Cache Queries
@dataclass(frozen=True)
class GetCacheStatsQuery(Query):
    """Query to get cache statistics and performance metrics."""
    workspace_name: Optional[str] = None
    model_name: Optional[str] = None
    

@dataclass(frozen=True)
class GetCacheEntryQuery(Query):
    """Query to get a specific cache entry."""
    cache_key: str
    

@dataclass(frozen=True)
class SearchCacheEntriesQuery(Query):
    """Query to search cache entries by criteria."""
    workspace_name: Optional[str] = None
    model_name: Optional[str] = None
    search_term: Optional[str] = None
    include_expired: bool = False
    limit: int = 100
    offset: int = 0
    

# Execution Context Queries
@dataclass(frozen=True)
class GetExecutionContextQuery(Query):
    """Query to get an execution context by ID."""
    context_id: UUID
    

@dataclass(frozen=True)
class ListExecutionContextsQuery(Query):
    """Query to list execution contexts with filtering."""
    workspace_name: Optional[str] = None
    execution_mode: Optional[ExecutionMode] = None
    active_only: bool = False
    limit: int = 100
    offset: int = 0
    

@dataclass(frozen=True)
class GetActiveExecutionContextsQuery(Query):
    """Query to get currently active execution contexts."""
    workspace_name: Optional[str] = None
    

# LLM Request History Queries
@dataclass(frozen=True)
class GetLLMRequestHistoryQuery(Query):
    """Query to get LLM request history."""
    execution_context_id: Optional[UUID] = None
    workspace_name: Optional[str] = None
    model_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0
    

@dataclass(frozen=True)
class GetLLMRequestPerformanceQuery(Query):
    """Query to get LLM request performance metrics."""
    model_name: Optional[str] = None
    workspace_name: Optional[str] = None
    period: str = "day"
    

# Query Handler Interfaces
class GetLLMProvidersQueryHandler(QueryHandler[GetLLMProvidersQuery, List[LLMProvider]], ABC):
    """Handler for GetLLMProvidersQuery."""
    
    @abstractmethod
    async def handle(self, query: GetLLMProvidersQuery) -> List[LLMProvider]:
        """Handle the get LLM providers query."""
        pass


class GetLLMProviderQueryHandler(QueryHandler[GetLLMProviderQuery, Optional[LLMProvider]], ABC):
    """Handler for GetLLMProviderQuery."""
    
    @abstractmethod
    async def handle(self, query: GetLLMProviderQuery) -> Optional[LLMProvider]:
        """Handle the get LLM provider query."""
        pass


class GetLLMProviderHealthQueryHandler(QueryHandler[GetLLMProviderHealthQuery, Dict[str, Any]], ABC):
    """Handler for GetLLMProviderHealthQuery."""
    
    @abstractmethod
    async def handle(self, query: GetLLMProviderHealthQuery) -> Dict[str, Any]:
        """Handle the get LLM provider health query."""
        pass


class SearchLLMProvidersQueryHandler(QueryHandler[SearchLLMProvidersQuery, List[LLMProvider]], ABC):
    """Handler for SearchLLMProvidersQuery."""
    
    @abstractmethod
    async def handle(self, query: SearchLLMProvidersQuery) -> List[LLMProvider]:
        """Handle the search LLM providers query."""
        pass


class GetTokenUsageQueryHandler(QueryHandler[GetTokenUsageQuery, Optional[TokenUsage]], ABC):
    """Handler for GetTokenUsageQuery."""
    
    @abstractmethod
    async def handle(self, query: GetTokenUsageQuery) -> Optional[TokenUsage]:
        """Handle the get token usage query."""
        pass


class ListTokenUsageQueryHandler(QueryHandler[ListTokenUsageQuery, List[TokenUsage]], ABC):
    """Handler for ListTokenUsageQuery."""
    
    @abstractmethod
    async def handle(self, query: ListTokenUsageQuery) -> List[TokenUsage]:
        """Handle the list token usage query."""
        pass


class GetTokenAnalyticsQueryHandler(QueryHandler[GetTokenAnalyticsQuery, Dict[str, Any]], ABC):
    """Handler for GetTokenAnalyticsQuery."""
    
    @abstractmethod
    async def handle(self, query: GetTokenAnalyticsQuery) -> Dict[str, Any]:
        """Handle the get token analytics query."""
        pass


class GetTopTokenConsumersQueryHandler(QueryHandler[GetTopTokenConsumersQuery, List[Dict[str, Any]]], ABC):
    """Handler for GetTopTokenConsumersQuery."""
    
    @abstractmethod
    async def handle(self, query: GetTopTokenConsumersQuery) -> List[Dict[str, Any]]:
        """Handle the get top token consumers query."""
        pass


class GetCacheStatsQueryHandler(QueryHandler[GetCacheStatsQuery, Dict[str, Any]], ABC):
    """Handler for GetCacheStatsQuery."""
    
    @abstractmethod
    async def handle(self, query: GetCacheStatsQuery) -> Dict[str, Any]:
        """Handle the get cache stats query."""
        pass


class GetCacheEntryQueryHandler(QueryHandler[GetCacheEntryQuery, Optional[Dict[str, Any]]], ABC):
    """Handler for GetCacheEntryQuery."""
    
    @abstractmethod
    async def handle(self, query: GetCacheEntryQuery) -> Optional[Dict[str, Any]]:
        """Handle the get cache entry query."""
        pass


class SearchCacheEntriesQueryHandler(QueryHandler[SearchCacheEntriesQuery, List[Dict[str, Any]]], ABC):
    """Handler for SearchCacheEntriesQuery."""
    
    @abstractmethod
    async def handle(self, query: SearchCacheEntriesQuery) -> List[Dict[str, Any]]:
        """Handle the search cache entries query."""
        pass


class GetExecutionContextQueryHandler(QueryHandler[GetExecutionContextQuery, Optional[ExecutionContext]], ABC):
    """Handler for GetExecutionContextQuery."""
    
    @abstractmethod
    async def handle(self, query: GetExecutionContextQuery) -> Optional[ExecutionContext]:
        """Handle the get execution context query."""
        pass


class ListExecutionContextsQueryHandler(QueryHandler[ListExecutionContextsQuery, List[ExecutionContext]], ABC):
    """Handler for ListExecutionContextsQuery."""
    
    @abstractmethod
    async def handle(self, query: ListExecutionContextsQuery) -> List[ExecutionContext]:
        """Handle the list execution contexts query."""
        pass


class GetActiveExecutionContextsQueryHandler(QueryHandler[GetActiveExecutionContextsQuery, List[ExecutionContext]], ABC):
    """Handler for GetActiveExecutionContextsQuery."""
    
    @abstractmethod
    async def handle(self, query: GetActiveExecutionContextsQuery) -> List[ExecutionContext]:
        """Handle the get active execution contexts query."""
        pass


class GetLLMRequestHistoryQueryHandler(QueryHandler[GetLLMRequestHistoryQuery, List[Dict[str, Any]]], ABC):
    """Handler for GetLLMRequestHistoryQuery."""
    
    @abstractmethod
    async def handle(self, query: GetLLMRequestHistoryQuery) -> List[Dict[str, Any]]:
        """Handle the get LLM request history query."""
        pass


class GetLLMRequestPerformanceQueryHandler(QueryHandler[GetLLMRequestPerformanceQuery, Dict[str, Any]], ABC):
    """Handler for GetLLMRequestPerformanceQuery."""
    
    @abstractmethod
    async def handle(self, query: GetLLMRequestPerformanceQuery) -> Dict[str, Any]:
        """Handle the get LLM request performance query."""
        pass
