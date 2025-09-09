# System Architecture

WriteIt employs a **single-process, multi-layer architecture** that combines a Textual TUI frontend with an embedded FastAPI server, utilizing LMDB for persistent storage and llm.datasette.io for multi-provider AI integration.

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WriteIt Application                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    HTTP/WebSocket    ┌───────────────┐ │
│  │   TUI Client    │ ◄─────────────────► │ FastAPI Server│ │
│  │   (Textual)     │                     │   (async)     │ │
│  └─────────────────┘                     └───────────────┘ │
│           │                                       │         │
│           ▼                                       ▼         │
│  ┌─────────────────┐                     ┌───────────────┐ │
│  │ WebSocket Client│                     │ LLM Router    │ │
│  │  (async)        │                     │ (llm.datasette)│ │
│  └─────────────────┘                     └───────────────┘ │
│                                                   │         │
│                                                   ▼         │
│                                          ┌───────────────┐ │
│                                          │ Pipeline Engine│ │
│                                          │ (Event Sourced)│ │
│                                          └───────────────┘ │
│                                                   │         │
│                                                   ▼         │
│                                          ┌───────────────┐ │
│                                          │ LMDB Storage  │ │
│                                          │ (Versioned)   │ │
│                                          └───────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🧩 Core Components

### 1. TUI Layer (Textual Framework)
**Purpose**: Provides interactive terminal interface for pipeline management

**Key Components**:
- `PipelineView`: Main pipeline execution interface
- `StreamWidget`: Real-time LLM response display
- `SelectionWidget`: Response selection and feedback interface  
- `NavigationWidget`: Step progression and branching controls

**Responsibilities**:
- Real-time streaming display of LLM responses
- User input collection and validation
- Pipeline step navigation and control
- WebSocket communication with embedded server

### 2. Server Layer (FastAPI)
**Purpose**: Orchestrates pipeline execution and API endpoints

**Key Components**:
- `PipelineRouter`: REST endpoints for pipeline management
- `StepRouter`: Step execution and selection endpoints
- `WebSocketHandler`: Real-time streaming coordination
- `ErrorHandler`: Centralized error management

**Responsibilities**:
- Pipeline lifecycle management
- WebSocket streaming coordination
- API request validation and routing
- Background task management

### 3. LLM Integration Layer
**Purpose**: Unified interface to multiple AI providers with fallback handling

**Key Components**:
- `LLMClient`: Provider abstraction layer
- `StreamHandler`: Token-by-token response streaming
- `FallbackManager`: Provider health monitoring and switching
- `UsageTracker`: Cost tracking and rate limiting

**Responsibilities**:
- Multi-provider LLM communication
- Response streaming and buffering
- Provider fallback and error recovery
- Usage analytics and cost tracking

### 4. Pipeline Engine
**Purpose**: Manages pipeline state transitions and execution flow

**Key Components**:
- `StateMachine`: Pipeline state management
- `StepExecutor`: Individual step processing
- `BranchManager`: Rewind and forking operations
- `TemplateEngine`: Prompt generation and substitution

**Responsibilities**:
- Pipeline state validation and transitions
- Step execution orchestration
- Branching and rewind operations
- User feedback integration

### 5. Storage Layer (LMDB)
**Purpose**: Persistent storage with versioning and event sourcing

**Key Components**:
- `EventStore`: Immutable event logging
- `ArtifactManager`: Versioned artifact storage
- `QueryEngine`: Efficient data retrieval
- `BackupManager`: Export and recovery operations

**Responsibilities**:
- Immutable pipeline history storage
- Artifact versioning and retrieval
- Branch and rewind state management
- Export and backup operations

## 🔄 Data Flow

### Pipeline Execution Flow
```
1. User Input (TUI) → FastAPI Server
2. Server → Pipeline Engine (validate & initialize)
3. Pipeline Engine → LLM Integration (generate responses)
4. LLM Integration → WebSocket Stream → TUI (real-time display)
5. User Selection (TUI) → Server → Pipeline Engine (state update)
6. Pipeline Engine → Storage Layer (persist artifacts)
7. Repeat steps 3-6 for next pipeline step
```

### State Management Flow
```
1. Pipeline State Change → Event Store (immutable append)
2. Event Store → Artifact Manager (version artifacts)
3. Query Request → Query Engine (efficient retrieval)
4. Branch/Rewind → Artifact Manager (copy-on-write)
```

## 🎯 Design Principles

### 1. **Single Process Architecture**
- **Rationale**: Simplifies deployment and reduces complexity
- **Implementation**: Embedded FastAPI server within TUI process
- **Benefits**: No network configuration, simplified error handling

### 2. **Event Sourcing**
- **Rationale**: Complete audit trail and rewind/branch capabilities
- **Implementation**: Immutable event log in LMDB
- **Benefits**: Time travel debugging, branch exploration

### 3. **Library-First Design**
- **Rationale**: Modular, testable, reusable components
- **Implementation**: Each layer as standalone library
- **Benefits**: Independent testing, clear boundaries

### 4. **Async-First**
- **Rationale**: Non-blocking UI during LLM operations
- **Implementation**: asyncio throughout stack
- **Benefits**: Responsive UI, concurrent operations

### 5. **Real Dependencies**
- **Rationale**: Integration testing with actual services
- **Implementation**: No mocks, actual LLM APIs
- **Benefits**: Realistic testing, production confidence

## 🔗 Inter-Component Communication

### TUI ↔ Server Communication
```python
# WebSocket for streaming
async def stream_responses():
    async with websockets.connect("ws://localhost:8000/stream") as websocket:
        async for message in websocket:
            update_ui(json.loads(message))

# HTTP for control operations
async def select_response(response_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"/step/select", json={"response_id": response_id})
        return response.json()
```

### Server ↔ LLM Integration
```python
# Async streaming from multiple providers
async def execute_step(prompt: str, models: List[str]):
    tasks = []
    for model in models:
        task = asyncio.create_task(stream_from_model(model, prompt))
        tasks.append(task)
    
    async for model_name, chunk in merge_streams(tasks):
        await websocket.send_json({"model": model_name, "chunk": chunk})
```

### Pipeline Engine ↔ Storage
```python
# Event sourcing pattern
async def complete_step(pipeline_id: UUID, step_data: StepData):
    # Create immutable event
    event = StepCompletedEvent(
        pipeline_id=pipeline_id,
        step_name=step_data.name,
        responses=step_data.responses,
        user_selection=step_data.selection
    )
    
    # Persist to event store
    await event_store.append(pipeline_id, event)
    
    # Update query projections
    await update_pipeline_projection(pipeline_id, event)
```

## 📊 Performance Characteristics

### Response Times
- **Step Initiation**: <100ms (local LMDB query)
- **First Token**: <2s (LLM provider dependent)
- **Step Transition**: <200ms (event store append)
- **UI Updates**: <16ms (60fps target)

### Memory Usage
- **Base Application**: ~50MB
- **Per Active Pipeline**: ~10-20MB
- **Streaming Buffer**: ~5MB per concurrent LLM
- **Total Target**: <100MB under normal load

### Storage Efficiency
- **Artifacts**: ~100KB per LLM response
- **Complete Pipeline**: ~1-2MB including history
- **LMDB Overhead**: ~10% metadata overhead
- **Compression**: None (LMDB handles efficiency)

## 🔒 Error Handling Strategy

### Graceful Degradation
1. **Primary Provider Failure** → Automatic fallback to secondary
2. **All Providers Fail** → Local model fallback (if available)
3. **Network Issues** → Offline mode with cached responses
4. **Storage Errors** → Memory-only mode with export on exit

### Error Recovery Patterns
```python
@retry(max_attempts=3, backoff=exponential_backoff)
async def call_llm_with_fallback(prompt: str) -> str:
    for provider in provider_chain:
        try:
            return await provider.generate(prompt)
        except ProviderError:
            continue
    raise AllProvidersFailedError()
```

## 🧪 Testing Strategy

### Architecture Testing Layers
1. **Contract Tests**: API endpoint compliance
2. **Integration Tests**: Cross-component workflows
3. **Component Tests**: Individual layer testing
4. **End-to-End Tests**: Complete user journeys

### Test Data Flow
```
Test Input → TUI Simulation → Server Layer → Mock LLM Responses
    ↓              ↓               ↓              ↓
Assertions ← Storage Layer ← Pipeline Engine ← Response Handler
```

This architecture provides WriteIt with a robust, scalable foundation that maintains simplicity while supporting advanced features like real-time streaming, pipeline branching, and multi-provider AI integration.