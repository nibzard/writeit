"""Token usage repository interface.

Provides data access operations for token usage tracking including
usage analytics, billing data, and consumption monitoring.
"""

from abc import abstractmethod
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from ....shared.repository import Repository, Specification
from ....domains.workspace.value_objects.workspace_name import WorkspaceName
from ..value_objects.model_name import ModelName
from ..value_objects.token_count import TokenCount


class TokenUsageRecord:
    """Value object representing a token usage record.
    
    Contains usage data, billing information, and metadata.
    """
    
    def __init__(
        self,
        usage_id: UUID,
        workspace: WorkspaceName,
        model_name: ModelName,
        prompt_tokens: TokenCount,
        completion_tokens: TokenCount,
        total_tokens: TokenCount,
        timestamp: datetime,
        pipeline_run_id: Optional[UUID] = None,
        step_execution_id: Optional[UUID] = None,
        cost_estimate: Optional[float] = None,
        request_duration_ms: Optional[int] = None,
        cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.usage_id = usage_id
        self.workspace = workspace
        self.model_name = model_name
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = total_tokens
        self.timestamp = timestamp
        self.pipeline_run_id = pipeline_run_id
        self.step_execution_id = step_execution_id
        self.cost_estimate = cost_estimate
        self.request_duration_ms = request_duration_ms
        self.cache_hit = cache_hit
        self.metadata = metadata or {}
    
    @property
    def tokens_per_second(self) -> Optional[float]:
        """Calculate tokens per second rate."""
        if self.request_duration_ms is None or self.request_duration_ms == 0:
            return None
        return (self.total_tokens.value * 1000) / self.request_duration_ms
    
    @property
    def cost_per_token(self) -> Optional[float]:
        """Calculate cost per token."""
        if self.cost_estimate is None or self.total_tokens.value == 0:
            return None
        return self.cost_estimate / self.total_tokens.value


class TokenUsageRepository(Repository[TokenUsageRecord]):
    """Repository for token usage record persistence and retrieval.
    
    Handles CRUD operations for token usage tracking with analytics,
    billing data, and consumption monitoring.
    """
    
    @abstractmethod
    async def record_usage(
        self,
        workspace: WorkspaceName,
        model_name: ModelName,
        prompt_tokens: TokenCount,
        completion_tokens: TokenCount,
        pipeline_run_id: Optional[UUID] = None,
        step_execution_id: Optional[UUID] = None,
        cost_estimate: Optional[float] = None,
        request_duration_ms: Optional[int] = None,
        cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ) -> TokenUsageRecord:
        """Record a new token usage event.
        
        Args:
            workspace: Workspace where usage occurred
            model_name: Model that consumed tokens
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            pipeline_run_id: Optional pipeline run ID
            step_execution_id: Optional step execution ID
            cost_estimate: Estimated cost of the request
            request_duration_ms: Request duration in milliseconds
            cache_hit: Whether this was a cache hit
            metadata: Additional usage metadata
            
        Returns:
            Created usage record
            
        Raises:
            RepositoryError: If recording fails
        """
        pass
    
    @abstractmethod
    async def find_by_workspace(
        self, 
        workspace: WorkspaceName,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[TokenUsageRecord]:
        """Find usage records for a workspace.
        
        Args:
            workspace: Workspace to get usage for
            since: Optional start date filter
            until: Optional end date filter
            
        Returns:
            List of usage records for the workspace
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_model(
        self, 
        model_name: ModelName,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[TokenUsageRecord]:
        """Find usage records for a model.
        
        Args:
            model_name: Model to get usage for
            since: Optional start date filter
            until: Optional end date filter
            
        Returns:
            List of usage records for the model
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_pipeline_run(
        self, 
        run_id: UUID
    ) -> List[TokenUsageRecord]:
        """Find usage records for a pipeline run.
        
        Args:
            run_id: Pipeline run identifier
            
        Returns:
            List of usage records for the run
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def get_usage_summary(
        self,
        workspace: Optional[WorkspaceName] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get token usage summary statistics.
        
        Args:
            workspace: Optional workspace filter
            since: Optional start date filter
            until: Optional end date filter
            
        Returns:
            Dictionary with usage summary:
            - total_tokens: Total tokens consumed
            - prompt_tokens: Total prompt tokens
            - completion_tokens: Total completion tokens
            - total_cost: Total estimated cost
            - requests_count: Number of requests
            - cache_hit_rate: Cache hit percentage
            - average_tokens_per_request: Average tokens per request
            - models_used: List of models used
            - peak_usage_hour: Hour with highest usage
            
        Raises:
            RepositoryError: If calculation fails
        """
        pass
    
    @abstractmethod
    async def get_daily_usage(
        self,
        workspace: Optional[WorkspaceName] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily token usage breakdown.
        
        Args:
            workspace: Optional workspace filter
            days: Number of days to include
            
        Returns:
            List of daily usage dictionaries:
            - date: Usage date
            - total_tokens: Tokens used that day
            - total_cost: Estimated cost that day
            - requests_count: Number of requests
            - models_breakdown: Usage by model
            
        Raises:
            RepositoryError: If calculation fails
        """
        pass
    
    @abstractmethod
    async def get_model_usage_stats(
        self,
        workspace: Optional[WorkspaceName] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get usage statistics by model.
        
        Args:
            workspace: Optional workspace filter
            since: Optional start date filter
            
        Returns:
            List of model usage dictionaries:
            - model_name: Model name
            - total_tokens: Total tokens used
            - total_cost: Total estimated cost
            - requests_count: Number of requests
            - average_tokens_per_request: Average tokens per request
            - cache_hit_rate: Cache hit percentage
            
        Raises:
            RepositoryError: If calculation fails
        """
        pass
    
    @abstractmethod
    async def get_workspace_rankings(
        self, 
        metric: str = "total_tokens",
        since: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get workspace rankings by usage metric.
        
        Args:
            metric: Metric to rank by (total_tokens, total_cost, requests_count)
            since: Optional start date filter
            limit: Maximum number of workspaces to return
            
        Returns:
            List of workspace ranking dictionaries:
            - workspace: Workspace name
            - metric_value: Value of the ranking metric
            - percentage_of_total: Percentage of total usage
            
        Raises:
            RepositoryError: If calculation fails
        """
        pass
    
    @abstractmethod
    async def get_cost_projection(
        self,
        workspace: WorkspaceName,
        projection_days: int = 30
    ) -> Dict[str, Any]:
        """Get cost projection based on recent usage.
        
        Args:
            workspace: Workspace to project for
            projection_days: Number of days to project
            
        Returns:
            Dictionary with cost projection:
            - current_daily_average: Current daily cost average
            - projected_monthly_cost: Projected monthly cost
            - confidence_level: Confidence in projection (0-1)
            - trend: Usage trend (increasing/decreasing/stable)
            
        Raises:
            RepositoryError: If calculation fails
        """
        pass
    
    @abstractmethod
    async def get_anomaly_detection(
        self,
        workspace: Optional[WorkspaceName] = None,
        sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect usage anomalies (spikes or unusual patterns).
        
        Args:
            workspace: Optional workspace filter
            sensitivity: Anomaly detection sensitivity (standard deviations)
            
        Returns:
            List of anomaly dictionaries:
            - timestamp: When anomaly occurred
            - metric: Which metric was anomalous
            - value: Anomalous value
            - expected_range: Expected value range
            - severity: Anomaly severity (low/medium/high)
            
        Raises:
            RepositoryError: If detection fails
        """
        pass
    
    @abstractmethod
    async def cleanup_old_records(
        self,
        older_than: datetime,
        keep_summary: bool = True
    ) -> int:
        """Clean up old usage records.
        
        Args:
            older_than: Delete records older than this date
            keep_summary: Whether to keep summary data
            
        Returns:
            Number of records deleted
            
        Raises:
            RepositoryError: If cleanup fails
        """
        pass
    
    @abstractmethod
    async def export_billing_data(
        self,
        workspace: WorkspaceName,
        start_date: datetime,
        end_date: datetime,
        format: str = "csv"
    ) -> bytes:
        """Export billing data for a date range.
        
        Args:
            workspace: Workspace to export data for
            start_date: Start of export range
            end_date: End of export range
            format: Export format (csv, json, xlsx)
            
        Returns:
            Exported data as bytes
            
        Raises:
            RepositoryError: If export fails
        """
        pass


# Specifications for token usage queries

class ByWorkspaceSpecification(Specification[TokenUsageRecord]):
    """Specification for filtering usage records by workspace."""
    
    def __init__(self, workspace: WorkspaceName):
        self.workspace = workspace
    
    def is_satisfied_by(self, record: TokenUsageRecord) -> bool:
        return record.workspace == self.workspace


class ByModelSpecification(Specification[TokenUsageRecord]):
    """Specification for filtering usage records by model."""
    
    def __init__(self, model_name: ModelName):
        self.model_name = model_name
    
    def is_satisfied_by(self, record: TokenUsageRecord) -> bool:
        return record.model_name == self.model_name


class DateRangeSpecification(Specification[TokenUsageRecord]):
    """Specification for filtering usage records by date range."""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
    
    def is_satisfied_by(self, record: TokenUsageRecord) -> bool:
        return self.start_date <= record.timestamp <= self.end_date


class ByPipelineRunSpecification(Specification[TokenUsageRecord]):
    """Specification for filtering usage records by pipeline run."""
    
    def __init__(self, run_id: UUID):
        self.run_id = run_id
    
    def is_satisfied_by(self, record: TokenUsageRecord) -> bool:
        return record.pipeline_run_id == self.run_id


class CacheHitSpecification(Specification[TokenUsageRecord]):
    """Specification for filtering cache hit records."""
    
    def is_satisfied_by(self, record: TokenUsageRecord) -> bool:
        return record.cache_hit


class HighCostSpecification(Specification[TokenUsageRecord]):
    """Specification for filtering high-cost usage records."""
    
    def __init__(self, min_cost: float):
        self.min_cost = min_cost
    
    def is_satisfied_by(self, record: TokenUsageRecord) -> bool:
        return record.cost_estimate is not None and record.cost_estimate >= self.min_cost


class HighTokenUsageSpecification(Specification[TokenUsageRecord]):
    """Specification for filtering high token usage records."""
    
    def __init__(self, min_tokens: int):
        self.min_tokens = min_tokens
    
    def is_satisfied_by(self, record: TokenUsageRecord) -> bool:
        return record.total_tokens.value >= self.min_tokens
