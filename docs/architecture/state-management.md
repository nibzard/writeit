# State Management

WriteIt employs **Event Sourcing** combined with **Copy-on-Write** semantics to enable complete pipeline history tracking, time-travel capabilities, and efficient branching operations.

## 🎯 Event Sourcing Overview

Event sourcing treats state changes as a sequence of immutable events. Instead of storing current state, WriteIt stores the complete history of events that led to the current state.

```
Current State = f(Event₁, Event₂, Event₃, ..., Eventₙ)
```

This approach enables:
- **Complete audit trails** of every user decision
- **Time-travel debugging** to any previous state
- **Branching** from any point in pipeline history
- **Replay capabilities** for testing and analysis

## 📋 Event Types

### Core Pipeline Events

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from typing import Dict, List, Any

class EventType(Enum):
    PIPELINE_STARTED = "pipeline_started"
    STEP_STARTED = "step_started"
    RESPONSE_RECEIVED = "response_received"
    RESPONSE_SELECTED = "response_selected"
    STEP_COMPLETED = "step_completed"
    PIPELINE_PAUSED = "pipeline_paused"
    PIPELINE_RESUMED = "pipeline_resumed"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_BRANCHED = "pipeline_branched"
    PIPELINE_REWOUND = "pipeline_rewound"

@dataclass(frozen=True)  # Immutable
class BaseEvent:
    event_id: UUID
    pipeline_run_id: UUID
    event_type: EventType
    timestamp: datetime
    user_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### Specific Event Implementations

```python
@dataclass(frozen=True)
class PipelineStartedEvent(BaseEvent):
    configuration_id: str
    user_inputs: Dict[str, str]
    initial_step: StepName
    
    def __post_init__(self):
        super().__init__(event_type=EventType.PIPELINE_STARTED)

@dataclass(frozen=True)
class StepStartedEvent(BaseEvent):
    step_name: StepName
    models_requested: List[str]
    prompt_template: str
    user_feedback: str = ""

@dataclass(frozen=True)
class ResponseReceivedEvent(BaseEvent):
    step_name: StepName
    response: AIResponse
    response_index: int

@dataclass(frozen=True)
class ResponseSelectedEvent(BaseEvent):
    step_name: StepName
    selected_response_index: int
    user_feedback: str
    merged_content: str

@dataclass(frozen=True)
class PipelineBranchedEvent(BaseEvent):
    parent_pipeline_run_id: UUID
    branch_point: StepName
    branch_name: Optional[str] = None
```

## 🔄 State Reconstruction

### Event Replay Pattern
```python
class PipelineStateProjector:
    """Reconstructs pipeline state from event stream"""
    
    def __init__(self):
        self.event_handlers = {
            EventType.PIPELINE_STARTED: self._handle_pipeline_started,
            EventType.STEP_STARTED: self._handle_step_started,
            EventType.RESPONSE_RECEIVED: self._handle_response_received,
            EventType.RESPONSE_SELECTED: self._handle_response_selected,
            EventType.STEP_COMPLETED: self._handle_step_completed,
            EventType.PIPELINE_BRANCHED: self._handle_pipeline_branched,
        }
    
    async def reconstruct_state(self, pipeline_run_id: UUID) -> PipelineRun:
        """Reconstruct current pipeline state from events"""
        events = await self.event_store.get_events(pipeline_run_id)
        
        # Initialize empty state
        state = None
        
        # Replay events in chronological order
        for event in events:
            handler = self.event_handlers.get(event.event_type)
            if handler:
                state = await handler(state, event)
        
        return state
    
    async def _handle_pipeline_started(
        self, 
        state: Optional[PipelineRun], 
        event: PipelineStartedEvent
    ) -> PipelineRun:
        """Initialize pipeline state"""
        return PipelineRun(
            pipeline_run_id=event.pipeline_run_id,
            configuration_id=event.configuration_id,
            created_at=event.timestamp,
            current_step=event.initial_step,
            status=PipelineStatus.RUNNING,
            user_inputs=event.user_inputs,
            steps={}
        )
    
    async def _handle_response_received(
        self, 
        state: PipelineRun, 
        event: ResponseReceivedEvent
    ) -> PipelineRun:
        """Add response to step state"""
        if event.step_name not in state.steps:
            state.steps[event.step_name] = StepState(
                step_name=event.step_name,
                status=StepStatus.RUNNING
            )
        
        state.steps[event.step_name].ai_responses.append(event.response)
        return state
    
    async def _handle_response_selected(
        self, 
        state: PipelineRun, 
        event: ResponseSelectedEvent
    ) -> PipelineRun:
        """Complete step with user selection"""
        step_state = state.steps[event.step_name]
        step_state.user_selection = event.selected_response_index
        step_state.user_feedback = event.user_feedback
        step_state.merged_content = event.merged_content
        step_state.status = StepStatus.COMPLETED
        step_state.completed_at = event.timestamp
        
        return state
```

## 🌳 Branching Implementation

### Copy-on-Write Branching
WriteIt implements efficient branching using copy-on-write semantics, where branches share immutable history until they diverge.

```python
class BranchManager:
    """Manages pipeline branching and rewind operations"""
    
    async def create_branch(
        self, 
        parent_run_id: UUID, 
        branch_point: StepName,
        branch_name: Optional[str] = None
    ) -> UUID:
        """Create new branch from specified step"""
        
        # Get parent pipeline history up to branch point
        parent_events = await self.event_store.get_events(parent_run_id)
        branch_events = self._filter_events_to_step(parent_events, branch_point)
        
        # Create new pipeline run ID
        branch_run_id = uuid4()
        
        # Create branching event
        branch_event = PipelineBranchedEvent(
            event_id=uuid4(),
            pipeline_run_id=branch_run_id,
            parent_pipeline_run_id=parent_run_id,
            branch_point=branch_point,
            branch_name=branch_name,
            timestamp=datetime.utcnow(),
            user_id="current_user"
        )
        
        # Store branch relationship
        await self.event_store.append_event(branch_event)
        
        # Copy relevant events to new branch (with new pipeline_run_id)
        for event in branch_events:
            branch_event_copy = self._copy_event_to_branch(event, branch_run_id)
            await self.event_store.append_event(branch_event_copy)
        
        return branch_run_id
    
    def _filter_events_to_step(
        self, 
        events: List[BaseEvent], 
        target_step: StepName
    ) -> List[BaseEvent]:
        """Filter events up to specified step"""
        step_order = [StepName.ANGLES, StepName.OUTLINE, StepName.DRAFT, StepName.POLISH]
        target_index = step_order.index(target_step)
        
        filtered_events = []
        for event in events:
            if isinstance(event, (StepStartedEvent, ResponseReceivedEvent, ResponseSelectedEvent)):
                event_step_index = step_order.index(event.step_name)
                if event_step_index <= target_index:
                    filtered_events.append(event)
            else:
                # Include pipeline-level events
                filtered_events.append(event)
        
        return filtered_events
    
    async def rewind_to_step(
        self, 
        pipeline_run_id: UUID, 
        target_step: StepName
    ) -> None:
        """Rewind pipeline to specified step"""
        
        # Create rewind event (marks invalidation point)
        rewind_event = PipelineRewindEvent(
            event_id=uuid4(),
            pipeline_run_id=pipeline_run_id,
            target_step=target_step,
            timestamp=datetime.utcnow(),
            user_id="current_user"
        )
        
        await self.event_store.append_event(rewind_event)
        
        # State reconstruction will handle the rewind logic
        # by ignoring events after the rewind point
```

### Efficient Branch Storage
```python
class EventStore:
    """LMDB-based event storage with branch optimization"""
    
    async def get_effective_events(self, pipeline_run_id: UUID) -> List[BaseEvent]:
        """Get events considering rewind operations"""
        all_events = await self.get_events(pipeline_run_id)
        
        # Find the most recent rewind event
        rewind_events = [e for e in all_events if isinstance(e, PipelineRewindEvent)]
        if not rewind_events:
            return all_events
        
        latest_rewind = max(rewind_events, key=lambda e: e.timestamp)
        rewind_timestamp = latest_rewind.timestamp
        
        # Filter out events after rewind point
        effective_events = []
        for event in all_events:
            if event.timestamp <= rewind_timestamp:
                effective_events.append(event)
            elif isinstance(event, PipelineRewindEvent) and event == latest_rewind:
                effective_events.append(event)
        
        return effective_events
    
    async def get_branch_tree(self, root_run_id: UUID) -> Dict[UUID, List[UUID]]:
        """Get complete branch tree structure"""
        with self.env.begin() as txn:
            branch_tree = {}
            
            def build_tree(run_id: UUID):
                children_key = f"branch_children:{run_id}"
                children_data = txn.get(children_key.encode())
                
                if children_data:
                    children = json.loads(children_data.decode())
                    branch_tree[run_id] = [UUID(child_id) for child_id in children]
                    
                    # Recursively build subtrees
                    for child_id in children:
                        build_tree(UUID(child_id))
                else:
                    branch_tree[run_id] = []
            
            build_tree(root_run_id)
            return branch_tree
```

## ⚡ Performance Optimizations

### Snapshot Strategy
For long-running pipelines with many events, WriteIt uses periodic snapshots to speed up state reconstruction:

```python
class SnapshotManager:
    """Manages pipeline state snapshots for performance"""
    
    async def create_snapshot(
        self, 
        pipeline_run_id: UUID, 
        state: PipelineRun
    ) -> None:
        """Create snapshot at current state"""
        snapshot = PipelineSnapshot(
            pipeline_run_id=pipeline_run_id,
            state=state,
            event_count=await self.event_store.count_events(pipeline_run_id),
            created_at=datetime.utcnow()
        )
        
        await self.store_snapshot(snapshot)
    
    async def reconstruct_from_snapshot(
        self, 
        pipeline_run_id: UUID
    ) -> Optional[PipelineRun]:
        """Reconstruct state from most recent snapshot + subsequent events"""
        latest_snapshot = await self.get_latest_snapshot(pipeline_run_id)
        
        if not latest_snapshot:
            return None
        
        # Get events after snapshot
        events_after_snapshot = await self.event_store.get_events_after(
            pipeline_run_id, 
            latest_snapshot.created_at
        )
        
        # Apply events to snapshot state
        state = latest_snapshot.state
        for event in events_after_snapshot:
            state = await self.projector.apply_event(state, event)
        
        return state
```

### Memory Management
```python
class StateCache:
    """LRU cache for frequently accessed pipeline states"""
    
    def __init__(self, max_size: int = 100):
        self.cache: OrderedDict[UUID, PipelineRun] = OrderedDict()
        self.max_size = max_size
        self.access_times: Dict[UUID, datetime] = {}
    
    async def get_state(self, pipeline_run_id: UUID) -> Optional[PipelineRun]:
        """Get cached state with LRU eviction"""
        if pipeline_run_id in self.cache:
            # Move to end (most recently used)
            state = self.cache.pop(pipeline_run_id)
            self.cache[pipeline_run_id] = state
            self.access_times[pipeline_run_id] = datetime.utcnow()
            return state
        
        return None
    
    async def store_state(self, pipeline_run_id: UUID, state: PipelineRun) -> None:
        """Store state with LRU eviction"""
        if len(self.cache) >= self.max_size:
            # Remove least recently used
            oldest_id = next(iter(self.cache))
            self.cache.pop(oldest_id)
            self.access_times.pop(oldest_id, None)
        
        self.cache[pipeline_run_id] = state
        self.access_times[pipeline_run_id] = datetime.utcnow()
```

## 🧪 Testing Event Sourcing

### Event Store Testing
```python
class TestEventSourcing:
    """Test suite for event sourcing functionality"""
    
    async def test_pipeline_reconstruction(self):
        """Test complete pipeline state reconstruction"""
        # Given: A sequence of events
        events = [
            PipelineStartedEvent(...),
            StepStartedEvent(step_name=StepName.ANGLES, ...),
            ResponseReceivedEvent(...),
            ResponseSelectedEvent(...),
            StepCompletedEvent(...)
        ]
        
        # When: Reconstructing state
        for event in events:
            await event_store.append_event(event)
        
        reconstructed_state = await projector.reconstruct_state(pipeline_run_id)
        
        # Then: State matches expected final state
        assert reconstructed_state.current_step == StepName.OUTLINE
        assert len(reconstructed_state.steps[StepName.ANGLES].ai_responses) == 1
        assert reconstructed_state.steps[StepName.ANGLES].status == StepStatus.COMPLETED
    
    async def test_branching_isolation(self):
        """Test that branches don't affect parent state"""
        # Given: Original pipeline with completed steps
        original_id = await create_test_pipeline()
        
        # When: Creating branch and modifying it
        branch_id = await branch_manager.create_branch(
            original_id, 
            StepName.OUTLINE
        )
        
        await execute_step(branch_id, StepName.DRAFT)
        
        # Then: Original pipeline unchanged
        original_state = await projector.reconstruct_state(original_id)
        branch_state = await projector.reconstruct_state(branch_id)
        
        assert original_state.current_step == StepName.POLISH
        assert branch_state.current_step == StepName.DRAFT
        assert original_state.steps != branch_state.steps
    
    async def test_rewind_functionality(self):
        """Test pipeline rewind to previous step"""
        # Given: Pipeline at final step
        pipeline_id = await create_completed_pipeline()
        
        # When: Rewinding to earlier step
        await branch_manager.rewind_to_step(pipeline_id, StepName.OUTLINE)
        
        # Then: State reflects rewind
        state = await projector.reconstruct_state(pipeline_id)
        assert state.current_step == StepName.OUTLINE
        assert StepName.DRAFT not in state.steps
        assert StepName.POLISH not in state.steps
```

This event sourcing architecture provides WriteIt with complete auditability, flexible branching capabilities, and the ability to replay and analyze pipeline executions while maintaining excellent performance through caching and snapshot strategies.