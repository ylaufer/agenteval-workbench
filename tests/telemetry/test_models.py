from agenteval.telemetry.models import SpanRecord, TraceEnvelope


def test_models_basic_construction() -> None:
    span = SpanRecord("s1", None, "http.server:/ask", "gateway", "SERVER", 0, 1, {})
    trace = TraceEnvelope("t1", "simple_rag_query", "s1", [span])
    assert trace.root_span_id == "s1"
