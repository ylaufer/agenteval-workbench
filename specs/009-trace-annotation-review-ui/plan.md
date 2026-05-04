# Implementation Plan: Trace Annotation & Review UI

**Branch**: `009-trace-annotation-review-ui` | **Date**: 2026-05-04 | **Spec**: `specs/009-trace-annotation-review-ui/spec.md`

## Summary

Enhance the Inspect page with three connected capabilities: (1) inline reviewer annotations on trace steps, persisted to `reports/{case_id}.annotations.json`; (2) auto-score overlay that color-codes steps and shows evaluator evidence inline; (3) evidence linking that highlights cited steps when reviewing evaluation results. Step-level diff view (US4) is deferred — it requires real trace variants that don't yet exist in the dataset.

## Technical Context

**Language/Version**: Python 3.10+, `from __future__ import annotations`
**Primary Dependencies**: `jsonschema>=4.21.0` (existing), `streamlit>=1.30.0` (UI, optional extra)
**Storage**: Filesystem — `reports/{case_id}.annotations.json`
**Testing**: pytest
**Target Platform**: Local desktop (Streamlit UI + CLI library)
**Project Type**: Library + Streamlit UI enhancement
**Performance Goals**: Annotation read/write < 50ms for typical cases (< 50 annotations)
**Constraints**: No new runtime dependencies; all file I/O within repo root via `_safe_resolve_within()`
**Scale/Scope**: Single-user lab tool; annotation files are small JSON (< 100 annotations per case typical)

## Constitution Check

| Principle | Status | Notes |
|---|---|---|
| I. Security First | ✅ PASS | Annotations stored locally; all paths via `_safe_resolve_within()`; no secrets in annotation content at validation time |
| II. Schema-First | ✅ PASS | `schemas/annotation_schema.json` added; validated on read and write |
| III. Offline | ✅ PASS | All I/O is local filesystem |
| IV. Test-Driven | ✅ PASS | `tests/test_annotations.py` required before implementation |
| V. Minimal Dependencies | ✅ PASS | No new runtime deps |
| VI. Dataset Completeness | ✅ PASS | Annotations stored in `reports/`, not `data/cases/` |
| VII. Backward Compatible | ✅ PASS | `page_inspect.py` enhanced, not replaced; existing CLI unaffected |
| VIII. Library-First | ✅ PASS | All logic in `src/agenteval/core/annotations.py`; UI is thin wrapper |

## Project Structure

```text
src/agenteval/core/annotations.py     — Annotation dataclass, CRUD, overlay builder
src/agenteval/core/service.py         — 4 new thin wrapper functions
schemas/annotation_schema.json        — JSON Schema for annotation files
app/components/annotation.py          — Streamlit annotation widget
app/page_inspect.py                   — Enhanced: overlay + annotations + evidence linking
tests/test_annotations.py             — Unit tests
specs/009-trace-annotation-review-ui/ — This spec directory
```

## User Stories

### US1 (P1): Inline Annotations
Reviewers can add text notes to specific trace steps. Notes persist across sessions and are visible to all reviewers viewing the same case.

**Done when**: Add Note form works; notes survive page reload; `reports/{case_id}.annotations.json` is valid per schema.

### US2 (P1): Auto-Score Overlay
When an auto-evaluation exists for a case, trace steps are color-coded and evaluator evidence is shown inline.

**Done when**: Steps with `evidence_step_ids` references show a dimension badge; steps without references are clean; case-level flags shown in sidebar; color coding is visible.

### US3 (P2): Evidence Linking
From the Evaluation section, clicking a cited step highlights it in the trace viewer.

**Done when**: Each `evidence_step_id` in the evaluation template has a "→ Jump" button; clicking it sets `st.session_state.highlighted_step` and the target step renders with a distinct border.

## Architecture Decisions

- **Annotation IDs**: `ann_` + 8 hex chars from `secrets.token_hex(4)`
- **Timestamps**: `datetime.now(timezone.utc).isoformat()`
- **Schema validation on write**: validate before writing to disk; fail loudly
- **Auto-eval lookup**: `reports/{case_id}.auto_evaluation.json` first; then scan `runs/*/` for most recent
- **highlighted_step**: `st.session_state["inspect_highlighted_step"]` — cleared when case selection changes
- **Reviewer name persistence**: `st.session_state["inspect_reviewer_id"]` — survives page reruns within session
