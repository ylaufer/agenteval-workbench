# Implementation Plan: Streamlit UI for AgentEval Workbench

**Branch**: `002-streamlit-ui` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-streamlit-ui/spec.md`

## Summary

Build a thin Streamlit UI layer over the existing AgentEval library modules. The UI provides four pages (Generate, Evaluate, Inspect, Report) with sidebar navigation. All business logic delegates to existing library functions in `src/agenteval/`. Small wrapper functions are added to `runner.py` and `report.py` to expose programmatic APIs that return data structures instead of writing files directly. Streamlit is added as an optional dependency under `[project.optional-dependencies.ui]` to preserve the minimal-dependency core.

## Technical Context

**Language/Version**: Python 3.10+ (consistent with existing project)
**Primary Dependencies**: Streamlit (UI framework, optional `[ui]` extra), existing `jsonschema` (runtime)
**Storage**: Local filesystem — `data/cases/` for cases, `reports/` for evaluation outputs
**Testing**: pytest (unit tests for wrapper functions; manual testing for Streamlit pages)
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
| IV. Test-Driven Quality | PASS | Wrapper functions will have pytest tests; Streamlit pages tested manually |
| V. Minimal Dependencies | JUSTIFIED | Streamlit is added as optional `[ui]` extra, not a core runtime dependency. Core library remains jsonschema-only |
| VI. Dataset Completeness | PASS | No changes to dataset structure; generator and validator unchanged |
| VII. Backward-Compatible | PASS | Existing CLI entry points unchanged; wrapper functions are additive |
| VIII. Library-First | PASS | UI is a thin display layer; all logic in `src/agenteval/` library modules |

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
│   ├── runner.py        # MODIFIED — add run_evaluation() wrapper function
│   ├── report.py        # MODIFIED — add generate_summary_report() wrapper function
│   ├── loader.py         # unchanged
│   ├── tagger.py         # unchanged
│   ├── types.py          # unchanged
│   └── calibration.py    # unchanged
├── dataset/
│   ├── validator.py      # unchanged (already has validate_dataset() API)
│   ├── generator.py      # unchanged (already has generate_case() API)
│   └── __init__.py       # unchanged
├── ui/
│   ├── __init__.py       # NEW — package init
│   ├── app.py            # NEW — Streamlit app entry point + sidebar navigation
│   ├── page_generate.py  # NEW — Generate & Validate page
│   ├── page_evaluate.py  # NEW — Evaluate page
│   ├── page_inspect.py   # NEW — Inspect page
│   └── page_report.py    # NEW — Report page
└── __init__.py            # unchanged

tests/
├── test_runner.py        # MODIFIED — add tests for run_evaluation() wrapper
├── test_report.py        # MODIFIED — add tests for generate_summary_report() wrapper
└── ...                    # existing tests unchanged
```

**Structure Decision**: Single project layout extending `src/agenteval/` with a new `ui/` subpackage. UI pages are separate modules for maintainability. Wrapper functions are added directly to existing `runner.py` and `report.py` modules rather than creating a separate wrapper module, keeping related logic together.

## Key Design Decisions

### 1. Wrapper Functions Over CLI Subprocess Calls

The existing `runner.main()` and `report.main()` functions parse CLI arguments, process data, and write files. The UI needs programmatic access to intermediate results. Rather than calling CLI entry points via subprocess (fragile, loses type safety), we extract the core logic into new library functions:

- `runner.run_evaluation()` → returns `list[CaseEvaluationTemplate]` and optionally writes files
- `report.generate_summary_report()` → returns `dict` and optionally writes files

The existing `main()` functions are refactored to call these new functions, preserving backward compatibility.

### 2. Streamlit as Optional Dependency

Streamlit is added under `[project.optional-dependencies.ui]` in pyproject.toml. This keeps the core library dependency-free (jsonschema only) while allowing `pip install -e ".[ui]"` for UI users. Constitution V compliance is maintained.

### 3. Multi-Page Streamlit App

The app uses Streamlit's native multi-page pattern with sidebar navigation. Each page is a self-contained module that imports and calls library functions. No business logic in UI code — pages handle only:
- Input collection (forms, dropdowns, buttons)
- Library function calls
- Output display (tables, expandable sections, success/error messages)

### 4. Validation Display Pattern

After case generation, the UI calls `validate_dataset()` and partitions the returned `ValidationIssue` list by matching the `case_id` field against the newly generated case ID. New-case issues are shown prominently; other-case issues go in a collapsed expander.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Streamlit dependency | Users need visual access to evaluation workflow without CLI | Pure CLI is insufficient for the target audience (non-CLI users). Streamlit is optional, not core. |
