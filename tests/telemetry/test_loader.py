import json
from pathlib import Path

import pytest

from agenteval.telemetry.loader import load_trace


def test_load_trace() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    assert trace.trace_id == "trace-001"
    assert len(trace.spans) == 3


def test_load_trace_bad_types_raises() -> None:
    with pytest.raises(ValueError, match="must be an integer"):
        load_trace(Path("fixtures/traces/malformed_trace_bad_types.json"))


def test_load_trace_not_valid_json(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        load_trace(bad)


def test_load_trace_top_level_not_dict(tmp_path: Path) -> None:
    f = tmp_path / "t.json"
    f.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="must contain a JSON object"):
        load_trace(f)


def test_load_trace_missing_required_field(tmp_path: Path) -> None:
    f = tmp_path / "t.json"
    f.write_text(json.dumps({"trace_id": "x", "journey": "j", "root_span_id": "s1"}), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required field: 'spans'"):
        load_trace(f)


def test_load_trace_spans_not_list(tmp_path: Path) -> None:
    payload = {"trace_id": "x", "journey": "j", "root_span_id": "s1", "spans": "bad"}
    f = tmp_path / "t.json"
    f.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="'spans' must be a list"):
        load_trace(f)


def test_load_trace_span_missing_field(tmp_path: Path) -> None:
    payload = {
        "trace_id": "x", "journey": "j", "root_span_id": "s1",
        "spans": [{"span_id": "s1", "name": "op"}],  # missing service, kind, start_ms, end_ms
    }
    f = tmp_path / "t.json"
    f.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="missing required field"):
        load_trace(f)


def test_load_trace_span_not_dict(tmp_path: Path) -> None:
    payload = {"trace_id": "x", "journey": "j", "root_span_id": "s1", "spans": ["not-a-dict"]}
    f = tmp_path / "t.json"
    f.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        load_trace(f)


def test_load_trace_span_wrong_str_type(tmp_path: Path) -> None:
    payload = {
        "trace_id": "x", "journey": "j", "root_span_id": "s1",
        "spans": [{
            "span_id": 123,  # should be str
            "name": "op", "service": "svc", "kind": "INTERNAL",
            "start_ms": 0, "end_ms": 10,
        }],
    }
    f = tmp_path / "t.json"
    f.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="must be a string"):
        load_trace(f)
