# Implementation Plan: Custom Rubric Builder

**Branch**: `010-custom-rubric-builder` | **Date**: 2026-05-04 | **Spec**: `specs/010-custom-rubric-builder/spec.md`

## Summary

Enable teams to create custom evaluation rubrics from the Streamlit UI without editing raw YAML. Implements a rubric builder page with 4 starter templates, per-dimension editing via inline expanders, schema validation before save, JSON/YAML preview, and auto-versioned file output to `rubrics/v{N}_{name}.json`. Also adds a rubric mismatch warning in the comparison engine for runs scored against different rubric versions.

## Technical Context

**Language/Version**: Python 3.10+, `from __future__ import annotations`
**Primary Dependencies**: `jsonschema>=4.21.0` (existing), `streamlit>=1.30.0` (UI, optional extra)
**Storage**: Filesystem — `rubrics/v{N}_{name}.json`, `rubrics/templates/*.json`
**Testing**: pytest
**Target Platform**: Local desktop (Streamlit UI + importable library)
**Project Type**: Library + Streamlit UI enhancement
**Performance Goals**: Rubric save/load < 100ms; validation < 50ms
**Constraints**: No new runtime dependencies; all file I/O within repo root via `_safe_resolve_within()`
**Scale/Scope**: Single-user lab tool; rubric files are small JSON (< 50 dimensions typical)

## Constitution Check

| Principle | Status | Notes |
|---|---|---|
| I. Security First | ✅ PASS | Rubric files stored locally; all paths via `_safe_resolve_within()`; no secrets in rubric content |
| II. Schema-First | ✅ PASS | `rubric_schema.json` already exists and governs the format; validate on save |
| III. Offline | ✅ PASS | All I/O is local filesystem |
| IV. Test-Driven | ✅ PASS | `tests/test_rubric_builder.py` required; covers validation, versioning, template loading, save pipeline |
| V. Minimal Dependencies | ✅ PASS | No new runtime deps; YAML preview via stdlib formatter |
| VI. Dataset Completeness | ✅ PASS | Rubric files in `rubrics/`, not `data/cases/` |
| VII. Backward Compatible | ✅ PASS | Existing `v1_agent_general.json` untouched; new rubrics are additive |
| VIII. Library-First | ✅ PASS | All logic in `src/agenteval/core/rubric_builder.py`; UI is thin wrapper |

## Project Structure

```text
src/agenteval/core/rubric_builder.py    — RubricDimension, CRUD, validate, save, version logic
src/agenteval/core/service.py           — 5 new thin wrapper functions
rubrics/templates/                      — 4 starter template JSON files
  general_agent.json
  rag_pipeline.json
  customer_support.json
  code_generation.json
app/page_rubric.py                      — Streamlit rubric builder page
app/app.py                              — Add "Rubric Builder" to navigation
tests/test_rubric_builder.py            — Unit tests
specs/010-custom-rubric-builder/        — This spec directory
```

## User Stories

### US1 (P1): Template-based rubric creation
Users can start from one of 4 templates, edit dimensions, and save a versioned rubric file.

**Done when**: All 4 templates load; dimensions are editable (name, title, description, scale, weight, evidence_required, scoring_guide); save writes `rubrics/v{N}_{name}.json` validated against schema.

### US2 (P1): Dimension management
Users can add, remove, and reorder dimensions within the builder.

**Done when**: "Add Dimension" creates a blank dimension; "Remove" deletes it; ↑/↓ buttons swap adjacent dimensions; at least one dimension must remain.

### US3 (P1): Validation and preview
Users can preview the rubric as JSON and (simplified) YAML, and run explicit schema validation before saving.

**Done when**: JSON preview tab shows correct representation; YAML preview tab shows a human-readable representation; "Validate" shows green success or red error list; Save is blocked if validation fails.

### US4 (P2): Rubric mismatch warning in comparison
When comparing two runs that used different rubric versions, show a visible warning.

**Done when**: `compare_runs()` reads rubric version from each run record and returns a `rubric_mismatch` flag; `page_compare.py` displays a warning banner when flag is set.

## Architecture Decisions

- **Version auto-increment**: scan `rubrics/` for `v*_{name}.json`, take max N, use N+1
- **Template format**: JSON (no YAML dependency)
- **Dimension editor**: `st.expander` per dimension (not `st.dialog`) — simpler state management
- **Reorder**: ↑/↓ swap buttons in session state list
- **YAML preview**: stdlib-only minimal formatter (rubric structure is shallow and known)
- **Scoring guide keys**: auto-derived from scale (`"0-2"` → `["0","1","2"]`)
- **Rubric mismatch**: extract version stem from `run.json#rubric_path`, compare, add flag to `ComparisonResult`
