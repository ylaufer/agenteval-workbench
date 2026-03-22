# Research: Dataset Governance

**Feature**: 001-dataset-governance
**Date**: 2026-03-21

## R1: Validator Severity Model

**Decision**: Two-level severity (error / warning) using a string literal field on `ValidationIssue`.

**Rationale**: The spec explicitly requires two levels (clarification Q3). A simple string field (`"error"` | `"warning"`) avoids introducing an enum dependency and stays consistent with the existing frozen-dataclass pattern in `types.py`. `ValidationResult.ok` reflects errors only; warnings are informational.

**Alternatives considered**:
- Separate `warnings` tuple on `ValidationResult` — rejected because it doubles the collection logic and callers must check two lists.
- Numeric severity (0-3) — rejected as overengineered for a two-level model.

## R2: Case Generator Architecture

**Decision**: Extract generation logic into `src/agenteval/dataset/generator.py` with a `generate_case()` function that accepts case_id, failure_type (optional), output_dir, and overwrite flag. `execution.py` re-exports for backward compatibility.

**Rationale**: Constitution Principle VIII (Library-First) requires all logic in importable modules. Co-locating the generator with the validator in `dataset/` makes the package boundary clear: `dataset/` owns the case contract.

**Alternatives considered**:
- Keep generator in `core/execution.py` — rejected because generation is a dataset concern, not an evaluation concern.
- New `dataset/` subpackage with `__init__`, `validator.py`, `generator.py` — this is the chosen approach; `dataset/` already exists as a package.

## R3: YAML Header Validation

**Decision**: Validate the `expected_outcome.md` front matter programmatically inside the validator. Required fields: `Case ID`, `Primary Failure`, `Secondary Failures`, `Severity`, `case_version`.

**Rationale**: The runner already parses this header via `_parse_expected_outcome_header()`. The validator adds field-presence checks using the same parsing logic. No separate JSON Schema is needed since the header is YAML front matter in a Markdown file, not a standalone JSON document.

**Alternatives considered**:
- YAML Schema file (e.g., `schemas/expected_outcome_schema.yaml`) — rejected because it adds a new schema format (YAML Schema) and a new dependency. The header has only 5 fields; programmatic validation is simpler.
- JSON Schema for a JSON version of the header — rejected because it requires changing the file format.

## R4: Version-Bump Detection

**Decision**: Git-aware optional check inside the validation command. Uses `git diff HEAD` to detect changes to `trace.json` and `expected_outcome.md` without a `case_version` increment.

**Rationale**: The validator already receives the repo root. Calling `git diff --name-only HEAD -- <path>` via `subprocess` is lightweight, offline, and works in both local and CI contexts. When git is unavailable (fresh unzipped archive), the check is skipped silently — this is an advisory warning, not a blocking gate.

**Alternatives considered**:
- Content checksums stored in a manifest file — rejected as overengineered; git already tracks content changes.
- Separate CLI command for version-bump checks — rejected because the spec clarification (Q2) explicitly places this in the validation command.

## R5: Pre-Commit Framework

**Decision**: Use the `pre-commit` framework with a local hook definition in `.pre-commit-config.yaml`.

**Rationale**: `pre-commit` is the standard Python ecosystem tool for pre-commit hooks. It's portable across platforms, doesn't require manual `.git/hooks/` management, and integrates with CI. Added as a dev dependency only — does not affect runtime.

**Alternatives considered**:
- Raw `.git/hooks/pre-commit` script — rejected because it's not versioned by default and requires manual setup per contributor.
- Husky (Node.js) — rejected because the project is Python-only; introducing Node.js is unnecessary.

## R6: Failure-Type Presets for Generator

**Decision**: The generator accepts an optional `failure_type` string parameter matching the 12 canonical failure categories from `docs/failure_taxonomy.md`. When provided, the generated `expected_outcome.md` header, trace structure, and prompt are customized to match that failure pattern.

**Rationale**: The spec clarification (Q5) requires this capability for pipeline testing. The generator maps each failure type to a template trace that exhibits the failure pattern, enabling end-to-end evaluation pipeline testing.

**Alternatives considered**:
- Separate "case template" files per failure type — rejected as file proliferation; the templates are small enough to define in code.
- Only supporting a subset of failure types — rejected because all 12 types are already defined in the taxonomy.
