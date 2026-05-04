# Implementation Plan: Run Comparison

**Branch**: `008-run-comparison` | **Date**: 2026-05-04 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/008-run-comparison/spec.md`

---

## Summary

Enable side-by-side comparison of any two evaluation runs to detect score regressions and improvements. Implemented as a pure computation module (`comparison.py`) that reads existing run artifacts, a new CLI entry point (`agenteval-compare`), a service layer function, a JSON schema for validation, and a Streamlit comparison page.

---

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `jsonschema>=4.21.0` (already required); `streamlit` (optional, already under `[ui]`); `pyyaml` (already present)  
**Storage**: Files — reads from `runs/<run_id>/`, optionally writes `comparison.json` to disk  
**Testing**: pytest (existing suite)  
**Target Platform**: Windows/Linux/macOS local dev  
**Project Type**: Library + CLI + optional Streamlit UI  
**Performance Goals**: Comparison of 20-case runs in <1s  
**Constraints**: No new runtime dependencies; zero network calls; all paths via `_safe_resolve_within()`  
**Scale/Scope**: Dozens of runs, up to ~100 cases per run

---

## Constitution Check

| Rule | Status | Notes |
|------|--------|-------|
| No secrets/credentials | ✅ Pass | No auth involved |
| No external URLs | ✅ Pass | Local file reads only |
| No absolute paths in case files | ✅ Pass | Paths computed via `_get_repo_root()` |
| No path traversal | ✅ Pass | `_safe_resolve_within()` on all run paths |
| Security validation runs offline | ✅ Pass | No network calls |
| No new runtime dependencies | ✅ Pass | `jsonschema` already present |
| Keep core pipeline intact | ✅ Pass | Additive: new `comparison.py`, no modifications to runner/report |

---

## Project Structure

```text
src/agenteval/core/
├── comparison.py           # NEW — comparison engine + CLI entry point
├── service.py              # MODIFY — add compare_runs() service function

app/
├── page_compare.py         # NEW — Streamlit comparison page
├── app.py                  # MODIFY — add "Compare" to sidebar nav

schemas/
├── comparison_schema.json  # NEW — JSON schema for ComparisonResult

tests/
├── test_comparison.py      # NEW — unit + integration tests

pyproject.toml              # MODIFY — add agenteval-compare CLI entry point
docs/
├── run_comparison.md       # NEW — comparison workflow guide
```

---

## Complexity Tracking

No constitution violations. Single-project, additive changes only.
