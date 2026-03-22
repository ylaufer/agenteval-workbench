from __future__ import annotations

import os
from pathlib import Path

import pytest

from agenteval.dataset.generator import generate_case, VALID_FAILURE_TYPES
from agenteval.dataset.validator import validate_dataset


class TestGenerateCase:
    def test_produces_all_three_files(self, repo_root_env: Path) -> None:
        """T022: generate_case() produces all 3 required files."""
        case_dir = generate_case(case_id="test_gen", output_dir=repo_root_env / "data" / "cases")
        assert (case_dir / "prompt.txt").is_file()
        assert (case_dir / "trace.json").is_file()
        assert (case_dir / "expected_outcome.md").is_file()

    def test_generated_case_passes_validation(self, repo_root_env: Path) -> None:
        """T023: Generated case passes validate_dataset()."""
        generate_case(case_id="valid_case", output_dir=repo_root_env / "data" / "cases")
        result = validate_dataset()
        assert result.ok is True

    def test_failure_type_produces_correct_header(self, repo_root_env: Path) -> None:
        """T024: generate_case() with failure_type produces correct header."""
        case_dir = generate_case(
            case_id="halluc_case",
            failure_type="tool_hallucination",
            output_dir=repo_root_env / "data" / "cases",
        )
        content = (case_dir / "expected_outcome.md").read_text(encoding="utf-8")
        assert "Primary Failure: Tool Hallucination" in content
        assert "case_version: 1.0" in content
        assert "Severity: Critical" in content

    def test_raises_when_case_exists_no_overwrite(self, repo_root_env: Path) -> None:
        """T025: Raises ValueError when case exists and overwrite=False."""
        output_dir = repo_root_env / "data" / "cases"
        generate_case(case_id="dup_case", output_dir=output_dir)
        with pytest.raises(ValueError, match="already exists"):
            generate_case(case_id="dup_case", output_dir=output_dir, overwrite=False)

    def test_overwrite_replaces_existing(self, repo_root_env: Path) -> None:
        """T026: generate_case() with overwrite=True replaces existing case."""
        output_dir = repo_root_env / "data" / "cases"
        case_dir = generate_case(case_id="ow_case", output_dir=output_dir)
        original_content = (case_dir / "prompt.txt").read_text(encoding="utf-8")

        # Overwrite with a failure type to change content
        case_dir2 = generate_case(
            case_id="ow_case",
            failure_type="tool_hallucination",
            output_dir=output_dir,
            overwrite=True,
        )
        new_content = (case_dir2 / "prompt.txt").read_text(encoding="utf-8")
        assert new_content != original_content

    def test_raises_for_invalid_failure_type(self, repo_root_env: Path) -> None:
        """T027: Raises ValueError for invalid failure_type."""
        with pytest.raises(ValueError, match="Invalid failure_type"):
            generate_case(
                case_id="bad_type",
                failure_type="nonexistent_failure",
                output_dir=repo_root_env / "data" / "cases",
            )

    def test_rejects_output_dir_outside_repo(
        self, repo_root_env: Path, tmp_path_factory: pytest.TempPathFactory
    ) -> None:
        """T028: Raises ValueError for output_dir outside repo root."""
        outside_dir = tmp_path_factory.mktemp("outside_repo")
        with pytest.raises(ValueError, match="Path escapes repo root"):
            generate_case(case_id="escape_case", output_dir=outside_dir)
