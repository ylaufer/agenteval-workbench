# Implementation Plan: Ingestion UI

**Branch**: `012-ingestion-ui` | **Date**: 2026-03-25 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-ingestion-ui/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Add a Streamlit page that enables users to upload trace files (single or bulk ZIP), auto-detect format using existing ingestion adapters, preview converted traces before saving, and create new benchmark cases without using the CLI. This feature wraps the existing `src/agenteval/ingestion/` module (Feature 005) with a thin UI layer, following the library-first architecture principle.

## Technical Context

**Language/Version**: Python 3.10+ (using `from __future__ import annotations`)
**Primary Dependencies**: Streamlit (UI), jsonschema (validation), existing ingestion module
**Storage**: Filesystem (`data/cases/case_NNN/trace.json`)
**Testing**: pytest (reuse existing ingestion test fixtures)
**Target Platform**: Local development (Windows/Mac/Linux), web browser UI
**Project Type**: Web UI (Streamlit app) wrapping library code
**Performance Goals**: Handle 10MB files interactively, 50MB hard limit
**Constraints**: Must use existing service layer pattern (`src/agenteval/core/service.py`), zero new runtime dependencies, offline-only (no network calls)
**Scale/Scope**: Single-user local tool, 1 new Streamlit page, 2-3 new service functions

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Security First** ✅
- No secrets, API keys, or credentials introduced
- No external URLs in feature logic
- Uses existing `_safe_resolve_within()` for file operations
- All conversions validated against trace schema before saving

**II. Schema-First Contracts** ✅
- All converted traces validated against `schemas/trace_schema.json`
- No schema modifications required
- Reuses existing ingestion adapters (no schema changes)

**III. Offline & Sandboxed Execution** ✅
- Zero network calls (wraps offline ingestion module)
- All file I/O via service layer using existing safety helpers

**IV. Test-Driven Quality** ✅
- Will reuse existing ingestion test fixtures from `tests/ingestion/fixtures/`
- Service layer functions will have unit tests
- UI tested via manual acceptance scenarios

**V. Minimal Dependencies** ✅
- Zero new runtime dependencies
- Streamlit already available under `[ui]` extras
- Uses existing ingestion module

**VI. Dataset Completeness** ⚠️ ADDRESSED
- Feature creates only `trace.json` initially
- User must manually add `prompt.txt` and `expected_outcome.md` afterward
- Alternative: Add input fields for prompt and expected outcome in the UI (Phase 1 design decision)

**VII. Backward-Compatible Evolution** ✅
- No changes to existing CLI commands
- No changes to trace schema
- Purely additive: new UI page + service functions

**VIII. Library-First Architecture** ✅
- Follows pattern: `app/page_ingest.py` → `service.py` → `ingestion/` library
- All business logic in `src/agenteval/ingestion/` (already exists)
- Service layer provides thin orchestration

**GATE STATUS**: ✅ PASS (with design decision needed for completeness)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/agenteval/
├── core/
│   ├── service.py           # ADD: get_next_case_id(), ingest_trace(), ingest_bulk()
│   └── ...
└── ingestion/               # EXISTING (no changes)
    ├── __init__.py          # Adapter registry
    ├── base.py              # TraceAdapter protocol, check_file_size()
    ├── otel.py
    ├── langchain.py
    ├── crewai.py
    ├── openai_raw.py
    └── generic.py

app/
├── app.py                   # MODIFY: Add "Ingest" to sidebar nav
├── page_ingest.py           # NEW: Main ingestion UI page
├── components/
│   ├── help_section.py      # REUSE: Contextual help
│   └── tooltip.py           # REUSE: Tooltips
└── onboarding/              # EXISTING (no changes)

tests/
├── core/
│   └── test_service.py      # ADD: Tests for new service functions
└── ingestion/
    └── fixtures/            # REUSE: Existing test trace files
```

**Structure Decision**: This feature adds one new UI page (`app/page_ingest.py`) and extends the service layer (`service.py`) with orchestration functions. It reuses the existing ingestion module without modification, following the library-first architecture pattern established in Feature 005.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations requiring justification.** All constitution principles are satisfied.
