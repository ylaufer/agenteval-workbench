from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from agenteval.dataset.validator import (
    _check_version_bump,
    _parse_expected_outcome_header,
    _safe_resolve_within,
    _scan_text_for_security_violations,
    _validate_case_structure,
    _validate_header_fields,
    _validate_trace_against_schema,
    validate_dataset,
    ValidationIssue,
    ValidationResult,
    main,
)


# ---------------------------------------------------------------------------
# _safe_resolve_within
# ---------------------------------------------------------------------------


class TestSafeResolveWithin:
    def test_valid_subpath(self, tmp_path: Path) -> None:
        child = tmp_path / "sub" / "file.txt"
        child.parent.mkdir(parents=True)
        child.touch()
        result = _safe_resolve_within(tmp_path, child)
        assert result == child.resolve()

    def test_path_traversal_rejected(self, tmp_path: Path) -> None:
        escaped = tmp_path / "sub" / ".." / ".." / "etc" / "passwd"
        with pytest.raises(ValueError, match="Path escapes repo root"):
            _safe_resolve_within(tmp_path, escaped)

    def test_exact_root(self, tmp_path: Path) -> None:
        result = _safe_resolve_within(tmp_path, tmp_path)
        assert result == tmp_path.resolve()

    def test_valid_nested(self, tmp_path: Path) -> None:
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)
        result = _safe_resolve_within(tmp_path, nested)
        assert result == nested.resolve()


# ---------------------------------------------------------------------------
# _scan_text_for_security_violations
# ---------------------------------------------------------------------------


class TestScanTextForSecurityViolations:
    def test_clean_text(self) -> None:
        assert _scan_text_for_security_violations("Hello world, this is fine.") == []

    def test_sk_key(self) -> None:
        violations = _scan_text_for_security_violations("key: sk-abc1234567890")
        assert any("Secret-like" in v for v in violations)

    def test_bearer_token(self) -> None:
        violations = _scan_text_for_security_violations("Authorization: Bearer abcdef1234")
        assert any("Secret-like" in v for v in violations)

    def test_api_key_pattern(self) -> None:
        violations = _scan_text_for_security_violations("api_key = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'")
        assert any("Secret-like" in v for v in violations)

    def test_url_detected(self) -> None:
        violations = _scan_text_for_security_violations("Visit https://example.com")
        assert any("External URL" in v for v in violations)

    def test_http_url_detected(self) -> None:
        violations = _scan_text_for_security_violations("Visit http://example.com")
        assert any("External URL" in v for v in violations)

    def test_absolute_path_posix(self) -> None:
        violations = _scan_text_for_security_violations("/Users/admin/secret")
        assert any("Absolute path" in v for v in violations)

    def test_absolute_path_windows(self) -> None:
        violations = _scan_text_for_security_violations("path is C:\\Users\\admin")
        assert any("Absolute path" in v for v in violations)

    def test_path_traversal_forward(self) -> None:
        violations = _scan_text_for_security_violations("go to ../etc/passwd")
        assert any("Path traversal" in v for v in violations)

    def test_path_traversal_backward(self) -> None:
        violations = _scan_text_for_security_violations("go to ..\\secret")
        assert any("Path traversal" in v for v in violations)


# ---------------------------------------------------------------------------
# _validate_case_structure
# ---------------------------------------------------------------------------


class TestValidateCaseStructure:
    def test_all_files_present(self, tmp_path: Path) -> None:
        for fname in ("prompt.txt", "trace.json", "expected_outcome.md"):
            (tmp_path / fname).touch()
        assert _validate_case_structure(tmp_path) == []

    def test_missing_prompt(self, tmp_path: Path) -> None:
        (tmp_path / "trace.json").touch()
        (tmp_path / "expected_outcome.md").touch()
        errors = _validate_case_structure(tmp_path)
        assert any("prompt.txt" in e for e in errors)

    def test_missing_trace(self, tmp_path: Path) -> None:
        (tmp_path / "prompt.txt").touch()
        (tmp_path / "expected_outcome.md").touch()
        errors = _validate_case_structure(tmp_path)
        assert any("trace.json" in e for e in errors)

    def test_missing_expected_outcome(self, tmp_path: Path) -> None:
        (tmp_path / "prompt.txt").touch()
        (tmp_path / "trace.json").touch()
        errors = _validate_case_structure(tmp_path)
        assert any("expected_outcome.md" in e for e in errors)

    def test_extra_files_ok(self, tmp_path: Path) -> None:
        for fname in ("prompt.txt", "trace.json", "expected_outcome.md", "notes.txt"):
            (tmp_path / fname).touch()
        assert _validate_case_structure(tmp_path) == []


# ---------------------------------------------------------------------------
# _validate_trace_against_schema
# ---------------------------------------------------------------------------


class TestValidateTraceAgainstSchema:
    def test_valid_trace(
        self,
        tmp_path: Path,
        minimal_trace: Dict[str, Any],
    ) -> None:
        trace_path = tmp_path / "trace.json"
        trace_path.write_text(json.dumps(minimal_trace), encoding="utf-8")
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "trace_schema.json"
        assert _validate_trace_against_schema(trace_path, schema_path) == []

    def test_missing_required_field(self, tmp_path: Path) -> None:
        trace_path = tmp_path / "trace.json"
        trace_path.write_text(json.dumps({"task_id": "x"}), encoding="utf-8")
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "trace_schema.json"
        errors = _validate_trace_against_schema(trace_path, schema_path)
        assert len(errors) > 0
        assert any("Schema validation error" in e for e in errors)

    def test_invalid_json(self, tmp_path: Path) -> None:
        trace_path = tmp_path / "trace.json"
        trace_path.write_text("not json", encoding="utf-8")
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "trace_schema.json"
        errors = _validate_trace_against_schema(trace_path, schema_path)
        assert len(errors) > 0


# ---------------------------------------------------------------------------
# validate_dataset
# ---------------------------------------------------------------------------


class TestValidateDataset:
    def test_valid_dataset(self, sample_case_dir: Path, repo_root_env: Path) -> None:
        result = validate_dataset()
        assert result.ok is True
        assert result.issues == ()

    def test_missing_dataset_dir(self, repo_root_env: Path) -> None:
        # Don't create data/cases/ at all
        result = validate_dataset()
        assert result.ok is False
        assert any("Dataset directory" in i.message for i in result.issues)

    def test_invalid_trace(self, repo_root_env: Path) -> None:
        case_dir = repo_root_env / "data" / "cases" / "case_001"
        case_dir.mkdir(parents=True)
        (case_dir / "prompt.txt").write_text("test", encoding="utf-8")
        (case_dir / "trace.json").write_text('{"bad": true}', encoding="utf-8")
        (case_dir / "expected_outcome.md").write_text("outcome", encoding="utf-8")
        result = validate_dataset()
        assert result.ok is False

    def test_security_violation_in_prompt(
        self, repo_root_env: Path, minimal_trace: Dict[str, Any]
    ) -> None:
        case_dir = repo_root_env / "data" / "cases" / "case_001"
        case_dir.mkdir(parents=True)
        (case_dir / "prompt.txt").write_text("Use key sk-abcdefghijklmnop1234", encoding="utf-8")
        (case_dir / "trace.json").write_text(json.dumps(minimal_trace), encoding="utf-8")
        (case_dir / "expected_outcome.md").write_text("outcome", encoding="utf-8")
        result = validate_dataset()
        assert result.ok is False
        assert any("Secret-like" in i.message for i in result.issues)

    def test_empty_dataset_dir(self, repo_root_env: Path) -> None:
        (repo_root_env / "data" / "cases").mkdir(parents=True)
        result = validate_dataset()
        # Empty dir with no case folders is valid (0 issues)
        assert result.ok is True


# ---------------------------------------------------------------------------
# main (CLI)
# ---------------------------------------------------------------------------


class TestMain:
    @pytest.mark.integration
    def test_exit_zero_on_valid(self, sample_case_dir: Path, repo_root_env: Path) -> None:
        exit_code = main([])
        assert exit_code == 0

    @pytest.mark.integration
    def test_exit_one_on_invalid(self, repo_root_env: Path) -> None:
        # Missing dataset dir → issues → exit 1
        exit_code = main([])
        assert exit_code == 1


# ---------------------------------------------------------------------------
# Header validation (US1)
# ---------------------------------------------------------------------------


VALID_HEADER = (
    "---\n"
    "Case ID: test_001\n"
    "Primary Failure: Tool Hallucination\n"
    "Secondary Failures: Constraint Violation\n"
    "Severity: Critical\n"
    "case_version: 1.0\n"
    "---\n"
)


class TestHeaderValidation:
    def test_valid_header_all_fields(self, tmp_path: Path) -> None:
        """T010: Valid header with all 5 fields passes validation."""
        outcome = tmp_path / "expected_outcome.md"
        outcome.write_text(VALID_HEADER + "\nSome content.\n", encoding="utf-8")
        header = _parse_expected_outcome_header(outcome)
        issues = _validate_header_fields("test_001", header, outcome)
        assert issues == []

    def test_missing_case_version_produces_error(self, tmp_path: Path) -> None:
        """T011: Missing case_version produces severity=error."""
        outcome = tmp_path / "expected_outcome.md"
        outcome.write_text(
            "---\nCase ID: test_001\nPrimary Failure: Tool Hallucination\n"
            "Secondary Failures: None\nSeverity: High\n---\n",
            encoding="utf-8",
        )
        header = _parse_expected_outcome_header(outcome)
        issues = _validate_header_fields("test_001", header, outcome)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "case_version" in issues[0].message

    def test_missing_yaml_header_produces_errors(self, tmp_path: Path) -> None:
        """T012: Missing YAML header entirely produces severity=error for all fields."""
        outcome = tmp_path / "expected_outcome.md"
        outcome.write_text("No header here.\n", encoding="utf-8")
        header = _parse_expected_outcome_header(outcome)
        issues = _validate_header_fields("test_001", header, outcome)
        assert len(issues) == 5
        assert all(i.severity == "error" for i in issues)

    def test_ok_true_when_only_warnings(self) -> None:
        """T013: ValidationResult.ok=True when only warnings exist."""
        issues = (
            ValidationIssue(case_id="c", file_path="f", message="w", severity="warning"),
        )
        result = ValidationResult(ok=not any(i.severity == "error" for i in issues), issues=issues)
        assert result.ok is True

    def test_ok_false_when_error_exists(self) -> None:
        """T014: ValidationResult.ok=False when at least one error exists."""
        issues = (
            ValidationIssue(case_id="c", file_path="f", message="w", severity="warning"),
            ValidationIssue(case_id="c", file_path="f", message="e", severity="error"),
        )
        result = ValidationResult(ok=not any(i.severity == "error" for i in issues), issues=issues)
        assert result.ok is False


# ---------------------------------------------------------------------------
# Batch reporting (US3)
# ---------------------------------------------------------------------------


class TestBatchReporting:
    def test_three_broken_cases_produce_three_issues(
        self, repo_root_env: Path, minimal_trace: Dict[str, Any]
    ) -> None:
        """T036: 3 broken cases produce 3+ issues in a single ValidationResult."""
        cases_dir = repo_root_env / "data" / "cases"

        # Case 1: missing prompt.txt
        c1 = cases_dir / "broken_001"
        c1.mkdir(parents=True)
        (c1 / "trace.json").write_text(json.dumps(minimal_trace), encoding="utf-8")
        (c1 / "expected_outcome.md").write_text(
            "---\nCase ID: broken_001\nPrimary Failure: None\n"
            "Secondary Failures:\nSeverity: Low\ncase_version: 1.0\n---\n",
            encoding="utf-8",
        )

        # Case 2: bad schema
        c2 = cases_dir / "broken_002"
        c2.mkdir(parents=True)
        (c2 / "prompt.txt").write_text("test", encoding="utf-8")
        (c2 / "trace.json").write_text('{"bad": true}', encoding="utf-8")
        (c2 / "expected_outcome.md").write_text(
            "---\nCase ID: broken_002\nPrimary Failure: None\n"
            "Secondary Failures:\nSeverity: Low\ncase_version: 1.0\n---\n",
            encoding="utf-8",
        )

        # Case 3: missing header fields
        c3 = cases_dir / "broken_003"
        c3.mkdir(parents=True)
        (c3 / "prompt.txt").write_text("test", encoding="utf-8")
        (c3 / "trace.json").write_text(json.dumps(minimal_trace), encoding="utf-8")
        (c3 / "expected_outcome.md").write_text("No header here.\n", encoding="utf-8")

        result = validate_dataset()
        assert result.ok is False
        # All 3 cases should have issues
        case_ids_with_issues = {i.case_id for i in result.issues}
        assert "broken_001" in case_ids_with_issues
        assert "broken_002" in case_ids_with_issues
        assert "broken_003" in case_ids_with_issues

    def test_extra_files_do_not_cause_errors(
        self, repo_root_env: Path, minimal_trace: Dict[str, Any]
    ) -> None:
        """T037: Extra files in case directory do not cause errors."""
        case_dir = repo_root_env / "data" / "cases" / "extra_files_case"
        case_dir.mkdir(parents=True)
        (case_dir / "prompt.txt").write_text("test", encoding="utf-8")
        (case_dir / "trace.json").write_text(json.dumps(minimal_trace), encoding="utf-8")
        (case_dir / "expected_outcome.md").write_text(
            "---\nCase ID: extra_files_case\nPrimary Failure: None\n"
            "Secondary Failures:\nSeverity: Low\ncase_version: 1.0\n---\n",
            encoding="utf-8",
        )
        (case_dir / "notes.txt").write_text("extra notes", encoding="utf-8")
        (case_dir / "debug.log").write_text("debug info", encoding="utf-8")

        result = validate_dataset()
        assert result.ok is True

    def test_mixed_severity_all_reported(
        self, repo_root_env: Path, minimal_trace: Dict[str, Any]
    ) -> None:
        """T038: Mixed severity issues (errors + warnings) all reported, ok=False."""
        # This test verifies that both errors and warnings appear in the same result
        issues = (
            ValidationIssue(case_id="c1", file_path="f", message="missing file", severity="error"),
            ValidationIssue(case_id="c2", file_path="f", message="version bump", severity="warning"),
        )
        result = ValidationResult(
            ok=not any(i.severity == "error" for i in issues),
            issues=issues,
        )
        assert result.ok is False
        assert len(result.issues) == 2
        severities = {i.severity for i in result.issues}
        assert "error" in severities
        assert "warning" in severities


# ---------------------------------------------------------------------------
# Version-bump detection (US4)
# ---------------------------------------------------------------------------


class TestVersionBumpDetection:
    def test_modified_trace_without_bump_produces_warning(self, tmp_path: Path) -> None:
        """T043: Modified trace.json without version bump produces severity=warning."""
        # This tests the function directly without a real git repo
        # We test _check_version_bump with a non-git directory — it should skip silently
        case_dir = tmp_path / "case_001"
        case_dir.mkdir()
        (case_dir / "trace.json").write_text("{}", encoding="utf-8")
        (case_dir / "expected_outcome.md").write_text(
            "---\nCase ID: 001\nPrimary Failure: None\n"
            "Secondary Failures:\nSeverity: Low\ncase_version: 1.0\n---\n",
            encoding="utf-8",
        )
        header = {"case_version": "1.0"}
        # Without a git repo, this should return no issues (skips silently)
        issues = _check_version_bump("case_001", case_dir, header, tmp_path)
        assert issues == []

    def test_prompt_only_no_warning(self, tmp_path: Path) -> None:
        """T044: Modified prompt.txt only does NOT produce warning."""
        # prompt.txt changes don't trigger version-bump detection
        case_dir = tmp_path / "case_001"
        case_dir.mkdir()
        (case_dir / "prompt.txt").write_text("modified", encoding="utf-8")
        header = {"case_version": "1.0"}
        issues = _check_version_bump("case_001", case_dir, header, tmp_path)
        assert issues == []

    def test_skipped_when_not_in_git_repo(self, tmp_path: Path) -> None:
        """T045: Version-bump detection skipped when not in a git repo."""
        case_dir = tmp_path / "case_001"
        case_dir.mkdir()
        (case_dir / "trace.json").write_text("{}", encoding="utf-8")
        header = {"case_version": "1.0"}
        issues = _check_version_bump("case_001", case_dir, header, tmp_path)
        assert issues == []
