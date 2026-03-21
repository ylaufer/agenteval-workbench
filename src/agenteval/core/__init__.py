from __future__ import annotations

from . import loader, report, runner, types  # noqa: F401

"""
Core evaluation engine for AgentEval.

This package provides:
- Typed representations for rubrics and case evaluations
- Helpers for loading/validating traces and rubrics
- A CLI runner that generates structured JSON + Markdown evaluation templates
"""

__all__ = ["loader", "report", "runner", "types"]

