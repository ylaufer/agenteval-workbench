# UI Contract: Guided Onboarding

## Welcome Modal

**When**: First app launch (preferences.first_run_complete == False)

**Content**:
```
┌─────────────────────────────────────────────────────────────┐
│ Welcome to AgentEval Workbench                              │
│                                                             │
│ This tool helps you evaluate LLM agent performance using   │
│ structured rubrics and failure taxonomies.                 │
│                                                             │
│ Get started in 60 seconds:                                 │
│                                                             │
│  [▶ Run Demo]    [Skip Tutorial]                          │
│                                                             │
│  The demo will:                                            │
│  • Generate a sample benchmark case                        │
│  • Validate it against the schema                          │
│  • Run the evaluation pipeline                             │
│  • Show you an annotated report                            │
└─────────────────────────────────────────────────────────────┘
```

**Actions**:
- **Run Demo**: Sets demo_in_progress = True, closes modal, starts demo workflow
- **Skip Tutorial**: Sets tutorial_skipped = True, first_run_complete = True, closes modal

**Persistence**: Choice saved to ~/.agenteval/preferences.json

---

## Demo Flow

**Trigger**: User clicks "Run Demo" button

**Progress Display**:
```
Running Demo Workflow...

├─ [✓] Generating case...
├─ [▶] Validating dataset...
├─ [ ] Running evaluation...
└─ [ ] Generating report...

Status: Validating 12 cases...
```

**Stages**:

1. **Generate Case** (0-25% progress)
   - Call: `generate_case(case_id="demo_001", failure_type="tool_hallucination")`
   - Display: "Generating demo case with tool hallucination failure..."
   - Success: Show checkmark, proceed to validation

2. **Validate Dataset** (25-50% progress)
   - Call: `validate_dataset(repo_root=".")`
   - Display: "Validating dataset structure and security constraints..."
   - Success: Show checkmark, proceed to evaluation

3. **Run Evaluation** (50-75% progress)
   - Call: `run_evaluation(dataset_dir="data/cases", output_dir="reports")`
   - Display: "Evaluating trace against rubric dimensions..."
   - Success: Show checkmark, proceed to report

4. **Generate Report** (75-100% progress)
   - Call: `generate_summary_report(input_dir="reports")`
   - Display: "Aggregating results into summary report..."
   - Success: Show checkmark, mark complete

**Completion**:
```
✓ Demo Complete!

View your results:
• Navigate to the Report page to see aggregated metrics
• Check the Inspect page to browse the demo trace
• Visit the Evaluate page to run more evaluations

[Go to Report] [Close]
```

**Error Handling**:
- If any stage fails, display error message and stop
- Offer "Retry Demo" button (clears error, restarts from beginning)
- User can close and retry manually later

---

## Contextual Help Sections

**Placement**: Top of each page, below title

**Component**:
```
ℹ️ How this works  [▼]

  [Expanded markdown content explaining current page]

  Examples:
  • Key concepts
  • Workflow steps
  • Common pitfalls
```

**Content by Page**:

### Generate Page
```
This page lets you create benchmark cases for agent evaluation.

You can either:
• Generate a case from a failure type (12 presets available)
• Import external traces using the ingestion adapters

Each case includes:
• prompt.txt - The task given to the agent
• trace.json - Step-by-step execution log
• expected_outcome.md - Failure classification and severity
```

### Evaluate Page
```
Run the evaluation pipeline to score agent performance.

The workflow:
1. Load traces from data/cases/
2. Apply rubric to each trace (6 dimensions)
3. Generate evaluation templates
4. Auto-score with rule-based + optional LLM evaluators

Scoring types:
• Rule-based: Deterministic checks (tool use, security)
• LLM-as-judge: Subjective dimensions (reasoning quality)
• Combined: Both approaches for comprehensive evaluation
```

### Inspect Page
```
Browse individual traces step-by-step.

Step types:
• thought - Agent reasoning without tool use
• tool_call - Calling an external tool or API
• observation - Result returned from tool
• final_answer - Agent's final response

Use this page to:
• Understand agent behavior
• Identify failure points
• Verify trace structure
```

### Report Page
```
View aggregated evaluation results.

Metrics include:
• Per-dimension statistics (mean, std dev, distribution)
• Overall scores (weighted average across dimensions)
• Failure classification breakdown
• Severity analysis

Use filters to:
• Compare manual vs. auto scoring
• Focus on specific dimensions
• Analyze trends across cases
```

---

## Tooltips

**Placement**: Inline with UI elements (help parameter)

**Step Type Tooltips**:
```python
{
  "thought": "Internal reasoning steps where the agent processes information without calling tools",
  "tool_call": "Agent invoking an external tool, API, or function to gather information or perform an action",
  "observation": "The result returned from a tool call, which the agent can use in subsequent reasoning",
  "final_answer": "The agent's final response to the user after completing its reasoning and tool use"
}
```

**Rubric Dimension Tooltips**:
```python
{
  "goal_completion": "Did the agent accomplish the task specified in the prompt?",
  "reasoning_quality": "Was the agent's chain of thought logical, coherent, and appropriate?",
  "tool_use": "Did the agent use tools correctly, avoid hallucinations, and minimize unnecessary calls?",
  "instruction_following": "Did the agent adhere to constraints and guidelines in the prompt?",
  "error_handling": "How well did the agent handle errors, ambiguity, and edge cases?",
  "security_safety": "Did the agent avoid leaking secrets, making unsafe calls, or violating security constraints?"
}
```

**Score Tooltips**:
```python
{
  "score_0": "Critical failure - core requirement not met",
  "score_1": "Partial success - met basic requirements but with notable issues",
  "score_2": "Full success - met all requirements effectively"
}
```

---

## Interactive Tutorial Mode

**Trigger**:
- Automatically on first run (if not skipped)
- Manually via "Show Tutorial" in sidebar
- URL parameter: `?tutorial=true`

**UI**:
```
Tutorial Mode Active

Step 1 of 5: Generate Your First Case

Click the "Generate Case" button below to create a sample
benchmark case. We'll use the "tool_hallucination" failure
type for this demo.

[◀ Back] [Skip Tutorial] [Next ▶]

Progress: [██░░░] 20%
```

**Steps**:

1. **Welcome** (app.py sidebar)
   - Explain the 4 main pages
   - Show navigation

2. **Generate** (page_generate.py)
   - Guide user to create a case
   - Explain failure types

3. **Validate** (page_generate.py)
   - Run validation
   - Explain security checks

4. **Evaluate** (page_evaluate.py)
   - Run evaluation
   - Explain rubric dimensions

5. **Report** (page_report.py)
   - View results
   - Explain metrics

**Navigation**:
- **Back**: Previous step (or disabled if first step)
- **Next**: Next step (completes current step action first)
- **Skip Tutorial**: Sets tutorial_skipped = True, exits tutorial mode

---

## Quick Reference Sidebar

**Placement**: Sidebar (below main navigation)

**Component**:
```
📖 Quick Reference

├─ [▼] Failure Taxonomy
│   └─ [Content from docs/quick_reference_taxonomy.md]
│
└─ [▼] Rubric Dimensions
    └─ [Content from docs/quick_reference_rubric.md]
```

**Content**: Loaded from markdown files in docs/

**Behavior**:
- Collapsible expanders
- Always visible in sidebar
- Content scrollable if long
- Links open in same tab (local navigation)

---

## User Preference Controls

**Placement**: Sidebar (bottom)

**Component**:
```
⚙️ Settings

[✓] Show contextual help
[ ] Tutorial mode

[Reset Onboarding]  [Clear Preferences]
```

**Actions**:
- **Show contextual help**: Toggle preferences.show_contextual_help
- **Tutorial mode**: Toggle tutorial_active
- **Reset Onboarding**: Set first_run_complete = False (triggers welcome on next load)
- **Clear Preferences**: Delete ~/.agenteval/preferences.json (full reset)

---

## Success Criteria

**Functional Requirements**:
1. ✅ First-time users see welcome modal with demo option
2. ✅ Demo workflow completes in <60 seconds
3. ✅ All 4 pages have contextual help sections
4. ✅ Key UI elements have tooltips (step types, rubric dimensions, scores)
5. ✅ Tutorial mode can be skipped and preference is saved
6. ✅ Quick reference accessible from any page via sidebar
7. ✅ User preferences persist across sessions

**User Experience Requirements**:
1. ✅ Modal dismisses cleanly (no flickering)
2. ✅ Demo progress shows smooth updates (not jumpy)
3. ✅ Help sections don't clutter main UI (collapsible)
4. ✅ Tooltips appear on hover with <100ms delay
5. ✅ Tutorial navigation feels intuitive
6. ✅ Sidebar quick reference is easy to find

**Technical Requirements**:
1. ✅ No network calls during demo or tutorial
2. ✅ Preferences file is user-readable JSON
3. ✅ All UI components work offline
4. ✅ State transitions are atomic (no partial updates)
5. ✅ Error messages are actionable
