"""Integration class for AI, chat and ticket systems."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

from tickets_api.src.tickets_api import TicketStatus

try:
    from opentelemetry import metrics

    TELEMETRY_AVAILABLE = True
except ImportError:
    TELEMETRY_AVAILABLE = False

if TYPE_CHECKING:
    from ai_api.src.ai_api import AIInterface
    from chat_api.src.chat_api import ChatInterface, Message
    from opentelemetry.metrics import Histogram
    from opentelemetry.metrics._internal.instrument import Counter
    from tickets_api.src.tickets_api import Ticket, TicketInterface

logger = logging.getLogger(__name__)

# System prompt for AI to parse natural language commands
SYSTEM_PROMPT = """You are a ticket management assistant that interprets natural language requests \
and converts them into structured ticket operations.

Analyze the user's message and determine which ticket operation they want to perform:
- CREATE: User wants to create a new ticket (e.g., "create a ticket", "make a new task", "add a ticket")
- UPDATE: User wants to update an existing ticket (e.g., "update ticket", "change status", "rename ticket")
- DELETE: User wants to delete a ticket (e.g., "delete ticket", "remove task")
- GET: User wants to view/retrieve a ticket (e.g., "show me ticket", "get ticket details", "view ticket")
- SEARCH: User wants to search/list tickets (e.g., "search for tickets", "find tickets about login", "list all open tickets", "show me closed tickets")
- HELP: User needs help or information about available commands
- UNKNOWN: The request doesn't match any ticket operation

Extract relevant parameters:
- For CREATE: extract 'title' (required) and 'description' (optional)
- For UPDATE: extract 'ticket_id' (required), 'title' (optional), and 'status' (optional, \
must be one of: "open", "in_progress", "closed")
- For DELETE: extract 'ticket_id' (required)
- For GET: extract 'ticket_id' (required)
- For SEARCH: extract 'query' (optional, search text) and 'status' (optional, must be one of: "open", "in_progress", "closed")

Return a structured response matching the provided schema."""

# Response schema for AI structured output
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["CREATE", "UPDATE", "DELETE", "GET", "SEARCH", "HELP", "UNKNOWN"],
            "description": "The ticket operation to perform",
        },
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["open", "in_progress", "closed"]},
                "query": {"type": "string"},
            },
            "additionalProperties": False,
            "required": ["ticket_id", "title", "status", "description", "query"],
            "description": "Parameters for the action",
        },
    },
    "required": ["action", "parameters"],
}


class AiChatTicketIntegration:
    """Integration between chat and ticket systems.

    This class bridges chat, AI and ticket APIs, enabling natural language-based
    ticket management through chat messages.
    """

    def __init__(
        self,
        chat_api: ChatInterface,
        ticket_api: TicketInterface,
        ai_api: AIInterface,
        channel_id: str,
        poll_interval: float = 1.0,
    ) -> None:
        """Initialize the integration.

        Args:
            chat_api: Chat API implementation
            ticket_api: Ticket API implementation
            ai_api: AI API implementation
            channel_id: Fixed channel ID for chat operations
            poll_interval: Polling interval in seconds (default: 1.0)

        """
        self.chat_api = chat_api
        self.ticket_api = ticket_api
        self.ai_api = ai_api
        self.channel_id = channel_id
        self.poll_interval = poll_interval
        self._running = False
        # assume message IDs are ordered and thus comparable
        self._last_process_message_id = ""

        # Initialize OpenTelemetry metrics if available
        self._request_counter: Counter | None = None
        self._success_counter: Counter | None = None
        self._failure_counter: Counter | None = None
        self._latency_histogram: Histogram | None = None
        if TELEMETRY_AVAILABLE:
            meter = metrics.get_meter(__name__)
            self._request_counter = meter.create_counter(
                name="integration_requests_total",
                description="Total number of processed messages",
                unit="1",
            )
            self._success_counter = meter.create_counter(
                name="integration_requests_success",
                description="Number of successfully processed messages",
                unit="1",
            )
            self._failure_counter = meter.create_counter(
                name="integration_requests_failure",
                description="Number of failed message processing attempts",
                unit="1",
            )
            self._latency_histogram = meter.create_histogram(
                name="integration_request_duration",
                description="Message processing duration in milliseconds",
                unit="ms",
            )

    async def start(self) -> None:
        """Start the integration polling loop."""
        self._running = True
        logger.info("Starting AI-chat-ticket integration")

        try:
            while self._running:
                await self._poll_and_process()
                await asyncio.sleep(self.poll_interval)
        except Exception:
            logger.exception("Error in polling loop")
            raise

    def stop(self) -> None:
        """Stop the integration polling loop."""
        self._running = False
        logger.info("Stopping chat-ticket integration")

    async def _poll_and_process(self) -> None:
        """Poll messages and process commands."""
        try:
            # Run the blocking get_messages call in a thread
            messages = await asyncio.to_thread(self.chat_api.get_messages, self.channel_id, limit=2)

            for message in messages:
                message_id = message.id

                if message_id <= self._last_process_message_id:
                    continue

                self._last_process_message_id = message_id

                content = message.content
                if content:
                    await self._process_command(content, message)

        except Exception:
            logger.exception("Error polling messages")

    async def _process_command(self, content: str, _message: Message) -> None:
        """Process a natural language message using AI to extract intent and parameters."""
        content = content.strip()
        start_time = time.time()
        success = False

        try:
            # Record request
            if self._request_counter:
                self._request_counter.add(1, {"channel_id": self.channel_id})

            # Use AI to parse the natural language message
            ai_response = await asyncio.to_thread(
                self.ai_api.generate_response,
                user_input=content,
                system_prompt=SYSTEM_PROMPT,
                response_schema=RESPONSE_SCHEMA,
            )

            # Parse the AI response
            parsed_action = self._parse_ai_response(ai_response)

            if not parsed_action:
                _ = self.chat_api.send_message(
                    self.channel_id, "Sorry, I couldn't understand your request. Please try again.",
                )
                return

            action = parsed_action["action"]
            parameters: dict[str, Any] = parsed_action.get("parameters", {})

            # Delegate action routing to a separate method
            success = await self._route_action(action, parameters)

        except Exception:
            logger.exception("Error processing natural language command")
            _ = self.chat_api.send_message(
                self.channel_id, "An error occurred while processing your request.",
            )
        finally:
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000

            if self._latency_histogram:
                self._latency_histogram.record(
                    latency_ms,
                    {
                        "channel_id": self.channel_id,
                        "success": str(success),
                    },
                )

            if success and self._success_counter:
                self._success_counter.add(1, {"channel_id": self.channel_id})
            elif not success and self._failure_counter:
                self._failure_counter.add(1, {"channel_id": self.channel_id})

    async def _route_action(self, action: str, parameters: dict[str, Any]) -> bool:
        """Route the parsed action to the appropriate handler."""
        try:
            if action == "CREATE":
                await self._handle_create(parameters)
            elif action == "UPDATE":
                await self._handle_update(parameters)
            elif action == "DELETE":
                await self._handle_delete(parameters)
            elif action == "GET":
                await self._handle_get(parameters)
            elif action == "SEARCH":
                await self._handle_search(parameters)
            elif action == "HELP":
                await self._handle_help(())
            elif action == "UNKNOWN":
                _ = self.chat_api.send_message(
                    self.channel_id,
                    "I'm not sure what you want to do. Try asking me to create, update, get, search, or delete a ticket.",
                )
            else:
                _ = self.chat_api.send_message(
                    self.channel_id,
                    "Unrecognized action. Please try again.",
                )
                return False
        except Exception:
            logger.exception("Error routing action: %s", action)
            _ = self.chat_api.send_message(
                self.channel_id, "An error occurred while handling your request.",
            )
            return False
        else:
            return True

    def _parse_ai_response(self, ai_response: str | dict[str, Any]) -> dict[str, Any] | None:
        """Parse the AI response into a structured format.

        Args:
            ai_response: Response from AI (either dict if structured, or str if conversational)

        Returns:
            Parsed action dictionary or None if parsing failed

        """
        if isinstance(ai_response, dict):
            # AI returned structured data
            return ai_response

        # If AI returned a string, we can't parse it properly
        logger.warning("AI returned unstructured response: %s", ai_response)
        return None

    async def _handle_create(self, parameters: dict[str, Any]) -> None:
        """Handle create action from natural language.

        Args:
            parameters: Dict with 'title' (required) and 'description' (optional)

        """
        title = parameters.get("title", "").strip()
        description = parameters.get("description", "").strip()

        if not title:
            _ = self.chat_api.send_message(
                self.channel_id, "I need a title to create a ticket. Please specify what the ticket should be called.",
            )
            return

        try:
            ticket = self.ticket_api.create_ticket(title, description, None)
            _ = self.chat_api.send_message(
                self.channel_id,
                f"Created ticket with ID {ticket.id}.\n\n{await self._format_ticket_details(ticket)}",
            )
            logger.info("Created ticket: %s", ticket)
        except Exception:
            logger.exception("Error creating ticket")
            _ = self.chat_api.send_message(
                self.channel_id, "Failed to create the ticket. Please try again.",
            )

    async def _handle_update(self, parameters: dict[str, Any]) -> None:
        """Handle update action from natural language.

        Args:
            parameters: Dict with 'ticket_id' (required), 'title' (optional), 'status' (optional)

        """
        ticket_id = parameters.get("ticket_id", "").strip()
        title = parameters.get("title")
        status_raw = parameters.get("status")

        if not ticket_id:
            _ = self.chat_api.send_message(
                self.channel_id, "I need a ticket ID to update. Please specify which ticket to update.",
            )
            return

        # Parse status if provided
        status: TicketStatus | None = None
        if status_raw:
            status_lower = str(status_raw).lower()
            if status_lower == "open":
                status = TicketStatus.OPEN
            elif status_lower in ("in progress", "in_progress"):
                status = TicketStatus.IN_PROGRESS
            elif status_lower == "closed":
                status = TicketStatus.CLOSED
            else:
                _ = self.chat_api.send_message(
                    self.channel_id,
                    f"Invalid status '{status_raw}'. Valid statuses are: open, in progress, closed.",
                )
                return

        # Convert title to string if provided
        title_str: str | None = str(title).strip() if title else None

        try:
            ticket = self.ticket_api.update_ticket(ticket_id, status, title_str)
            _ = self.chat_api.send_message(
                self.channel_id, f"Updated ticket with ID {ticket.id}.\n\n{await self._format_ticket_details(ticket)}",
            )
            logger.info("Updated ticket: %s", ticket)
        except Exception:
            logger.exception("Error updating ticket")
            _ = self.chat_api.send_message(
                self.channel_id, f"Failed to update ticket {ticket_id}. It may not exist.",
            )

    async def _handle_delete(self, parameters: dict[str, Any]) -> None:
        """Handle delete action from natural language.

        Args:
            parameters: Dict with 'ticket_id' (required)

        """
        ticket_id = parameters.get("ticket_id", "").strip()

        if not ticket_id:
            _ = self.chat_api.send_message(
                self.channel_id, "I need a ticket ID to delete. Please specify which ticket to delete.",
            )
            return

        try:
            result = self.ticket_api.delete_ticket(ticket_id)
            _ = self.chat_api.send_message(
                self.channel_id,
                f"Deleted ticket with ID {ticket_id}." if result else f"Ticket with ID {ticket_id} not found.",
            )
            logger.info("Deleted ticket %s: %s", ticket_id, result)
        except Exception:
            logger.exception("Error deleting ticket")
            _ = self.chat_api.send_message(
                self.channel_id, f"Failed to delete ticket {ticket_id}.",
            )

    async def _handle_get(self, parameters: dict[str, Any]) -> None:
        """Handle get action from natural language.

        Args:
            parameters: Dict with 'ticket_id' (required)

        """
        ticket_id = parameters.get("ticket_id", "").strip()

        if not ticket_id:
            _ = self.chat_api.send_message(
                self.channel_id, "I need a ticket ID to retrieve. Please specify which ticket to get.",
            )
            return

        try:
            ticket = self.ticket_api.get_ticket(ticket_id)
            _ = self.chat_api.send_message(
                self.channel_id,
                await self._format_ticket_details(ticket) if ticket else f"Ticket with ID {ticket_id} not found.",
            )
            logger.info("Retrieved ticket: %s", ticket)
        except Exception:
            logger.exception("Error retrieving ticket")
            _ = self.chat_api.send_message(
                self.channel_id, f"Failed to retrieve ticket {ticket_id}.",
            )

    async def _handle_search(self, parameters: dict[str, Any]) -> None:
        """Handle search action from natural language.

        Args:
            parameters: Dict with 'query' (optional) and 'status' (optional)

        """
        query = parameters.get("query", "").strip() or None
        status_raw = parameters.get("status")

        # Parse status if provided
        status: TicketStatus | None = None
        if status_raw:
            status_lower = str(status_raw).lower()
            if status_lower == "open":
                status = TicketStatus.OPEN
            elif status_lower in ("in progress", "in_progress"):
                status = TicketStatus.IN_PROGRESS
            elif status_lower == "closed":
                status = TicketStatus.CLOSED
            else:
                _ = self.chat_api.send_message(
                    self.channel_id,
                    f"Invalid status '{status_raw}'. Valid statuses are: open, in progress, closed.",
                )
                return

        try:
            # Check if ticket_api has search_tickets method
            if not hasattr(self.ticket_api, "search_tickets"):
                _ = self.chat_api.send_message(
                    self.channel_id,
                    "Search functionality is not available with the current ticket system.",
                )
                return

            # Run search in a thread since search_tickets is synchronous
            tickets = await asyncio.to_thread(
                self.ticket_api.search_tickets,  # type: ignore[attr-defined]
                query=query,
                status=status,
            )

            if not tickets:
                search_desc = []
                if query:
                    search_desc.append(f"query '{query}'")
                if status:
                    search_desc.append(f"status {status.name}")
                search_text = " and ".join(search_desc) if search_desc else "your criteria"
                _ = self.chat_api.send_message(
                    self.channel_id,
                    f"No tickets found matching {search_text}.",
                )
                return

            # Format the results
            result_lines = [f"Found {len(tickets)} ticket(s):"]
            for ticket in tickets[:10]:  # Limit to first 10 to avoid overwhelming the chat
                result_lines.append(f"\n**{ticket.title}** (ID: {ticket.id})")
                result_lines.append(f"  Status: {ticket.status.name}")
                if ticket.description:
                    desc_preview = ticket.description[:50] + "..." if len(ticket.description) > 50 else ticket.description
                    result_lines.append(f"  Description: {desc_preview}")

            if len(tickets) > 10:
                result_lines.append(f"\n... and {len(tickets) - 10} more tickets.")

            _ = self.chat_api.send_message(
                self.channel_id,
                "\n".join(result_lines),
            )
            logger.info("Found %d tickets matching search criteria", len(tickets))
        except Exception:
            logger.exception("Error searching tickets")
            _ = self.chat_api.send_message(
                self.channel_id, "Failed to search for tickets. Please try again.",
            )

    async def _handle_help(self, _groups: tuple[str, ...]) -> None:
        """Handle help command."""
        help_text = """
I can help you manage tickets using natural language! Here are some examples:

**Create a ticket:**
- "Create a ticket called 'Fix login bug'"
- "Make a new task for implementing user authentication"
- "Add a ticket to track the homepage redesign with description: update the UI"

**Update a ticket:**
- "Update ticket ABC123 to in progress"
- "Change ticket DEF456 status to closed"
- "Rename ticket GHI789 to 'New feature request'"

**Get ticket details:**
- "Show me ticket ABC123"
- "Get details for ticket DEF456"
- "What's in ticket GHI789?"

**Search for tickets:**
- "Search for tickets about login"
- "Find all open tickets"
- "List closed tickets"
- "Show me tickets with bug in the title"

**Delete a ticket:**
- "Delete ticket ABC123"
- "Remove ticket DEF456"

Just describe what you want to do in natural language, and I'll handle it!
        """
        _ = self.chat_api.send_message(
            self.channel_id,
            help_text.strip(),
        )

    async def _format_ticket_details(self, ticket: Ticket) -> str:
        """Format ticket details for display."""
        return (
            f"Ticket ID: {ticket.id}\n"
            f"Title: {ticket.title}\n"
            f"Description: {ticket.description}\n"
            f"Status: {ticket.status.name}\n"
        )
