from __future__ import annotations

from typing_extensions import NotRequired, TypedDict


class Security(TypedDict, total=False):
    redact_patterns: list[str]


class Dimension(TypedDict):
    name: str
    title: NotRequired[str]
    scale: str  # "0-2", "1-5", "0-4"
    weight: NotRequired[float]
    description: str
    scoring_guide: dict[str, str]
    evidence_required: NotRequired[bool]


class Rubric(TypedDict):
    version: str
    name: NotRequired[str]
    security: NotRequired[Security]
    dimensions: list[Dimension]