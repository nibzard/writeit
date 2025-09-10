# WriteIt Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-09

## Active Technologies
- **Python 3.11+** + **FastAPI** + **Textual** + **LMDB** + **llm.datasette.io** (001-build-me-writeit)

## Project Structure
```
src/
├── models/          # Shared data models (Pipeline, Artifact, etc.)
├── storage/         # LMDB storage library with workspace awareness
├── workspace/       # Centralized workspace management (~/.writeit)
├── llm/            # LLM integration library
├── pipeline/       # Pipeline execution engine
├── server/         # FastAPI server
├── tui/            # Textual UI components
└── cli/            # Main entry points with workspace commands

tests/
├── contract/       # API contract tests
├── integration/    # End-to-end pipeline tests  
└── unit/          # Library unit tests

~/.writeit/         # Centralized storage (created by writeit init)
├── config.yaml     # Global settings
├── templates/      # Global pipeline templates
├── styles/         # Global style primers
├── workspaces/     # User workspaces
│   ├── default/    # Default workspace
│   └── project1/   # Example project workspace
└── cache/          # LLM response cache
```

## Commands
```bash
# Core WriteIt commands
writeit --version                    # Show version
writeit init [--migrate]             # Initialize ~/.writeit (with optional migration)

# Workspace Management (NEW - works from any directory!)
writeit workspace create <name>      # Create new workspace
writeit workspace list              # List all workspaces
writeit workspace use <name>        # Switch active workspace
writeit workspace info [name]       # Show workspace details
writeit workspace remove <name>     # Delete workspace

# Pipeline Operations
writeit list-pipelines              # List available pipelines  
writeit run <pipeline.yaml>         # Start TUI pipeline execution in active workspace
writeit run --global <pipeline>     # Use global pipeline template
writeit --workspace <name> run <pipeline>  # Use specific workspace

# Template & Style Validation
writeit validate <template-name>                # Validate templates/styles (workspace-aware, no .yaml needed)
writeit validate --type pipeline <template>     # Validate pipeline template
writeit validate --type style <primer>          # Validate style primer
writeit validate --detailed <template>          # Show detailed issues & suggestions
writeit validate --global <template>            # Only check global templates
writeit validate --local ./template             # Only check current directory

# Development commands (use uv run for local development)
uv run writeit init                             # Initialize for development
uv run writeit validate --detailed tech-article # Validate during development (no .yaml needed)
uv run writeit run quick-article                # Test pipelines
uv run pytest tests/               # Run all tests
uv run pytest tests/contract/      # Contract tests only
uv run pytest tests/integration/   # Integration tests only
uv run ruff check src/ tests/      # Linting
uv run mypy src/                   # Type checking
```

## Code Style
- **Library-first architecture**: Each feature as standalone library
- **TDD mandatory**: Tests before implementation, RED-GREEN-Refactor
- **Real dependencies**: No mocks, use actual LLM APIs and LMDB
- **Event sourcing patterns**: Immutable state with copy-on-write branching
- **Async-first**: Use asyncio for all I/O operations

## WriteIt-Specific Patterns

### Workspace-Aware Storage
```python
# Storage manager with workspace isolation
storage = StorageManager(workspace_manager, workspace_name)
storage.store_json("pipeline_run", run_data, db_name="pipelines")

# Workspace management
workspace = Workspace()  # Uses ~/.writeit by default
workspace.create_workspace("project1")
workspace.set_active_workspace("project1")
```

### Pipeline State Management
```python
# Immutable state transitions with workspace context
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

## Package Management

This project uses **uv** (Astral's fast Python package manager) instead of pip:

### Development Setup
```bash
# Install dependencies and sync environment
uv sync

# Add new dependencies
uv add package-name
uv add --dev dev-package-name

# Remove dependencies  
uv remove package-name

# Update dependencies
uv lock --upgrade

# Run commands with uv
uv run command-name
```

### Installation Methods
```bash
# Global tool installation
uv tool install writeit[openai,anthropic]

# Project-local installation
uv add writeit[openai,anthropic]

# From source (development)
git clone repo && cd repo
uv sync  # Installs all dependencies automatically
```

### Benefits of uv
- **10-100x faster** than pip for installs and dependency resolution
- **Unified tool** for package management, virtual environments, and Python versions
- **Better caching** with global dependency cache
- **Automatic virtual environment management**
- **Built-in dependency locking** with uv.lock
- **Cross-platform Python version management**

## Recent Changes
- 001-build-me-writeit: Added WriteIt LLM Article Pipeline TUI application with FastAPI backend, LMDB storage, multi-provider LLM support, real-time streaming, and event sourcing

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->