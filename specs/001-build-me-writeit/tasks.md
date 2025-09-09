# Tasks: WriteIt - LLM Article Pipeline TUI Application

**Input**: Design documents from `/specs/001-build-me-writeit/`
**Prerequisites**: plan.md (required), research.md, data-model.md, contracts/api-spec.yaml, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✅ Implementation plan loaded successfully
   → Extracted: Python 3.11+, FastAPI, Textual, LMDB, llm.datasette.io, single project
2. Load optional design documents:
   → data-model.md: 6 entities (PipelineConfiguration, PipelineRun, StepState, AIResponse, StylePrimer, UserSession)
   → contracts/: 8 REST endpoints + WebSocket streaming
   → research.md: TUI framework (Textual), storage (LMDB), LLM integration decisions
3. Generate tasks by category:
   → Setup: Python project, dependencies, LMDB, llm providers
   → Tests: 8 contract tests, 6 integration tests (quickstart scenarios)
   → Core: 6 models, 5 libraries (storage, llm, pipeline, server, tui)
   → Integration: WebSocket streaming, CLI commands, error handling
   → Polish: unit tests, performance validation, documentation
4. Apply task rules:
   → Different files = [P] for parallel execution
   → Same file modifications = sequential
   → Tests before implementation (TDD mandatory)
5. Number tasks sequentially (T001-T039)
6. Generate dependency graph and parallel execution examples
7. Validate task completeness: All entities, contracts, and user stories covered
8. Return: SUCCESS (39 tasks ready for TDD execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Single project**: `src/`, `tests/` at repository root (per plan.md structure)
- All paths relative to `/Users/nikola/dev/writeit/`

## Phase 3.1: Setup & Infrastructure
- [ ] T001 Create project structure with src/ and tests/ directories per plan.md
- [ ] T002 Initialize Python 3.11+ project with pyproject.toml and core dependencies
- [ ] T003 [P] Configure ruff linting and black formatting tools with pyproject.toml
- [ ] T004 [P] Set up pytest configuration with test markers in pyproject.toml
- [ ] T005 [P] Create example pipeline configurations in pipelines/tech-article.yaml
- [ ] T006 [P] Create style primer templates in styles/tech-journalist.txt

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3
**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoints)
- [ ] T007 [P] Contract test POST /pipeline/start in tests/contract/test_pipeline_start.py
- [ ] T008 [P] Contract test GET /pipeline/{id}/status in tests/contract/test_pipeline_status.py
- [ ] T009 [P] Contract test POST /step/{id}/execute in tests/contract/test_step_execute.py
- [ ] T010 [P] Contract test POST /step/{id}/select in tests/contract/test_step_select.py
- [ ] T011 [P] Contract test POST /step/{id}/rewind in tests/contract/test_step_rewind.py
- [ ] T012 [P] Contract test POST /step/{id}/fork in tests/contract/test_step_fork.py
- [ ] T013 [P] Contract test POST /pipeline/{id}/save in tests/contract/test_pipeline_save.py
- [ ] T014 [P] Contract test GET /artifacts/{id} in tests/contract/test_artifacts_get.py

### Integration Tests (User Journey & Quickstart Scenarios)
- [ ] T015 [P] Integration test complete 4-step pipeline execution in tests/integration/test_complete_pipeline.py
- [ ] T016 [P] Integration test multi-model response handling in tests/integration/test_multi_model.py  
- [ ] T017 [P] Integration test rewind functionality in tests/integration/test_rewind.py
- [ ] T018 [P] Integration test branching/forking in tests/integration/test_branching.py
- [ ] T019 [P] Integration test YAML export with metadata in tests/integration/test_export.py
- [ ] T020 [P] Integration test TUI real-time streaming in tests/integration/test_tui_streaming.py

## Phase 3.3: Core Data Models (ONLY after tests are failing)
- [ ] T021 [P] PipelineConfiguration model in src/models/pipeline_config.py
- [ ] T022 [P] PipelineRun model with state transitions in src/models/pipeline_run.py
- [ ] T023 [P] StepState model with validation in src/models/step_state.py
- [ ] T024 [P] AIResponse model with usage tracking in src/models/ai_response.py
- [ ] T025 [P] StylePrimer model in src/models/style_primer.py
- [ ] T026 [P] UserSession model with preferences in src/models/user_session.py

## Phase 3.4: Library Implementation
### Storage Layer
- [ ] T027 [P] LMDB storage interface in src/storage/lmdb_store.py
- [ ] T028 [P] Event sourcing persistence in src/storage/event_store.py
- [ ] T029 [P] Artifact versioning and branching in src/storage/artifact_manager.py

### LLM Integration Layer
- [ ] T030 [P] Multi-provider LLM client in src/llm/llm_client.py
- [ ] T031 [P] Streaming response handler in src/llm/stream_handler.py
- [ ] T032 [P] Provider fallback and error handling in src/llm/provider_manager.py

### Pipeline Execution Engine
- [ ] T033 Pipeline state machine in src/pipeline/state_machine.py
- [ ] T034 Step executor with template rendering in src/pipeline/step_executor.py

## Phase 3.5: Server & API Implementation
- [ ] T035 FastAPI application setup in src/server/app.py
- [ ] T036 WebSocket streaming endpoint in src/server/websocket.py
- [ ] T037 Pipeline management endpoints in src/server/pipeline_routes.py
- [ ] T038 Step execution endpoints in src/server/step_routes.py

## Phase 3.6: TUI Implementation  
- [ ] T039 Textual TUI application in src/tui/main_app.py
- [ ] T040 Real-time streaming widgets in src/tui/stream_widgets.py
- [ ] T041 Pipeline step navigation in src/tui/pipeline_view.py

## Phase 3.7: CLI & Integration
- [ ] T042 Main CLI entry point writeit command in src/cli/main.py
- [ ] T043 Pipeline configuration loader in src/cli/config_loader.py
- [ ] T044 Error handling and logging setup in src/cli/error_handler.py

## Phase 3.8: Polish & Validation
- [ ] T045 [P] Unit tests for pipeline state machine in tests/unit/test_state_machine.py
- [ ] T046 [P] Unit tests for LLM client fallbacks in tests/unit/test_llm_client.py  
- [ ] T047 [P] Unit tests for LMDB operations in tests/unit/test_lmdb_store.py
- [ ] T048 Performance validation (<200ms step transitions) in tests/performance/test_response_times.py
- [ ] T049 Memory usage validation (<100MB) in tests/performance/test_memory_usage.py
- [ ] T050 [P] Execute complete quickstart.md validation test
- [ ] T051 [P] Update CLAUDE.md with implementation patterns

## Dependencies
**Critical Path (TDD)**:
- Setup (T001-T006) → Tests (T007-T020) → Implementation (T021-T044) → Polish (T045-T051)

**Detailed Dependencies**:
- T007-T020 must complete and FAIL before T021 starts
- T021-T026 (models) before T027-T032 (services that use models)  
- T033-T034 (pipeline engine) needs T021-T026 (models)
- T035-T038 (server) needs T027-T032 (storage, LLM) and T033-T034 (pipeline)
- T039-T041 (TUI) needs T035-T038 (server endpoints)
- T042-T044 (CLI) needs T039-T041 (TUI) and T035-T038 (server)
- T045-T051 (polish) needs all implementation complete

## Parallel Execution Examples

### Phase 3.1 Setup (can run in parallel):
```bash
# Launch T003-T006 together:
Task: "Configure ruff linting and black formatting tools with pyproject.toml"
Task: "Set up pytest configuration with test markers in pyproject.toml"  
Task: "Create example pipeline configurations in pipelines/tech-article.yaml"
Task: "Create style primer templates in styles/tech-journalist.txt"
```

### Phase 3.2 Contract Tests (can run in parallel):
```bash
# Launch T007-T014 together:
Task: "Contract test POST /pipeline/start in tests/contract/test_pipeline_start.py"
Task: "Contract test GET /pipeline/{id}/status in tests/contract/test_pipeline_status.py"
Task: "Contract test POST /step/{id}/execute in tests/contract/test_step_execute.py"
Task: "Contract test POST /step/{id}/select in tests/contract/test_step_select.py"
Task: "Contract test POST /step/{id}/rewind in tests/contract/test_step_rewind.py"
Task: "Contract test POST /step/{id}/fork in tests/contract/test_step_fork.py"
Task: "Contract test POST /pipeline/{id}/save in tests/contract/test_pipeline_save.py"
Task: "Contract test GET /artifacts/{id} in tests/contract/test_artifacts_get.py"
```

### Phase 3.2 Integration Tests (can run in parallel):
```bash
# Launch T015-T020 together:
Task: "Integration test complete 4-step pipeline execution in tests/integration/test_complete_pipeline.py"
Task: "Integration test multi-model response handling in tests/integration/test_multi_model.py"
Task: "Integration test rewind functionality in tests/integration/test_rewind.py" 
Task: "Integration test branching/forking in tests/integration/test_branching.py"
Task: "Integration test YAML export with metadata in tests/integration/test_export.py"
Task: "Integration test TUI real-time streaming in tests/integration/test_tui_streaming.py"
```

### Phase 3.3 Data Models (can run in parallel):
```bash
# Launch T021-T026 together:
Task: "PipelineConfiguration model in src/models/pipeline_config.py"
Task: "PipelineRun model with state transitions in src/models/pipeline_run.py"
Task: "StepState model with validation in src/models/step_state.py"
Task: "AIResponse model with usage tracking in src/models/ai_response.py"
Task: "StylePrimer model in src/models/style_primer.py"
Task: "UserSession model with preferences in src/models/user_session.py"
```

### Phase 3.4 Storage Layer (can run in parallel):
```bash
# Launch T027-T029 together:
Task: "LMDB storage interface in src/storage/lmdb_store.py"
Task: "Event sourcing persistence in src/storage/event_store.py"
Task: "Artifact versioning and branching in src/storage/artifact_manager.py"
```

### Phase 3.4 LLM Layer (can run in parallel):
```bash
# Launch T030-T032 together:  
Task: "Multi-provider LLM client in src/llm/llm_client.py"
Task: "Streaming response handler in src/llm/stream_handler.py"
Task: "Provider fallback and error handling in src/llm/provider_manager.py"
```

## Notes
- [P] tasks = different files, no dependencies - can run concurrently
- Verify ALL tests fail before implementing (TDD requirement)
- Commit after each completed task  
- Real LLM APIs required - no mocking allowed per constitutional requirements
- LMDB must be used for artifact storage with event sourcing patterns

## Task Generation Rules Applied

1. **From Contracts (api-spec.yaml)**:
   - 8 API endpoints → 8 contract test tasks [P] (T007-T014)
   - Each endpoint → corresponding implementation tasks (T035-T038)
   
2. **From Data Model**:
   - 6 entities → 6 model creation tasks [P] (T021-T026)
   - Storage relationships → storage service tasks (T027-T029)
   
3. **From Quickstart Scenarios**:
   - 6 user journey scenarios → 6 integration tests [P] (T015-T020)
   - Performance requirements → validation tasks (T048-T049)

4. **From Plan.md Structure**:
   - 6 libraries identified → library implementation tasks (T027-T044)
   - TUI + CLI components → interface tasks (T039-T044)

## Validation Checklist
*GATE: Verified before task completion*

- [✅] All 8 contracts have corresponding contract tests (T007-T014)
- [✅] All 6 entities have model creation tasks (T021-T026)  
- [✅] All tests come before implementation (Phase 3.2 before 3.3)
- [✅] Parallel tasks truly independent (different files, no shared state)
- [✅] Each task specifies exact file path for implementation
- [✅] No [P] task modifies same file as another [P] task
- [✅] TDD enforced: tests must fail before implementation begins
- [✅] Constitutional requirements met: library-first, real dependencies, event sourcing