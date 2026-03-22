<!--
Sync Impact Report
- Version change: 0.0.0 → 1.0.0
- Modified principles: N/A (initial constitution)
- Added sections:
  - Core Principles: 5 principles (Security First, Schema-Driven, Offline & Sandboxed,
    Test-Driven Quality, Minimal Dependencies)
  - Security Constraints (Section 2)
  - Development Workflow (Section 3)
  - Governance
- Removed sections: N/A
- Templates requiring updates:
  - .specify/templates/plan-template.md — ✅ compatible (Constitution Check section exists)
  - .specify/templates/spec-template.md — ✅ compatible (no constitution-specific references)
  - .specify/templates/tasks-template.md — ✅ compatible (phase structure aligns)
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

### II. Schema-Driven Contracts

All data interchange MUST be governed by explicit, versioned JSON schemas.

- Every `trace.json` MUST validate against `schemas/trace_schema.json`.
- Every rubric MUST validate against `schemas/rubric_schema.json`.
- Schema changes MUST be backward-compatible: add new optional fields rather than
  breaking existing traces.
- Both `schemas/*.json` and `docs/dataset_*.md` MUST be updated together when
  modifying trace or rubric semantics.
- Python type bindings in `src/agenteval/schemas/` MUST stay in sync with their
  JSON schema counterparts.

**Rationale**: Schemas are the contract between data producers (benchmark authors),
the evaluation engine, and downstream consumers (reports, dashboards). Breaking a
schema silently corrupts the entire pipeline.

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

**Version**: 1.0.0 | **Ratified**: 2026-03-21 | **Last Amended**: 2026-03-21
