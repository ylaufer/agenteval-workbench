# Security Model

Telemetry is sensitive by default.

## Controls
- redact before report generation
- do not commit raw production traces
- local sanitized fixtures only
- fail closed on missing config
- no live secrets in config or fixtures
