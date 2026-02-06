# Architecture

## System overview

```
┌─────────────────┐     LiveKit      ┌──────────────────┐
│   Frontend       │◄───(voice +────►│   Python Agent    │
│   (Next.js)      │    text)         │   (LiveKit Agent) │
└─────────────────┘                  └──────┬───────────┘
                                            │
                                    ┌───────┴────────┐
                                    │                │
                              ┌─────▼─────┐   ┌─────▼──────┐
                              │  OpenAI    │   │  GitHub    │
                              │  Realtime  │   │  API       │
                              │  API       │   │  (Issues)  │
                              └───────────┘   └────────────┘
```

## Components

### Backend — `agent/`

- **agent.py** — Main entry point. Configures the LiveKit voice agent with:
  - System prompt (bug reporter persona, priority definitions, conversation flow)
  - Product knowledge loaded from repo docs
  - Tools for creating GitHub issues
- **OpenAI Realtime API** — Handles the voice conversation (speech-to-text, LLM reasoning, text-to-speech)
- **LiveKit Agents SDK** — Manages the real-time session, audio transport, and agent lifecycle

### Frontend — `frontend/`

- **Next.js app** — Web interface where clients connect to the agent
- **LiveKit client SDK** — Handles the voice connection from the browser
- **Text display** — Shows important information alongside voice (Loom guidance link, ticket summary, GitHub issue URL)

## Data flow

1. Client opens frontend → connects to LiveKit room
2. Agent joins the room → greets the client
3. Conversational exchange via voice (OpenAI Realtime handles STT + LLM + TTS)
4. Agent collects structured data throughout the conversation:
   - Bug description
   - Expected behaviour
   - Reproduction steps
   - Priority (Urgent / High / Medium / Low)
   - Loom recording link
   - Bug vs feature request classification
5. Agent summarises and gets confirmation (voice + text display)
6. Agent calls GitHub API to create the issue
7. Agent shares the issue URL with the client (voice + text display)
8. Call ends

## Priority definitions (used in agent prompt)

| Priority | Response time | Resolution target | Description |
|----------|--------------|-------------------|-------------|
| Urgent | 1 hour | 1 day | Platform offline, serious brand damage, income restriction |
| High | 1 working day | 3 working days | Brand or function issue, part of platform damaged |
| Medium | 1 working day | 8 working days | Inhibits user experience, but platform still usable |
| Low | 2 working days | Agreed with client | No UX impact, e.g. styling issues |

## Build plan

1. Strip existing agent, set up bug reporter persona/instructions
2. Add structured data gathering (priority, description, expected behaviour, repro steps)
3. Add repo docs reading for product knowledge
4. Add Loom link collection with guidance document link (text display in frontend)
5. Add summary/confirmation step
6. Add GitHub issue creation and return URL
7. Add text display in frontend for links and summaries
