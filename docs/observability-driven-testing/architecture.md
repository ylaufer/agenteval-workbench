# Architecture

The telemetry extension adds an offline-first observability-driven testing capability to AgentEval.

## Flow
1. Load local JSON trace fixture
2. Normalize into typed internal model
3. Redact sensitive values
4. Validate semantic and structural rules
5. Load journey invariants from YAML
6. Evaluate conformance
7. Produce markdown and JSON reports

## Boundaries
- No live telemetry sources in the MVP
- No network access required
- No raw secret persistence
