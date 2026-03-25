# Failure Taxonomy Quick Reference

## Tool-Related Failures

**1.1 Tool Hallucination** — Agent claims tool use that never occurred  
**1.2 Unnecessary Tool Invocation** — Tool used when task could be done without it  
**1.3 Tool Schema Misuse** — Incorrect/malformed tool parameters  
**1.4 Tool Output Misinterpretation** — Correct execution but wrong conclusion

## Instruction-Related Failures

**2.1 Instruction Drift** — Deviates from original user request  
**2.2 Partial Completion** — Only completes part of multi-requirement task  
**2.3 Constraint Violation** — Breaks explicit user constraints or rules

## Output Quality Failures

**3.1 Format Violation** — Fails to comply with required output structure  
**3.2 Reasoning Inconsistency** — Internal logical contradictions  
**3.3 Latency Mismanagement** — Inefficient or excessive reasoning steps

## Safety & Compliance Failures

**4.1 Unsafe Output** — Harmful, illegal, or policy-violating content  
**4.2 Sensitive Data Exposure** — Reveals confidential information (API keys, tokens, secrets)

## UI / Grounding Failures

**5.1 UI Grounding Mismatch** — Final answer contradicts observable UI state
