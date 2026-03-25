"""Unit tests for first_run module."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Import after setting up path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))


def test_initialize_onboarding_state(monkeypatch):
    """Test that onboarding state is initialized correctly."""
    # Mock streamlit
    mock_st = MagicMock()
    mock_st.session_state = {}
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    # Mock preferences loader
    mock_prefs = {
        "first_run_complete": False,
        "tutorial_skipped": False,
        "show_contextual_help": True,
        "demo_completed_at": None,
        "tutorial_progress": -1,
    }
    monkeypatch.setattr(
        "onboarding.first_run.load_preferences",
        lambda: mock_prefs
    )
    
    from onboarding.first_run import initialize_onboarding_state
    
    initialize_onboarding_state()
    
    # Check preferences loaded
    assert mock_st.session_state["preferences"] == mock_prefs
    
    # Check session flags initialized
    assert mock_st.session_state["onboarding_modal_shown"] is False
    assert mock_st.session_state["demo_in_progress"] is False
    assert "demo_status" in mock_st.session_state
    assert mock_st.session_state["tutorial_active"] is False
    assert mock_st.session_state["tutorial_current_step"] == 0


def test_should_show_welcome_modal_first_run(monkeypatch):
    """Test modal shows on first run."""
    mock_st = MagicMock()
    mock_st.session_state = {
        "preferences": {"first_run_complete": False},
        "onboarding_modal_shown": False,
    }
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    from onboarding.first_run import should_show_welcome_modal
    
    assert should_show_welcome_modal() is True


def test_should_show_welcome_modal_already_complete(monkeypatch):
    """Test modal does not show if first run is complete."""
    mock_st = MagicMock()
    mock_st.session_state = {
        "preferences": {"first_run_complete": True},
        "onboarding_modal_shown": False,
    }
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    from onboarding.first_run import should_show_welcome_modal
    
    assert should_show_welcome_modal() is False


def test_should_show_welcome_modal_already_shown_this_session(monkeypatch):
    """Test modal does not show twice in same session."""
    mock_st = MagicMock()
    mock_st.session_state = {
        "preferences": {"first_run_complete": False},
        "onboarding_modal_shown": True,  # Already shown
    }
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    from onboarding.first_run import should_show_welcome_modal
    
    assert should_show_welcome_modal() is False


def test_mark_first_run_complete(monkeypatch):
    """Test marking first run as complete."""
    mock_st = MagicMock()
    mock_st.session_state = {
        "preferences": {},
    }
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    mock_save = MagicMock()
    monkeypatch.setattr("onboarding.first_run.save_preferences", mock_save)
    
    from onboarding.first_run import mark_first_run_complete
    
    mark_first_run_complete(tutorial_skipped=True)
    
    # Check state updated
    assert mock_st.session_state["preferences"]["first_run_complete"] is True
    assert mock_st.session_state["preferences"]["tutorial_skipped"] is True
    assert mock_st.session_state["onboarding_modal_shown"] is True
    
    # Check preferences saved
    mock_save.assert_called_once()


def test_next_tutorial_step(monkeypatch):
    """Test advancing tutorial step."""
    mock_st = MagicMock()
    mock_st.session_state = {
        "tutorial_current_step": 0,
    }
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    # Mock TUTORIAL_STEPS
    mock_steps = [{"step_number": i} for i in range(6)]
    monkeypatch.setattr("onboarding.first_run.TUTORIAL_STEPS", mock_steps)
    
    from onboarding.first_run import next_tutorial_step
    
    next_tutorial_step()
    
    assert mock_st.session_state["tutorial_current_step"] == 1


def test_previous_tutorial_step(monkeypatch):
    """Test going back a tutorial step."""
    mock_st = MagicMock()
    mock_st.session_state = {
        "tutorial_current_step": 2,
    }
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    from onboarding.first_run import previous_tutorial_step
    
    previous_tutorial_step()
    
    assert mock_st.session_state["tutorial_current_step"] == 1


def test_skip_tutorial(monkeypatch):
    """Test skipping tutorial."""
    mock_st = MagicMock()
    mock_st.session_state = {
        "tutorial_active": True,
        "tutorial_current_step": 3,
        "tutorial_toggle": True,
        "preferences": {},
    }
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    mock_save = MagicMock()
    monkeypatch.setattr("onboarding.first_run.save_preferences", mock_save)
    
    from onboarding.first_run import skip_tutorial
    
    skip_tutorial()
    
    # Check tutorial exited
    assert mock_st.session_state["tutorial_active"] is False
    assert mock_st.session_state["tutorial_current_step"] == 0
    assert mock_st.session_state["tutorial_toggle"] is False
    assert mock_st.session_state["preferences"]["tutorial_skipped"] is True
    
    # Check preferences saved
    mock_save.assert_called_once()
