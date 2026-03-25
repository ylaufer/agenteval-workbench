"""User preference persistence for guided onboarding."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict


class UserPreferences(TypedDict):
    """User preferences structure."""

    first_run_complete: bool
    tutorial_skipped: bool
    show_contextual_help: bool
    demo_completed_at: str | None
    tutorial_progress: int


def get_preferences_path() -> Path:
    """Get path to preferences file."""
    return Path.home() / ".agenteval" / "preferences.json"


def get_default_preferences() -> UserPreferences:
    """Return default preferences (fresh dict each time)."""
    return {
        "first_run_complete": False,
        "tutorial_skipped": False,
        "show_contextual_help": True,
        "demo_completed_at": None,
        "tutorial_progress": -1,
    }


def load_preferences() -> UserPreferences:
    """Load preferences from file, with corruption recovery."""
    path = get_preferences_path()

    if not path.exists():
        return get_default_preferences()

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Validate structure
        defaults = get_default_preferences()
        for key in defaults:
            if key not in data:
                raise ValueError(f"Missing key: {key}")

        return data

    except (json.JSONDecodeError, ValueError, OSError) as e:
        # Corruption detected - return defaults + error info
        return {
            **get_default_preferences(),
            "_corruption_error": str(e),  # Flag for warning banner
        }


def save_preferences(prefs: UserPreferences) -> None:
    """Save preferences to file."""
    path = get_preferences_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    # Remove internal flags before saving
    clean_prefs = {k: v for k, v in prefs.items() if not k.startswith("_")}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean_prefs, f, indent=2)

    # Set restrictive permissions (user read/write only)
    path.chmod(0o600)
