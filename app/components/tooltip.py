"""Tooltip helper utilities."""
from __future__ import annotations


def get_tooltip(tooltip_dict: dict[str, str], key: str) -> str | None:
    """Get tooltip text from a dictionary, returning None if not found.

    Args:
        tooltip_dict: Dictionary mapping keys to tooltip text
        key: The key to look up

    Returns:
        Tooltip text, or None if key not found
    """
    return tooltip_dict.get(key)
