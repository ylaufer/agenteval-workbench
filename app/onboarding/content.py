"""Help content, tooltips, and tutorial steps."""
from __future__ import annotations


# Page help sections (for st.expander)
PAGE_HELP = {
    "generate": """
This page lets you create benchmark cases for agent evaluation.

You can either:
• Generate a case from a failure type (12 presets available)
• Import external traces using the ingestion adapters

Each case includes:
• `prompt.txt` - The task given to the agent
• `trace.json` - Step-by-step execution log
• `expected_outcome.md` - Failure classification and severity
    """.strip(),
    "evaluate": """
Run the evaluation pipeline to score agent performance.

The workflow:
1. Load traces from `data/cases/`
2. Apply rubric to each trace (6 dimensions)
3. Generate evaluation templates
4. Auto-score with rule-based + optional LLM evaluators

Scoring types:
• Rule-based: Deterministic checks (tool use, security)
• LLM-as-judge: Subjective dimensions (reasoning quality)
• Combined: Both approaches for comprehensive evaluation
    """.strip(),
    "inspect": """
Browse individual traces step-by-step.

Step types:
• **thought** - Agent reasoning without tool use
• **tool_call** - Calling an external tool or API
• **observation** - Result returned from tool
• **final_answer** - Agent's final response

Use this page to:
• Understand agent behavior
• Identify failure points
• Verify trace structure
    """.strip(),
    "report": """
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
    """.strip(),
}


# Tooltips for step types
STEP_TYPE_TOOLTIPS = {
    "thought": "Internal reasoning steps where the agent processes information without calling tools",
    "tool_call": "Agent invoking an external tool, API, or function to gather information or perform an action",
    "observation": "The result returned from a tool call, which the agent can use in subsequent reasoning",
    "final_answer": "The agent's final response to the user after completing its reasoning and tool use",
}


# Tooltips for rubric dimensions
RUBRIC_DIMENSION_TOOLTIPS = {
    "goal_completion": "Did the agent accomplish the task specified in the prompt?",
    "reasoning_quality": "Was the agent's chain of thought logical, coherent, and appropriate?",
    "tool_use": "Did the agent use tools correctly, avoid hallucinations, and minimize unnecessary calls?",
    "instruction_following": "Did the agent adhere to constraints and guidelines in the prompt?",
    "error_handling": "How well did the agent handle errors, ambiguity, and edge cases?",
    "security_safety": "Did the agent avoid leaking secrets, making unsafe calls, or violating security constraints?",
}


# Tutorial steps (for read-only walkthrough)
TUTORIAL_STEPS = [
    {
        "step_number": 0,
        "title": "Welcome to AgentEval Workbench",
        "description": "This tool helps you evaluate LLM agent performance using structured rubrics and failure taxonomies. Navigate through the pages to see the full workflow.",
        "page": "home",
    },
    {
        "step_number": 1,
        "title": "Generate Your First Case",
        "description": "The Generate page lets you create benchmark cases from failure type presets or import external traces. No action required—just explore the options.",
        "page": "generate",
    },
    {
        "step_number": 2,
        "title": "Validate Your Dataset",
        "description": "Validation ensures data integrity and security. It checks for required files, schema compliance, and security violations.",
        "page": "generate",
    },
    {
        "step_number": 3,
        "title": "Run Evaluation",
        "description": "The Evaluate page runs the evaluation pipeline, applying the rubric to generate scoring templates. You can use manual, auto, or combined scoring.",
        "page": "evaluate",
    },
    {
        "step_number": 4,
        "title": "Inspect Traces",
        "description": "The Inspect page lets you browse individual traces step-by-step. You can view case metadata, trace steps, and evaluation scores for each case and run.",
        "page": "inspect",
    },
    {
        "step_number": 5,
        "title": "View Reports",
        "description": "The Report page aggregates results across all cases, showing dimension statistics, failure distributions, and severity analysis.",
        "page": "report",
    },
]
