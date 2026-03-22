# CLI Contracts: Dataset Governance

**Feature**: 001-dataset-governance
**Date**: 2026-03-21

## agenteval-validate-dataset (MODIFIED)

Existing command. Backward-compatible changes only.

### Arguments (unchanged)

```
agenteval-validate-dataset --repo-root <path>
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| --repo-root | no | auto-detect | Repository root directory |

### Exit Codes (unchanged behavior, refined semantics)

| Code | Meaning |
|------|---------|
| 0 | All cases valid (warnings may be present) |
| 1 | One or more validation errors found |

### Output Format (extended)

Errors are prefixed with the case identifier and categorized:

```
[case_001] ERROR: Missing required file: prompt.txt
[case_002] ERROR: trace.json schema violation: 'task_id' is a required property
[case_003] ERROR: Security violation in trace.json: API key pattern detected
[case_004] ERROR: expected_outcome.md missing required header field: case_version
[case_005] WARNING: trace.json modified without case_version bump (1.0 → 1.0)
```

- Lines starting with `ERROR:` correspond to `severity="error"` issues
- Lines starting with `WARNING:` correspond to `severity="warning"` issues
- Exit code is non-zero only when at least one ERROR exists

### New Validation Checks

1. **Header field validation**: `expected_outcome.md` YAML header MUST contain all 5 required fields: `Case ID`, `Primary Failure`, `Secondary Failures`, `Severity`, `case_version`
2. **Version-bump detection** (git-aware, advisory): warns when `trace.json` or `expected_outcome.md` content changed without a `case_version` increment

---

## agenteval-generate-case (NEW)

New CLI entry point for case generation.

### Arguments

```
agenteval-generate-case [--case-id <id>] [--failure-type <type>] [--output-dir <dir>] [--overwrite]
```

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| --case-id | no | auto-generated | Case directory name (e.g., `demo_case`) |
| --failure-type | no | none (generic pass) | Failure category from taxonomy |
| --output-dir | no | `data/cases` | Parent directory for the case |
| --overwrite | no | false | Allow overwriting existing case directory |

### Valid --failure-type Values

Matches the 12 canonical failure categories:
`tool_hallucination`, `unnecessary_tool_invocation`, `instruction_drift`, `partial_completion`, `tool_schema_misuse`, `ui_grounding_mismatch`, `unsafe_output`, `format_violation`, `latency_mismanagement`, `reasoning_inconsistency`, `constraint_violation`, `incomplete_execution`

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Case generated successfully |
| 1 | Error (e.g., case already exists without --overwrite, invalid failure type) |

### Output

```
Generated case at data/cases/<case_id>
```

### Library Function

```python
# src/agenteval/dataset/generator.py
def generate_case(
    case_id: str | None = None,
    failure_type: str | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> Path:
    """Generate a complete, schema-valid case directory.

    Returns the path to the created case directory.
    Raises ValueError if case exists and overwrite is False.
    Raises ValueError if failure_type is not a valid taxonomy entry.
    """
```

---

## agenteval-eval-runner (MODIFIED)

### Changes

- Evaluation templates (JSON and Markdown) now include `case_version` when present in the `expected_outcome.md` header
- No changes to CLI arguments or exit codes
- Backward compatible: if `case_version` is absent, the field is `null` in JSON and omitted from Markdown

---

## Pre-Commit Hook Contract

### .pre-commit-config.yaml

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-dataset
        name: Validate AgentEval dataset
        entry: agenteval-validate-dataset --repo-root .
        language: system
        pass_filenames: false
        always_run: true
```

### Behavior

- Runs before every `git commit`
- Blocks commit if any validation errors exist
- Warnings are displayed but do not block
- Requires `pre-commit install` to activate (one-time setup per clone)
