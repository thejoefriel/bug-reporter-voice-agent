# Task Log

## Build Plan

1. [x] Strip existing agent, set up bug reporter persona/instructions
2. [x] Add structured data gathering (priority, description, expected behaviour, repro steps)
3. [ ] Add repo docs reading for product knowledge
4. [ ] Add Loom link collection with guidance document link (text display in frontend)
5. [ ] Add summary/confirmation step
6. [ ] Add GitHub issue creation and return URL
7. [ ] Add text display in frontend for links and summaries

## Completed Tasks

### Step 1 — Bug reporter persona

- **Goal:** Replace the demo note-taking agent with the bug reporter persona
- **Plan:** Remove memory/note tools, write new instructions, update greeting
- **Decisions:**
  - Removed `memory` dict, `save_note`, `get_notes` — not applicable to bug reporting
  - Removed `function_tool` import — no tools needed yet, will add in later steps
  - Renamed class from `VoiceAgent` to `BugReporterAgent`
  - Instructions define: conversation flow (6 steps), priority definitions, behaviour guidelines
  - Greeting asks the client to describe their issue
- **Files changed:**
  - `agent/agent.py`
- **Follow-ups:**
  - Step 2: Add structured data gathering so the agent tracks what info has been collected

### Step 2 — Structured data gathering

- **Goal:** Track what information has been collected during the conversation
- **Plan:** Add a BugReport dataclass, tools to save fields and check status
- **Decisions:**
  - Created `BugReport` dataclass with 11 fields (5 required, 6 optional)
  - Required fields: description, expected_behaviour, steps_to_reproduce, priority, issue_type
  - Optional fields: error_message, logged_in_user, url, page_title, browser, loom_link
  - Added `save_report_field` tool — validates field names, priority values, and issue_type values
  - Added `get_report_status` tool — shows what's collected and what's missing
  - Updated instructions to explain how to use the tools
- **Files changed:**
  - `agent/agent.py`
- **Follow-ups:**
  - Step 3: Add repo docs reading for product knowledge
