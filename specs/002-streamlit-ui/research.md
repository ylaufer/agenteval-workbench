# Research: Streamlit UI for AgentEval Workbench

## Decision 1: UI Framework

**Decision**: Streamlit
**Rationale**: User explicitly requested Streamlit. It supports multi-page apps with sidebar navigation, runs locally, requires no frontend build toolchain, and fits the "thin UI layer" constraint. The app is single-file entry with modular pages.
**Alternatives considered**: Gradio (less flexible layout), Panel (heavier), Flask+Jinja (requires HTML/CSS), plain CLI (insufficient for non-CLI users).

## Decision 2: Dependency Placement

**Decision**: Optional dependency under `[project.optional-dependencies.ui]`
**Rationale**: Constitution V mandates jsonschema as the only runtime dependency. Adding Streamlit to core would violate this principle. Optional extras allow `pip install -e ".[ui]"` for UI users while keeping the core library dependency-free.
**Alternatives considered**: Core dependency (violates Constitution V), separate package (over-engineered for v1).

## Decision 3: Wrapper Function Placement

**Decision**: Add `run_evaluation()` to `runner.py` and `generate_summary_report()` to `report.py`
**Rationale**: Co-locating wrapper functions with existing logic keeps related code together, avoids circular imports, and follows Constitution VIII (library-first). The existing `main()` functions are refactored to delegate to these wrappers.
**Alternatives considered**: Separate `src/agenteval/core/api.py` module (introduces another file without benefit), direct import of private functions in UI (fragile coupling to internals).

## Decision 4: Multi-Page Architecture

**Decision**: Streamlit multi-page with sidebar navigation — 4 pages (Generate, Evaluate, Inspect, Report)
**Rationale**: Matches the 4 user stories in the spec. Each page is independently testable and maps 1:1 to a user workflow. Sidebar provides constant navigation without page reloads.
**Alternatives considered**: Single scrollable page (poor UX for 4 distinct workflows), tabs (less discoverable than sidebar).

## Decision 5: Validation Result Partitioning

**Decision**: UI-layer filtering of `ValidationResult.issues` by `case_id` field
**Rationale**: The existing `validate_dataset()` returns all issues for all cases. Rather than modifying the library function (which would break its contract), the UI partitions issues by matching `case_id` against the newly generated case. This keeps the library function unchanged and the partitioning logic trivial (a list comprehension).
**Alternatives considered**: Adding a `case_filter` parameter to `validate_dataset()` (unnecessary complexity for one consumer), running validation twice (wasteful).
