# CLI Contract: `agenteval-compare`

## Entry Point

```
agenteval-compare
```

Registered in `pyproject.toml` under `[project.scripts]`:
```toml
agenteval-compare = "agenteval.core.comparison:main"
```

---

## Arguments

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--run-a` | str | Yes* | Run A identifier (baseline) |
| `--run-b` | str | Yes* | Run B identifier (current) |
| `--baseline` | str | No | Alias for `--run-a` |
| `--current` | str | No | Alias for `--run-b` |
| `--output-json` | path | No | Write full ComparisonResult JSON to this file |

*`--run-a`/`--run-b` and `--baseline`/`--current` are mutually exclusive pairs; at least one pair must be provided.

---

## Behaviour

1. Resolve both run IDs against `runs/<run_id>/` under repo root.
2. Fail with exit code 1 + message if either run directory does not exist.
3. Load per-case evaluation JSONs from both runs.
4. Compute `ComparisonResult`.
5. Validate result against `schemas/comparison_schema.json`.
6. Print summary table to stdout (always).
7. If `--output-json` given, write full JSON to the specified path.
8. Exit 0 on success; exit 1 on any error.

---

## stdout Format

```
Run A: 20260320T120000_aa11  (17 cases)
Run B: 20260324T150000_bb22  (18 cases)

Summary
  Overall score delta : +0.15  ▲ improved
  Cases improved      : 5
  Cases regressed     : 2
  Cases unchanged     : 10
  Cases new           : 1
  Cases removed       : 0
  New failure types   : (none)
  Resolved failures   : Constraint Violation

Dimension Deltas
  Dimension             Run A    Run B    Delta
  ─────────────────── ──────── ──────── ────────
  accuracy              0.60     0.80    +0.20 ▲
  tool_use              0.70     0.65    -0.05 ▼
  security_safety       0.80     0.80     0.00 –
  ...
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Comparison completed successfully |
| 1 | Error: missing run, invalid data, schema validation failure |
