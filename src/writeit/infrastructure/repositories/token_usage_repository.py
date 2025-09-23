"""LMDB implementation of TokenUsageRepository.

Provides persistent storage for token usage metrics using LMDB
with analytics and billing support.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from ...domains.execution.repositories.token_usage_repository import TokenUsageRepository
from ...domains.execution.entities.token_usage import TokenUsage
from ...domains.execution.value_objects.model_name import ModelName
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError
from ..persistence.lmdb_storage import LMDBStorage
from ..base.exceptions import StorageError


class LMDBTokenUsageRepository(TokenUsageRepository):
    """LMDB-based implementation of TokenUsageRepository.
    
    Stores token usage metrics with analytics and billing support.
    """
    
    def __init__(self, storage: LMDBStorage, workspace: Optional[WorkspaceName] = None):
        """Initialize repository.
        
        Args:
            storage: LMDB storage instance
            workspace: Current workspace (if None, uses global scope)
        """
        super().__init__(workspace)
        self.storage = storage
        self._db_name = "token_usage"
    
    async def save(self, usage: TokenUsage) -> None:
        """Save token usage record.
        
        Args:
            usage: Token usage to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        try:
            key = self._make_key(usage.id, usage.workspace)
            
            await self.storage.store_entity(
                usage,
                key,
                self._db_name
            )
            
        except StorageError as e:
            raise RepositoryError(f"Failed to save token usage {usage.id}: {e}") from e
    
    async def find_by_id(self, usage_id: UUID) -> Optional[TokenUsage]:
        """Find token usage by ID.
        
        Args:
            usage_id: Usage ID to search for
            
        Returns:
            Token usage if found, None otherwise
        """
        try:
            key = self._make_key(usage_id, self.workspace)
            return await self.storage.load_entity(
                key,
                TokenUsage,
                self._db_name
            )
        except StorageError as e:
            raise RepositoryError(f"Failed to find token usage {usage_id}: {e}") from e
    
    async def find_by_model(self, model: ModelName) -> List[TokenUsage]:
        """Find token usage by model.
        
        Args:
            model: Model name to filter by
            
        Returns:
            List of token usage records for the model
        """
        try:
            all_usage = await self._get_all_usage()
            
            model_usage = [
                usage for usage in all_usage
                if usage.model_name == model
            ]
            
            # Sort by timestamp descending
            model_usage.sort(key=lambda u: u.timestamp, reverse=True)
            
            return model_usage
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find usage by model {model}: {e}") from e
    
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[TokenUsage]:
        """Find token usage within date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of token usage records in the date range
        """
        try:
            all_usage = await self._get_all_usage()
            
            date_usage = [
                usage for usage in all_usage
                if start_date <= usage.timestamp <= end_date
            ]
            
            return date_usage
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to find usage in date range {start_date} to {end_date}: {e}"
            ) from e
    
    async def find_by_operation(self, operation: str) -> List[TokenUsage]:
        """Find token usage by operation type.
        
        Args:
            operation: Operation type to filter by
            
        Returns:
            List of token usage records for the operation
        """
        try:
            all_usage = await self._get_all_usage()
            
            operation_usage = [
                usage for usage in all_usage
                if usage.operation_type == operation
            ]
            
            return operation_usage
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find usage by operation {operation}: {e}") from e
    
    async def get_daily_usage(
        self,
        date: datetime,
        model: Optional[ModelName] = None
    ) -> Dict[str, Any]:
        """Get aggregated usage for a specific day.
        
        Args:
            date: Date to analyze
            model: Specific model (None for all models)
            
        Returns:
            Dictionary with daily usage metrics
        """
        try:
            # Get usage for the entire day
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
            
            daily_usage = await self.find_by_date_range(start_date, end_date)
            
            # Filter by model if specified
            if model:
                daily_usage = [
                    usage for usage in daily_usage
                    if usage.model_name == model
                ]
            
            # Aggregate metrics
            total_tokens = sum(usage.total_tokens for usage in daily_usage)
            prompt_tokens = sum(usage.prompt_tokens for usage in daily_usage)
            completion_tokens = sum(usage.completion_tokens for usage in daily_usage)
            total_cost = sum(usage.estimated_cost for usage in daily_usage)
            
            # Count operations
            operation_counts = {}
            for usage in daily_usage:
                op = usage.operation_type
                operation_counts[op] = operation_counts.get(op, 0) + 1
            
            # Model breakdown
            model_breakdown = {}
            for usage in daily_usage:
                model_str = usage.model_name.value
                if model_str not in model_breakdown:
                    model_breakdown[model_str] = {
                        "total_tokens": 0,
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "cost": 0.0,
                        "requests": 0
                    }
                
                breakdown = model_breakdown[model_str]
                breakdown["total_tokens"] += usage.total_tokens
                breakdown["prompt_tokens"] += usage.prompt_tokens
                breakdown["completion_tokens"] += usage.completion_tokens
                breakdown["cost"] += usage.estimated_cost
                breakdown["requests"] += 1
            
            return {
                "date": date.date().isoformat(),
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_cost": total_cost,
                "total_requests": len(daily_usage),
                "operation_counts": operation_counts,
                "model_breakdown": model_breakdown,
                "workspace": self.workspace.value if self.workspace else "global"
            }
            
        except StorageError as e:
            raise RepositoryError(f"Failed to get daily usage for {date}: {e}") from e
    
    async def get_monthly_usage(
        self,
        year: int,
        month: int,
        model: Optional[ModelName] = None
    ) -> Dict[str, Any]:
        """Get aggregated usage for a specific month.
        
        Args:
            year: Year
            month: Month (1-12)
            model: Specific model (None for all models)
            
        Returns:
            Dictionary with monthly usage metrics
        """
        try:
            # Get date range for the month
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(microseconds=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(microseconds=1)
            
            monthly_usage = await self.find_by_date_range(start_date, end_date)
            
            # Filter by model if specified
            if model:
                monthly_usage = [
                    usage for usage in monthly_usage
                    if usage.model_name == model
                ]
            
            # Aggregate metrics
            total_tokens = sum(usage.total_tokens for usage in monthly_usage)
            prompt_tokens = sum(usage.prompt_tokens for usage in monthly_usage)
            completion_tokens = sum(usage.completion_tokens for usage in monthly_usage)
            total_cost = sum(usage.estimated_cost for usage in monthly_usage)
            
            # Daily breakdown
            daily_breakdown = {}
            for usage in monthly_usage:
                day_key = usage.timestamp.date().isoformat()
                if day_key not in daily_breakdown:
                    daily_breakdown[day_key] = {
                        "tokens": 0,
                        "cost": 0.0,
                        "requests": 0
                    }
                
                daily_breakdown[day_key]["tokens"] += usage.total_tokens
                daily_breakdown[day_key]["cost"] += usage.estimated_cost
                daily_breakdown[day_key]["requests"] += 1
            
            return {
                "year": year,
                "month": month,
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_cost": total_cost,
                "total_requests": len(monthly_usage),
                "daily_breakdown": daily_breakdown,
                "workspace": self.workspace.value if self.workspace else "global"
            }
            
        except StorageError as e:
            raise RepositoryError(f"Failed to get monthly usage for {year}-{month}: {e}") from e
    
    async def get_model_statistics(self, model: ModelName) -> Dict[str, Any]:
        """Get statistics for specific model.
        
        Args:
            model: Model to analyze
            
        Returns:
            Dictionary with model statistics
        """
        try:
            model_usage = await self.find_by_model(model)
            
            if not model_usage:
                return {
                    "model": model.value,
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "average_tokens_per_request": 0,
                    "first_used": None,
                    "last_used": None
                }
            
            total_requests = len(model_usage)
            total_tokens = sum(usage.total_tokens for usage in model_usage)
            total_cost = sum(usage.estimated_cost for usage in model_usage)
            
            avg_tokens = total_tokens / total_requests if total_requests > 0 else 0
            
            # Sort by timestamp to get first and last usage
            sorted_usage = sorted(model_usage, key=lambda u: u.timestamp)
            first_used = sorted_usage[0].timestamp
            last_used = sorted_usage[-1].timestamp
            
            return {
                "model": model.value,
                "total_requests": total_requests,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "average_tokens_per_request": avg_tokens,
                "first_used": first_used.isoformat(),
                "last_used": last_used.isoformat(),
                "workspace": self.workspace.value if self.workspace else "global"
            }
            
        except StorageError as e:
            raise RepositoryError(f"Failed to get model statistics for {model}: {e}") from e
    
    async def detect_usage_anomalies(
        self,
        threshold_multiplier: float = 3.0
    ) -> List[TokenUsage]:
        """Detect anomalous usage patterns.
        
        Args:
            threshold_multiplier: Multiplier for anomaly detection threshold
            
        Returns:
            List of anomalous usage records
        """
        try:
            # Get recent usage (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_usage = await self.find_by_date_range(cutoff_date, datetime.now())
            
            if len(recent_usage) < 10:  # Need sufficient data
                return []
            
            # Calculate average and standard deviation
            token_counts = [usage.total_tokens for usage in recent_usage]
            avg_tokens = sum(token_counts) / len(token_counts)
            
            variance = sum((x - avg_tokens) ** 2 for x in token_counts) / len(token_counts)
            std_dev = variance ** 0.5
            
            # Find anomalies (usage > threshold)
            threshold = avg_tokens + (threshold_multiplier * std_dev)
            
            anomalies = [
                usage for usage in recent_usage
                if usage.total_tokens > threshold
            ]
            
            return anomalies
            
        except StorageError as e:
            raise RepositoryError(f"Failed to detect usage anomalies: {e}") from e
    
    async def cleanup_old_records(self, days: int = 365) -> int:
        """Clean up old usage records.
        
        Args:
            days: Number of days to keep (older records will be deleted)
            
        Returns:
            Number of records deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            all_usage = await self._get_all_usage()
            
            # Find old records
            old_records = [
                usage for usage in all_usage
                if usage.timestamp < cutoff_date
            ]
            
            # Delete old records
            deleted_count = 0
            for usage in old_records:
                if await self.delete(str(usage.id)):
                    deleted_count += 1
            
            return deleted_count
            
        except StorageError as e:
            raise RepositoryError(f"Failed to cleanup old records: {e}") from e
    
    async def find_all(self) -> List[TokenUsage]:
        """Find all token usage records.
        
        Returns:
            List of all usage records
        """
        return await self._get_all_usage()
    
    async def delete(self, usage_id: str) -> bool:
        """Delete a token usage record.
        
        Args:
            usage_id: ID of usage record to delete
            
        Returns:
            True if record was deleted, False if not found
        """
        try:
            usage_uuid = UUID(usage_id)
            key = self._make_key(usage_uuid, self.workspace)
            return await self.storage.delete_entity(key, self._db_name)
            
        except (StorageError, ValueError) as e:
            raise RepositoryError(f"Failed to delete usage record {usage_id}: {e}") from e
    
    async def count(self) -> int:
        """Count token usage records.
        
        Returns:
            Number of usage records
        """
        try:
            if self.workspace:
                prefix = f"usage:{self.workspace.value}:"
            else:
                prefix = "usage:"
            
            return await self.storage.count_entities(prefix, self._db_name)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to count usage records: {e}") from e
    
    def _make_key(self, usage_id: UUID, workspace: Optional[WorkspaceName]) -> str:
        """Create storage key for usage record.
        
        Args:
            usage_id: Usage ID
            workspace: Workspace (None for global)
            
        Returns:
            Storage key
        """
        if workspace:
            return f"usage:{workspace.value}:{usage_id}"
        else:
            return f"usage:global:{usage_id}"
    
    async def _get_all_usage(self) -> List[TokenUsage]:
        """Get all usage records in current workspace.
        
        Returns:
            List of all usage records
        """
        if self.workspace:
            prefix = f"usage:{self.workspace.value}:"
        else:
            prefix = "usage:"
        
        return await self.storage.find_entities_by_prefix(
            prefix,
            TokenUsage,
            self._db_name
        )
