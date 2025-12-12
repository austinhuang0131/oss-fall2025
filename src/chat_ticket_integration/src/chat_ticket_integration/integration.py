"""Integration class for chat and ticket systems."""

from __future__ import annotations

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class ChatAPI(ABC):
    """Abstract chat API interface."""

    @abstractmethod
    def get_messages(self, channel_id: str, max_results: int = 10) -> Iterator[Any]:
        """Get messages from a channel."""


class TicketAPI(ABC):
    """Abstract ticket API interface."""

    @abstractmethod
    async def create_card(self, list_id: str, name: str, description: str | None = None) -> Any:
        """Create a new ticket card."""

    @abstractmethod
    async def get_card(self, card_id: str) -> Any:
        """Get a ticket card by ID."""

    @abstractmethod
    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        description: str | None = None,
        list_id: str | None = None,
    ) -> Any:
        """Update a ticket card."""

    @abstractmethod
    async def delete_card(self, card_id: str) -> bool:
        """Delete a ticket card."""

    @abstractmethod
    async def get_cards(self, list_id: str) -> list[Any]:
        """Get all cards in a list."""

    @abstractmethod
    async def get_lists(self, board_id: str) -> list[Any]:
        """Get all lists in a board."""


class ChatTicketIntegration:
    """Integration between chat and ticket systems.

    This class bridges chat APIs with ticket APIs, enabling command-based
    ticket management through chat messages.
    """

    def __init__(
        self,
        chat_api: ChatAPI,
        ticket_api: TicketAPI,
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
                r"^!update\s+(\S+)(?:\s+--name\s+(.+?))?(?:\s+--desc\s+(.+?))?(?:\s+--list\s+(\S+))?$", re.IGNORECASE | re.DOTALL
            ),
            "delete": re.compile(r"^!delete\s+(\S+)$", re.IGNORECASE),
            "get": re.compile(r"^!get\s+(\S+)$", re.IGNORECASE),
            "list": re.compile(r"^!list(?:\s+(\S+))?$", re.IGNORECASE),
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
            messages = self.chat_api.get_messages(self.channel_id, max_results=20)

            for message in messages:
                message_id = self._get_message_id(message)

                if message_id in self._processed_message_ids:
                    continue

                self._processed_message_ids.add(message_id)

                content = self._get_message_content(message)
                if content:
                    await self._process_command(content, message)

        except Exception:
            logger.exception("Error polling messages")

    def _get_message_id(self, message: Any) -> str:
        """Extract message ID from message object."""
        if hasattr(message, "id"):
            return message.id
        if isinstance(message, dict):
            return message.get("id", str(id(message)))
        return str(id(message))

    def _get_message_content(self, message: Any) -> str:
        """Extract content from message object."""
        if hasattr(message, "content"):
            return message.content
        if hasattr(message, "body"):
            return message.body
        if isinstance(message, dict):
            return message.get("content", message.get("body", ""))
        return str(message)

    async def _process_command(self, content: str, message: Any) -> None:
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
                return

    async def _handle_create(self, groups: tuple[str, ...]) -> None:
        """Handle create command: !create <name> [--desc <description>]"""
        name = groups[0].strip()
        description = groups[1].strip() if len(groups) > 1 and groups[1] else None

        # Get the first list in the board
        lists = await self.ticket_api.get_lists(self.board_id)
        if not lists:
            logger.error("No lists found in board %s", self.board_id)
            return

        list_id = lists[0].id if hasattr(lists[0], "id") else lists[0].get("id")

        card = await self.ticket_api.create_card(list_id, name, description)
        logger.info("Created card: %s", card)

    async def _handle_update(self, groups: tuple[str, ...]) -> None:
        """Handle update command: !update <card_id> [--name <name>] [--desc <description>] [--list <list_id>]"""
        card_id = groups[0].strip()
        name = groups[1].strip() if len(groups) > 1 and groups[1] else None
        description = groups[2].strip() if len(groups) > 2 and groups[2] else None
        list_id = groups[3].strip() if len(groups) > 3 and groups[3] else None

        card = await self.ticket_api.update_card(card_id, name=name, description=description, list_id=list_id)
        logger.info("Updated card: %s", card)

    async def _handle_delete(self, groups: tuple[str, ...]) -> None:
        """Handle delete command: !delete <card_id>"""
        card_id = groups[0].strip()

        result = await self.ticket_api.delete_card(card_id)
        logger.info("Deleted card %s: %s", card_id, result)

    async def _handle_get(self, groups: tuple[str, ...]) -> None:
        """Handle get command: !get <card_id>"""
        card_id = groups[0].strip()

        card = await self.ticket_api.get_card(card_id)
        logger.info("Retrieved card: %s", card)

    async def _handle_list(self, groups: tuple[str, ...]) -> None:
        """Handle list command: !list [<list_id>]"""
        list_id = groups[0].strip() if groups and groups[0] else None

        if list_id:
            cards = await self.ticket_api.get_cards(list_id)
            logger.info("Cards in list %s: %s", list_id, cards)
        else:
            lists = await self.ticket_api.get_lists(self.board_id)
            logger.info("Lists in board: %s", lists)

    async def _handle_help(self, _groups: tuple[str, ...]) -> None:
        """Handle help command: !help."""
        help_text = """
Available commands:
- !create <name> [--desc <description>]: Create a new ticket
- !update <card_id> [--name <name>] [--desc <description>] [--list <list_id>]: Update a ticket
- !delete <card_id>: Delete a ticket
- !get <card_id>: Get ticket details
- !list [<list_id>]: List all lists or cards in a list
- !help: Show this help message
        """
        logger.info("Help: %s", help_text.strip())
