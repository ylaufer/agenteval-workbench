"""First-run detection and session state initialization."""
from __future__ import annotations

import streamlit as st
from utils.preferences import load_preferences, save_preferences


def initialize_onboarding_state() -> None:
    """Initialize all onboarding-related session state.

    Call this ONCE at the top of streamlit_app.py, before page navigation.
    """
    # Load preferences from file (or defaults if missing)
    if "preferences" not in st.session_state:
        st.session_state.preferences = load_preferences()

    # Session flags (not persisted)
    st.session_state.setdefault("onboarding_modal_shown", False)
    st.session_state.setdefault("demo_in_progress", False)
    st.session_state.setdefault(
        "demo_status",
        {
            "step": "generate",
            "progress": 0.0,
            "message": "",
            "error": None,
        },
    )

    # Tutorial state (T033: session state tracking for tutorial mode)
    st.session_state.setdefault("tutorial_active", False)
    st.session_state.setdefault("tutorial_current_step", 0)  # 0-indexed (0-4 for 5 steps)


def should_show_welcome_modal() -> bool:
    """Check if welcome modal should be displayed this session."""
    prefs = st.session_state.preferences

    # Show if: first run not complete AND modal not shown this session
    return (
        not prefs.get("first_run_complete", False)
        and not st.session_state.onboarding_modal_shown
    )


def mark_first_run_complete(tutorial_skipped: bool = False) -> None:
    """Mark first run as complete and persist to file."""
    st.session_state.preferences["first_run_complete"] = True
    st.session_state.preferences["tutorial_skipped"] = tutorial_skipped
    st.session_state.onboarding_modal_shown = True

    save_preferences(st.session_state.preferences)


def next_tutorial_step() -> None:
    """Advance to next tutorial step (callback for Next button)."""
    from onboarding.content import TUTORIAL_STEPS

    if st.session_state.tutorial_current_step < len(TUTORIAL_STEPS) - 1:
        st.session_state.tutorial_current_step += 1


def previous_tutorial_step() -> None:
    """Go back to previous tutorial step (callback for Back button)."""
    if st.session_state.tutorial_current_step > 0:
        st.session_state.tutorial_current_step -= 1


def skip_tutorial() -> None:
    """Exit tutorial mode and save preference (callback for Skip button)."""
    st.session_state.tutorial_active = False
    st.session_state.tutorial_current_step = 0
    st.session_state.tutorial_toggle = False  # Uncheck the checkbox
    st.session_state.preferences["tutorial_skipped"] = True
    save_preferences(st.session_state.preferences)
