"""Mock implementation of TokenUsageRepository for testing."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from writeit.domains.execution.repositories.token_usage_repository import (
    TokenUsageRepository, TokenUsageRecord
)
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.domains.execution.value_objects.model_name import ModelName
from writeit.domains.execution.value_objects.token_count import TokenCount
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError


class MockTokenUsageRepository(BaseMockRepository[TokenUsageRecord], TokenUsageRepository):
    """Mock implementation of TokenUsageRepository.
    
    Provides in-memory storage for token usage tracking with analytics,
    billing data, and consumption monitoring.
    """
    
    def __init__(self):
        # Token usage repository doesn't have workspace isolation
        super().__init__(None)
        
    def _get_entity_id(self, entity: TokenUsageRecord) -> Any:
        """Extract entity ID from token usage record."""
        return str(entity.usage_id)
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "TokenUsageRecord"
        
    # Repository interface implementation
    
    async def save(self, entity: TokenUsageRecord) -> None:
        """Save or update a token usage record."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id, workspace="global")
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: UUID) -> Optional[TokenUsageRecord]:
        """Find token usage record by ID."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        record = self._get_entity(str(entity_id), workspace="global")
        self._log_event("find_by_id", self._get_entity_type_name(), 
                       str(entity_id), found=record is not None)
        return record
        
    async def find_all(self) -> List[TokenUsageRecord]:
        """Find all token usage records."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        records = self._get_all_entities(workspace="global")
        self._log_event("find_all", self._get_entity_type_name(), count=len(records))
        return records
        
    async def find_by_specification(self, spec: Specification[TokenUsageRecord]) -> List[TokenUsageRecord]:
        """Find token usage records matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        records = self._find_entities_by_specification(spec, workspace="global")
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(records))
        return records
        
    async def exists(self, entity_id: UUID) -> bool:
        """Check if token usage record exists."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        exists = self._entity_exists(str(entity_id), workspace="global")
        self._log_event("exists", self._get_entity_type_name(), str(entity_id), exists=exists)
        return exists
        
    async def delete(self, entity: TokenUsageRecord) -> None:
        """Delete a token usage record."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id, workspace="global"):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: UUID) -> bool:
        """Delete token usage record by ID."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(str(entity_id), workspace="global")
        self._log_event("delete_by_id", self._get_entity_type_name(), 
                       str(entity_id), deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total token usage records."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        total = self._count_entities(workspace="global")
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    # TokenUsageRepository-specific methods
    
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
        """Record a new token usage event."""
        await self._check_error_condition("record_usage")
        self._increment_call_count("record_usage")
        await self._apply_call_delay("record_usage")
        
        total_tokens = TokenCount(prompt_tokens.value + completion_tokens.value)
        
        record = TokenUsageRecord(
            usage_id=uuid4(),
            workspace=workspace,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            timestamp=datetime.now(),
            pipeline_run_id=pipeline_run_id,
            step_execution_id=step_execution_id,
            cost_estimate=cost_estimate,
            request_duration_ms=request_duration_ms,
            cache_hit=cache_hit,
            metadata=metadata
        )
        
        await self.save(record)
        self._log_event("record_usage", self._get_entity_type_name(), 
                       str(record.usage_id), workspace=str(workspace.value), 
                       model=str(model_name.value), total_tokens=total_tokens.value)
        return record
        
    async def find_by_workspace(
        self, 
        workspace: WorkspaceName,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[TokenUsageRecord]:
        """Find usage records for a workspace."""
        await self._check_error_condition("find_by_workspace")
        self._increment_call_count("find_by_workspace")
        await self._apply_call_delay("find_by_workspace")
        
        records = self._get_all_entities(workspace="global")
        matching_records = [r for r in records if r.workspace == workspace]
        
        if since:
            matching_records = [r for r in matching_records if r.timestamp >= since]
        if until:
            matching_records = [r for r in matching_records if r.timestamp <= until]
            
        self._log_event("find_by_workspace", self._get_entity_type_name(), 
                       count=len(matching_records), workspace=str(workspace.value),
                       since=since, until=until)
        return matching_records
        
    async def find_by_model(
        self, 
        model_name: ModelName,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> List[TokenUsageRecord]:
        """Find usage records for a model."""
        await self._check_error_condition("find_by_model")
        self._increment_call_count("find_by_model")
        await self._apply_call_delay("find_by_model")
        
        records = self._get_all_entities(workspace="global")
        matching_records = [r for r in records if r.model_name == model_name]
        
        if since:
            matching_records = [r for r in matching_records if r.timestamp >= since]
        if until:
            matching_records = [r for r in matching_records if r.timestamp <= until]
            
        self._log_event("find_by_model", self._get_entity_type_name(), 
                       count=len(matching_records), model=str(model_name.value),
                       since=since, until=until)
        return matching_records
        
    async def find_by_pipeline_run(
        self, 
        run_id: UUID
    ) -> List[TokenUsageRecord]:
        """Find usage records for a pipeline run."""
        await self._check_error_condition("find_by_pipeline_run")
        self._increment_call_count("find_by_pipeline_run")
        await self._apply_call_delay("find_by_pipeline_run")
        
        records = self._get_all_entities(workspace="global")
        matching_records = [r for r in records if r.pipeline_run_id == run_id]
        
        self._log_event("find_by_pipeline_run", self._get_entity_type_name(), 
                       count=len(matching_records), run_id=str(run_id))
        return matching_records
        
    async def get_usage_summary(
        self,
        workspace: Optional[WorkspaceName] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get token usage summary statistics."""
        await self._check_error_condition("get_usage_summary")
        self._increment_call_count("get_usage_summary")
        await self._apply_call_delay("get_usage_summary")
        
        records = self._get_all_entities(workspace="global")
        
        if workspace:
            records = [r for r in records if r.workspace == workspace]
        if since:
            records = [r for r in records if r.timestamp >= since]
        if until:
            records = [r for r in records if r.timestamp <= until]
            
        if not records:
            summary = {
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_cost": 0.0,
                "requests_count": 0,
                "cache_hit_rate": 0.0,
                "average_tokens_per_request": 0.0,
                "models_used": [],
                "peak_usage_hour": 0
            }
        else:
            total_tokens = sum(r.total_tokens.value for r in records)
            prompt_tokens = sum(r.prompt_tokens.value for r in records)
            completion_tokens = sum(r.completion_tokens.value for r in records)
            total_cost = sum(r.cost_estimate or 0.0 for r in records)
            requests_count = len(records)
            cache_hits = len([r for r in records if r.cache_hit])
            cache_hit_rate = (cache_hits / requests_count * 100) if requests_count > 0 else 0
            avg_tokens_per_request = total_tokens / requests_count if requests_count > 0 else 0
            
            models_used = list(set(str(r.model_name.value) for r in records))
            
            # Find peak usage hour
            hour_usage = {}
            for record in records:
                hour = record.timestamp.hour
                hour_usage[hour] = hour_usage.get(hour, 0) + record.total_tokens.value
            peak_usage_hour = max(hour_usage.items(), key=lambda x: x[1])[0] if hour_usage else 0
            
            summary = {
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_cost": total_cost,
                "requests_count": requests_count,
                "cache_hit_rate": cache_hit_rate,
                "average_tokens_per_request": avg_tokens_per_request,
                "models_used": models_used,
                "peak_usage_hour": peak_usage_hour
            }
            
        self._log_event("get_usage_summary", self._get_entity_type_name(), 
                       workspace=str(workspace.value) if workspace else None,
                       since=since, until=until, **summary)
        return summary
        
    async def get_daily_usage(
        self,
        workspace: Optional[WorkspaceName] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily token usage breakdown."""
        await self._check_error_condition("get_daily_usage")
        self._increment_call_count("get_daily_usage")
        await self._apply_call_delay("get_daily_usage")
        
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        records = self._get_all_entities(workspace="global")
        if workspace:
            records = [r for r in records if r.workspace == workspace]
            
        # Group by date
        daily_usage = {}
        for record in records:
            record_date = record.timestamp.date()
            if start_date <= record_date <= end_date:
                if record_date not in daily_usage:
                    daily_usage[record_date] = {
                        "date": record_date.isoformat(),
                        "total_tokens": 0,
                        "total_cost": 0.0,
                        "requests_count": 0,
                        "models_breakdown": {}
                    }
                    
                daily_usage[record_date]["total_tokens"] += record.total_tokens.value
                daily_usage[record_date]["total_cost"] += record.cost_estimate or 0.0
                daily_usage[record_date]["requests_count"] += 1
                
                model = str(record.model_name.value)
                if model not in daily_usage[record_date]["models_breakdown"]:
                    daily_usage[record_date]["models_breakdown"][model] = 0
                daily_usage[record_date]["models_breakdown"][model] += record.total_tokens.value
                
        # Fill in missing days with zeros
        current_date = start_date
        while current_date <= end_date:
            if current_date not in daily_usage:
                daily_usage[current_date] = {
                    "date": current_date.isoformat(),
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "requests_count": 0,
                    "models_breakdown": {}
                }
            current_date += timedelta(days=1)
            
        result = list(daily_usage.values())
        result.sort(key=lambda x: x["date"])
        
        self._log_event("get_daily_usage", self._get_entity_type_name(), 
                       workspace=str(workspace.value) if workspace else None,
                       days=days, result_count=len(result))
        return result
        
    async def get_model_usage_stats(
        self,
        workspace: Optional[WorkspaceName] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get usage statistics by model."""
        await self._check_error_condition("get_model_usage_stats")
        self._increment_call_count("get_model_usage_stats")
        await self._apply_call_delay("get_model_usage_stats")
        
        records = self._get_all_entities(workspace="global")
        
        if workspace:
            records = [r for r in records if r.workspace == workspace]
        if since:
            records = [r for r in records if r.timestamp >= since]
            
        # Group by model
        model_stats = {}
        for record in records:
            model = str(record.model_name.value)
            if model not in model_stats:
                model_stats[model] = {
                    "model_name": model,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "requests_count": 0,
                    "cache_hits": 0
                }
                
            model_stats[model]["total_tokens"] += record.total_tokens.value
            model_stats[model]["total_cost"] += record.cost_estimate or 0.0
            model_stats[model]["requests_count"] += 1
            if record.cache_hit:
                model_stats[model]["cache_hits"] += 1
                
        # Calculate derived metrics
        for stats in model_stats.values():
            requests = stats["requests_count"]
            stats["average_tokens_per_request"] = stats["total_tokens"] / requests if requests > 0 else 0
            stats["cache_hit_rate"] = (stats["cache_hits"] / requests * 100) if requests > 0 else 0
            
        result = list(model_stats.values())
        result.sort(key=lambda x: x["total_tokens"], reverse=True)
        
        self._log_event("get_model_usage_stats", self._get_entity_type_name(), 
                       workspace=str(workspace.value) if workspace else None,
                       since=since, result_count=len(result))
        return result
        
    async def get_workspace_rankings(
        self, 
        metric: str = "total_tokens",
        since: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get workspace rankings by usage metric."""
        await self._check_error_condition("get_workspace_rankings")
        self._increment_call_count("get_workspace_rankings")
        await self._apply_call_delay("get_workspace_rankings")
        
        records = self._get_all_entities(workspace="global")
        
        if since:
            records = [r for r in records if r.timestamp >= since]
            
        # Group by workspace
        workspace_stats = {}
        total_metric_value = 0
        
        for record in records:
            workspace_name = str(record.workspace.value)
            if workspace_name not in workspace_stats:
                workspace_stats[workspace_name] = {
                    "workspace": workspace_name,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "requests_count": 0
                }
                
            workspace_stats[workspace_name]["total_tokens"] += record.total_tokens.value
            workspace_stats[workspace_name]["total_cost"] += record.cost_estimate or 0.0
            workspace_stats[workspace_name]["requests_count"] += 1
            
        # Calculate total for percentages
        for stats in workspace_stats.values():
            total_metric_value += stats.get(metric, 0)
            
        # Add percentage and sort
        rankings = []
        for stats in workspace_stats.values():
            metric_value = stats.get(metric, 0)
            percentage = (metric_value / total_metric_value * 100) if total_metric_value > 0 else 0
            
            rankings.append({
                "workspace": stats["workspace"],
                "metric_value": metric_value,
                "percentage_of_total": percentage
            })
            
        rankings.sort(key=lambda x: x["metric_value"], reverse=True)
        result = rankings[:limit]
        
        self._log_event("get_workspace_rankings", self._get_entity_type_name__, 
                       metric=metric, since=since, limit=limit, result_count=len(result))
        return result
        
    async def get_cost_projection(
        self,
        workspace: WorkspaceName,
        projection_days: int = 30
    ) -> Dict[str, Any]:
        """Get cost projection based on recent usage."""
        await self._check_error_condition("get_cost_projection")
        self._increment_call_count("get_cost_projection")
        await self._apply_call_delay("get_cost_projection")
        
        # Get recent usage for trend analysis
        lookback_days = min(projection_days, 30)
        since = datetime.now() - timedelta(days=lookback_days)
        
        records = await self.find_by_workspace(workspace, since=since)
        
        if not records:
            projection = {
                "current_daily_average": 0.0,
                "projected_monthly_cost": 0.0,
                "confidence_level": 0.0,
                "trend": "stable"
            }
        else:
            # Calculate daily average cost
            total_cost = sum(r.cost_estimate or 0.0 for r in records)
            daily_average = total_cost / lookback_days
            
            # Project monthly cost
            projected_monthly = daily_average * 30
            
            # Mock trend analysis
            trend = "stable"
            if len(records) > 10:
                # Simple trend based on first half vs second half
                mid_point = len(records) // 2
                first_half_avg = sum(r.cost_estimate or 0.0 for r in records[:mid_point]) / mid_point
                second_half_avg = sum(r.cost_estimate or 0.0 for r in records[mid_point:]) / (len(records) - mid_point)
                
                if second_half_avg > first_half_avg * 1.1:
                    trend = "increasing"
                elif second_half_avg < first_half_avg * 0.9:
                    trend = "decreasing"
                    
            # Confidence based on data availability
            confidence = min(1.0, len(records) / (lookback_days * 2))
            
            projection = {
                "current_daily_average": daily_average,
                "projected_monthly_cost": projected_monthly,
                "confidence_level": confidence,
                "trend": trend
            }
            
        self._log_event("get_cost_projection", self._get_entity_type_name(), 
                       str(workspace.value), projection_days=projection_days, **projection)
        return projection
        
    async def get_anomaly_detection(
        self,
        workspace: Optional[WorkspaceName] = None,
        sensitivity: float = 2.0
    ) -> List[Dict[str, Any]]:
        """Detect usage anomalies (spikes or unusual patterns)."""
        await self._check_error_condition("get_anomaly_detection")
        self._increment_call_count("get_anomaly_detection")
        await self._apply_call_delay("get_anomaly_detection")
        
        # Mock anomaly detection - return configured anomalies or empty list
        anomalies = self._behavior.return_values.get("get_anomaly_detection", [
            {
                "timestamp": datetime.now() - timedelta(hours=2),
                "metric": "total_tokens",
                "value": 15000,
                "expected_range": "2000-5000",
                "severity": "high"
            },
            {
                "timestamp": datetime.now() - timedelta(hours=6),
                "metric": "requests_count",
                "value": 150,
                "expected_range": "20-50",
                "severity": "medium"
            }
        ])
        
        self._log_event("get_anomaly_detection", self._get_entity_type_name(), 
                       workspace=str(workspace.value) if workspace else None,
                       sensitivity=sensitivity, anomaly_count=len(anomalies))
        return anomalies
        
    async def cleanup_old_records(
        self,
        older_than: datetime,
        keep_summary: bool = True
    ) -> int:
        """Clean up old usage records."""
        await self._check_error_condition("cleanup_old_records")
        self._increment_call_count("cleanup_old_records")
        await self._apply_call_delay("cleanup_old_records")
        
        records = self._get_all_entities(workspace="global")
        old_records = [r for r in records if r.timestamp < older_than]
        
        # If keeping summary, we'd normally aggregate before deleting
        if keep_summary:
            # Mock: log that we're keeping summary data
            self._log_event("cleanup_old_records", "SummaryData", 
                           action="aggregated", record_count=len(old_records))
        
        deleted_count = 0
        for record in old_records:
            await self.delete(record)
            deleted_count += 1
            
        self._log_event("cleanup_old_records", self._get_entity_type_name(), 
                       deleted_count=deleted_count, older_than=older_than, keep_summary=keep_summary)
        return deleted_count
        
    async def export_billing_data(
        self,
        workspace: WorkspaceName,
        start_date: datetime,
        end_date: datetime,
        format: str = "csv"
    ) -> bytes:
        """Export billing data for a date range."""
        await self._check_error_condition("export_billing_data")
        self._increment_call_count("export_billing_data")
        await self._apply_call_delay("export_billing_data")
        
        records = await self.find_by_workspace(workspace, since=start_date, until=end_date)
        
        if format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            writer.writerow([
                "timestamp", "model", "prompt_tokens", "completion_tokens", 
                "total_tokens", "cost_estimate", "cache_hit", "pipeline_run_id"
            ])
            
            # Data rows
            for record in records:
                writer.writerow([
                    record.timestamp.isoformat(),
                    str(record.model_name.value),
                    record.prompt_tokens.value,
                    record.completion_tokens.value,
                    record.total_tokens.value,
                    record.cost_estimate or 0.0,
                    record.cache_hit,
                    str(record.pipeline_run_id) if record.pipeline_run_id else ""
                ])
                
            result = output.getvalue().encode('utf-8')
            
        elif format == "json":
            import json
            
            export_data = {
                "workspace": str(workspace.value),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "records": [
                    {
                        "timestamp": record.timestamp.isoformat(),
                        "model": str(record.model_name.value),
                        "prompt_tokens": record.prompt_tokens.value,
                        "completion_tokens": record.completion_tokens.value,
                        "total_tokens": record.total_tokens.value,
                        "cost_estimate": record.cost_estimate,
                        "cache_hit": record.cache_hit,
                        "pipeline_run_id": str(record.pipeline_run_id) if record.pipeline_run_id else None
                    }
                    for record in records
                ],
                "exported_at": datetime.now().isoformat()
            }
            
            result = json.dumps(export_data, indent=2).encode('utf-8')
            
        else:
            # Default to CSV for unknown formats
            result = b"Unsupported format"
            
        self._log_event("export_billing_data", self._get_entity_type_name(), 
                       str(workspace.value), start_date=start_date, end_date=end_date,
                       format=format, record_count=len(records), size_bytes=len(result))
        return result