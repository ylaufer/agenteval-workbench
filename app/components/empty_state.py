"""Reusable empty state component for AgentEval Workbench UI."""
from __future__ import annotations

import streamlit as st


def render_empty_state(
    icon: str,
    title: str,
    message: str,
    action_label: str | None = None,
    action_page: str | None = None,
) -> None:
    """Render a centered empty state with an icon, title, message, and optional action.

    Args:
        icon: Material icon string, e.g. ":material/folder_open:"
        title: Short headline for the empty state.
        message: One-sentence guidance explaining what to do next.
        action_label: Button label (e.g. "Go to Generate"). Omit if no action.
        action_page: Navigation key that matches a PAGES entry in app.py (e.g. "Generate").
                     When clicked, sets st.session_state.nav_to_page and reruns.
    """
    with st.container(border=True):
        with st.container(horizontal_alignment="center"):
            st.markdown(f"## {icon}")
            st.markdown(f"**{title}**")
            st.caption(message)
            if action_label and action_page:
                if st.button(action_label, key=f"_empty_state_btn_{action_page}_{title[:8]}"):
                    st.session_state.nav_to_page = action_page
                    st.rerun()
