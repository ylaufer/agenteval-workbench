# Quickstart: Dataset Governance

**Feature**: 001-dataset-governance

## Setup

```bash
# Install with dev dependencies (includes pre-commit)
pip install -e ".[dev]"

# Activate pre-commit hooks (one-time per clone)
pre-commit install
```

## Validate the Dataset

```bash
# Run validation (checks all cases under data/cases/)
agenteval-validate-dataset --repo-root .
```

Expected output for a clean dataset:
```
✅ Dataset validation passed (13 cases).
```

Expected output with errors and warnings:
```
[case_003] ERROR: Missing required file: prompt.txt
[case_007] ERROR: expected_outcome.md missing required header field: case_version
[demo_case] WARNING: trace.json modified without case_version bump (1.0 → 1.0)

❌ Dataset validation failed (2 errors, 1 warning).
```

## Generate a Demo Case

```bash
# Generate a generic passing case
agenteval-generate-case --case-id my_test_case

# Generate a case with a specific failure type
agenteval-generate-case --case-id hallucination_example --failure-type tool_hallucination

# Overwrite an existing case
agenteval-generate-case --case-id demo_case --overwrite
```

## Verify a Generated Case

```bash
# Generate and immediately validate
agenteval-generate-case --case-id verify_me
agenteval-validate-dataset --repo-root .
```

## Case Versioning Workflow

1. Edit a case's `trace.json` or `expected_outcome.md`
2. Increment `case_version` in the YAML header:
   ```yaml
   ---
   Case ID: 001
   Primary Failure: Tool Hallucination
   Secondary Failures: Constraint Violation
   Severity: Critical
   case_version: 1.1
   ---
   ```
3. Run validation — no warnings
4. Commit

If you forget to bump the version:
```
[case_001] WARNING: trace.json modified without case_version bump (1.0 → 1.0)
```

## Pre-Commit Hook

After `pre-commit install`, validation runs automatically before every commit:

```bash
git add data/cases/case_001/
git commit -m "Update case 001 trace"
# → Pre-commit hook runs agenteval-validate-dataset
# → Blocks if errors, warns if version bump missing
```

## Run the Evaluation Pipeline

```bash
# Generate evaluation templates (now includes case_version)
agenteval-eval-runner --dataset-dir data/cases --output-dir reports

# Generate summary report
agenteval-eval-report --input-dir reports
```
