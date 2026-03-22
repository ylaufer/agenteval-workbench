# Quickstart: Streamlit UI for AgentEval Workbench

## Prerequisites

```bash
# Install with UI extras
pip install -e ".[ui]"
```

## Launch the UI

```bash
streamlit run src/agenteval/ui/app.py
```

The app opens in your default browser at `http://localhost:8501`.

## Scenario 1: Generate and Validate a Case (US1 — P1)

1. Navigate to the **Generate** page via the sidebar
2. Enter a case ID (e.g., `my_test_case`) or leave blank for auto-generated
3. Select a failure type from the dropdown (e.g., "Tool Hallucination")
4. Click **Generate Case**
5. Verify: success message shows the created case path
6. Verify: validation runs automatically and shows results
7. Verify: new-case issues (if any) are shown prominently; other-case issues are collapsed

**Expected output on disk**:
```
data/cases/my_test_case/
├── prompt.txt
├── trace.json
└── expected_outcome.md
```

## Scenario 2: Validate Dataset Independently (US1 — P1)

1. Navigate to the **Generate** page
2. Click **Validate Dataset** (without generating a case)
3. Verify: full dataset validation results are displayed
4. Verify: issues are grouped by severity (errors first, then warnings)

## Scenario 3: Run Evaluation Pipeline (US2 — P2)

1. Ensure at least one valid case exists in `data/cases/`
2. Navigate to the **Evaluate** page
3. Click **Run Evaluation**
4. Verify: per-case summary table shows case IDs, failure types, severity
5. Verify: evaluation template files are created in `reports/`

**Expected output on disk**:
```
reports/
├── my_test_case.evaluation.json
└── my_test_case.evaluation.md
```

## Scenario 4: Inspect a Case (US3 — P2)

1. Navigate to the **Inspect** page
2. Select a case from the dropdown
3. Verify: case metadata (Case ID, Primary Failure, Severity, case_version) is displayed
4. Verify: trace steps are shown in order with type badges, actor, content
5. Verify: tool_call steps show tool_name and tool_input
6. Verify: if evaluation template exists, rubric dimensions are shown with scores

## Scenario 5: Generate Summary Report (US4 — P3)

1. Ensure evaluation templates exist in `reports/`
2. Navigate to the **Report** page
3. Click **Generate Report**
4. Verify: dimension statistics table is displayed (mean scores, distributions)
5. Verify: failure frequency counts are shown
6. Verify: summary files are saved to `reports/`

**Expected output on disk**:
```
reports/
├── summary.evaluation.json
└── summary.evaluation.md
```

## Scenario 6: Error Handling

1. **Generate page**: Try generating a case with an existing ID without overwrite — verify error message
2. **Evaluate page**: Delete `rubrics/v1_agent_general.json` temporarily — verify error message with file path
3. **Inspect page**: When no cases exist — verify info message suggesting Generate page
4. **Report page**: When no evaluation templates exist — verify info message suggesting Evaluate page

## Backward Compatibility Check

After all scenarios, verify existing CLI commands still work:

```bash
agenteval-validate-dataset --repo-root .
agenteval-eval-runner --dataset-dir data/cases --output-dir reports
agenteval-eval-report --input-dir reports
```

All commands MUST produce identical output to before the UI changes.
