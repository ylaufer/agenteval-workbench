# Quickstart Guide: Ingestion UI

**Feature**: Ingestion UI (012)
**Date**: 2026-03-25
**Audience**: AgentEval users who want to ingest external traces via the UI

## Prerequisites

- AgentEval Workbench installed with UI extras: `pip install -e ".[ui]"`
- Streamlit UI running: `streamlit run app/app.py`
- At least one trace file from a supported framework (OTel, LangChain, CrewAI, OpenAI)

---

## Scenario 1: Ingest a Single Trace File

**Goal**: Upload a LangChain trace, preview the conversion, and save it as a new benchmark case.

**Steps**:

1. **Navigate to Ingest page**
   - Open Streamlit UI in browser
   - Click "Ingest" in the sidebar navigation

2. **Upload trace file**
   - Click "Choose a file" button
   - Select `langchain_trace.json` from your filesystem
   - File uploads automatically

3. **Review auto-detection**
   - UI shows: "Detected format: LangChain"
   - Conversion preview displays:
     - **Step count**: 12 steps
     - **Step type breakdown**:
       - `thought`: 3
       - `tool_call`: 5
       - `observation`: 5
       - `final_answer`: 1
     - **Warnings**: (if any mapping issues)

4. **Choose case ID**
   - UI auto-suggests: `case_015` (next available)
   - Accept suggestion or type custom ID (e.g., `case_langchain_01`)

5. **Save case**
   - Click "Save Case" button
   - UI shows success message: "Case created successfully!"
   - Click link to "View in Inspect Page"

6. **Verify case**
   - Case directory created: `data/cases/case_015/`
   - Files present:
     - `trace.json` — Converted trace
     - `prompt.txt` — Placeholder: `[TODO: Add the agent prompt...]`
     - `expected_outcome.md` — Placeholder with YAML front matter

7. **Complete the case** (manual step)
   - Edit `prompt.txt` → add the agent prompt
   - Edit `expected_outcome.md` → describe failure and expected behavior
   - Run `agenteval-validate-dataset` to verify completeness

**Expected Outcome**: One complete case ready for evaluation.

---

## Scenario 2: Manual Adapter Override

**Goal**: Upload a trace that auto-detection doesn't recognize, manually select the adapter, and convert.

**Steps**:

1. **Upload file**
   - Upload `custom_agent_trace.json`
   - UI shows: "⚠️ Format not recognized. Please select an adapter manually."

2. **Select adapter**
   - Dropdown appears: "Adapter: [Auto-detect ▼]"
   - Select "OpenAI" from dropdown
   - Preview regenerates using OpenAI adapter

3. **Review preview**
   - Verify step count and breakdown match expectations
   - Check warnings for any mapping issues

4. **Save case**
   - Proceed as in Scenario 1 (choose ID, click Save)

**Expected Outcome**: Trace converted using manually selected adapter.

---

## Scenario 3: Generic Adapter with Custom Mapping

**Goal**: Ingest a trace from a custom framework using a Generic adapter mapping config.

**Steps**:

1. **Upload trace file**
   - Upload `custom_framework_trace.json`
   - UI shows: "Format not recognized"

2. **Select Generic adapter**
   - Dropdown: Select "Generic"
   - Second file uploader appears: "Upload mapping config (YAML or JSON)"

3. **Upload mapping config**
   - Click "Choose a file" for mapping config
   - Upload `custom_mapping.yaml`:
     ```yaml
     trace_id: run.id
     steps: execution.actions
     step_mappings:
       timestamp: action.timestamp
       type:
         map:
           think: thought
           call_tool: tool_call
       content: action.output
     ```

4. **Preview conversion**
   - UI validates mapping config
   - Preview shows step count and breakdown using custom mapping

5. **Save case**
   - Proceed as normal (choose ID, save)

**Expected Outcome**: Custom format successfully converted using Generic adapter.

---

## Scenario 4: Bulk Upload via ZIP

**Goal**: Ingest 10 trace files at once using a ZIP archive.

**Steps**:

1. **Prepare ZIP**
   - Create `batch_traces.zip` containing:
     - `trace_001.json` (OTel format)
     - `trace_002.json` (LangChain format)
     - `trace_003.json` (invalid JSON)
     - `trace_004.json` (CrewAI format)
     - ...
     - `readme.txt` (non-JSON file)

2. **Upload ZIP**
   - File uploader: Select `batch_traces.zip`
   - UI detects ZIP format and switches to bulk mode

3. **Review processing status**
   - UI shows status table with columns:
     - **Filename**
     - **Detected Format**
     - **Status** (✅ Converted / ❌ Failed / ⊘ Skipped)
     - **Case ID** (for converted files)
     - **Error/Reason** (for failed/skipped)

   Example:
   | Filename | Format | Status | Case ID | Error/Reason |
   |----------|--------|--------|---------|--------------|
   | trace_001.json | OTel | ✅ Converted | case_020 | — |
   | trace_002.json | LangChain | ✅ Converted | case_021 | — |
   | trace_003.json | Unknown | ❌ Failed | — | Invalid JSON: Unexpected token |
   | trace_004.json | CrewAI | ✅ Converted | case_022 | — |
   | readme.txt | — | ⊘ Skipped | — | not JSON |

4. **Review summary**
   - UI shows:
     - **Total files**: 5
     - **Converted**: 3
     - **Failed**: 1
     - **Skipped**: 1

5. **Verify cases**
   - Navigate to Inspect page
   - Verify `case_020`, `case_021`, `case_022` appear in case list

**Expected Outcome**: Partial success — valid traces converted, failures clearly reported.

---

## Scenario 5: Handle File Size Limits

**Goal**: Understand soft and hard size limits.

**Steps**:

1. **Upload 15 MB file**
   - UI shows warning: "⚠️ File exceeds 10 MB soft limit. Conversion may be slow."
   - Preview still generates, user can proceed

2. **Upload 60 MB file**
   - UI immediately rejects: "❌ File exceeds 50 MB hard limit. Please reduce file size."
   - No preview generated, save blocked

**Expected Outcome**: Soft limit warns but allows; hard limit rejects immediately.

---

## Scenario 6: Overwrite Existing Case

**Goal**: Replace an existing case's trace.

**Steps**:

1. **Upload trace**
   - Preview generated successfully

2. **Choose existing case ID**
   - Type `case_010` (already exists)
   - UI shows warning: "⚠️ Case directory `case_010` already exists. Files will be overwritten."

3. **Confirm overwrite**
   - Checkbox appears: "☐ I understand this will overwrite existing files"
   - Check box to enable Save button

4. **Save case**
   - Click "Save Case"
   - Existing `trace.json` replaced
   - `prompt.txt` and `expected_outcome.md` also replaced with placeholders

**Expected Outcome**: Existing case overwritten (use caution!).

---

## Common Errors and Solutions

### Error: "Format not recognized"
**Cause**: Auto-detection failed to match any adapter.
**Solution**: Use manual adapter selection (Scenario 2) or Generic adapter with mapping (Scenario 3).

### Error: "Schema validation failed: steps.0.type is required"
**Cause**: Converted trace doesn't conform to `schemas/trace_schema.json`.
**Solution**: Check mapping config (for Generic adapter) or file a bug if using built-in adapter.

### Error: "Generic adapter requires a mapping config"
**Cause**: Selected Generic adapter but didn't upload mapping config.
**Solution**: Upload a valid YAML/JSON mapping config file.

### Error: "Invalid JSON: Unexpected token at position 42"
**Cause**: Uploaded file is not valid JSON.
**Solution**: Validate JSON syntax using `jq` or online JSON validator.

### Error: "File exceeds 50 MB hard limit"
**Cause**: Trace file too large.
**Solution**: Split trace into multiple files or filter unnecessary steps before upload.

---

## Next Steps After Ingestion

Once traces are ingested, complete the cases:

1. **Edit `prompt.txt`**
   - Add the agent prompt that produced this trace
   - Include any relevant context or configuration

2. **Edit `expected_outcome.md`**
   - Describe the failure and expected behavior
   - Assign primary failure type from `docs/failure_taxonomy.md`
   - Add evaluation guidance for reviewers

3. **Validate dataset**
   ```bash
   agenteval-validate-dataset --repo-root .
   ```

4. **Run evaluation**
   ```bash
   agenteval-eval-runner
   ```

5. **Generate report**
   ```bash
   agenteval-eval-report
   ```

---

## Tips and Best Practices

- **Batch processing**: Use ZIP upload for 10+ files to save time
- **Adapter order**: Auto-detection tries adapters in priority order (most specific first)
- **Mapping configs**: Keep reusable mapping configs for custom frameworks
- **Case IDs**: Use descriptive IDs (e.g., `case_langchain_auth_failure`) for easier browsing
- **Placeholders**: Don't forget to fill in `prompt.txt` and `expected_outcome.md` after ingestion
- **Validation**: Always run `agenteval-validate-dataset` before committing cases

---

## Reference

- **Ingestion CLI**: `agenteval-ingest --help` (CLI alternative to UI)
- **Adapter docs**: `docs/ingestion_usage.md`
- **Generic mapping**: `docs/generic_mapping.md`
- **Troubleshooting**: `docs/ingestion_troubleshooting.md`
- **Failure taxonomy**: `docs/failure_taxonomy.md`
