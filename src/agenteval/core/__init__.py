from __future__ import annotations

from . import calibration, loader, report, runner, runs, service, tagger, types  # noqa: F401

"""
Core evaluation engine for AgentEval.

This package provides:
- Typed representations for rubrics and case evaluations
- Helpers for loading/validating traces and rubrics
- A CLI runner that generates structured JSON + Markdown evaluation templates
- Failure pattern classification via rule-based tagging
- Inter-reviewer calibration and agreement metrics
"""

__all__ = ["calibration", "loader", "report",
           "runner", "runs", "service", "tagger", "types"]
