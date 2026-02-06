# Product Playbook: Bug Reporter Voice Agent

This document describes how the Bug Reporter Voice Agent works. It is used by the AI agent to understand the product when helping users report bugs.

---

## Product Summary

**Product Name:** Bug Reporter Voice Agent

**What it does:** A voice-powered assistant that helps clients report bugs or issues. The client speaks to the agent via a web interface, and the agent guides them through a structured conversation to gather all the information needed to create a GitHub issue.

**Who uses it:**
- Clients (non-technical users) who have encountered a bug or issue
- Development teams who receive the resulting GitHub issues

**Key value:** Clients can report bugs by talking naturally instead of filling out forms. The agent ensures all necessary information is captured before submitting.

---

## User Roles

| Role | Description | What they can do |
|------|-------------|------------------|
| Client | A user of a product who has encountered an issue | Start a voice call, describe their issue, answer questions, confirm the ticket summary |

**Note:** There is no login system. Clients access the voice agent directly via a web page. The agent does not store user accounts or require authentication.

---

## Features

### Voice Conversation
- Clients speak to the agent using their microphone
- The agent responds with voice (text-to-speech)
- Real-time, natural conversation flow

### Bug Report Data Collection
The agent gathers the following information during the conversation:

**Required fields:**
- Description of the issue
- Expected behaviour (what should have happened)
- Steps to reproduce
- Priority level (Urgent, High, Medium, Low)
- Issue type (bug or feature request)

**Optional fields (asked when relevant):**
- Error message seen
- URL where the issue occurred
- Page title
- Browser being used
- Loom recording link

### Priority Classification
The agent helps clients determine the appropriate priority:

| Priority | Response Time | Resolution Target | When to use |
|----------|--------------|-------------------|-------------|
| Urgent | 1 hour | 1 day | Platform offline, serious brand damage, income restriction |
| High | 1 working day | 3 working days | Part of platform damaged but not offline |
| Medium | 1 working day | 8 working days | Inhibits user experience but platform still usable |
| Low | 2 working days | Agreed with client | Cosmetic issues, no UX impact |

### Ticket Summary & Confirmation
Before submitting, the agent:
1. Summarises all gathered information
2. Displays the summary as text in the UI
3. Asks the client to confirm or make corrections

### GitHub Issue Creation
Once confirmed, the agent:
1. Creates a GitHub issue with all the gathered information
2. Applies appropriate labels (priority, bug/feature)
3. Shares the issue URL with the client

---

## User Journey: Reporting a Bug

1. Client opens the bug reporter web page
2. Client clicks to start a voice call
3. Agent greets the client and asks them to describe their issue
4. Client explains the problem in their own words
5. Agent asks clarifying questions based on what they've said
6. Agent gathers diagnostic details (error messages, URL, browser, etc.)
7. Agent helps determine if this is a bug or feature request
8. Agent guides priority selection based on impact
9. Agent asks if they have a screen recording
10. Agent summarises the full ticket
11. Client confirms or requests changes
12. Agent creates the GitHub issue
13. Agent shares the issue URL
14. Call ends

---

## What This Product Does NOT Have

- No user accounts or login system
- No database of past tickets (issues go straight to GitHub)
- No dashboard or admin panel
- No email notifications (GitHub handles those)
- No file upload (Loom links only for recordings)

---

## Technical Details (for context)

- **Frontend:** Web page with microphone access
- **Voice:** LiveKit for real-time audio, OpenAI Realtime for speech-to-text and text-to-speech
- **AI:** OpenAI's GPT model processes the conversation
- **Issue tracking:** GitHub Issues API

---

## Common Terminology

| Term | Meaning |
|------|---------|
| Client | The person reporting the bug |
| Agent | The AI voice assistant |
| Ticket | The bug report being created |
| Issue | A GitHub issue (the final output) |
| Loom | A screen recording tool |
| Priority | Urgency level of the bug |
| Repro steps | Steps to reproduce the bug |

---

## FAQ

**Q: Can I report a bug without speaking?**
A: No, this is a voice-only interface. For text-based reporting, use GitHub Issues directly.

**Q: What if I don't have a Loom recording?**
A: That's fine — it's optional. The agent will provide a link to guidance on how to create one if you'd like to add it later.

**Q: Can I edit the ticket after it's created?**
A: Yes, you'll receive the GitHub issue URL and can edit it directly on GitHub.

**Q: What browsers are supported?**
A: Any modern browser with microphone support (Chrome, Firefox, Safari, Edge).
