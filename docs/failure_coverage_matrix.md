# Failure Coverage Matrix

## Coverage Table

| Failure Category                | Covered | Case IDs |
|----------------------------------|---------|----------|
| Tool Hallucination               | Yes     | 001, 003 |
| Unnecessary Tool Invocation      | Yes     | 002 |
| Tool Schema Misuse               | Yes     | 003 |
| Tool Output Misinterpretation    | Yes     | 004 |
| Instruction Drift                | Yes     | 005 |
| Partial Completion               | Yes     | 006 |
| Constraint Violation             | Yes     | 007 |
| Format Violation                 | Yes     | 008 |
| Reasoning Inconsistency          | Yes     | 009 |
| Unsafe Output                    | Yes     | 010 |
| Sensitive Data Exposure          | No      | — |
| UI Grounding Mismatch            | No      | — |

---

## Coverage Status Summary

Total Failure Categories Defined: 12  
Primary Failure Categories Covered: 10  
Remaining Categories: 2  

Benchmark coverage is comprehensive across tool use, reasoning integrity, instruction fidelity, structure compliance, and safety enforcement.
