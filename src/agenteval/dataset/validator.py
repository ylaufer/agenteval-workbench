from __future__ import annotations

import argparse
import json
import os
import re
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


@dataclass(frozen=True)
class ValidationIssue:
    case_id: str
    file_path: str
    message: str


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
    raise RuntimeError(
        "Repo root not found (expected pyproject.toml or .git).")


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
        issues = (ValidationIssue(case_id="__global__",
                  file_path=str(repo_root), message=str(e)),)
        return ValidationResult(ok=False, issues=issues)

    if not dataset_dir.exists() or not dataset_dir.is_dir():
        issues = (ValidationIssue(case_id="__global__", file_path=str(
            dataset_dir), message="Dataset directory missing or not a directory"),)
        return ValidationResult(ok=False, issues=issues)

    if not schema_path.exists() or not schema_path.is_file():
        issues = (ValidationIssue(case_id="__global__", file_path=str(
            schema_path), message="Trace schema missing or not a file"),)
        return ValidationResult(ok=False, issues=issues)

    issues_list: list[ValidationIssue] = []

    case_dirs = [p for p in dataset_dir.iterdir() if p.is_dir()]
    for case_dir in sorted(case_dirs, key=lambda p: p.name):
        case_id = case_dir.name

        # Enforce case directories remain within repo (symlink safety)
        try:
            case_dir = _safe_resolve_within(repo_root, case_dir)
        except Exception as e:
            issues_list.append(ValidationIssue(
                case_id=case_id, file_path=str(case_dir), message=str(e)))
            continue

        # Structure checks
        for err in _validate_case_structure(case_dir):
            issues_list.append(ValidationIssue(
                case_id=case_id, file_path=str(case_dir), message=err))

        # Schema check
        trace_path = case_dir / "trace.json"
        if trace_path.exists() and trace_path.is_file():
            for err in _validate_trace_against_schema(trace_path, schema_path):
                issues_list.append(ValidationIssue(
                    case_id=case_id, file_path=str(trace_path), message=err))

        # Security scans on required files (if present)
        for fname in REQUIRED_CASE_FILES:
            fpath = case_dir / fname
            if not fpath.exists() or not fpath.is_file():
                continue
            try:
                fpath = _safe_resolve_within(repo_root, fpath)
                text = _read_text(fpath)
                for v in _scan_text_for_security_violations(text):
                    issues_list.append(ValidationIssue(
                        case_id=case_id, file_path=str(fpath), message=v))
            except Exception as e:
                issues_list.append(ValidationIssue(case_id=case_id, file_path=str(
                    fpath), message=f"Failed to read/scan file: {e}"))

    issues = tuple(issues_list)
    return ValidationResult(ok=(len(issues) == 0), issues=issues)


def _print_result(result: ValidationResult) -> None:
    if result.ok:
        print("✅ Dataset validation successful.")
        return

    print("❌ Dataset validation failed.\n")
    for i, issue in enumerate(result.issues, start=1):
        print(f"{i}. [{issue.case_id}] {issue.file_path}\n   - {issue.message}")
    print()


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
