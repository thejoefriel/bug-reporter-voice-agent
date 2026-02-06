import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional
from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent, room_io, function_tool, get_job_context
from livekit.plugins import openai, noise_cancellation

load_dotenv(".env.local")

# Configuration: path to the product repo whose docs we'll load
TARGET_REPO_PATH = os.getenv("TARGET_REPO_PATH")

# URL to Loom recording guidance document (shown to clients who need help recording)
LOOM_GUIDANCE_URL = os.getenv("LOOM_GUIDANCE_URL", "https://support.loom.com/hc/en-us/articles/360002158057-Getting-started-with-Loom")


def load_product_docs(repo_path: str) -> str:
    """
    Load all markdown documentation from a repo's docs/ai folder.

    Args:
        repo_path: Absolute path to the product repository

    Returns:
        Combined content of all .md files, with filenames as headers
    """
    docs_path = Path(repo_path) / "docs" / "ai"

    # Check if the docs folder exists
    if not docs_path.exists():
        return f"No documentation found at {docs_path}"

    # Find all markdown files
    md_files = sorted(docs_path.glob("*.md"))  # sorted() for consistent order

    if not md_files:
        return f"No .md files found in {docs_path}"

    # Read each file and combine with a header
    sections = []
    for file in md_files:
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()
        # Use the filename (without extension) as a section header
        filename = file.stem  # e.g., "PROJECT_OVERVIEW" from "PROJECT_OVERVIEW.md"
        sections.append(f"### {filename}\n\n{content}")

    return "\n\n---\n\n".join(sections)


# Load product documentation at startup (if configured)
# This runs once when the module is imported, not on every request
PRODUCT_DOCS = load_product_docs(TARGET_REPO_PATH) if TARGET_REPO_PATH else None


def build_agent_instructions() -> str:
    """
    Build the full system instructions for the agent, including product docs if available.

    Returns:
        The complete instruction string for the agent
    """
    # Base instructions (the core persona and conversation flow)
    base_instructions = """
        You are a friendly and professional bug reporting assistant. Your job is to help
        clients report bugs or issues they are experiencing with a product. You guide
        them through a structured conversation to gather all the information needed to
        create a clear, actionable ticket.

        ## Your conversation flow

        1. Greet the client and explain what will happen during this conversation. The point is to help clarify the issue. It means they may be asked a couple of times what's happening, and that is just to try and spot and information that might be useful for our developers. 
        2. Ask them to describe the issue they're facing.
        3. Listen carefully and ask clarifying questions to understand the problem.
        4. Gather diagnostic details by asking relevant questions. Examples:
           - Did you see an error message? If so, what did it say?
           - What was the URL in your browser when the issue occurred?
           - What was the title or name of the page you were on?
           - What browser are you using (Chrome, Safari, Firefox, etc.)?
           IMPORTANT: Only ask questions that are relevant to the product's actual features.
           Check the product documentation to understand what the product has. For example,
           if the product has no login system, do not ask about login or user accounts.
        5. Help them articulate what they expected to happen versus what actually happened.
        6. If the client hasn't already described the steps they took, guide them through
           recalling what happened. But if they've already explained the sequence of events
           while describing the issue, don't ask them to repeat it — just confirm you understood.
        7. Help them determine the priority level based on these definitions:
           - Urgent: The platform is offline or in a state causing serious brand damage
             or restriction on income. Response within 1 hour, resolve within 1 day.
           - High: A brand or function issue, e.g. part of the platform is damaged but
             not offline. Response within 1 working day, resolve within 3 working days.
           - Medium: An error that inhibits typical user experience but does not prevent
             use of the tool or cause direct revenue loss. Response within 1 working day,
             resolve within 8 working days.
           - Low: An error that does not inhibit user experience, such as a styling issue.
             Response within 2 working days, resolution time agreed with client.
        8. Ask if they have a screen recording of the issue (e.g. a Loom recording).

        ## Your behaviour

        - Be conversational and patient. Clients will likely not be technical.
        - IMPORTANT: Do not make clients repeat themselves. If they've already explained
          something (like what steps they took), don't ask again. Extract the information
          from what they've already said and confirm your understanding instead.
        - Keep the conversation moving — don't over-thank or be overly formal.
        - Apologise that they are facing issues
        - Reassure them that even though you are a bot, this is designed to help them break down the issue and then share it with our very human team!
        - Ask one or two questions at a time, not a long list.
        - Summarise what you've understood back to the client to confirm accuracy. Only do this once you have a number of bits of information. 
        - If the client is unsure about priority, help them by asking about the impact
          (is the platform down? is it affecting revenue? can they still use the tool?).
        - Do not submit anything until you have gathered all the information and the
          client has confirmed the summary.
        - Keep your responses concise — this is a voice conversation.

        ## Using your tools

        As you gather information, use the save_report_field tool to record each piece.
        Valid field names are:
        - description: What the issue is
        - expected_behaviour: What should have happened
        - steps_to_reproduce: How to recreate the issue
        - priority: Must be one of: Urgent, High, Medium, Low
        - issue_type: Must be one of: bug, feature_request
        - error_message: Any error message they saw
        - logged_in_user: Their email or username if logged in
        - url: The URL where the issue occurred
        - page_title: The title of the page they were on
        - browser: Which browser they were using
        - loom_link: Link to their screen recording

        Use get_report_status to check what you've collected and what's still missing.
        The required fields are: description, expected_behaviour, steps_to_reproduce,
        priority, and issue_type. Don't ask to submit until all required fields are filled.

        ## Sharing links and text with the client

        Use send_text_to_client to display text in the client's chat window. This is useful for:
        - Sharing links they need to click
        - Displaying summaries they can review
        - Showing the final GitHub issue URL

        IMPORTANT: When sharing links or asking for text input, you MUST actually call
        the tool — don't just say you're sharing a link. The client can't see links
        unless you call the tool.

        - send_loom_guidance: Call this when the client needs help creating a screen recording.
          It sends them a clickable link to Loom's getting started guide.
        - request_text_input: Call this when you need the client to type something (like a
          URL or email). It opens the chat and prompts them to type there.
    """

    # If we have product docs, add them to help the agent understand the product
    if PRODUCT_DOCS:
        product_context = f"""

        ## Product knowledge

        IMPORTANT: You have documentation about the specific product below. You MUST use
        this to tailor your questions. Do not ask about features the product doesn't have.

        Use the product documentation to:
        - Understand what features exist and how they should work
        - ONLY ask diagnostic questions relevant to the product's actual features
        - If the product has no login system, never ask about login or user accounts
        - If the product has no dashboard, never ask about dashboard issues
        - Determine if what the client describes is a bug (something broken) or a
          feature request (something that doesn't exist yet)
        - Reference specific parts of the product when clarifying the issue

        Here is the product documentation:

        {PRODUCT_DOCS}
        """
        return base_instructions + product_context
    else:
        return base_instructions


@dataclass
class BugReport:
    """Holds all the information gathered during a bug report conversation."""

    # Core fields (required for a complete report)
    description: Optional[str] = None
    expected_behaviour: Optional[str] = None
    steps_to_reproduce: Optional[str] = None
    priority: Optional[str] = None  # Urgent, High, Medium, Low
    issue_type: Optional[str] = None  # bug, feature_request

    # Diagnostic fields (optional but helpful)
    error_message: Optional[str] = None
    logged_in_user: Optional[str] = None
    url: Optional[str] = None
    page_title: Optional[str] = None
    browser: Optional[str] = None
    loom_link: Optional[str] = None

    def get_missing_required_fields(self) -> list[str]:
        """Returns a list of required fields that haven't been filled in yet."""
        required = ['description', 'expected_behaviour', 'steps_to_reproduce', 'priority', 'issue_type']
        return [f for f in required if getattr(self, f) is None]

    def get_filled_fields(self) -> dict:
        """Returns a dict of all fields that have been filled in."""
        all_fields = [
            'description', 'expected_behaviour', 'steps_to_reproduce', 'priority',
            'issue_type', 'error_message', 'logged_in_user', 'url', 'page_title',
            'browser', 'loom_link'
        ]
        return {f: getattr(self, f) for f in all_fields if getattr(self, f) is not None}

class BugReporterAgent(Agent):
    def __init__(self):
        # Each agent instance has its own bug report to track the conversation
        self.bug_report = BugReport()

        # Build instructions with product docs (if configured)
        super().__init__(
            instructions=build_agent_instructions(),
        )

    @function_tool
    async def save_report_field(self, field_name: str, value: str) -> str:
        """
        Save a piece of information to the bug report.

        Args:
            field_name: The field to save. Must be one of: description, expected_behaviour,
                       steps_to_reproduce, priority, issue_type, error_message, logged_in_user,
                       url, page_title, browser, loom_link
            value: The value to save for this field
        """
        valid_fields = [
            'description', 'expected_behaviour', 'steps_to_reproduce', 'priority',
            'issue_type', 'error_message', 'logged_in_user', 'url', 'page_title',
            'browser', 'loom_link'
        ]

        if field_name not in valid_fields:
            return f"Error: '{field_name}' is not a valid field. Valid fields are: {', '.join(valid_fields)}"

        # Validate priority values
        if field_name == 'priority' and value not in ['Urgent', 'High', 'Medium', 'Low']:
            return f"Error: priority must be one of: Urgent, High, Medium, Low. Got: {value}"

        # Validate issue_type values
        if field_name == 'issue_type' and value not in ['bug', 'feature_request']:
            return f"Error: issue_type must be one of: bug, feature_request. Got: {value}"

        setattr(self.bug_report, field_name, value)
        return f"Saved {field_name}: {value}"

    @function_tool
    async def get_report_status(self) -> str:
        """
        Check the current status of the bug report.
        Returns what has been collected and what required fields are still missing.
        """
        filled = self.bug_report.get_filled_fields()
        missing = self.bug_report.get_missing_required_fields()

        status_parts = []

        if filled:
            status_parts.append("Collected so far:")
            for field_name, value in filled.items():
                # Truncate long values for readability
                display_value = value if len(value) <= 100 else value[:100] + "..."
                status_parts.append(f"  - {field_name}: {display_value}")

        if missing:
            status_parts.append(f"\nStill needed (required): {', '.join(missing)}")
        else:
            status_parts.append("\nAll required fields collected! Ready to summarise and confirm with the client.")

        return "\n".join(status_parts)

    @function_tool
    async def send_text_to_client(self, message: str) -> str:
        """
        Send a text message that appears in the client's chat window.
        Use this to share links, summaries, or important information they need to see.
        The chat window will automatically open when you use this tool.

        Args:
            message: The text to display. Can include markdown links like [text](url).
        """
        # get_job_context() retrieves the current LiveKit session context
        ctx = get_job_context()

        # send_text() sends a data message to the "lk.chat" topic
        # which is the standard LiveKit chat topic that frontend components listen to
        await ctx.room.local_participant.send_text(message, topic="lk.chat")

        return f"Sent to client: {message}"

    @function_tool
    async def send_loom_guidance(self) -> str:
        """
        Send the Loom recording guidance link to the client.
        Use this when the client doesn't have a recording and wants help creating one.
        The chat window will automatically open to show the link.
        """
        ctx = get_job_context()

        message = f"Here's a guide on how to create a Loom recording: {LOOM_GUIDANCE_URL}"
        await ctx.room.local_participant.send_text(message, topic="lk.chat")

        return f"Sent Loom guidance link to client: {LOOM_GUIDANCE_URL}"

    @function_tool
    async def request_text_input(self, prompt: str) -> str:
        """
        Ask the client to type something in the chat. Use this when you need them to
        provide a link, email, or other text that's easier to type than speak.
        The chat window will automatically open.

        Args:
            prompt: What you want them to type (e.g., "Please paste the Loom link here")
        """
        ctx = get_job_context()

        await ctx.room.local_participant.send_text(prompt, topic="lk.chat")

        return f"Asked client to type: {prompt}"


server = AgentServer()

@server.rtc_session()
async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        llm=openai.realtime.RealtimeModel(
            voice="alloy",
            model="gpt-realtime-mini",
        )
    )

    await session.start(
        room=ctx.room,
        agent=BugReporterAgent(),
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
            ),
        ),
    )

    await session.generate_reply(
        instructions="Greet the client warmly and let them know you're here to help them report a bug or issue. Ask them to start by describing what happened."
    )

if __name__ == "__main__":
    agents.cli.run_app(server)