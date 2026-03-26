"""AgentEval Workbench — Streamlit UI entry point."""
from __future__ import annotations

import streamlit as st

# Import onboarding utilities
from components.welcome_modal import show_welcome_modal
from onboarding.demo import run_demo_workflow, show_demo_completion_message
from onboarding.first_run import (
    initialize_onboarding_state,
    should_show_welcome_modal,
)
from utils.preferences import save_preferences

st.set_page_config(page_title="AgentEval Workbench", layout="wide")

# T050: Add visible focus indicators for accessibility
st.markdown(
    """
    <style>
    /* Enhanced focus indicators for keyboard navigation */
    button:focus-visible,
    [data-testid="stExpander"] summary:focus-visible,
    [data-testid="baseButton-secondary"]:focus-visible,
    input:focus-visible,
    textarea:focus-visible {
        outline: 2px solid #1f77b4 !important;
        outline-offset: 2px !important;
        box-shadow: 0 0 0 3px rgba(31, 119, 180, 0.2) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize onboarding state (MUST be before navigation)
initialize_onboarding_state()

# Check for preference corruption and show warning
prefs = st.session_state.preferences
if "_corruption_error" in prefs:
    st.warning(
        f"⚠️ **Preferences file corrupted**: {prefs['_corruption_error']}. "
        "Reset to defaults. Click below for details.",
        icon="⚠️",
    )
    with st.expander("Show Details"):
        st.code(prefs["_corruption_error"])

# Show welcome modal if needed (before navigation)
if should_show_welcome_modal():
    show_welcome_modal()
    # T048: Mark modal as shown so Esc dismissal doesn't cause it to reappear
    st.session_state.onboarding_modal_shown = True

PAGES = {
    "Generate": "page_generate",
    "Ingest": "page_ingest",
    "Evaluate": "page_evaluate",
    "Inspect": "page_inspect",
    "Report": "page_report",
}

st.sidebar.title("AgentEval Workbench")

# Auto-navigate during tutorial mode (T034-T038)
if st.session_state.get("tutorial_active"):
    from onboarding.content import TUTORIAL_STEPS

    current_step = st.session_state.tutorial_current_step
    step_info = TUTORIAL_STEPS[current_step]
    tutorial_page = step_info.get("page", "home")

    # Map tutorial page names to actual page keys
    page_mapping = {
        "home": "Generate",  # Home tutorial step shows on Generate page
        "generate": "Generate",
        "evaluate": "Evaluate",
        "inspect": "Inspect",
        "report": "Report",
    }

    # Auto-select page based on tutorial step
    selection = page_mapping.get(tutorial_page, "Generate")
    st.sidebar.radio("Navigation", list(PAGES.keys()), index=list(PAGES.keys()).index(selection), disabled=True)
else:
    selection = st.sidebar.radio("Navigation", list(PAGES.keys()))

# Settings section in sidebar
st.sidebar.divider()
st.sidebar.subheader("⚙️ Settings")

# Initialize widget state from preferences (before creating widget)
if "help_toggle" not in st.session_state:
    st.session_state.help_toggle = st.session_state.preferences.get("show_contextual_help", True)

def on_help_toggle_change():
    """Sync widget state to preferences and save."""
    st.session_state.preferences["show_contextual_help"] = st.session_state.help_toggle
    save_preferences(st.session_state.preferences)

# Help visibility toggle
st.sidebar.checkbox(
    "Show contextual help",
    key="help_toggle",
    on_change=on_help_toggle_change,
    help="Show expandable help sections on each page",
)

# Tutorial mode toggle (T040)
if "tutorial_toggle" not in st.session_state:
    st.session_state.tutorial_toggle = st.session_state.get("tutorial_active", False)

def on_tutorial_toggle_change():
    """Enable/disable tutorial mode (callback for checkbox)."""
    st.session_state.tutorial_active = st.session_state.tutorial_toggle
    if st.session_state.tutorial_active:
        st.session_state.tutorial_current_step = 0  # Reset to first step

st.sidebar.checkbox(
    "Tutorial mode",
    key="tutorial_toggle",
    on_change=on_tutorial_toggle_change,
    help="Step-by-step walkthrough of the app",
)

# Quick Reference section (T045)
from components.quick_reference import show_quick_reference
show_quick_reference()

# Handle demo flow (runs before page content)
if st.session_state.get("demo_in_progress"):
    run_demo_workflow()
elif st.session_state.demo_status.get("step") == "complete":
    show_demo_completion_message()

# Tutorial navigation UI (T032, T041)
if st.session_state.get("tutorial_active"):
    from onboarding.content import TUTORIAL_STEPS
    from onboarding.first_run import next_tutorial_step, previous_tutorial_step, skip_tutorial

    current_step = st.session_state.tutorial_current_step
    total_steps = len(TUTORIAL_STEPS)
    step_info = TUTORIAL_STEPS[current_step]

    # Progress indicator
    st.progress((current_step + 1) / total_steps)
    st.caption(f"Step {current_step + 1} of {total_steps}")

    # Tutorial content box
    with st.container(border=True):
        st.subheader(step_info["title"], anchor=False)
        st.write(step_info["description"])

    # Navigation buttons
    with st.container(horizontal=True):
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            st.button(
                "Back",
                icon=":material/arrow_back:",
                on_click=previous_tutorial_step,
                disabled=(current_step == 0),
                use_container_width=True,
            )

        with col2:
            st.button(
                "Skip tutorial",
                on_click=skip_tutorial,
                use_container_width=True,
            )

        with col3:
            if current_step < total_steps - 1:
                st.button(
                    "Next",
                    icon=":material/arrow_forward:",
                    on_click=next_tutorial_step,
                    type="primary",
                    use_container_width=True,
                )
            else:
                # Last step - show "Finish" button
                st.button(
                    "Finish",
                    icon=":material/check_circle:",
                    on_click=skip_tutorial,  # Same as skip - exits tutorial
                    type="primary",
                    use_container_width=True,
                )

    st.divider()

if selection == "Generate":
    from page_generate import render
elif selection == "Ingest":
    from page_ingest import render
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
