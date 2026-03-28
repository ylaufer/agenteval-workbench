"""Unit tests for demo module."""
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

    def __getitem__(self, key: str) -> object:
        return getattr(self, key)

    def __setitem__(self, key: str, value: object) -> None:
        setattr(self, key, value)

    def get(self, key: str, default: object = None) -> object:
        return getattr(self, key, default)


def test_run_demo_workflow_success(monkeypatch):
    """Test successful demo workflow execution."""
    fake_state = _FakeSessionState(
        demo_status={},
        demo_in_progress=True,
        preferences={},
    )
    monkeypatch.setattr("streamlit.session_state", fake_state)

    # Mock service layer functions
    mock_generate = MagicMock()
    mock_validate = MagicMock(return_value=MagicMock(ok=True))
    mock_eval = MagicMock()
    mock_report = MagicMock()
    mock_save_prefs = MagicMock()

    monkeypatch.setattr("onboarding.demo.generate_case", mock_generate)
    monkeypatch.setattr("onboarding.demo.validate_dataset", mock_validate)
    monkeypatch.setattr("onboarding.demo.run_evaluation", mock_eval)
    monkeypatch.setattr("onboarding.demo.generate_summary_report", mock_report)
    monkeypatch.setattr("onboarding.demo.save_preferences", mock_save_prefs)

    # Mock st.status as a context manager returning a usable status object
    mock_status = MagicMock()
    mock_st_status = MagicMock()
    mock_st_status.return_value.__enter__ = MagicMock(return_value=mock_status)
    mock_st_status.return_value.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr("streamlit.status", mock_st_status)

    from onboarding.demo import run_demo_workflow

    run_demo_workflow()

    # Verify all stages called
    mock_generate.assert_called_once()
    mock_validate.assert_called_once()
    mock_eval.assert_called_once()
    mock_report.assert_called_once()

    # Verify status updated to complete
    assert fake_state.demo_status["step"] == "complete"
    assert fake_state.demo_in_progress is False

    # Verify completion saved
    mock_save_prefs.assert_called_once()


def test_run_demo_workflow_validation_failure(monkeypatch):
    """Test demo workflow handles validation failure."""
    fake_state = _FakeSessionState(
        demo_status={},
        demo_in_progress=True,
    )
    monkeypatch.setattr("streamlit.session_state", fake_state)

    # Mock service layer — validation fails
    mock_generate = MagicMock()
    mock_validate = MagicMock(return_value=MagicMock(
        ok=False,
        issues=[MagicMock(message="Test error")],
    ))

    monkeypatch.setattr("onboarding.demo.generate_case", mock_generate)
    monkeypatch.setattr("onboarding.demo.validate_dataset", mock_validate)

    mock_status = MagicMock()
    mock_st_status = MagicMock()
    mock_st_status.return_value.__enter__ = MagicMock(return_value=mock_status)
    mock_st_status.return_value.__exit__ = MagicMock(return_value=False)
    monkeypatch.setattr("streamlit.status", mock_st_status)
    monkeypatch.setattr("streamlit.error", MagicMock())
    monkeypatch.setattr("streamlit.button", MagicMock(return_value=False))

    from onboarding.demo import run_demo_workflow

    run_demo_workflow()

    # Verify error captured
    assert fake_state.demo_status.get("error") is not None
    assert fake_state.demo_in_progress is False


def test_show_demo_completion_message(monkeypatch):
    """Test demo completion message display."""
    mock_success = MagicMock()
    mock_markdown = MagicMock()
    mock_button = MagicMock(return_value=False)

    monkeypatch.setattr("streamlit.success", mock_success)
    monkeypatch.setattr("streamlit.markdown", mock_markdown)
    monkeypatch.setattr("streamlit.button", mock_button)

    from onboarding.demo import show_demo_completion_message

    show_demo_completion_message()

    # Verify success message shown
    mock_success.assert_called_once()

    # Verify button rendered
    mock_button.assert_called_once()
