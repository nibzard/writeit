"""LMDB implementation of PipelineRunRepository.

Provides persistent storage for pipeline runs using LMDB
with execution state management and performance tracking.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from ...domains.pipeline.repositories.pipeline_run_repository import PipelineRunRepository
from ...domains.pipeline.entities.pipeline_run import PipelineRun
from ...domains.pipeline.value_objects.pipeline_id import PipelineId
from ...domains.pipeline.value_objects.execution_status import ExecutionStatus
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError
from ..persistence.lmdb_storage import LMDBStorage
from ..base.exceptions import StorageError


class LMDBPipelineRunRepository(PipelineRunRepository):
    """LMDB-based implementation of PipelineRunRepository.
    
    Stores pipeline runs with execution state management,
    history tracking, and performance analytics.
    """
    
    def __init__(self, storage: LMDBStorage, workspace: Optional[WorkspaceName] = None):
        """Initialize repository.
        
        Args:
            storage: LMDB storage instance
            workspace: Current workspace (if None, uses global scope)
        """
        super().__init__(workspace)
        self.storage = storage
        self._db_name = "pipeline_runs"
    
    async def save(self, run: PipelineRun) -> None:
        """Save a pipeline run.
        
        Args:
            run: Pipeline run to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        try:
            key = self._make_key(run.id, run.workspace)
            
            await self.storage.store_entity(
                run,
                key,
                self._db_name
            )
            
        except StorageError as e:
            raise RepositoryError(f"Failed to save pipeline run {run.id}: {e}") from e
    
    async def find_by_id(self, run_id: UUID) -> Optional[PipelineRun]:
        """Find run by ID.
        
        Args:
            run_id: Run ID to search for
            
        Returns:
            Pipeline run if found, None otherwise
        """
        try:
            key = self._make_key(run_id, self.workspace)
            return await self.storage.load_entity(
                key,
                PipelineRun,
                self._db_name
            )
        except StorageError as e:
            raise RepositoryError(f"Failed to find pipeline run {run_id}: {e}") from e
    
    async def find_by_template_id(self, template_id: PipelineId) -> List[PipelineRun]:
        """Find all runs for a specific template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            List of runs for the template, ordered by start time desc
        """
        try:
            all_runs = await self._get_all_runs()
            
            # Filter by template ID
            template_runs = [
                run for run in all_runs
                if run.template_id == template_id
            ]
            
            # Sort by start time descending (most recent first)
            template_runs.sort(
                key=lambda r: r.started_at or datetime.min,
                reverse=True
            )
            
            return template_runs
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to find runs for template {template_id}: {e}"
            ) from e
    
    async def find_by_status(self, status: ExecutionStatus) -> List[PipelineRun]:
        """Find all runs with specific status.
        
        Args:
            status: Execution status to filter by
            
        Returns:
            List of runs with the status
        """
        try:
            all_runs = await self._get_all_runs()
            
            # Filter by status
            status_runs = [
                run for run in all_runs
                if run.status == status
            ]
            
            return status_runs
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find runs by status {status}: {e}") from e
    
    async def find_active_runs(self) -> List[PipelineRun]:
        """Find all currently active (running) pipeline runs.
        
        Returns:
            List of active runs
        """
        try:
            active_statuses = [
                ExecutionStatus.RUNNING,
                ExecutionStatus.PENDING,
                ExecutionStatus.PAUSED
            ]
            
            all_runs = await self._get_all_runs()
            
            active_runs = [
                run for run in all_runs
                if run.status in active_statuses
            ]
            
            return active_runs
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find active runs: {e}") from e
    
    async def find_recent_runs(self, limit: int = 50) -> List[PipelineRun]:
        """Find recent pipeline runs.
        
        Args:
            limit: Maximum number of runs to return
            
        Returns:
            List of recent runs, ordered by start time desc
        """
        try:
            all_runs = await self._get_all_runs()
            
            # Sort by start time descending
            recent_runs = sorted(
                all_runs,
                key=lambda r: r.started_at or datetime.min,
                reverse=True
            )
            
            return recent_runs[:limit]
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find recent runs: {e}") from e
    
    async def find_runs_in_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[PipelineRun]:
        """Find runs within date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of runs in the date range
        """
        try:
            all_runs = await self._get_all_runs()
            
            # Filter by date range
            date_runs = [
                run for run in all_runs
                if run.started_at and start_date <= run.started_at <= end_date
            ]
            
            return date_runs
            
        except StorageError as e:
            raise RepositoryError(
                f"Failed to find runs in date range {start_date} to {end_date}: {e}"
            ) from e
    
    async def get_execution_metrics(
        self,
        template_id: Optional[PipelineId] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get execution metrics for templates.
        
        Args:
            template_id: Specific template (None for all templates)
            days: Number of days to look back
            
        Returns:
            Dictionary with execution metrics
        """
        try:
            # Get runs from the last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_runs = await self.find_runs_in_date_range(
                cutoff_date,
                datetime.now()
            )
            
            # Filter by template if specified
            if template_id:
                recent_runs = [
                    run for run in recent_runs
                    if run.template_id == template_id
                ]
            
            # Calculate metrics
            total_runs = len(recent_runs)
            successful_runs = sum(
                1 for run in recent_runs
                if run.status == ExecutionStatus.COMPLETED
            )
            failed_runs = sum(
                1 for run in recent_runs
                if run.status == ExecutionStatus.FAILED
            )
            
            # Calculate average duration for completed runs
            completed_runs = [
                run for run in recent_runs
                if run.status == ExecutionStatus.COMPLETED and run.completed_at and run.started_at
            ]
            
            avg_duration = None
            if completed_runs:
                total_duration = sum(
                    (run.completed_at - run.started_at).total_seconds()
                    for run in completed_runs
                )
                avg_duration = total_duration / len(completed_runs)
            
            success_rate = (successful_runs / total_runs) if total_runs > 0 else 0
            
            return {
                'total_runs': total_runs,
                'successful_runs': successful_runs,
                'failed_runs': failed_runs,
                'success_rate': success_rate,
                'average_duration_seconds': avg_duration,
                'period_days': days,
                'template_id': str(template_id) if template_id else None
            }
            
        except StorageError as e:
            raise RepositoryError(f"Failed to get execution metrics: {e}") from e
    
    async def cleanup_old_runs(self, days: int = 90) -> int:
        """Clean up old completed runs.
        
        Args:
            days: Number of days to keep (older runs will be deleted)
            
        Returns:
            Number of runs deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            all_runs = await self._get_all_runs()
            
            # Find old completed runs
            old_runs = [
                run for run in all_runs
                if (run.completed_at and run.completed_at < cutoff_date and 
                    run.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED])
            ]
            
            # Delete old runs
            deleted_count = 0
            for run in old_runs:
                if await self.delete(run.id):
                    deleted_count += 1
            
            return deleted_count
            
        except StorageError as e:
            raise RepositoryError(f"Failed to cleanup old runs: {e}") from e
    
    async def find_all(self) -> List[PipelineRun]:
        """Find all runs in current workspace.
        
        Returns:
            List of all runs
        """
        return await self._get_all_runs()
    
    async def delete(self, run_id: UUID) -> bool:
        """Delete a pipeline run.
        
        Args:
            run_id: ID of run to delete
            
        Returns:
            True if run was deleted, False if not found
        """
        try:
            key = self._make_key(run_id, self.workspace)
            return await self.storage.delete_entity(key, self._db_name)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to delete run {run_id}: {e}") from e
    
    async def count(self) -> int:
        """Count runs in current workspace.
        
        Returns:
            Number of runs
        """
        try:
            if self.workspace:
                prefix = f"run:{self.workspace.value}:"
            else:
                prefix = "run:"
            
            return await self.storage.count_entities(prefix, self._db_name)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to count runs: {e}") from e
    
    def _make_key(self, run_id: UUID, workspace: Optional[WorkspaceName]) -> str:
        """Create storage key for run.
        
        Args:
            run_id: Run ID
            workspace: Workspace (None for global)
            
        Returns:
            Storage key
        """
        if workspace:
            return f"run:{workspace.value}:{run_id}"
        else:
            return f"run:global:{run_id}"
    
    async def _get_all_runs(self) -> List[PipelineRun]:
        """Get all runs in current workspace.
        
        Returns:
            List of all runs
        """
        if self.workspace:
            prefix = f"run:{self.workspace.value}:"
        else:
            prefix = "run:"
        
        return await self.storage.find_entities_by_prefix(
            prefix,
            PipelineRun,
            self._db_name
        )
