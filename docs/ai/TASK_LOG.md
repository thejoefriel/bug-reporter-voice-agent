# Task Log

## Build Plan

1. [x] Strip existing agent, set up bug reporter persona/instructions
2. [x] Add structured data gathering (priority, description, expected behaviour, repro steps)
3. [x] Add repo docs reading for product knowledge
4. [x] Add Loom link collection with guidance document link (text display in frontend)
5. [x] Add summary/confirmation step
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

### Step 3 — Repo docs reading for product knowledge

- **Goal:** Give the agent product context so it can ask informed questions and distinguish bugs from feature requests
- **Plan:** Load markdown files from a configured repo's `docs/ai` folder at startup
- **Decisions:**
  - Added `TARGET_REPO_PATH` environment variable for configuration
  - Created `load_product_docs()` function using `pathlib` for cross-platform path handling
  - Docs are loaded once at module import time (not per-request) for efficiency
  - Extracted instructions into `build_agent_instructions()` function for cleaner code
  - Product docs are appended to base instructions with guidance on how to use them
  - For testing, pointed `TARGET_REPO_PATH` at this repo itself
- **Python concepts covered:**
  - `os.getenv()` for environment variables
  - `pathlib.Path` for modern file path handling
  - `glob()` for pattern matching files
  - Context managers (`with open()`) for safe file handling
  - Ternary expressions (`x if condition else y`)
  - SCREAMING_SNAKE_CASE convention for constants
- **Files changed:**
  - `agent/agent.py`
  - `agent/.env.local`
- **Follow-ups:**
  - Step 4: Add Loom link collection with guidance document link

### Step 4 — Loom link collection with text display

- **Goal:** Allow the agent to send text/links to the frontend chat (for Loom guidance, summaries, etc.)
- **Plan:** Add tools that use LiveKit's send_text() to display messages in the chat
- **Decisions:**
  - Added `get_job_context` import to access the LiveKit session from within tools
  - Added `LOOM_GUIDANCE_URL` environment variable with sensible default
  - Created `send_text_to_client` tool for general text/link sharing
  - Created `send_loom_guidance` tool specifically for the Loom help link
  - Created `request_text_input` tool to prompt users to type in chat
  - **Key learning:** Must use `topic="lk.chat"` (the standard LiveKit chat topic) for messages
    to appear in the frontend. Custom topics require registering handlers manually.
  - Updated frontend `session-view.tsx` to auto-open chat when agent sends a chat message
    (detected by `lastMessage.type === 'chatMessage'` and `from?.isLocal === false`)
  - Updated instructions to explain when to use these tools
- **Python concepts covered:**
  - `get_job_context()` — accessing runtime context from within a tool
  - `await` with async methods — `send_text()` is asynchronous
  - Default values in `os.getenv()` — fallback URL if not configured
- **Files changed:**
  - `agent/agent.py`
  - `frontend/components/app/session-view.tsx`
- **Follow-ups:**
  - Step 5: Add summary/confirmation step

### Step 5 — Summary and confirmation

- **Goal:** Let the client review and confirm the bug report before submission
- **Plan:** Add a tool that formats and displays a summary, then agent asks for confirmation
- **Decisions:**
  - Created `generate_summary` tool that:
    - Checks all required fields are filled before generating
    - Builds a markdown-formatted summary with all collected fields
    - Sends the summary to the client's chat window
    - Returns guidance to the agent to ask for confirmation
  - Updated instructions with "Summary and confirmation" section explaining:
    - When to call `generate_summary` (after all required fields collected)
    - How to handle confirmation (proceed to submit)
    - How to handle corrections (update field, regenerate summary)
- **Python concepts covered:**
  - Building multi-line strings with lists and `"\n".join()`
  - Conditional string building (only add optional fields if present)
- **Files changed:**
  - `agent/agent.py`
- **Follow-ups:**
  - Step 6: Add GitHub issue creation and return URL
