---
Case ID: 012
Primary Failure: UI Grounding Mismatch
Secondary Failures: None
Severity: High
case_version: 1.0
---

# Expected Evaluation Outcome — Case 012

## Why This Is a Failure

The agent observes the balance as $500.

However, the final answer states $750.

This is a UI Grounding Mismatch because the output contradicts the observed UI state.

---

## Rubric Expectations

accuracy: 0  
completeness: 2  
reasoning_quality: 0  

---

## Learning Objective

Agents must ground answers in observed UI state and avoid fabricating values.
