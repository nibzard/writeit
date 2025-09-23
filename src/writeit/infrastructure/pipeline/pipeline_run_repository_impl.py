"""LMDB implementation of PipelineRunRepository.

Provides concrete LMDB-backed storage for pipeline runs with
workspace isolation, status tracking, and execution monitoring.
"""

from typing import List, Optional, Any
from datetime import datetime, timedelta

from ...domains.pipeline.repositories.pipeline_run_repository import (
    PipelineRunRepository,
    ByPipelineSpecification,
    ByStatusSpecification,
    ByWorkspaceSpecification,
    ActiveRunsSpecification,
    CompletedRunsSpecification,
    RecentRunsSpecification
)
from ...domains.pipeline.entities.pipeline_run import PipelineRun
from ...domains.pipeline.value_objects.pipeline_id import PipelineId
from ...domains.pipeline.value_objects.execution_status import ExecutionStatus, PipelineExecutionStatus
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError, EntityNotFoundError
from ..base.repository_base import LMDBRepositoryBase
from ..base.storage_manager import LMDBStorageManager
from ..base.serialization import DomainEntitySerializer


class LMDBPipelineRunRepository(LMDBRepositoryBase[PipelineRun], PipelineRunRepository):
    """LMDB implementation of PipelineRunRepository.
    
    Stores pipeline runs with workspace isolation and provides
    advanced querying capabilities for execution monitoring.
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
            entity_type=PipelineRun,
            db_name="pipeline_runs",
            db_key="runs"
        )
    
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with pipeline run-specific types.
        
        Args:
            serializer: Serializer to configure
        """
        # Register value objects
        serializer.register_value_object(PipelineId)
        serializer.register_value_object(ExecutionStatus)
        serializer.register_value_object(WorkspaceName)
        
        # Register entity types
        serializer.register_type("PipelineRun", PipelineRun)
        
        # Register enums
        serializer.register_type("PipelineExecutionStatus", PipelineExecutionStatus)
    
    def _get_entity_id(self, entity: PipelineRun) -> Any:
        """Extract entity ID for storage key.
        
        Args:
            entity: Pipeline run entity
            
        Returns:
            Entity identifier
        """
        return entity.id
    
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID.
        
        Args:
            entity_id: Entity identifier (run ID string)
            
        Returns:
            Storage key string
        """
        workspace_prefix = self._get_workspace_prefix()
        return f"{workspace_prefix}run:{str(entity_id)}"
    
    async def find_by_pipeline(self, pipeline_id: PipelineId) -> List[PipelineRun]:
        """Find all runs for a specific pipeline.
        
        Args:
            pipeline_id: Pipeline identifier
            
        Returns:
            List of pipeline runs
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByWorkspaceSpecification(self.workspace_name) & ByPipelineSpecification(pipeline_id)
        return await self.find_by_specification(spec)
    
    async def find_by_status(self, status: PipelineExecutionStatus) -> List[PipelineRun]:
        """Find runs by execution status.
        
        Args:
            status: Execution status to filter by
            
        Returns:
            List of matching pipeline runs
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByWorkspaceSpecification(self.workspace_name) & ByStatusSpecification(status)
        return await self.find_by_specification(spec)
    
    async def find_active_runs(self) -> List[PipelineRun]:
        """Find all currently active (running) pipeline runs.
        
        Returns:
            List of active pipeline runs
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByWorkspaceSpecification(self.workspace_name) & ActiveRunsSpecification()
        return await self.find_by_specification(spec)
    
    async def find_completed_runs(self, limit: Optional[int] = None) -> List[PipelineRun]:
        """Find completed pipeline runs.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of completed pipeline runs, ordered by completion time
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByWorkspaceSpecification(self.workspace_name) & CompletedRunsSpecification()
        runs = await self.find_by_specification(spec)
        
        # Sort by completion time (newest first)
        runs.sort(key=lambda r: r.completed_at or datetime.min, reverse=True)
        
        if limit:
            runs = runs[:limit]
            
        return runs
    
    async def find_failed_runs(self, limit: Optional[int] = None) -> List[PipelineRun]:
        """Find failed pipeline runs.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of failed pipeline runs, ordered by failure time
            
        Raises:
            RepositoryError: If query operation fails
        """
        failed_runs = await self.find_by_status(PipelineExecutionStatus.FAILED)
        
        # Sort by completion time (newest first)
        failed_runs.sort(key=lambda r: r.completed_at or datetime.min, reverse=True)
        
        if limit:
            failed_runs = failed_runs[:limit]
            
        return failed_runs
    
    async def find_recent_runs(self, hours: int = 24) -> List[PipelineRun]:
        """Find runs created within the specified time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of recent pipeline runs
            
        Raises:
            RepositoryError: If query operation fails
        """
        since = datetime.now() - timedelta(hours=hours)
        spec = ByWorkspaceSpecification(self.workspace_name) & RecentRunsSpecification(since)
        return await self.find_by_specification(spec)
    
    async def find_by_workspace_name(self, workspace: str) -> List[PipelineRun]:
        """Find runs by workspace name.
        
        Args:
            workspace: Workspace name string
            
        Returns:
            List of pipeline runs in the workspace
            
        Raises:
            RepositoryError: If query operation fails
        """
        all_runs = await self.find_all()
        return [run for run in all_runs if run.workspace_name == workspace]
    
    async def find_runs_with_errors(self) -> List[PipelineRun]:
        """Find runs that have error information.
        
        Returns:
            List of pipeline runs with errors
            
        Raises:
            RepositoryError: If query operation fails
        """
        all_runs = await self.find_by_workspace()
        return [run for run in all_runs if run.error]
    
    async def find_longest_running(self, limit: int = 10) -> List[PipelineRun]:
        """Find the longest running pipeline executions.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of runs ordered by execution time (longest first)
            
        Raises:
            RepositoryError: If query operation fails
        """
        completed_runs = await self.find_completed_runs()
        
        # Filter runs with duration and sort by duration
        runs_with_duration = [run for run in completed_runs if run.duration is not None]
        runs_with_duration.sort(key=lambda r: r.duration, reverse=True)
        
        return runs_with_duration[:limit]
    
    async def count_by_status(self, status: PipelineExecutionStatus) -> int:
        """Count runs by status.
        
        Args:
            status: Execution status to count
            
        Returns:
            Number of runs with the given status
            
        Raises:
            RepositoryError: If count operation fails
        """
        runs = await self.find_by_status(status)
        return len(runs)
    
    async def count_active_runs(self) -> int:
        """Count currently active runs.
        
        Returns:
            Number of active runs
            
        Raises:
            RepositoryError: If count operation fails
        """
        active_runs = await self.find_active_runs()
        return len(active_runs)
    
    async def get_execution_statistics(self) -> dict:
        """Get execution statistics for current workspace.
        
        Returns:
            Dictionary with execution statistics
            
        Raises:
            RepositoryError: If statistics calculation fails
        """
        all_runs = await self.find_by_workspace()
        
        if not all_runs:
            return {
                "total_runs": 0,
                "success_rate": 0.0,
                "avg_duration": 0.0,
                "total_tokens": 0,
                "status_counts": {}
            }
        
        # Calculate statistics
        total_runs = len(all_runs)
        successful_runs = [r for r in all_runs if r.is_completed]
        failed_runs = [r for r in all_runs if r.is_failed]
        
        success_rate = len(successful_runs) / total_runs if total_runs > 0 else 0.0
        
        # Calculate average duration for completed runs
        completed_with_duration = [r for r in all_runs if r.duration is not None]
        avg_duration = (
            sum(r.duration for r in completed_with_duration) / len(completed_with_duration)
            if completed_with_duration else 0.0
        )
        
        # Calculate total tokens
        total_tokens = sum(r.get_total_tokens() for r in all_runs)
        
        # Count by status
        status_counts = {}
        for run in all_runs:
            status = run.status.status.value if hasattr(run.status.status, 'value') else str(run.status.status)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_runs": total_runs,
            "success_rate": success_rate,
            "avg_duration": avg_duration,
            "total_tokens": total_tokens,
            "status_counts": status_counts,
            "successful_runs": len(successful_runs),
            "failed_runs": len(failed_runs)
        }
    
    async def cleanup_old_runs(self, older_than_days: int = 30) -> int:
        """Clean up old completed runs.
        
        Args:
            older_than_days: Delete runs older than this many days
            
        Returns:
            Number of runs deleted
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        all_runs = await self.find_by_workspace()
        
        old_runs = [
            run for run in all_runs
            if (run.completed_at and run.completed_at < cutoff_date) or
               (not run.completed_at and run.created_at < cutoff_date)
        ]
        
        deleted_count = 0
        for run in old_runs:
            if await self.delete_by_id(run.id):
                deleted_count += 1
        
        return deleted_count
    
    async def find_runs_by_pipeline_name(self, pipeline_name: str) -> List[PipelineRun]:
        """Find runs by pipeline name (requires metadata lookup).
        
        Note: This is a convenience method that requires additional
        pipeline template lookups for name resolution.
        
        Args:
            pipeline_name: Pipeline template name
            
        Returns:
            List of matching pipeline runs
        """
        # This would typically require a join with pipeline templates
        # For now, return empty list - implement when needed
        return []
    
    async def get_run_timeline(self, run_id: str) -> Optional[dict]:
        """Get execution timeline for a specific run.
        
        Args:
            run_id: Pipeline run identifier
            
        Returns:
            Timeline dictionary with key events
            
        Raises:
            RepositoryError: If query operation fails
        """
        run = await self.find_by_id(run_id)
        if not run:
            return None
        
        timeline = []
        
        # Add creation event
        timeline.append({
            "event": "created",
            "timestamp": run.created_at,
            "status": "pending"
        })
        
        # Add start event
        if run.started_at:
            timeline.append({
                "event": "started",
                "timestamp": run.started_at,
                "status": "running"
            })
        
        # Add completion event
        if run.completed_at:
            if run.is_completed:
                event = "completed"
            elif run.is_failed:
                event = "failed"
            elif run.is_cancelled:
                event = "cancelled"
            else:
                event = "finished"
                
            timeline.append({
                "event": event,
                "timestamp": run.completed_at,
                "status": run.status.status.value if hasattr(run.status.status, 'value') else str(run.status.status),
                "error": run.error if run.error else None
            })
        
        return {
            "run_id": run_id,
            "timeline": timeline,
            "duration": run.duration,
            "total_tokens": run.get_total_tokens()
        }