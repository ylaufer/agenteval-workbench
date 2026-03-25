# Implementation Plan: Guided Onboarding

**Branch**: `006-guided-onboarding` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-guided-onboarding/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Reduce time-to-first-value for new users from "read 3 docs" to "see results in 60 seconds" by implementing:
1. First-run detection with welcome modal and one-click demo flow
2. Contextual help system on every UI page with tooltips
3. Interactive step-by-step tutorial mode
4. Quick reference sidebar for failure taxonomy and rubric dimensions

Technical approach: Enhance existing Streamlit UI with session state for first-run detection, collapsible help sections, tooltip components, and a demo orchestration function that runs the full evaluate workflow programmatically.

## Technical Context

**Language/Version**: Python 3.10+ (from __future__ import annotations)
**Primary Dependencies**: Streamlit (already in [ui] extras), existing service layer (src/agenteval/core/service.py)
**Storage**: User preferences in Streamlit session state + optional file-based persistence
**Testing**: pytest for UI helper functions, manual QA for Streamlit UI interactions
**Target Platform**: Web browser (Streamlit app, localhost:8501)
**Project Type**: Web application (Streamlit UI enhancement)
**Performance Goals**: Demo flow completes in <60 seconds, UI interactions feel instant (<100ms)
**Constraints**: Must work offline (no network calls), must not break existing UI pages
**Scale/Scope**: 4 existing UI pages + new onboarding components, ~10 help sections, ~20 tooltips

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Phase 0 Check

**I. Security First**: ✅ PASS
- No benchmark data modified
- No file I/O beyond reading existing docs
- No network calls
- No secrets or credentials involved

**II. Schema-First Contracts**: ✅ PASS
- No schema changes
- Uses existing trace schema via service layer

**III. Offline & Sandboxed Execution**: ✅ PASS
- Entirely offline operation
- Uses existing filesystem helpers for doc access

**IV. Test-Driven Quality**: ⚠️ ADVISORY
- Streamlit UI testing is challenging (mostly manual QA)
- Helper functions (first-run detection, demo orchestration) MUST have unit tests
- UI interactions will be manually tested

**V. Minimal Dependencies**: ✅ PASS
- Uses existing Streamlit dependency (already in [ui] extras)
- No new runtime dependencies

**VI. Dataset Completeness**: ✅ N/A
- UI-only feature, doesn't modify dataset

**VII. Backward-Compatible Evolution**: ✅ PASS
- Enhances existing UI pages without breaking functionality
- New components are additive
- Existing users can ignore tutorial

**VIII. Library-First Architecture**: ✅ PASS
- Demo orchestration will use existing service layer (service.py)
- UI components are thin wrappers
- No evaluation logic in UI code

**Overall**: ✅ PASS with ADVISORY on testing (inherent Streamlit limitation)

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
app/
├── app.py                      # Main entry point (existing)
├── page_generate.py            # Generate page (existing)
├── page_evaluate.py            # Evaluate page (existing)
├── page_inspect.py             # Inspect page (existing)
├── page_report.py              # Report page (existing)
├── components/                 # NEW: Reusable UI components
│   ├── __init__.py
│   ├── welcome_modal.py        # First-run welcome dialog
│   ├── help_section.py         # Collapsible help component
│   ├── tooltip.py              # Tooltip helper
│   └── quick_reference.py      # Sidebar reference sheets
├── onboarding/                 # NEW: Onboarding logic
│   ├── __init__.py
│   ├── first_run.py            # First-run detection & state
│   ├── demo.py                 # Demo flow orchestration
│   └── content.py              # Help text and tooltip content
└── utils/                      # NEW: UI utilities
    ├── __init__.py
    └── preferences.py          # User preference persistence

tests/
└── app/                        # NEW: App tests
    ├── test_first_run.py
    ├── test_demo.py
    └── test_preferences.py

docs/
├── quick_reference_taxonomy.md # NEW: Failure taxonomy quick ref
└── quick_reference_rubric.md   # NEW: Rubric dimensions quick ref
```

**Structure Decision**: Streamlit UI enhancement using component-based architecture. New directories under `app/` for onboarding components, with helper functions tested in `tests/app/`. Content lives in `app/onboarding/content.py` for easy maintenance.

## Complexity Tracking

*No violations - all constitution checks passed.*

---

## Post-Design Constitution Check

*Re-evaluation after Phase 1 design complete*

**I. Security First**: ✅ PASS
- No security-sensitive data involved
- File I/O limited to ~/.agenteval/preferences.json (user-owned)
- No external data sources

**II. Schema-First Contracts**: ✅ PASS
- No schema modifications
- Uses existing trace schema via service layer
- Preferences.json is simple JSON, no formal schema needed

**III. Offline & Sandboxed Execution**: ✅ PASS
- Entirely offline operation confirmed in design
- Filesystem access limited to user home directory (~/.agenteval/)

**IV. Test-Driven Quality**: ✅ PASS
- Helper functions (first_run.py, demo.py, preferences.py) have unit tests
- UI components tested via manual QA (inherent Streamlit limitation)
- Test coverage plan documented in quickstart.md

**V. Minimal Dependencies**: ✅ PASS
- Zero new dependencies
- Uses existing Streamlit (already in [ui] extras)

**VI. Dataset Completeness**: ✅ N/A
- UI-only feature

**VII. Backward-Compatible Evolution**: ✅ PASS
- No breaking changes to existing UI
- New components are additive
- Existing workflows unaffected

**VIII. Library-First Architecture**: ✅ PASS
- Demo orchestration uses service layer (service.py)
- Helper functions in app/ are thin utilities, not business logic
- All evaluation logic remains in src/agenteval/

**Final Status**: ✅ ALL CHECKS PASSED
