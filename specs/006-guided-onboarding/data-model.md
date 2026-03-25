# Data Model: Guided Onboarding

## Entities

### 1. UserPreferences

Persistent user settings stored in `~/.agenteval/preferences.json`

```python
{
  "first_run_complete": bool,      # Has user completed first-run demo?
  "tutorial_skipped": bool,         # Did user skip tutorial?
  "show_contextual_help": bool,     # Show help sections by default?
  "demo_completed_at": str | null,  # ISO timestamp of demo completion
  "tutorial_progress": int          # Current tutorial step (0-based, -1 if not started)
}
```

**Default Values**:
```python
{
  "first_run_complete": False,
  "tutorial_skipped": False,
  "show_contextual_help": True,
  "demo_completed_at": None,
  "tutorial_progress": -1
}
```

**Validation Rules**:
- `first_run_complete`: Must be boolean
- `tutorial_skipped`: Must be boolean, only set to True after first run
- `show_contextual_help`: Must be boolean
- `demo_completed_at`: Must be ISO8601 string or null
- `tutorial_progress`: Must be integer >= -1

---

### 2. SessionState

In-memory state managed by Streamlit session_state

```python
{
  "onboarding_modal_shown": bool,     # Has welcome modal been shown this session?
  "demo_in_progress": bool,            # Is demo currently running?
  "demo_status": dict,                 # Demo progress tracking
  "tutorial_active": bool,             # Is tutorial mode active?
  "tutorial_current_step": int,        # Current tutorial step
  "preferences": UserPreferences       # Loaded from file at startup
}
```

**State Transitions**:

1. **First Launch**:
   ```
   preferences.first_run_complete = False
   → Show welcome modal
   → onboarding_modal_shown = True
   ```

2. **Demo Start**:
   ```
   demo_in_progress = True
   demo_status = {"step": "generate", "progress": 0.0}
   → Run demo workflow
   → Update demo_status at each step
   ```

3. **Demo Complete**:
   ```
   demo_in_progress = False
   preferences.first_run_complete = True
   preferences.demo_completed_at = now()
   → Save preferences to file
   ```

4. **Tutorial Skip**:
   ```
   preferences.tutorial_skipped = True
   tutorial_active = False
   → Save preferences to file
   ```

---

### 3. DemoStatus

Tracks demo workflow progress

```python
{
  "step": str,              # Current step: "generate" | "validate" | "evaluate" | "report" | "complete"
  "progress": float,        # 0.0 to 1.0
  "message": str,           # Status message to display
  "error": str | null       # Error message if step failed
}
```

**State Machine**:
```
generate (0.0)
   ↓
validate (0.25)
   ↓
evaluate (0.50)
   ↓
report (0.75)
   ↓
complete (1.0)
```

**Error Handling**:
- If any step fails, set `error` field and stop progression
- User can retry demo (clears error and restarts from beginning)

---

### 4. HelpContent

Static content structure for contextual help

```python
{
  "page_name": str,           # "generate" | "evaluate" | "inspect" | "report"
  "title": str,               # Help section title
  "content": str,             # Markdown content
  "tooltips": dict[str, str]  # Element ID -> tooltip text
}
```

**Example**:
```python
{
  "page_name": "inspect",
  "title": "How Trace Inspection Works",
  "content": "Traces show step-by-step agent execution...",
  "tooltips": {
    "step_type_thought": "Internal reasoning steps without tool use",
    "step_type_tool_call": "Agent calling an external tool or API",
    "step_type_observation": "Result returned from a tool call",
    "step_type_final_answer": "Agent's final response to the user"
  }
}
```

---

### 5. TutorialStep

Tutorial walkthrough step definition

```python
{
  "step_number": int,
  "title": str,
  "description": str,
  "page": str,              # Which page this step is on
  "highlight": str | null,  # Element to highlight (if possible)
  "action": str | null      # Expected user action to proceed
}
```

**Tutorial Flow**:
```
Step 0: Welcome (app.py)
  → "Welcome to AgentEval Workbench"

Step 1: Generate Page (page_generate.py)
  → "Let's generate your first benchmark case"

Step 2: Validate (page_generate.py)
  → "Validation ensures data integrity"

Step 3: Evaluate Page (page_evaluate.py)
  → "Run the evaluation pipeline"

Step 4: Report Page (page_report.py)
  → "Review aggregated results"

Step 5: Complete (page_report.py)
  → "You're all set!"
```

---

## Relationships

```
UserPreferences (file)
      ↕ (load/save)
SessionState (memory)
      ↓
DemoStatus (transient)
HelpContent (static)
TutorialStep (static)
```

---

## File Storage

### Preferences File Location

**Path**: `~/.agenteval/preferences.json`

**Structure**:
```
~/.agenteval/
├── preferences.json       # User preferences (this feature)
└── .first_run_marker      # DEPRECATED: Use preferences.json instead
```

**File Format**:
```json
{
  "first_run_complete": false,
  "tutorial_skipped": false,
  "show_contextual_help": true,
  "demo_completed_at": null,
  "tutorial_progress": -1
}
```

**Permissions**: User read/write only (0600)

---

## Migration

If `~/.agenteval/.first_run_marker` exists (old approach), migrate to new preferences.json:

```python
if Path("~/.agenteval/.first_run_marker").exists():
    preferences = {
        "first_run_complete": True,
        "tutorial_skipped": True,  # Assume skipped if using old marker
        "show_contextual_help": True,
        "demo_completed_at": None,
        "tutorial_progress": -1
    }
    save_preferences(preferences)
    Path("~/.agenteval/.first_run_marker").unlink()
```

---

## State Persistence

**On App Startup**:
1. Load UserPreferences from ~/.agenteval/preferences.json
2. Initialize SessionState with loaded preferences
3. Check first_run_complete to decide whether to show welcome modal

**On User Action**:
1. Update SessionState immediately (for UI responsiveness)
2. Save UserPreferences to file (for persistence)

**Concurrency**: File writes are sequential (single-user app), no locking needed
