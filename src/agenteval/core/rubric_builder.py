"""Custom rubric builder — create, validate, version, and save evaluation rubrics.

All filesystem access is constrained to the repo root via _safe_resolve_within().
No new runtime dependencies: validation uses jsonschema (already required).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import jsonschema  # type: ignore[import-untyped]

from agenteval.dataset.validator import _get_repo_root, _safe_resolve_within


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_SCALES = ("0-2", "1-5", "0-4")

SCALE_KEYS: dict[str, list[str]] = {
    "0-2": ["0", "1", "2"],
    "1-5": ["1", "2", "3", "4", "5"],
    "0-4": ["0", "1", "2", "3", "4"],
}

_NAME_PATTERN = re.compile(r"^[a-z0-9_]+$")

# Lazy-loaded rubric schema cache
_RUBRIC_SCHEMA: dict[str, Any] | None = None


def _get_rubric_schema(repo_root: Path) -> dict[str, Any]:
    global _RUBRIC_SCHEMA
    if _RUBRIC_SCHEMA is None:
        schema_path = _safe_resolve_within(repo_root, repo_root / "schemas" / "rubric_schema.json")
        _RUBRIC_SCHEMA = json.loads(schema_path.read_text(encoding="utf-8"))
    return _RUBRIC_SCHEMA


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class RubricDimension:
    """In-memory representation of a single scoring dimension."""

    name: str
    scale: Literal["0-2", "1-5", "0-4"]
    description: str
    scoring_guide: dict[str, str]
    title: str = ""
    weight: float = 1.0
    evidence_required: bool = True

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "name": self.name,
            "scale": self.scale,
            "description": self.description,
            "scoring_guide": self.scoring_guide,
        }
        if self.title:
            d["title"] = self.title
        d["weight"] = self.weight
        d["evidence_required"] = self.evidence_required
        return d


@dataclass
class RubricDraft:
    """Full rubric being assembled, held in session state or passed programmatically."""

    name: str
    dimensions: list[RubricDimension] = field(default_factory=list)
    description: str = ""
    template_source: str | None = None

    def to_rubric_dict(self, version: str) -> dict[str, Any]:
        d: dict[str, Any] = {
            "version": version,
            "dimensions": [dim.to_dict() for dim in self.dimensions],
        }
        if self.name:
            d["name"] = self.name
        if self.description:
            d["description"] = self.description
        return d


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_templates(repo_root: Path | None = None) -> list[str]:
    """Return sorted template IDs by scanning rubrics/templates/.

    Returns:
        Sorted list of template IDs (filename stems without .json), e.g.
        ["code_generation", "customer_support", "general_agent", "rag_pipeline"]
    """
    if repo_root is None:
        repo_root = _get_repo_root()
    templates_dir = _safe_resolve_within(repo_root, repo_root / "rubrics" / "templates")
    if not templates_dir.exists():
        return []
    return sorted(p.stem for p in templates_dir.iterdir() if p.suffix == ".json")


def load_template(template_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    """Load a starter template from rubrics/templates/{template_id}.json.

    Args:
        template_id: Template identifier (e.g. "rag_pipeline")
        repo_root: Repo root path. Defaults to auto-detected.

    Returns:
        Dict with name, optional description, and dimensions list.

    Raises:
        FileNotFoundError: If template does not exist.
    """
    if repo_root is None:
        repo_root = _get_repo_root()
    template_path = _safe_resolve_within(
        repo_root, repo_root / "rubrics" / "templates" / f"{template_id}.json"
    )
    if not template_path.exists():
        raise FileNotFoundError(f"Template '{template_id}' not found at {template_path}")
    result: dict[str, Any] = json.loads(template_path.read_text(encoding="utf-8"))
    return result


def validate_rubric(rubric: dict[str, Any], repo_root: Path | None = None) -> tuple[bool, list[str]]:
    """Validate a rubric dict against rubric_schema.json and semantic rules.

    Semantic checks beyond schema:
    - Each dimension name matches ^[a-z0-9_]+$
    - Each dimension scoring_guide contains all keys for its scale
    - At least one dimension present

    Args:
        rubric: Rubric dict with version, dimensions, etc.
        repo_root: Repo root for schema loading. Defaults to auto-detected.

    Returns:
        (is_valid, errors) — errors is empty when valid.
    """
    if repo_root is None:
        repo_root = _get_repo_root()

    errors: list[str] = []

    # JSON schema validation
    try:
        schema = _get_rubric_schema(repo_root)
        jsonschema.validate(instance=rubric, schema=schema)
    except jsonschema.ValidationError as exc:
        errors.append(f"Schema error: {exc.message}")
        return False, errors

    # Semantic checks
    dimensions = rubric.get("dimensions", [])
    if not dimensions:
        errors.append("Rubric must have at least one dimension.")
        return False, errors

    for dim in dimensions:
        name = dim.get("name", "")
        scale = dim.get("scale", "")
        scoring_guide = dim.get("scoring_guide", {})

        if not _NAME_PATTERN.match(name):
            errors.append(
                f"dimension '{name}': name must match ^[a-z0-9_]+$ "
                f"(only lowercase letters, digits, underscores)"
            )

        if scale in SCALE_KEYS:
            required_keys = SCALE_KEYS[scale]
            for k in required_keys:
                if k not in scoring_guide:
                    errors.append(
                        f"dimension '{name}': scoring_guide missing key '{k}' for scale '{scale}'"
                    )

    return len(errors) == 0, errors


def next_version(name: str, repo_root: Path | None = None) -> str:
    """Determine the next version prefix for a given rubric name.

    Scans rubrics/ for files matching v*_{name}.json, takes max numeric prefix,
    returns v{n+1}. Returns "v1" if none exist.

    Args:
        name: Rubric base name (e.g. "rag_pipeline")
        repo_root: Repo root path. Defaults to auto-detected.

    Returns:
        Version string, e.g. "v1" or "v2".
    """
    if repo_root is None:
        repo_root = _get_repo_root()
    rubrics_dir = _safe_resolve_within(repo_root, repo_root / "rubrics")
    if not rubrics_dir.exists():
        return "v1"

    max_n = 0
    pattern = re.compile(rf"^v(\d+)_{re.escape(name)}\.json$")
    for p in rubrics_dir.iterdir():
        m = pattern.match(p.name)
        if m:
            max_n = max(max_n, int(m.group(1)))

    return f"v{max_n + 1}"


def save_rubric(
    name: str,
    rubric: dict[str, Any],
    repo_root: Path | None = None,
) -> Path:
    """Save a rubric dict to rubrics/ with an auto-versioned filename.

    Sets rubric["version"] to "v{N}_{name}" before writing.

    Args:
        name: Rubric base name (e.g. "rag_pipeline"). Must match ^[a-z0-9_]+$.
        rubric: Rubric dict (must pass validate_rubric).
        repo_root: Repo root path. Defaults to auto-detected.

    Returns:
        Path to the saved file (e.g. rubrics/v1_rag_pipeline.json).

    Raises:
        ValueError: If name is empty or contains invalid characters.
        ValueError: If rubric fails validation.
    """
    if repo_root is None:
        repo_root = _get_repo_root()

    if not name or not _NAME_PATTERN.match(name):
        raise ValueError(
            f"Rubric name '{name}' is invalid; must match ^[a-z0-9_]+$"
        )

    is_valid, errors = validate_rubric(rubric, repo_root)
    if not is_valid:
        raise ValueError(f"Rubric validation failed: {'; '.join(errors)}")

    version_prefix = next_version(name, repo_root)
    version_id = f"{version_prefix}_{name}"

    # Mutate a copy so caller's dict isn't modified unexpectedly
    saved = dict(rubric)
    saved["version"] = version_id

    rubrics_dir = _safe_resolve_within(repo_root, repo_root / "rubrics")
    rubrics_dir.mkdir(parents=True, exist_ok=True)

    dest = _safe_resolve_within(repo_root, repo_root / "rubrics" / f"{version_id}.json")
    dest.write_text(json.dumps(saved, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return dest


def list_rubrics(repo_root: Path | None = None) -> list[str]:
    """List all rubric files available in rubrics/ (excludes templates/ subdirectory).

    Args:
        repo_root: Repo root path. Defaults to auto-detected.

    Returns:
        Sorted list of filename stems, e.g. ["v1_agent_general", "v1_rag_pipeline"].
    """
    if repo_root is None:
        repo_root = _get_repo_root()
    rubrics_dir = _safe_resolve_within(repo_root, repo_root / "rubrics")
    if not rubrics_dir.exists():
        return []
    templates_dir = rubrics_dir / "templates"
    return sorted(
        p.stem
        for p in rubrics_dir.iterdir()
        if p.is_file() and p.suffix == ".json" and p.parent != templates_dir
    )
