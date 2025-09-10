# Agent Development Guide for WriteIt

## Commands
```bash
# Build/Test/Lint (use uv for all commands)
uv run pytest tests/                    # Run all tests
uv run pytest tests/unit/test_specific.py::test_function  # Run single test
uv run pytest tests/contract/           # Contract tests only
uv run pytest tests/integration/        # Integration tests only
uv run ruff check src/ tests/           # Linting
uv run mypy src/                        # Type checking
uv run writeit init                     # Initialize for development
uv run writeit validate --detailed <template>  # Validate templates

# Pipeline execution
uv run writeit run <pipeline-name>      # Run in TUI mode (interactive)
uv run writeit run <pipeline-name> --cli  # Run in CLI mode (simple prompts)
uv run writeit pipeline list            # List available pipelines
```

## Code Style
- **Package manager**: Use `uv` (not pip) for all package operations
- **Architecture**: Library-first design, each feature as standalone library in `src/writeit/`
- **Testing**: TDD mandatory - write tests first, use real dependencies (no mocks)
- **Async**: Use asyncio for all I/O operations, prefer async/await
- **Types**: Full type hints required, use Pydantic models for data structures
- **Imports**: Group by standard lib, third-party, then local with workspace-aware patterns
- **Error handling**: Use proper exception handling with workspace context
- **State management**: Immutable state with event sourcing patterns
- **Code structure**: Follow existing patterns in `storage/`, `llm/`, `pipeline/`, `tui/`, `cli/`
