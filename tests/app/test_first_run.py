"""Unit tests for first_run module."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))


class _FakeSessionState:
    """Supports both attribute-style and dict-style access, matching Streamlit's SessionState."""

    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)

    def __setitem__(self, key: str, value: object) -> None:
        setattr(self, key, value)

    def get(self, key: str, default: object = None) -> object:
        return getattr(self, key, default)

    def setdefault(self, key: str, default: object = None) -> object:
        if not hasattr(self, key):
            setattr(self, key, default)
        return getattr(self, key)


def test_initialize_onboarding_state(monkeypatch):
    """Test that onboarding state is initialized correctly."""
    fake_state = _FakeSessionState()
    monkeypatch.setattr("streamlit.session_state", fake_state)

    mock_prefs = {
        "first_run_complete": False,
        "tutorial_skipped": False,
        "show_contextual_help": True,
        "demo_completed_at": None,
        "tutorial_progress": -1,
    }
    monkeypatch.setattr("onboarding.first_run.load_preferences", lambda: mock_prefs)

    from onboarding.first_run import initialize_onboarding_state

    initialize_onboarding_state()

    # Check preferences loaded
    assert fake_state["preferences"] == mock_prefs

    # Check session flags initialized
    assert fake_state["onboarding_modal_shown"] is False
    assert fake_state["demo_in_progress"] is False
    assert "demo_status" in fake_state
    assert fake_state["tutorial_active"] is False
    assert fake_state["tutorial_current_step"] == 0


def test_should_show_welcome_modal_first_run(monkeypatch):
    """Test modal shows on first run."""
    fake_state = _FakeSessionState(
        preferences={"first_run_complete": False},
        onboarding_modal_shown=False,
    )
    monkeypatch.setattr("streamlit.session_state", fake_state)

    from onboarding.first_run import should_show_welcome_modal

    assert should_show_welcome_modal() is True


def test_should_show_welcome_modal_already_complete(monkeypatch):
    """Test modal does not show if first run is complete."""
    fake_state = _FakeSessionState(
        preferences={"first_run_complete": True},
        onboarding_modal_shown=False,
    )
    monkeypatch.setattr("streamlit.session_state", fake_state)

    from onboarding.first_run import should_show_welcome_modal

    assert should_show_welcome_modal() is False


def test_should_show_welcome_modal_already_shown_this_session(monkeypatch):
    """Test modal does not show twice in same session."""
    fake_state = _FakeSessionState(
        preferences={"first_run_complete": False},
        onboarding_modal_shown=True,
    )
    monkeypatch.setattr("streamlit.session_state", fake_state)

    from onboarding.first_run import should_show_welcome_modal

    assert should_show_welcome_modal() is False


def test_mark_first_run_complete(monkeypatch):
    """Test marking first run as complete."""
    fake_state = _FakeSessionState(preferences={})
    monkeypatch.setattr("streamlit.session_state", fake_state)

    mock_save = MagicMock()
    monkeypatch.setattr("onboarding.first_run.save_preferences", mock_save)

    from onboarding.first_run import mark_first_run_complete

    mark_first_run_complete(tutorial_skipped=True)

    assert fake_state["preferences"]["first_run_complete"] is True
    assert fake_state["preferences"]["tutorial_skipped"] is True
    assert fake_state["onboarding_modal_shown"] is True

    mock_save.assert_called_once()


def test_next_tutorial_step(monkeypatch):
    """Test advancing tutorial step."""
    fake_state = _FakeSessionState(tutorial_current_step=0)
    monkeypatch.setattr("streamlit.session_state", fake_state)

    mock_steps = [{"step_number": i} for i in range(6)]
    monkeypatch.setattr("onboarding.content.TUTORIAL_STEPS", mock_steps)

    from onboarding.first_run import next_tutorial_step

    next_tutorial_step()

    assert fake_state["tutorial_current_step"] == 1


def test_previous_tutorial_step(monkeypatch):
    """Test going back a tutorial step."""
    fake_state = _FakeSessionState(tutorial_current_step=2)
    monkeypatch.setattr("streamlit.session_state", fake_state)

    from onboarding.first_run import previous_tutorial_step

    previous_tutorial_step()

    assert fake_state["tutorial_current_step"] == 1


def test_skip_tutorial(monkeypatch):
    """Test skipping tutorial."""
    fake_state = _FakeSessionState(
        tutorial_active=True,
        tutorial_current_step=3,
        tutorial_toggle=True,
        preferences={},
    )
    monkeypatch.setattr("streamlit.session_state", fake_state)

    mock_save = MagicMock()
    monkeypatch.setattr("onboarding.first_run.save_preferences", mock_save)

    from onboarding.first_run import skip_tutorial

    skip_tutorial()

    assert fake_state["tutorial_active"] is False
    assert fake_state["tutorial_current_step"] == 0
    assert fake_state["tutorial_toggle"] is False
    assert fake_state["preferences"]["tutorial_skipped"] is True

    mock_save.assert_called_once()
