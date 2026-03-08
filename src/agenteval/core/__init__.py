from __future__ import annotations

"""
Core evaluation engine for AgentEval.

This package provides:
- Typed representations for rubrics and case evaluations
- Helpers for loading/validating traces and rubrics
- A CLI runner that generates structured JSON + Markdown evaluation templates
"""

from . import loader, runner, types  # noqa: F401

__all__ = ["loader", "runner", "types"]

