# Tasks: Run Comparison (Feature 008)

**Branch**: `008-run-comparison`  
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md) | **Data Model**: [data-model.md](data-model.md)

---

## User Stories

| ID | Priority | Story |
|----|----------|-------|
| US1 | P1 | Core comparison engine: compare two runs, compute per-case and per-dimension score deltas, classify changes |
| US2 | P1 | CLI: `agenteval-compare` prints a summary table and optionally writes JSON |
| US3 | P2 | UI: side-by-side Streamlit comparison page with color-coded delta indicators |

---

## Phase 1: Setup

- [ ] T001 Add `agenteval-compare = "agenteval.core.comparison:main"` entry point to `pyproject.toml` under `[project.scripts]`
- [ ] T002 Create `schemas/comparison_schema.json` — JSON Schema validating `ComparisonResult` (comparison_id, run_a, run_b, timestamp, summary, dimension_deltas, case_deltas)

---

## Phase 2: Foundational

> Blocking prerequisites for all user stories. Complete before Phase 3.

- [ ] T003 Define `CaseDelta`, `DimensionDelta`, `ComparisonSummary`, `ComparisonResult` frozen dataclasses in `src/agenteval/core/comparison.py` (see data-model.md for all fields)
- [ ] T004 Implement `_parse_scale_max(scale: str) -> float` and `_normalize_score(raw: int, scale_max: float) -> float` helpers in `src/agenteval/core/comparison.py`
- [ ] T005 Implement `_compute_overall_score(dimensions: dict) -> float | None` — weighted average of normalized per-dimension scores, excluding null scores — in `src/agenteval/core/comparison.py`

---

## Phase 3: US1 — Core Comparison Engine

**Story goal**: `compare_runs(run_a_id, run_b_id)` returns a validated `ComparisonResult` with accurate per-case and per-dimension deltas.

**Independent test criteria**: `compare_runs()` can be called against real run directories and returns the correct case counts, delta signs, and `net_quality_change`.

- [ ] T006 [P] Write unit tests for `classify_change()` (all five statuses, null combinations) in `tests/test_comparison.py`
- [ ] T007 [P] Write unit tests for `_normalize_score()`, `_parse_scale_max()`, and `_compute_overall_score()` (happy path, all-null, partial null) in `tests/test_comparison.py`
- [ ] T008 Implement `classify_change(score_a: float | None, score_b: float | None) -> Literal["improved","regressed","unchanged"]` in `src/agenteval/core/comparison.py`
- [ ] T009 Implement `_build_case_deltas(results_a, results_b) -> list[CaseDelta]` — aligns cases by case_id, computes per-case overall and dimension deltas, classifies new/removed — in `src/agenteval/core/comparison.py`
- [ ] T010 Implement `_build_dimension_deltas(case_deltas) -> list[DimensionDelta]` — aggregates per-dimension stats (mean_score_a/b, mean_delta, cases_improved/regressed/unchanged) — in `src/agenteval/core/comparison.py`
- [ ] T011 Implement `compare_runs(run_a_id, run_b_id, repo_root=None) -> ComparisonResult` — loads runs via `get_run_results()`, assembles result, validates against `comparison_schema.json` — in `src/agenteval/core/comparison.py`
- [ ] T012 Write integration test for `compare_runs()` using two existing run directories (`runs/20260325T184347_ee91` and `runs/20260325T184409_b550`) in `tests/test_comparison.py`
- [ ] T013 Write edge case tests: missing run raises `FileNotFoundError`; runs with disjoint case sets produce correct new/removed counts; runs with all-null scores yield `net_quality_change = "insufficient_data"` — in `tests/test_comparison.py`

---

## Phase 4: US2 — CLI Interface

**Story goal**: `agenteval-compare --run-a <id> --run-b <id>` prints a formatted summary; `--output-json <path>` writes full JSON.

**Independent test criteria**: CLI exits 0 with a table on valid runs; exits 1 with an error message on missing run.

- [ ] T014 Implement `main(argv=None)` CLI function in `src/agenteval/core/comparison.py` — parses `--run-a/--run-b` (and `--baseline/--current` aliases), calls `compare_runs()`, prints summary table per contracts/cli.md, handles `--output-json`
- [ ] T015 Write CLI tests (valid run pair exits 0; missing run exits 1; `--output-json` writes valid JSON) in `tests/test_comparison.py`

---

## Phase 5: US3 — UI Comparison Page

**Story goal**: A Compare Runs page in the Streamlit app lets users select two runs, see summary metrics, a dimension delta table, and a sortable case-level table.

**Independent test criteria**: Page renders without errors; selecting two runs and clicking Compare populates all three sections.

> ⚠️ Before implementing any task in this phase, invoke `/developing-with-streamlit` skill.

- [ ] T016 Add `compare_runs(run_a_id, run_b_id) -> ComparisonResult` to `src/agenteval/core/service.py` as a thin wrapper around `comparison.compare_runs()`
- [ ] T017 Create `app/page_compare.py` — run selector dropdowns (populated from `service.list_runs()`), Compare button, session state for result caching
- [ ] T018 Add summary metrics section to `app/page_compare.py` — overall score delta with arrow indicator, cases improved/regressed/unchanged/new/removed, new/resolved failure types
- [ ] T019 Add dimension delta table to `app/page_compare.py` — columns: Dimension, Run A, Run B, Delta with color-coded delta cell (green/red/gray)
- [ ] T020 Add case-level delta table to `app/page_compare.py` — columns: Case, Run A, Run B, Delta, Status; sortable by delta magnitude; color-coded status
- [ ] T021 Register Compare Runs page in `app/app.py` sidebar navigation (import `page_compare`, add to page dict)

---

## Phase 6: Polish

- [ ] T022 [P] Write `docs/run_comparison.md` — comparison workflow guide, CLI reference, delta interpretation table (per quickstart.md)
- [ ] T023 [P] Update README to add `agenteval-compare` to the Key Commands section
- [ ] T024 Run `pytest tests/ -v` and confirm all tests pass; run `ruff check src/` and `mypy src/` and fix any issues

---

## Dependencies

```
T001, T002 (setup) → T003, T004, T005 (foundational)
                          ↓
            T006, T007 can run in parallel
            T008 → T009 → T010 → T011 → T012, T013
                                              ↓
                                         T014, T015 (CLI)
                                              ↓
                             T016 → T017 → T018 → T019 → T020 → T021 (UI)
                                                                      ↓
                                                              T022, T023, T024 (Polish)
```

## Parallel Execution Examples

**Phase 3 start** (after T005):
- T006 (classify_change tests) ‖ T007 (normalization tests)

**Phase 6**:
- T022 (docs) ‖ T023 (README)

---

## Implementation Strategy

**MVP scope (US1 + US2 only — Phases 1–4):**  
Delivers a working CLI and comparison engine with full test coverage. The UI can be added independently in Phase 5.

**Incremental delivery:**
1. Phases 1–2: Schema + dataclasses (no behavior, but compilable)
2. Phase 3: Core engine passes all tests
3. Phase 4: CLI entry point is functional
4. Phase 5: UI integrated — activate with `streamlit run app/app.py`
5. Phase 6: Docs + final validation

---

## Task Count

| Phase | Tasks |
|-------|-------|
| Setup | 2 |
| Foundational | 3 |
| US1 — Core Engine | 8 |
| US2 — CLI | 2 |
| US3 — UI | 6 |
| Polish | 3 |
| **Total** | **24** |

Parallel opportunities: T006‖T007, T022‖T023
