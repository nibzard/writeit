# Research Findings: WriteIt LLM Article Pipeline

**Phase 0 Research Completion** | **Date**: 2025-09-08

## TUI Framework Selection

**Decision**: Textual framework

**Rationale**: 
- Native async architecture built on asyncio - perfect for real-time LLM streaming
- Reactive programming model with live UI updates without blocking
- Modern CSS-like styling and React-inspired component system
- Production-ready with cross-platform terminal compatibility
- Ideal widget ecosystem: real-time logs, progress bars, multi-panel layouts, keyboard shortcuts

**Alternatives considered**:
- **Rich**: Excellent for beautiful output but limited interactivity - better as a component
- **prompt_toolkit**: Great for CLI prompts but complex for full TUI applications  
- **urwid**: Battle-tested but dated API design and verbose syntax

**Integration patterns**: Seamless FastAPI WebSocket integration with Textual's async architecture enables real-time token-by-token streaming from LLM APIs with multi-panel layouts and reactive UI updates.

## LMDB Storage Architecture

**Decision**: Hierarchical Key Schema with MVCC Transaction Management

**Rationale**:
- LMDB's built-in MVCC provides versioning without overhead
- Lexicographically sorted keys enable efficient prefix-based queries
- Memory-mapped architecture offers zero-copy performance
- Parent-child transactions support complex branching with rollback safety
- Single writer, multiple readers design aligns with pipeline execution patterns

**Alternatives considered**:
- JSON document storage (rejected due to atomic update limitations)
- Separate metadata/content stores (rejected due to consistency challenges)  
- Git-like object storage (rejected as overly complex for linear pipelines)

**Implementation patterns**: 
- **Key Design**: Hierarchical paths like `/p/{pipeline_id}/s/{step_num}/{version}/a/{artifact_id}`
- **Transactions**: Atomic operations for branching, rewinding, and artifact storage
- **Performance**: ~100KB per artifact, 200 concurrent readers, 3-4x write speed with batch operations

## FastAPI WebSocket Streaming

**Decision**: Hybrid AsyncWebSocket + ConnectionPool Pattern

**Rationale**:
- Real-time requirements for WriteIt's 4-step pipeline need immediate token delivery
- Supporting multiple AI providers requires provider abstraction with unified streaming
- Human-in-the-loop design needs robust session state management for feedback/interruption
- TUI integration requires minimal latency and efficient connection lifecycle

**Alternatives considered**:
- Server-Sent Events (insufficient for bidirectional communication)
- HTTP Streaming Response (no real-time user interaction)
- Raw TCP Sockets (over-engineered, complex error handling)

**Implementation patterns**:
- **ConnectionManager** with per-session isolation
- **AsyncLLMStream** handlers with concurrent model support  
- **Circuit Breaker** pattern for error resilience
- **Token Buffer** with backpressure management

## LLM Integration Strategy

**Decision**: Unified LLM Library Integration with Custom Fallback Layer

**Rationale**:
- llm.datasette.io provides consistent API across OpenAI, Anthropic, local models through plugins
- Built-in configuration management via `llm keys set` and environment variables
- Native async support with `llm.get_async_model()` and streaming patterns
- Built-in SQLite logging with token usage tracking
- Extensible plugin system for custom model integrations

**Alternatives considered**:
- Direct Provider APIs (would require building unified interfaces from scratch)
- LangChain (more complex, heavyweight for WriteIt's focused use case)
- Custom Multi-Provider Library (high development overhead, less mature)
- OpenAI-Only Integration (limited to single provider)

**Implementation patterns**:
- Model optimization per pipeline step (fast models for angles, quality models for drafts)
- Automatic fallback chains with provider health monitoring
- Cost tracking across pipeline runs with per-model pricing
- Configuration-driven model selection with environment-based API keys

## Pipeline State Management

**Decision**: Event Sourcing with LMDB + Immutable State Trees

**Rationale**:
- Perfect fit with LMDB's MVCC model and copy-on-write semantics
- WriteIt's 4-step linear pipeline maps to state machine with checkpoints
- Event sourcing provides complete audit trails for human-in-the-loop decisions
- Copy-on-write enables efficient branching without duplicating data
- LMDB's MVCC allows concurrent pipeline executions with consistency

**Alternatives considered**:
- Pure State Machine (too limited for versioning/branching)
- Git-like Object Database (over-engineered, complex implementation)
- Append-Only Log (read performance issues, complex compaction)
- Traditional RDBMS (architectural mismatch with LMDB)

**Implementation patterns**:
- **State Structure**: Immutable pipeline states with copy-on-write step sharing
- **Transactions**: Atomic step completion and branching operations
- **Branching**: Parent-child relationships with shared immutable history
- **Concurrency**: Application-level pipeline locking with LMDB's single-writer semantics

## Technical Architecture Summary

The research confirms WriteIt's architecture as a single Python application with:

1. **TUI Layer**: Textual framework with async WebSocket client for real-time streaming
2. **Server Layer**: Embedded FastAPI server with WebSocket endpoints for internal communication  
3. **LLM Layer**: llm.datasette.io with multi-provider support and fallback strategies
4. **Storage Layer**: LMDB with event sourcing and immutable state trees
5. **Pipeline Layer**: State machine with copy-on-write branching and rewind capabilities

This architecture provides the foundation for WriteIt's core requirements:
- Real-time LLM streaming to TUI
- Human-in-the-loop feedback at each pipeline step
- Complete artifact history with rewind/branching
- Multi-provider LLM support with fallbacks
- Efficient storage with versioning and concurrent access

All research findings support the constitutional requirements of simplicity, library-first architecture, and test-driven development patterns.