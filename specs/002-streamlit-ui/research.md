# Research: Streamlit UI for AgentEval Workbench

## Decision 1: UI Framework

**Decision**: Streamlit
**Rationale**: User explicitly requested Streamlit. It supports multi-page apps with sidebar navigation, runs locally, requires no frontend build toolchain, and fits the "thin UI layer" constraint. The app is single-file entry with modular pages.
**Alternatives considered**: Gradio (less flexible layout), Panel (heavier), Flask+Jinja (requires HTML/CSS), plain CLI (insufficient for non-CLI users).

## Decision 2: Dependency Placement

**Decision**: Optional dependency under `[project.optional-dependencies.ui]`
**Rationale**: Constitution V mandates jsonschema as the only runtime dependency. Adding Streamlit to core would violate this principle. Optional extras allow `pip install -e ".[ui]"` for UI users while keeping the core library dependency-free.
**Alternatives considered**: Core dependency (violates Constitution V), separate package (over-engineered for v1).

## Decision 3: Service Layer Architecture

**Decision**: New `src/agenteval/core/service.py` module instead of modifying runner.py or report.py
**Rationale**: Runner.py and report.py have well-defined CLI responsibilities. Adding UI-facing wrappers directly to them risks breaking existing behavior. A separate service layer composes existing public APIs (generate_case, validate_dataset, runner.main, report.main) without touching any existing code. This is the smallest safe change.
**Alternatives considered**: Adding wrapper functions to runner.py/report.py (higher risk of breaking CLI), calling CLI entry points via subprocess (fragile, loses error context), importing private functions from runner/report (fragile coupling to internals).

## Decision 4: Service Layer Evaluation Strategy

**Decision**: Service layer calls `runner.main(argv)` and `report.main(argv)` as functions, then reads their generated JSON output files from disk.
**Rationale**: runner.main() and report.main() already handle all the complex orchestration (loading rubrics, iterating cases, building templates, writing files). Calling them with constructed argv arrays reuses 100% of existing logic with zero duplication. Reading the JSON outputs afterward gives the UI structured data to display.
**Alternatives considered**: Extracting internal logic from runner/report into public functions (requires modifying those files), reimplementing evaluation logic in service.py (duplicates code, violates FR-009).

## Decision 5: Streamlit App Location

**Decision**: `app/` directory at repository root, outside `src/agenteval/`
**Rationale**: The Streamlit app is a consumer of the library, not part of it. Placing it outside the package keeps the library independent of Streamlit, avoids Streamlit as a transitive dependency, and follows the same pattern as CLI entry points (thin wrappers that call library code).
**Alternatives considered**: `src/agenteval/ui/` (couples library to Streamlit), `scripts/` (conflates scripts with app), root-level `streamlit_app.py` (clutters repo root).

## Decision 6: Multi-Page Architecture

**Decision**: Streamlit multi-page with sidebar navigation — 4 pages (Generate, Evaluate, Inspect, Report)
**Rationale**: Matches the 4 user stories in the spec. Each page is independently testable and maps 1:1 to a user workflow. Sidebar provides constant navigation without page reloads.
**Alternatives considered**: Single scrollable page (poor UX for 4 distinct workflows), tabs (less discoverable than sidebar).

## Decision 7: Validation Result Partitioning

**Decision**: UI-layer filtering of `ValidationResult.issues` by `case_id` field
**Rationale**: The existing `validate_dataset()` returns all issues for all cases. Rather than modifying the library function (which would break its contract), the UI partitions issues by matching `case_id` against the newly generated case. This keeps the library function unchanged and the partitioning logic trivial (a list comprehension in the page module).
**Alternatives considered**: Adding a `case_filter` parameter to `validate_dataset()` (unnecessary complexity for one consumer), running validation twice (wasteful).
