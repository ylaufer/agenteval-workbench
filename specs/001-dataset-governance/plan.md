# Implementation Plan: Dataset Governance

**Branch**: `001-dataset-governance` | **Date**: 2026-03-21 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-dataset-governance/spec.md`

## Summary

Extend the existing dataset validator and case generation tooling to enforce dataset governance: YAML header validation (5 required fields including `case_version`), error/warning severity levels, version-bump detection, failure-type presets for the generator, pre-commit hook automation, and case version propagation into evaluation templates. All new logic lives in `src/agenteval/` as library code; scripts remain thin wrappers.

## Technical Context

**Language/Version**: Python >= 3.10 (`from __future__ import annotations`)
**Primary Dependencies**: `jsonschema>=4.21.0` (only runtime dep)
**Storage**: Filesystem only — `data/cases/`, `schemas/`, `rubrics/`, `reports/`
**Testing**: pytest >= 8.0.0 with strict mypy/ruff gates
**Target Platform**: Cross-platform (Windows/Linux/macOS), offline-capable
**Project Type**: Library + CLI (src layout, entry points in pyproject.toml)
**Performance Goals**: Validate 100+ cases in < 5 seconds
**Constraints**: Offline only, no network calls, all I/O within repo root, single runtime dependency
**Scale/Scope**: ~12-50 cases, single-repo benchmark dataset

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Security First | PASS | Validator already enforces all security constraints; no changes to security scanning |
| II. Schema-First Contracts | PASS | Extending `expected_outcome.md` header validation; trace schema unchanged |
| III. Offline & Sandboxed | PASS | No network calls added; all I/O uses existing `_safe_resolve_within()` |
| IV. Test-Driven Quality | PASS | All new modules ship with pytest tests |
| V. Minimal Dependencies | PASS | No new runtime dependencies; `pre-commit` is dev-only |
| VI. Dataset Completeness | PASS | This feature directly enforces this principle |
| VII. Backward-Compatible | PASS | Existing CLI args unchanged; `case_version` defaults to `1.0` for existing cases without it |
| VIII. Library-First | PASS | All logic in `src/agenteval/`; scripts delegate to library functions |

No violations. All gates pass.

## Project Structure

### Documentation (this feature)

```text
specs/001-dataset-governance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-contracts.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/agenteval/
├── dataset/
│   ├── __init__.py
│   ├── validator.py          # MODIFY: add header validation, severity levels, version-bump warning
│   └── generator.py          # NEW: case generation library (extracted from execution.py)
├── core/
│   ├── types.py              # MODIFY: extend CaseEvaluationTemplate with case_version field
│   ├── runner.py             # MODIFY: include case_version in evaluation templates
│   ├── execution.py          # MODIFY: delegate to dataset.generator, keep as thin wrapper
│   ├── loader.py             # No changes
│   ├── report.py             # No changes
│   ├── tagger.py             # No changes
│   └── calibration.py        # No changes
└── schemas/
    ├── trace.py              # No changes
    └── rubric.py             # No changes

scripts/
├── generate_trace.py         # MODIFY: delegate to dataset.generator library
└── run_eval.py               # No changes

tests/
├── test_validator.py          # MODIFY: add tests for header validation, severity, version-bump
├── test_generator.py          # NEW: tests for case generation library
├── test_runner.py             # MODIFY: add test for case_version in templates
└── ...                        # Existing test files unchanged

.pre-commit-config.yaml        # NEW: pre-commit hook for dataset validation

data/cases/
├── case_001/                  # MODIFY: add case_version to expected_outcome.md header
├── ...
└── case_012/                  # MODIFY: add case_version to expected_outcome.md header
```

**Structure Decision**: Single project, existing `src/` layout. New code follows the established pattern: library modules under `src/agenteval/`, CLI entry points in `pyproject.toml`, convenience scripts in `scripts/`.

## Complexity Tracking

No constitution violations to justify.

## Key Design Decisions

### 1. Validator Severity Model

The existing `ValidationIssue` dataclass gains a `severity` field with two levels:
- **error**: Missing files, schema violations, security violations, missing required header fields → non-zero exit
- **warning**: Version-bump detection → reported but does not affect exit code

`ValidationResult.ok` remains `True` only when zero errors exist. Warnings are collected in the same `issues` tuple but do not flip `ok` to `False`.

### 2. Case Generator Placement

The case generation logic currently lives in `src/agenteval/core/execution.py`. Per Library-First Architecture (Principle VIII), the generation library moves to `src/agenteval/dataset/generator.py` — co-located with the validator since both operate on the dataset contract. `execution.py` becomes a thin import re-export to preserve backward compatibility.

### 3. Header Validation Strategy

Rather than a separate schema file for `expected_outcome.md`, the validator validates the YAML front matter inline using the existing `_parse_expected_outcome_header` pattern from `runner.py`. The five required fields (`Case ID`, `Primary Failure`, `Secondary Failures`, `Severity`, `case_version`) are checked programmatically.

### 4. Version-Bump Detection

FR-011 requires detecting content changes without a version bump. Since the validator runs against the working tree (not git diffs), the detection is implemented as a git-aware optional check:
- If inside a git repo with history, compare `trace.json` and `expected_outcome.md` against `HEAD` for staged/unstaged changes
- If changes are detected and `case_version` is unchanged, emit a warning
- If not in a git repo (e.g., fresh clone, CI), skip version-bump detection silently

### 5. Backward Compatibility for Existing Cases

Existing cases lack `case_version`. Migration strategy:
- Add `case_version: 1.0` to all 12 existing cases in a single commit
- The validator treats missing `case_version` as an error (FR-009) after this migration
- No grace period — the migration commit is part of this feature's implementation

### 6. Pre-Commit Hook

A `.pre-commit-config.yaml` using a local hook runs `agenteval-validate-dataset --repo-root .` before every commit. This is a `pre-commit` framework hook (dev dependency), not a raw git hook, for portability and ease of setup.

### 7. Header Parser Duplication

Both `validator.py` and `runner.py` parse the `expected_outcome.md` YAML front matter. This is intentional: the validator checks field presence (5 required fields) while the runner extracts field values for template generation. Extracting a shared parser was considered but rejected — the two parsers have different error handling needs (validator collects ValidationIssues; runner raises on malformed headers) and coupling them would violate the module boundary between `dataset/` and `core/`.
