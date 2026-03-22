from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import jsonschema


# ----------------------------
# Security-first validation config
# ----------------------------

DEFAULT_SECRET_PATTERNS: list[re.Pattern] = [
    re.compile(r"sk-[A-Za-z0-9]{10,}"),  # common API key-like pattern
    re.compile(r"(?i)authorization:\s*bearer\s+[a-z0-9\-._~+/]+=*"),
    re.compile(r"(?i)\bbearer\s+[a-z0-9\-._~+/]+=*"),
    # Match api_key/token only when value looks like a real secret (length + charset)
    re.compile(r"(?i)\bapi[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}['\"]?"),
    re.compile(r"(?i)\btoken\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{20,}['\"]?"),
]

URL_PATTERN = re.compile(r"https?://", re.IGNORECASE)

# Conservative absolute path detection inside content (POSIX or Windows drive paths).
# Uses \A (start of string) or whitespace/quote/bracket boundary.
# Examples: "/Users/..." or "C:\Users\..."
ABSOLUTE_PATH_IN_TEXT_PATTERN = re.compile(r"(\A|[\s\"'(\[])(/|[A-Za-z]:\\)")

# Path traversal attempts in text (blocks both ../ and ..\)
PATH_TRAVERSAL_PATTERN = re.compile(r"\.\.[/\\]")

REQUIRED_CASE_FILES = ("prompt.txt", "trace.json", "expected_outcome.md")

REQUIRED_HEADER_FIELDS = (
    "Case ID",
    "Primary Failure",
    "Secondary Failures",
    "Severity",
    "case_version",
)


@dataclass(frozen=True)
class ValidationIssue:
    case_id: str
    file_path: str
    message: str
    severity: str = "error"


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    issues: tuple[ValidationIssue, ...]


def _find_repo_root(start: Path) -> Path:
    """
    Find repo root by looking for marker files.
    Markers: pyproject.toml (preferred) or .git directory.
    Searches upward from `start` up to a fixed depth.
    """
    markers = ("pyproject.toml", ".git")
    cur = start.resolve()
    for _ in range(12):
        if any((cur / m).exists() for m in markers):
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    raise RuntimeError("Repo root not found (expected pyproject.toml or .git).")


def _get_repo_root() -> Path:
    """
    Repo root resolution priority:
    1) AGENTEVAL_REPO_ROOT (if set)
    2) Marker search from current working directory
    """
    env_root = os.environ.get("AGENTEVAL_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return _find_repo_root(Path.cwd())


def _safe_resolve_within(root: Path, target: Path) -> Path:
    """
    Ensure target is within root after resolving symlinks.
    Prevents escaping via ../ or symlinks.
    """
    root_resolved = root.resolve()
    target_resolved = target.resolve()

    try:
        target_resolved.relative_to(root_resolved)
    except ValueError as e:
        raise ValueError(f"Path escapes repo root: {target}") from e

    return target_resolved


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def _load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _scan_text_for_security_violations(text: str) -> list[str]:
    violations: list[str] = []

    for pat in DEFAULT_SECRET_PATTERNS:
        if pat.search(text):
            violations.append(f"Secret-like pattern detected: {pat.pattern}")

    if URL_PATTERN.search(text):
        violations.append("External URL detected (http/https)")

    if ABSOLUTE_PATH_IN_TEXT_PATTERN.search(text):
        violations.append("Absolute path detected in content")

    if PATH_TRAVERSAL_PATTERN.search(text):
        violations.append("Path traversal pattern detected ('../' or '..\\')")

    return violations


def _validate_case_structure(case_dir: Path) -> list[str]:
    errors: list[str] = []
    for fname in REQUIRED_CASE_FILES:
        fpath = case_dir / fname
        if not fpath.exists():
            errors.append(f"Missing required file: {fname}")
        elif not fpath.is_file():
            errors.append(f"Expected a file but found non-file: {fname}")
    return errors


def _validate_trace_against_schema(trace_path: Path, schema_path: Path) -> list[str]:
    errors: list[str] = []

    try:
        schema = _load_json(schema_path)
    except Exception as e:
        return [f"Failed to load schema JSON: {e}"]

    try:
        trace = _load_json(trace_path)
    except Exception as e:
        return [f"Failed to load trace JSON: {e}"]

    try:
        jsonschema.validate(instance=trace, schema=schema)
    except jsonschema.ValidationError as e:
        errors.append(f"Schema validation error: {e.message}")
    except Exception as e:
        errors.append(f"Unexpected schema validation error: {e}")

    return errors


def _parse_expected_outcome_header(path: Path) -> dict[str, str]:
    """Parse YAML front matter from expected_outcome.md and return a dict of header fields."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    header: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        header[key.strip()] = value.strip()

    return header


def _validate_header_fields(
    case_id: str, header: dict[str, str], outcome_path: Path
) -> list[ValidationIssue]:
    """Check for the 5 required header fields and return issues for missing ones."""
    issues: list[ValidationIssue] = []
    for field_name in REQUIRED_HEADER_FIELDS:
        if field_name not in header:
            issues.append(
                ValidationIssue(
                    case_id=case_id,
                    file_path=str(outcome_path),
                    message=f"expected_outcome.md missing required header field: {field_name}",
                    severity="error",
                )
            )
    return issues


def _check_version_bump(
    case_id: str,
    case_dir: Path,
    header: dict[str, str],
    repo_root: Path,
) -> list[ValidationIssue]:
    """Check if trace.json or expected_outcome.md changed without a case_version bump.

    Uses git diff to detect changes. Skips silently if git is unavailable or
    the repo has no commits.
    """
    issues: list[ValidationIssue] = []
    case_version = header.get("case_version")
    if not case_version:
        return issues

    files_to_check = ["trace.json", "expected_outcome.md"]

    for fname in files_to_check:
        fpath = case_dir / fname
        if not fpath.exists():
            continue

        try:
            result = subprocess.run(
                ["git", "diff", "HEAD", "--", str(fpath)],
                capture_output=True,
                text=True,
                cwd=str(repo_root),
                timeout=10,
            )
            if result.returncode != 0:
                continue

            if result.stdout.strip():
                # File has changes — check if version was bumped
                # Compare current case_version with HEAD version
                old_result = subprocess.run(
                    ["git", "show", f"HEAD:{fpath.relative_to(repo_root).as_posix()}"],
                    capture_output=True,
                    text=True,
                    cwd=str(repo_root),
                    timeout=10,
                )
                if old_result.returncode != 0:
                    continue

                # Parse old header to get old case_version
                old_lines = old_result.stdout.splitlines()
                old_version = None
                if old_lines and old_lines[0].strip() == "---":
                    for line in old_lines[1:]:
                        stripped = line.strip()
                        if stripped == "---":
                            break
                        if stripped.startswith("case_version:"):
                            old_version = stripped.split(":", 1)[1].strip()
                            break

                if old_version and old_version == case_version:
                    issues.append(
                        ValidationIssue(
                            case_id=case_id,
                            file_path=str(fpath),
                            message=(
                                f"{fname} modified without case_version bump "
                                f"({old_version} \u2192 {case_version})"
                            ),
                            severity="warning",
                        )
                    )
        except (OSError, subprocess.TimeoutExpired):
            continue

    return issues


def validate_dataset(
    dataset_dir: Path | None = None,
    schema_path: Path | None = None,
) -> ValidationResult:
    """
    Validate dataset integrity + security constraints.

    Enforced constraints:
    - trace.json validates against schemas/trace_schema.json
    - each case folder contains prompt.txt, trace.json, expected_outcome.md
    - no secrets/tokens patterns in any required case file
    - no external URLs (http/https) in any required case file
    - no absolute paths in any required case file
    - no path traversal patterns in any required case file
    - all reads constrained within repo root (prevents local filesystem access)
    """
    repo_root = _get_repo_root()

    dataset_dir = dataset_dir or (repo_root / "data" / "cases")
    schema_path = schema_path or (repo_root / "schemas" / "trace_schema.json")

    try:
        dataset_dir = _safe_resolve_within(repo_root, dataset_dir)
        schema_path = _safe_resolve_within(repo_root, schema_path)
    except Exception as e:
        issues = (
            ValidationIssue(
                case_id="__global__", file_path=str(repo_root), message=str(e), severity="error"
            ),
        )
        return ValidationResult(ok=False, issues=issues)

    if not dataset_dir.exists() or not dataset_dir.is_dir():
        issues = (
            ValidationIssue(
                case_id="__global__",
                file_path=str(dataset_dir),
                message="Dataset directory missing or not a directory",
                severity="error",
            ),
        )
        return ValidationResult(ok=False, issues=issues)

    if not schema_path.exists() or not schema_path.is_file():
        issues = (
            ValidationIssue(
                case_id="__global__",
                file_path=str(schema_path),
                message="Trace schema missing or not a file",
                severity="error",
            ),
        )
        return ValidationResult(ok=False, issues=issues)

    issues_list: list[ValidationIssue] = []

    case_dirs = [p for p in dataset_dir.iterdir() if p.is_dir()]
    for case_dir in sorted(case_dirs, key=lambda p: p.name):
        case_id = case_dir.name

        # Enforce case directories remain within repo (symlink safety)
        try:
            case_dir = _safe_resolve_within(repo_root, case_dir)
        except Exception as e:
            issues_list.append(
                ValidationIssue(
                    case_id=case_id, file_path=str(case_dir), message=str(e), severity="error"
                )
            )
            continue

        # Structure checks
        for err in _validate_case_structure(case_dir):
            issues_list.append(
                ValidationIssue(
                    case_id=case_id, file_path=str(case_dir), message=err, severity="error"
                )
            )

        # Schema check
        trace_path = case_dir / "trace.json"
        if trace_path.exists() and trace_path.is_file():
            for err in _validate_trace_against_schema(trace_path, schema_path):
                issues_list.append(
                    ValidationIssue(
                        case_id=case_id, file_path=str(trace_path), message=err, severity="error"
                    )
                )

        # Header validation on expected_outcome.md
        outcome_path = case_dir / "expected_outcome.md"
        header: dict[str, str] = {}
        if outcome_path.exists() and outcome_path.is_file():
            try:
                header = _parse_expected_outcome_header(outcome_path)
                issues_list.extend(_validate_header_fields(case_id, header, outcome_path))
            except Exception as e:
                issues_list.append(
                    ValidationIssue(
                        case_id=case_id,
                        file_path=str(outcome_path),
                        message=f"Failed to parse expected_outcome.md header: {e}",
                        severity="error",
                    )
                )

        # Version-bump detection (git-aware, advisory)
        if header:
            issues_list.extend(_check_version_bump(case_id, case_dir, header, repo_root))

        # Security scans on required files (if present)
        for fname in REQUIRED_CASE_FILES:
            fpath = case_dir / fname
            if not fpath.exists() or not fpath.is_file():
                continue
            try:
                fpath = _safe_resolve_within(repo_root, fpath)
                text = _read_text(fpath)
                for v in _scan_text_for_security_violations(text):
                    issues_list.append(
                        ValidationIssue(
                            case_id=case_id, file_path=str(fpath), message=v, severity="error"
                        )
                    )
            except Exception as e:
                issues_list.append(
                    ValidationIssue(
                        case_id=case_id,
                        file_path=str(fpath),
                        message=f"Failed to read/scan file: {e}",
                        severity="error",
                    )
                )

    all_issues: tuple[ValidationIssue, ...] = tuple(issues_list)
    has_errors = any(i.severity == "error" for i in all_issues)
    return ValidationResult(ok=(not has_errors), issues=all_issues)


def _print_result(result: ValidationResult) -> None:
    error_count = sum(1 for i in result.issues if i.severity == "error")
    warning_count = sum(1 for i in result.issues if i.severity == "warning")

    for issue in result.issues:
        prefix = "ERROR" if issue.severity == "error" else "WARNING"
        print(f"[{issue.case_id}] {prefix}: {issue.message}")

    if result.ok and not result.issues:
        print("✅ Dataset validation passed.")
    elif result.ok and warning_count > 0:
        print(f"\n✅ Dataset validation passed ({warning_count} warning(s)).")
    else:
        parts = []
        if error_count:
            parts.append(f"{error_count} error(s)")
        if warning_count:
            parts.append(f"{warning_count} warning(s)")
        print(f"\n❌ Dataset validation failed ({', '.join(parts)}).")


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        prog="agenteval-dataset-validator",
        description="Validate AgentEval benchmark dataset (schema + security constraints).",
    )
    parser.add_argument(
        "--dataset-dir",
        default=None,
        help="Override dataset directory (must be inside repo). Default: data/cases",
    )
    parser.add_argument(
        "--schema-path",
        default=None,
        help="Override trace schema path (must be inside repo). Default: schemas/trace_schema.json",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Explicit repo root. Equivalent to setting AGENTEVAL_REPO_ROOT.",
    )

    args = parser.parse_args(argv)

    if args.repo_root:
        os.environ["AGENTEVAL_REPO_ROOT"] = args.repo_root

    dataset_dir = Path(args.dataset_dir) if args.dataset_dir else None
    schema_path = Path(args.schema_path) if args.schema_path else None

    result = validate_dataset(dataset_dir=dataset_dir, schema_path=schema_path)
    _print_result(result)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
