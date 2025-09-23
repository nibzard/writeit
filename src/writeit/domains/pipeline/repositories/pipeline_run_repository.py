"""Pipeline run repository interface.

Provides data access operations for pipeline runs including
execution state persistence, history tracking, and performance analytics.
"""

from abc import abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ....shared.repository import WorkspaceAwareRepository, Specification
from ....domains.workspace.value_objects.workspace_name import WorkspaceName
from ..entities.pipeline_run import PipelineRun
from ..value_objects.pipeline_id import PipelineId
from ..value_objects.execution_status import ExecutionStatus


class PipelineRunRepository(WorkspaceAwareRepository[PipelineRun]):
    """Repository for pipeline run persistence and retrieval.
    
    Handles CRUD operations for pipeline execution instances with
    state management, history tracking, and performance analytics.
    """
    
    @abstractmethod
    async def find_by_template_id(self, template_id: PipelineId) -> List[PipelineRun]:
        """Find all runs for a specific template.
        
        Args:
            template_id: Template identifier
            
        Returns:
            List of runs for the template, ordered by start time desc
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: ExecutionStatus) -> List[PipelineRun]:
        """Find all runs with specific status.
        
        Args:
            status: Execution status to filter by
            
        Returns:
            List of runs with the status
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_active_runs(self) -> List[PipelineRun]:
        """Find all currently active (running) pipeline runs.
        
        Returns:
            List of active runs
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_completed_runs(
        self, 
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[PipelineRun]:
        """Find completed runs with optional filtering.
        
        Args:
            since: Only include runs completed after this time
            limit: Maximum number of runs to return
            
        Returns:
            List of completed runs, ordered by completion time desc
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_failed_runs(
        self, 
        since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[PipelineRun]:
        """Find failed runs with optional filtering.
        
        Args:
            since: Only include runs that failed after this time
            limit: Maximum number of runs to return
            
        Returns:
            List of failed runs, ordered by failure time desc
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def find_runs_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[PipelineRun]:
        """Find runs within a date range.
        
        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            
        Returns:
            List of runs in the date range
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def get_execution_stats(
        self, 
        template_id: Optional[PipelineId] = None
    ) -> dict:
        """Get execution statistics.
        
        Args:
            template_id: Optional template to get stats for
            
        Returns:
            Dictionary with execution statistics:
            - total_runs: Total number of runs
            - successful_runs: Number of successful runs
            - failed_runs: Number of failed runs
            - average_duration: Average execution time
            - success_rate: Success percentage
            
        Raises:
            RepositoryError: If stats calculation fails
        """
        pass
    
    @abstractmethod
    async def get_recent_runs(
        self, 
        limit: int = 10, 
        workspace: Optional[WorkspaceName] = None
    ) -> List[PipelineRun]:
        """Get most recent runs.
        
        Args:
            limit: Maximum number of runs to return
            workspace: Optional workspace filter
            
        Returns:
            List of recent runs, ordered by start time desc
            
        Raises:
            RepositoryError: If query operation fails
        """
        pass
    
    @abstractmethod
    async def cleanup_old_runs(
        self, 
        older_than: datetime, 
        keep_count: int = 100
    ) -> int:
        """Clean up old pipeline runs.
        
        Args:
            older_than: Delete runs older than this date
            keep_count: Minimum number of runs to keep per template
            
        Returns:
            Number of runs deleted
            
        Raises:
            RepositoryError: If cleanup operation fails
        """
        pass
    
    @abstractmethod
    async def update_run_status(
        self, 
        run_id: UUID, 
        status: ExecutionStatus, 
        error_message: Optional[str] = None
    ) -> None:
        """Update run status and optional error message.
        
        Args:
            run_id: Run identifier
            status: New execution status
            error_message: Optional error message for failed runs
            
        Raises:
            EntityNotFoundError: If run not found
            RepositoryError: If update operation fails
        """
        pass


# Specifications for pipeline run queries

class ByTemplateIdSpecification(Specification[PipelineRun]):
    """Specification for filtering runs by template ID."""
    
    def __init__(self, template_id: PipelineId):
        self.template_id = template_id
    
    def is_satisfied_by(self, run: PipelineRun) -> bool:
        return run.template_id == self.template_id


class ByStatusSpecification(Specification[PipelineRun]):
    """Specification for filtering runs by status."""
    
    def __init__(self, status: ExecutionStatus):
        self.status = status
    
    def is_satisfied_by(self, run: PipelineRun) -> bool:
        return run.status == self.status


class ActiveRunsSpecification(Specification[PipelineRun]):
    """Specification for filtering active runs."""
    
    def is_satisfied_by(self, run: PipelineRun) -> bool:
        return run.status in [ExecutionStatus.RUNNING, ExecutionStatus.PENDING]


class CompletedRunsSpecification(Specification[PipelineRun]):
    """Specification for filtering completed runs."""
    
    def is_satisfied_by(self, run: PipelineRun) -> bool:
        return run.status == ExecutionStatus.COMPLETED


class FailedRunsSpecification(Specification[PipelineRun]):
    """Specification for filtering failed runs."""
    
    def is_satisfied_by(self, run: PipelineRun) -> bool:
        return run.status == ExecutionStatus.FAILED


class DateRangeSpecification(Specification[PipelineRun]):
    """Specification for filtering runs by date range."""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        self.start_date = start_date
        self.end_date = end_date
    
    def is_satisfied_by(self, run: PipelineRun) -> bool:
        return (
            run.started_at is not None and
            self.start_date <= run.started_at <= self.end_date
        )


class ByPipelineSpecification(Specification[PipelineRun]):
    """Specification for filtering runs by pipeline ID."""
    
    def __init__(self, pipeline_id: PipelineId):
        self.pipeline_id = pipeline_id
    
    def is_satisfied_by(self, run: PipelineRun) -> bool:
        return run.pipeline_id == self.pipeline_id


class ByWorkspaceSpecification(Specification[PipelineRun]):
    """Specification for filtering runs by workspace."""
    
    def __init__(self, workspace_name: WorkspaceName):
        self.workspace_name = workspace_name
    
    def is_satisfied_by(self, run: PipelineRun) -> bool:
        return run.workspace_name == self.workspace_name


class RecentRunsSpecification(Specification[PipelineRun]):
    """Specification for filtering recent runs."""
    
    def __init__(self, days: int = 7, limit: int = 100):
        self.days = days
        self.limit = limit
        self.cutoff_date = datetime.now() - timedelta(days=days)
    
    def is_satisfied_by(self, run: PipelineRun) -> bool:
        return (
            run.started_at is not None and
            run.started_at >= self.cutoff_date
        )
