# Implementation Plan: UI Polish (Feature 011)

## Tech Stack
- Python 3.10+, Streamlit (existing `[ui]` extra)
- No new runtime dependencies

## Architecture

### New files
- `app/components/empty_state.py` — `render_empty_state(icon, title, message, action_label, action_page)` using `st.container(border=True, horizontal_alignment="center")`
- `app/components/workflow_nav.py` — `render_next_step_hint(current_page)` suggestion banner

### Modified files
- `app/app.py` — workflow step indicators in sidebar showing current position
- `app/page_generate.py` — next-step hint after case generation
- `app/page_evaluate.py` — `render_empty_state` for no-cases/no-runs, `st.badge()` for severity/failure, next-step hint after scoring
- `app/page_report.py` — `render_empty_state` for no-evaluations scenario
- `app/page_inspect.py` — `render_empty_state` for no-cases scenario, `st.badge()` for step type/severity
- `app/page_compare.py` — `render_empty_state` for < 2 runs scenario

## Design Decisions
- Material icons (`:material/icon_name:`) for empty state icons — no emojis
- `st.badge()` for status indicators (severity, step type, failure type)
- `st.toast()` for lightweight confirmations post-save
- `st.container(border=True, horizontal_alignment="center")` for empty states
- Sentence casing throughout
- Session state key `nav_to_page` for cross-page navigation hints that trigger sidebar update
- No new runtime deps, no CSS injection
