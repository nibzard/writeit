"""LMDB implementation of TokenUsageRepository.

Provides concrete LMDB-backed storage for token usage tracking with
workspace isolation and usage analytics capabilities.
"""

from typing import List, Optional, Any, Dict
from datetime import datetime, timedelta
import uuid

from ...domains.execution.repositories.token_usage_repository import TokenUsageRepository
from ...domains.execution.value_objects.model_name import ModelName
from ...domains.execution.value_objects.token_count import TokenCount
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError, EntityNotFoundError
from ..base.repository_base import LMDBRepositoryBase
from ..base.storage_manager import LMDBStorageManager
from ..base.serialization import DomainEntitySerializer


class TokenUsageRecord:
    """Token usage record entity."""
    
    def __init__(
        self,
        record_id: str,
        model_name: ModelName,
        operation_type: str,
        input_tokens: TokenCount,
        output_tokens: TokenCount,
        total_tokens: TokenCount,
        cost_estimate: Optional[float] = None,
        pipeline_run_id: Optional[str] = None,
        step_id: Optional[str] = None,
        created_at: datetime = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.record_id = record_id
        self.model_name = model_name
        self.operation_type = operation_type
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = total_tokens
        self.cost_estimate = cost_estimate
        self.pipeline_run_id = pipeline_run_id
        self.step_id = step_id
        self.created_at = created_at or datetime.now()
        self.metadata = metadata or {}


class LMDBTokenUsageRepository(LMDBRepositoryBase[TokenUsageRecord], TokenUsageRepository):
    """LMDB implementation of TokenUsageRepository.
    
    Stores token usage records with workspace isolation and provides
    comprehensive usage analytics and cost tracking.
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
            entity_type=TokenUsageRecord,
            db_name="token_usage",
            db_key="usage_records"
        )
    
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with token usage-specific types."""
        serializer.register_value_object(ModelName)
        serializer.register_value_object(TokenCount)
        serializer.register_value_object(WorkspaceName)
        serializer.register_type("TokenUsageRecord", TokenUsageRecord)
    
    def _get_entity_id(self, entity: TokenUsageRecord) -> Any:
        """Extract entity ID for storage key."""
        return entity.record_id
    
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID."""
        workspace_prefix = self._get_workspace_prefix()
        return f"{workspace_prefix}usage:{str(entity_id)}"
    
    async def record_usage(
        self,
        model_name: ModelName,
        operation_type: str,
        input_tokens: TokenCount,
        output_tokens: TokenCount,
        pipeline_run_id: Optional[str] = None,
        step_id: Optional[str] = None,
        cost_estimate: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record token usage for an operation."""
        record_id = f"usage-{uuid.uuid4().hex[:8]}"
        total_tokens = TokenCount(input_tokens.value + output_tokens.value)
        
        usage_record = TokenUsageRecord(
            record_id=record_id,
            model_name=model_name,
            operation_type=operation_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            cost_estimate=cost_estimate,
            pipeline_run_id=pipeline_run_id,
            step_id=step_id,
            metadata=metadata
        )
        
        await self.save(usage_record)
        return record_id
    
    async def get_usage_by_model(
        self, 
        model_name: ModelName,
        since: Optional[datetime] = None
    ) -> List[TokenUsageRecord]:
        """Get usage records for a specific model."""
        all_usage = await self.find_by_workspace()
        model_usage = [u for u in all_usage if u.model_name == model_name]
        
        if since:
            model_usage = [u for u in model_usage if u.created_at >= since]
        
        return model_usage
    
    async def get_usage_by_pipeline_run(self, run_id: str) -> List[TokenUsageRecord]:
        """Get usage records for a specific pipeline run."""
        all_usage = await self.find_by_workspace()
        return [u for u in all_usage if u.pipeline_run_id == run_id]
    
    async def get_daily_usage(
        self, 
        date: datetime,
        model_name: Optional[ModelName] = None
    ) -> Dict[str, Any]:
        """Get token usage for a specific day."""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        all_usage = await self.find_by_workspace()
        day_usage = [
            u for u in all_usage 
            if start_of_day <= u.created_at < end_of_day
        ]
        
        if model_name:
            day_usage = [u for u in day_usage if u.model_name == model_name]
        
        total_input = sum(u.input_tokens.value for u in day_usage)
        total_output = sum(u.output_tokens.value for u in day_usage)
        total_cost = sum(u.cost_estimate for u in day_usage if u.cost_estimate)
        
        return {
            "date": date.date().isoformat(),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost": total_cost,
            "operation_count": len(day_usage)
        }
    
    async def get_usage_statistics(
        self, 
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get comprehensive usage statistics."""
        all_usage = await self.find_by_workspace()
        
        if since:
            all_usage = [u for u in all_usage if u.created_at >= since]
        
        if not all_usage:
            return {
                "total_records": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "models": {},
                "operations": {}
            }
        
        # Calculate totals
        total_input = sum(u.input_tokens.value for u in all_usage)
        total_output = sum(u.output_tokens.value for u in all_usage)
        total_cost = sum(u.cost_estimate for u in all_usage if u.cost_estimate)
        
        # Count by model
        models = {}
        for usage in all_usage:
            model = str(usage.model_name)
            if model not in models:
                models[model] = {
                    "count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0.0
                }
            models[model]["count"] += 1
            models[model]["input_tokens"] += usage.input_tokens.value
            models[model]["output_tokens"] += usage.output_tokens.value
            if usage.cost_estimate:
                models[model]["cost"] += usage.cost_estimate
        
        # Count by operation type
        operations = {}
        for usage in all_usage:
            op_type = usage.operation_type
            if op_type not in operations:
                operations[op_type] = {
                    "count": 0,
                    "tokens": 0
                }
            operations[op_type]["count"] += 1
            operations[op_type]["tokens"] += usage.total_tokens.value
        
        return {
            "total_records": len(all_usage),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "total_cost": total_cost,
            "models": models,
            "operations": operations
        }
    
    async def get_cost_analysis(
        self, 
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get cost analysis and trends."""
        all_usage = await self.find_by_workspace()
        
        if since:
            all_usage = [u for u in all_usage if u.created_at >= since]
        
        # Filter records with cost estimates
        usage_with_cost = [u for u in all_usage if u.cost_estimate is not None]
        
        if not usage_with_cost:
            return {
                "total_cost": 0.0,
                "average_cost_per_operation": 0.0,
                "cost_by_model": {},
                "daily_costs": []
            }
        
        total_cost = sum(u.cost_estimate for u in usage_with_cost)
        avg_cost = total_cost / len(usage_with_cost)
        
        # Cost by model
        cost_by_model = {}
        for usage in usage_with_cost:
            model = str(usage.model_name)
            cost_by_model[model] = cost_by_model.get(model, 0.0) + usage.cost_estimate
        
        return {
            "total_cost": total_cost,
            "average_cost_per_operation": avg_cost,
            "cost_by_model": cost_by_model,
            "records_with_cost": len(usage_with_cost),
            "total_records": len(all_usage)
        }
    
    async def cleanup_old_records(self, older_than_days: int = 90) -> int:
        """Clean up old usage records."""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        all_usage = await self.find_by_workspace()
        
        old_records = [u for u in all_usage if u.created_at < cutoff_date]
        
        deleted_count = 0
        for record in old_records:
            if await self.delete_by_id(record.record_id):
                deleted_count += 1
        
        return deleted_count