# Implementation Plan: Run Tracking

**Branch**: `003-run-tracking` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/003-run-tracking/spec.md`

## Summary

Introduce explicit run tracking for the evaluation pipeline. Each evaluation execution produces a tracked run with a unique `YYYYMMDDTHHMMSS_xxxx` run ID, timestamps, dataset path reference, and configuration. Run results (per-case evaluation templates + summary report) are persisted exclusively under a run-specific directory. Users can list past runs, inspect run details, and access run history via both CLI and Streamlit UI.

The implementation follows the library-first architecture: a new `src/agenteval/core/runs.py` module provides all run tracking logic, the service layer (`service.py`) is extended to orchestrate run-aware evaluation, and thin CLI entry points expose list/inspect commands.

## Technical Context

**Language/Version**: Python >= 3.10 (`from __future__ import annotations`)
**Primary Dependencies**: `jsonschema>=4.21.0` (only runtime dep; no new deps added)
**Storage**: Local filesystem — run data stored under `runs/` directory at repo root
**Testing**: `pytest>=8.0.0` with strict markers and fail-fast (`-x`)
**Target Platform**: Cross-platform (Windows, Linux, macOS)
**Project Type**: Library + CLI + optional Streamlit UI
**Performance Goals**: < 1 second overhead for run record creation (SC-006)
**Constraints**: Offline-only, no network calls, all paths sandboxed within repo root
**Scale/Scope**: Unbounded number of runs (no retention policy in v1)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Security First | PASS | All paths use `_safe_resolve_within()`. Run data stays in repo root. No secrets in run metadata. |
| II. Schema-First Contracts | PASS | Run metadata stored as JSON. Existing trace/rubric schemas unchanged. |
| III. Offline & Sandboxed | PASS | No network calls. All I/O via `_get_repo_root()` + `_safe_resolve_within()`. |
| IV. Test-Driven Quality | PASS | New `test_runs.py` ships with the module. Service layer tests extended. |
| V. Minimal Dependencies | PASS | No new runtime dependencies. Uses stdlib `datetime`, `secrets`, `json`. |
| VI. Dataset Completeness | PASS | Run tracking does not modify dataset structure. |
| VII. Backward-Compatible Evolution | PASS | Existing CLI commands (`agenteval-eval-runner`, `agenteval-eval-report`) continue to work with same arguments. Run tracking is additive. |
| VIII. Library-First Architecture | PASS | All logic in `src/agenteval/core/runs.py`. CLI entry points are thin wrappers. UI delegates to service layer. |

No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-run-tracking/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── cli-contracts.md
│   └── library-contracts.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/agenteval/core/
├── __init__.py          # MODIFY: add "runs" to exports
├── runs.py              # NEW: run tracking library module
├── runner.py            # EXISTING: unchanged (backward compatible)
├── report.py            # EXISTING: unchanged (backward compatible)
├── service.py           # MODIFY: add run-aware evaluation orchestration
├── types.py             # MODIFY: add RunRecord, RunStatus types
├── loader.py            # EXISTING: unchanged
├── tagger.py            # EXISTING: unchanged
└── calibration.py       # EXISTING: unchanged

tests/
├── test_runs.py         # NEW: run tracking tests
├── test_service.py      # MODIFY: add run-aware service tests
└── ...                  # EXISTING: unchanged

app/
├── page_evaluate.py     # MODIFY: run-aware evaluation with run list
├── page_inspect.py      # MODIFY: add run selection for inspection
└── ...                  # EXISTING: unchanged

runs/                    # NEW: run data storage directory (created at runtime)
└── <run_id>/
    ├── run.json         # Run metadata record
    ├── *.evaluation.json
    ├── *.evaluation.md
    ├── summary.evaluation.json
    └── summary.evaluation.md
```

**Structure Decision**: Extends the existing single-project `src/agenteval/` layout. The new `runs.py` module lives alongside existing core modules. Run data is stored under a top-level `runs/` directory (parallel to `data/`, `reports/`, `rubrics/`). No structural reorganization needed.
