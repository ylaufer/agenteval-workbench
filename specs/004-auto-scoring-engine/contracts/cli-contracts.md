# CLI Contracts: Auto-Scoring Engine

**Feature**: 004-auto-scoring-engine
**Date**: 2026-03-22

## Command: `agenteval-auto-score`

**Entry point**: `agenteval.core.scorer:main`

### Arguments

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `--dataset-dir` | path | No | `data/cases` | Path to dataset directory |
| `--output-dir` | path | No | `reports` | Directory for auto-evaluation output files |
| `--rubric` | path | No | `rubrics/v1_agent_general.json` | Path to rubric file |
| `--strategy` | string | No | `rule` | Scoring strategy filter: "rule", "llm", or "all" |

### Behavior

1. Loads rubric from `--rubric` path
2. Creates evaluator registry filtered by `--strategy`
3. For each case directory in `--dataset-dir`:
   - Loads `trace.json`
   - Scores all registered dimensions
   - Writes `{case_id}.auto_evaluation.json` to `--output-dir`
4. Prints summary of scored cases and dimensions

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All cases scored successfully (partial dimension failures are OK) |
| 1 | One or more cases failed to produce any output |
| 2 | Invalid arguments or missing rubric/dataset |

### Example Output

```text
Auto-scored 12 case(s):
  case_001: 2/6 dimensions scored (tool_use=2, security_safety=2)
  case_002: 2/6 dimensions scored (tool_use=1, security_safety=2)
  ...

Results written to reports/
```

### Example Error Output (stderr)

```text
case_005: tool_use evaluator error: empty trace, no steps to analyze
case_008: security_safety evaluator error: expected_outcome.md not found
```

## Schema: `schemas/auto_evaluation_schema.json`

Validates the output of auto-scoring. Structure:

```json
{
  "type": "object",
  "required": ["case_id", "scoring_type", "rubric_version", "dimensions", "auto_tags", "metadata"],
  "properties": {
    "case_id": { "type": "string" },
    "scoring_type": { "type": "string", "const": "auto" },
    "rubric_version": { "type": "string" },
    "dimensions": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "required": ["dimension_name", "score", "weight", "scale", "evidence_step_ids", "notes", "evaluator_type"],
        "properties": {
          "dimension_name": { "type": "string" },
          "score": { "type": ["integer", "null"] },
          "weight": { "type": "number" },
          "scale": { "type": "string" },
          "evidence_step_ids": { "type": "array", "items": { "type": "string" } },
          "notes": { "type": "string" },
          "evaluator_type": { "type": "string", "enum": ["rule", "llm"] },
          "confidence": { "type": ["number", "null"] },
          "error": { "type": ["string", "null"] }
        }
      }
    },
    "auto_tags": { "type": "array", "items": { "type": "string" } },
    "metadata": {
      "type": "object",
      "required": ["timestamp"],
      "properties": {
        "timestamp": { "type": "string" },
        "model": { "type": ["string", "null"] },
        "evaluator_versions": { "type": "object" }
      }
    }
  }
}
```
