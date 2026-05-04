from pathlib import Path

from agenteval.telemetry.loader import load_trace
from agenteval.telemetry.redaction import load_redaction_rules, redact_trace


def test_redaction_applies() -> None:
    trace = load_trace(Path("fixtures/traces/sample_trace.json"))
    rules = load_redaction_rules(Path("config/telemetry_redaction_rules.yaml"))
    redacted = redact_trace(trace, rules)
    attrs = redacted.spans[0].attributes
    assert "Bearer test-secret" not in str(attrs)
    assert "alice@example.com" not in str(attrs)
