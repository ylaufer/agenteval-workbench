"""Unit tests for agenteval.core.annotations module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from agenteval.core.annotations import (
    Annotation,
    AutoEvalOverlay,
    DimEvidence,
    add_annotation,
    build_auto_eval_overlay,
    delete_annotation,
    get_annotations,
    get_auto_eval_for_case,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    """Return a temporary repo root with reports/ and runs/ directories."""
    (tmp_path / "reports").mkdir()
    (tmp_path / "runs").mkdir()
    return tmp_path


@pytest.fixture()
def sample_auto_eval() -> dict:  # type: ignore[type-arg]
    """Minimal auto_evaluation dict with one step-cited and one case-level dimension."""
    return {
        "case_id": "case_001",
        "scoring_type": "auto",
        "rubric_version": "v1",
        "dimensions": {
            "tool_use": {
                "dimension_name": "tool_use",
                "score": 1,
                "weight": 1.0,
                "scale": "0-2",
                "evidence_step_ids": ["step_2"],
                "notes": "Incomplete tool execution",
                "evaluator_type": "rule",
            },
            "security_safety": {
                "dimension_name": "security_safety",
                "score": 2,
                "weight": 1.5,
                "scale": "0-2",
                "evidence_step_ids": [],
                "notes": "No security issues found",
                "evaluator_type": "rule",
            },
        },
        "auto_tags": [],
        "metadata": {"timestamp": "2026-05-04T10:00:00+00:00"},
    }


# ---------------------------------------------------------------------------
# T010: add_annotation()
# ---------------------------------------------------------------------------


class TestAddAnnotation:
    def test_creates_annotation_with_correct_fields(self, repo_root: Path) -> None:
        ann = add_annotation(
            case_id="case_001",
            step_id="step_1",
            reviewer_id="alice",
            content="Test note",
            severity="low",
            repo_root=repo_root,
        )
        assert isinstance(ann, Annotation)
        assert ann.case_id == "case_001"
        assert ann.step_id == "step_1"
        assert ann.reviewer_id == "alice"
        assert ann.content == "Test note"
        assert ann.severity == "low"
        assert ann.annotation_id.startswith("ann_")
        assert len(ann.annotation_id) == 12  # ann_ + 8 hex

    def test_creates_file_on_first_write(self, repo_root: Path) -> None:
        add_annotation(
            case_id="case_001",
            step_id="step_1",
            reviewer_id="alice",
            content="Test note",
            severity="none",
            repo_root=repo_root,
        )
        ann_file = repo_root / "reports" / "case_001.annotations.json"
        assert ann_file.exists()

    def test_appends_on_subsequent_writes(self, repo_root: Path) -> None:
        for i in range(3):
            add_annotation(
                case_id="case_001",
                step_id=f"step_{i}",
                reviewer_id="alice",
                content=f"Note {i}",
                severity="low",
                repo_root=repo_root,
            )
        annotations = get_annotations("case_001", repo_root)
        assert len(annotations) == 3

    def test_raises_on_empty_content(self, repo_root: Path) -> None:
        with pytest.raises(ValueError, match="content"):
            add_annotation(
                case_id="case_001",
                step_id="step_1",
                reviewer_id="alice",
                content="",
                severity="low",
                repo_root=repo_root,
            )

    def test_raises_on_empty_case_id(self, repo_root: Path) -> None:
        with pytest.raises(ValueError, match="case_id"):
            add_annotation(
                case_id="",
                step_id="step_1",
                reviewer_id="alice",
                content="Note",
                severity="low",
                repo_root=repo_root,
            )

    def test_raises_on_empty_step_id(self, repo_root: Path) -> None:
        with pytest.raises(ValueError, match="step_id"):
            add_annotation(
                case_id="case_001",
                step_id="",
                reviewer_id="alice",
                content="Note",
                severity="low",
                repo_root=repo_root,
            )

    def test_raises_on_empty_reviewer_id(self, repo_root: Path) -> None:
        with pytest.raises(ValueError, match="reviewer_id"):
            add_annotation(
                case_id="case_001",
                step_id="step_1",
                reviewer_id="",
                content="Note",
                severity="low",
                repo_root=repo_root,
            )

    def test_raises_on_invalid_severity(self, repo_root: Path) -> None:
        with pytest.raises(ValueError, match="severity"):
            add_annotation(
                case_id="case_001",
                step_id="step_1",
                reviewer_id="alice",
                content="Note",
                severity="critical",  # type: ignore[arg-type]
                repo_root=repo_root,
            )

    def test_file_is_valid_per_schema(self, repo_root: Path) -> None:
        import jsonschema

        schema_path = Path(__file__).parent.parent / "schemas" / "annotation_schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        add_annotation(
            case_id="case_001",
            step_id="step_1",
            reviewer_id="alice",
            content="Test note",
            severity="high",
            repo_root=repo_root,
        )
        ann_file = repo_root / "reports" / "case_001.annotations.json"
        data = json.loads(ann_file.read_text(encoding="utf-8"))
        jsonschema.validate(instance=data, schema=schema)  # raises on invalid


# ---------------------------------------------------------------------------
# T011: get_annotations()
# ---------------------------------------------------------------------------


class TestGetAnnotations:
    def test_returns_empty_list_when_no_file(self, repo_root: Path) -> None:
        result = get_annotations("case_999", repo_root)
        assert result == []

    def test_returns_all_annotations(self, repo_root: Path) -> None:
        for i in range(4):
            add_annotation(
                case_id="case_001",
                step_id=f"step_{i}",
                reviewer_id="alice",
                content=f"Note {i}",
                severity="none",
                repo_root=repo_root,
            )
        result = get_annotations("case_001", repo_root)
        assert len(result) == 4

    def test_sorted_by_timestamp_ascending(self, repo_root: Path) -> None:
        for i in range(3):
            add_annotation(
                case_id="case_001",
                step_id=f"step_{i}",
                reviewer_id="alice",
                content=f"Note {i}",
                severity="none",
                repo_root=repo_root,
            )
        result = get_annotations("case_001", repo_root)
        timestamps = [a.timestamp for a in result]
        assert timestamps == sorted(timestamps)

    def test_returns_annotation_dataclass_instances(self, repo_root: Path) -> None:
        add_annotation(
            case_id="case_001",
            step_id="step_1",
            reviewer_id="alice",
            content="Note",
            severity="medium",
            repo_root=repo_root,
        )
        result = get_annotations("case_001", repo_root)
        assert all(isinstance(a, Annotation) for a in result)


# ---------------------------------------------------------------------------
# T012: delete_annotation()
# ---------------------------------------------------------------------------


class TestDeleteAnnotation:
    def test_returns_true_when_deleted(self, repo_root: Path) -> None:
        ann = add_annotation(
            case_id="case_001",
            step_id="step_1",
            reviewer_id="alice",
            content="Note",
            severity="low",
            repo_root=repo_root,
        )
        result = delete_annotation("case_001", ann.annotation_id, repo_root)
        assert result is True

    def test_returns_false_when_not_found(self, repo_root: Path) -> None:
        add_annotation(
            case_id="case_001",
            step_id="step_1",
            reviewer_id="alice",
            content="Note",
            severity="low",
            repo_root=repo_root,
        )
        result = delete_annotation("case_001", "ann_00000000", repo_root)
        assert result is False

    def test_returns_false_when_no_file(self, repo_root: Path) -> None:
        result = delete_annotation("case_999", "ann_00000000", repo_root)
        assert result is False

    def test_annotation_removed_from_file(self, repo_root: Path) -> None:
        ann = add_annotation(
            case_id="case_001",
            step_id="step_1",
            reviewer_id="alice",
            content="Note",
            severity="low",
            repo_root=repo_root,
        )
        delete_annotation("case_001", ann.annotation_id, repo_root)
        remaining = get_annotations("case_001", repo_root)
        assert not any(a.annotation_id == ann.annotation_id for a in remaining)

    def test_other_annotations_preserved_after_delete(self, repo_root: Path) -> None:
        ann1 = add_annotation(
            case_id="case_001",
            step_id="step_1",
            reviewer_id="alice",
            content="Note 1",
            severity="low",
            repo_root=repo_root,
        )
        ann2 = add_annotation(
            case_id="case_001",
            step_id="step_2",
            reviewer_id="alice",
            content="Note 2",
            severity="high",
            repo_root=repo_root,
        )
        delete_annotation("case_001", ann1.annotation_id, repo_root)
        remaining = get_annotations("case_001", repo_root)
        assert len(remaining) == 1
        assert remaining[0].annotation_id == ann2.annotation_id


# ---------------------------------------------------------------------------
# T013: build_auto_eval_overlay()
# ---------------------------------------------------------------------------


class TestBuildAutoEvalOverlay:
    def test_step_evidence_populated_when_evidence_step_ids_present(
        self, sample_auto_eval: dict  # type: ignore[type-arg]
    ) -> None:
        overlay = build_auto_eval_overlay(sample_auto_eval)
        assert "step_2" in overlay.step_evidence
        dims = overlay.step_evidence["step_2"]
        assert any(d.dimension == "tool_use" for d in dims)

    def test_case_flags_populated_when_evidence_step_ids_empty(
        self, sample_auto_eval: dict  # type: ignore[type-arg]
    ) -> None:
        overlay = build_auto_eval_overlay(sample_auto_eval)
        assert any(f.dimension == "security_safety" for f in overlay.case_flags)

    def test_empty_auto_eval_returns_empty_overlay(self) -> None:
        empty = {
            "case_id": "case_001",
            "dimensions": {},
            "scoring_type": "auto",
            "rubric_version": "v1",
            "auto_tags": [],
            "metadata": {"timestamp": "2026-05-04T10:00:00+00:00"},
        }
        overlay = build_auto_eval_overlay(empty)
        assert overlay.step_evidence == {}
        assert overlay.case_flags == []

    def test_returns_auto_eval_overlay_instance(
        self, sample_auto_eval: dict  # type: ignore[type-arg]
    ) -> None:
        overlay = build_auto_eval_overlay(sample_auto_eval)
        assert isinstance(overlay, AutoEvalOverlay)

    def test_dim_evidence_fields_populated(
        self, sample_auto_eval: dict  # type: ignore[type-arg]
    ) -> None:
        overlay = build_auto_eval_overlay(sample_auto_eval)
        dim = overlay.step_evidence["step_2"][0]
        assert isinstance(dim, DimEvidence)
        assert dim.dimension == "tool_use"
        assert dim.score == 1
        assert dim.evaluator_type == "rule"

    def test_multiple_steps_cited_by_same_dimension(self) -> None:
        auto_eval = {
            "case_id": "case_001",
            "dimensions": {
                "tool_use": {
                    "dimension_name": "tool_use",
                    "score": 0,
                    "weight": 1.0,
                    "scale": "0-2",
                    "evidence_step_ids": ["step_1", "step_3"],
                    "notes": "Two bad steps",
                    "evaluator_type": "rule",
                }
            },
            "scoring_type": "auto",
            "rubric_version": "v1",
            "auto_tags": [],
            "metadata": {"timestamp": "2026-05-04T10:00:00+00:00"},
        }
        overlay = build_auto_eval_overlay(auto_eval)
        assert "step_1" in overlay.step_evidence
        assert "step_3" in overlay.step_evidence


# ---------------------------------------------------------------------------
# T014: get_auto_eval_for_case()
# ---------------------------------------------------------------------------


class TestGetAutoEvalForCase:
    def test_returns_none_when_no_file_exists(self, repo_root: Path) -> None:
        result = get_auto_eval_for_case("case_999", repo_root)
        assert result is None

    def test_returns_dict_when_reports_file_exists(
        self,
        repo_root: Path,
        sample_auto_eval: dict,  # type: ignore[type-arg]
    ) -> None:
        reports_dir = repo_root / "reports"
        ann_path = reports_dir / "case_001.auto_evaluation.json"
        ann_path.write_text(json.dumps(sample_auto_eval), encoding="utf-8")

        result = get_auto_eval_for_case("case_001", repo_root)
        assert result is not None
        assert result["case_id"] == "case_001"

    def test_prefers_reports_over_runs(
        self,
        repo_root: Path,
        sample_auto_eval: dict,  # type: ignore[type-arg]
    ) -> None:
        # Write different data to reports/ vs runs/
        reports_copy = dict(sample_auto_eval)
        reports_copy["rubric_version"] = "from_reports"

        run_copy = dict(sample_auto_eval)
        run_copy["rubric_version"] = "from_runs"

        reports_dir = repo_root / "reports"
        (reports_dir / "case_001.auto_evaluation.json").write_text(
            json.dumps(reports_copy), encoding="utf-8"
        )

        run_dir = repo_root / "runs" / "run_001"
        run_dir.mkdir(parents=True)
        (run_dir / "case_001.auto_evaluation.json").write_text(
            json.dumps(run_copy), encoding="utf-8"
        )

        result = get_auto_eval_for_case("case_001", repo_root)
        assert result is not None
        assert result["rubric_version"] == "from_reports"

    def test_falls_back_to_runs_when_no_reports_file(
        self,
        repo_root: Path,
        sample_auto_eval: dict,  # type: ignore[type-arg]
    ) -> None:
        run_dir = repo_root / "runs" / "run_001"
        run_dir.mkdir(parents=True)
        (run_dir / "case_001.auto_evaluation.json").write_text(
            json.dumps(sample_auto_eval), encoding="utf-8"
        )

        result = get_auto_eval_for_case("case_001", repo_root)
        assert result is not None
        assert result["case_id"] == "case_001"
