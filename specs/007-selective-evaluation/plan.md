# Implementation Plan: Selective Evaluation

**Branch**: `master` | **Date**: 2026-03-28 | **Spec**: `specs/007-selective-evaluation/spec.md`
**Input**: Feature specification from `/specs/007-selective-evaluation/spec.md`

---

## Summary

Adds selective evaluation to `agenteval-auto-score` — filtering cases by failure type, severity, tags, or glob pattern before auto-scoring runs. Implemented as a new `filtering.py` library module, extended `scorer.py` CLI args, a `run_selective_evaluation()` service function, and updated Streamlit UI with case selection controls.

---

## Technical Context

**Language/Version**: Python 3.10+, `from __future__ import annotations`
**Primary Dependencies**: `jsonschema>=4.21.0` (existing); `fnmatch` (stdlib — no new deps)
**Storage**: Filesystem (existing `data/cases/` + `runs/`)
**Testing**: pytest
**Target Platform**: Cross-platform (Windows/Linux/macOS)
**Project Type**: Library + CLI + Streamlit UI
**Performance Goals**: Filtering 50 cases < 1s (all file reads are local); scoring N cases ≈ N × single-case time
**Constraints**: Zero new runtime dependencies; all file I/O within repo root via `_safe_resolve_within()`
**Scale/Scope**: 10–100 benchmark cases; filtering is O(N) per case

---

## Constitution Check

| Principle | Gate | Status |
|---|---|---|
| I. Security First | No new file I/O paths; all use `_safe_resolve_within()` | ✅ PASS |
| II. Schema-First | No schema changes; `auto_tags` field already exists | ✅ PASS |
| III. Offline & Sandboxed | All filtering is local; no network calls | ✅ PASS |
| IV. Test-Driven | `filtering.py` + tagger extensions ship with tests | ✅ PASS |
| V. Minimal Dependencies | `fnmatch` is stdlib; no new runtime deps | ✅ PASS |
| VI. Dataset Completeness | Missing `expected_outcome.md` → case excluded from filter, not error | ✅ PASS |
| VII. Backward-Compatible | New CLI args default to no-op; `score_dataset()` signature extended with optional `case_filter` | ✅ PASS |
| VIII. Library-First | All filtering logic in `src/agenteval/core/filtering.py`; UI and CLI are thin wrappers | ✅ PASS |

---

## Project Structure

### Documentation (this feature)

```text
specs/007-selective-evaluation/
├── spec.md              ← Feature specification (clarified 2026-03-28)
├── plan.md              ← This file
├── research.md          ← Phase 0 research findings
├── data-model.md        ← Entity definitions and module layout
├── quickstart.md        ← Usage guide
├── contracts/
│   ├── library-contracts.md
│   └── cli-contracts.md
└── tasks.md             ← Phase 2 output (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code Changes

```text
src/agenteval/core/
├── filtering.py          ← NEW: filter_cases(), derive_structural_tags(), get_dataset_tags()
├── tagger.py             ← MODIFIED: add has_tool_calls, multi_step, has_final_answer tags
├── scorer.py             ← MODIFIED: add --cases/--filter-* CLI args + case_filter param
└── service.py            ← MODIFIED: add run_selective_evaluation(), get_dataset_tags()

app/
├── page_evaluate.py      ← MODIFIED: case selection UI + filter controls
└── page_inspect.py       ← MODIFIED: "Evaluate This Case" button

tests/
└── test_filtering.py     ← NEW: unit tests for filtering.py + extended tagger
```

---

## Phase 0: Research Findings

See `research.md` for full details. Key decisions:

1. **Tag derivation**: Extend `tagger.py` with structural tags (`has_tool_calls`, `multi_step`, `has_final_answer`); derive live from `trace.json` — no pre-indexing or sidecars.
2. **Metadata source**: `load_case_metadata()` in `service.py` already parses `expected_outcome.md` YAML front matter. Filtering reads `primary_failure` and `severity` from there.
3. **Filtering module**: New `filtering.py` — pure stdlib, zero new deps.
4. **CLI scope**: `agenteval-auto-score` only. `agenteval-eval-runner` unchanged.
5. **Batch failure**: Continue-and-collect pattern (extends existing `score_dataset()` try/except).
6. **Filter logic**: AND (intersection) across all criteria; `case_ids` overrides all filters.
7. **Pattern syntax**: Glob via `fnmatch.fnmatch()` — no regex.

---

## Phase 1: Design

### `filtering.py` — Core Logic

```python
import fnmatch
from pathlib import Path
from typing import Any

from agenteval.core.loader import load_trace
from agenteval.core.tagger import tag_trace
from agenteval.schemas.trace import Trace


def filter_cases(
    case_dirs: list[Path],
    case_ids: list[str] | None = None,
    failure_type: str | None = None,
    severity: list[str] | None = None,
    tags: list[str] | None = None,
    pattern: str | None = None,
) -> list[Path]:
    # If explicit case_ids given, short-circuit all other filters
    if case_ids:
        id_set = set(case_ids)
        return [d for d in case_dirs if d.name in id_set]

    result = []
    for case_dir in case_dirs:
        if pattern and not fnmatch.fnmatch(case_dir.name, pattern):
            continue
        if failure_type is not None or severity is not None:
            meta = _read_metadata(case_dir)
            if failure_type and meta.get("primary_failure", "").lower() != failure_type.lower():
                continue
            if severity:
                case_sev = meta.get("severity", "").strip()
                if case_sev.lower() not in [s.lower() for s in severity]:
                    continue
        if tags:
            case_tags = _get_tags(case_dir)
            if not all(t in case_tags for t in tags):
                continue
        result.append(case_dir)
    return result
```

### `tagger.py` — Structural Tags Extension

Add to `tag_trace()`:
```python
# Structural tags
if any(s["type"] == "tool_call" for s in steps):
    tags.append("has_tool_calls")
if len(steps) > 3:
    tags.append("multi_step")
if any(s["type"] == "final_answer" for s in steps):
    tags.append("has_final_answer")
```

### `scorer.py` — CLI Extension

```python
# New argparse args in main():
parser.add_argument("--cases", type=str, default=None,
    help="Comma-separated case IDs to score")
parser.add_argument("--filter-failure", type=str, default=None)
parser.add_argument("--filter-severity", type=str, default=None)
parser.add_argument("--filter-tag", type=str, default=None)
parser.add_argument("--filter-pattern", type=str, default=None)

# score_dataset() gains optional case_filter param:
def score_dataset(
    dataset_dir, output_dir, rubric_path=None, registry=None,
    case_filter: list[Path] | None = None,
) -> list[dict]:
    case_dirs = case_filter if case_filter is not None else sorted(...)
```

### `service.py` — New Functions

```python
def run_selective_evaluation(
    case_ids: list[str],
    dataset_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    """Run auto-scoring on a specific subset of cases with run tracking."""

def get_dataset_tags(dataset_dir: Path | None = None) -> set[str]:
    """Return union of all tags across dataset. Used by UI for tag dropdown."""
```

### `page_evaluate.py` — UI Changes

Replace single "Run Evaluation" button with:
1. Filter controls row: failure type dropdown, severity multiselect, tags multiselect, pattern text input
2. Case list with checkboxes (driven by `list_cases()` + `load_case_metadata()`)
3. "Evaluate All Filtered (N)" and "Evaluate Selected (N)" buttons
4. Label: "Run Auto-Scoring on selected cases" to clarify pipeline target

### `page_inspect.py` — UI Changes

Add "Evaluate This Case" button to per-case view, calling `run_selective_evaluation([case_id])`.

---

## Post-Design Constitution Check

All 8 principles confirmed passing (see Phase 0 gate table above). No rework required.
