"""LMDB implementation of StepExecutionRepository.

Provides persistent storage for step executions using LMDB
with retry management and performance tracking.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from ...domains.pipeline.repositories.step_execution_repository import StepExecutionRepository
from ...domains.pipeline.entities.step_execution import StepExecution
from ...domains.pipeline.value_objects.step_id import StepId
from ...domains.pipeline.value_objects.execution_status import ExecutionStatus
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError
from ..persistence.lmdb_storage import LMDBStorage
from ..base.exceptions import StorageError


class LMDBStepExecutionRepository(StepExecutionRepository):
    """LMDB-based implementation of StepExecutionRepository.
    
    Stores step executions with retry management and performance tracking.
    """
    
    def __init__(self, storage: LMDBStorage, workspace: Optional[WorkspaceName] = None):
        """Initialize repository.
        
        Args:
            storage: LMDB storage instance
            workspace: Current workspace (if None, uses global scope)
        """
        super().__init__(workspace)
        self.storage = storage
        self._db_name = "step_executions"
    
    async def save(self, execution: StepExecution) -> None:
        """Save a step execution.
        
        Args:
            execution: Step execution to save
            
        Raises:
            RepositoryError: If save operation fails
        """
        try:
            key = self._make_key(execution.id, execution.workspace)
            
            await self.storage.store_entity(
                execution,
                key,
                self._db_name
            )
            
        except StorageError as e:
            raise RepositoryError(f"Failed to save step execution {execution.id}: {e}") from e
    
    async def find_by_id(self, execution_id: UUID) -> Optional[StepExecution]:
        """Find execution by ID.
        
        Args:
            execution_id: Execution ID to search for
            
        Returns:
            Step execution if found, None otherwise
        """
        try:
            key = self._make_key(execution_id, self.workspace)
            return await self.storage.load_entity(
                key,
                StepExecution,
                self._db_name
            )
        except StorageError as e:
            raise RepositoryError(f"Failed to find step execution {execution_id}: {e}") from e
    
    async def find_by_run_id(self, run_id: UUID) -> List[StepExecution]:
        """Find all executions for a pipeline run.
        
        Args:
            run_id: Pipeline run identifier
            
        Returns:
            List of step executions for the run, ordered by sequence
        """
        try:
            all_executions = await self._get_all_executions()
            
            # Filter by run ID
            run_executions = [
                execution for execution in all_executions
                if execution.run_id == run_id
            ]
            
            # Sort by sequence number (assuming steps have sequence)
            run_executions.sort(
                key=lambda e: e.step.sequence if hasattr(e.step, 'sequence') else 0
            )
            
            return run_executions
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find executions for run {run_id}: {e}") from e
    
    async def find_by_step_id(self, step_id: StepId) -> List[StepExecution]:
        """Find all executions for a specific step.
        
        Args:
            step_id: Step identifier
            
        Returns:
            List of executions for the step, ordered by start time desc
        """
        try:
            all_executions = await self._get_all_executions()
            
            # Filter by step ID
            step_executions = [
                execution for execution in all_executions
                if execution.step_id == step_id
            ]
            
            # Sort by start time descending
            step_executions.sort(
                key=lambda e: e.started_at or datetime.min,
                reverse=True
            )
            
            return step_executions
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find executions for step {step_id}: {e}") from e
    
    async def find_by_status(self, status: ExecutionStatus) -> List[StepExecution]:
        """Find all executions with specific status.
        
        Args:
            status: Execution status to filter by
            
        Returns:
            List of executions with the status
        """
        try:
            all_executions = await self._get_all_executions()
            
            # Filter by status
            status_executions = [
                execution for execution in all_executions
                if execution.status == status
            ]
            
            return status_executions
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find executions by status {status}: {e}") from e
    
    async def find_failed_executions(self, since_date: Optional[datetime] = None) -> List[StepExecution]:
        """Find failed step executions.
        
        Args:
            since_date: Only return failures since this date (None for all)
            
        Returns:
            List of failed executions
        """
        try:
            failed_executions = await self.find_by_status(ExecutionStatus.FAILED)
            
            if since_date:
                failed_executions = [
                    execution for execution in failed_executions
                    if execution.started_at and execution.started_at >= since_date
                ]
            
            return failed_executions
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find failed executions: {e}") from e
    
    async def find_with_retries(self) -> List[StepExecution]:
        """Find executions that have been retried.
        
        Returns:
            List of executions with retry attempts
        """
        try:
            all_executions = await self._get_all_executions()
            
            # Filter executions with retries
            retry_executions = [
                execution for execution in all_executions
                if execution.retry_count > 0
            ]
            
            return retry_executions
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find executions with retries: {e}") from e
    
    async def get_performance_metrics(
        self,
        step_id: Optional[StepId] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance metrics for step executions.
        
        Args:
            step_id: Specific step (None for all steps)
            days: Number of days to look back
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            # Get executions from the last N days
            cutoff_date = datetime.now() - timedelta(days=days)
            all_executions = await self._get_all_executions()
            
            recent_executions = [
                execution for execution in all_executions
                if execution.started_at and execution.started_at >= cutoff_date
            ]
            
            # Filter by step if specified
            if step_id:
                recent_executions = [
                    execution for execution in recent_executions
                    if execution.step_id == step_id
                ]
            
            # Calculate metrics
            total_executions = len(recent_executions)
            successful_executions = sum(
                1 for execution in recent_executions
                if execution.status == ExecutionStatus.COMPLETED
            )
            failed_executions = sum(
                1 for execution in recent_executions
                if execution.status == ExecutionStatus.FAILED
            )
            
            # Calculate average duration for completed executions
            completed_executions = [
                execution for execution in recent_executions
                if (execution.status == ExecutionStatus.COMPLETED and 
                   execution.completed_at and execution.started_at)
            ]
            
            avg_duration = None
            min_duration = None
            max_duration = None
            
            if completed_executions:
                durations = [
                    (execution.completed_at - execution.started_at).total_seconds()
                    for execution in completed_executions
                ]
                avg_duration = sum(durations) / len(durations)
                min_duration = min(durations)
                max_duration = max(durations)
            
            # Calculate retry metrics
            total_retries = sum(execution.retry_count for execution in recent_executions)
            executions_with_retries = sum(
                1 for execution in recent_executions
                if execution.retry_count > 0
            )
            
            success_rate = (successful_executions / total_executions) if total_executions > 0 else 0
            
            return {
                'total_executions': total_executions,
                'successful_executions': successful_executions,
                'failed_executions': failed_executions,
                'success_rate': success_rate,
                'average_duration_seconds': avg_duration,
                'min_duration_seconds': min_duration,
                'max_duration_seconds': max_duration,
                'total_retries': total_retries,
                'executions_with_retries': executions_with_retries,
                'period_days': days,
                'step_id': str(step_id) if step_id else None
            }
            
        except StorageError as e:
            raise RepositoryError(f"Failed to get performance metrics: {e}") from e
    
    async def find_slowest_executions(
        self,
        limit: int = 10,
        days: int = 30
    ) -> List[StepExecution]:
        """Find slowest step executions.
        
        Args:
            limit: Maximum number of executions to return
            days: Number of days to look back
            
        Returns:
            List of slowest executions, ordered by duration desc
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            all_executions = await self._get_all_executions()
            
            # Filter completed executions from recent period
            completed_executions = [
                execution for execution in all_executions
                if (execution.status == ExecutionStatus.COMPLETED and
                   execution.started_at and execution.started_at >= cutoff_date and
                   execution.completed_at)
            ]
            
            # Sort by duration descending
            completed_executions.sort(
                key=lambda e: (e.completed_at - e.started_at).total_seconds(),
                reverse=True
            )
            
            return completed_executions[:limit]
            
        except StorageError as e:
            raise RepositoryError(f"Failed to find slowest executions: {e}") from e
    
    async def cleanup_old_executions(self, days: int = 90) -> int:
        """Clean up old completed executions.
        
        Args:
            days: Number of days to keep (older executions will be deleted)
            
        Returns:
            Number of executions deleted
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            all_executions = await self._get_all_executions()
            
            # Find old completed executions
            old_executions = [
                execution for execution in all_executions
                if (execution.completed_at and execution.completed_at < cutoff_date and
                   execution.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED])
            ]
            
            # Delete old executions
            deleted_count = 0
            for execution in old_executions:
                if await self.delete(execution.id):
                    deleted_count += 1
            
            return deleted_count
            
        except StorageError as e:
            raise RepositoryError(f"Failed to cleanup old executions: {e}") from e
    
    async def find_all(self) -> List[StepExecution]:
        """Find all executions in current workspace.
        
        Returns:
            List of all executions
        """
        return await self._get_all_executions()
    
    async def delete(self, execution_id: UUID) -> bool:
        """Delete a step execution.
        
        Args:
            execution_id: ID of execution to delete
            
        Returns:
            True if execution was deleted, False if not found
        """
        try:
            key = self._make_key(execution_id, self.workspace)
            return await self.storage.delete_entity(key, self._db_name)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to delete execution {execution_id}: {e}") from e
    
    async def count(self) -> int:
        """Count executions in current workspace.
        
        Returns:
            Number of executions
        """
        try:
            if self.workspace:
                prefix = f"step:{self.workspace.value}:"
            else:
                prefix = "step:"
            
            return await self.storage.count_entities(prefix, self._db_name)
            
        except StorageError as e:
            raise RepositoryError(f"Failed to count executions: {e}") from e
    
    def _make_key(self, execution_id: UUID, workspace: Optional[WorkspaceName]) -> str:
        """Create storage key for execution.
        
        Args:
            execution_id: Execution ID
            workspace: Workspace (None for global)
            
        Returns:
            Storage key
        """
        if workspace:
            return f"step:{workspace.value}:{execution_id}"
        else:
            return f"step:global:{execution_id}"
    
    async def _get_all_executions(self) -> List[StepExecution]:
        """Get all executions in current workspace.
        
        Returns:
            List of all executions
        """
        if self.workspace:
            prefix = f"step:{self.workspace.value}:"
        else:
            prefix = "step:"
        
        return await self.storage.find_entities_by_prefix(
            prefix,
            StepExecution,
            self._db_name
        )
