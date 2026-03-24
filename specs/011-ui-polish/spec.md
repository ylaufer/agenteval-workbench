# Feature Specification: UI Polish

**Feature ID:** 011
**Phase:** 2.7
**Priority:** MEDIUM
**Status:** Not Started

---

## Problem Statement

The current UI covers the workflow but lacks navigational coherence, feedback states, and contextual actions. It feels like a prototype, not a product.

## Goal

Transform the UI into a cohesive, intuitive product experience with clear navigation flow, helpful empty states, and contextual actions throughout.

---

## Capabilities

### 1. Navigation Flow Enforcement

- Define clear workflow path: Generate → Inspect → Evaluate → Report
- Breadcrumb navigation showing current location
- "Next step" suggestions at each stage
- Persistent sidebar with workflow visualization

### 2. Empty States

Replace blank pages with helpful messages and direct actions:

- **No cases yet**: "No cases yet — generate one to get started" + [Generate Case] button
- **No runs yet**: "No evaluation runs yet. Generate and evaluate a case first." + workflow guide
- **No reports yet**: "No reports available. Run an evaluation to generate reports." + [Run Evaluation] button

### 3. Error States

- Clear error messages with recovery suggestions
- Example: "Trace validation failed. Check that trace.json matches the schema." + [View Schema] link
- Example: "Evaluation failed for case_003. Check the trace and try again." + [Inspect Trace] button

### 4. Loading States

- Progress indicators during long-running operations
- Evaluation: "Evaluating 12 cases... (5/12 complete)"
- Auto-scoring: "Running auto-scoring... (ToolUseEvaluator complete, SecurityEvaluator in progress)"
- Report generation: "Generating summary report..."

### 5. Contextual Actions

Every data item gets relevant action buttons:

#### Case in List
- [Inspect Trace]
- [Evaluate]
- [View Report] (if exists)

#### Run in List
- [View Details]
- [Compare with...]
- [Download Results]

#### Trace Step
- [Add Annotation]
- [View Evidence] (if auto-eval exists)

### 6. Case Filtering

Consistent filtering UI across all pages that display case lists:

- Filter by case_id (text search)
- Filter by failure type (dropdown, multi-select)
- Filter by severity (dropdown, multi-select)
- Filter by tag (dropdown, multi-select)
- Filter state persists across navigation

### 7. Consistent Layout & Components

- Standard page header with title and help icon
- Consistent button styles (primary, secondary, danger)
- Consistent table layouts (sortable headers, hover states)
- Consistent color coding:
  - 🟢 Green: success, improvement, clean
  - 🔴 Red: error, regression, flagged
  - 🟡 Yellow: warning, attention needed
  - ⚪ Gray: neutral, unchanged
- Consistent spacing and typography

---

## UI Patterns

### Page Header Template

```
┌──────────────────────────────────────────────────────────────┐
│  [Page Title]                                    [Help ℹ️]  │
│  [Breadcrumb: Home > Generate > Case 001]                    │
└──────────────────────────────────────────────────────────────┘
```

### Empty State Template

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                      📦                                      │
│                                                              │
│              No cases found                                  │
│                                                              │
│     Generate a case to get started with evaluation          │
│                                                              │
│                 [Generate Case]                              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Loading State Template

```
┌──────────────────────────────────────────────────────────────┐
│  Evaluating cases...                                         │
│                                                              │
│  [████████░░░░░░░░░░] 5/12 complete                          │
│                                                              │
│  Current: case_005 (ToolUseEvaluator running)               │
└──────────────────────────────────────────────────────────────┘
```

### Error State Template

```
┌──────────────────────────────────────────────────────────────┐
│  ⚠️  Evaluation failed for case_003                          │
│                                                              │
│  Error: Trace validation failed                             │
│  trace.json does not match the required schema.             │
│                                                              │
│  [View Schema] [Inspect Trace] [Retry]                      │
└──────────────────────────────────────────────────────────────┘
```

### Contextual Actions (Case List)

```
┌──────────────────────────────────────────────────────────────┐
│  case_001  Tool Hallucination  Critical                      │
│  [Inspect Trace] [Evaluate] [View Report]                   │
│                                                              │
│  case_002  Constraint Violation  High                        │
│  [Inspect Trace] [Evaluate] [View Report]                   │
└──────────────────────────────────────────────────────────────┘
```

---

## Workflow Visualization (Sidebar)

```
┌─────────────────────┐
│  Workflow           │
│  ├─ 1. Generate  ✓  │
│  ├─ 2. Inspect   ✓  │
│  ├─ 3. Evaluate  ←  │ (current step)
│  └─ 4. Report       │
└─────────────────────┘
```

---

## Architecture

```
app/components/
  header.py           — page header with breadcrumb
  empty_state.py      — reusable empty state component
  error_state.py      — reusable error state component
  loading_state.py    — reusable loading indicator
  filter_bar.py       — case filtering UI component
  workflow_sidebar.py — workflow visualization sidebar

app/styles.py         — centralized styling constants
```

---

## Success Criteria

1. ✅ Every page has a clear header with breadcrumb navigation
2. ✅ Empty states provide helpful guidance and direct actions
3. ✅ Error states include recovery suggestions
4. ✅ Long-running operations show progress indicators
5. ✅ Every data item has contextual action buttons
6. ✅ Case filtering works consistently across all pages
7. ✅ UI uses consistent layout, colors, and typography
8. ✅ Workflow sidebar shows current position in the evaluation flow

---

## Dependencies

- Existing Streamlit UI pages (`app/page_*.py`)
- Service layer (`src/agenteval/core/service.py`)

---

## Testing Requirements

- UI component rendering tests
- Workflow navigation flow tests
- Empty/error/loading state display tests
- Filter persistence tests

---

## Documentation Requirements

- UI navigation guide
- Workflow overview diagram
- Design system reference (colors, typography, components)
