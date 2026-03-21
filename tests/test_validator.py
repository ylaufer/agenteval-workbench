from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from agenteval.dataset.validator import (
    _safe_resolve_within,
    _scan_text_for_security_violations,
    _validate_case_structure,
    _validate_trace_against_schema,
    validate_dataset,
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
