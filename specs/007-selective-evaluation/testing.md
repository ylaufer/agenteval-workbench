# Manual Test Cases — Feature 007: Selective Evaluation

## Status: COMPLETE ✅

### Bugs found and fixed
- **OSError on "Run Full Evaluation"**: `print(..., flush=True)` in `runner.py` fails on Windows in Streamlit context. Fixed by redirecting stdout to StringIO in `service.py` before calling `runner_main()`.
- **`RunRecord` missing `filter_criteria` field**: `_write_filter_criteria()` patched run.json but `RunRecord` had no matching field, causing `__init__()` crash on `complete_run`/`fail_run`. Fixed by adding `filter_criteria: dict | None = None` to `RunRecord` and propagating it through `complete_run`/`fail_run`.

---

## Evaluate Page — Filter Controls

**TC-01** Failure Type filter
- Go to **Evaluate** in the sidebar
- In the **Failure Type** dropdown, select any value (e.g. "Tool Hallucination")
- Expected: case list narrows to matching cases only

**TC-02** Severity filter
- Clear failure type, open **Severity** multiselect, pick "Critical"
- Expected: case list updates to only Critical cases

**TC-03** Tags filter
- Open **Tags** multiselect, pick `has_tool_calls`
- Expected: only cases whose trace contains at least one tool_call step shown

**TC-04** Case ID Pattern — matching
- Type `case_*` in the **Case ID Pattern** field
- Expected: all cases starting with "case_" match

**TC-05** Case ID Pattern — no match
- Type `generated_*` in the **Case ID Pattern** field
- Expected: only generated cases shown, or "No cases match the current filter" if none exist

**TC-06** AND logic (combined filters)
- Set Severity = Critical AND Tag = has_tool_calls simultaneously
- Expected: result set is smaller than or equal to either filter alone (intersection, not union)

---

## Evaluate Page — Selective Scoring

**TC-07** Score selected cases
- With cases visible, check 1–2 individual checkboxes
- Click **Run Auto-Scoring on Selected (N)**
- Expected: results table appears below with one row per scored case, showing dimension scores and auto-tags

**TC-08** Score all filtered cases
- Clear individual checkboxes
- Click **Evaluate All Filtered (N)**
- Expected: all currently filtered cases are scored and shown in results table

**TC-09** Run History — filter criteria recorded
- After scoring in TC-07 or TC-08, scroll to **Run History** at the bottom
- Expected: the **Filter** column shows the criteria used (not "all cases")

---

## Evaluate Page — Edge Cases

**TC-10** Zero-match filter
- Set Case ID Pattern to `zzz_*`
- Expected: "No cases match the current filter" message shown; both scoring buttons disabled

**TC-11** Full evaluation (existing behaviour preserved)
- Expand **Run evaluation on all cases**
- Click **Run Full Evaluation**
- Expected: all cases evaluated, no error

---

## Inspect Page — Single Case Scoring

**TC-12** Score single case inline
- Go to **Inspect**, select any case from the dropdown
- Scroll to the bottom of the trace view
- Click **Run Auto-Scoring on this case**
- Expected: results table appears inline showing dimension scores and auto-tags for that case

---

## CLI

**TC-13** Filter by tag
```bash
agenteval-auto-score --filter-tag "has_tool_calls" --filter-severity Critical
```
Expected: only Critical cases with tool calls scored; summary printed; exit 0

**TC-14** Unknown case ID warning
```bash
agenteval-auto-score --cases nonexistent_case_999
```
Expected: warning printed for unknown ID, "No cases matched" message, exit 0

**TC-15** Pattern filter
```bash
agenteval-auto-score --filter-pattern "case_0*"
```
Expected: only cases matching the glob pattern are scored
