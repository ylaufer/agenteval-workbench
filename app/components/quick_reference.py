"""Quick reference component for sidebar."""
from __future__ import annotations

from pathlib import Path

import streamlit as st


def show_quick_reference() -> None:
    """Display quick reference sections in sidebar.
    
    Shows failure taxonomy and rubric dimensions in collapsible expanders.
    Loads content from markdown files in docs/.
    """
    st.sidebar.divider()
    st.sidebar.subheader(":material/book: Quick Reference")
    
    # Get paths to reference files
    repo_root = Path(__file__).parent.parent.parent
    taxonomy_path = repo_root / "docs" / "quick_reference_taxonomy.md"
    rubric_path = repo_root / "docs" / "quick_reference_rubric.md"
    
    # Failure Taxonomy section
    if taxonomy_path.exists():
        with st.sidebar.expander("Failure Taxonomy (12 categories)", icon=":material/error:"):
            content = taxonomy_path.read_text(encoding="utf-8")
            st.markdown(content)
    else:
        st.sidebar.caption(":gray[Taxonomy reference not available]")
    
    # Rubric Dimensions section
    if rubric_path.exists():
        with st.sidebar.expander("Rubric Dimensions (6 dimensions)", icon=":material/checklist:"):
            content = rubric_path.read_text(encoding="utf-8")
            st.markdown(content)
    else:
        st.sidebar.caption(":gray[Rubric reference not available]")
