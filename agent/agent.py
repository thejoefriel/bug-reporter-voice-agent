from dotenv import load_dotenv
from dataclasses import dataclass
from typing import Optional
from livekit import agents
from livekit.agents import AgentServer, AgentSession, Agent, room_io, function_tool
from livekit.plugins import openai, noise_cancellation

load_dotenv(".env.local")


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

        super().__init__(
            instructions="""
                You are a friendly and professional bug reporting assistant. Your job is to help
                clients report bugs or issues they are experiencing with a product. You guide
                them through a structured conversation to gather all the information needed to
                create a clear, actionable ticket.

                ## Your conversation flow

                1. Greet the client and ask them to describe the issue they're facing.
                2. Listen carefully and ask clarifying questions to understand the problem.
                3. Gather diagnostic details by asking relevant questions such as:
                   - Did you see an error message? If so, what did it say?
                   - Were you logged in at the time?
                   - If logged in, what email or username were you using?
                   - What was the URL in your browser when the issue occurred?
                   - What was the title or name of the page you were on?
                   - What browser are you using (Chrome, Safari, Firefox, etc.)?
                   Only ask the questions that are relevant — don't ask all of them every time.
                4. Help them articulate what they expected to happen versus what actually happened.
                5. Guide them through recalling the steps they took before the issue occurred.
                6. Help them determine the priority level based on these definitions:
                   - Urgent: The platform is offline or in a state causing serious brand damage
                     or restriction on income. Response within 1 hour, resolve within 1 day.
                   - High: A brand or function issue, e.g. part of the platform is damaged but
                     not offline. Response within 1 working day, resolve within 3 working days.
                   - Medium: An error that inhibits typical user experience but does not prevent
                     use of the tool or cause direct revenue loss. Response within 1 working day,
                     resolve within 8 working days.
                   - Low: An error that does not inhibit user experience, such as a styling issue.
                     Response within 2 working days, resolution time agreed with client.
                7. Ask if they have a screen recording of the issue (e.g. a Loom recording).

                ## Your behaviour

                - Be conversational and patient. Clients will likely not be technical.
                - Apologise that they are facing issues
                - Reassure them that even though you are a bot, this is designed to help them break down the issue and then share it with our very human team!
                - Ask one or two questions at a time, not a long list.
                - Summarise what you've understood back to the client to confirm accuracy.
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
            """,
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