# Implementation Plan: WriteIt - LLM Article Pipeline TUI Application

**Branch**: `001-build-me-writeit` | **Date**: 2025-09-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-build-me-writeit/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✅ Feature spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✅ Detected Python TUI application with FastAPI backend
   → ❗ Need clarification on AI providers, storage preferences, multi-user support
3. Evaluate Constitution Check section below
   → ✅ Initial check shows good simplicity, needs library-first verification
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → 📋 Research TUI frameworks, LLM integration, LMDB patterns
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
6. Re-evaluate Constitution Check section
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
WriteIt is a minimalist TUI application that transforms raw content into polished articles through a 4-step LLM pipeline (angles → outline → draft → polish). The system provides human-in-the-loop feedback at each checkpoint, supporting multiple AI models, real-time streaming, and complete artifact history with rewind/branching capabilities.

## Technical Context
**Language/Version**: Python 3.11+  
**Primary Dependencies**: FastAPI, Textual, LMDB, llm.datasette.io, Pydantic, PyYAML  
**Storage**: LMDB for artifacts + YAML files for pipeline configs and exports  
**Testing**: pytest with real LLM integration tests  
**Target Platform**: Linux/macOS terminals, Windows terminal support  
**Project Type**: single - TUI client + embedded FastAPI server  
**Performance Goals**: <200ms step transitions, real-time LLM streaming, <100MB memory usage  
**Constraints**: Must work offline (local models), graceful degradation for network issues  
**Scale/Scope**: Single user, multiple concurrent pipelines, 1000+ saved artifacts per user

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Simplicity**:
- Projects: 1 (single TUI app with embedded server)
- Using framework directly? ✅ (Textual for TUI, FastAPI for server)
- Single data model? ✅ (shared models for TUI/server)
- Avoiding patterns? ✅ (no Repository/UoW, direct LMDB access)

**Architecture**:
- EVERY feature as library? 📋 (need to verify: storage, pipeline, llm, tui libraries)
- Libraries listed: [to be defined in Phase 1]
- CLI per library: [to be designed with --help/--version/--format]
- Library docs: llms.txt format planned? 📋

**Testing (NON-NEGOTIABLE)**:
- RED-GREEN-Refactor cycle enforced? 📋 (will enforce during implementation)
- Git commits show tests before implementation? 📋
- Order: Contract→Integration→E2E→Unit strictly followed? 📋
- Real dependencies used? ✅ (actual LLM APIs, no mocking)
- Integration tests for: new libraries, contract changes, shared schemas? 📋
- FORBIDDEN: Implementation before test, skipping RED phase ✅

**Observability**:
- Structured logging included? 📋 (plan for pipeline execution logs)
- Frontend logs → backend? N/A (single process)
- Error context sufficient? 📋

**Versioning**:
- Version number assigned? 📋 (0.1.0 for initial version)
- BUILD increments on every change? 📋
- Breaking changes handled? 📋 (pipeline format migration plan)

## Project Structure

### Documentation (this feature)
```
specs/001-build-me-writeit/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Single project structure
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

**Structure Decision**: Option 1 (single project) - TUI app with embedded FastAPI server for internal communication

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - Research Textual vs other Python TUI frameworks
   - Best practices for FastAPI WebSocket streaming
   - LMDB usage patterns for versioned artifacts
   - llm.datasette.io integration and model management
   - Pipeline state management and branching strategies

2. **Generate and dispatch research agents**:
   ```
   Task: "Research Textual framework for real-time streaming TUI applications"
   Task: "Research LMDB best practices for artifact versioning and branching"
   Task: "Research FastAPI WebSocket streaming patterns for LLM responses"
   Task: "Research llm.datasette.io integration with multiple AI providers"
   Task: "Research pipeline state management for rewind/branch operations"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Pipeline Configuration (YAML structure)
   - Pipeline Run (execution instance) 
   - Step Artifact (individual LLM responses)
   - Article (final output with history)
   - Style Primer (writing guidelines)
   - User Session (active state)

2. **Generate API contracts** from functional requirements:
   - Pipeline Management: POST /pipeline/start, GET /pipeline/{id}/status
   - Step Execution: POST /step/{id}/execute, WebSocket /step/{id}/stream
   - History/Branching: POST /step/{id}/rewind, POST /step/{id}/fork
   - Persistence: POST /pipeline/{id}/save, GET /artifacts/{id}
   - Output OpenAPI schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint group
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Complete 4-step pipeline execution
   - Multi-model response handling
   - Rewind/branch functionality
   - Style consistency validation
   - YAML export with metadata

5. **Update agent file incrementally** (O(1) operation):
   - Run `/scripts/update-agent-context.sh claude`
   - Add WriteIt-specific context and patterns
   - Include pipeline patterns and TUI conventions

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, CLAUDE.md

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models → Storage → LLM → Pipeline → Server → TUI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 30-35 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*No constitutional violations identified that require justification*

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [✅] Phase 0: Research complete (/plan command)
- [✅] Phase 1: Design complete (/plan command)
- [✅] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [✅] Initial Constitution Check: PASS
- [✅] Post-Design Constitution Check: PASS
- [✅] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*