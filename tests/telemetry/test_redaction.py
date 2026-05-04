from pathlib import Path

import pytest

from agenteval.telemetry.loader import load_trace
from agenteval.telemetry.models import SpanRecord, TraceEnvelope
from agenteval.telemetry.redaction import load_redaction_rules, redact_trace


_RULES_PATH = Path("config/telemetry_redaction_rules.yaml")


def _trace_with_attrs(**attrs) -> TraceEnvelope:  # type: ignore[no-untyped-def]
    span = SpanRecord("s1", None, "http.server:/ask", "gw", "SERVER", 0, 10, attrs)
    return TraceEnvelope("t1", "simple_rag_query", "s1", [span])


def test_redaction_applies() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    rules = load_redaction_rules(_RULES_PATH)
    redacted = redact_trace(trace, rules)
    attrs = redacted.spans[0].attributes
    assert "Bearer test-secret" not in str(attrs)
    assert "alice@example.com" not in str(attrs)


def test_redaction_path_patterns_direct_key_hit() -> None:
    # 'headers.authorization' path_pattern should be replaced wholesale
    trace = _trace_with_attrs(headers={"authorization": "Bearer my-secret-token"})
    rules = load_redaction_rules(_RULES_PATH)
    redacted = redact_trace(trace, rules)
    assert redacted.spans[0].attributes["headers"]["authorization"] == "[REDACTED]"


def test_redaction_email_regex_in_string_value() -> None:
    trace = _trace_with_attrs(user="hello bob@example.com end")
    rules = load_redaction_rules(_RULES_PATH)
    redacted = redact_trace(trace, rules)
    assert "bob@example.com" not in redacted.spans[0].attributes["user"]
    assert "[REDACTED_EMAIL]" in redacted.spans[0].attributes["user"]


def test_redaction_list_attribute_values() -> None:
    trace = _trace_with_attrs(emails=["alice@example.com", "bob@example.com"])
    rules = load_redaction_rules(_RULES_PATH)
    redacted = redact_trace(trace, rules)
    for val in redacted.spans[0].attributes["emails"]:
        assert "@example.com" not in val


def test_redaction_non_string_scalar_passthrough() -> None:
    trace = _trace_with_attrs(count=42, flag=True)
    rules = load_redaction_rules(_RULES_PATH)
    redacted = redact_trace(trace, rules)
    assert redacted.spans[0].attributes["count"] == 42
    assert redacted.spans[0].attributes["flag"] is True


def test_redaction_does_not_mutate_original() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    original_auth = trace.spans[0].attributes["headers"]["authorization"]
    rules = load_redaction_rules(_RULES_PATH)
    redact_trace(trace, rules)
    assert trace.spans[0].attributes["headers"]["authorization"] == original_auth


def test_redaction_sensitive_fixture() -> None:
    trace = load_trace(Path("fixtures/traces/malformed_trace_sensitive_data.json"))
    rules = load_redaction_rules(_RULES_PATH)
    redacted = redact_trace(trace, rules)
    result_str = str(redacted.spans[0].attributes)
    assert "secret123" not in result_str
    assert "bob@example.com" not in result_str


def test_redaction_fails_closed_on_empty_rules() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    with pytest.raises(ValueError, match="redaction rule"):
        redact_trace(trace, {"redaction_rules": []})


def test_redaction_fails_closed_on_missing_rules_key() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    with pytest.raises(ValueError, match="redaction rule"):
        redact_trace(trace, {})
