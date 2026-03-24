# Tasks: Trace Ingestion Adapters

**Input**: Design documents from `/specs/005-trace-ingestion-adapters/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by adapter (user story) to enable independent implementation and testing of each adapter.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which adapter this task belongs to (e.g., US1=OTel, US2=LangChain, etc.)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create ingestion module directory at src/agenteval/ingestion/
- [X] T002 Create test directory at tests/ingestion/
- [X] T003 Create test fixtures directory at tests/ingestion/fixtures/
- [X] T004 Add CLI entry point to pyproject.toml: agenteval-ingest → agenteval.ingestion.cli:main

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY adapter can be implemented

**⚠️ CRITICAL**: No adapter work can begin until this phase is complete

- [X] T005 Define TraceAdapter Protocol in src/agenteval/ingestion/base.py with can_handle(), convert(), validate_mapping() methods
- [X] T006 Create adapter registry in src/agenteval/ingestion/__init__.py with auto_detect_adapter() function
- [X] T007 Implement file size validation in src/agenteval/ingestion/base.py: check_file_size() with 10MB soft/50MB hard limits
- [X] T008 Implement validation strategy helpers in src/agenteval/ingestion/base.py: fail_fast_validator(), collect_warnings()
- [X] T009 Create CLI argument parser in src/agenteval/ingestion/cli.py with --adapter, --output, --output-dir, --mapping, --dry-run, --verbose flags
- [X] T010 Implement bulk ingestion coordinator in src/agenteval/ingestion/cli.py with progress bar (tqdm) and error summary
- [X] T011 Create common adapter utilities in src/agenteval/ingestion/base.py: parse_timestamp(), map_step_type(), validate_trace_output()

**Checkpoint**: Foundation ready - adapter implementation can now begin in parallel

---

## Phase 3: OpenTelemetry Adapter (Priority: P1) 🎯 MVP

**Goal**: Enable ingestion of OpenTelemetry OTLP JSON traces

**Independent Test**: Convert an OTel trace fixture and validate against trace schema

### Tests for OpenTelemetry Adapter

- [X] T012 [P] [US1] Create OTel fixture at tests/ingestion/fixtures/otel_trace.json with nested spans and attributes
- [X] T013 [P] [US1] Unit test for OTelAdapter.can_handle() in tests/ingestion/test_otel.py: verify detection logic
- [X] T014 [P] [US1] Unit test for OTelAdapter.convert() in tests/ingestion/test_otel.py: verify span-to-step conversion
- [X] T015 [P] [US1] Unit test for nested span flattening in tests/ingestion/test_otel.py
- [X] T016 [P] [US1] Error handling test for malformed OTel trace in tests/ingestion/test_otel.py

### Implementation for OpenTelemetry Adapter

- [X] T017 [US1] Implement OTelAdapter class in src/agenteval/ingestion/otel.py with Protocol methods
- [X] T018 [US1] Implement can_handle() to detect resourceSpans structure in src/agenteval/ingestion/otel.py
- [X] T019 [US1] Implement span attribute mapping (SPAN_KIND_TO_STEP_TYPE) in src/agenteval/ingestion/otel.py
- [X] T020 [US1] Implement span hierarchy flattening logic in src/agenteval/ingestion/otel.py
- [X] T021 [US1] Implement timestamp conversion (nanos to ISO8601) in src/agenteval/ingestion/otel.py
- [X] T022 [US1] Register OTelAdapter in src/agenteval/ingestion/__init__.py

**Checkpoint**: OTel adapter functional - can convert OTel traces end-to-end

---

## Phase 4: LangChain Adapter (Priority: P2)

**Goal**: Enable ingestion of LangChain/LangSmith run tree JSON traces

**Independent Test**: Convert a LangChain trace fixture with tool calls and validate

### Tests for LangChain Adapter

- [X] T023 [P] [US2] Create LangChain fixture at tests/ingestion/fixtures/langchain_run.json with llm/tool/chain runs
- [X] T024 [P] [US2] Unit test for LangChainAdapter.can_handle() in tests/ingestion/test_langchain.py
- [X] T025 [P] [US2] Unit test for run tree flattening in tests/ingestion/test_langchain.py
- [X] T026 [P] [US2] Unit test for tool run expansion (tool_call + observation) in tests/ingestion/test_langchain.py
- [X] T027 [P] [US2] Error handling test for streaming token events in tests/ingestion/test_langchain.py

### Implementation for LangChain Adapter

- [X] T028 [US2] Implement LangChainAdapter class in src/agenteval/ingestion/langchain.py
- [X] T029 [US2] Implement can_handle() to detect runs structure in src/agenteval/ingestion/langchain.py
- [X] T030 [US2] Implement run type mapping (RUN_TYPE_TO_STEP_TYPE) in src/agenteval/ingestion/langchain.py
- [X] T031 [US2] Implement run tree recursive flattening in src/agenteval/ingestion/langchain.py
- [X] T032 [US2] Implement tool run expansion (create two steps) in src/agenteval/ingestion/langchain.py
- [X] T033 [US2] Implement streaming token collapsing in src/agenteval/ingestion/langchain.py
- [X] T034 [US2] Register LangChainAdapter in src/agenteval/ingestion/__init__.py

**Checkpoint**: LangChain adapter functional - can convert LangChain traces end-to-end

---

## Phase 5: CrewAI Adapter (Priority: P3)

**Goal**: Enable ingestion of CrewAI task execution logs

**Independent Test**: Convert a CrewAI trace fixture with multi-agent actions and validate

### Tests for CrewAI Adapter

- [X] T035 [P] [US3] Create CrewAI fixture at tests/ingestion/fixtures/crewai_log.json with tasks and agent actions
- [X] T036 [P] [US3] Unit test for CrewAIAdapter.can_handle() in tests/ingestion/test_crewai.py
- [X] T037 [P] [US3] Unit test for agent-to-actor_id mapping in tests/ingestion/test_crewai.py
- [X] T038 [P] [US3] Unit test for task action sequence conversion in tests/ingestion/test_crewai.py
- [X] T039 [P] [US3] Error handling test for missing agent field in tests/ingestion/test_crewai.py

### Implementation for CrewAI Adapter

- [X] T040 [US3] Implement CrewAIAdapter class in src/agenteval/ingestion/crewai.py
- [X] T041 [US3] Implement can_handle() to detect tasks array in src/agenteval/ingestion/crewai.py
- [X] T042 [US3] Implement action type mapping (ACTION_TO_STEP_TYPE) in src/agenteval/ingestion/crewai.py
- [X] T043 [US3] Implement agent name to actor_id mapping in src/agenteval/ingestion/crewai.py
- [X] T044 [US3] Implement task action iteration and step creation in src/agenteval/ingestion/crewai.py
- [X] T045 [US3] Register CrewAIAdapter in src/agenteval/ingestion/__init__.py

**Checkpoint**: CrewAI adapter functional - can convert CrewAI traces end-to-end

---

## Phase 6: OpenAI Raw API Adapter (Priority: P3)

**Goal**: Enable ingestion of raw OpenAI Chat Completions API responses

**Independent Test**: Convert an OpenAI conversation fixture with function calls and validate

### Tests for OpenAI Raw API Adapter

- [X] T046 [P] [US4] Create OpenAI fixture at tests/ingestion/fixtures/openai_response.json with messages and tool_calls
- [X] T047 [P] [US4] Unit test for OpenAIRawAdapter.can_handle() in tests/ingestion/test_openai_raw.py
- [X] T048 [P] [US4] Unit test for message-to-step conversion in tests/ingestion/test_openai_raw.py
- [X] T049 [P] [US4] Unit test for parallel tool call handling in tests/ingestion/test_openai_raw.py
- [X] T050 [P] [US4] Unit test for final_answer heuristic in tests/ingestion/test_openai_raw.py

### Implementation for OpenAI Raw API Adapter

- [X] T051 [US4] Implement OpenAIRawAdapter class in src/agenteval/ingestion/openai_raw.py
- [X] T052 [US4] Implement can_handle() to detect messages array in src/agenteval/ingestion/openai_raw.py
- [X] T053 [US4] Implement message type detection (skip user, process assistant/tool) in src/agenteval/ingestion/openai_raw.py
- [X] T054 [US4] Implement tool_calls expansion to tool_call steps in src/agenteval/ingestion/openai_raw.py
- [X] T055 [US4] Implement tool message to observation step mapping in src/agenteval/ingestion/openai_raw.py
- [X] T056 [US4] Implement final_answer heuristic (last assistant message) in src/agenteval/ingestion/openai_raw.py
- [X] T057 [US4] Register OpenAIRawAdapter in src/agenteval/ingestion/__init__.py

**Checkpoint**: OpenAI adapter functional - can convert OpenAI API responses end-to-end

---

## Phase 7: Generic JSON Adapter (Priority: P3)

**Goal**: Enable ingestion of custom JSON formats via user-defined mappings

**Independent Test**: Create a mapping config, convert a custom trace fixture, and validate

### Tests for Generic JSON Adapter

- [X] T058 [P] [US5] Create mapping config fixture at tests/ingestion/fixtures/custom_mapping.yaml with field mappings
- [X] T059 [P] [US5] Create custom trace fixture at tests/ingestion/fixtures/custom_trace.json matching the mapping
- [X] T060 [P] [US5] Unit test for GenericAdapter.can_handle() with mapping in tests/ingestion/test_generic.py
- [X] T061 [P] [US5] Unit test for JSONPath field extraction in tests/ingestion/test_generic.py
- [X] T062 [P] [US5] Unit test for transform functions (map, iso8601, concat) in tests/ingestion/test_generic.py
- [X] T063 [P] [US5] Unit test for mapping validation (unmappable fields) in tests/ingestion/test_generic.py
- [X] T064 [P] [US5] Error handling test for invalid mapping config in tests/ingestion/test_generic.py

### Implementation for Generic JSON Adapter

- [X] T065 [US5] Implement GenericAdapter class in src/agenteval/ingestion/generic.py
- [X] T066 [US5] Implement mapping config loader (YAML/JSON) in src/agenteval/ingestion/generic.py
- [X] T067 [US5] Implement JSONPath field extractor in src/agenteval/ingestion/generic.py
- [X] T068 [US5] Implement transform functions (map, iso8601, concat) in src/agenteval/ingestion/generic.py
- [X] T069 [US5] Implement mapping completeness validator in src/agenteval/ingestion/generic.py
- [X] T070 [US5] Implement trace construction from mapped fields in src/agenteval/ingestion/generic.py
- [X] T071 [US5] Register GenericAdapter in src/agenteval/ingestion/__init__.py

**Checkpoint**: Generic adapter functional - can convert custom traces via mappings

---

## Phase 8: Integration & Polish

**Purpose**: End-to-end testing, documentation, and cross-cutting improvements

### Integration Tests

- [X] T072 [P] Integration test: ingest → validate → evaluate pipeline in tests/ingestion/test_integration.py
- [X] T073 [P] Integration test: bulk ingest with mixed success/failure in tests/ingestion/test_integration.py
- [X] T074 [P] Integration test: size limit enforcement (10MB/50MB) in tests/ingestion/test_integration.py
- [X] T075 [P] Integration test: CLI auto-detection across all adapters in tests/ingestion/test_integration.py

### CLI Improvements

- [X] T076 Implement progress bar for bulk operations using tqdm in src/agenteval/ingestion/cli.py
- [X] T077 Implement --verbose flag detailed logging in src/agenteval/ingestion/cli.py
- [X] T078 Implement bulk error summary reporting in src/agenteval/ingestion/cli.py
- [X] T079 Add helpful error messages for common failures in src/agenteval/ingestion/cli.py

### Documentation

- [X] T080 [P] Create usage guide at docs/ingestion_usage.md with examples for each adapter
- [X] T081 [P] Create generic mapping reference at docs/generic_mapping.md with transform documentation
- [X] T082 [P] Create troubleshooting guide at docs/ingestion_troubleshooting.md
- [X] T083 [P] Add example mapping configs at examples/mappings/ for common custom formats
- [X] T084 Update CLAUDE.md with ingestion module architecture notes
- [X] T085 Update README.md with agenteval-ingest command documentation

### Validation & Cleanup

- [X] T086 Run agenteval-validate-dataset to ensure all test fixtures pass validation
- [X] T087 Run mypy type checking on src/agenteval/ingestion/
- [X] T088 Run ruff linting and formatting on src/agenteval/ingestion/
- [X] T089 Validate quickstart.md examples work end-to-end
- [X] T090 Code review and refactoring pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all adapters
- **Adapters (Phases 3-7)**: All depend on Foundational phase completion
  - Adapters can proceed in parallel (if staffed)
  - Or sequentially in order (OTel → LangChain → CrewAI → OpenAI → Generic)
- **Integration & Polish (Phase 8)**: Depends on all adapters being complete

### Adapter Dependencies

- **OpenTelemetry (US1)**: Can start after Foundational (Phase 2) - No dependencies on other adapters
- **LangChain (US2)**: Can start after Foundational (Phase 2) - No dependencies on other adapters
- **CrewAI (US3)**: Can start after Foundational (Phase 2) - No dependencies on other adapters
- **OpenAI (US4)**: Can start after Foundational (Phase 2) - No dependencies on other adapters
- **Generic (US5)**: Can start after Foundational (Phase 2) - No dependencies on other adapters

All adapters are **independently implementable** and **independently testable**.

### Within Each Adapter

- Tests before implementation (write fixtures and tests first)
- can_handle() before convert()
- Type mapping before complex conversion logic
- Adapter complete before registry registration

### Parallel Opportunities

- All Setup tasks (T001-T004) can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all 5 adapter phases can start in parallel
- All test tasks within an adapter marked [P] can run in parallel
- All documentation tasks (T080-T085) can run in parallel
- All validation tasks (T086-T089) can run in parallel

---

## Parallel Example: OpenTelemetry Adapter

```bash
# Launch all tests for OTel adapter together:
Task: "Create OTel fixture at tests/ingestion/fixtures/otel_trace.json"
Task: "Unit test for OTelAdapter.can_handle() in tests/ingestion/test_otel.py"
Task: "Unit test for OTelAdapter.convert() in tests/ingestion/test_otel.py"
Task: "Unit test for nested span flattening in tests/ingestion/test_otel.py"
Task: "Error handling test for malformed OTel trace in tests/ingestion/test_otel.py"
```

---

## Parallel Example: All Adapters (after Foundational complete)

```bash
# Different team members can work on different adapters:
Developer A: Phase 3 - OpenTelemetry Adapter (T012-T022)
Developer B: Phase 4 - LangChain Adapter (T023-T034)
Developer C: Phase 5 - CrewAI Adapter (T035-T045)
Developer D: Phase 6 - OpenAI Adapter (T046-T057)
Developer E: Phase 7 - Generic Adapter (T058-T071)
```

---

## Implementation Strategy

### MVP First (OpenTelemetry Adapter Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T011) - CRITICAL
3. Complete Phase 3: OpenTelemetry Adapter (T012-T022)
4. **STOP and VALIDATE**: Test OTel ingestion end-to-end
5. Commit and tag as MVP

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add OpenTelemetry Adapter → Test independently → Commit (MVP!)
3. Add LangChain Adapter → Test independently → Commit
4. Add CrewAI Adapter → Test independently → Commit
5. Add OpenAI Adapter → Test independently → Commit
6. Add Generic Adapter → Test independently → Commit
7. Polish & Documentation → Final release

Each adapter adds value without breaking previous adapters.

### Parallel Team Strategy

With 5 developers:

1. Team completes Setup + Foundational together (T001-T011)
2. Once Foundational is done, split:
   - Developer A: OpenTelemetry Adapter (T012-T022)
   - Developer B: LangChain Adapter (T023-T034)
   - Developer C: CrewAI Adapter (T035-T045)
   - Developer D: OpenAI Adapter (T046-T057)
   - Developer E: Generic Adapter (T058-T071)
3. All adapters complete and integrate independently
4. Team reconvenes for Integration & Polish (T072-T090)

---

## Notes

- **Total Tasks**: 90 tasks across 8 phases
- **MVP Scope**: Phases 1-3 (22 tasks) deliver OpenTelemetry ingestion
- **Parallel Opportunities**: 48 tasks marked [P] can run in parallel within their phase
- **Independent Adapters**: Each adapter (US1-US5) is fully independent
- Tests are included because spec explicitly requests them
- All tasks include exact file paths for implementation
- Checkpoint after each adapter to validate independently
- Run agenteval-validate-dataset after creating test fixtures
- Commit after each adapter phase completion
