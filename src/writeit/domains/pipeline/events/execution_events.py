"""Pipeline execution domain events.

Events related to pipeline and step execution lifecycle."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional

from ....shared.events import DomainEvent
from ..value_objects.pipeline_id import PipelineId
from ..value_objects.step_id import StepId


@dataclass(frozen=True)
class PipelineExecutionStarted(DomainEvent):
    """Event fired when pipeline execution begins.
    
    This event is published when a pipeline run is created
    and execution has started.
    """
    
    run_id: str = field()
    pipeline_id: PipelineId = field()
    workspace_name: str = field()
    inputs: Dict[str, Any] = field()
    step_count: int = field()
    started_at: datetime = field()
    started_by: Optional[str] = field()
    execution_mode: str = field()  # 'cli', 'tui', 'api'
    
    @property
    def event_type(self) -> str:
        return "pipeline.execution.started"
    
    @property
    def aggregate_id(self) -> str:
        return self.run_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "run_id": self.run_id,
                "pipeline_id": str(self.pipeline_id),
                "workspace_name": self.workspace_name,
                "inputs": self.inputs,
                "step_count": self.step_count,
                "started_at": self.started_at.isoformat(),
                "started_by": self.started_by,
                "execution_mode": self.execution_mode
            }
        }


@dataclass(frozen=True)
class PipelineExecutionCompleted(DomainEvent):
    """Event fired when pipeline execution completes successfully.
    
    This event is published when a pipeline run finishes
    successfully with all steps completed.
    """
    
    run_id: str = field()
    pipeline_id: PipelineId = field()
    workspace_name: str = field()
    outputs: Dict[str, Any] = field()
    execution_time: float = field()  # seconds
    total_tokens_used: int = field()
    completed_at: datetime = field()
    steps_completed: int = field()
    steps_skipped: int = field()
    
    @property
    def event_type(self) -> str:
        return "pipeline.execution.completed"
    
    @property
    def aggregate_id(self) -> str:
        return self.run_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "run_id": self.run_id,
                "pipeline_id": str(self.pipeline_id),
                "workspace_name": self.workspace_name,
                "outputs": self.outputs,
                "execution_time": self.execution_time,
                "total_tokens_used": self.total_tokens_used,
                "completed_at": self.completed_at.isoformat(),
                "steps_completed": self.steps_completed,
                "steps_skipped": self.steps_skipped
            }
        }


@dataclass(frozen=True)
class PipelineExecutionFailed(DomainEvent):
    """Event fired when pipeline execution fails.
    
    This event is published when a pipeline run fails
    due to an error or unrecoverable condition.
    """
    
    run_id: str = field()
    pipeline_id: PipelineId = field()
    workspace_name: str = field()
    error_message: str = field()
    error_type: str = field()
    failed_step_id: Optional[StepId] = field()
    execution_time: float = field()  # seconds
    failed_at: datetime = field()
    steps_completed: int = field()
    recoverable: bool = field()
    
    @property
    def event_type(self) -> str:
        return "pipeline.execution.failed"
    
    @property
    def aggregate_id(self) -> str:
        return self.run_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "run_id": self.run_id,
                "pipeline_id": str(self.pipeline_id),
                "workspace_name": self.workspace_name,
                "error_message": self.error_message,
                "error_type": self.error_type,
                "failed_step_id": str(self.failed_step_id) if self.failed_step_id else None,
                "execution_time": self.execution_time,
                "failed_at": self.failed_at.isoformat(),
                "steps_completed": self.steps_completed,
                "recoverable": self.recoverable
            }
        }


@dataclass(frozen=True)
class PipelineExecutionCancelled(DomainEvent):
    """Event fired when pipeline execution is cancelled.
    
    This event is published when a pipeline run is cancelled
    by user request or system intervention.
    """
    
    run_id: str = field()
    pipeline_id: PipelineId = field()
    workspace_name: str = field()
    cancelled_by: Optional[str] = field()
    cancelled_at: datetime = field()
    execution_time: float = field()  # seconds
    steps_completed: int = field()
    reason: Optional[str] = field()
    
    @property
    def event_type(self) -> str:
        return "pipeline.execution.cancelled"
    
    @property
    def aggregate_id(self) -> str:
        return self.run_id
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "run_id": self.run_id,
                "pipeline_id": str(self.pipeline_id),
                "workspace_name": self.workspace_name,
                "cancelled_by": self.cancelled_by,
                "cancelled_at": self.cancelled_at.isoformat(),
                "execution_time": self.execution_time,
                "steps_completed": self.steps_completed,
                "reason": self.reason
            }
        }


@dataclass(frozen=True)
class StepExecutionStarted(DomainEvent):
    """Event fired when step execution begins.
    
    This event is published when a pipeline step
    starts execution within a pipeline run.
    """
    
    run_id: str = field()
    step_id: StepId = field()
    step_name: str = field()
    step_type: str = field()
    inputs: Dict[str, Any] = field()
    started_at: datetime = field()
    attempt_number: int = field()
    
    @property
    def event_type(self) -> str:
        return "step.execution.started"
    
    @property
    def aggregate_id(self) -> str:
        return f"{self.run_id}:{self.step_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "run_id": self.run_id,
                "step_id": str(self.step_id),
                "step_name": self.step_name,
                "step_type": self.step_type,
                "inputs": self.inputs,
                "started_at": self.started_at.isoformat(),
                "attempt_number": self.attempt_number
            }
        }


@dataclass(frozen=True)
class StepExecutionCompleted(DomainEvent):
    """Event fired when step execution completes successfully.
    
    This event is published when a pipeline step
    finishes successfully with outputs.
    """
    
    run_id: str = field()
    step_id: StepId = field()
    step_name: str = field()
    step_type: str = field()
    outputs: Dict[str, Any] = field()
    execution_time: float = field()  # seconds
    tokens_used: int = field()
    completed_at: datetime = field()
    attempt_number: int = field()
    
    @property
    def event_type(self) -> str:
        return "step.execution.completed"
    
    @property
    def aggregate_id(self) -> str:
        return f"{self.run_id}:{self.step_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "run_id": self.run_id,
                "step_id": str(self.step_id),
                "step_name": self.step_name,
                "step_type": self.step_type,
                "outputs": self.outputs,
                "execution_time": self.execution_time,
                "tokens_used": self.tokens_used,
                "completed_at": self.completed_at.isoformat(),
                "attempt_number": self.attempt_number
            }
        }


@dataclass(frozen=True)
class StepExecutionFailed(DomainEvent):
    """Event fired when step execution fails.
    
    This event is published when a pipeline step
    fails due to an error or timeout.
    """
    
    run_id: str = field()
    step_id: StepId = field()
    step_name: str = field()
    step_type: str = field()
    error_message: str = field()
    error_type: str = field()
    execution_time: float = field()  # seconds
    failed_at: datetime = field()
    attempt_number: int = field()
    will_retry: bool = field()
    
    @property
    def event_type(self) -> str:
        return "step.execution.failed"
    
    @property
    def aggregate_id(self) -> str:
        return f"{self.run_id}:{self.step_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "run_id": self.run_id,
                "step_id": str(self.step_id),
                "step_name": self.step_name,
                "step_type": self.step_type,
                "error_message": self.error_message,
                "error_type": self.error_type,
                "execution_time": self.execution_time,
                "failed_at": self.failed_at.isoformat(),
                "attempt_number": self.attempt_number,
                "will_retry": self.will_retry
            }
        }


@dataclass(frozen=True)
class StepExecutionSkipped(DomainEvent):
    """Event fired when step execution is skipped.
    
    This event is published when a pipeline step
    is skipped due to conditional logic or dependencies.
    """
    
    run_id: str = field()
    step_id: StepId = field()
    step_name: str = field()
    step_type: str = field()
    reason: str = field()
    skipped_at: datetime = field()
    
    @property
    def event_type(self) -> str:
        return "step.execution.skipped"
    
    @property
    def aggregate_id(self) -> str:
        return f"{self.run_id}:{self.step_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "run_id": self.run_id,
                "step_id": str(self.step_id),
                "step_name": self.step_name,
                "step_type": self.step_type,
                "reason": self.reason,
                "skipped_at": self.skipped_at.isoformat()
            }
        }


@dataclass(frozen=True)
class StepExecutionRetried(DomainEvent):
    """Event fired when step execution is retried.
    
    This event is published when a pipeline step
    is retried after a previous failure.
    """
    
    run_id: str = field()
    step_id: StepId = field()
    step_name: str = field()
    step_type: str = field()
    previous_error: str = field()
    retry_attempt: int = field()
    max_retries: int = field()
    retried_at: datetime = field()
    delay_seconds: float = field()
    
    @property
    def event_type(self) -> str:
        return "step.execution.retried"
    
    @property
    def aggregate_id(self) -> str:
        return f"{self.run_id}:{self.step_id}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "event_id": str(self.event_id),
            "aggregate_id": self.aggregate_id,
            "timestamp": self.timestamp.isoformat(),
            "data": {
                "run_id": self.run_id,
                "step_id": str(self.step_id),
                "step_name": self.step_name,
                "step_type": self.step_type,
                "previous_error": self.previous_error,
                "retry_attempt": self.retry_attempt,
                "max_retries": self.max_retries,
                "retried_at": self.retried_at.isoformat(),
                "delay_seconds": self.delay_seconds
            }
        }