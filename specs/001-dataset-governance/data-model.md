# Data Model: Dataset Governance

**Feature**: 001-dataset-governance
**Date**: 2026-03-21

## Entity: ValidationIssue (MODIFIED)

Existing frozen dataclass. Adding `severity` field.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| case_id | str | yes | Identifier of the case (directory name) |
| file_path | str | yes | Path to the file with the issue |
| message | str | yes | Human-readable error/warning description |
| severity | str | yes (NEW) | `"error"` or `"warning"` |

**Constraints**:
- `severity` MUST be one of `"error"`, `"warning"`
- Frozen dataclass (immutable after creation)

## Entity: ValidationResult (UNCHANGED)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ok | bool | yes | `True` if zero errors (warnings allowed) |
| issues | tuple[ValidationIssue, ...] | yes | All issues found across all cases |

**Constraints**:
- `ok` is `True` only when no issues with `severity="error"` exist
- Warnings do not affect `ok`

## Entity: ExpectedOutcomeHeader (FORMALIZED)

YAML front matter in `expected_outcome.md`. Not a Python dataclass — validated programmatically.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Case ID | str | yes | Case identifier matching the directory name |
| Primary Failure | str | yes | Primary failure category from taxonomy |
| Secondary Failures | str | yes | Comma-separated list (may be empty string) |
| Severity | str | yes | One of: Low, Moderate, High, Critical |
| case_version | str | yes (NEW) | Numeric version, e.g., `1.0`, `1.1`, `2.0` |

**Constraints**:
- All five fields MUST be present for validation to pass
- `case_version` format: `MAJOR.MINOR` numeric (e.g., `1.0`, `1.1`)
- Version bump required when `trace.json` or `expected_outcome.md` content changes

## Entity: CaseEvaluationTemplate (MODIFIED)

Existing frozen dataclass in `types.py`. Adding `case_version` field.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| ... | ... | ... | All existing fields unchanged |
| case_version | str \| None | no (NEW) | Version from `expected_outcome.md` header; `None` if header lacks it |

**Constraints**:
- `case_version` is included in both JSON and Markdown evaluation templates
- Runner reads it from the parsed header and passes it through

## Entity: GeneratedCase (CONCEPTUAL)

Not a Python dataclass — the generator produces three files in a directory. Documenting the contract.

| Output File | Content | Description |
|-------------|---------|-------------|
| prompt.txt | Plain text | Agent prompt (generic or failure-specific) |
| trace.json | JSON (schema-valid) | Agent execution trace with steps |
| expected_outcome.md | Markdown with YAML header | Expected result with all 5 required header fields |

**Constraints**:
- Generated case MUST pass all validation checks immediately
- `case_version` defaults to `1.0` for new generated cases
- If `failure_type` is provided, the trace, prompt, and header reflect that failure pattern

## State Transitions

### Case Lifecycle

```
[New Case] → generate or author manually
    ↓
[Unvalidated] → run validator
    ↓
[Valid / Invalid]
    ↓ (if valid)
[Committed] → modify content
    ↓
[Modified] → bump case_version → re-validate → commit
```

### Validation Issue Severity

```
Missing file        → error (blocks)
Schema violation    → error (blocks)
Security violation  → error (blocks)
Missing header field → error (blocks)
Version bump missing → warning (advisory)
```
