# Implementation Plan: Streamlit UI for AgentEval Workbench

**Branch**: `002-streamlit-ui` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-streamlit-ui/spec.md`
**Revised**: 2026-03-23 — service layer architecture, app/ at repo root

## Summary

Build a thin Streamlit UI layer over the existing AgentEval library modules. The UI provides four pages (Generate, Evaluate, Inspect, Report) with sidebar navigation. A new service layer (`src/agenteval/core/service.py`) provides UI-facing orchestration functions that compose existing library APIs — runner.py and report.py remain untouched. The Streamlit app lives outside the library package in `app/` at the repository root. Streamlit is added as an optional dependency under `[project.optional-dependencies.ui]` to preserve the minimal-dependency core.

## Technical Context

**Language/Version**: Python 3.10+ (consistent with existing project)
**Primary Dependencies**: Streamlit (UI framework, optional `[ui]` extra), existing `jsonschema` (runtime)
**Storage**: Local filesystem — `data/cases/` for cases, `reports/` for evaluation outputs
**Testing**: pytest (unit tests for service layer; manual testing for Streamlit pages)
**Target Platform**: Local development machine (Windows/macOS/Linux)
**Project Type**: Library with thin UI layer
**Performance Goals**: N/A — single-user local tool
**Constraints**: Offline-only, all paths within repo root, no new runtime dependencies in core
**Scale/Scope**: Single user, local filesystem, ~12-50 cases

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Security First | PASS | UI delegates to existing path-safe library functions; no new file I/O outside repo root |
| II. Schema-First Contracts | PASS | No schema changes; UI reads existing trace/rubric schemas via library loaders |
| III. Offline & Sandboxed | PASS | No network calls; Streamlit runs locally; all file ops use `_get_repo_root()` |
| IV. Test-Driven Quality | PASS | Service layer has pytest tests; Streamlit pages tested manually |
| V. Minimal Dependencies | JUSTIFIED | Streamlit is added as optional `[ui]` extra, not a core runtime dependency. Core library remains jsonschema-only |
| VI. Dataset Completeness | PASS | No changes to dataset structure; generator and validator unchanged |
| VII. Backward-Compatible | PASS | runner.py, report.py, and all CLI entry points are completely untouched |
| VIII. Library-First | PASS | Service layer lives in `src/agenteval/core/`; UI is a thin display layer in `app/` |

## Project Structure

### Documentation (this feature)

```text
specs/002-streamlit-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/agenteval/
├── core/
│   ├── service.py       # NEW — service layer for UI-facing orchestration
│   ├── runner.py        # UNCHANGED
│   ├── report.py        # UNCHANGED
│   ├── loader.py        # unchanged
│   ├── tagger.py        # unchanged
│   ├── types.py         # unchanged
│   └── calibration.py   # unchanged
├── dataset/
│   ├── validator.py     # unchanged (already has validate_dataset() API)
│   ├── generator.py     # unchanged (already has generate_case() API)
│   └── __init__.py      # unchanged
└── __init__.py          # unchanged

app/
├── app.py               # NEW — Streamlit entry point + sidebar navigation
├── page_generate.py     # NEW — Generate & Validate page
├── page_evaluate.py     # NEW — Evaluate page
├── page_inspect.py      # NEW — Inspect page
└── page_report.py       # NEW — Report page

tests/
├── test_service.py      # NEW — tests for service layer
└── ...                  # existing tests unchanged
```

**Structure Decision**: The service layer lives inside the library (`src/agenteval/core/service.py`) because it is reusable orchestration logic that any consumer (UI, scripts, notebooks) can import. The Streamlit app lives outside the library in `app/` at the repo root because it is a consumer of the library, not part of it. This keeps the library independent of Streamlit.

## Key Design Decisions

### 1. Service Layer Instead of Modifying Runner/Report

runner.py and report.py are not modified. A new `service.py` module provides orchestration functions that compose existing public APIs:

- `service.run_evaluation()` → calls `runner.main()` with constructed argv, then reads generated JSON files from disk to return structured data
- `service.generate_summary_report()` → calls `report.main()` with constructed argv, then reads generated summary JSON
- `service.generate_case()` → delegates to `dataset.generator.generate_case()`
- `service.validate_dataset()` → delegates to `dataset.validator.validate_dataset()`
- `service.list_cases()` → lists case directories in dataset dir
- `service.load_case_metadata()` → parses expected_outcome.md YAML header
- `service.load_trace()` → delegates to `core.loader.load_trace()`
- `service.load_evaluation_template()` → reads evaluation JSON from reports/

This approach is the smallest safe change: zero risk of breaking existing CLI behavior since runner.py and report.py are never touched.

### 2. Streamlit App Outside Library Package

The Streamlit app lives in `app/` at the repo root, not inside `src/agenteval/`. This:
- Keeps the library package clean and independent of Streamlit
- Avoids Streamlit as a transitive dependency for library importers
- Makes the app a consumer of the library, same as CLI entry points
- Allows running via `streamlit run app/app.py` without package concerns

### 3. Streamlit as Optional Dependency

Streamlit is added under `[project.optional-dependencies.ui]` in pyproject.toml. This keeps the core library dependency-free (jsonschema only) while allowing `pip install -e ".[ui]"` for UI users. Constitution V compliance is maintained.

### 4. Multi-Page Streamlit App

The app uses Streamlit's page-based pattern with sidebar navigation. Each page is a self-contained module that imports service layer functions. No business logic in UI code — pages handle only:
- Input collection (forms, dropdowns, buttons)
- Service layer function calls
- Output display (tables, expandable sections, success/error messages)

### 5. Validation Display Pattern

After case generation, the UI calls `service.validate_dataset()` and partitions the returned `ValidationIssue` list by matching the `case_id` field against the newly generated case ID. New-case issues are shown prominently; other-case issues go in a collapsed expander.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Streamlit dependency | Users need visual access to evaluation workflow without CLI | Pure CLI is insufficient for the target audience (non-CLI users). Streamlit is optional, not core. |
