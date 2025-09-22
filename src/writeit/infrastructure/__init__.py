"""
Infrastructure Layer - External System Adapters

This layer contains adapters that connect the core domain logic
to external systems and frameworks.

## Responsibilities

- Implement domain repository interfaces with concrete storage
- Provide framework-specific adapters (FastAPI, CLI, TUI)
- Handle external system integration (LLM APIs, file system)
- Manage infrastructure concerns (logging, monitoring, security)

## Modules

### Persistence (writeit.infrastructure.persistence)
- LMDB storage implementation
- File system storage implementation
- Cache storage implementation
- Transaction management

### LLM (writeit.infrastructure.llm)
- OpenAI API adapter
- Anthropic API adapter
- Local LLM adapter
- Provider health monitoring

### Web (writeit.infrastructure.web)
- FastAPI application setup
- REST endpoint implementations
- WebSocket handlers
- HTTP middleware

### CLI (writeit.infrastructure.cli)
- Command-line interface adapters
- Output formatting
- Error handling for CLI context
- Progress reporting

## Design Principles

1. **Dependency Inversion**: Infrastructure depends on domain abstractions
2. **Single Responsibility**: Each adapter has one external system concern
3. **Error Translation**: Convert infrastructure errors to domain errors
4. **Configuration**: External configuration for all infrastructure components
"""