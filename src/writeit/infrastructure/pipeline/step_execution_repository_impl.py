"""LMDB implementation of StepExecutionRepository.

Provides concrete LMDB-backed storage for step executions with
performance tracking, retry management, and analytics.
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import statistics

from ...domains.pipeline.repositories.step_execution_repository import (
    StepExecutionRepository,
    StepExecution,
    ByRunIdSpecification,
    ByStepIdSpecification,
    FailedExecutionsSpecification,
    RetryExecutionsSpecification,
    SuccessfulExecutionsSpecification
)
from ...domains.pipeline.value_objects.step_id import StepId
from ...domains.pipeline.value_objects.execution_status import ExecutionStatus
from ...domains.workspace.value_objects.workspace_name import WorkspaceName
from ...shared.repository import RepositoryError, EntityNotFoundError
from ..base.repository_base import LMDBRepositoryBase
from ..base.storage_manager import LMDBStorageManager
from ..base.serialization import DomainEntitySerializer


class LMDBStepExecutionRepository(LMDBRepositoryBase[StepExecution], StepExecutionRepository):
    """LMDB implementation of StepExecutionRepository.
    
    Stores step executions with performance tracking and provides
    analytics capabilities for pipeline optimization.
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
            entity_type=StepExecution,
            db_name="step_executions",
            db_key="executions"
        )
    
    def _setup_serializer(self, serializer: DomainEntitySerializer) -> None:
        """Setup serializer with step execution-specific types.
        
        Args:
            serializer: Serializer to configure
        """
        # Register value objects
        serializer.register_value_object(StepId)
        serializer.register_value_object(ExecutionStatus)
        serializer.register_value_object(WorkspaceName)
        
        # Register entity types
        serializer.register_type("StepExecution", StepExecution)
    
    def _get_entity_id(self, entity: StepExecution) -> Any:
        """Extract entity ID for storage key.
        
        Args:
            entity: Step execution entity
            
        Returns:
            Entity identifier
        """
        return entity.execution_id
    
    def _make_storage_key(self, entity_id: Any) -> str:
        """Create storage key from entity ID.
        
        Args:
            entity_id: Entity identifier (execution UUID)
            
        Returns:
            Storage key string
        """
        workspace_prefix = self._get_workspace_prefix()
        return f"{workspace_prefix}execution:{str(entity_id)}"
    
    async def find_by_run_id(self, run_id: uuid.UUID) -> List[StepExecution]:
        """Find all step executions for a pipeline run.
        
        Args:
            run_id: Pipeline run identifier
            
        Returns:
            List of step executions, ordered by started_at
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByRunIdSpecification(run_id)
        executions = await self.find_by_specification(spec)
        
        # Sort by started_at time
        executions.sort(key=lambda e: e.started_at)
        return executions
    
    async def find_by_step_id(
        self, 
        run_id: uuid.UUID, 
        step_id: StepId
    ) -> Optional[StepExecution]:
        """Find specific step execution within a run.
        
        Args:
            run_id: Pipeline run identifier
            step_id: Step identifier
            
        Returns:
            Step execution if found, None otherwise
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = ByRunIdSpecification(run_id) & ByStepIdSpecification(step_id)
        executions = await self.find_by_specification(spec)
        return executions[0] if executions else None
    
    async def find_failed_executions(
        self, 
        since: Optional[datetime] = None
    ) -> List[StepExecution]:
        """Find failed step executions.
        
        Args:
            since: Only include failures after this time
            
        Returns:
            List of failed executions
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = FailedExecutionsSpecification()
        failed_executions = await self.find_by_specification(spec)
        
        if since:
            failed_executions = [
                e for e in failed_executions 
                if e.started_at >= since
            ]
        
        # Sort by failure time (newest first)
        failed_executions.sort(key=lambda e: e.completed_at or e.started_at, reverse=True)
        return failed_executions
    
    async def find_retry_executions(
        self, 
        min_retries: int = 1
    ) -> List[StepExecution]:
        """Find step executions that required retries.
        
        Args:
            min_retries: Minimum number of retries
            
        Returns:
            List of executions with retries
            
        Raises:
            RepositoryError: If query operation fails
        """
        spec = RetryExecutionsSpecification(min_retries)
        return await self.find_by_specification(spec)
    
    async def get_performance_stats(
        self, 
        step_id: Optional[StepId] = None,
        since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get step execution performance statistics.
        
        Args:
            step_id: Optional step to get stats for
            since: Only include executions after this time
            
        Returns:
            Dictionary with performance statistics
            
        Raises:
            RepositoryError: If stats calculation fails
        """
        # Get relevant executions
        if step_id:
            spec = ByStepIdSpecification(step_id)
            executions = await self.find_by_specification(spec)
        else:
            executions = await self.find_by_workspace()
        
        # Filter by time if specified
        if since:
            executions = [e for e in executions if e.started_at >= since]
        
        if not executions:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "average_duration_ms": 0,
                "median_duration_ms": 0,
                "success_rate": 0.0,
                "retry_rate": 0.0,
                "total_tokens": 0
            }
        
        # Calculate statistics
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.is_successful])
        failed_executions = len([e for e in executions if not e.is_successful])
        retry_executions = len([e for e in executions if e.retry_count > 0])
        
        # Duration statistics
        durations = [e.execution_time_ms for e in executions if e.execution_time_ms is not None]
        avg_duration = statistics.mean(durations) if durations else 0
        median_duration = statistics.median(durations) if durations else 0
        
        # Token usage
        total_tokens = sum(
            sum(e.token_usage.values()) for e in executions
        )
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "average_duration_ms": avg_duration,
            "median_duration_ms": median_duration,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0.0,
            "retry_rate": retry_executions / total_executions if total_executions > 0 else 0.0,
            "total_tokens": total_tokens
        }
    
    async def get_slowest_steps(
        self, 
        limit: int = 10,
        since: Optional[datetime] = None
    ) -> List[StepExecution]:
        """Get slowest step executions.
        
        Args:
            limit: Maximum number of results
            since: Only include executions after this time
            
        Returns:
            List of slowest executions, ordered by duration desc
            
        Raises:
            RepositoryError: If query operation fails
        """
        executions = await self.find_by_workspace()
        
        # Filter by time if specified
        if since:
            executions = [e for e in executions if e.started_at >= since]
        
        # Filter executions with duration data and sort by duration
        executions_with_duration = [
            e for e in executions if e.execution_time_ms is not None
        ]
        executions_with_duration.sort(key=lambda e: e.execution_time_ms, reverse=True)
        
        return executions_with_duration[:limit]
    
    async def get_most_failed_steps(
        self, 
        limit: int = 10,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get steps with highest failure rates.
        
        Args:
            limit: Maximum number of results
            since: Only include executions after this time
            
        Returns:
            List of dictionaries with step failure statistics
            
        Raises:
            RepositoryError: If query operation fails
        """
        executions = await self.find_by_workspace()
        
        # Filter by time if specified
        if since:
            executions = [e for e in executions if e.started_at >= since]
        
        # Group by step ID
        step_stats = {}
        for execution in executions:
            step_key = str(execution.step_id)
            if step_key not in step_stats:
                step_stats[step_key] = {
                    "step_id": execution.step_id,
                    "total_executions": 0,
                    "failed_executions": 0,
                    "error_messages": []
                }
            
            step_stats[step_key]["total_executions"] += 1
            if not execution.is_successful:
                step_stats[step_key]["failed_executions"] += 1
                if execution.error_message:
                    step_stats[step_key]["error_messages"].append(execution.error_message)
        
        # Calculate failure rates and common errors
        result = []
        for stats in step_stats.values():
            total = stats["total_executions"]
            failed = stats["failed_executions"]
            failure_rate = failed / total if total > 0 else 0.0
            
            # Find most common errors
            error_counts = {}
            for error in stats["error_messages"]:
                error_counts[error] = error_counts.get(error, 0) + 1
            
            common_errors = sorted(
                error_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]  # Top 5 errors
            
            result.append({
                "step_id": stats["step_id"],
                "total_executions": total,
                "failed_executions": failed,
                "failure_rate": failure_rate,
                "common_errors": [{"error": error, "count": count} for error, count in common_errors]
            })
        
        # Sort by failure rate and return top results
        result.sort(key=lambda x: x["failure_rate"], reverse=True)
        return result[:limit]
    
    async def record_execution_start(
        self, 
        run_id: uuid.UUID, 
        step_id: StepId
    ) -> uuid.UUID:
        """Record the start of a step execution.
        
        Args:
            run_id: Pipeline run identifier
            step_id: Step identifier
            
        Returns:
            Execution ID for tracking
            
        Raises:
            RepositoryError: If recording fails
        """
        execution_id = uuid.uuid4()
        
        execution = StepExecution(
            execution_id=execution_id,
            run_id=run_id,
            step_id=step_id,
            status=ExecutionStatus.created(),  # Assuming this exists
            started_at=datetime.now()
        )
        
        await self.save(execution)
        return execution_id
    
    async def record_execution_completion(
        self,
        execution_id: uuid.UUID,
        status: ExecutionStatus,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        token_usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record the completion of a step execution.
        
        Args:
            execution_id: Execution identifier
            status: Final execution status
            result: Execution result (for successful executions)
            error_message: Error message (for failed executions)
            token_usage: Token consumption metrics
            metadata: Additional execution metadata
            
        Raises:
            EntityNotFoundError: If execution not found
            RepositoryError: If recording fails
        """
        execution = await self.find_by_id(execution_id)
        if not execution:
            raise EntityNotFoundError("StepExecution", execution_id)
        
        # Calculate execution time
        execution_time_ms = None
        if execution.started_at:
            duration = datetime.now() - execution.started_at
            execution_time_ms = int(duration.total_seconds() * 1000)
        
        # Create updated execution
        updated_execution = StepExecution(
            execution_id=execution.execution_id,
            run_id=execution.run_id,
            step_id=execution.step_id,
            status=status,
            started_at=execution.started_at,
            completed_at=datetime.now(),
            result=result,
            error_message=error_message,
            retry_count=execution.retry_count,
            execution_time_ms=execution_time_ms,
            token_usage=token_usage or execution.token_usage,
            metadata={**execution.metadata, **(metadata or {})}
        )
        
        await self.save(updated_execution)
    
    async def record_retry(
        self, 
        execution_id: uuid.UUID, 
        retry_reason: str
    ) -> None:
        """Record a retry attempt for a step execution.
        
        Args:
            execution_id: Execution identifier
            retry_reason: Reason for the retry
            
        Raises:
            EntityNotFoundError: If execution not found
            RepositoryError: If recording fails
        """
        execution = await self.find_by_id(execution_id)
        if not execution:
            raise EntityNotFoundError("StepExecution", execution_id)
        
        # Update retry count and metadata
        updated_metadata = execution.metadata.copy()
        if "retry_history" not in updated_metadata:
            updated_metadata["retry_history"] = []
        
        updated_metadata["retry_history"].append({
            "timestamp": datetime.now().isoformat(),
            "reason": retry_reason,
            "retry_number": execution.retry_count + 1
        })
        
        updated_execution = StepExecution(
            execution_id=execution.execution_id,
            run_id=execution.run_id,
            step_id=execution.step_id,
            status=execution.status,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            result=execution.result,
            error_message=execution.error_message,
            retry_count=execution.retry_count + 1,
            execution_time_ms=execution.execution_time_ms,
            token_usage=execution.token_usage,
            metadata=updated_metadata
        )
        
        await self.save(updated_execution)
    
    async def cleanup_old_executions(
        self, 
        older_than: datetime, 
        keep_count: int = 1000
    ) -> int:
        """Clean up old step executions.
        
        Args:
            older_than: Delete executions older than this date
            keep_count: Minimum number of executions to keep
            
        Returns:
            Number of executions deleted
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        all_executions = await self.find_by_workspace()
        
        # Sort by started_at (newest first)
        all_executions.sort(key=lambda e: e.started_at, reverse=True)
        
        # Keep the newest executions
        executions_to_keep = all_executions[:keep_count]
        keep_ids = {e.execution_id for e in executions_to_keep}
        
        # Find old executions to delete
        old_executions = [
            e for e in all_executions
            if e.started_at < older_than and e.execution_id not in keep_ids
        ]
        
        deleted_count = 0
        for execution in old_executions:
            if await self.delete_by_id(execution.execution_id):
                deleted_count += 1
        
        return deleted_count
    
    async def get_execution_timeline(self, run_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Get execution timeline for a pipeline run.
        
        Args:
            run_id: Pipeline run identifier
            
        Returns:
            List of execution events in chronological order
        """
        executions = await self.find_by_run_id(run_id)
        
        timeline = []
        for execution in executions:
            timeline.append({
                "execution_id": execution.execution_id,
                "step_id": str(execution.step_id),
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "status": str(execution.status),
                "duration_ms": execution.execution_time_ms,
                "retry_count": execution.retry_count,
                "has_error": execution.error_message is not None
            })
        
        return timeline
    
    async def get_token_usage_by_step(self, since: Optional[datetime] = None) -> Dict[str, Dict[str, int]]:
        """Get token usage statistics by step.
        
        Args:
            since: Only include executions after this time
            
        Returns:
            Dictionary mapping step IDs to token usage by provider
        """
        executions = await self.find_by_workspace()
        
        if since:
            executions = [e for e in executions if e.started_at >= since]
        
        step_token_usage = {}
        for execution in executions:
            step_key = str(execution.step_id)
            if step_key not in step_token_usage:
                step_token_usage[step_key] = {}
            
            for provider, tokens in execution.token_usage.items():
                if provider not in step_token_usage[step_key]:
                    step_token_usage[step_key][provider] = 0
                step_token_usage[step_key][provider] += tokens
        
        return step_token_usage