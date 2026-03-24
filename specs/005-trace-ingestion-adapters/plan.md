# Implementation Plan: Trace Ingestion Adapters

**Branch**: `005-trace-ingestion-adapters` | **Date**: 2026-03-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-trace-ingestion-adapters/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Enable real-world trace ingestion from popular agent frameworks (LangChain, OpenTelemetry, CrewAI, OpenAI) and custom formats. Provide a pluggable adapter architecture with automatic format detection, validation, and clear error messages. This removes the manual trace conversion barrier that currently blocks adoption.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: jsonschema>=4.21.0 (existing); No protobuf (OTLP JSON-only)
**Storage**: File-based (trace.json output)
**Testing**: pytest
**Target Platform**: Cross-platform CLI (Windows/Linux/macOS)
**Project Type**: Library + CLI tool
**Performance Goals**: Process typical trace files (<1MB) in <1 second; support up to 10MB with warning, hard limit 50MB
**Constraints**: Offline-only, no network calls, all file I/O within repo root; fail-fast on schema errors, collect warnings; bulk mode continues on errors
**Scale/Scope**: 5 adapters (OTel, LangChain, CrewAI, OpenAI, Generic), 1 new CLI command

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Applicable Principles

1. **Security First (NON-NEGOTIABLE)** - ✅ PASS
   - Ingested traces will be validated against security patterns (no secrets, URLs, absolute paths)
   - All file I/O uses `_safe_resolve_within()` to stay within repo bounds
   - No network calls during ingestion

2. **Schema-First Contracts** - ✅ PASS
   - All converted traces MUST validate against `schemas/trace_schema.json`
   - Adapters will use existing trace schema validation
   - No schema changes required for this feature

3. **Offline & Sandboxed Execution** - ✅ PASS
   - No network calls in any adapter
   - File I/O constrained to repo root
   - Ingestion is purely local transformation

4. **Test-Driven Quality** - ✅ PASS
   - Each adapter will have unit tests with sample fixtures
   - Integration tests for ingest → validate pipeline
   - Error handling tests for malformed inputs

5. **Minimal Dependencies** - ⚠️ NEEDS REVIEW
   - May need protobuf library for OpenTelemetry OTLP binary format
   - Alternative: only support OTLP JSON format (no new dependency)
   - **ACTION**: Research if protobuf is strictly necessary

6. **Library-First Architecture** - ✅ PASS
   - Adapter logic in `src/agenteval/ingestion/`
   - CLI (`agenteval-ingest`) as thin wrapper
   - All adapters importable as library code

7. **Backward-Compatible Evolution** - ✅ PASS
   - No changes to existing evaluation runner
   - Additive feature, no breaking changes
   - Existing traces and workflows unaffected

### Gate Status: ✅ PASS

**All questions resolved** - see research.md and spec clarifications (2026-03-24)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/agenteval/
├── ingestion/           # NEW: Trace ingestion adapters
│   ├── __init__.py      # Exports adapters + auto-detection
│   ├── base.py          # TraceAdapter Protocol
│   ├── otel.py          # OpenTelemetry adapter
│   ├── langchain.py     # LangChain adapter
│   ├── crewai.py        # CrewAI adapter
│   ├── openai_raw.py    # Raw OpenAI API adapter
│   ├── generic.py       # Generic JSON mapping adapter
│   └── cli.py           # CLI entry point logic
├── schemas/             # EXISTING: Trace/rubric types
│   └── trace.py         # Used by adapters for output
├── dataset/             # EXISTING: Validation
│   └── validator.py     # Used to validate converted traces
└── core/                # EXISTING: Evaluation engine
    └── loader.py        # Used to load/validate traces

tests/
├── ingestion/           # NEW: Adapter tests
│   ├── __init__.py
│   ├── test_otel.py
│   ├── test_langchain.py
│   ├── test_crewai.py
│   ├── test_openai_raw.py
│   ├── test_generic.py
│   ├── fixtures/        # Sample input files
│   │   ├── otel_trace.json
│   │   ├── langchain_run.json
│   │   ├── crewai_log.json
│   │   └── openai_response.json
│   └── test_integration.py  # End-to-end ingest→validate→evaluate
└── [existing test modules]

pyproject.toml           # Add agenteval-ingest CLI entry point
```

**Structure Decision**: Single project (AgentEval Workbench) with new `ingestion/` module under `src/agenteval/`. Follows existing library-first architecture with CLI as thin wrapper.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. All constitutional requirements satisfied.

---

## Post-Design Constitution Check

*Re-evaluated after Phase 1 design completion*

### Final Gate Status: ✅ PASS

All design decisions align with constitutional principles:

1. **Security First** - ✅ PASS
   - All adapters validate output traces for security violations
   - File I/O uses `_safe_resolve_within()` consistently
   - No network calls in any adapter implementation

2. **Schema-First Contracts** - ✅ PASS
   - All converted traces validated against `schemas/trace_schema.json`
   - No schema modifications required
   - Adapter output contracts documented in data-model.md

3. **Offline & Sandboxed Execution** - ✅ PASS
   - Zero network dependencies
   - All file paths validated against repo root
   - Adapters are pure transformations

4. **Test-Driven Quality** - ✅ PASS
   - Test plan includes unit tests for each adapter
   - Integration tests for full pipeline
   - Fixture-based testing with sample inputs

5. **Minimal Dependencies** - ✅ PASS (RESOLVED)
   - **Decision**: Support OTLP JSON-only (no protobuf)
   - **Net new dependencies**: ZERO
   - All adapters use stdlib + existing jsonschema

6. **Library-First Architecture** - ✅ PASS
   - Core logic in `src/agenteval/ingestion/`
   - CLI as thin wrapper in `cli.py`
   - All adapters importable as library code

7. **Backward-Compatible Evolution** - ✅ PASS
   - No changes to existing evaluation pipeline
   - Additive feature only
   - Existing workflows unaffected

### Research Resolution

**Original question**: "Do we need protobuf library for OTel?"
**Resolution**: No - support OTLP JSON format only
**Impact**: Zero new dependencies, aligns with Minimal Dependencies principle

---

## Phase 1 Outputs

✅ **research.md** - All unknowns resolved, zero new dependencies
✅ **data-model.md** - Entities, mappings, and validation rules defined
✅ **contracts/cli-contract.md** - CLI interface fully specified
✅ **quickstart.md** - User guide with 5 example workflows
✅ **Agent context updated** - CLAUDE.md includes new feature context
✅ **Spec clarifications** - 4 critical ambiguities resolved (see spec.md § Clarifications)

---

## Clarifications Impact on Implementation

**Date**: 2026-03-24

The following clarifications were added to the spec and affect implementation:

### 1. Trace Size Limits
- **Decision**: 10MB soft limit (warn), 50MB hard limit (fail)
- **Impact**:
  - Add file size check before parsing
  - Emit warning for 10MB < size < 50MB
  - Raise clear error for size >= 50MB
  - Update error messages in CLI

### 2. Validation Strategy
- **Decision**: Fail-fast on schema errors, collect warnings
- **Impact**:
  - Schema validation failures abort immediately
  - Mapping warnings accumulate and display together
  - Two error paths in adapter logic

### 3. Bulk Ingestion Error Handling
- **Decision**: Continue on errors, report summary
- **Impact**:
  - Bulk mode wraps each file in try-catch
  - Track success/failure counts
  - Display summary: "✓ Converted N/M traces successfully. X failed"
  - Do NOT abort batch on individual failures

### 4. Progress Reporting
- **Decision**: Progress bar for bulk, quiet for single files
- **Impact**:
  - Detect bulk vs. single mode (input is dir vs. file)
  - Use progress bar library (e.g., tqdm) for bulk operations
  - Single-file mode: minimal output (success/error only)
  - Optional --verbose flag for detailed logs

---

## Clarification-Updated Artifacts

Following spec clarifications (2026-03-24), the following design artifacts have been updated:

✅ **plan.md** - Technical Context updated with clarified constraints
✅ **data-model.md** - Data flow updated with size check and validation strategy
✅ **contracts/cli-contract.md** - Exit codes and examples updated with size limits and progress reporting
✅ **spec.md** - Constraints section added with all clarifications

All planning artifacts are now **aligned and ready for task generation**.

---

## Next Steps

This plan is now ready for task generation via `/speckit.tasks`.

The tasks phase will produce:
- **tasks.md** - Dependency-ordered implementation tasks
- Task breakdown by module (base, adapters, CLI, tests)
- Estimated complexity per task
- Implementation considerations for size limits, validation strategy, bulk error handling, and progress reporting
