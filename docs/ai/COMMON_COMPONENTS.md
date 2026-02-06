# Common Components and Patterns

## UI library

- **Radix UI** — headless component primitives
- **TailwindCSS** — utility-first styling
- **shadcn/ui** — pre-built components built on Radix + Tailwind
- **LiveKit React Components** — voice/video UI components

## Key frontend components

_To be documented as we build. Will include:_

- Voice connection controls (start/end call)
- Text display panel (for links, summaries, issue URLs alongside voice)
- Status indicators (agent thinking, recording, etc.)

## Reuse rules

- Before creating a new component, search for existing equivalents
- Prefer extending existing components over adding near-duplicates
- Use shadcn/ui patterns for any new UI elements

## Agent patterns

_To be documented as we build. Will include:_

- System prompt structure
- Tool definitions (GitHub issue creation, etc.)
- Product knowledge loading from docs
