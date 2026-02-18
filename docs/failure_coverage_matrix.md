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
| Tool Hallucination               | Yes     | 001, 003 | 001: fabricated tool output; 003: false success after schema error |
| Unnecessary Tool Invocation      | Yes     | 002      | Tool used for trivial arithmetic |
| Tool Schema Misuse               | Yes     | 003      | Incorrect parameters cause validation error |
| Tool Output Misinterpretation    | Yes     | 004      | Tool returns valid status but agent misinterprets it |
| Instruction Drift                | Yes     | 005      | Violates explicit length and content constraints |
| Partial Completion               | No      | —        | Planned Case 006 |
| Constraint Violation             | Yes*    | 001, 005 | Secondary failures (integrity / constraint breach) |
| Format Violation                 | No      | —        | Planned Case 008 |
| Reasoning Inconsistency          | Yes*    | 004      | Secondary: contradiction with tool output |
| Latency Mismanagement            | Yes*    | 002      | Secondary classification only |
| Unsafe Output                    | No      | —        | Planned Case 010 |
| Sensitive Data Exposure          | No      | —        | Future security case |
| UI Grounding Mismatch            | No      | —        | Future multimodal case |


*Categories marked with an asterisk currently appear only as secondary failures and do not yet have a canonical primary benchmark case.


---

# 3. Coverage Status Summary

Total Failure Categories Defined: 13  
Primary Failure Categories Covered: 5  
Secondary Coverage Categories Present: 4  
Remaining Categories to Implement: 6  

Coverage is systematically expanding.

---

# 4. Planned Case Roadmap

| Planned Case | Target Failure Category |
|--------------|------------------------|
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
