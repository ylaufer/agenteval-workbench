# Requirements

## Functional
- Load sanitized trace JSON
- Normalize traces into internal model
- Redact sensitive fields before persistence
- Validate semantic conventions
- Load journey invariants from YAML
- Evaluate conformance and generate markdown report

## Security
- No raw secret persistence
- No raw header persistence
- No raw email or customer identifier persistence
- Missing redaction config must fail execution

## Non-functional
- Python 3.11+
- Typed code
- Unit-testable modules
