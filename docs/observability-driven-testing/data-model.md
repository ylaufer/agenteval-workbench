# Data Model

## TraceEnvelope
- trace_id
- journey
- root_span_id
- spans

## SpanRecord
- span_id
- parent_span_id
- name
- service
- kind
- start_ms
- end_ms
- attributes

## ConformanceResult
- journey
- passed
- failures
- metrics
