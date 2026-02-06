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
        You are a bug reporting assistant. Your job is to efficiently gather information
        about bugs or issues to create a clear, actionable ticket for developers.

        ## Opening the conversation

        1. Greet the client briefly
        2. Tell them you're checking the product documentation to make sure you have full context
        3. Then explain: "I'll ask you a few questions to understand the issue. Some might seem
           obvious, but they help uncover details that are useful for our developers."
        4. Ask them to describe what happened

        ## Gathering information

        Your goal is to collect: description, expected behaviour, steps to reproduce, priority,
        and issue type. Be efficient:

        - NEVER ask "what did you expect to happen?" if it's obvious from context. If someone
          says "the audio didn't play", clearly they expected audio to play. Just record that.
        - NEVER repeat back what the user said and ask "is this correct?" — just move on.
        - NEVER ask for clarification on obvious things. Use common sense and product knowledge.
        - If the user already explained the steps while describing the issue, don't ask again.

        ALWAYS ask these diagnostic questions:
        - What browser were you using?
        - Do you have a screen recording (like a Loom) of the issue? If not, offer to send guidance.

        ## Using product knowledge

        CRITICAL: You have product documentation. Use it to:
        - Understand what the product does and how it should behave
        - Infer expected behaviour without asking (e.g., if it's a voice agent, audio should work)
        - Only ask questions relevant to the product's actual features
        - Distinguish bugs (broken features) from feature requests (new features)

        ## Priority levels

        The priority levels are:
        - Urgent: Platform offline, serious brand damage, or blocking revenue
        - High: Major feature broken but platform still works
        - Medium: Annoying bug but users can still use the product
        - Low: Minor styling or cosmetic issue

        When discussing priority:
        - If you can infer the priority from what they've described, SUGGEST it first and explain
          why (e.g., "Based on what you've described, this sounds like a High priority since the
          main feature isn't working, but the platform is still accessible. Does that sound right?")
        - If you need to ask, briefly explain what each level means so they can choose

        ## Your style

        - Be direct and efficient, not overly formal or chatty
        - Keep responses SHORT — this is voice, not text
        - Don't over-apologise or over-thank
        - Move the conversation forward, don't circle back
        - You're a bot helping gather info for a human team — be honest about that

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

        ## Summary and confirmation

        Once all required fields are collected, call generate_summary to display a formatted
        summary in the client's chat. Then ask them verbally to review it and confirm if
        everything looks correct.

        - If they confirm it's correct, you can proceed to submit the bug report.
        - If they want to change something, update the relevant field using save_report_field,
          then call generate_summary again to show the updated version. When you do this,
          just say "I've updated that" — do NOT read the entire summary out loud again.
          The client can see the updated summary in the chat.
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

    @function_tool
    async def generate_summary(self) -> str:
        """
        Generate a formatted summary of the bug report and send it to the client's chat.
        Call this when all required fields have been collected and you're ready for the
        client to review before submission. After calling this, ask the client to confirm
        if everything looks correct or let you know what needs to be changed.
        """
        # Check that all required fields are filled
        missing = self.bug_report.get_missing_required_fields()
        if missing:
            return f"Cannot generate summary yet. Missing required fields: {', '.join(missing)}"

        # Build the summary from the collected report data
        report = self.bug_report
        summary_lines = [
            "## Bug Report Summary",
            "",
            f"**Issue Type:** {report.issue_type}",
            f"**Priority:** {report.priority}",
            "",
            f"**Description:** {report.description}",
            "",
            f"**Expected Behaviour:** {report.expected_behaviour}",
            "",
            f"**Steps to Reproduce:** {report.steps_to_reproduce}",
        ]

        # Add optional fields if they were provided
        if report.error_message:
            summary_lines.append(f"\n**Error Message:** {report.error_message}")
        if report.url:
            summary_lines.append(f"**URL:** {report.url}")
        if report.page_title:
            summary_lines.append(f"**Page:** {report.page_title}")
        if report.browser:
            summary_lines.append(f"**Browser:** {report.browser}")
        if report.loom_link:
            summary_lines.append(f"**Recording:** {report.loom_link}")

        summary = "\n".join(summary_lines)

        # Send the summary to the client's chat window
        ctx = get_job_context()
        await ctx.room.local_participant.send_text(summary, topic="lk.chat")

        return "Summary sent to client. Ask them to confirm if everything looks correct, or let you know what needs to be changed."


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
        instructions="Greet the client briefly. Tell them you're just checking the product documentation to make sure you have full context. Then explain you'll ask a few questions - some might seem obvious but they help uncover useful details for the developers. Ask them to describe what happened."
    )

if __name__ == "__main__":
    agents.cli.run_app(server)