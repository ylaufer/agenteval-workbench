"""Next-step navigation hints for AgentEval Workbench UI."""
from __future__ import annotations

import streamlit as st

# Logical next step after completing the primary action on each page
_NEXT_STEP: dict[str, tuple[str, str, str]] = {
    "Generate": (
        "Inspect",
        ":material/search: Next: inspect the trace",
        "Open the **Inspect** page to browse the generated trace and add annotations.",
    ),
    "Inspect": (
        "Evaluate",
        ":material/rule: Next: run auto-scoring",
        "Head to the **Evaluate** page to run auto-scoring on your cases.",
    ),
    "Evaluate": (
        "Report",
        ":material/summarize: Next: generate a report",
        "Go to the **Report** page to produce an aggregated summary of all evaluations.",
    ),
    "Report": (
        "Compare",
        ":material/compare: Next: compare runs",
        "Use the **Compare** page to diff this run against a baseline.",
    ),
}


def render_next_step_hint(current_page: str) -> None:
    """Render a subtle next-step suggestion after completing an action.

    Args:
        current_page: The PAGES key for the current page (e.g. "Generate").
    """
    entry = _NEXT_STEP.get(current_page)
    if entry is None:
        return
    target_page, headline, detail = entry
    with st.container():
        st.info(
            f"{headline}\n\n{detail}",
            icon=":material/arrow_forward:",
        )
        if st.button(f"Go to {target_page}", key=f"_next_step_{current_page}"):
            st.session_state.nav_to_page = target_page
            st.rerun()
