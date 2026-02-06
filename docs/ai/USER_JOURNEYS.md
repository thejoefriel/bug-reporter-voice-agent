# User Journeys

## Journey 1: Client reports a bug

**Actor:** Client (non-technical user of the product)

**Preconditions:**
- The agent is configured with the product's repo and docs
- The client has access to the web frontend

**Flow:**

1. Client opens the bug reporter web page
2. Client clicks to start a voice call with the agent
3. Agent greets the client and asks them to describe the issue they're facing
4. Client explains the problem in their own words
5. Agent asks clarifying questions based on its knowledge of the product (loaded from `docs/ai`)
6. Agent determines whether this is a bug or a feature request and tells the client
7. Agent guides the client through describing:
   - What they expected to happen vs what actually happened
   - The steps they took before the issue occurred
8. Agent helps the client determine the priority level by explaining the definitions and asking about impact (is the platform down? is it causing revenue loss? is it a cosmetic issue?)
9. Agent asks if the client has a screen recording. If not, it sends a link to Loom guidance via the text display in the UI
10. Client provides the Loom link (or says they'll add it later)
11. Agent summarises the full ticket back to the client:
    - Title
    - Type (bug / feature request)
    - Priority
    - Description
    - Expected behaviour
    - Steps to reproduce
    - Loom link (if provided)
12. The summary is also displayed as text in the UI
13. Client confirms or requests changes
14. Agent creates the GitHub issue
15. Agent shares the GitHub issue URL via voice and text display
16. Client can view the issue and make further edits directly on GitHub
17. Call ends

**Postconditions:**
- A structured GitHub issue exists in the repo
- The client has the issue URL to track progress

## Journey 2: Client reports what turns out to be a feature request

**Actor:** Client

**Flow:**

1. Steps 1-5 same as Journey 1
2. Based on the product docs, the agent recognises the described behaviour is not a bug — the feature doesn't exist yet
3. Agent explains this to the client: "Based on how the product currently works, this sounds like it would be a new feature rather than a bug. Would you like me to raise it as a feature request?"
4. Client agrees
5. Agent continues gathering information but frames questions around the desired behaviour rather than reproduction steps
6. Flow continues from Journey 1, step 11, with type set to "feature request"
