"""Pipeline run entity.

Domain entity representing an instance of pipeline execution.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Self

from ..value_objects.pipeline_id import PipelineId
from ..value_objects.step_id import StepId
from ..value_objects.execution_status import ExecutionStatus, PipelineExecutionStatus


@dataclass
class PipelineRun:
    """Domain entity representing a pipeline execution instance.
    
    A pipeline run tracks the execution of a specific pipeline template
    with user-provided inputs, maintaining state and progress through
    individual step executions.
    
    Examples:
        run = PipelineRun.create(
            pipeline_id=pipeline_id,
            workspace_name="my-project",
            inputs={"topic": "AI ethics"}
        )
        
        # Start execution
        run = run.start()
        
        # Update status
        run = run.update_status(ExecutionStatus.running())
        
        # Complete execution
        run = run.complete(outputs={"article": "..."})
    """
    
    id: str
    pipeline_id: PipelineId
    workspace_name: str
    status: ExecutionStatus
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    total_tokens_used: Dict[str, int] = field(default_factory=dict)
    total_execution_time: float = 0.0
    
    def __post_init__(self) -> None:
        """Validate pipeline run."""
        if not self.id or not isinstance(self.id, str):
            raise ValueError("Pipeline run id must be a non-empty string")
            
        if not isinstance(self.pipeline_id, PipelineId):
            raise TypeError("Pipeline id must be a PipelineId")
            
        if not self.workspace_name or not isinstance(self.workspace_name, str):
            raise ValueError("Workspace name must be a non-empty string")
            
        if not isinstance(self.status, ExecutionStatus):
            raise TypeError("Status must be an ExecutionStatus")
            
        if not isinstance(self.inputs, dict):
            raise TypeError("Inputs must be a dictionary")
            
        if not isinstance(self.outputs, dict):
            raise TypeError("Outputs must be a dictionary")
            
        if not isinstance(self.created_at, datetime):
            raise TypeError("Created_at must be a datetime")
            
        if self.started_at is not None and not isinstance(self.started_at, datetime):
            raise TypeError("Started_at must be a datetime or None")
            
        if self.completed_at is not None and not isinstance(self.completed_at, datetime):
            raise TypeError("Completed_at must be a datetime or None")
            
        # Validate state consistency
        if self.status.is_active and self.started_at is None:
            raise ValueError("Active pipeline run must have started_at set")
            
        if self.status.is_terminal and self.completed_at is None:
            raise ValueError("Completed pipeline run must have completed_at set")
            
        if self.status.is_failed and not self.error:
            raise ValueError("Failed pipeline run must have error message")
    
    @property
    def is_running(self) -> bool:
        """Check if pipeline is currently running."""
        return self.status.is_active
    
    @property
    def is_completed(self) -> bool:
        """Check if pipeline completed successfully."""
        return self.status.is_successful
    
    @property
    def is_failed(self) -> bool:
        """Check if pipeline failed."""
        return self.status.is_failed
    
    @property
    def is_cancelled(self) -> bool:
        """Check if pipeline was cancelled."""
        return self.status.is_cancelled
    
    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    def start(self) -> Self:
        """Start pipeline execution.
        
        Returns:
            New pipeline run with started status
            
        Raises:
            ValueError: If pipeline is already started
        """
        if self.started_at is not None:
            raise ValueError("Pipeline run is already started")
            
        new_status = self.status.transition_to(PipelineExecutionStatus.RUNNING)
        
        return dataclass.replace(
            self,
            status=new_status,
            started_at=datetime.now()
        )
    
    def pause(self) -> Self:
        """Pause pipeline execution.
        
        Returns:
            New pipeline run with paused status
            
        Raises:
            ValueError: If pipeline is not running
        """
        if not self.status.is_active:
            raise ValueError("Can only pause running pipeline")
            
        new_status = self.status.transition_to(PipelineExecutionStatus.PAUSED)
        
        return dataclass.replace(
            self,
            status=new_status
        )
    
    def resume(self) -> Self:
        """Resume paused pipeline execution.
        
        Returns:
            New pipeline run with running status
            
        Raises:
            ValueError: If pipeline is not paused
        """
        if self.status.status != PipelineExecutionStatus.PAUSED:
            raise ValueError("Can only resume paused pipeline")
            
        new_status = self.status.transition_to(PipelineExecutionStatus.RUNNING)
        
        return dataclass.replace(
            self,
            status=new_status
        )
    
    def complete(self, outputs: Optional[Dict[str, Any]] = None) -> Self:
        """Complete pipeline execution successfully.
        
        Args:
            outputs: Final pipeline outputs
            
        Returns:
            New pipeline run with completed status
            
        Raises:
            ValueError: If pipeline is not running
        """
        if not self.status.is_active:
            raise ValueError("Can only complete active pipeline")
            
        new_status = self.status.transition_to(PipelineExecutionStatus.COMPLETED)
        
        return dataclass.replace(
            self,
            status=new_status,
            outputs=outputs or self.outputs,
            completed_at=datetime.now()
        )
    
    def fail(self, error_message: str) -> Self:
        """Fail pipeline execution.
        
        Args:
            error_message: Error description
            
        Returns:
            New pipeline run with failed status
        """
        new_status = self.status.transition_to(
            PipelineExecutionStatus.FAILED,
            error_message=error_message
        )
        
        return dataclass.replace(
            self,
            status=new_status,
            error=error_message,
            completed_at=datetime.now()
        )
    
    def cancel(self) -> Self:
        """Cancel pipeline execution.
        
        Returns:
            New pipeline run with cancelled status
        """
        new_status = self.status.transition_to(PipelineExecutionStatus.CANCELLED)
        
        return dataclass.replace(
            self,
            status=new_status,
            completed_at=datetime.now()
        )
    
    def update_status(self, status: ExecutionStatus) -> Self:
        """Update pipeline status.
        
        Args:
            status: New execution status
            
        Returns:
            New pipeline run with updated status
        """
        if not isinstance(status, ExecutionStatus):
            raise TypeError("Status must be an ExecutionStatus")
            
        return dataclass.replace(self, status=status)
    
    def update_metadata(self, metadata: Dict[str, Any]) -> Self:
        """Update pipeline metadata.
        
        Args:
            metadata: New metadata (merged with existing)
            
        Returns:
            New pipeline run with updated metadata
        """
        new_metadata = {**self.metadata, **metadata}
        return dataclass.replace(self, metadata=new_metadata)
    
    def add_token_usage(self, provider: str, tokens: int) -> Self:
        """Add token usage for a provider.
        
        Args:
            provider: LLM provider name
            tokens: Number of tokens used
            
        Returns:
            New pipeline run with updated token usage
        """
        new_token_usage = self.total_tokens_used.copy()
        new_token_usage[provider] = new_token_usage.get(provider, 0) + tokens
        
        return dataclass.replace(self, total_tokens_used=new_token_usage)
    
    def update_execution_time(self, additional_time: float) -> Self:
        """Update total execution time.
        
        Args:
            additional_time: Additional execution time in seconds
            
        Returns:
            New pipeline run with updated execution time
        """
        return dataclass.replace(
            self,
            total_execution_time=self.total_execution_time + additional_time
        )
    
    def set_outputs(self, outputs: Dict[str, Any]) -> Self:
        """Set pipeline outputs.
        
        Args:
            outputs: Pipeline output values
            
        Returns:
            New pipeline run with updated outputs
        """
        return dataclass.replace(self, outputs=outputs)
    
    def get_input(self, key: str, default: Any = None) -> Any:
        """Get input value by key.
        
        Args:
            key: Input key
            default: Default value if key not found
            
        Returns:
            Input value or default
        """
        return self.inputs.get(key, default)
    
    def get_output(self, key: str, default: Any = None) -> Any:
        """Get output value by key.
        
        Args:
            key: Output key
            default: Default value if key not found
            
        Returns:
            Output value or default
        """
        return self.outputs.get(key, default)
    
    def get_total_tokens(self) -> int:
        """Get total tokens used across all providers."""
        return sum(self.total_tokens_used.values())
    
    @classmethod
    def create(
        cls,
        pipeline_id: PipelineId,
        workspace_name: str,
        inputs: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Self:
        """Create a new pipeline run.
        
        Args:
            pipeline_id: Pipeline template identifier
            workspace_name: Workspace name
            inputs: Pipeline input values
            metadata: Additional metadata
            
        Returns:
            New pipeline run
        """
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        
        return cls(
            id=run_id,
            pipeline_id=pipeline_id,
            workspace_name=workspace_name,
            status=ExecutionStatus.created(),
            inputs=inputs or {},
            metadata=metadata or {},
            created_at=datetime.now()
        )
    
    @classmethod
    def from_template(
        cls,
        pipeline_id: PipelineId,
        workspace_name: str,
        template_inputs: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Self:
        """Create pipeline run from template with validated inputs.
        
        Args:
            pipeline_id: Pipeline template identifier
            workspace_name: Workspace name
            template_inputs: Validated template inputs
            metadata: Additional metadata
            
        Returns:
            New pipeline run
        """
        return cls.create(
            pipeline_id=pipeline_id,
            workspace_name=workspace_name,
            inputs=template_inputs,
            metadata=metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'pipeline_id': str(self.pipeline_id),
            'workspace_name': self.workspace_name,
            'status': str(self.status.status),
            'inputs': self.inputs,
            'outputs': self.outputs,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
            'metadata': self.metadata,
            'total_tokens_used': self.total_tokens_used,
            'total_execution_time': self.total_execution_time
        }
    
    def __str__(self) -> str:
        """String representation."""
        return f"PipelineRun({self.id} - {self.status.status})"
    
    def __repr__(self) -> str:
        """Debug representation."""
        return (f"PipelineRun(id='{self.id}', pipeline_id={self.pipeline_id}, "
                f"status={self.status.status}, workspace='{self.workspace_name}')")