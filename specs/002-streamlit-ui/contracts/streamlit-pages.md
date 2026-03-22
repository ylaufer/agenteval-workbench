# Interface Contract: Streamlit Pages

## Page Structure

Each page is a Python module in `app/` with a single `render()` function called by the main app. Pages import only from `agenteval.core.service` — never directly from runner, report, validator, or generator modules.

---

## Generate Page (`app/page_generate.py`)

### User Inputs

| Input | Type | Required | Default |
|-------|------|----------|---------|
| Case ID | text input | No | Auto-generated UUID prefix |
| Failure Type | dropdown | No | None (generic case) |
| Overwrite | checkbox | No | False |

### Actions

| Button | Service Call | Output |
|--------|-------------|--------|
| Generate Case | `service.generate_case(case_id, failure_type, output_dir, overwrite)` | Success message with case path, or error message |
| Validate Dataset | `service.validate_dataset()` | Validation result display |

### Display After Generation

1. Success/error banner
2. Auto-triggered validation results:
   - New-case issues: prominent, grouped by severity (errors first)
   - Other-case issues: collapsed expander, grouped by severity
   - Each issue shows: case_id, file_path, message, severity badge

### Error Display

| Error Type | Display |
|------------|---------|
| Case exists (no overwrite) | Warning with suggestion to enable overwrite |
| Invalid failure type | Error with list of valid types |
| Path escapes repo root | Error with security message |
| Unexpected error | Error with exception message |

---

## Evaluate Page (`app/page_evaluate.py`)

### User Inputs

None — uses default paths.

### Actions

| Button | Service Call | Output |
|--------|-------------|--------|
| Run Evaluation | `service.run_evaluation()` | Per-case summary table |

### Display After Evaluation

1. Summary: "Processed N cases, M evaluation templates generated"
2. Per-case table:
   - Columns: Case ID, Primary Failure, Severity, Dimensions (scored/unscored count), Auto Tags
   - Rows: one per evaluation template dict returned

### Error Display

| Error Type | Display |
|------------|---------|
| No cases in dataset | Info message suggesting Generate page |
| Rubric missing | Error with file path |
| Individual case failure | Warning per case; other cases still shown |

---

## Inspect Page (`app/page_inspect.py`)

### User Inputs

| Input | Type | Required |
|-------|------|----------|
| Case selector | dropdown | Yes (populated via `service.list_cases()`) |

### Display Sections

1. **Case Metadata** — via `service.load_case_metadata()`:
   - Case ID, Primary Failure, Secondary Failures, Severity, case_version

2. **Trace Viewer** — via `service.load_trace()`:
   - Each step shows: step_id, type (color-coded badge), actor_id, content
   - Tool call steps additionally show: tool_name, tool_input (formatted JSON)
   - Observation steps show: tool_output

3. **Evaluation Template** — via `service.load_evaluation_template()`:
   - Per-dimension display: title, scale, weight, current score or "Not yet scored"
   - Scoring guide text for each dimension
   - Overall notes and auto-tags

### Error Display

| Error Type | Display |
|------------|---------|
| No cases exist | Info message suggesting Generate page |
| Invalid trace JSON | Error with parse message |
| No evaluation template | Info: "Run evaluation first" |

---

## Report Page (`app/page_report.py`)

### User Inputs

None — uses default paths.

### Actions

| Button | Service Call | Output |
|--------|-------------|--------|
| Generate Report | `service.generate_summary_report()` | Summary display |

### Display After Report Generation

1. **Overview**: Total cases, scored cases, rubric version
2. **Dimension Statistics**: Table with columns: Dimension, Weight, Mean Score, Scored Count, Distribution
3. **Failure Summary**: Primary failure frequency counts, severity distribution
4. **Recommendations**: Bulleted list of improvement suggestions
5. **Output Files**: Confirmation that summary.evaluation.json and summary.evaluation.md were written

### Error Display

| Error Type | Display |
|------------|---------|
| No evaluation templates | Info message suggesting Evaluate page first |
| Rubric missing | Error with file path |
