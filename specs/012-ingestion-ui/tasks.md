# Implementation Tasks: Ingestion UI

**Feature**: Ingestion UI
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)
**Status**: Ready for implementation
**Created**: 2026-03-25 | **Updated**: 2026-03-25
**Design Artifacts**: [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

---

## Overview

This document breaks down the Ingestion UI feature into executable tasks organized by user story. Each user story represents an independently testable increment that delivers user value.

**User Stories** (from spec.md):
- **US1 (P1)**: Single Trace Upload and Convert — Core use case, blocks all other stories
- **US2 (P2)**: Manual Adapter Override — Fallback mechanism when auto-detection fails
- **US3 (P3)**: Bulk Upload via ZIP — Batch workflow enhancement

**Implementation Strategy**: Build incrementally, starting with US1 (MVP), then add US2 and US3 as enhancements. Each story is independently testable and delivers user value.

---

## Phase 1: Setup

**Goal**: Verify prerequisites and prepare project structure.

### Tasks

- [X] T001 Verify ingestion module is stable (5 adapters working: OTel, LangChain, CrewAI, OpenAI, Generic)
- [X] T002 Verify service layer exists at src/agenteval/core/service.py
- [X] T003 Verify existing Streamlit pages structure (app/page_*.py pattern)
- [X] T004 Create feature branch `012-ingestion-ui`

**Note**: Setup tasks T001-T004 completed during planning phase.

---

## Phase 2: Foundational

**Goal**: Add service layer functions needed by all user stories.

**Design Reference**: [contracts/service_layer_api.md](contracts/service_layer_api.md)

### Tasks

- [X] T005 [P] Implement `get_next_case_id()` in src/agenteval/core/service.py (scan data/cases/, return next case_NNN)
- [X] T006 [P] Implement `ingest_trace()` in src/agenteval/core/service.py (convert trace, validate schema, create 3 files with placeholders)
- [X] T007 [P] Add imports for ingestion module (auto_detect_adapter, get_adapter_by_name) to src/agenteval/core/service.py

**Independent Test**:
1. Call `get_next_case_id()` → returns `"case_001"` or next available
2. Call `ingest_trace()` with OTel fixture → creates case directory with `trace.json`, `prompt.txt`, `expected_outcome.md`
3. Verify trace validates against `schemas/trace_schema.json`

**Acceptance Criteria** (from contracts/service_layer_api.md):
- AC-001: `get_next_case_id()` returns correct next ID when cases exist
- AC-002: `get_next_case_id()` returns `"case_001"` when no cases exist
- AC-003: `ingest_trace()` with valid OTel trace creates 3 files in case directory
- AC-004: `ingest_trace()` with invalid trace raises `ValueError` with schema errors

---

## Phase 3: User Story 1 — Single Trace Upload and Convert (P1)

**Goal**: Enable users to upload a single trace file, see preview, and save to a case directory.

**Priority**: P1 (Core use case - blocks all other stories)

**Design References**:
- Entities: UploadedFile, ConversionPreview, CaseDirectory ([data-model.md](data-model.md))
- Quickstart: Scenario 1 ([quickstart.md](quickstart.md#scenario-1-ingest-a-single-trace-file))

**Independent Test**: Upload `tests/ingestion/fixtures/otel_trace.json` → format auto-detected → preview shows step count/types → save creates `data/cases/case_NNN/trace.json` + placeholders → navigate to Inspect page shows new case.

### Tasks

- [X] T008 [US1] Create app/page_ingest.py with basic page structure and title
- [X] T009 [US1] Add file uploader widget (st.file_uploader for JSON files) in app/page_ingest.py
- [X] T010 [US1] Implement file size validation (10MB soft limit warning, 50MB hard limit error) in app/page_ingest.py
- [X] T011 [US1] Add session state initialization for upload workflow in app/page_ingest.py
- [X] T012 [US1] Implement auto-detection logic (call ingestion.auto_detect_adapter) in app/page_ingest.py
- [X] T013 [US1] Display detected format name and adapter info in app/page_ingest.py
- [X] T014 [US1] Implement conversion preview (step count, step type breakdown, warnings) in app/page_ingest.py
- [X] T015 [US1] Add case ID input field with auto-suggested next ID in app/page_ingest.py
- [X] T016 [US1] Add directory existence check and overwrite warning in app/page_ingest.py
- [X] T017 [US1] Implement save button with conversion + validation in app/page_ingest.py
- [X] T018 [US1] Add success message with next steps in app/page_ingest.py
- [X] T019 [US1] Add error handling for schema validation failures in app/page_ingest.py
- [X] T020 [US1] Add error handling for unrecognized formats in app/page_ingest.py
- [X] T021 [US1] Add "Ingest" to sidebar navigation in app/app.py
- [X] T022 [US1] Add contextual help section using st.expander
- [X] T023 [US1] Add tooltips using help="" parameters

**Acceptance Criteria (from spec)**:
1. Upload valid OTel/LangChain/CrewAI/OpenAI JSON → shows detected format name
2. View conversion preview → see step count, step type breakdown, warnings
3. Confirm and save → trace written to case directory + success message links to Inspect
4. Upload fails schema validation → clear error message, no files written

---

## Phase 4: User Story 2 — Manual Adapter Override (P2)

**Goal**: Allow manual adapter selection when auto-detection fails or user wants to force a specific adapter.

**Priority**: P2 (Fallback mechanism)

**Design References**:
- Research Decision: RQ3 - Generic adapter mapping config via separate file upload ([research.md](research.md))
- Quickstart: Scenario 2, Scenario 3 ([quickstart.md](quickstart.md#scenario-2-manual-adapter-override))

**Independent Test**: Upload a file → select adapter manually from dropdown → preview regenerates using selected adapter → save works.

### Tasks

- [ ] T024 [US2] Add adapter selection dropdown (Auto-detect, OTel, LangChain, CrewAI, OpenAI, Generic) in app/page_ingest.py
- [ ] T025 [US2] Implement dropdown onChange handler to regenerate preview in app/page_ingest.py
- [ ] T026 [US2] Show adapter name in preview header in app/page_ingest.py
- [ ] T027 [US2] Add conditional mapping config uploader for Generic adapter in app/page_ingest.py
- [ ] T028 [US2] Implement mapping config validation for Generic adapter in app/page_ingest.py
- [ ] T029 [US2] Block save button when Generic selected but no mapping config provided in app/page_ingest.py

**Acceptance Criteria (from spec)**:
1. Auto-detection fails → user selects adapter manually → preview generates
2. Auto-detection succeeds → user overrides → preview regenerates
3. User selects Generic → mapping config uploader appears → conversion blocked until mapping provided

---

## Phase 5: User Story 3 — Bulk Upload via ZIP (P3)

**Goal**: Enable batch ingestion by uploading a ZIP file containing multiple trace files.

**Priority**: P3 (Batch workflow enhancement)

**Design References**:
- Entity: IngestionResult ([data-model.md](data-model.md))
- Service Function: ingest_bulk() ([contracts/service_layer_api.md](contracts/service_layer_api.md))
- Research Decision: RQ4 - In-memory ZIP processing ([research.md](research.md))
- Quickstart: Scenario 4 ([quickstart.md](quickstart.md#scenario-4-bulk-upload-via-zip))

**Independent Test**: Create ZIP with 3 fixture JSONs → upload → status table shows 3 rows with converted/failed/skipped → verify created case directories.

### Tasks

- [ ] T030 [US3] Implement `ingest_bulk()` in src/agenteval/core/service.py (in-memory ZIP extraction + batch conversion, returns list of IngestionResult)
- [ ] T031 [US3] Update file uploader to accept ZIP files in app/page_ingest.py
- [ ] T032 [US3] Add ZIP detection and extraction logic in app/page_ingest.py
- [ ] T033 [US3] Implement per-file status tracking (converted/failed/skipped) in app/page_ingest.py
- [ ] T034 [US3] Create status table UI with columns: filename, format, status, case ID, error in app/page_ingest.py
- [ ] T035 [US3] Implement partial success handling (continue on single file failure) in app/page_ingest.py
- [ ] T036 [US3] Add non-JSON file skipping logic in app/page_ingest.py
- [ ] T037 [US3] Add bulk conversion summary (total converted/failed/skipped counts) in app/page_ingest.py
- [ ] T038 [US3] Handle edge case: ZIP with zero JSON files in app/page_ingest.py

**Acceptance Criteria (from spec)**:
1. Upload ZIP → processing completes → per-file status table shows results
2. Some files fail → successfully converted files saved, failed files listed as errors
3. ZIP contains non-JSON → skipped with "skipped (not JSON)" status
4. Bulk complete → summary shows total counts

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Final UI improvements, error states, and documentation.

### Tasks

- [ ] T039 [P] Add empty state when no file uploaded in app/page_ingest.py
- [ ] T040 [P] Add loading spinner during conversion in app/page_ingest.py
- [ ] T041 [P] Add Material icons to buttons and status badges in app/page_ingest.py
- [ ] T042 [P] Use st.container with borders for visual grouping in app/page_ingest.py
- [ ] T043 [P] Add progress indicator for bulk uploads in app/page_ingest.py
- [ ] T044 [P] Update CLAUDE.md to document new service layer functions
- [ ] T045 [P] Update README.md to mention Ingest page in UI workflow
- [ ] T046 [P] Add example ingestion workflow to docs/

---

## Dependencies

### User Story Completion Order

```
Setup (T001-T004)
    ↓
Foundational (T005-T007) — MUST complete before user stories
    ↓
    ├─→ US1 (T008-T023) — MVP, blocks nothing
    ├─→ US2 (T024-T029) — Depends on US1 UI structure
    └─→ US3 (T030-T038) — Depends on US1 + service layer
         ↓
Polish (T039-T046) — Depends on all user stories
```

**Critical Path**: T001-T007 → T008-T023 (US1) → T039-T046 (Polish)

**US2 and US3 can run in parallel** after US1 completes if multiple developers are available.

---

## Parallel Execution Opportunities

### Within US1 (after T008-T011 complete)
- T012-T014 (detection + preview logic) in parallel
- T015-T017 (case ID input + save logic) in parallel
- T022-T023 (help + tooltips) in parallel

### Across User Stories (after US1 complete)
- US2 tasks (T024-T029) can run in parallel with US3 tasks (T030-T038)

### Polish Phase (after all user stories)
- All T039-T046 can run in parallel (different files/concerns)

---

## MVP Scope

**Recommended MVP**: Complete through US1 (T001-T023)

This delivers:
- ✅ Single file upload and conversion
- ✅ Auto-detection of all 4 built-in adapters
- ✅ Conversion preview before save
- ✅ Schema validation
- ✅ Success flow with link to Inspect page
- ✅ Error handling for common failures

**Post-MVP Enhancements**:
- US2: Manual adapter override (when auto-detection fails)
- US3: Bulk ZIP upload (batch workflows)
- Polish: Loading states, progress bars, docs updates

---

## Implementation Notes

**Architecture Patterns (from existing codebase)**:
- Service layer delegates to ingestion module (no direct imports in UI)
- Relative imports within `app/` (e.g., `from components.help_section import ...`)
- Session state for multi-step workflows
- Material icons for visual design
- Bordered containers for grouping

**File Size Limits** (from ingestion.base):
- Soft limit: 10MB (warning, but allow continuation)
- Hard limit: 50MB (reject upload immediately)

**Adapter Registry** (from ingestion.__init__):
- `auto_detect_adapter(raw)` → returns adapter or None
- `get_adapter_by_name(name)` → returns adapter or None
- `list_adapters()` → returns list of adapter class names

---

## Task Count Summary

- **Setup**: 4 tasks (✓ completed during planning)
- **Foundational**: 3 tasks (service layer functions)
- **US1 (P1)**: 16 tasks (MVP - single file upload)
- **US2 (P2)**: 6 tasks (manual adapter override)
- **US3 (P3)**: 9 tasks (bulk ZIP upload)
- **Polish**: 8 tasks (UI polish + docs)

**Total**: 46 tasks

**Parallel opportunities**: 15+ tasks can run in parallel across phases

**Design Artifacts**: This task breakdown is based on:
- [plan.md](plan.md) — Technical context and architecture
- [research.md](research.md) — 5 research decisions resolved
- [data-model.md](data-model.md) — 4 entities (UploadedFile, ConversionPreview, IngestionResult, CaseDirectory)
- [contracts/service_layer_api.md](contracts/service_layer_api.md) — 3 service functions with acceptance criteria
- [quickstart.md](quickstart.md) — 6 usage scenarios for testing
