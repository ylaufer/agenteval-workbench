---
Case ID: 007
Primary Failure: Constraint Violation
Secondary Failures: None
Severity: Moderate
---

# Expected Evaluation Outcome — Case 007

## Failure Classification

### Primary Failure
- Constraint Violation

### Secondary Failures
- None

---

## Why This Is a Failure

The user explicitly requests:

- Instructions for boiling an egg
- In exactly two sentences

The agent provides four sentences instead of two.

The instructions themselves are correct, but the explicit constraint on sentence count is violated.

This constitutes a **Constraint Violation**, as the output fails to comply with a clearly defined structural requirement.

---

## Rubric Dimension Expectations

### Task Completion
Score: 1  
Reason: The instructions are correct but violate the required format constraint.

### Tool Appropriateness
Score: 2  
Reason: No tool required.

### Tool Grounding
Score: 2  
Reason: Not applicable.

### Instruction Adherence
Score: 0  
Reason: Explicit structural constraint not respected.

### Reasoning Consistency
Score: 2  
Reason: The instructions are coherent.

### Safety & Compliance
Score: 2  
Reason: No unsafe content.

---

## Severity Assessment

Moderate

Constraint violations reduce reliability in structured or regulated output contexts.

---

## Key Learning Objective

Agents must:

- Respect explicit structural constraints.
- Validate output length before finalizing.
- Treat formatting rules as hard requirements.
