"""Integration class for chat and ticket systems."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import TYPE_CHECKING

from tickets_api.src.tickets_api import TicketStatus

if TYPE_CHECKING:
    from chat_api.src.chat_api import ChatInterface, Message
    from tickets_api.src.tickets_api import Ticket, TicketInterface

logger = logging.getLogger(__name__)


class ChatTicketIntegration:
    """Integration between chat and ticket systems.

    This class bridges chat APIs with ticket APIs, enabling command-based
    ticket management through chat messages.
    """

    def __init__(
        self,
        chat_api: ChatInterface,
        ticket_api: TicketInterface,
        channel_id: str,
        board_id: str,
        poll_interval: float = 1.0,
    ) -> None:
        """Initialize the integration.

        Args:
            chat_api: Chat API implementation
            ticket_api: Ticket API implementation
            channel_id: Fixed channel ID for chat operations
            board_id: Fixed board ID for ticket operations
            poll_interval: Polling interval in seconds (default: 1.0)

        """
        self.chat_api = chat_api
        self.ticket_api = ticket_api
        self.channel_id = channel_id
        self.board_id = board_id
        self.poll_interval = poll_interval
        self._running = False
        self._processed_message_ids: set[str] = set()

        # Command patterns
        self._command_patterns = {
            "create": re.compile(r"^!create\s+(.+?)(?:\s+--desc\s+(.+))?$", re.IGNORECASE | re.DOTALL),
            "update": re.compile(
                r"^!update\s+(\S+)(?:\s+--name\s+(.+?))?(?:\s+--status\s+(.+?))?$", re.IGNORECASE | re.DOTALL,
            ),
            "delete": re.compile(r"^!delete\s+(\S+)$", re.IGNORECASE),
            "get": re.compile(r"^!get\s+(\S+)$", re.IGNORECASE),
            "help": re.compile(r"^!help$", re.IGNORECASE),
        }

    async def start(self) -> None:
        """Start the integration polling loop."""
        self._running = True
        logger.info("Starting chat-ticket integration")

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
            messages = self.chat_api.get_messages(self.channel_id, limit=2)

            for message in messages:
                message_id = message.id

                if message_id in self._processed_message_ids:
                    continue

                self._processed_message_ids.add(message_id)

                content = message.content
                if content:
                    await self._process_command(content, message)

        except Exception:
            logger.exception("Error polling messages")

    async def _process_command(self, content: str, _message: Message) -> None:
        """Process a command from message content."""
        content = content.strip()

        for command_type, pattern in self._command_patterns.items():
            match = pattern.match(content)
            if match:
                handler = getattr(self, f"_handle_{command_type}", None)
                if handler:
                    try:
                        await handler(match.groups())
                    except Exception:
                        logger.exception("Error handling %s command", command_type)
                        _ = self.chat_api.send_message(
                            self.channel_id, f"Error processing {command_type} command.",
                        )
                return

    async def _handle_create(self, groups: tuple[str, ...]) -> None:
        """Handle create command: !create <name> [--desc <description>]."""
        name = groups[0].strip()
        description = groups[1].strip() if len(groups) > 1 and groups[1] else ""

        card = self.ticket_api.create_ticket(name, description, None)
        _ = self.chat_api.send_message(
            self.channel_id, f"Created ticket with ID {card.id}.\n\n{await self._format_ticket_details(card)}",
        )
        logger.info("Created card: %s", card)

    async def _handle_update(self, groups: tuple[str, ...]) -> None:
        """Handle update command: !update <card_id> [--name <name>] [--status <status>]."""
        card_id = groups[0].strip()
        name = groups[1].strip() if len(groups) > 1 and groups[1] else None
        status_raw = groups[2].strip() if len(groups) > 2 and groups[2] else None  # noqa: PLR2004
        # interpret status_raw to TicketStatus
        status: TicketStatus | None = None
        if status_raw:  # Only validate if status was provided
            match status_raw.lower():
                case "open":
                    status = TicketStatus.OPEN
                case "in progress":
                    status = TicketStatus.IN_PROGRESS
                case "closed":
                    status = TicketStatus.CLOSED
                case _:
                    _ = self.chat_api.send_message(
                        self.channel_id, f"Invalid status '{status_raw}'. Valid statuses are: open, in progress, closed.",
                    )
                    return

        card = self.ticket_api.update_ticket(card_id, status, name)
        _ = self.chat_api.send_message(
            self.channel_id, f"Created ticket with ID {card.id}.\n\n{await self._format_ticket_details(card)}",
        )
        logger.info("Updated card: %s", card)

    async def _handle_delete(self, groups: tuple[str, ...]) -> None:
        """Handle delete command: !delete <card_id>."""
        card_id = groups[0].strip()

        result = self.ticket_api.delete_ticket(card_id)
        _ = self.chat_api.send_message(
            self.channel_id, f"Deleted ticket with ID {card_id}." if result else f"Ticket with ID {card_id} not found.",
        )
        logger.info("Deleted card %s: %s", card_id, result)

    async def _handle_get(self, groups: tuple[str, ...]) -> None:
        """Handle get command: !get <card_id>."""
        card_id = groups[0].strip()

        card = self.ticket_api.get_ticket(card_id)
        _ = self.chat_api.send_message(
            self.channel_id, await self._format_ticket_details(card) if card else f"Ticket with ID {card_id} not found.",
        )
        logger.info("Retrieved card: %s", card)

    async def _handle_help(self, _groups: tuple[str, ...]) -> None:
        """Handle help command: !help."""
        help_text = """
Available commands:
- !create <name> [--desc <description>]: Create a new ticket
- !update <card_id> [--name <name>] [--desc <description>] [--list <list_id>]: Update a ticket
- !delete <card_id>: Delete a ticket
- !get <card_id>: Get ticket details
- !help: Show this help message
        """
        logger.info("Help: %s", help_text.strip())

    async def _format_ticket_details(self, ticket: Ticket) -> str:
        """Format ticket details for display."""
        return (
            f"Ticket ID: {ticket.id}\n"
            f"Title: {ticket.title}\n"
            f"Description: {ticket.description}\n"
            f"Status: {ticket.status.name}\n"
        )
