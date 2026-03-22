# Feature Specification: Dataset Governance

**Feature Branch**: `001-dataset-governance`
**Created**: 2026-03-21
**Status**: Draft
**Input**: User description: "Build a dataset governance feature for AgentEval Workbench. The system must validate every dataset case before commit. Each case must contain prompt.txt, trace.json, and expected_outcome.md. Traces must validate against the trace schema. The project must support auto-generation of complete demo cases and fail fast on incomplete or invalid cases. It should also define a case versioning strategy so dataset changes are reviewable and reproducible. Focus on the what and why, not the implementation details."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validate Dataset Before Commit (Priority: P1)

A benchmark contributor prepares or modifies a dataset case and runs the validation command before committing. The system checks every case directory for completeness (all three required files present), validates each `trace.json` against the trace schema, and scans for security violations. If any case is incomplete or invalid, the system reports all errors and exits with a non-zero status, preventing the commit from proceeding.

**Why this priority**: Without reliable pre-commit validation, invalid or incomplete cases enter the repository and break downstream evaluation workflows (runner, report, calibration). This is the foundation that all other governance features depend on.

**Independent Test**: Run the validator against a dataset containing both valid and intentionally broken cases. Verify that all errors are reported with case identifiers and that the exit code is non-zero when any case fails.

**Acceptance Scenarios**:

1. **Given** a dataset with 12 valid cases and 1 case missing `prompt.txt`, **When** the contributor runs the validation command, **Then** the system reports the missing file with the case identifier and exits with a non-zero status.
2. **Given** a dataset with all cases complete but one `trace.json` containing an invalid schema (e.g., missing required `task_id` field), **When** the contributor runs validation, **Then** the system reports the schema violation with the specific field and case identifier.
3. **Given** a dataset where all cases are complete and schema-valid, **When** the contributor runs validation, **Then** the system exits with status 0 and reports success.
4. **Given** a case file containing an API key pattern, **When** validation runs, **Then** the system flags the security violation and rejects the case.

---

### User Story 2 - Auto-Generate Complete Demo Cases (Priority: P2)

A new contributor or automated pipeline needs a reference case for testing or development. They run a case generation command that produces a complete, valid case directory containing `prompt.txt`, `trace.json`, and `expected_outcome.md`. The generated case passes all validation checks immediately — no manual fixup is required.

**Why this priority**: Demo case generation enables onboarding, testing, and CI workflows. Without it, contributors must manually author all three files, which is error-prone and slows development. Auto-generation also serves as a living specification of what a valid case looks like.

**Independent Test**: Run the case generator, then immediately run the validator on the output. Verify that the generated case passes all checks and that the trace validates against the schema.

**Acceptance Scenarios**:

1. **Given** a contributor runs the case generation command with no arguments, **When** generation completes, **Then** a new case directory exists under `data/cases/` containing `prompt.txt`, `trace.json`, and `expected_outcome.md`.
2. **Given** a generated case, **When** the dataset validator runs against it, **Then** it passes all completeness, schema, and security checks.
3. **Given** a contributor specifies a case identifier (e.g., `demo_case`), **When** generation runs, **Then** the case directory uses that identifier and the `expected_outcome.md` metadata header references it.
4. **Given** the trace schema is updated with new optional fields, **When** a case is generated, **Then** the generated `trace.json` includes the new fields with sensible defaults.

---

### User Story 3 - Fail Fast on Invalid Cases (Priority: P2)

When a contributor introduces an incomplete or invalid case, the system detects the problem at the earliest possible point — ideally during local validation before commit, and definitively during CI. The system reports all errors in a single run (not one-at-a-time) so the contributor can fix everything before re-running.

**Why this priority**: Fail-fast behavior reduces iteration cycles. Batch error reporting (all errors in one run) is critical for contributor productivity — discovering one error per run forces unnecessary re-validation cycles.

**Independent Test**: Create a dataset with multiple errors across different cases (missing files, invalid schemas, security violations). Run validation once and verify that all errors are reported together.

**Acceptance Scenarios**:

1. **Given** a dataset with 3 broken cases (one missing a file, one with invalid schema, one with a security violation), **When** validation runs, **Then** all 3 errors are reported in a single output with case identifiers and error categories.
2. **Given** CI is configured to run validation on push, **When** a contributor pushes a branch containing an invalid case, **Then** the CI pipeline fails and the error report is visible in the CI output.
3. **Given** a case directory contains extra unexpected files beyond the required three, **When** validation runs, **Then** validation still passes (extra files are not treated as errors).

---

### User Story 4 - Case Versioning for Reviewable Changes (Priority: P3)

When a benchmark case is modified (e.g., the trace is updated, the expected outcome changes, or metadata is corrected), the change must be reviewable through standard version control workflows. Each case carries version metadata so reviewers can tell whether a case was modified and what version of the case a given evaluation was scored against.

**Why this priority**: Reproducibility requires knowing exactly which version of a case was used in an evaluation. Without case-level versioning, it is impossible to determine whether evaluation results reflect the current case definition or an earlier one.

**Independent Test**: Modify a case, update its version metadata, and create a pull request. Verify that the diff clearly shows the version change alongside the content change, and that the evaluation runner references the case version in its output.

**Acceptance Scenarios**:

1. **Given** a case with version `1.0` in its metadata, **When** a contributor modifies the `trace.json` and increments the version to `1.1`, **Then** the version change is visible in the pull request diff alongside the trace change.
2. **Given** a case with version metadata, **When** the evaluation runner generates a template for that case, **Then** the template includes the case version so evaluators know which version they scored.
3. **Given** a contributor modifies a case without updating the version metadata, **When** validation runs, **Then** the system warns that the case content changed without a version bump.

---

### Edge Cases

- What happens when a case directory exists but is completely empty (no files at all)? The validator reports all three missing files.
- What happens when `trace.json` is valid JSON but does not conform to the trace schema? The validator reports the specific schema violations (missing fields, wrong types).
- What happens when the case generator is run but a case with the same identifier already exists? The generator refuses to overwrite and reports an error, unless an explicit overwrite flag is provided.
- What happens when `expected_outcome.md` exists but has no YAML metadata header? The validator reports a malformed metadata header.
- What happens when `expected_outcome.md` has a YAML header but is missing one of the five required fields (`Case ID`, `Primary Failure`, `Secondary Failures`, `Severity`, `case_version`)? The validator reports the missing field(s) as an error.
- What happens when the trace schema itself is malformed or missing? The validator reports that schema loading failed and exits without validating individual cases.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST validate that every case directory under `data/cases/` contains exactly `prompt.txt`, `trace.json`, and `expected_outcome.md`.
- **FR-002**: The system MUST validate each `trace.json` against `schemas/trace_schema.json` and report all schema violations with field-level detail.
- **FR-003**: The system MUST scan all required case files for security violations (secrets, external URLs, absolute paths, path traversal) and reject cases that contain them.
- **FR-004**: The system MUST report all validation errors across all cases in a single run, not abort after the first error.
- **FR-005**: The system MUST exit with a non-zero status code when any validation error is found. Validation issues are categorized into two severity levels: **errors** (missing files, schema violations, security violations) block commit with a non-zero exit code; **warnings** (e.g., missing version bump) are reported but do not block.
- **FR-006**: The system MUST provide a case generation capability that produces a complete, schema-valid case directory from a single command invocation. By default the generator produces a generic passing case. It MUST also accept an optional failure-type parameter (e.g., `tool_hallucination`, `unsafe_output`) to produce cases pre-configured with failure annotations matching the failure taxonomy.
- **FR-007**: Generated cases MUST pass all validation checks (completeness, schema, security) without manual intervention.
- **FR-008**: The case generator MUST NOT overwrite an existing case directory unless the user explicitly requests it.
- **FR-009**: Each case MUST carry version metadata in its `expected_outcome.md` YAML header (e.g., `case_version: 1.0`). The required YAML header fields are: `Case ID`, `Primary Failure`, `Secondary Failures`, `Severity`, and `case_version`. The validator MUST reject cases missing any of these fields.
- **FR-010**: The evaluation runner MUST include the case version in generated evaluation templates so scores are traceable to a specific case revision.
- **FR-011**: The validation command SHOULD warn when `trace.json` or `expected_outcome.md` content is modified without a corresponding version metadata increment. This warning is reported alongside other validation issues in the same run. Cosmetic fixes to `prompt.txt` alone do not require a version bump.
- **FR-012**: The validation command MUST be runnable offline with no network access.
- **FR-013**: All file access during validation and generation MUST be constrained within the repository root.

### Key Entities

- **Dataset Case**: A directory under `data/cases/` representing a single evaluation scenario. Contains three required files: `prompt.txt` (the agent prompt), `trace.json` (the agent execution trace), and `expected_outcome.md` (the expected result with failure metadata). Carries version metadata for change tracking.
- **Trace Schema**: The JSON Schema definition (`schemas/trace_schema.json`) that governs the structure of all trace files. Serves as the contract between case authors and the evaluation engine.
- **Validation Result**: The outcome of running the validator against the dataset. Contains a pass/fail status and a collection of issues, each tied to a specific case, error category (missing file, schema violation, security violation), and severity level (error or warning). Errors cause a non-zero exit; warnings are advisory and do not block.
- **Case Version**: A version identifier embedded in the `expected_outcome.md` metadata header. MUST be incremented when `trace.json` or `expected_outcome.md` content changes. Cosmetic fixes to `prompt.txt` alone are exempt. Referenced by evaluation templates for reproducibility.

## Assumptions

- The existing dataset validator (`agenteval-validate-dataset`) already performs completeness checks and security scanning. This feature formalizes and extends that behavior rather than replacing it.
- Case version metadata uses a simple numeric scheme (e.g., `1.0`, `1.1`, `2.0`) rather than full SemVer, since cases are data artifacts not software.
- The case generator produces synthetic but realistic traces — not production data. Generated traces are intended for testing and demonstration, not for benchmarking real agent performance.
- Version change detection (FR-011) compares the current commit against the previous commit using standard version control diffing. It does not require a separate checksumming mechanism.

## Clarifications

### Session 2026-03-21

- Q: What triggers a case version bump? → A: Changes to `trace.json` or `expected_outcome.md` content require a bump; `prompt.txt` typo fixes do not.
- Q: How is the version-bump warning enforced? → A: Part of the validation command — warns alongside other validation issues in the same run.
- Q: Should validation errors distinguish severity levels? → A: Two levels — errors block (missing files, schema, security), warnings are advisory (version bump).
- Q: What are the required `expected_outcome.md` YAML header fields? → A: Five required: `Case ID`, `Primary Failure`, `Secondary Failures`, `Severity`, `case_version`.
- Q: Should the case generator support failure-type presets? → A: Default generic passing case, with optional failure-type parameter to produce taxonomy-aligned failure cases.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of cases in the repository pass validation before every merge to the main branch.
- **SC-002**: A new contributor can generate a complete, valid demo case in under 30 seconds using a single command.
- **SC-003**: When a dataset contains errors, all errors are reported in a single validation run — zero cases require multiple validation cycles to discover all issues.
- **SC-004**: Every evaluation template produced by the runner includes the case version, enabling 100% traceability between scores and case revisions.
- **SC-005**: Dataset changes are reviewable in pull requests with clear version metadata diffs, requiring no additional tooling beyond standard code review workflows.
