"""Collapsible help section component."""
from __future__ import annotations

import streamlit as st


def show_help_section(title: str, content: str, expanded: bool | None = None) -> None:
    """Display a collapsible help section with markdown content.

    Args:
        title: Section title (e.g., "How this works")
        content: Markdown content to display
        expanded: If None, uses user preference; if True/False, forces state
    """
    # Check user preference - if disabled, don't render at all
    if expanded is None:
        prefs = st.session_state.get("preferences", {})
        show_help = prefs.get("show_contextual_help", True)
        if not show_help:
            return  # Don't render help section when preference is disabled
        expanded = True  # If showing, always start expanded

    with st.expander(f"ℹ️ {title}", expanded=expanded):
        st.markdown(content)
