# Project Overview

## What this app is

A voice-powered bug reporting agent that clients can talk to when they encounter issues with a product. The agent conversationally gathers all the information needed to raise a well-structured GitHub issue, then creates it automatically.

## Who uses it

- **Clients** — non-technical users who have found a bug or issue in a product and need to report it. They speak to the agent via a web interface.
- **Development team** — receives structured GitHub issues created by the agent, ready for triage.

## How it works (high level)

1. The agent is pre-configured with a specific product and GitHub repo.
2. The agent has pre-loaded knowledge from the repo's `docs/ai` directory so it understands the product.
3. A client connects via the web frontend and starts describing their issue.
4. The agent conversationally gathers:
   - A clear description of the bug
   - What the user expected to happen
   - Steps to reproduce
   - Priority level (Urgent / High / Medium / Low)
   - A Loom recording link (with guidance provided via text in the UI)
5. The agent uses its product knowledge to ask insightful questions and determine if this is a bug or a feature request.
6. Once all information is gathered, the agent summarises the ticket back to the user for confirmation.
7. On confirmation, the agent creates a GitHub issue and shares the URL with the user via the text display.

## Tech stack

- **Backend**: Python 3.12+ with LiveKit Agents framework, OpenAI Realtime API
- **Frontend**: Next.js 15, React 19, TypeScript, TailwindCSS, Radix UI
- **Real-time voice**: LiveKit client/server SDKs
- **AI model**: OpenAI Realtime (gpt-realtime-mini)
- **Issue tracking**: GitHub API (issues)
- **Package managers**: Python (uv), Node (pnpm)

## External integrations

- **LiveKit** — real-time voice communication between client and agent
- **OpenAI Realtime API** — powers the voice agent's conversational ability
- **GitHub API** — creates issues on the configured repo (requires personal access token)

## How to run locally

_To be documented as we build._

## Key directories

- `agent/` — Python backend, voice agent logic
- `frontend/` — Next.js web frontend with voice UI
- `docs/ai/` — AI-readable project documentation

## Conventions

- Building incrementally — each feature is added and understood before moving to the next
- This is a learning project — code should be clear and well-commented where the logic isn't obvious
