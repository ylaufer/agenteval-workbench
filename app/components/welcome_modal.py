"""Welcome modal for first-time users."""
from __future__ import annotations

import streamlit as st
from onboarding.first_run import mark_first_run_complete


@st.dialog("Welcome to AgentEval Workbench", width="large")
def show_welcome_modal() -> None:
    """Display welcome modal with demo and skip options."""

    st.markdown(
        """
    This tool helps you evaluate LLM agent performance using structured rubrics and failure taxonomies.

    **Get started in 60 seconds:**

    The demo will:
    • Generate a sample benchmark case
    • Validate it against the schema
    • Run the evaluation pipeline
    • Show you an annotated report
    """
    )

    st.space("medium")

    # Button group with horizontal alignment
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        if st.button("▶ Run Demo", type="primary", use_container_width=True):
            # Mark modal as shown, start demo
            mark_first_run_complete(tutorial_skipped=False)
            st.session_state.demo_in_progress = True
            st.rerun()  # Close dialog and start demo

        if st.button("Skip Tutorial", use_container_width=True):
            # Mark as complete, skip demo
            mark_first_run_complete(tutorial_skipped=True)
            st.rerun()  # Close dialog
