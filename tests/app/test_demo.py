"""Unit tests for demo module."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import after setting up path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))


def test_run_demo_workflow_success(monkeypatch):
    """Test successful demo workflow execution."""
    mock_st = MagicMock()
    mock_st.session_state = {
        "demo_status": {},
        "demo_in_progress": True,
        "preferences": {},
    }
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
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
    
    # Mock st.status
    mock_status = MagicMock()
    mock_st.status.return_value.__enter__ = MagicMock(return_value=mock_status)
    mock_st.status.return_value.__exit__ = MagicMock(return_value=False)
    
    from onboarding.demo import run_demo_workflow
    
    run_demo_workflow()
    
    # Verify all stages called
    mock_generate.assert_called_once()
    mock_validate.assert_called_once()
    mock_eval.assert_called_once()
    mock_report.assert_called_once()
    
    # Verify status updated to complete
    assert mock_st.session_state["demo_status"]["step"] == "complete"
    assert mock_st.session_state["demo_in_progress"] is False
    
    # Verify completion saved
    mock_save_prefs.assert_called_once()


def test_run_demo_workflow_validation_failure(monkeypatch):
    """Test demo workflow handles validation failure."""
    mock_st = MagicMock()
    mock_st.session_state = {
        "demo_status": {},
        "demo_in_progress": True,
    }
    monkeypatch.setattr("streamlit.session_state", mock_st.session_state)
    
    # Mock service layer - validation fails
    mock_generate = MagicMock()
    mock_validate = MagicMock(return_value=MagicMock(
        ok=False,
        issues=[MagicMock(message="Test error")]
    ))
    
    monkeypatch.setattr("onboarding.demo.generate_case", mock_generate)
    monkeypatch.setattr("onboarding.demo.validate_dataset", mock_validate)
    
    # Mock st.status
    mock_status = MagicMock()
    mock_st.status.return_value.__enter__ = MagicMock(return_value=mock_status)
    mock_st.status.return_value.__exit__ = MagicMock(return_value=False)
    mock_st.error = MagicMock()
    mock_st.button = MagicMock(return_value=False)
    
    from onboarding.demo import run_demo_workflow
    
    # Should raise and be caught
    run_demo_workflow()
    
    # Verify error captured
    assert mock_st.session_state["demo_status"].get("error") is not None
    assert mock_st.session_state["demo_in_progress"] is False


def test_show_demo_completion_message(monkeypatch):
    """Test demo completion message display."""
    mock_st = MagicMock()
    mock_st.success = MagicMock()
    mock_st.markdown = MagicMock()
    mock_st.button = MagicMock(return_value=False)
    
    from onboarding.demo import show_demo_completion_message
    
    show_demo_completion_message()
    
    # Verify success message shown
    mock_st.success.assert_called_once()
    
    # Verify button rendered
    mock_st.button.assert_called_once()
