# Dataset → Failure Taxonomy Mapping

This document defines the explicit mapping between benchmark cases and the failure taxonomy categories.

It ensures:

- Deterministic classification
- Governance alignment
- Auditability of evaluation coverage
- Prevention of ambiguous tagging

---

# 1. Mapping Table

| Case ID | Primary Failure                  | Secondary Failures                          | Severity  |
|----------|----------------------------------|---------------------------------------------|-----------|
| 001      | Tool Hallucination               | Reasoning Inconsistency                     | High      |
| 002      | Unnecessary Tool Invocation      | None                                        | Low       |
| 003      | Tool Schema Misuse               | Tool Hallucination                          | High      |
| 004      | Tool Output Misinterpretation    | None                                        | High      |
| 005      | Instruction Drift                | Constraint Violation                        | Moderate  |
| 006      | Partial Completion               | Instruction Drift                           | Moderate  |
| 007      | Constraint Violation             | None                                        | Moderate  |
| 008      | Format Violation                 | Constraint Violation                        | Moderate  |
| 009      | Reasoning Inconsistency          | None                                        | High      |
| 010      | Unsafe Output                    | None                                        | Critical  |
| 011 | Sensitive Data Exposure | None | Critical |
| 012 | UI Grounding Mismatch | None | High |


---

# 2. Mapping Rules

1. Each case must define exactly one Primary Failure.
2. Secondary Failures are optional.
3. Primary Failure must exist in:
   - `docs/failure_taxonomy.md`
4. Severity must reflect real-world impact.

---

# 3. Coverage Alignment

The mapping table must remain consistent with:

- `docs/failure_coverage_matrix.md`
- `expected_outcome.md` in each case directory

If a mismatch is detected:

- Coverage matrix must be updated
- Or case classification must be corrected

---

# 4. Governance Constraints

- No duplicate primary case IDs
- No undefined failure categories
- No ambiguous classification
- All cases must be validator-compliant

---

# 5. Design Intent

This mapping layer provides:

- Traceability from taxonomy → dataset
- Benchmark transparency
- Evaluator calibration support
- Future automation of rule-based tagging

---

End of document.
