<!--
Sync Impact Report
- Version change: 1.0.0 → 1.1.0
- Modified principles:
  - "II. Schema-Driven Contracts" → "II. Schema-First Contracts" (renamed + expanded
    with reproducibility-first emphasis and explicit trace validation requirement)
  - "IV. Test-Driven Quality" → expanded to explicitly mandate testing for schema
    contracts, dataset validation, and report generation
- Added principles:
  - "VI. Dataset Completeness (NON-NEGOTIABLE)" — every case must include prompt.txt,
    trace.json, expected_outcome.md; all must be valid before commit
  - "VII. Backward-Compatible Evolution" — features must preserve backward
    compatibility for the evaluation runner
  - "VIII. Library-First Architecture" — UI features must remain thin wrappers
    over library code in src/
- Added sections: None
- Removed sections: None
- Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ compatible (dynamic Constitution Check)
  - .specify/templates/spec-template.md — ✅ compatible
  - .specify/templates/tasks-template.md — ✅ compatible
- Follow-up TODOs: None
-->

# AgentEval Workbench Constitution

## Core Principles

### I. Security First (NON-NEGOTIABLE)

Security is a hard constraint, not a quality attribute to be traded off.

- All benchmark data MUST be free of API keys, tokens, secrets, and credentials.
- No external URLs (http/https) are permitted in case files.
- No absolute filesystem paths are permitted in case files.
- No path traversal sequences (`../` or `..\`) are permitted in case files.
- All filesystem access MUST be constrained within the repository root using
  symlink-safe resolution (`_safe_resolve_within()`).
- Validation MUST run offline with zero network calls.
- The dataset validator (`agenteval-validate-dataset`) MUST pass before every commit;
  CI blocks merge on failure.

**Rationale**: Benchmark data flows through automated pipelines and reviewer
workflows. A single leaked secret or traversal exploit compromises the entire
evaluation chain.

### II. Schema-First Contracts

This project is schema-first and reproducibility-first. All data interchange
MUST be governed by explicit, versioned JSON schemas.

- Every `trace.json` MUST validate against `schemas/trace_schema.json`.
- All generated traces MUST validate against the trace schema before being
  accepted into the dataset.
- Every rubric MUST validate against `schemas/rubric_schema.json`.
- Schema changes MUST be backward-compatible: add new optional fields rather than
  breaking existing traces.
- Both `schemas/*.json` and `docs/dataset_*.md` MUST be updated together when
  modifying trace or rubric semantics.
- Python type bindings in `src/agenteval/schemas/` MUST stay in sync with their
  JSON schema counterparts.

**Rationale**: Schemas are the contract between data producers (benchmark authors),
the evaluation engine, and downstream consumers (reports, dashboards). Breaking a
schema silently corrupts the entire pipeline. Schema-first design ensures
reproducibility across environments and reviewers.

### III. Offline & Sandboxed Execution

The framework MUST operate without network access and within repository boundaries.

- No runtime code path may initiate network calls.
- All file I/O MUST use `_get_repo_root()` + `_safe_resolve_within()` helpers to
  prevent escaping the repository root.
- Symlinks MUST be resolved and validated before any read or write operation.

**Rationale**: Evaluation workloads run in CI, air-gapped environments, and
reviewer laptops. Network dependencies introduce flakiness, security risk, and
reproducibility failures.

### IV. Test-Driven Quality

All modules MUST have automated test coverage; untested code is incomplete code.

- New modules MUST ship with corresponding `pytest` tests.
- Tests MUST cover happy paths, error paths, and boundary conditions.
- Testing is mandatory for: schema contracts, dataset validation, and report
  generation. These three areas MUST NOT ship without tests.
- CI MUST gate on: `agenteval-validate-dataset`, `ruff check`, `ruff format --check`,
  `mypy --strict`, and `pytest`.
- Rubric changes MUST be versioned (e.g., `v2_agent_general`) rather than mutating
  existing versions in place.

**Rationale**: An evaluation framework that produces incorrect results is worse than
no framework at all. Automated tests are the only scalable way to maintain
correctness as the codebase grows.

### V. Minimal Dependencies

The runtime dependency surface MUST be kept as small as possible.

- `jsonschema` (>=4.21.0) is the only permitted runtime dependency.
- New runtime dependencies MUST NOT be introduced unless strictly necessary and
  explicitly justified.
- Development dependencies (ruff, mypy, pytest) are permitted under `[dev]` extras.

**Rationale**: Every dependency is an attack surface, a compatibility risk, and a
maintenance burden. For a security-focused evaluation tool, a minimal footprint is
a feature.

### VI. Dataset Completeness (NON-NEGOTIABLE)

All dataset cases MUST be complete and valid before commit.

- Every case directory under `data/cases/` MUST contain exactly three files:
  `prompt.txt`, `trace.json`, and `expected_outcome.md`.
- No partial or placeholder cases are permitted in the repository.
- The dataset validator enforces completeness; incomplete cases MUST NOT be
  committed even with `--no-verify`.

**Rationale**: Incomplete cases produce misleading evaluation results and break
downstream tooling (runner, report, calibration). The three-file contract is the
atomic unit of the benchmark.

### VII. Backward-Compatible Evolution

Features MUST preserve backward compatibility for the evaluation runner.

- New features MUST NOT break existing `agenteval-eval-runner` or
  `agenteval-eval-report` workflows.
- Trace schema evolution MUST be additive: new optional fields only, never remove
  or rename existing fields.
- Rubric versions MUST be immutable once published; create new versions (e.g.,
  `v2_agent_general`) instead of mutating existing ones.
- CLI entry points MUST maintain their existing argument contracts; new arguments
  MUST default to preserving prior behavior.

**Rationale**: Evaluation pipelines depend on stable interfaces. Breaking the
runner or report CLI invalidates in-progress evaluations and erodes trust in
the framework.

### VIII. Library-First Architecture

UI features MUST remain thin wrappers over library code in `src/`.

- All business logic MUST live in `src/agenteval/` as importable library code.
- CLI entry points MUST be thin wrappers that parse arguments, call library
  functions, and format output.
- Scripts in `scripts/` are convenience utilities; they MUST delegate to library
  code rather than duplicating logic.
- No evaluation logic may exist solely in a CLI or script without a corresponding
  library function.

**Rationale**: Library-first architecture enables testing without subprocess
overhead, supports programmatic integration, and prevents logic from being
trapped behind CLI argument parsing.

## Security Constraints

These constraints apply to all code, data, documentation, and CI configuration:

- **Secret scanning**: Regex-based patterns detect API keys, Bearer tokens, and
  other credential formats in all benchmark files. The validator is the gatekeeper.
- **URL blocking**: No `http://` or `https://` URLs in any case file.
- **Path safety**: Absolute paths and traversal sequences are rejected at validation
  time.
- **Filesystem sandboxing**: All file operations are confined to the repository root
  via symlink-aware path resolution.
- **CI enforcement**: The GitHub Actions workflow runs the validator on every push
  and pull request. Failure blocks merge unconditionally.

## Development Workflow

### Code Standards

- Python >= 3.10 with `from __future__ import annotations`.
- `src/` layout: all packages under `src/agenteval/`.
- Ruff: line-length 100, target py310.
- Mypy: strict mode (`disallow_untyped_defs`, `warn_return_any`,
  `no_implicit_optional`).

### Pre-Commit Checklist

Before every commit, the following MUST pass:

1. `agenteval-validate-dataset --repo-root .`
2. `ruff check src/` and `ruff format --check src/`
3. `mypy src/`
4. `pytest tests/ -v` (when tests exist for modified modules)

### Trace Schema Evolution

- `steps` is an append-only, deterministically ordered event log.
- Use `event_id`, `parent_event_id`, `actor_id`, `span_id`, and `context_refs`
  when extending traces.
- Never remove or rename existing fields; deprecate by adding replacements.

### Failure Taxonomy

- 12 canonical failure categories defined in `docs/failure_taxonomy.md`.
- Case mappings tracked in `docs/failure_mapping.md`.
- Coverage matrix maintained in `docs/failure_coverage_matrix.md`.
- New failure categories MUST be added to all three documents together.

## Governance

This constitution is the authoritative source of project principles and constraints.
It supersedes ad-hoc decisions and informal conventions.

- **Amendments** require: (1) a documented rationale, (2) review of downstream
  impact on templates, schemas, and CI, and (3) a version bump following SemVer.
- **Versioning**: MAJOR for principle removals or redefinitions, MINOR for new
  principles or material expansions, PATCH for clarifications and wording fixes.
- **Compliance**: All pull requests and code reviews MUST verify adherence to these
  principles. The `CLAUDE.md` file MUST stay aligned with this constitution.
- **Guidance**: Runtime development guidance lives in `CLAUDE.md`; this constitution
  defines the non-negotiable constraints that `CLAUDE.md` implements.

**Version**: 1.1.0 | **Ratified**: 2026-03-21 | **Last Amended**: 2026-03-21
