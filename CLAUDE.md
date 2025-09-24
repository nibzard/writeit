# WriteIt Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-01-15

## ⚠️ IMPORTANT: CI/CD DISABLED DURING DEVELOPMENT
**GitHub Actions are temporarily disabled** (workflows moved to `.github/workflows-disabled/`)  
**DO NOT use CI/CD or GitHub Actions during active development phase**  
This prevents interference with rapid development and testing cycles.

## Active Technologies
- **Python 3.12+** + **FastAPI** + **Textual** + **LMDB** + **llm.datasette.io**
- **WebSocket** + **aiohttp** + **Event Sourcing** + **LLM Caching** (Fully Implemented)

## Project Structure
```
src/
├── models/          # Shared data models (Pipeline, PipelineRun, StepExecution, etc.)
├── storage/         # LMDB storage library with workspace awareness
├── workspace/       # Centralized workspace management (~/.writeit)
├── llm/            # LLM integration library with caching and token tracking
│   ├── cache.py     # LLM response caching with workspace isolation
│   └── token_usage.py # Token usage tracking and analytics
├── pipeline/       # Pipeline execution engine ✅ FULLY IMPLEMENTED
│   ├── executor.py  # Core pipeline execution with async LLM calls
│   └── events.py    # Event sourcing for immutable state management
├── server/         # FastAPI server ✅ FULLY IMPLEMENTED
│   ├── app.py      # REST API + WebSocket endpoints
│   └── client.py   # Client library for TUI/CLI integration
├── tui/            # Textual UI components ✅ DDD INTEGRATED
│   ├── pipeline_runner.py      # Legacy TUI runner (external dependencies)
│   └── modern_pipeline_runner.py  # Modern DDD-integrated TUI runner
└── cli/            # Main entry points with workspace commands

tests/
├── contract/       # API contract tests
├── integration/    # End-to-end pipeline tests ✅ COMPREHENSIVE
└── unit/          # Library unit tests

~/.writeit/         # Centralized storage (created by writeit init)
├── config.yaml     # Global settings
├── templates/      # Global pipeline templates
├── styles/         # Global style primers
├── workspaces/     # User workspaces with isolated LMDB databases
│   ├── default/    # Default workspace
│   └── project1/   # Example project workspace
└── cache/          # LLM response cache (per-workspace)
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
writeit run <pipeline.yaml>         # Start CLI pipeline execution in active workspace (default)
writeit run <pipeline> --tui        # Start TUI pipeline execution for rich interactive mode
writeit run --global <pipeline>     # Use global pipeline template
writeit --workspace <name> run <pipeline>  # Use specific workspace

# Server Operations (NEW - Backend API)
writeit server start               # Start FastAPI server (port 8000)
writeit server stop                # Stop running server
writeit server status              # Check server health

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
uv run writeit run quick-article                # Test pipelines (CLI mode by default)
uv run writeit run quick-article --tui          # Test pipelines in TUI mode
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

### Modern TUI with DDD Integration
The modern TUI (`ModernPipelineRunnerApp`) provides a rich, interactive interface with full DDD integration:

```python
from writeit.tui import ModernPipelineRunnerApp, TUIExecutionConfig
from pathlib import Path
import asyncio

# Configure TUI execution
config = TUIExecutionConfig(
    auto_save_interval=30,      # Auto-save every 30 seconds
    max_log_entries=1000,        # Keep last 1000 log entries
    enable_animations=True,      # Enable smooth UI animations
    show_token_usage=True,       # Display token usage metrics
    show_performance=True        # Show performance analytics
)

# Run pipeline with modern TUI
async def run_pipeline():
    await run_modern_pipeline_tui(
        pipeline_path=Path("pipeline.yaml"),
        workspace_name="default",
        config=config
    )

# Key features:
# - Real-time execution progress with DDD services
# - Interactive step execution with feedback
# - Token usage tracking and analytics
# - Workspace-aware execution
# - Comprehensive error handling
# - Export and restart capabilities
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

## Core Architecture Components ✅ FULLY IMPLEMENTED

### Pipeline Execution Engine (`src/writeit/pipeline/`)
- **PipelineExecutor**: Async execution engine with LLM integration and caching
- **Event Sourcing**: Immutable state management with copy-on-write branching  
- **Step Execution**: Multi-step workflow with progress tracking and error handling
- **Template Rendering**: Dynamic prompt generation with context variable substitution

### FastAPI Server (`src/writeit/server/`)
- **REST API**: Complete CRUD operations for pipelines, runs, and workspaces
- **WebSocket Streaming**: Real-time execution updates and bi-directional communication
- **Multi-tenant**: Workspace-aware execution with isolated storage
- **Error Handling**: Comprehensive error management with helpful suggestions

### LLM Response Caching (`src/writeit/llm/`)
- **Smart Caching**: Context-aware caching with workspace isolation
- **Two-tier Storage**: Memory + persistent LMDB caching with LRU eviction
- **Cache Analytics**: Hit/miss tracking and performance optimization
- **TTL Management**: Configurable cache expiration and cleanup

### Event Sourcing System (`src/writeit/pipeline/events.py`)
- **Immutable State**: Copy-on-write state transitions with event replay
- **Event Store**: Persistent event logging with sequence numbering
- **State Snapshots**: Performance optimization for large event streams
- **Branch Support**: Parallel execution branches with state isolation

## API Endpoints

### Pipeline Management
```
POST /api/pipelines          # Create pipeline from YAML file
GET  /api/pipelines/{id}     # Get pipeline configuration
```

### Pipeline Execution  
```
POST /api/runs               # Create new pipeline run
POST /api/runs/{id}/execute  # Execute pipeline run
GET  /api/runs/{id}          # Get run status and results
GET  /api/workspaces/{name}/runs # List runs in workspace
```

### Real-time Communication
```
WS   /ws/{run_id}           # WebSocket for real-time execution updates
```

## Pipeline YAML Structure

```yaml
metadata:
  name: "Article Pipeline"
  description: "Generate structured articles"
  version: "1.0.0"

defaults:
  model: "gpt-4o-mini"
  
inputs:
  topic:
    type: text
    label: "Article Topic"
    required: true
    placeholder: "Enter topic..."
  
  style:
    type: choice
    label: "Writing Style"
    options:
      - {label: "Formal", value: "formal"}
      - {label: "Casual", value: "casual"}
    default: "formal"

steps:
  outline:
    name: "Create Outline"
    description: "Generate article structure"
    type: llm_generate
    prompt_template: |
      Create an outline for {{ inputs.topic }} 
      in {{ inputs.style }} style.
    model_preference: ["{{ defaults.model }}"]
    
  content:
    name: "Write Article"
    description: "Generate full content"
    type: llm_generate
    prompt_template: |
      Based on outline: {{ steps.outline }}
      Write complete article about {{ inputs.topic }}.
    depends_on: ["outline"]
```

## Development Commands

```bash
# Start development server
uv run uvicorn writeit.server.app:app --reload --port 8000

# Run comprehensive tests
uv run pytest tests/ -v

# Run specific test categories
uv run pytest tests/integration/ -v    # Integration tests
uv run pytest tests/unit/ -v           # Unit tests
uv run pytest tests/contract/ -v       # Contract tests

# Type checking and linting
uv run mypy src/
uv run ruff check src/ tests/

# Test pipeline execution
uv run python -c "
from writeit.pipeline import PipelineExecutor
from writeit.server import PipelineClient
# Test components
"
```

## Recent Changes
- **2025-01-15**: ✅ MAJOR RELEASE - Complete backend implementation
  - Implemented core pipeline execution engine with async LLM integration
  - Added FastAPI server with REST API and WebSocket streaming  
  - Implemented event sourcing for immutable state management
  - Added comprehensive LLM response caching with workspace isolation
  - Created client library for TUI/server communication
  - Added extensive integration test suite with real pipeline execution
  - Updated dependencies and async test infrastructure

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->