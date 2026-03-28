from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from agenteval.core.filtering import derive_structural_tags, filter_cases, get_dataset_tags


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_trace(steps: list[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    """Return a minimal valid trace dict."""
    return {
        "trace_id": "test-001",
        "session_id": "s1",
        "agent_id": "agent",
        "task": "test",
        "steps": steps or [],
        "final_status": "success",
    }


def _make_step(step_id: str, step_type: str, **kwargs: Any) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "step_id": step_id,
        "type": step_type,
        "actor_id": "agent",
        "content": "content",
    }
    base.update(kwargs)
    return base


def _write_trace(case_dir: Path, trace: Dict[str, Any]) -> None:
    (case_dir / "trace.json").write_text(json.dumps(trace), encoding="utf-8")


def _write_outcome(
    case_dir: Path,
    primary_failure: str = "Tool Hallucination",
    severity: str = "Critical",
    tags: str = "[]",
    notes: str = '""',
) -> None:
    (case_dir / "expected_outcome.md").write_text(
        f"---\nprimary_failure: {primary_failure}\nseverity: {severity}\n"
        f"tags: {tags}\nnotes: {notes}\n---\n",
        encoding="utf-8",
    )


def _make_case(
    tmp_path: Path,
    name: str,
    steps: list[Dict[str, Any]] | None = None,
    primary_failure: str = "Tool Hallucination",
    severity: str = "Critical",
    write_trace: bool = True,
    write_outcome: bool = True,
) -> Path:
    """Create a minimal case directory under tmp_path."""
    case_dir = tmp_path / name
    case_dir.mkdir(parents=True, exist_ok=True)
    if write_trace:
        _write_trace(case_dir, _make_trace(steps))
    if write_outcome:
        _write_outcome(case_dir, primary_failure=primary_failure, severity=severity)
    return case_dir


# ---------------------------------------------------------------------------
# derive_structural_tags
# ---------------------------------------------------------------------------


class TestDeriveStructuralTags:
    def test_tool_call_step_returns_has_tool_calls(self) -> None:
        trace = _make_trace(
            [
                _make_step("s1", "tool_call", tool_name="search"),
                _make_step("s2", "final_answer"),
            ]
        )
        tags = derive_structural_tags(trace)  # type: ignore[arg-type]
        assert "has_tool_calls" in tags

    def test_more_than_three_steps_returns_multi_step(self) -> None:
        steps = [_make_step(f"s{i}", "thought") for i in range(4)]
        trace = _make_trace(steps)
        tags = derive_structural_tags(trace)  # type: ignore[arg-type]
        assert "multi_step" in tags

    def test_exactly_three_steps_not_multi_step(self) -> None:
        steps = [_make_step(f"s{i}", "thought") for i in range(3)]
        trace = _make_trace(steps)
        tags = derive_structural_tags(trace)  # type: ignore[arg-type]
        assert "multi_step" not in tags

    def test_final_answer_step_returns_has_final_answer(self) -> None:
        trace = _make_trace(
            [
                _make_step("s1", "thought"),
                _make_step("s2", "final_answer"),
            ]
        )
        tags = derive_structural_tags(trace)  # type: ignore[arg-type]
        assert "has_final_answer" in tags

    def test_all_three_conditions_returns_all_tags(self) -> None:
        steps = [
            _make_step("s1", "thought"),
            _make_step("s2", "tool_call", tool_name="x"),
            _make_step("s3", "observation", tool_output="data"),
            _make_step("s4", "final_answer"),
        ]
        trace = _make_trace(steps)
        tags = derive_structural_tags(trace)  # type: ignore[arg-type]
        assert "has_tool_calls" in tags
        assert "multi_step" in tags
        assert "has_final_answer" in tags

    def test_empty_steps_returns_empty_tuple(self) -> None:
        trace = _make_trace([])
        tags = derive_structural_tags(trace)  # type: ignore[arg-type]
        assert tags == ()

    def test_returns_tuple(self) -> None:
        trace = _make_trace([])
        result = derive_structural_tags(trace)  # type: ignore[arg-type]
        assert isinstance(result, tuple)

    def test_no_tool_call_no_tag(self) -> None:
        trace = _make_trace([_make_step("s1", "thought")])
        tags = derive_structural_tags(trace)  # type: ignore[arg-type]
        assert "has_tool_calls" not in tags

    def test_no_final_answer_no_tag(self) -> None:
        trace = _make_trace([_make_step("s1", "thought")])
        tags = derive_structural_tags(trace)  # type: ignore[arg-type]
        assert "has_final_answer" not in tags


# ---------------------------------------------------------------------------
# get_dataset_tags
# ---------------------------------------------------------------------------


class TestGetDatasetTags:
    def test_returns_union_of_tags_across_cases(self, tmp_path: Path) -> None:
        # case_a: has tool_call → has_tool_calls
        case_a = _make_case(
            tmp_path,
            "case_a",
            steps=[
                _make_step("s1", "tool_call", tool_name="t"),
                _make_step("s2", "observation", tool_output="data"),
                _make_step("s3", "final_answer"),
            ],
        )
        # case_b: has final_answer only
        case_b = _make_case(
            tmp_path,
            "case_b",
            steps=[_make_step("s1", "final_answer")],
        )
        all_tags = get_dataset_tags([case_a, case_b])
        assert isinstance(all_tags, set)
        assert "has_tool_calls" in all_tags
        assert "has_final_answer" in all_tags

    def test_skips_missing_trace_json(self, tmp_path: Path) -> None:
        # case with no trace.json at all
        case_dir = tmp_path / "case_no_trace"
        case_dir.mkdir()
        _write_outcome(case_dir)
        # Should return empty set, not raise
        result = get_dataset_tags([case_dir])
        assert isinstance(result, set)

    def test_skips_unreadable_trace_json(self, tmp_path: Path) -> None:
        case_dir = tmp_path / "case_bad_trace"
        case_dir.mkdir()
        (case_dir / "trace.json").write_text("not valid json {{{{", encoding="utf-8")
        # Should return empty set, not raise
        result = get_dataset_tags([case_dir])
        assert isinstance(result, set)

    def test_empty_case_list_returns_empty_set(self) -> None:
        result = get_dataset_tags([])
        assert result == set()

    def test_mixed_valid_and_missing(self, tmp_path: Path) -> None:
        # One valid case, one missing trace
        valid = _make_case(
            tmp_path,
            "valid",
            steps=[_make_step("s1", "final_answer")],
        )
        missing = tmp_path / "missing"
        missing.mkdir()
        result = get_dataset_tags([valid, missing])
        assert "has_final_answer" in result


# ---------------------------------------------------------------------------
# filter_cases
# ---------------------------------------------------------------------------


class TestFilterCasesNoFilters:
    def test_no_filters_returns_all_cases(self, tmp_path: Path) -> None:
        case_a = _make_case(tmp_path, "case_a")
        case_b = _make_case(tmp_path, "case_b")
        result = filter_cases([case_a, case_b])
        assert set(result) == {case_a, case_b}

    def test_empty_input_returns_empty(self) -> None:
        result = filter_cases([])
        assert result == []


class TestFilterCasesByCaseIds:
    def test_case_ids_returns_only_matching(self, tmp_path: Path) -> None:
        case_a = _make_case(tmp_path, "case_a")
        case_b = _make_case(tmp_path, "case_b")
        case_c = _make_case(tmp_path, "case_c")
        result = filter_cases([case_a, case_b, case_c], case_ids=["case_a", "case_c"])
        assert set(result) == {case_a, case_c}

    def test_case_ids_overrides_other_filters(self, tmp_path: Path) -> None:
        case_a = _make_case(tmp_path, "case_a", primary_failure="Tool Hallucination")
        case_b = _make_case(tmp_path, "case_b", primary_failure="Format Violation")
        # Passing failure_type that would exclude case_a, but case_ids takes precedence
        result = filter_cases(
            [case_a, case_b],
            case_ids=["case_a"],
            failure_type="Format Violation",
        )
        assert result == [case_a]

    def test_case_ids_no_match_returns_empty(self, tmp_path: Path) -> None:
        case_a = _make_case(tmp_path, "case_a")
        result = filter_cases([case_a], case_ids=["nonexistent"])
        assert result == []

    def test_empty_case_ids_treated_as_no_filter(self, tmp_path: Path) -> None:
        # Empty list is falsy — all cases returned
        case_a = _make_case(tmp_path, "case_a")
        result = filter_cases([case_a], case_ids=[])
        assert result == [case_a]


class TestFilterCasesByFailureType:
    def test_failure_type_matches_primary_failure(self, tmp_path: Path) -> None:
        match = _make_case(tmp_path, "case_match", primary_failure="Tool Hallucination")
        no_match = _make_case(tmp_path, "case_no_match", primary_failure="Format Violation")
        result = filter_cases([match, no_match], failure_type="Tool Hallucination")
        assert result == [match]

    def test_failure_type_case_insensitive(self, tmp_path: Path) -> None:
        case_dir = _make_case(tmp_path, "case_a", primary_failure="Tool Hallucination")
        result = filter_cases([case_dir], failure_type="tool hallucination")
        assert result == [case_dir]

    def test_failure_type_missing_outcome_excludes_case(self, tmp_path: Path) -> None:
        case_dir = _make_case(tmp_path, "case_a", write_outcome=False)
        result = filter_cases([case_dir], failure_type="Tool Hallucination")
        assert result == []

    def test_failure_type_no_match_returns_empty(self, tmp_path: Path) -> None:
        case_dir = _make_case(tmp_path, "case_a", primary_failure="Format Violation")
        result = filter_cases([case_dir], failure_type="Tool Hallucination")
        assert result == []


class TestFilterCasesBySeverity:
    def test_severity_matches_case(self, tmp_path: Path) -> None:
        critical = _make_case(tmp_path, "case_crit", severity="Critical")
        low = _make_case(tmp_path, "case_low", severity="Low")
        result = filter_cases([critical, low], severity=["Critical"])
        assert result == [critical]

    def test_severity_case_insensitive(self, tmp_path: Path) -> None:
        case_dir = _make_case(tmp_path, "case_a", severity="Critical")
        result = filter_cases([case_dir], severity=["critical"])
        assert result == [case_dir]

    def test_severity_matches_any_in_list(self, tmp_path: Path) -> None:
        high = _make_case(tmp_path, "case_high", severity="High")
        critical = _make_case(tmp_path, "case_crit", severity="Critical")
        low = _make_case(tmp_path, "case_low", severity="Low")
        result = filter_cases([high, critical, low], severity=["High", "Critical"])
        assert set(result) == {high, critical}

    def test_severity_missing_outcome_excludes_case(self, tmp_path: Path) -> None:
        case_dir = _make_case(tmp_path, "case_a", write_outcome=False)
        result = filter_cases([case_dir], severity=["Critical"])
        assert result == []

    def test_severity_no_match_returns_empty(self, tmp_path: Path) -> None:
        case_dir = _make_case(tmp_path, "case_a", severity="Low")
        result = filter_cases([case_dir], severity=["Critical"])
        assert result == []


class TestFilterCasesByTags:
    def test_tags_case_must_have_all_listed_tags(self, tmp_path: Path) -> None:
        multi = _make_case(
            tmp_path,
            "case_multi",
            steps=[
                _make_step("s1", "thought"),
                _make_step("s2", "tool_call", tool_name="t"),
                _make_step("s3", "observation", tool_output="d"),
                _make_step("s4", "final_answer"),
            ],
        )
        single = _make_case(
            tmp_path,
            "case_single",
            steps=[_make_step("s1", "tool_call", tool_name="t")],
        )
        # multi has both has_tool_calls and multi_step; single only has_tool_calls
        result = filter_cases([multi, single], tags=["has_tool_calls", "multi_step"])
        assert result == [multi]

    def test_tags_single_tag_filter(self, tmp_path: Path) -> None:
        with_final = _make_case(
            tmp_path,
            "case_final",
            steps=[_make_step("s1", "final_answer")],
        )
        without_final = _make_case(
            tmp_path,
            "case_no_final",
            steps=[_make_step("s1", "thought")],
        )
        result = filter_cases([with_final, without_final], tags=["has_final_answer"])
        assert result == [with_final]

    def test_tags_missing_trace_json_excludes_case(self, tmp_path: Path) -> None:
        case_dir = _make_case(tmp_path, "case_a", write_trace=False)
        result = filter_cases([case_dir], tags=["has_tool_calls"])
        assert result == []

    def test_tags_unreadable_trace_json_excludes_case(self, tmp_path: Path) -> None:
        case_dir = _make_case(tmp_path, "case_a", write_trace=False)
        (case_dir / "trace.json").write_text("{{bad json", encoding="utf-8")
        result = filter_cases([case_dir], tags=["has_tool_calls"])
        assert result == []

    def test_tags_no_match_returns_empty(self, tmp_path: Path) -> None:
        case_dir = _make_case(
            tmp_path,
            "case_a",
            steps=[_make_step("s1", "thought")],
        )
        result = filter_cases([case_dir], tags=["has_tool_calls"])
        assert result == []


class TestFilterCasesByPattern:
    def test_pattern_glob_matches_name(self, tmp_path: Path) -> None:
        case_001 = _make_case(tmp_path, "case_001")
        case_002 = _make_case(tmp_path, "case_002")
        other = _make_case(tmp_path, "other_case")
        result = filter_cases([case_001, case_002, other], pattern="case_0*")
        assert set(result) == {case_001, case_002}

    def test_pattern_no_match_returns_empty(self, tmp_path: Path) -> None:
        case_dir = _make_case(tmp_path, "case_a")
        result = filter_cases([case_dir], pattern="xyz_*")
        assert result == []

    def test_pattern_exact_match(self, tmp_path: Path) -> None:
        case_a = _make_case(tmp_path, "case_a")
        case_b = _make_case(tmp_path, "case_b")
        result = filter_cases([case_a, case_b], pattern="case_a")
        assert result == [case_a]


class TestFilterCasesAndLogic:
    def test_failure_type_and_severity_combined(self, tmp_path: Path) -> None:
        match = _make_case(
            tmp_path, "match", primary_failure="Tool Hallucination", severity="Critical"
        )
        wrong_sev = _make_case(
            tmp_path, "wrong_sev", primary_failure="Tool Hallucination", severity="Low"
        )
        wrong_failure = _make_case(
            tmp_path, "wrong_failure", primary_failure="Format Violation", severity="Critical"
        )
        result = filter_cases(
            [match, wrong_sev, wrong_failure],
            failure_type="Tool Hallucination",
            severity=["Critical"],
        )
        assert result == [match]

    def test_pattern_and_failure_type_combined(self, tmp_path: Path) -> None:
        case_001_match = _make_case(
            tmp_path, "case_001", primary_failure="Tool Hallucination"
        )
        case_002_wrong = _make_case(
            tmp_path, "case_002", primary_failure="Format Violation"
        )
        other_match = _make_case(
            tmp_path, "other_001", primary_failure="Tool Hallucination"
        )
        result = filter_cases(
            [case_001_match, case_002_wrong, other_match],
            failure_type="Tool Hallucination",
            pattern="case_*",
        )
        assert result == [case_001_match]

    def test_tags_and_failure_type_combined(self, tmp_path: Path) -> None:
        match = _make_case(
            tmp_path,
            "match",
            primary_failure="Tool Hallucination",
            steps=[_make_step("s1", "tool_call", tool_name="t")],
        )
        wrong_failure = _make_case(
            tmp_path,
            "wrong_failure",
            primary_failure="Format Violation",
            steps=[_make_step("s1", "tool_call", tool_name="t")],
        )
        wrong_tags = _make_case(
            tmp_path,
            "wrong_tags",
            primary_failure="Tool Hallucination",
            steps=[_make_step("s1", "thought")],
        )
        result = filter_cases(
            [match, wrong_failure, wrong_tags],
            failure_type="Tool Hallucination",
            tags=["has_tool_calls"],
        )
        assert result == [match]

    def test_all_filters_no_match_returns_empty(self, tmp_path: Path) -> None:
        case_dir = _make_case(
            tmp_path,
            "case_a",
            primary_failure="Tool Hallucination",
            severity="Critical",
            steps=[_make_step("s1", "thought")],
        )
        result = filter_cases(
            [case_dir],
            failure_type="Tool Hallucination",
            severity=["Critical"],
            tags=["has_tool_calls"],
            pattern="case_a",
        )
        assert result == []
