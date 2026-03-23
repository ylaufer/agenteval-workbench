from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict

import pytest

from agenteval.core.runs import (
    complete_run,
    create_run,
    fail_run,
    generate_run_id,
    get_run,
    get_run_dir,
    get_run_results,
    get_run_summary,
    list_runs,
    main_inspect,
    main_list,
)
from agenteval.core.types import RunStatus


# ---------------------------------------------------------------------------
# generate_run_id
# ---------------------------------------------------------------------------


class TestGenerateRunId:
    def test_format_matches_pattern(self) -> None:
        run_id = generate_run_id()
        assert re.match(r"^\d{8}T\d{6}_[0-9a-f]{4}$", run_id), f"Bad format: {run_id}"

    def test_unique_ids(self) -> None:
        ids = {generate_run_id() for _ in range(50)}
        assert len(ids) >= 2  # At least some should differ (suffix is random)


# ---------------------------------------------------------------------------
# create_run / complete_run / fail_run
# ---------------------------------------------------------------------------


class TestRunLifecycle:
    def test_create_run_creates_directory_and_json(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        assert record.status == RunStatus.RUNNING.value
        assert record.num_cases == 0
        assert record.completed_at is None
        assert record.error is None

        run_dir = get_run_dir(record.run_id)
        assert run_dir.exists()
        assert (run_dir / "run.json").exists()

        data = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        assert data["run_id"] == record.run_id
        assert data["status"] == "running"

    def test_complete_run_updates_status(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        completed = complete_run(record.run_id, num_cases=12)

        assert completed.status == RunStatus.COMPLETED.value
        assert completed.num_cases == 12
        assert completed.completed_at is not None
        assert completed.error is None

    def test_fail_run_updates_status(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        failed = fail_run(record.run_id, error="Trace validation failed", num_cases=3)

        assert failed.status == RunStatus.FAILED.value
        assert failed.num_cases == 3
        assert failed.error == "Trace validation failed"
        assert failed.completed_at is None

    def test_complete_run_missing_raises(self, repo_root_env: Path) -> None:
        with pytest.raises(FileNotFoundError):
            complete_run("nonexistent_id", num_cases=0)

    def test_fail_run_missing_raises(self, repo_root_env: Path) -> None:
        with pytest.raises(FileNotFoundError):
            fail_run("nonexistent_id", error="error")


# ---------------------------------------------------------------------------
# get_run
# ---------------------------------------------------------------------------


class TestGetRun:
    def test_returns_record(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        fetched = get_run(record.run_id)
        assert fetched is not None
        assert fetched.run_id == record.run_id

    def test_returns_none_for_missing(self, repo_root_env: Path) -> None:
        result = get_run("nonexistent_id")
        assert result is None


# ---------------------------------------------------------------------------
# list_runs
# ---------------------------------------------------------------------------


class TestListRuns:
    def test_empty_returns_empty(self, repo_root_env: Path) -> None:
        result = list_runs()
        assert result == []

    def test_lists_in_reverse_chronological(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        r1 = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        time.sleep(0.05)
        r2 = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)

        runs = list_runs()
        assert len(runs) == 2
        assert runs[0].run_id == r2.run_id
        assert runs[1].run_id == r1.run_id

    def test_skips_corrupted_run_json(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)

        # Create a corrupted run directory
        bad_dir = repo_root_env / "runs" / "bad_run"
        bad_dir.mkdir(parents=True)
        (bad_dir / "run.json").write_text("not valid json", encoding="utf-8")

        runs = list_runs()
        assert len(runs) == 1  # Only the valid run

    def test_skips_dir_without_run_json(self, repo_root_env: Path) -> None:
        runs_dir = repo_root_env / "runs"
        runs_dir.mkdir(parents=True)
        (runs_dir / "orphan_dir").mkdir()

        runs = list_runs()
        assert runs == []


# ---------------------------------------------------------------------------
# get_run_results / get_run_summary
# ---------------------------------------------------------------------------


class TestRunResults:
    def test_returns_empty_for_missing_run(self, repo_root_env: Path) -> None:
        result = get_run_results("nonexistent_id")
        assert result == []

    def test_returns_evaluation_files(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        run_dir = get_run_dir(record.run_id)

        # Write mock evaluation files
        eval_data = {"case_id": "case_001", "primary_failure": "Tool Hallucination"}
        (run_dir / "case_001.evaluation.json").write_text(
            json.dumps(eval_data), encoding="utf-8"
        )

        results = get_run_results(record.run_id)
        assert len(results) == 1
        assert results[0]["case_id"] == "case_001"

    def test_excludes_summary(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        run_dir = get_run_dir(record.run_id)

        (run_dir / "case_001.evaluation.json").write_text(
            json.dumps({"case_id": "case_001"}), encoding="utf-8"
        )
        (run_dir / "summary.evaluation.json").write_text(
            json.dumps({"summary": True}), encoding="utf-8"
        )

        results = get_run_results(record.run_id)
        assert len(results) == 1
        assert results[0]["case_id"] == "case_001"


class TestRunSummary:
    def test_returns_none_for_missing(self, repo_root_env: Path) -> None:
        result = get_run_summary("nonexistent_id")
        assert result is None

    def test_returns_summary_dict(self, repo_root_env: Path) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        run_dir = get_run_dir(record.run_id)

        summary_data: Dict[str, Any] = {"summary": {"total_cases": 5}}
        (run_dir / "summary.evaluation.json").write_text(
            json.dumps(summary_data), encoding="utf-8"
        )

        result = get_run_summary(record.run_id)
        assert result is not None
        assert result["summary"]["total_cases"] == 5


# ---------------------------------------------------------------------------
# CLI entry points
# ---------------------------------------------------------------------------


class TestCLIList:
    def test_empty_state_message(self, repo_root_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main_list([])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert "No evaluation runs found" in captured.out

    def test_lists_runs(self, repo_root_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        complete_run(record.run_id, num_cases=5)

        exit_code = main_list([])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert record.run_id in captured.out
        assert "completed" in captured.out


class TestCLIInspect:
    def test_not_found(self, repo_root_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main_inspect(["20260101T000000_0000"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_inspect_run(self, repo_root_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
        dataset_dir = repo_root_env / "data" / "cases"
        dataset_dir.mkdir(parents=True)
        rubric_path = repo_root_env / "rubrics" / "v1_agent_general.json"

        record = create_run(dataset_dir=dataset_dir, rubric_path=rubric_path)
        complete_run(record.run_id, num_cases=3)

        exit_code = main_inspect([record.run_id])
        assert exit_code == 0
        captured = capsys.readouterr()
        assert record.run_id in captured.out
        assert "completed" in captured.out
        assert "Cases evaluated: 3" in captured.out
