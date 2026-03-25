# Quickstart: Guided Onboarding

## Scenario 1: First-Time User Experience

**Goal**: New user opens AgentEval Workbench and gets productive in 60 seconds

**Steps**:

1. **Launch App**
   ```bash
   streamlit run app/app.py
   ```

2. **Welcome Modal Appears**
   - User sees welcome message
   - Two options: "Run Demo" or "Skip Tutorial"

3. **User Clicks "Run Demo"**
   - Modal closes
   - Demo progress appears with 4 stages:
     - Generate case (demo_001)
     - Validate dataset
     - Run evaluation
     - Generate report
   - Each stage shows progress bar and status message

4. **Demo Completes (~45 seconds)**
   - Success message appears
   - "Go to Report" button highlighted
   - User preference saved (first_run_complete = True)

5. **User Navigates to Report Page**
   - Sees annotated demo results
   - Contextual help section explains metrics
   - Tooltips on dimension scores

**Expected Outcome**: User has seen full workflow and understands key concepts

---

## Scenario 2: Skipping Tutorial

**Goal**: Experienced user wants to skip onboarding

**Steps**:

1. **Welcome Modal Appears**
   - User clicks "Skip Tutorial"

2. **Preference Saved**
   - first_run_complete = True
   - tutorial_skipped = True
   - Modal won't appear on next launch

3. **User Proceeds Directly**
   - No forced tutorial
   - Contextual help still available (collapsible)
   - Quick reference in sidebar

**Expected Outcome**: User can work without interruption

---

## Scenario 3: Using Contextual Help

**Goal**: User needs explanation of a specific page

**Steps**:

1. **Navigate to Inspect Page**

2. **Expand "How this works" Section**
   - Click on "ℹ️ How this works" expander
   - Read explanation of trace inspection
   - See examples of step types

3. **Hover Over Step Type Badge**
   - Tooltip appears explaining "thought" vs "tool_call" vs "observation"

4. **Collapse Help Section**
   - Click expander again to minimize
   - Main UI remains uncluttered

**Expected Outcome**: User understands page without leaving workflow

---

## Scenario 4: Interactive Tutorial Mode

**Goal**: User wants guided walkthrough after initial skip

**Steps**:

1. **Enable Tutorial via Sidebar**
   - Click "Tutorial mode" checkbox in Settings

2. **Tutorial Activates**
   - Progress bar appears (Step 1 of 5)
   - Instructions for current page

3. **Follow Tutorial Steps**
   - Step 1: Welcome (overview)
   - Step 2: Generate case (create demo_tutorial_001)
   - Step 3: Validate dataset
   - Step 4: Run evaluation
   - Step 5: View report

4. **Complete Tutorial**
   - Preference saved (tutorial_progress = 5)
   - Can restart anytime via Settings

**Expected Outcome**: User completes hands-on walkthrough

---

## Scenario 5: Quick Reference Access

**Goal**: User needs to check failure taxonomy while evaluating

**Steps**:

1. **On Any Page**
   - Scroll to sidebar

2. **Expand "Failure Taxonomy" Quick Reference**
   - Click "📖 Quick Reference" > "Failure Taxonomy"
   - See list of 12 failure categories with descriptions

3. **Scan for Relevant Category**
   - Find "tool_hallucination"
   - Read definition and indicators

4. **Collapse and Continue**
   - Close expander
   - Return to evaluation

**Expected Outcome**: User found reference info without leaving page

---

## Scenario 6: Resetting Onboarding

**Goal**: User wants to re-run demo or reset tutorial

**Steps**:

1. **Open Settings in Sidebar**

2. **Click "Reset Onboarding"**
   - Sets first_run_complete = False
   - Clears demo completion timestamp

3. **Reload Page**
   - Welcome modal appears again
   - Can run demo again

**Alternative**: Click "Clear Preferences"
- Deletes ~/.agenteval/preferences.json entirely
- Full reset to factory defaults

**Expected Outcome**: User can re-experience onboarding

---

## Scenario 7: Demo Error Recovery

**Goal**: Handle demo failure gracefully

**Steps**:

1. **Run Demo**
   - Demo starts normally

2. **Stage Fails** (e.g., validation error)
   - Error message displayed
   - Progress bar turns red
   - Specific error shown: "Validation failed: case_demo_001 missing prompt.txt"

3. **User Clicks "Retry Demo"**
   - Demo status resets
   - Starts from beginning
   - Uses fresh case ID (demo_002) to avoid conflicts

4. **Demo Succeeds on Retry**
   - Progress completes
   - Success message shown

**Expected Outcome**: User can recover from errors without restarting app

---

## Scenario 8: Preference Persistence

**Goal**: Verify preferences survive app restarts

**Steps**:

1. **Complete Demo**
   - first_run_complete = True saved to ~/.agenteval/preferences.json

2. **Close App**

3. **Relaunch App**
   ```bash
   streamlit run app/app.py
   ```

4. **No Welcome Modal**
   - App loads directly to main UI
   - User sees familiar interface

5. **Check Preferences**
   - Settings in sidebar show current state
   - "Show contextual help" checkbox reflects saved preference

**Expected Outcome**: User preferences persist across sessions

---

## Scenario 9: Tooltip Discovery

**Goal**: User explores UI and discovers helpful tooltips

**Steps**:

1. **On Inspect Page**
   - View a trace with multiple step types

2. **Hover Over "thought" Badge**
   - Tooltip appears: "Internal reasoning steps where the agent processes information..."

3. **Hover Over "tool_call" Badge**
   - Tooltip appears: "Agent invoking an external tool, API, or function..."

4. **On Report Page**
   - Hover over dimension scores

5. **Hover Over "Security & Safety" Dimension**
   - Tooltip explains: "Did the agent avoid leaking secrets, making unsafe calls..."

**Expected Outcome**: User discovers explanations organically

---

## Scenario 10: Customizing Help Visibility

**Goal**: Power user wants to hide help sections

**Steps**:

1. **Open Settings in Sidebar**

2. **Uncheck "Show contextual help"**
   - Preference saved to file

3. **Navigate Between Pages**
   - Help sections now collapsed by default
   - Can still manually expand if needed

4. **Re-enable Later**
   - Check "Show contextual help" again
   - Help sections expand by default

**Expected Outcome**: UI adapts to user preference

---

## Developer Testing Checklist

**Before committing:**

- [ ] First-run modal appears on clean install
- [ ] Demo completes successfully (generate → validate → evaluate → report)
- [ ] Demo progress updates smoothly (no frozen UI)
- [ ] Preferences persist after app restart
- [ ] Skip tutorial works and is remembered
- [ ] All 4 pages have contextual help sections
- [ ] Tooltips appear on all key elements (step types, dimensions, scores)
- [ ] Tutorial mode can be activated/deactivated
- [ ] Quick reference loads from markdown files
- [ ] Reset onboarding button works
- [ ] Error recovery (demo retry) works
- [ ] Settings UI controls reflect current state
- [ ] No network calls during demo/tutorial
- [ ] Preferences file is valid JSON and human-readable

**Manual QA scenarios:**
- Test on fresh machine (no ~/.agenteval/ directory)
- Test with existing preferences file
- Test with corrupted preferences file (should reset gracefully)
- Test demo with no network connection (should work offline)
- Test all tutorial steps in sequence
- Test skipping tutorial mid-way

---

## File Locations

**Preferences**:
```
~/.agenteval/preferences.json
```

**Quick Reference Content**:
```
docs/quick_reference_taxonomy.md
docs/quick_reference_rubric.md
```

**Help Content (in code)**:
```python
app/onboarding/content.py
```

**Demo Cases (generated)**:
```
data/cases/case_demo_001/
├── prompt.txt
├── trace.json
└── expected_outcome.md
```

**Demo Reports (generated)**:
```
reports/
├── case_demo_001.evaluation.json
├── case_demo_001.evaluation.md
└── summary.evaluation.json
```
