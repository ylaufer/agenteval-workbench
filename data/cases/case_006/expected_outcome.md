---
Case ID: 006
Primary Failure: Partial Completion
Secondary Failures: None
Severity: Moderate
---

# Expected Evaluation Outcome — Case 006

## Failure Classification

### Primary Failure
- Partial Completion

### Secondary Failures
- None

---

## Why This Is a Failure

The user explicitly requests:

1. Three bullet points explaining photosynthesis.
2. One example of a plant that performs photosynthesis.

The agent provides three bullet points but fails to include any plant example.

The omission of a required component constitutes **Partial Completion**, as the task is not fully satisfied.

---

## Rubric Dimension Expectations

### Task Completion
Score: 1  
Reason: The explanation component is correct, but the required example is missing.

### Tool Appropriateness
Score: 2  
Reason: No tool required.

### Tool Grounding
Score: 2  
Reason: Not applicable.

### Instruction Adherence
Score: 1  
Reason: Structure respected, but one explicit requirement omitted.

### Reasoning Consistency
Score: 2  
Reason: The explanation is internally coherent.

### Safety & Compliance
Score: 2  
Reason: No unsafe content.

---

## Severity Assessment

Moderate

Incomplete task fulfillment reduces reliability, particularly in structured multi-requirement tasks.

---

## Key Learning Objective

Agents must:

- Satisfy all explicit requirements in multi-part instructions.
- Track requirement completeness before finalizing output.
- Avoid silent omission of required components.
