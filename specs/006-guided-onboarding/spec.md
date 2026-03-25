# Feature Specification: Guided Onboarding

**Feature ID:** 006
**Phase:** 2.2
**Priority:** HIGH
**Status:** Not Started

---

## Clarifications

### Session 2026-03-24

- Q: What should happen if demo flow fails at any stage (generate/validate/evaluate/report)? → A: Show error message and offer "Retry Demo" button (reuses same demo case ID)
- Q: If the preferences.json file becomes corrupted or contains invalid JSON, how should the app handle this? → A: Show warning banner, reset to defaults, offer "Show Details" (transparent recovery with option to see error)
- Q: The demo flow generates a case with ID "demo_001". What should happen if case_demo_001/ already exists from a previous demo run? → A: Overwrite existing demo case (always use case_demo_001, replace files if present)
- Q: Must users complete the action on each tutorial step (e.g., actually generate a case) before proceeding to the next step? → A: Read-only walkthrough - User can click Next without executing, tutorial just explains each page
- Q: What level of accessibility (keyboard navigation, screen readers, WCAG compliance) should the onboarding UI support? → A: Keyboard navigation for critical flows - Modal dismissal (Esc), tutorial navigation (arrows/Tab), help expansion (Enter/Space)

---

## Problem Statement

A new user currently has to understand failure taxonomies, rubric dimensions, trace schemas, and the full generate→validate→evaluate→report flow before getting any value. The learning curve is steep and documentation alone won't fix it.

## Goal

Reduce time-to-first-value from "read 3 docs and figure it out" to "click one button, see results in 60 seconds."

---

## Capabilities

### 1. First-Run Experience

- Detect first launch (no existing cases or runs)
- Present a welcome page explaining the core workflow in plain language
- Offer a one-click "Run the demo" that:
  - generates a demo case
  - validates it
  - runs evaluation
  - opens the report
- Show results with annotations explaining what each section means

### 2. Contextual Help System

- Every UI page gets an expandable "How this works" section
- Trace viewer: tooltip on each step type explaining what `thought`, `tool_call`, `observation`, `final_answer` mean
- Evaluation template: inline help explaining each rubric dimension
- Report page: annotations explaining score calculations, what the numbers mean

### 3. Interactive Walkthrough Mode

- Step-by-step guided tutorial using Streamlit's native components
- Read-only walkthrough: users can navigate with "Next" button without executing actions
- Highlights key UI elements at each step
- Progress indicator showing where the user is in the workflow
- "Skip tutorial" option that remembers preference

### 4. Quick Reference

- Sidebar link to failure taxonomy summary
- Rubric dimension cheat sheet accessible from any page
- Example traces for each failure type, browsable from the Generate page

---

## User Flow

1. **First Launch**
   - User opens Streamlit UI for the first time
   - Welcome modal appears with overview
   - "Run Demo" button prominently displayed

2. **Demo Flow**
   - Click "Run Demo" → generates case_demo_001 (overwrites if exists)
   - Progress indicator shows: Generate → Validate → Evaluate → Report
   - Each step displays brief explanation of what's happening
   - Success screen with annotated report view
   - **Error Handling**: If any stage fails, show error message with specific details and offer "Retry Demo" button (reuses same demo case ID)

3. **Subsequent Launches**
   - Welcome dismissed (stored in user preferences)
   - Optional tutorial mode available via sidebar
   - Contextual help always accessible via info icons
   - **Preference Recovery**: If preferences.json is corrupted, show warning banner at top of UI, reset to factory defaults, and offer "Show Details" button to view error

---

## UI Components

### Welcome Modal
```
┌─────────────────────────────────────────────┐
│  Welcome to AgentEval Workbench             │
│                                             │
│  This tool helps you evaluate LLM agent    │
│  performance using structured rubrics.      │
│                                             │
│  [Run Demo] [Skip Tutorial]                │
└─────────────────────────────────────────────┘
```

### Contextual Help (Collapsible)
```
ℹ️ How this works
  └─ [Expanded content explaining current page]
```

### Tooltips
- Hover over step types, rubric dimensions, scores
- Brief, plain-language explanations

---

## Success Criteria

1. ✅ First-time users can see evaluation results within 60 seconds
2. ✅ Every UI page has contextual help
3. ✅ Tutorial can be skipped and preference is remembered
4. ✅ Users can access failure taxonomy and rubric reference from any page
5. ✅ Demo flow completes successfully on first run

---

## Dependencies

- Existing Streamlit UI (`app/`)
- Case generator (`src/agenteval/dataset/generator.py`)
- Service layer (`src/agenteval/core/service.py`)

---

## Testing Requirements

- First-run detection logic
- Demo flow end-to-end test
- User preference persistence
- Help content accessibility tests

---

## Accessibility Requirements

- **Keyboard Navigation**: Support for critical flows
  - Modal dismissal: Esc key closes welcome modal
  - Tutorial navigation: Tab for focus, Enter/Space to activate buttons, arrow keys for step navigation
  - Help expansion: Enter/Space to toggle collapsible help sections
- **Focus Management**: Visible focus indicators on interactive elements
- **Screen Reader**: Rely on Streamlit's built-in ARIA labels (no custom implementation required for MVP)
- **WCAG Compliance**: Defer full WCAG 2.1 AA compliance to post-MVP phase

---

## Documentation Requirements

- Onboarding content (welcome text, explanations)
- Tooltip text for all key concepts
- Tutorial step descriptions
- Quick reference sheets (failure taxonomy, rubric dimensions)
