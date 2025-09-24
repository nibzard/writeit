"""Mock implementation of StepExecutionRepository for testing."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from writeit.domains.pipeline.repositories.step_execution_repository import (
    StepExecutionRepository, StepExecution
)
from writeit.domains.pipeline.value_objects.step_name import StepName
from writeit.domains.pipeline.value_objects.execution_status import ExecutionStatus
from writeit.domains.workspace.value_objects.workspace_name import WorkspaceName
from writeit.shared.repository import Specification

from ..base_mock_repository import BaseMockRepository, MockEntityNotFoundError


class MockStepExecutionRepository(BaseMockRepository[StepExecution], StepExecutionRepository):
    """Mock implementation of StepExecutionRepository.
    
    Provides in-memory storage for step executions with execution tracking
    and pipeline run association.
    """
    
    def __init__(self, workspace_name: WorkspaceName):
        super().__init__(str(workspace_name.value))
        self._workspace_name_obj = workspace_name
        
    def _get_entity_id(self, entity: StepExecution) -> Any:
        """Extract entity ID from step execution."""
        return str(entity.id)
        
    def _get_entity_type_name(self) -> str:
        """Get entity type name for logging."""
        return "StepExecution"
        
    # Repository interface implementation
    
    async def save(self, entity: StepExecution) -> None:
        """Save or update a step execution."""
        await self._check_error_condition("save")
        self._increment_call_count("save")
        await self._apply_call_delay("save")
        
        entity_id = self._get_entity_id(entity)
        self._store_entity(entity, entity_id)
        self._log_event("save", self._get_entity_type_name(), entity_id)
        
    async def find_by_id(self, entity_id: UUID) -> Optional[StepExecution]:
        """Find step execution by ID."""
        await self._check_error_condition("find_by_id")
        self._increment_call_count("find_by_id")
        await self._apply_call_delay("find_by_id")
        
        execution = self._get_entity(str(entity_id))
        self._log_event("find_by_id", self._get_entity_type_name(), str(entity_id), found=execution is not None)
        return execution
        
    async def find_all(self) -> List[StepExecution]:
        """Find all step executions in current workspace."""
        await self._check_error_condition("find_all")
        self._increment_call_count("find_all")
        await self._apply_call_delay("find_all")
        
        executions = self._get_all_entities()
        self._log_event("find_all", self._get_entity_type_name(), count=len(executions))
        return executions
        
    async def find_by_specification(self, spec: Specification[StepExecution]) -> List[StepExecution]:
        """Find step executions matching specification."""
        await self._check_error_condition("find_by_specification")
        self._increment_call_count("find_by_specification")
        await self._apply_call_delay("find_by_specification")
        
        executions = self._find_entities_by_specification(spec)
        self._log_event("find_by_specification", self._get_entity_type_name(), count=len(executions))
        return executions
        
    async def exists(self, entity_id: UUID) -> bool:
        """Check if step execution exists."""
        await self._check_error_condition("exists")
        self._increment_call_count("exists")
        await self._apply_call_delay("exists")
        
        exists = self._entity_exists(str(entity_id))
        self._log_event("exists", self._get_entity_type_name(), str(entity_id), exists=exists)
        return exists
        
    async def delete(self, entity: StepExecution) -> None:
        """Delete a step execution."""
        await self._check_error_condition("delete")
        self._increment_call_count("delete")
        await self._apply_call_delay("delete")
        
        entity_id = self._get_entity_id(entity)
        if not self._delete_entity(entity_id):
            raise MockEntityNotFoundError(self._get_entity_type_name(), entity_id)
        self._log_event("delete", self._get_entity_type_name(), entity_id)
        
    async def delete_by_id(self, entity_id: UUID) -> bool:
        """Delete step execution by ID."""
        await self._check_error_condition("delete_by_id")
        self._increment_call_count("delete_by_id")
        await self._apply_call_delay("delete_by_id")
        
        deleted = self._delete_entity(str(entity_id))
        self._log_event("delete_by_id", self._get_entity_type_name(), str(entity_id), deleted=deleted)
        return deleted
        
    async def count(self) -> int:
        """Count total step executions."""
        await self._check_error_condition("count")
        self._increment_call_count("count")
        await self._apply_call_delay("count")
        
        total = self._count_entities()
        self._log_event("count", self._get_entity_type_name(), total=total)
        return total
        
    async def _find_by_workspace_impl(self, workspace: WorkspaceName) -> List[StepExecution]:
        """Implementation-specific workspace query."""
        return self._get_all_entities(str(workspace.value))
        
    # StepExecutionRepository-specific methods
    
    async def find_by_pipeline_run(self, run_id: UUID) -> List[StepExecution]:
        """Find all step executions for a pipeline run."""
        await self._check_error_condition("find_by_pipeline_run")
        self._increment_call_count("find_by_pipeline_run")
        await self._apply_call_delay("find_by_pipeline_run")
        
        executions = self._get_all_entities()
        matching_executions = [e for e in executions if e.pipeline_run_id == run_id]
        
        # Sort by step order/sequence
        matching_executions.sort(key=lambda e: e.step_order if hasattr(e, 'step_order') else 0)
        
        self._log_event("find_by_pipeline_run", self._get_entity_type_name(), 
                       count=len(matching_executions), run_id=str(run_id))
        return matching_executions
        
    async def find_by_step_name(self, step_name: StepName) -> List[StepExecution]:
        """Find all executions for a specific step name."""
        await self._check_error_condition("find_by_step_name")
        self._increment_call_count("find_by_step_name")
        await self._apply_call_delay("find_by_step_name")
        
        executions = self._get_all_entities()
        matching_executions = [e for e in executions if e.step_name == step_name]
        
        # Sort by execution time desc
        matching_executions.sort(key=lambda e: e.started_at or datetime.min, reverse=True)
        
        self._log_event("find_by_step_name", self._get_entity_type_name(), 
                       count=len(matching_executions), step_name=str(step_name.value))
        return matching_executions
        
    async def find_by_status(self, status: ExecutionStatus) -> List[StepExecution]:
        """Find step executions with specific status."""
        await self._check_error_condition("find_by_status")
        self._increment_call_count("find_by_status")
        await self._apply_call_delay("find_by_status")
        
        executions = self._get_all_entities()
        matching_executions = [e for e in executions if e.status == status]
        
        self._log_event("find_by_status", self._get_entity_type_name(), 
                       count=len(matching_executions), status=str(status))
        return matching_executions
        
    async def find_failed_steps(
        self, 
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[StepExecution]:
        """Find failed step executions."""
        await self._check_error_condition("find_failed_steps")
        self._increment_call_count("find_failed_steps")
        await self._apply_call_delay("find_failed_steps")
        
        executions = self._get_all_entities()
        failed_executions = [e for e in executions if e.status == ExecutionStatus.FAILED]
        
        if since:
            failed_executions = [e for e in failed_executions 
                               if e.failed_at and e.failed_at >= since]
            
        # Sort by failure time desc
        failed_executions.sort(key=lambda e: e.failed_at or datetime.min, reverse=True)
        
        if limit:
            failed_executions = failed_executions[:limit]
            
        self._log_event("find_failed_steps", self._get_entity_type_name(), 
                       count=len(failed_executions), since=since, limit=limit)
        return failed_executions
        
    async def find_long_running_steps(
        self, 
        threshold_seconds: int = 300
    ) -> List[StepExecution]:
        """Find long-running step executions."""
        await self._check_error_condition("find_long_running_steps")
        self._increment_call_count("find_long_running_steps")
        await self._apply_call_delay("find_long_running_steps")
        
        executions = self._get_all_entities()
        current_time = datetime.now()
        
        long_running = []
        for execution in executions:
            if execution.status == ExecutionStatus.RUNNING and execution.started_at:
                duration = (current_time - execution.started_at).total_seconds()
                if duration > threshold_seconds:
                    long_running.append(execution)
                    
        self._log_event("find_long_running_steps", self._get_entity_type_name(), 
                       count=len(long_running), threshold_seconds=threshold_seconds)
        return long_running
        
    async def get_step_performance_stats(
        self, 
        step_name: Optional[StepName] = None
    ) -> Dict[str, Any]:
        """Get step execution performance statistics."""
        await self._check_error_condition("get_step_performance_stats")
        self._increment_call_count("get_step_performance_stats")
        await self._apply_call_delay("get_step_performance_stats")
        
        executions = self._get_all_entities()
        if step_name:
            executions = [e for e in executions if e.step_name == step_name]
            
        total_executions = len(executions)
        successful_executions = len([e for e in executions if e.status == ExecutionStatus.COMPLETED])
        failed_executions = len([e for e in executions if e.status == ExecutionStatus.FAILED])
        
        # Calculate average duration for completed executions
        completed_executions = [e for e in executions 
                              if e.status == ExecutionStatus.COMPLETED and e.duration]
        avg_duration = (sum(e.duration.total_seconds() for e in completed_executions) 
                       / len(completed_executions)) if completed_executions else 0
        
        success_rate = (successful_executions / total_executions * 100) if total_executions > 0 else 0
        
        stats = {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "failed_executions": failed_executions,
            "average_duration_seconds": avg_duration,
            "success_rate": success_rate
        }
        
        self._log_event("get_step_performance_stats", self._get_entity_type_name(), 
                       step_name=str(step_name.value) if step_name else None, **stats)
        return stats
        
    async def get_execution_timeline(
        self, 
        run_id: UUID
    ) -> List[Dict[str, Any]]:
        """Get execution timeline for a pipeline run."""
        await self._check_error_condition("get_execution_timeline")
        self._increment_call_count("get_execution_timeline")
        await self._apply_call_delay("get_execution_timeline")
        
        executions = await self.find_by_pipeline_run(run_id)
        
        timeline = []
        for execution in executions:
            timeline_entry = {
                "step_name": str(execution.step_name.value),
                "status": str(execution.status),
                "started_at": execution.started_at,
                "completed_at": execution.completed_at,
                "duration_seconds": execution.duration.total_seconds() if execution.duration else None,
                "error_message": execution.error_message
            }
            timeline.append(timeline_entry)
            
        self._log_event("get_execution_timeline", self._get_entity_type_name(), 
                       run_id=str(run_id), timeline_length=len(timeline))
        return timeline
        
    async def update_step_status(
        self, 
        execution_id: UUID, 
        status: ExecutionStatus, 
        error_message: Optional[str] = None
    ) -> None:
        """Update step execution status."""
        await self._check_error_condition("update_step_status")
        self._increment_call_count("update_step_status")
        await self._apply_call_delay("update_step_status")
        
        execution = self._get_entity(str(execution_id))
        if not execution:
            raise MockEntityNotFoundError(self._get_entity_type_name(), str(execution_id))
            
        # Create updated execution with new status (immutable update pattern)
        updated_execution = execution.with_status(status, error_message)
        self._store_entity(updated_execution, str(execution_id))
        
        self._log_event("update_step_status", self._get_entity_type_name(), 
                       str(execution_id), status=str(status), error_message=error_message)
        
    async def cleanup_old_executions(
        self, 
        older_than: datetime,
        keep_recent_count: int = 1000
    ) -> int:
        """Clean up old step executions."""
        await self._check_error_condition("cleanup_old_executions")
        self._increment_call_count("cleanup_old_executions")
        await self._apply_call_delay("cleanup_old_executions")
        
        executions = self._get_all_entities()
        
        # Sort by start time desc
        executions.sort(key=lambda e: e.started_at or datetime.min, reverse=True)
        
        # Keep the most recent executions
        executions_to_keep = executions[:keep_recent_count]
        executions_to_check = executions[keep_recent_count:]
        
        deleted_count = 0
        for execution in executions_to_check:
            if execution.started_at and execution.started_at < older_than:
                self._delete_entity(self._get_entity_id(execution))
                deleted_count += 1
                
        self._log_event("cleanup_old_executions", self._get_entity_type_name(), 
                       deleted_count=deleted_count, older_than=older_than, keep_recent_count=keep_recent_count)
        return deleted_count