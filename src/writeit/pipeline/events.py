# ABOUTME: Event sourcing system for WriteIt pipeline state management
# ABOUTME: Provides immutable state with copy-on-write branching and event replay
# DEPRECATED: This module is deprecated. Use writeit.domains.pipeline.events instead.

import uuid
from dataclasses import dataclass, field, asdict, replace
from typing import Dict, Any, List, Optional
from datetime import datetime, UTC
from enum import Enum
import warnings

# Import from DDD structure
from writeit.domains.pipeline.events import (
    PipelineExecutionStarted,
    PipelineExecutionCompleted,
    PipelineExecutionFailed,
    StepExecutionStarted,
    StepExecutionCompleted,
    StepExecutionFailed
)
from writeit.domains.pipeline.entities import PipelineRun, StepExecution
from writeit.domains.pipeline.value_objects.execution_status import (
    PipelineExecutionStatus,
    StepExecutionStatus
)

# Issue deprecation warning
warnings.warn(
    "writeit.pipeline.events is deprecated. Use writeit.domains.pipeline.events instead.",
    DeprecationWarning,
    stacklevel=2
)


class EventType(str, Enum):
    """Types of pipeline events. Backward compatibility wrapper."""
    
    @property
    def ddd_type(self):
        """Get corresponding DDD event type."""
        mapping = {
            "run_created": PipelineExecutionStarted,
            "run_started": PipelineExecutionStarted,
            "run_completed": PipelineExecutionCompleted,
            "run_failed": PipelineExecutionFailed,
            "step_started": StepExecutionStarted,
            "step_completed": StepExecutionCompleted,
            "step_failed": StepExecutionFailed,
        }
        return mapping.get(self.value)
    
    # Keep all original enum values for backward compatibility
    RUN_CREATED = "run_created"
    RUN_STARTED = "run_started"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    RUN_PAUSED = "run_paused"
    RUN_RESUMED = "run_resumed"
    RUN_CANCELLED = "run_cancelled"

    STEP_STARTED = "step_started"
    STEP_COMPLETED = "step_completed"
    STEP_FAILED = "step_failed"
    STEP_RESPONSE_GENERATED = "step_response_generated"
    STEP_RESPONSE_SELECTED = "step_response_selected"
    STEP_FEEDBACK_ADDED = "step_feedback_added"
    STEP_RETRIED = "step_retried"

    STATE_SNAPSHOT = "state_snapshot"


@dataclass
class PipelineEvent:
    """Base class for all pipeline events."""

    id: str
    run_id: str
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sequence_number: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for storage."""
        return {
            "id": self.id,
            "run_id": self.run_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "sequence_number": self.sequence_number,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineEvent":
        """Create event from dictionary."""
        return cls(
            id=data["id"],
            run_id=data["run_id"],
            event_type=EventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            sequence_number=data.get("sequence_number", 0),
        )


@dataclass
class PipelineState:
    """Immutable pipeline state snapshot."""

    run: PipelineRun
    version: int = 0
    branch_id: str = "main"
    parent_version: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def copy(self, **changes) -> "PipelineState":
        """Create a copy of the state with changes."""
        # Deep copy the run
        new_run_dict = asdict(self.run)
        new_run_dict.update(changes.get("run_changes", {}))
        new_run = PipelineRun(**new_run_dict)

        return replace(
            self,
            run=new_run,
            version=self.version + 1,
            parent_version=self.version,
            created_at=datetime.now(UTC),
            **{k: v for k, v in changes.items() if k != "run_changes"},
        )

    def branch(self, branch_id: str) -> "PipelineState":
        """Create a new branch from this state."""
        return replace(
            self,
            branch_id=branch_id,
            version=0,
            parent_version=None,
            created_at=datetime.now(UTC),
        )


class PipelineEventStore:
    """Event store for pipeline state management."""

    def __init__(self, storage_manager):
        self.storage = storage_manager
        self.event_cache: Dict[str, List[PipelineEvent]] = {}
        self.state_cache: Dict[str, PipelineState] = {}
        self.sequence_counters: Dict[str, int] = {}

    async def append_event(
        self,
        run_id: str,
        event_type: EventType,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PipelineEvent:
        """Append a new event to the event stream."""
        # Generate event ID and sequence number
        event_id = str(uuid.uuid4())
        sequence_number = self.sequence_counters.get(run_id, 0) + 1
        self.sequence_counters[run_id] = sequence_number

        # Create event
        event = PipelineEvent(
            id=event_id,
            run_id=run_id,
            event_type=event_type,
            timestamp=datetime.now(UTC),
            data=data,
            metadata=metadata or {},
            sequence_number=sequence_number,
        )

        # Store event
        await self._store_event(event)

        # Update cache
        if run_id not in self.event_cache:
            self.event_cache[run_id] = []
        self.event_cache[run_id].append(event)

        # Invalidate state cache for this run
        if run_id in self.state_cache:
            del self.state_cache[run_id]

        return event

    async def get_events(
        self, run_id: str, from_sequence: int = 0
    ) -> List[PipelineEvent]:
        """Get all events for a run from a specific sequence number."""
        # Check cache first
        if run_id in self.event_cache:
            cached_events = self.event_cache[run_id]
            return [e for e in cached_events if e.sequence_number > from_sequence]

        # Load from storage
        events = await self._load_events(run_id)
        self.event_cache[run_id] = events
        return [e for e in events if e.sequence_number > from_sequence]

    async def get_current_state(self, run_id: str) -> Optional[PipelineState]:
        """Get the current state by replaying all events."""
        # Check cache first
        if run_id in self.state_cache:
            return self.state_cache[run_id]

        # Get all events
        events = await self.get_events(run_id)
        if not events:
            return None

        # Replay events to build state
        state = await self._replay_events(events)

        # Cache the state
        self.state_cache[run_id] = state
        return state

    async def get_state_at_version(
        self, run_id: str, version: int
    ) -> Optional[PipelineState]:
        """Get state at a specific version."""
        events = await self.get_events(run_id)

        # Filter events up to the target version
        target_events = []
        for event in events:
            target_events.append(event)
            if len(target_events) >= version:
                break

        if not target_events:
            return None

        return await self._replay_events(target_events)

    async def create_snapshot(self, run_id: str) -> PipelineEvent:
        """Create a state snapshot event for performance."""
        current_state = await self.get_current_state(run_id)
        if not current_state:
            raise ValueError(f"No state found for run {run_id}")

        # Create snapshot event
        snapshot_data = {
            "state": asdict(current_state),
            "snapshot_version": current_state.version,
        }

        return await self.append_event(
            run_id, EventType.STATE_SNAPSHOT, snapshot_data, {"snapshot": True}
        )

    async def _replay_events(self, events: List[PipelineEvent]) -> PipelineState:
        """Replay events to build current state."""
        if not events:
            raise ValueError("Cannot replay empty event list")

        # Find the latest snapshot
        snapshot_event = None
        snapshot_index = 0

        for i, event in enumerate(events):
            if event.event_type == EventType.STATE_SNAPSHOT:
                snapshot_event = event
                snapshot_index = i

        # Start from snapshot or create initial state
        if snapshot_event:
            state_data = snapshot_event.data["state"]
            state = PipelineState(**state_data)
            replay_events = events[snapshot_index + 1 :]
        else:
            # Create initial state from first event
            first_event = events[0]
            if first_event.event_type != EventType.RUN_CREATED:
                raise ValueError("First event must be RUN_CREATED")

            initial_run = PipelineRun(**first_event.data)
            state = PipelineState(run=initial_run)
            replay_events = events[1:]

        # Replay remaining events
        for event in replay_events:
            state = await self._apply_event(state, event)

        return state

    async def _apply_event(
        self, state: PipelineState, event: PipelineEvent
    ) -> PipelineState:
        """Apply a single event to state and return new state."""
        run_changes = {}

        if event.event_type == EventType.RUN_STARTED:
            run_changes = {
                "status": PipelineExecutionStatus.RUNNING,
                "started_at": event.timestamp,
            }

        elif event.event_type == EventType.RUN_COMPLETED:
            run_changes = {
                "status": PipelineExecutionStatus.COMPLETED,
                "completed_at": event.timestamp,
                "outputs": event.data.get("outputs", {}),
            }

        elif event.event_type == EventType.RUN_FAILED:
            run_changes = {
                "status": PipelineExecutionStatus.FAILED,
                "completed_at": event.timestamp,
                "error": event.data.get("error"),
            }

        elif event.event_type == EventType.STEP_STARTED:
            step_key = event.data["step_key"]
            # Find or create step execution
            step_exec = self._find_or_create_step(state.run, step_key)
            step_exec.status = StepExecutionStatus.RUNNING
            step_exec.started_at = event.timestamp

            # Update run with modified step
            run_changes = {"steps": self._update_step_in_run(state.run, step_exec)}

        elif event.event_type == EventType.STEP_COMPLETED:
            step_key = event.data["step_key"]
            step_exec = self._find_step(state.run, step_key)
            if step_exec:
                step_exec.status = StepExecutionStatus.COMPLETED
                step_exec.completed_at = event.timestamp
                step_exec.execution_time = event.data.get("execution_time", 0)
                step_exec.tokens_used = event.data.get("tokens_used", {})

                run_changes = {"steps": self._update_step_in_run(state.run, step_exec)}

        elif event.event_type == EventType.STEP_RESPONSE_GENERATED:
            step_key = event.data["step_key"]
            step_exec = self._find_step(state.run, step_key)
            if step_exec:
                step_exec.responses = event.data.get("responses", [])
                run_changes = {"steps": self._update_step_in_run(state.run, step_exec)}

        elif event.event_type == EventType.STEP_RESPONSE_SELECTED:
            step_key = event.data["step_key"]
            step_exec = self._find_step(state.run, step_key)
            if step_exec:
                step_exec.selected_response = event.data.get("selected_response")
                run_changes = {"steps": self._update_step_in_run(state.run, step_exec)}

        elif event.event_type == EventType.STEP_FEEDBACK_ADDED:
            step_key = event.data["step_key"]
            step_exec = self._find_step(state.run, step_key)
            if step_exec:
                step_exec.user_feedback = event.data.get("feedback", "")
                run_changes = {"steps": self._update_step_in_run(state.run, step_exec)}

        # Create new state with changes
        return state.copy(run_changes=run_changes)

    def _find_step(self, run: PipelineRun, step_key: str) -> Optional[StepExecution]:
        """Find a step execution in the run."""
        for step in run.steps:
            if step.step_key == step_key:
                return step
        return None

    def _find_or_create_step(self, run: PipelineRun, step_key: str) -> StepExecution:
        """Find or create a step execution."""
        existing = self._find_step(run, step_key)
        if existing:
            return existing

        return StepExecution(step_key=step_key)

    def _update_step_in_run(
        self, run: PipelineRun, updated_step: StepExecution
    ) -> List[StepExecution]:
        """Update a step in the run's step list."""
        new_steps = []
        found = False

        for step in run.steps:
            if step.step_key == updated_step.step_key:
                new_steps.append(updated_step)
                found = True
            else:
                new_steps.append(step)

        if not found:
            new_steps.append(updated_step)

        return new_steps

    async def _store_event(self, event: PipelineEvent) -> None:
        """Store an event to persistent storage."""
        key = f"event_{event.run_id}_{event.sequence_number:06d}"
        self.storage.store_json(key, event.to_dict(), db_name="pipeline_events")

    async def _load_events(self, run_id: str) -> List[PipelineEvent]:
        """Load all events for a run from storage with efficient pagination."""
        try:
            # Use prefix search to find all events for this run
            event_prefix = f"event_{run_id}_"
            
            # Get all event keys for this run, sorted by sequence number
            event_keys = self.storage.list_keys(
                prefix=event_prefix, 
                db_name="pipeline_events"
            )
            
            # Sort keys by sequence number (encoded in the key)
            event_keys.sort()  # Keys are formatted as "event_{run_id}_{sequence_number:06d}"
            
            events = []
            
            # Load events in batches to avoid memory issues with large event streams
            batch_size = 100
            for i in range(0, len(event_keys), batch_size):
                batch_keys = event_keys[i:i + batch_size]
                
                # Load batch of events
                for key in batch_keys:
                    try:
                        event_data = self.storage.load_json(
                            key=key, 
                            db_name="pipeline_events"
                        )
                        if event_data:
                            event = PipelineEvent.from_dict(event_data)
                            events.append(event)
                    except (KeyError, ValueError, TypeError) as e:
                        # Log warning for corrupted events but continue processing
                        warnings.warn(
                            f"Failed to load event {key} for run {run_id}: {e}",
                            RuntimeWarning
                        )
                        continue
            
            # Sort events by sequence number to ensure correct order
            events.sort(key=lambda e: e.sequence_number)
            
            # Update sequence counter for this run
            if events:
                max_sequence = max(event.sequence_number for event in events)
                self.sequence_counters[run_id] = max_sequence
            
            return events
            
        except Exception as e:
            # Log error and return empty list to avoid breaking the system
            warnings.warn(
                f"Failed to load events for run {run_id}: {e}",
                RuntimeWarning
            )
            return []
