# WriteIt Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-09

## Active Technologies
- **Python 3.11+** + **FastAPI** + **Textual** + **LMDB** + **llm.datasette.io** (001-build-me-writeit)

## Project Structure
```
src/
├── models/          # Shared data models (Pipeline, Artifact, etc.)
├── storage/         # LMDB storage library  
├── llm/            # LLM integration library
├── pipeline/       # Pipeline execution engine
├── server/         # FastAPI server
├── tui/            # Textual UI components
└── cli/            # Main entry points

tests/
├── contract/       # API contract tests
├── integration/    # End-to-end pipeline tests  
└── unit/          # Library unit tests

pipelines/          # Example pipeline configurations
styles/            # Writing style primers
```

## Commands
```bash
# Core WriteIt commands
writeit --version                    # Show version
writeit init <workspace>             # Initialize workspace
writeit list-pipelines              # List available pipelines  
writeit run <pipeline.yaml>         # Start TUI pipeline execution

# Development commands
pytest tests/                       # Run all tests
pytest tests/contract/             # Contract tests only
pytest tests/integration/         # Integration tests only
```

## Code Style
- **Library-first architecture**: Each feature as standalone library
- **TDD mandatory**: Tests before implementation, RED-GREEN-Refactor
- **Real dependencies**: No mocks, use actual LLM APIs and LMDB
- **Event sourcing patterns**: Immutable state with copy-on-write branching
- **Async-first**: Use asyncio for all I/O operations

## WriteIt-Specific Patterns

### Pipeline State Management
```python
# Immutable state transitions
current_state = load_pipeline_state(txn, pipeline_id)
new_state = current_state.complete_step(step, responses, selection, feedback)
store_pipeline_state(txn, pipeline_id, new_state)
```

### LLM Integration
```python
# Multi-provider with fallbacks
model = llm.get_async_model(model_preference)
async for chunk in model.prompt(prompt, stream=True):
    await websocket.send_json({"content": chunk, "type": "token"})
```

### TUI Real-time Updates
```python
# Textual reactive updates
class PipelineView(Widget):
    responses: Reactive[List[str]] = Reactive([])
    
    def watch_responses(self) -> None:
        self.update_response_panels()
```

## Recent Changes
- 001-build-me-writeit: Added WriteIt LLM Article Pipeline TUI application with FastAPI backend, LMDB storage, multi-provider LLM support, real-time streaming, and event sourcing

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->