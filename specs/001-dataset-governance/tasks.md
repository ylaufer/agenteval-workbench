# Tasks: Dataset Governance

**Input**: Design documents from `specs/001-dataset-governance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included — constitution Principle IV mandates testing for dataset validation and report generation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/agenteval/`, `tests/` at repository root

---

## Phase 1: Setup

**Purpose**: Register new entry points, add dev dependencies

- [X] T001 Add `pre-commit` to `[project.optional-dependencies.dev]` in pyproject.toml
- [X] T002 Add `agenteval-generate-case = "agenteval.dataset.generator:main"` entry point in pyproject.toml `[project.scripts]`
- [X] T003 Re-install project in editable mode to activate new entry points (`pip install -e ".[dev]"`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core type changes and data migration that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Add `severity` field (default `"error"`) to `ValidationIssue` dataclass in src/agenteval/dataset/validator.py
- [X] T005 Update `ValidationResult.ok` logic in src/agenteval/dataset/validator.py to return `True` when only warnings exist (no errors)
- [X] T006 Update all existing `ValidationIssue(...)` constructor calls in src/agenteval/dataset/validator.py to include `severity="error"` explicitly
- [X] T007 [P] Add `case_version` field (`str | None = None`) to `CaseEvaluationTemplate` dataclass in src/agenteval/core/types.py
- [X] T008 Add `case_version: 1.0` to the YAML header of all 12 existing cases in data/cases/case_001/ through data/cases/case_012/expected_outcome.md
- [X] T009 Add `case_version: 1.0` to data/cases/demo_case/expected_outcome.md

**Checkpoint**: Foundation ready — severity model in place, all cases have `case_version`, types extended

---

## Phase 3: User Story 1 - Validate Dataset Before Commit (Priority: P1) MVP

**Goal**: Validator checks YAML header for 5 required fields, reports errors/warnings with severity, pre-commit hook blocks on errors

**Independent Test**: Run `agenteval-validate-dataset --repo-root .` against a dataset with valid cases and intentionally broken cases. Verify header errors are reported and exit code is non-zero.

### Tests for User Story 1

- [X] T010 [P] [US1] Add test for valid header with all 5 fields passes validation in tests/test_validator.py
- [X] T011 [P] [US1] Add test for missing `case_version` field produces severity=error in tests/test_validator.py
- [X] T012 [P] [US1] Add test for missing YAML header entirely produces severity=error in tests/test_validator.py
- [X] T013 [P] [US1] Add test for ValidationResult.ok=True when only warnings exist in tests/test_validator.py
- [X] T014 [P] [US1] Add test for ValidationResult.ok=False when at least one error exists in tests/test_validator.py

### Implementation for User Story 1

- [X] T015 [US1] Add `_parse_expected_outcome_header()` function to src/agenteval/dataset/validator.py that parses YAML front matter and returns a dict of header fields
- [X] T016 [US1] Add `_validate_header_fields()` function to src/agenteval/dataset/validator.py that checks for the 5 required fields (`Case ID`, `Primary Failure`, `Secondary Failures`, `Severity`, `case_version`) and returns `ValidationIssue` instances with `severity="error"` for each missing field
- [X] T017 [US1] Integrate header validation into the `validate_dataset()` pipeline in src/agenteval/dataset/validator.py — call after structure check, before security scan
- [X] T018 [US1] Update `main()` output formatting in src/agenteval/dataset/validator.py to prefix issues with `ERROR:` or `WARNING:` based on severity
- [X] T019 [US1] Update `main()` exit code logic in src/agenteval/dataset/validator.py to return 0 when only warnings exist
- [X] T020 [US1] Create .pre-commit-config.yaml at repository root with local hook running `agenteval-validate-dataset --repo-root .`
- [X] T021 [US1] Run `pytest tests/test_validator.py -v` to verify all new and existing tests pass

**Checkpoint**: Validator enforces header completeness, severity model works, pre-commit hook is in place

---

## Phase 4: User Story 2 - Auto-Generate Complete Demo Cases (Priority: P2)

**Goal**: Library function and CLI command to generate complete, valid cases with optional failure-type presets

**Independent Test**: Run `agenteval-generate-case --case-id test_gen`, then run `agenteval-validate-dataset --repo-root .` and verify the generated case passes all checks.

### Tests for User Story 2

- [X] T022 [P] [US2] Add test for `generate_case()` producing all 3 required files in tests/test_generator.py
- [X] T023 [P] [US2] Add test for generated case passing `validate_dataset()` in tests/test_generator.py
- [X] T024 [P] [US2] Add test for `generate_case()` with `failure_type="tool_hallucination"` producing correct header in tests/test_generator.py
- [X] T025 [P] [US2] Add test for `generate_case()` raising ValueError when case exists and `overwrite=False` in tests/test_generator.py
- [X] T026 [P] [US2] Add test for `generate_case()` with `overwrite=True` replacing existing case in tests/test_generator.py
- [X] T027 [P] [US2] Add test for `generate_case()` raising ValueError for invalid failure_type in tests/test_generator.py
- [X] T028 [P] [US2] Add test for `generate_case()` rejecting output_dir outside repo root in tests/test_generator.py

### Implementation for User Story 2

- [X] T029 [US2] Create src/agenteval/dataset/generator.py with `generate_case(case_id, failure_type, output_dir, overwrite) -> Path` function that produces prompt.txt, trace.json, and expected_outcome.md with all 5 required header fields including `case_version: 1.0`
- [X] T030 [US2] Validate output_dir is within repo root using `_safe_resolve_within()` in src/agenteval/dataset/generator.py before creating any files
- [X] T031 [US2] Add failure-type preset mappings in src/agenteval/dataset/generator.py for all 12 canonical failure categories (prompt text, trace structure, header metadata per type)
- [X] T032 [US2] Add `main(argv)` CLI entry point in src/agenteval/dataset/generator.py with argparse for `--case-id`, `--failure-type`, `--output-dir`, `--overwrite`
- [X] T033 [US2] Update src/agenteval/core/execution.py to import and delegate to `agenteval.dataset.generator.generate_case` for backward compatibility
- [X] T034 [US2] Update scripts/generate_trace.py to delegate to `agenteval.dataset.generator.generate_case`
- [X] T035 [US2] Run `pytest tests/test_generator.py -v` to verify all tests pass

**Checkpoint**: Generator produces valid cases with optional failure presets, CLI and library APIs work, backward compatible

---

## Phase 5: User Story 3 - Fail Fast on Invalid Cases (Priority: P2)

**Goal**: All errors across all cases reported in a single run with severity categorization; extra files tolerated

**Independent Test**: Create a dataset with 3 broken cases (missing file, bad schema, security violation). Run validation once and verify all 3 errors appear in output with case identifiers.

### Tests for User Story 3

- [X] T036 [P] [US3] Add test for batch reporting: 3 broken cases produce 3 issues in a single ValidationResult in tests/test_validator.py
- [X] T037 [P] [US3] Add test for extra files in case directory not causing errors in tests/test_validator.py
- [X] T038 [P] [US3] Add test for mixed severity: errors + warnings all reported together, ok=False in tests/test_validator.py

### Implementation for User Story 3

- [X] T039 [US3] Verify that `validate_dataset()` in src/agenteval/dataset/validator.py continues validating all cases after encountering an error (existing behavior, confirm no early-exit regressions from Phase 2-3 changes)
- [X] T040 [US3] Verify that case directories with extra files (beyond prompt.txt, trace.json, expected_outcome.md) do not trigger errors in src/agenteval/dataset/validator.py
- [X] T041 [US3] Add summary line to `main()` output in src/agenteval/dataset/validator.py showing total error and warning counts (e.g., `"Dataset validation failed (2 errors, 1 warning)."`)
- [X] T042 [US3] Run `pytest tests/test_validator.py -v` to verify all tests pass

**Checkpoint**: Batch error reporting confirmed, severity counts displayed, no false positives on extra files

---

## Phase 6: User Story 4 - Case Versioning for Reviewable Changes (Priority: P3)

**Goal**: Version-bump detection warns in validator; evaluation runner includes case_version in templates

**Independent Test**: Modify a case's trace.json without bumping case_version — validator should warn. Run the evaluation runner and verify case_version appears in output templates.

### Tests for User Story 4

- [X] T043 [P] [US4] Add test for version-bump detection: modified trace.json without version bump produces severity=warning in tests/test_validator.py
- [X] T044 [P] [US4] Add test for version-bump detection: modified prompt.txt only does NOT produce warning in tests/test_validator.py
- [X] T045 [P] [US4] Add test for version-bump detection: skipped when not in a git repo in tests/test_validator.py
- [X] T046 [P] [US4] Add test for runner including case_version in CaseEvaluationTemplate in tests/test_runner.py
- [X] T047 [P] [US4] Add test for runner handling missing case_version (None) gracefully in tests/test_runner.py

### Implementation for User Story 4

- [X] T048 [US4] Add `_check_version_bump()` function to src/agenteval/dataset/validator.py that uses `subprocess.run(["git", "diff", ...])` to detect changes to trace.json and expected_outcome.md, compares case_version, and returns `ValidationIssue` with `severity="warning"` if version unchanged
- [X] T049 [US4] Integrate `_check_version_bump()` into `validate_dataset()` pipeline in src/agenteval/dataset/validator.py — runs after header validation, skips silently if git unavailable
- [X] T050 [US4] Update `_parse_expected_outcome_header()` in src/agenteval/core/runner.py to extract `case_version` field from YAML header
- [X] T051 [US4] Update `CaseEvaluationTemplate` construction in src/agenteval/core/runner.py to include `case_version` from parsed header
- [X] T052 [US4] Update JSON template output in src/agenteval/core/runner.py to include `case_version` field
- [X] T053 [US4] Update Markdown template output in src/agenteval/core/runner.py to include case_version in the summary section (omit if None)
- [X] T054 [US4] Run `pytest tests/test_validator.py tests/test_runner.py -v` to verify all tests pass

**Checkpoint**: Version-bump detection warns on unversioned changes, runner propagates case_version into all templates

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Full validation, documentation, cleanup

- [X] T055 Run full test suite: `pytest tests/ -v` to verify no regressions across all modules
- [X] T056 Run linting: `ruff check src/` and `ruff format --check src/`
- [X] T057 Run type checking: `mypy src/`
- [X] T058 Run dataset validation: `agenteval-validate-dataset --repo-root .`
- [X] T059 Run evaluation runner: `agenteval-eval-runner --dataset-dir data/cases --output-dir reports` and verify case_version appears in output
- [X] T060 [P] Validate quickstart.md scenarios end-to-end (generate case, validate, run runner)
- [X] T061 [P] Update src/agenteval/dataset/__init__.py to export `generate_case` and `validate_dataset`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — core validator extensions
- **US2 (Phase 4)**: Depends on Phase 2 — can run in parallel with US1
- **US3 (Phase 5)**: Depends on Phase 3 (uses severity model and header validation)
- **US4 (Phase 6)**: Depends on Phase 3 (uses header parsing in validator)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependencies on other stories
- **US2 (P2)**: Can start after Phase 2 — independent of US1 (different module)
- **US3 (P2)**: Depends on US1 (severity model must exist) — extends validator behavior
- **US4 (P3)**: Depends on US1 (header parsing must exist) — adds version-bump detection + runner changes

### Within Each User Story

- Tests written FIRST, verified to FAIL before implementation
- Library functions before CLI wrappers
- Core logic before integration
- Full test pass before checkpoint

### Parallel Opportunities

- T007 can run in parallel with T004-T006 (different files: types.py vs validator.py)
- T008, T009 can run in parallel (different case directories)
- T010-T014 can all run in parallel (independent test cases)
- T022-T028 can all run in parallel (independent test cases)
- US1 and US2 can run in parallel after Phase 2 (different modules)
- T043-T047 can all run in parallel (independent test cases)
- T055-T061 in Phase 7: T056, T057, T060, T061 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together:
Task: "Add test for valid header with all 5 fields passes validation in tests/test_validator.py"
Task: "Add test for missing case_version field produces severity=error in tests/test_validator.py"
Task: "Add test for missing YAML header entirely produces severity=error in tests/test_validator.py"
Task: "Add test for ValidationResult.ok=True when only warnings exist in tests/test_validator.py"
Task: "Add test for ValidationResult.ok=False when at least one error exists in tests/test_validator.py"
```

## Parallel Example: User Story 2

```bash
# Launch all tests for US2 together:
Task: "Add test for generate_case() producing all 3 required files in tests/test_generator.py"
Task: "Add test for generated case passing validate_dataset() in tests/test_generator.py"
Task: "Add test for generate_case() with failure_type producing correct header in tests/test_generator.py"
Task: "Add test for generate_case() raising ValueError when case exists in tests/test_generator.py"
Task: "Add test for generate_case() rejecting output_dir outside repo root in tests/test_generator.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Run `agenteval-validate-dataset --repo-root .` — all cases pass with `case_version`
5. Pre-commit hook blocks invalid commits

### Incremental Delivery

1. Setup + Foundational → severity model + case_version migration done
2. US1 → header validation + pre-commit hook (MVP!)
3. US2 → case generator library + CLI (parallel with US1 if staffed)
4. US3 → batch reporting confirmation + summary counts
5. US4 → version-bump detection + runner integration
6. Polish → full suite validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
