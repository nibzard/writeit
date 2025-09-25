"""Execution status value object.

Provides state enumeration with valid state transitions and validation.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Set, Self, Optional, cast
from datetime import datetime


class PipelineExecutionStatus(str, Enum):
    """Valid states for pipeline execution."""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class StepExecutionStatus(str, Enum):
    """Valid states for step execution."""
    PENDING = "pending"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class ExecutionStatus:
    """Execution status with state transition validation.
    
    Tracks current status and validates state transitions to ensure
    proper execution lifecycle management.
    
    Examples:
        ExecutionStatus.created()
        ExecutionStatus.running(started_at=datetime.now())
        status.transition_to(PipelineExecutionStatus.COMPLETED)
    """
    
    status: PipelineExecutionStatus | StepExecutionStatus
    changed_at: datetime
    error_message: Optional[str] = None
    metadata: Optional[dict] = None
    
    def __post_init__(self) -> None:
        """Validate status configuration."""
        if not isinstance(self.status, (PipelineExecutionStatus, StepExecutionStatus)):
            raise TypeError("Status must be a valid execution status enum")
            
        if not isinstance(self.changed_at, datetime):
            raise TypeError("Changed_at must be a datetime")
            
        # Validate error message only for failed states
        if self.is_failed and not self.error_message:
            raise ValueError("Failed status must include error message")
            
        if not self.is_failed and self.error_message:
            raise ValueError("Non-failed status should not include error message")
    
    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal (final) state."""
        terminal_states = {
            PipelineExecutionStatus.COMPLETED,
            PipelineExecutionStatus.FAILED,
            PipelineExecutionStatus.CANCELLED,
            PipelineExecutionStatus.TIMEOUT,
            StepExecutionStatus.COMPLETED,
            StepExecutionStatus.FAILED,
            StepExecutionStatus.SKIPPED,
            StepExecutionStatus.CANCELLED,
            StepExecutionStatus.TIMEOUT,
        }
        return self.status in terminal_states
    
    @property
    def is_active(self) -> bool:
        """Check if execution is currently active."""
        active_states = {
            PipelineExecutionStatus.RUNNING,
            PipelineExecutionStatus.QUEUED,
            StepExecutionStatus.RUNNING,
            StepExecutionStatus.WAITING_INPUT,
        }
        return self.status in active_states
    
    @property
    def is_successful(self) -> bool:
        """Check if execution completed successfully."""
        success_states = {
            PipelineExecutionStatus.COMPLETED,
            StepExecutionStatus.COMPLETED,
            StepExecutionStatus.SKIPPED,  # Skipped is considered successful
        }
        return self.status in success_states
    
    @property
    def is_failed(self) -> bool:
        """Check if execution failed."""
        failed_states = {
            PipelineExecutionStatus.FAILED,
            PipelineExecutionStatus.TIMEOUT,
            StepExecutionStatus.FAILED,
            StepExecutionStatus.TIMEOUT,
        }
        return self.status in failed_states
    
    @property
    def is_cancelled(self) -> bool:
        """Check if execution was cancelled."""
        cancelled_states = {
            PipelineExecutionStatus.CANCELLED,
            StepExecutionStatus.CANCELLED,
        }
        return self.status in cancelled_states
    
    def can_transition_to(self, new_status: PipelineExecutionStatus | StepExecutionStatus) -> bool:
        """Check if transition to new status is valid."""
        return new_status in self._get_valid_transitions()
    
    def transition_to(
        self, 
        new_status: PipelineExecutionStatus | StepExecutionStatus,
        error_message: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> Self:
        """Create new status with state transition.
        
        Args:
            new_status: Target status
            error_message: Error message for failed states
            metadata: Additional status metadata
            
        Returns:
            New ExecutionStatus instance
            
        Raises:
            ValueError: If transition is invalid
        """
        if not self.can_transition_to(new_status):
            valid_transitions = self._get_valid_transitions()
            raise ValueError(
                f"Invalid transition from {self.status} to {new_status}. "
                f"Valid transitions: {', '.join(str(s) for s in valid_transitions)}"
            )
        
        return self.__class__(
            status=new_status,
            changed_at=datetime.now(),
            error_message=error_message,
            metadata=metadata
        )
    
    def _get_valid_transitions(self) -> Set[PipelineExecutionStatus | StepExecutionStatus]:
        """Get valid transitions from current status."""
        # Pipeline status transitions
        pipeline_transitions = {
            PipelineExecutionStatus.CREATED: {
                PipelineExecutionStatus.QUEUED,
                PipelineExecutionStatus.RUNNING,
                PipelineExecutionStatus.CANCELLED,
            },
            PipelineExecutionStatus.QUEUED: {
                PipelineExecutionStatus.RUNNING,
                PipelineExecutionStatus.CANCELLED,
            },
            PipelineExecutionStatus.RUNNING: {
                PipelineExecutionStatus.PAUSED,
                PipelineExecutionStatus.COMPLETED,
                PipelineExecutionStatus.FAILED,
                PipelineExecutionStatus.CANCELLED,
                PipelineExecutionStatus.TIMEOUT,
            },
            PipelineExecutionStatus.PAUSED: {
                PipelineExecutionStatus.RUNNING,
                PipelineExecutionStatus.CANCELLED,
            },
            # Terminal states have no valid transitions
            PipelineExecutionStatus.COMPLETED: set(),
            PipelineExecutionStatus.FAILED: set(),
            PipelineExecutionStatus.CANCELLED: set(),
            PipelineExecutionStatus.TIMEOUT: set(),
        }
        
        # Step status transitions
        step_transitions = {
            StepExecutionStatus.PENDING: {
                StepExecutionStatus.RUNNING,
                StepExecutionStatus.SKIPPED,
                StepExecutionStatus.CANCELLED,
            },
            StepExecutionStatus.RUNNING: {
                StepExecutionStatus.WAITING_INPUT,
                StepExecutionStatus.COMPLETED,
                StepExecutionStatus.FAILED,
                StepExecutionStatus.CANCELLED,
                StepExecutionStatus.TIMEOUT,
            },
            StepExecutionStatus.WAITING_INPUT: {
                StepExecutionStatus.RUNNING,
                StepExecutionStatus.CANCELLED,
                StepExecutionStatus.TIMEOUT,
            },
            # Terminal states have no valid transitions
            StepExecutionStatus.COMPLETED: set(),
            StepExecutionStatus.FAILED: set(),
            StepExecutionStatus.SKIPPED: set(),
            StepExecutionStatus.CANCELLED: set(),
            StepExecutionStatus.TIMEOUT: set(),
        }
        
        # Return transitions based on the actual status type
        if isinstance(self.status, PipelineExecutionStatus):
            return cast(Set[PipelineExecutionStatus | StepExecutionStatus], pipeline_transitions.get(self.status, set()))
        elif isinstance(self.status, StepExecutionStatus):
            return cast(Set[PipelineExecutionStatus | StepExecutionStatus], step_transitions.get(self.status, set()))
        else:
            return set()
    
    @classmethod
    def created(cls, metadata: Optional[dict] = None) -> Self:
        """Create a new CREATED status."""
        return cls(
            status=PipelineExecutionStatus.CREATED,
            changed_at=datetime.now(),
            metadata=metadata
        )
    
    @classmethod
    def running(cls, metadata: Optional[dict] = None) -> Self:
        """Create a new RUNNING status."""
        return cls(
            status=PipelineExecutionStatus.RUNNING,
            changed_at=datetime.now(),
            metadata=metadata
        )
    
    @classmethod
    def step_pending(cls, metadata: Optional[dict] = None) -> Self:
        """Create a new step PENDING status."""
        return cls(
            status=StepExecutionStatus.PENDING,
            changed_at=datetime.now(),
            metadata=metadata
        )
    
    @classmethod
    def failed(cls, error_message: str, metadata: Optional[dict] = None) -> Self:
        """Create a new FAILED status."""
        return cls(
            status=PipelineExecutionStatus.FAILED,
            changed_at=datetime.now(),
            error_message=error_message,
            metadata=metadata
        )
    
    @classmethod
    def completed(cls, metadata: Optional[dict] = None) -> Self:
        """Create a new COMPLETED status."""
        return cls(
            status=PipelineExecutionStatus.COMPLETED,
            changed_at=datetime.now(),
            metadata=metadata
        )
    
    @classmethod
    def cancelled(cls, metadata: Optional[dict] = None) -> Self:
        """Create a new CANCELLED status."""
        return cls(
            status=PipelineExecutionStatus.CANCELLED,
            changed_at=datetime.now(),
            metadata=metadata
        )
    
    @classmethod
    def paused(cls, metadata: Optional[dict] = None) -> Self:
        """Create a new PAUSED status."""
        return cls(
            status=PipelineExecutionStatus.PAUSED,
            changed_at=datetime.now(),
            metadata=metadata
        )
    
    def __str__(self) -> str:
        """String representation."""
        if self.error_message:
            return f"{self.status} ({self.error_message})"
        return str(self.status)
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if isinstance(other, ExecutionStatus):
            return self.status == other.status
        if isinstance(other, (PipelineExecutionStatus, StepExecutionStatus)):
            return self.status == other
        return False