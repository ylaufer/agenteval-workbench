"""Tests for agenteval.core.rubric_builder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agenteval.core.rubric_builder import (
    SCALE_KEYS,
    VALID_SCALES,
    RubricDimension,
    RubricDraft,
    list_rubrics,
    list_templates,
    load_template,
    next_version,
    save_rubric,
    validate_rubric,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    """Create a minimal repo root with rubrics/templates/ structure."""
    templates_dir = tmp_path / "rubrics" / "templates"
    templates_dir.mkdir(parents=True)

    # Create a minimal schema so validate_rubric works offline
    schemas_dir = tmp_path / "schemas"
    schemas_dir.mkdir()

    # Copy the real schema content (minimal valid schema for tests)
    schema_content = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": ["version", "dimensions"],
        "properties": {
            "version": {"type": "string", "minLength": 1},
            "name": {"type": "string"},
            "dimensions": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["name", "scale", "description", "scoring_guide"],
                    "additionalProperties": False,
                    "properties": {
                        "name": {"type": "string", "minLength": 1, "pattern": "^[a-z0-9_]+$"},
                        "title": {"type": "string"},
                        "scale": {"type": "string", "enum": ["0-2", "1-5", "0-4"]},
                        "weight": {"type": "number", "minimum": 0},
                        "description": {"type": "string", "minLength": 1},
                        "scoring_guide": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "0": {"type": "string"},
                                "1": {"type": "string"},
                                "2": {"type": "string"},
                                "3": {"type": "string"},
                                "4": {"type": "string"},
                                "5": {"type": "string"},
                            },
                        },
                        "evidence_required": {"type": "boolean"},
                    },
                },
            },
        },
    }
    (schemas_dir / "rubric_schema.json").write_text(
        json.dumps(schema_content), encoding="utf-8"
    )
    return tmp_path


@pytest.fixture()
def sample_template(repo_root: Path) -> dict:
    """Write one template JSON and return its content."""
    template = {
        "name": "Test Template",
        "dimensions": [
            {
                "name": "accuracy",
                "title": "Accuracy",
                "scale": "0-2",
                "weight": 1.0,
                "description": "Correctness of claims.",
                "evidence_required": True,
                "scoring_guide": {"0": "Wrong.", "1": "Partial.", "2": "Correct."},
            }
        ],
    }
    (repo_root / "rubrics" / "templates" / "test_template.json").write_text(
        json.dumps(template), encoding="utf-8"
    )
    return template


@pytest.fixture()
def valid_rubric() -> dict:
    return {
        "version": "v1_test",
        "dimensions": [
            {
                "name": "accuracy",
                "scale": "0-2",
                "description": "Correctness of claims.",
                "scoring_guide": {"0": "Wrong.", "1": "Partial.", "2": "Correct."},
            }
        ],
    }


# ---------------------------------------------------------------------------
# Tests: list_templates
# ---------------------------------------------------------------------------


class TestListTemplates:
    def test_returns_sorted_ids(self, repo_root: Path) -> None:
        """list_templates returns sorted list of template stems."""
        templates_dir = repo_root / "rubrics" / "templates"
        (templates_dir / "bravo.json").write_text("{}", encoding="utf-8")
        (templates_dir / "alpha.json").write_text("{}", encoding="utf-8")
        result = list_templates(repo_root)
        assert result == ["alpha", "bravo"]

    def test_empty_when_no_templates(self, repo_root: Path) -> None:
        result = list_templates(repo_root)
        assert result == []

    def test_excludes_non_json_files(self, repo_root: Path) -> None:
        templates_dir = repo_root / "rubrics" / "templates"
        (templates_dir / "good.json").write_text("{}", encoding="utf-8")
        (templates_dir / "readme.txt").write_text("ignore", encoding="utf-8")
        result = list_templates(repo_root)
        assert result == ["good"]

    def test_returns_four_real_templates(self) -> None:
        """The real repo root has exactly 4 templates."""
        from agenteval.dataset.validator import _get_repo_root

        real_root = _get_repo_root()
        templates = list_templates(real_root)
        assert len(templates) == 4
        assert set(templates) == {
            "code_generation",
            "customer_support",
            "general_agent",
            "rag_pipeline",
        }


# ---------------------------------------------------------------------------
# Tests: load_template
# ---------------------------------------------------------------------------


class TestLoadTemplate:
    def test_returns_dict_with_dimensions(self, repo_root: Path, sample_template: dict) -> None:
        result = load_template("test_template", repo_root)
        assert "dimensions" in result
        assert len(result["dimensions"]) == 1

    def test_raises_file_not_found_for_unknown(self, repo_root: Path) -> None:
        with pytest.raises(FileNotFoundError, match="nonexistent"):
            load_template("nonexistent", repo_root)

    def test_returned_dict_has_name(self, repo_root: Path, sample_template: dict) -> None:
        result = load_template("test_template", repo_root)
        assert result["name"] == "Test Template"


# ---------------------------------------------------------------------------
# Tests: list_rubrics
# ---------------------------------------------------------------------------


class TestListRubrics:
    def test_excludes_templates_subdir(self, repo_root: Path) -> None:
        """Files inside rubrics/templates/ must NOT appear in list_rubrics."""
        (repo_root / "rubrics" / "templates" / "inside_templates.json").write_text(
            "{}", encoding="utf-8"
        )
        (repo_root / "rubrics" / "v1_myrubric.json").write_text("{}", encoding="utf-8")
        result = list_rubrics(repo_root)
        assert "inside_templates" not in result
        assert "v1_myrubric" in result

    def test_returns_sorted(self, repo_root: Path) -> None:
        for name in ["v2_beta.json", "v1_alpha.json", "v1_beta.json"]:
            (repo_root / "rubrics" / name).write_text("{}", encoding="utf-8")
        result = list_rubrics(repo_root)
        assert result == sorted(result)

    def test_empty_when_no_rubrics(self, repo_root: Path) -> None:
        result = list_rubrics(repo_root)
        assert result == []


# ---------------------------------------------------------------------------
# Tests: next_version
# ---------------------------------------------------------------------------


class TestNextVersion:
    def test_returns_v1_when_none_exist(self, repo_root: Path) -> None:
        assert next_version("myrubric", repo_root) == "v1"

    def test_returns_v2_when_v1_exists(self, repo_root: Path) -> None:
        (repo_root / "rubrics" / "v1_myrubric.json").write_text("{}", encoding="utf-8")
        assert next_version("myrubric", repo_root) == "v2"

    def test_increments_past_gap(self, repo_root: Path) -> None:
        """With v1 and v3 present, next version is v4."""
        (repo_root / "rubrics" / "v1_gap.json").write_text("{}", encoding="utf-8")
        (repo_root / "rubrics" / "v3_gap.json").write_text("{}", encoding="utf-8")
        assert next_version("gap", repo_root) == "v4"

    def test_does_not_confuse_similar_names(self, repo_root: Path) -> None:
        """v1_myrubric_extra should NOT count toward v*_myrubric."""
        (repo_root / "rubrics" / "v1_myrubric_extra.json").write_text("{}", encoding="utf-8")
        assert next_version("myrubric", repo_root) == "v1"


# ---------------------------------------------------------------------------
# Tests: validate_rubric
# ---------------------------------------------------------------------------


class TestValidateRubric:
    def test_valid_rubric_passes(self, repo_root: Path, valid_rubric: dict) -> None:
        # Reset schema cache for isolated tests
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        is_valid, errors = validate_rubric(valid_rubric, repo_root)
        assert is_valid is True
        assert errors == []

    def test_missing_version_fails(self, repo_root: Path) -> None:
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        rubric = {
            "dimensions": [
                {
                    "name": "accuracy",
                    "scale": "0-2",
                    "description": "Correctness.",
                    "scoring_guide": {"0": "Wrong.", "1": "Partial.", "2": "Correct."},
                }
            ]
        }
        is_valid, errors = validate_rubric(rubric, repo_root)
        assert is_valid is False
        assert any("version" in e.lower() or "schema" in e.lower() for e in errors)

    def test_invalid_dimension_name_fails(self, repo_root: Path) -> None:
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        rubric = {
            "version": "v1_test",
            "dimensions": [
                {
                    "name": "Invalid Name!",
                    "scale": "0-2",
                    "description": "Correctness.",
                    "scoring_guide": {"0": "Wrong.", "1": "Partial.", "2": "Correct."},
                }
            ],
        }
        is_valid, errors = validate_rubric(rubric, repo_root)
        assert is_valid is False

    def test_incomplete_scoring_guide_fails(self, repo_root: Path) -> None:
        """Missing '1' key for scale 0-2 should fail semantic validation."""
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        rubric = {
            "version": "v1_test",
            "dimensions": [
                {
                    "name": "accuracy",
                    "scale": "0-2",
                    "description": "Correctness.",
                    "scoring_guide": {"0": "Wrong.", "2": "Correct."},  # missing "1"
                }
            ],
        }
        is_valid, errors = validate_rubric(rubric, repo_root)
        assert is_valid is False
        assert any("1" in e for e in errors)

    def test_no_dimensions_fails(self, repo_root: Path) -> None:
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        rubric = {"version": "v1_test", "dimensions": []}
        is_valid, errors = validate_rubric(rubric, repo_root)
        assert is_valid is False

    def test_all_scale_keys_validated(self, repo_root: Path) -> None:
        """Scale 1-5 requires keys 1,2,3,4,5."""
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        rubric = {
            "version": "v1_test",
            "dimensions": [
                {
                    "name": "accuracy",
                    "scale": "1-5",
                    "description": "Correctness.",
                    "scoring_guide": {
                        "1": "Very poor.",
                        "2": "Poor.",
                        "3": "Acceptable.",
                        "4": "Good.",
                        "5": "Excellent.",
                    },
                }
            ],
        }
        is_valid, errors = validate_rubric(rubric, repo_root)
        assert is_valid is True
        assert errors == []


# ---------------------------------------------------------------------------
# Tests: save_rubric
# ---------------------------------------------------------------------------


class TestSaveRubric:
    def test_saves_file_with_correct_version_stem(
        self, repo_root: Path, valid_rubric: dict
    ) -> None:
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        saved = save_rubric("myrubric", valid_rubric, repo_root)
        assert saved.exists()
        assert saved.name == "v1_myrubric.json"

    def test_second_save_increments_to_v2(
        self, repo_root: Path, valid_rubric: dict
    ) -> None:
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        save_rubric("myrubric", valid_rubric, repo_root)
        saved2 = save_rubric("myrubric", valid_rubric, repo_root)
        assert saved2.name == "v2_myrubric.json"

    def test_sets_version_field_in_file(
        self, repo_root: Path, valid_rubric: dict
    ) -> None:
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        saved = save_rubric("myrubric", valid_rubric, repo_root)
        content = json.loads(saved.read_text(encoding="utf-8"))
        assert content["version"] == "v1_myrubric"

    def test_invalid_name_raises_value_error(
        self, repo_root: Path, valid_rubric: dict
    ) -> None:
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        with pytest.raises(ValueError, match="invalid"):
            save_rubric("Invalid Name!", valid_rubric, repo_root)

    def test_empty_name_raises_value_error(
        self, repo_root: Path, valid_rubric: dict
    ) -> None:
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        with pytest.raises(ValueError):
            save_rubric("", valid_rubric, repo_root)

    def test_invalid_rubric_raises_value_error(self, repo_root: Path) -> None:
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        bad_rubric = {"version": "v1_test", "dimensions": []}
        with pytest.raises(ValueError, match="validation failed"):
            save_rubric("myrubric", bad_rubric, repo_root)

    def test_does_not_mutate_caller_dict(
        self, repo_root: Path, valid_rubric: dict
    ) -> None:
        """save_rubric must not modify the caller's rubric dict version field."""
        import agenteval.core.rubric_builder as rb
        rb._RUBRIC_SCHEMA = None

        original_version = valid_rubric["version"]
        save_rubric("myrubric", valid_rubric, repo_root)
        assert valid_rubric["version"] == original_version


# ---------------------------------------------------------------------------
# Tests: RubricDimension and RubricDraft data classes
# ---------------------------------------------------------------------------


class TestDataClasses:
    def test_rubric_dimension_defaults(self) -> None:
        dim = RubricDimension(
            name="accuracy",
            scale="0-2",
            description="Test.",
            scoring_guide={"0": "Bad.", "1": "OK.", "2": "Good."},
        )
        assert dim.title == ""
        assert dim.weight == 1.0
        assert dim.evidence_required is True

    def test_rubric_dimension_to_dict(self) -> None:
        dim = RubricDimension(
            name="accuracy",
            scale="0-2",
            description="Test.",
            scoring_guide={"0": "Bad.", "1": "OK.", "2": "Good."},
            title="Accuracy",
        )
        d = dim.to_dict()
        assert d["name"] == "accuracy"
        assert d["title"] == "Accuracy"
        assert "scoring_guide" in d

    def test_rubric_draft_to_rubric_dict(self) -> None:
        dim = RubricDimension(
            name="accuracy",
            scale="0-2",
            description="Test.",
            scoring_guide={"0": "Bad.", "1": "OK.", "2": "Good."},
        )
        draft = RubricDraft(name="test", dimensions=[dim])
        result = draft.to_rubric_dict("v1_test")
        assert result["version"] == "v1_test"
        assert len(result["dimensions"]) == 1

    def test_valid_scales_constant(self) -> None:
        assert "0-2" in VALID_SCALES
        assert "1-5" in VALID_SCALES
        assert "0-4" in VALID_SCALES

    def test_scale_keys_constant(self) -> None:
        assert SCALE_KEYS["0-2"] == ["0", "1", "2"]
        assert SCALE_KEYS["1-5"] == ["1", "2", "3", "4", "5"]
        assert SCALE_KEYS["0-4"] == ["0", "1", "2", "3", "4"]
