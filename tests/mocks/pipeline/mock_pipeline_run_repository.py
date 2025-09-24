"""Mock implementation of PipelineRunRepository for testing."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from writeit.domains.pipeline.repositories.pipeline_run_repository import PipelineRunRepository
from writeit.domains.pipeline.entities.pipeline_run import PipelineRun
from writeit.domains.pipeline.value_objects.pipeline_id import PipelineId
from writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError


class MockPipelineRunRepository(BaseMockRepository[PipelineRun], PipelineRunRepository):
    """Mock implementation of PipelineRunRepository.
    
    Provides in-memory storage for pipeline runs with execution state tracking
    and analytics support.
    """
    
    def __init__(self, workspace_name: WorkspaceName):
        super().__init__(str(workspace_name.value))
        self._workspace_name_obj = workspace_name
        
    def _get_entity_id(self, entity: PipelineRun) -> Any:
        """Extract entity ID from pipeline run."""
        return str(entity.id)
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "PipelineRun"
        
    # Repository interface implementation
    
    async def save(self, entity: PipelineRun) -> None:
        """Save or update a pipeline run."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id)
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: UUID) -> Optional[PipelineRun]:
        """Find run by ID."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        run = self._get_entity(str(entity_id))
        self._log_event("find_by_id", self._get_entity_type_name(), str(entity_id), found=run is not None)
        return run
        
    async def find_all(self) -> List[PipelineRun]:
        """Find all runs in current workspace."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        runs = self._get_all_entities()
        self._log_event("find_all", self._get_entity_type_name(), count=len(runs))
        return runs
        
    async def find_by_specification(self, spec: Specification[PipelineRun]) -> List[PipelineRun]:
        """Find runs matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        runs = self._find_entities_by_specification(spec)
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(runs))
        return runs
        
    async def exists(self, entity_id: UUID) -> bool:
        """Check if run exists."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        exists = self._entity_exists(str(entity_id))
        self._log_event("exists", self._get_entity_type_name(), str(entity_id), exists=exists)
        return exists
        
    async def delete(self, entity: PipelineRun) -> None:
        """Delete a run."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: UUID) -> bool:
        """Delete run by ID."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(str(entity_id))
        self._log_event("delete_by_id", self._get_entity_type_name(), str(entity_id), deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total runs."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        total = self._count_entities()
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    async def _find_by_workspace_impl(self, workspace: WorkspaceName) -> List[PipelineRun]:
        """Implementation-specific workspace query."""
        return self._get_all_entities(str(workspace.value))
        
    # PipelineRunRepository-specific methods
    
    async def find_by_template_id(self, template_id: PipelineId) -> List[PipelineRun]:
        """Find all runs for a specific template."""
        await self._check_error_condition("find_by_template_id")
        self._increment_call_count("find_by_template_id")
        await self._apply_call_delay("find_by_template_id")
        
        runs = self._get_all_entities()
        matching_runs = [r for r in runs if r.template_id == template_id]
        
        # Sort by start time desc
        matching_runs.sort(key=lambda r: r.started_at or datetime.min, reverse=True)
        
        self._log_event("find_by_template_id", self._get_entity_type_name(), 
                       count=len(matching_runs), template_id=str(template_id.value))
        return matching_runs
        
    async def find_by_status(self, status: ExecutionStatus) -> List[PipelineRun]:
        """Find all runs with specific status."""
        await self._check_error_condition("find_by_status")
        self._increment_call_count("find_by_status")
        await self._apply_call_delay("find_by_status")
        
        runs = self._get_all_entities()
        matching_runs = [r for r in runs if r.status == status]
        
        self._log_event("find_by_status", self._get_entity_type_name(), 
                       count=len(matching_runs), status=str(status))
        return matching_runs
        
    async def find_active_runs(self) -> List[PipelineRun]:
        """Find all currently active (running) pipeline runs."""
        await self._check_error_condition("find_active_runs")
        self._increment_call_count("find_active_runs")
        await self._apply_call_delay("find_active_runs")
        
        runs = self._get_all_entities()
        active_runs = [r for r in runs if r.status in [ExecutionStatus.RUNNING, ExecutionStatus.PENDING]]
        
        self._log_event("find_active_runs", self._get_entity_type_name(), count=len(active_runs))
        return active_runs
        
    async def find_completed_runs(
        self, 
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[PipelineRun]:
        """Find completed runs with optional filtering."""
        await self._check_error_condition("find_completed_runs")
        self._increment_call_count("find_completed_runs")
        await self._apply_call_delay("find_completed_runs")
        
        runs = self._get_all_entities()
        completed_runs = [r for r in runs if r.status == ExecutionStatus.COMPLETED]
        
        if since:
            completed_runs = [r for r in completed_runs 
                            if r.completed_at and r.completed_at >= since]
            
        # Sort by completion time desc
        completed_runs.sort(key=lambda r: r.completed_at or datetime.min, reverse=True)
        
        if limit:
            completed_runs = completed_runs[:limit]
            
        self._log_event("find_completed_runs", self._get_entity_type_name(), 
                       count=len(completed_runs), since=since, limit=limit)
        return completed_runs
        
    async def find_failed_runs(
        self, 
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[PipelineRun]:
        """Find failed runs with optional filtering."""
        await self._check_error_condition("find_failed_runs")
        self._increment_call_count("find_failed_runs")
        await self._apply_call_delay("find_failed_runs")
        
        runs = self._get_all_entities()
        failed_runs = [r for r in runs if r.status == ExecutionStatus.FAILED]
        
        if since:
            failed_runs = [r for r in failed_runs 
                         if r.failed_at and r.failed_at >= since]
            
        # Sort by failure time desc
        failed_runs.sort(key=lambda r: r.failed_at or datetime.min, reverse=True)
        
        if limit:
            failed_runs = failed_runs[:limit]
            
        self._log_event("find_failed_runs", self._get_entity_type_name(), 
                       count=len(failed_runs), since=since, limit=limit)
        return failed_runs
        
    async def find_runs_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[PipelineRun]:
        """Find runs within a date range."""
        await self._check_error_condition("find_runs_by_date_range")
        self._increment_call_count("find_runs_by_date_range")
        await self._apply_call_delay("find_runs_by_date_range")
        
        runs = self._get_all_entities()
        matching_runs = [r for r in runs 
                        if r.started_at and start_date <= r.started_at <= end_date]
        
        self._log_event("find_runs_by_date_range", self._get_entity_type_name(), 
                       count=len(matching_runs), start_date=start_date, end_date=end_date)
        return matching_runs
        
    async def get_execution_stats(
        self, 
        template_id: Optional[PipelineId] = None
    ) -> Dict[str, Any]:
        """Get execution statistics."""
        await self._check_error_condition("get_execution_stats")
        self._increment_call_count("get_execution_stats")
        await self._apply_call_delay("get_execution_stats")
        
        runs = self._get_all_entities()
        if template_id:
            runs = [r for r in runs if r.template_id == template_id]
            
        total_runs = len(runs)
        successful_runs = len([r for r in runs if r.status == ExecutionStatus.COMPLETED])
        failed_runs = len([r for r in runs if r.status == ExecutionStatus.FAILED])
        
        # Calculate average duration for completed runs
        completed_runs = [r for r in runs if r.status == ExecutionStatus.COMPLETED and r.duration]
        avg_duration = sum(r.duration.total_seconds() for r in completed_runs) / len(completed_runs) if completed_runs else 0
        
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        
        stats = {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "average_duration": avg_duration,
            "success_rate": success_rate
        }
        
        self._log_event("get_execution_stats", self._get_entity_type_name(), 
                       template_id=str(template_id.value) if template_id else None, **stats)
        return stats
        
    async def get_recent_runs(
        self, 
        limit: int = 10, 
        workspace: Optional[WorkspaceName] = None
    ) -> List[PipelineRun]:
        """Get most recent runs."""
        await self._check_error_condition("get_recent_runs")
        self._increment_call_count("get_recent_runs")
        await self._apply_call_delay("get_recent_runs")
        
        target_workspace = workspace or self._workspace_name_obj
        runs = self._get_all_entities(str(target_workspace.value))
        
        # Sort by start time desc
        runs.sort(key=lambda r: r.started_at or datetime.min, reverse=True)
        recent_runs = runs[:limit]
        
        self._log_event("get_recent_runs", self._get_entity_type_name(), 
                       count=len(recent_runs), limit=limit, 
                       workspace=str(target_workspace.value))
        return recent_runs
        
    async def cleanup_old_runs(
        self, 
        older_than: datetime, 
        keep_count: int = 100
    ) -> int:
        """Clean up old pipeline runs."""
        await self._check_error_condition("cleanup_old_runs")
        self._increment_call_count("cleanup_old_runs")
        await self._apply_call_delay("cleanup_old_runs")
        
        runs = self._get_all_entities()
        
        # Group by template
        template_runs: Dict[str, List[PipelineRun]] = {}
        for run in runs:
            template_id = str(run.template_id.value)
            if template_id not in template_runs:
                template_runs[template_id] = []
            template_runs[template_id].append(run)
            
        deleted_count = 0
        
        for template_id, template_run_list in template_runs.items():
            # Sort by start time desc
            template_run_list.sort(key=lambda r: r.started_at or datetime.min, reverse=True)
            
            # Keep the most recent keep_count runs
            runs_to_keep = template_run_list[:keep_count]
            runs_to_check = template_run_list[keep_count:]
            
            # Delete old runs beyond keep_count
            for run in runs_to_check:
                if run.started_at and run.started_at < older_than:
                    self._delete_entity(self._get_entity_id(run))
                    deleted_count += 1
                    
        self._log_event("cleanup_old_runs", self._get_entity_type_name(), 
                       deleted_count=deleted_count, older_than=older_than, keep_count=keep_count)
        return deleted_count
        
    async def update_run_status(
        self, 
        run_id: UUID, 
        status: ExecutionStatus, 
        error_message: Optional[str] = None
    ) -> None:
        """Update run status and optional error message."""
        await self._check_error_condition("update_run_status")
        self._increment_call_count("update_run_status")
        await self._apply_call_delay("update_run_status")
        
        run = self._get_entity(str(run_id))
        if not run:
            raise MockEntityNotFoundError(self._get_entity_type_name(), str(run_id))
            
        # Create updated run with new status (immutable update pattern)
        updated_run = run.with_status(status, error_message)
        self._store_entity(updated_run, str(run_id))
        
        self._log_event("update_run_status", self._get_entity_type_name(), 
                       str(run_id), status=str(status), error_message=error_message)