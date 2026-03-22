# Feature Specification: Run Tracking

**Feature Branch**: `003-run-tracking`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Introduce explicit run tracking for the evaluation pipeline. Each evaluation execution should produce a tracked run with a unique run_id, timestamp, dataset snapshot reference, and configuration. Users should be able to list past runs, inspect run details, persist run results, and track evaluation history over time."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Track an Evaluation Run (Priority: P1)

As an evaluator, I want each evaluation execution to automatically produce a tracked run record so that I can refer back to past evaluations and understand when they were performed, what dataset was evaluated, and what configuration was used.

**Why this priority**: Without run tracking, evaluation results are overwritten on each execution. This is the foundational capability that enables all downstream features (listing, inspecting, comparing runs).

**Independent Test**: Run the evaluation pipeline once and verify that a new run record is created with a unique identifier, timestamp, dataset reference, and the evaluation results are persisted under that run.

**Acceptance Scenarios**:

1. **Given** a valid dataset with benchmark cases, **When** the user triggers an evaluation run, **Then** the system creates a new run record with a unique run identifier, a timestamp of when the run started, a reference to the dataset that was evaluated, and the evaluation configuration used.
2. **Given** an evaluation run completes successfully, **Then** all per-case evaluation templates and the summary report are persisted under the run record, and the run is marked as completed.
3. **Given** an evaluation run fails partway through, **Then** the run record is still created and marked with an error status, preserving any partial results that were generated before the failure.

---

### User Story 2 - List Past Runs (Priority: P2)

As an evaluator, I want to see a chronological list of all past evaluation runs so that I can understand my evaluation history and find specific runs to inspect.

**Why this priority**: Listing runs is the primary navigation mechanism for accessing historical evaluations. Without it, users cannot discover or select past runs.

**Independent Test**: After executing multiple evaluation runs, verify that the run list displays all runs in reverse chronological order with key metadata (run ID, timestamp, number of cases, status).

**Acceptance Scenarios**:

1. **Given** multiple evaluation runs have been executed, **When** the user requests the run list, **Then** all runs are displayed in reverse chronological order showing: run identifier, timestamp, number of cases evaluated, and completion status.
2. **Given** no evaluation runs have been executed yet, **When** the user requests the run list, **Then** the system displays a message indicating no runs exist and suggests running an evaluation.

---

### User Story 3 - Inspect a Run (Priority: P2)

As an evaluator, I want to drill into a specific past run to see its full details — the cases evaluated, per-case results, summary statistics, and configuration — so that I can review what happened in that evaluation.

**Why this priority**: Inspection provides the detailed view of a run. It complements the list view and is essential for understanding evaluation results in context.

**Independent Test**: Select a past run from the list and verify that the run detail view shows all per-case evaluation results, summary statistics, dataset reference, configuration, and timestamps.

**Acceptance Scenarios**:

1. **Given** a completed evaluation run exists, **When** the user selects that run for inspection, **Then** the system displays: run metadata (ID, timestamp, status, configuration), a per-case summary table (case ID, primary failure, severity, scored dimensions), and the aggregated summary statistics.
2. **Given** a run with an error status, **When** the user inspects it, **Then** the system shows the partial results that were generated along with the error information.

---

### User Story 4 - Access Run Results via CLI (Priority: P3)

As a developer, I want to list and inspect runs from the command line so that I can integrate run tracking into scripts and automation workflows.

**Why this priority**: CLI access ensures run tracking is usable beyond the UI, supporting scripted workflows and CI/CD integration.

**Independent Test**: Run the CLI command to list runs and verify output matches the runs created. Run the CLI command to inspect a specific run and verify the detail output is correct.

**Acceptance Scenarios**:

1. **Given** evaluation runs exist, **When** the user runs the list-runs CLI command, **Then** the output shows all runs with identifiers, timestamps, case counts, and status.
2. **Given** a specific run identifier, **When** the user runs the inspect-run CLI command with that identifier, **Then** the output shows the full run details including per-case results and summary.

---

### Edge Cases

- What happens when the evaluation pipeline is interrupted mid-run (e.g., process killed)? The run record should reflect incomplete status.
- What happens when the user runs evaluation on an empty dataset? A run record should still be created with zero cases and appropriate status.
- What happens when disk space is insufficient to persist run results? The system should report the error clearly and not leave the run in an ambiguous state.
- What happens when two evaluation runs are triggered simultaneously? Each should receive a unique run identifier and persist results independently.
- What happens when past run data is manually deleted from disk? The system should handle missing run data gracefully when listing or inspecting.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST assign a unique run identifier to each evaluation execution, using a timestamp-prefixed format with a short random suffix (e.g., `20260322T143015_abc1`) to ensure natural chronological sorting and uniqueness under concurrent runs.
- **FR-002**: System MUST record a timestamp for when each run started and when it completed (or failed).
- **FR-003**: System MUST record the filesystem path of the dataset directory that was evaluated in each run (path reference only — no dataset duplication or snapshotting).
- **FR-004**: System MUST record the evaluation configuration used for each run (rubric path, output settings).
- **FR-005**: System MUST persist all per-case evaluation templates exclusively under the run record (not in `reports/`) so they are not overwritten by subsequent runs.
- **FR-006**: System MUST persist the aggregated summary report exclusively under the run record.
- **FR-007**: System MUST record the completion status of each run (completed, failed, incomplete).
- **FR-008**: System MUST provide a way to list all past runs in reverse chronological order.
- **FR-009**: System MUST provide a way to inspect a specific run by its identifier, showing full metadata, per-case results, and summary.
- **FR-010**: System MUST provide CLI commands for listing runs and inspecting a specific run.
- **FR-011**: System MUST expose run tracking through the existing UI, displaying the run list and run detail views.
- **FR-012**: System MUST maintain backward compatibility — existing CLI commands (`agenteval-eval-runner`, `agenteval-eval-report`) MUST continue to work. Run tracking MUST NOT break existing workflows.
- **FR-013**: System MUST handle partial runs (failures partway through) by persisting whatever results were generated and marking the run as failed or incomplete.

### Key Entities

- **Run**: Represents a single evaluation execution. Key attributes: run identifier (unique), start timestamp, end timestamp, status (completed/failed/incomplete), dataset directory path (string reference, not a copy), configuration (rubric path, output settings), number of cases evaluated.
- **Run Result**: The collection of per-case evaluation templates and the summary report that belong to a specific run.
- **Run Index**: A persistent record of all runs that enables listing and lookup by identifier.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can identify any past evaluation by its unique run identifier within 5 seconds of viewing the run list.
- **SC-002**: All evaluation results from a run are retrievable even after subsequent runs have been executed (no data overwriting).
- **SC-003**: The run list displays all historical runs with correct metadata (100% accuracy — no missing or phantom runs).
- **SC-004**: Run inspection shows complete per-case results and summary for any completed run (100% data integrity).
- **SC-005**: Existing CLI commands produce identical output behavior after run tracking is introduced (zero backward-compatibility regressions).
- **SC-006**: A new run record is created and persisted in under 1 second of overhead beyond the evaluation itself.

## Assumptions

- Run data is stored on the local filesystem (no external database required for v1).
- Run identifiers are generated automatically in `YYYYMMDDTHHMMSS_xxxx` format (users do not choose their own run IDs).
- There is no automatic cleanup or retention policy for old runs in v1; all runs are kept until manually deleted.
- When run tracking is active, the evaluation runner writes output exclusively to the run-specific directory. The `reports/` directory is no longer the primary output location. Existing CLI commands (`agenteval-eval-runner`, `agenteval-eval-report`) continue to work but output is directed to run storage.
- Run tracking applies to the evaluation pipeline only (not to dataset validation or case generation).
- The UI integration reuses the existing Streamlit app structure (adds to existing pages or adds a new page).

## Clarifications

### Session 2026-03-22

- Q: What does "dataset snapshot reference" mean — should the system record only the dataset directory path, or duplicate/hash the dataset contents? → A: Record the dataset directory path only (lightweight, no duplication).
- Q: When run tracking is active, does the runner still write to `reports/` in addition to the run directory? → A: Write only to the run-specific directory; `reports/` is no longer the primary output.
- Q: What format should run identifiers use? → A: Timestamp-prefixed with short random suffix (e.g., `20260322T143015_abc1`) — human-readable, naturally sortable, unique under concurrency.

## Out of Scope

- Run comparison (separate feature, depends on this one).
- Selective evaluation / filtering (separate feature).
- Automatic run cleanup or retention policies.
- Remote/cloud storage for runs.
- Multi-user run ownership or access control.
- Run annotations or tagging.
