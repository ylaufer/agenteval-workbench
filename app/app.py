"""AgentEval Workbench — Streamlit UI entry point."""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="AgentEval Workbench", layout="wide")

PAGES = {
    "Generate": "page_generate",
    "Evaluate": "page_evaluate",
    "Inspect": "page_inspect",
    "Report": "page_report",
}

st.sidebar.title("AgentEval Workbench")
selection = st.sidebar.radio("Navigation", list(PAGES.keys()))

if selection == "Generate":
    from page_generate import render
elif selection == "Evaluate":
    from page_evaluate import render
elif selection == "Inspect":
    from page_inspect import render
elif selection == "Report":
    from page_report import render
else:
    st.error(f"Unknown page: {selection}")
    st.stop()

render()
