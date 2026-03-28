# Research: Selective Evaluation (007)

**Date**: 2026-03-28 | **Branch**: master

---

## 1. Tag Derivation — Existing Infrastructure

**Decision**: Extend `tag_trace()` in `tagger.py` with structural tags; call live during filtering.

**Finding**: `src/agenteval/core/tagger.py` already implements `tag_trace(trace) -> tuple[str, ...]` with four failure-pattern tags:
- `incomplete_execution`
- `hallucination_tool_output`
- `ui_mismatch`
- `format_violation`

`scorer.py` already calls `tag_trace()` and stores results as `auto_tags` in every `AutoEvaluation`. The spec's "auto-detected tags" (e.g., `has_tool_calls`, `multi_step`) are *structural* tags, not yet implemented. We add them alongside the existing failure tags.

**Rationale**: Reuse `tag_trace()` infrastructure. Add structural tags (`has_tool_calls`, `multi_step`, `has_final_answer`) directly to `tagger.py` so they appear in `AutoEvaluation.auto_tags` as well — no parallel derivation path needed.

**Alternatives considered**:
- Sidecar `tags.json` per case — rejected (clarification Q1: live derivation chosen)
- Separate `derive_filter_tags()` in `filtering.py` — rejected (duplication of tagger logic)

---

## 2. Case Metadata Source — Failure Type & Severity

**Decision**: Parse `expected_outcome.md` YAML front matter via `load_case_metadata()` in `service.py`.

**Finding**: `service.py` already implements `load_case_metadata(case_dir) -> dict` which extracts `primary_failure` and `severity` from the YAML front matter of `expected_outcome.md`. The front matter fields are:
```yaml
primary_failure: Tool Hallucination
severity: Critical
```

`filter_cases()` will call `load_case_metadata()` per case to resolve failure type and severity filters.

**Rationale**: Single canonical source. No duplication of YAML parsing logic.

**Edge**: Generated cases via `ingest_trace()` write placeholder `primary_failure: unknown` and `severity: unknown` — these will not match any specific filter (correct behavior).

---

## 3. Filtering Module — New File

**Decision**: Create `src/agenteval/core/filtering.py` as a standalone library module.

**Rationale**: Constitution Principle VIII (Library-First) requires all business logic in `src/agenteval/`. Filtering logic is pure Python with no external deps — fits the Principle V (Minimal Dependencies) constraint perfectly.

**AND logic** (clarification Q4): all specified criteria are applied as intersection. A case must match every non-None filter to be included.

**Glob pattern** (clarification Q5): `fnmatch.fnmatch()` from stdlib — no regex, no new deps.

---

## 4. CLI Scope — Auto-Score Only

**Decision**: Add filter args to `agenteval-auto-score` only. `agenteval-eval-runner` is out of scope.

**Finding**: `scorer.py:main()` already uses `argparse`. The `score_dataset()` function accepts a `case_dirs` iterable — we can pass the filtered subset directly. No changes needed to `score_dataset()` internals.

**Implementation pattern**:
```python
# In scorer.main():
all_cases = list(dataset_dir.iterdir())
filtered = filter_cases(all_cases, failure_type=..., severity=..., tags=..., pattern=..., case_ids=...)
results = score_dataset(case_dirs=filtered, ...)
```

---

## 5. Batch Failure Behavior — Continue and Collect

**Decision**: Continue on failure, collect per-case errors, surface summary at end.

**Finding**: `score_dataset()` already implements this pattern:
```python
try:
    result = score_case(case_dir, rubric, registry)
    ...
except Exception as exc:
    print(f"{case_dir.name}: scoring error: {exc}", file=sys.stderr)
```

The existing per-case `try/except` in `score_dataset()` is exactly the right pattern. We extend it to track errors and return them in the service layer result.

**Rationale**: Consistent with `EvaluatorRegistry` per-dimension error isolation (clarification Q2).

---

## 6. Service Layer Additions

**Decision**: Add `run_selective_evaluation(case_ids, ...)` to `service.py`.

**Finding**: Existing `run_auto_scoring()` in `service.py` calls `score_dataset(dataset_dir=..., ...)` with no case filtering. We add `run_selective_evaluation()` that:
1. Resolves full case dirs from `case_ids`
2. Calls `score_dataset()` on the subset
3. Wraps with run tracking (same pattern as `run_auto_scoring()`)

**Structural tags needed for UI**: The UI filter dropdowns need to know which tags exist in the dataset. `get_dataset_tags(dataset_dir)` will scan all cases and return the union of tags — called once on page load.

---

## 7. UI Integration Points

**Decision**: Selective evaluation UI lives in `page_evaluate.py` (case selection before triggering auto-score).

**Finding**: `page_evaluate.py` currently has a single "Run Evaluation" button. We add:
- A case list with checkboxes (multi-select)
- Filter controls (failure type, severity, tag, pattern)
- "Evaluate Selected (N)" and "Evaluate All Filtered" buttons
- Clear labeling: "Run Auto-Scoring on selected cases"

The single-case "Evaluate This Case" button belongs in `page_inspect.py` (per spec) — that page already has per-case context.

---

## 8. Constitution Compliance

| Principle | Status |
|---|---|
| I. Security First | ✅ No new file I/O paths; all use existing `_safe_resolve_within()` |
| II. Schema-First | ✅ No schema changes; filtering is pre-scoring |
| III. Offline & Sandboxed | ✅ All filtering is local filesystem reads |
| IV. Test-Driven | ✅ `filtering.py` ships with full unit test coverage |
| V. Minimal Dependencies | ✅ `fnmatch` (stdlib); no new runtime deps |
| VI. Dataset Completeness | ✅ Filtering skips incomplete cases gracefully |
| VII. Backward-Compatible | ✅ New CLI args default to no-op (full dataset behavior preserved) |
| VIII. Library-First | ✅ All logic in `src/agenteval/core/filtering.py` |
