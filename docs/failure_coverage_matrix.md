# Failure Coverage Matrix

This document defines the coverage strategy for benchmark cases across the official Failure Taxonomy.

Its purpose is to:

- Ensure systematic failure coverage
- Identify taxonomy gaps
- Prevent untested failure classes
- Support evaluation completeness
- Enable future coverage expansion

---

# 1. Coverage Objective

The benchmark dataset must:

- Cover all primary failure categories
- Include at least one canonical case per major failure class
- Explicitly map each case to a defined taxonomy category
- Avoid orphan taxonomy categories with no benchmark coverage

---

# 2. Failure Taxonomy Coverage Table

| Failure Category                | Covered | Case IDs | Notes |
|----------------------------------|---------|----------|------|
| Tool Hallucination               | Yes     | 001, 003 | 001: fabricated tool output after failure; 003: false success after tool schema error |
| Unnecessary Tool Invocation      | Yes     | 002      | Tool used for trivial arithmetic |
| Tool Schema Misuse               | Yes     | 003      | Incorrect parameters cause schema validation error |
| Tool Output Misinterpretation    | Yes     | 004      | Tool returns valid status but agent interprets it incorrectly |
| Instruction Drift                | No      | —        | Planned Case 005 |
| Partial Completion               | No      | —        | Planned Case 006 |
| Constraint Violation             | Yes*    | 001      | Secondary/implicit integrity breach |
| Format Violation                 | No      | —        | Planned Case 008 |
| Reasoning Inconsistency          | Yes*    | 004      | Secondary: conclusion contradicts tool output |
| Latency Mismanagement            | Yes*    | 002      | Secondary classification only |
| Unsafe Output                    | No      | —        | Planned Case 010 |
| Sensitive Data Exposure          | No      | —        | Future security case |
| UI Grounding Mismatch            | No      | —        | Future multimodal case |

*Latency Mismanagement currently appears as a secondary failure only.

---

# 3. Coverage Status Summary

Total Failure Categories Defined: 13  
Primary Failure Categories Covered: 4  
Secondary Coverage Categories Present: 3  
Remaining Categories to Implement: 7  

Coverage is currently partial and expanding.

---

# 4. Planned Case Roadmap

| Planned Case | Target Failure Category |
|--------------|------------------------|
| Case 005     | Instruction Drift |
| Case 006     | Partial Completion |
| Case 007     | Constraint Violation |
| Case 008     | Format Violation |
| Case 009     | Reasoning Inconsistency |
| Case 010     | Unsafe Output |

---

# 5. Coverage Design Principles

Coverage must:

- Include canonical, easily classifiable failures
- Minimize ambiguity between categories
- Avoid overlapping primary failure definitions
- Allow multi-failure tagging where appropriate
- Prioritize high-severity categories first

---

# 6. Governance Policy

When a new failure category is introduced:

1. The taxonomy must be updated.
2. A canonical benchmark case must be added.
3. The coverage matrix must be updated.
4. CI validation must remain unaffected.

Coverage gaps should be visible and intentional — never accidental.

---

# 7. Evaluation Integrity Impact

Failure coverage ensures:

- Robust evaluation standards
- Balanced benchmark representation
- Reduced blind spots in agent assessment
- Scalable failure pattern mining
- Consistent evaluator expectations

The coverage matrix transforms the dataset from a collection of examples into a controlled evaluation instrument.
