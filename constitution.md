# Constitution

This repository is security-first.

## Non-negotiable rules

1. Never hardcode or commit secrets, API keys, passwords, bearer tokens, cookies, or credentials.
2. Never store raw production telemetry in the repository.
3. Treat all telemetry as sensitive by default.
4. Redact before persisting, exporting, or reporting.
5. Fail closed when required config for redaction or validation is missing.
6. Use local sanitized fixtures for the MVP. No live telemetry sources.
7. No network calls in tests for this module.
8. Keep changes additive and avoid breaking the existing AgentEval core.
9. Prefer deterministic, schema-driven validation over ad hoc parsing.
10. Security and privacy are release blockers for this capability.
