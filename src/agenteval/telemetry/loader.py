from __future__ import annotations

import json
from pathlib import Path

from .models import SpanRecord, TraceEnvelope


def load_trace(path: str | Path) -> TraceEnvelope:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    spans = [SpanRecord(**span) for span in payload["spans"]]
    return TraceEnvelope(
        trace_id=payload["trace_id"],
        journey=payload["journey"],
        root_span_id=payload["root_span_id"],
        spans=spans,
    )
