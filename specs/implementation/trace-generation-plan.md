# Implementation Plan: Trace Generation

## Modules

- core/execution.py → agent execution
- scripts/generate_trace.py → CLI entrypoint

---

## Steps

1. Create execution module
2. Implement demo agent runner
3. Generate valid trace structure
4. Save trace to dataset path
5. Validate trace with schema
6. Run existing evaluation pipeline

---

## Risks

- Trace schema mismatch
- Missing required fields
- Inconsistent step structure

---

## Validation

- Load trace with `load_trace`
- Run runner.py successfully
- Generate evaluation report