# Feature Specification: Ingestion UI

**Feature Branch**: `012-ingestion-ui`
**Created**: 2026-03-24
**Status**: Draft
**Input**: User description: "Ingestion UI — a Streamlit page that lets users upload trace files (single or bulk ZIP), auto-detect or manually select the adapter (OTel, LangChain, CrewAI, OpenAI, Generic), preview the converted trace before saving, configure the output case directory, and see per-file status for bulk uploads. References roadmap section 2.8 and existing ingestion module at src/agenteval/ingestion/. Feature ID: 012."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Single Trace Upload and Convert (Priority: P1)

A reviewer has a trace file exported from their agent framework (LangChain, OTel, etc.) and wants to bring it into AgentEval for evaluation without using the command line. They open the Ingest page, upload the file, see a preview of what will be converted, choose a target case ID, and save it.

**Why this priority**: This is the core use case. Without single-file ingestion working end-to-end in the UI, the page has no value. All other stories build on it.

**Independent Test**: Upload one of the fixture files from `tests/ingestion/fixtures/`, confirm format is detected, preview shows steps, save creates `data/cases/case_NNN/trace.json`, then navigate to Inspect to confirm it appears.

**Acceptance Scenarios**:

1. **Given** the user is on the Ingest page, **When** they upload a valid OTel/LangChain/CrewAI/OpenAI JSON file, **Then** the page shows the detected format name and a step-count summary without requiring any further input.
2. **Given** a format has been detected, **When** the user views the conversion preview, **Then** they see number of steps, step type breakdown (thought/tool_call/observation/final_answer), and any mapping warnings.
3. **Given** the preview is shown, **When** the user confirms and saves, **Then** the trace is written to the chosen case directory and a success message links to the Inspect page for that case.
4. **Given** the upload fails schema validation, **When** the user tries to save, **Then** a clear error message is shown with the validation failure reason and no files are written.

---

### User Story 2 — Manual Adapter Override (Priority: P2)

A user uploads a file that auto-detection fails to recognise, or they want to force a specific adapter. They select the adapter manually from a dropdown and proceed with conversion.

**Why this priority**: Auto-detection relies on format heuristics that can fail. Manual override is the fallback that makes the UI complete for all supported formats.

**Independent Test**: Upload a file, select a specific adapter from the dropdown, confirm conversion uses the selected adapter (adapter name visible in preview header), save.

**Acceptance Scenarios**:

1. **Given** a file is uploaded and auto-detection returns no match, **When** the user selects an adapter manually, **Then** the conversion preview is generated using the selected adapter.
2. **Given** a file is uploaded and auto-detection succeeds, **When** the user overrides the adapter via the dropdown, **Then** the preview regenerates using the manually selected adapter.
3. **Given** the user selects the Generic adapter, **Then** a secondary file picker appears for uploading a mapping config (YAML or JSON), and conversion is blocked until a mapping file is provided.

---

### User Story 3 — Bulk Upload via ZIP (Priority: P3)

A user has a folder of trace files from a batch agent run. They ZIP them up, upload the ZIP, and see a per-file status table showing which files converted successfully and which failed.

**Why this priority**: Bulk upload significantly reduces time-to-evaluation for teams with many traces. It depends on single-file ingestion (P1) working correctly.

**Independent Test**: Create a ZIP containing 3 fixture JSON files, upload it, confirm the status table shows 3 rows with converted/failed indicators, then verify the created case directories.

**Acceptance Scenarios**:

1. **Given** the user uploads a ZIP file, **When** processing completes, **Then** a per-file status table is shown with columns: filename, detected format, status (converted/failed/skipped), output case ID, and error reason.
2. **Given** some files in the ZIP fail, **When** the table is shown, **Then** successfully converted files are saved and only the failed files are listed as errors — partial success is accepted.
3. **Given** the ZIP contains non-JSON files, **When** processing runs, **Then** non-JSON files are skipped with a clear "skipped (not JSON)" note in the status table.
4. **Given** bulk conversion completes, **When** the user views the summary, **Then** the total count of converted, failed, and skipped files is shown prominently.

---

### Edge Cases

- What happens when a file exceeds the 50 MB hard size limit? → Upload is rejected immediately with a size error before any conversion is attempted.
- What happens when a file exceeds the 10 MB soft limit? → A warning is shown alongside the preview but the user can still proceed.
- What happens when the ZIP contains zero JSON files? → An error state is shown: "No JSON files found in ZIP."
- What happens when the target case directory already exists? → The user is warned that the directory exists and asked to confirm overwrite, or offered an alternative case ID.
- What happens when the JSON parses but no adapter can handle it? → A clear error: "Format not recognised. Try selecting an adapter manually."
- What happens when conversion succeeds but schema validation fails? → Error shown with the specific validation message; no files written.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to upload a single JSON trace file through a file picker in the UI.
- **FR-002**: Users MUST be able to upload a ZIP archive containing multiple JSON trace files.
- **FR-003**: The system MUST attempt to auto-detect the trace format using the registered adapter registry.
- **FR-004**: Users MUST be able to manually select an adapter from: Auto-detect, OTel, LangChain, CrewAI, OpenAI, Generic.
- **FR-005**: When the Generic adapter is selected, users MUST be able to upload a mapping config file (YAML or JSON) before conversion can proceed.
- **FR-006**: The system MUST display a conversion preview before the user commits to saving, showing: step count, step type breakdown, detected format, and any mapping warnings.
- **FR-007**: Users MUST be able to choose or confirm the output case ID before saving.
- **FR-008**: The system MUST suggest the next available case ID automatically.
- **FR-009**: The system MUST warn the user if the selected case directory already exists before overwriting.
- **FR-010**: After a successful save, the page MUST show a link to the Inspect page for the newly created case.
- **FR-011**: For bulk uploads, the system MUST display a per-file status table with: filename, detected format, status (converted/failed/skipped), output case ID, and error reason.
- **FR-012**: Bulk conversion MUST continue processing remaining files when a single file fails (partial success is valid).
- **FR-013**: The system MUST reject files exceeding the 50 MB hard size limit before conversion.
- **FR-014**: The system MUST show a warning (but allow the user to continue) for files between 10 MB and 50 MB.
- **FR-015**: Non-JSON files inside a ZIP MUST be skipped with a visible "skipped" status — not treated as errors.
- **FR-016**: The page MUST be accessible from the main sidebar navigation.

### Key Entities

- **Uploaded File**: A JSON trace file or ZIP archive provided by the user. Has a name, size, and raw content.
- **Conversion Preview**: A summary of what the adapter produced — step count, step type breakdown, warnings — shown before saving.
- **Ingestion Result**: The outcome of a single file's conversion — status (converted/failed/skipped), output case ID, error reason.
- **Case Directory**: The target `data/cases/case_NNN/` directory where `trace.json` is written.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with a supported trace file can complete the full ingest-to-case flow (upload → preview → save) without touching the command line.
- **SC-002**: Format auto-detection succeeds for all four built-in adapters (OTel, LangChain, CrewAI, OpenAI) when given valid fixture files.
- **SC-003**: A bulk ZIP upload of 10 files completes and shows a full per-file status table within a reasonable time for files under the soft size limit.
- **SC-004**: All conversion failures produce a visible, specific error message — no silent failures or blank screens.
- **SC-005**: After a successful single-file ingest, the new case is immediately visible in the Inspect page without restarting the app.
- **SC-006**: The Generic adapter path (with mapping config upload) works end-to-end: upload trace + upload mapping → preview → save.

---

## Assumptions

- The existing ingestion module (`src/agenteval/ingestion/`) is stable and does not need modification for this feature. The UI wraps it, it does not change it.
- The Generic adapter's mapping config upload covers YAML and JSON formats; TOML and other formats are out of scope.
- ZIP files are assumed to be flat (all JSON files at the top level). Nested directories inside ZIPs are out of scope.
- The mapping config file for Generic adapter applies to all files in a bulk ZIP upload — per-file mapping configs are out of scope.
- File size limits (10 MB soft, 50 MB hard) match the existing CLI behaviour and are not configurable from the UI.
- The page is added to the existing Streamlit sidebar navigation — no changes to routing architecture are needed.
- Existing cases are not modified or re-ingested by this feature; only new case directories are created.

---

## Dependencies

- Existing ingestion module: `src/agenteval/ingestion/` (OTel, LangChain, CrewAI, OpenAI, Generic adapters)
- Service layer: `src/agenteval/core/service.py` (new `ingest_trace()` and `ingest_bulk()` functions to be added)
- Existing Streamlit UI entry point: `app/app.py` (sidebar navigation)
- Dataset case structure: `data/cases/case_NNN/trace.json`
- File size utilities: `src/agenteval/ingestion/base.py` (`check_file_size`)
