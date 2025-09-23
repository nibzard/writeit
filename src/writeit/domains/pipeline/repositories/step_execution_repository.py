"""Step execution repository interface.

Provides data access operations for individual step executions including
result storage, performance tracking, and retry management.
"""

from abc import abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from ....shared.repository import Repository, Specification
from ..entities.pipeline_step import PipelineStep
from ..value_objects.step_id import StepId
from ..value_objects.execution_status import ExecutionStatus


class StepExecution:
    """Value object representing a step execution result.
    
    Contains execution metadata, results, and performance metrics.
    """
    
    def __init__(
        self,
        execution_id: UUID,
        run_id: UUID,
        step_id: StepId,
        status: ExecutionStatus,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        result: Optional[str] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0,
        execution_time_ms: Optional[int] = None,
        token_usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.execution_id = execution_id
        self.run_id = run_id
        self.step_id = step_id
        self.status = status
        self.started_at = started_at
        self.completed_at = completed_at
        self.result = result
        self.error_message = error_message
        self.retry_count = retry_count
        self.execution_time_ms = execution_time_ms
        self.token_usage = token_usage or {}
        self.metadata = metadata or {}
    
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed (success or failure)."""
        return self.status in [ExecutionStatus.COMPLETED, ExecutionStatus.FAILED]
    
    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        return self.status == ExecutionStatus.COMPLETED
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.execution_time_ms is not None:
            return self.execution_time_ms / 1000.0
        return None


class StepExecutionRepository(Repository[StepExecution]):
    """Repository for step execution persistence and retrieval.
    
    Handles CRUD operations for individual step executions with
    performance tracking, retry management, and analytics.
    """
    
    @abstractmethod
    async def find_by_run_id(self, run_id: UUID) -> List[StepExecution]:
        """Find all step executions for a pipeline run.
        
        Args:
            run_id: Pipeline run identifier
            
        Returns:
            List of step executions, ordered by execution order
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_step_id(
        self, 
        run_id: UUID, 
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
            Dictionary with performance statistics:
            - total_executions: Total number of executions
            - successful_executions: Number of successful executions
            - failed_executions: Number of failed executions
            - average_duration_ms: Average execution time
            - median_duration_ms: Median execution time
            - success_rate: Success percentage
            - retry_rate: Percentage requiring retries
            - total_tokens: Total tokens consumed
            
        Raises:
            RepositoryError: If stats calculation fails
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
            List of dictionaries with step failure statistics:
            - step_id: Step identifier
            - total_executions: Total execution count
            - failed_executions: Failed execution count
            - failure_rate: Failure percentage
            - common_errors: Most common error messages
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def record_execution_start(
        self, 
        run_id: UUID, 
        step_id: StepId
    ) -> UUID:
        """Record the start of a step execution.
        
        Args:
            run_id: Pipeline run identifier
            step_id: Step identifier
            
        Returns:
            Execution ID for tracking
            
        Raises:
            RepositoryError: If recording fails
        """
        pass
    
    @abstractmethod
    async def record_execution_completion(
        self,
        execution_id: UUID,
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
        pass
    
    @abstractmethod
    async def record_retry(
        self, 
        execution_id: UUID, 
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
        pass
    
    @abstractmethod
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
        pass


# Specifications for step execution queries

class ByRunIdSpecification(Specification[StepExecution]):
    """Specification for filtering executions by run ID."""
    
    def __init__(self, run_id: UUID):
        self.run_id = run_id
    
    def is_satisfied_by(self, execution: StepExecution) -> bool:
        return execution.run_id == self.run_id


class ByStepIdSpecification(Specification[StepExecution]):
    """Specification for filtering executions by step ID."""
    
    def __init__(self, step_id: StepId):
        self.step_id = step_id
    
    def is_satisfied_by(self, execution: StepExecution) -> bool:
        return execution.step_id == self.step_id


class FailedExecutionsSpecification(Specification[StepExecution]):
    """Specification for filtering failed executions."""
    
    def is_satisfied_by(self, execution: StepExecution) -> bool:
        return execution.status == ExecutionStatus.FAILED


class RetryExecutionsSpecification(Specification[StepExecution]):
    """Specification for filtering executions with retries."""
    
    def __init__(self, min_retries: int = 1):
        self.min_retries = min_retries
    
    def is_satisfied_by(self, execution: StepExecution) -> bool:
        return execution.retry_count >= self.min_retries


class SuccessfulExecutionsSpecification(Specification[StepExecution]):
    """Specification for filtering successful executions."""
    
    def is_satisfied_by(self, execution: StepExecution) -> bool:
        return execution.status == ExecutionStatus.COMPLETED
