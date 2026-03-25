"""Unit tests for preferences module."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

# Import after setting up path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "app"))

from utils.preferences import (
    get_default_preferences,
    get_preferences_path,
    load_preferences,
    save_preferences,
)


def test_get_default_preferences():
    """Test default preferences structure."""
    defaults = get_default_preferences()
    
    assert defaults["first_run_complete"] is False
    assert defaults["tutorial_skipped"] is False
    assert defaults["show_contextual_help"] is True
    assert defaults["demo_completed_at"] is None
    assert defaults["tutorial_progress"] == -1


def test_get_preferences_path():
    """Test preferences path generation."""
    path = get_preferences_path()
    
    assert path.name == "preferences.json"
    assert ".agenteval" in str(path)


def test_load_preferences_no_file():
    """Test loading when no preferences file exists."""
    # Mock non-existent path
    prefs = load_preferences()
    
    # Should return defaults
    assert prefs == get_default_preferences()


def test_save_and_load_preferences(tmp_path, monkeypatch):
    """Test saving and loading preferences roundtrip."""
    # Mock preferences path
    pref_file = tmp_path / "preferences.json"
    monkeypatch.setattr(
        "utils.preferences.get_preferences_path",
        lambda: pref_file
    )
    
    # Create custom preferences
    prefs = {
        "first_run_complete": True,
        "tutorial_skipped": True,
        "show_contextual_help": False,
        "demo_completed_at": "2024-01-01T00:00:00Z",
        "tutorial_progress": 3,
    }
    
    # Save
    save_preferences(prefs)
    
    # Verify file exists
    assert pref_file.exists()
    
    # Load
    loaded = load_preferences()
    
    # Verify roundtrip (excluding internal flags)
    assert loaded["first_run_complete"] is True
    assert loaded["tutorial_skipped"] is True
    assert loaded["show_contextual_help"] is False


def test_save_preferences_removes_internal_flags(tmp_path, monkeypatch):
    """Test that internal flags starting with _ are not saved."""
    pref_file = tmp_path / "preferences.json"
    monkeypatch.setattr(
        "utils.preferences.get_preferences_path",
        lambda: pref_file
    )
    
    prefs = get_default_preferences()
    prefs["_corruption_error"] = "Some error"  # Internal flag
    
    save_preferences(prefs)
    
    # Read raw file
    saved_data = json.loads(pref_file.read_text())
    
    # Internal flag should not be saved
    assert "_corruption_error" not in saved_data


def test_load_preferences_corruption_recovery(tmp_path, monkeypatch):
    """Test that corrupted preferences return defaults with error flag."""
    pref_file = tmp_path / "preferences.json"
    monkeypatch.setattr(
        "utils.preferences.get_preferences_path",
        lambda: pref_file
    )
    
    # Write invalid JSON
    pref_file.write_text("{invalid json")
    
    # Load should return defaults with error
    loaded = load_preferences()
    
    assert "_corruption_error" in loaded
    assert "first_run_complete" in loaded  # Still has defaults


def test_load_preferences_missing_key(tmp_path, monkeypatch):
    """Test that preferences with missing keys trigger recovery."""
    pref_file = tmp_path / "preferences.json"
    monkeypatch.setattr(
        "utils.preferences.get_preferences_path",
        lambda: pref_file
    )
    
    # Write valid JSON but missing required key
    incomplete = {
        "first_run_complete": True,
        # Missing other required keys
    }
    pref_file.write_text(json.dumps(incomplete))
    
    # Load should return defaults with error
    loaded = load_preferences()
    
    assert "_corruption_error" in loaded
