# Implementation Plan: Auto-Scoring Engine

**Branch**: `004-auto-scoring-engine` | **Date**: 2026-03-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/004-auto-scoring-engine/spec.md`

## Summary

Add an automatic scoring engine that evaluates benchmark cases against rubric dimensions using pluggable evaluators. Rule-based evaluators use deterministic trace analysis (extending the existing tagger pattern). LLM-based evaluators send trace + rubric context to a language model. Both produce structured auto-evaluation output files that coexist with manual reviewer scores. The existing runner and report modules remain unmodified; auto-scoring is a new parallel pipeline orchestrated through the service layer.

## Technical Context

**Language/Version**: Python >= 3.10 with `from __future__ import annotations`
**Primary Dependencies**: `jsonschema` (existing). LLM evaluators use `httpx` or stdlib `urllib` for API calls (optional dependency under `[llm]` extras).
**Storage**: JSON files under `runs/<run_id>/` or `reports/` (filesystem, no database)
**Testing**: pytest (existing), strict mypy/ruff gates
**Target Platform**: Windows/Linux/macOS (cross-platform, offline-first for rule-based)
**Project Type**: Library with CLI entry points and optional Streamlit UI
**Performance Goals**: Rule-based scoring < 5 seconds for 12 cases; LLM scoring depends on API latency
**Constraints**: Offline-capable for rule-based evaluators; LLM evaluators require network access (optional)
**Scale/Scope**: 12 benchmark cases, 6 rubric dimensions, extensible to more

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Security First | PASS | No secrets in outputs; LLM API keys via env vars only, never persisted |
| II. Schema-First Contracts | PASS | New `auto_evaluation_schema.json` for output validation |
| III. Offline & Sandboxed | CONDITIONAL PASS | Rule-based evaluators (MVP) are fully offline. LLM evaluators require network access but are: (1) opt-in via explicit configuration, (2) never imported by default, (3) isolated in `evaluators/llm_evaluator.py` — no core code path initiates network calls without user intent. |
| IV. Test-Driven Quality | PASS | Tests required for all evaluators, registry, and CLI |
| V. Minimal Dependencies | PASS | Rule-based: stdlib only. LLM: optional dependency under `[llm]` extras |
| VI. Dataset Completeness | PASS | Auto-scoring reads cases, never modifies them |
| VII. Backward-Compatible | PASS | New module; runner.py and report.py unchanged |
| VIII. Library-First | PASS | All logic in `src/agenteval/core/scorer.py` + evaluator modules; CLI is thin wrapper |

**Note on Principle III (Offline)**: LLM-based evaluators require network access, which appears to conflict with the offline mandate. This is resolved by:
1. LLM evaluators are an optional, clearly separated component (not imported by default)
2. Rule-based evaluators (P1 MVP) are fully offline
3. The LLM dependency is under an optional extras group (`[llm]`)
4. The system works without LLM evaluators — they enhance, not enable, the feature

## Project Structure

### Documentation (this feature)

```text
specs/004-auto-scoring-engine/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/agenteval/
├── core/
│   ├── scorer.py            # NEW — Auto-scoring orchestrator + CLI entry point
│   ├── evaluators/          # NEW — Pluggable evaluator modules
│   │   ├── __init__.py      # EvaluatorRegistry
│   │   ├── base.py          # Abstract Evaluator protocol/base class
│   │   ├── tool_use.py      # Rule-based: tool_use dimension
│   │   └── security.py      # Rule-based: security_safety dimension
│   ├── service.py           # MODIFIED — add run_auto_scoring() orchestration
│   ├── report.py            # MODIFIED — include auto scores in aggregation
│   └── types.py             # MODIFIED — add AutoEvaluation, DimensionScoreResult types
├── schemas/
│   └── auto_evaluation.py   # NEW — Python bindings for auto_evaluation_schema.json

schemas/
└── auto_evaluation_schema.json  # NEW — JSON schema for auto-evaluation output

tests/
├── test_scorer.py           # NEW — scorer orchestrator tests
├── test_evaluators.py       # NEW — individual evaluator tests
└── test_service.py          # MODIFIED — add auto-scoring integration tests
```

**Structure Decision**: Follows existing `src/agenteval/core/` layout. Evaluators get their own sub-package (`evaluators/`) since the pluggable architecture requires multiple modules. This mirrors how `tagger.py` works but with a registry pattern for extensibility.
