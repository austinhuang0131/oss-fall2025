"""Example integration usage with other teams' implementations.

This demonstrates how to use the ChatTicketIntegration class with
concrete implementations from other teams.
"""

import asyncio
import logging
import os
from typing import Any

from chat_ticket_integration.integration import ChatAPI, TicketAPI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MailClientChatAdapter(ChatAPI):
    """Adapter to use mail client as chat API.

    This adapter treats emails as chat messages, allowing the integration
    to work with any mail client implementation.
    """

    def __init__(self, mail_client: Any) -> None:
        """Initialize with a mail client instance."""
        self.mail_client = mail_client

    def get_messages(self, channel_id: str, max_results: int = 10) -> list[Any]:
        """Get messages from the mail client.

        Args:
            channel_id: Used as a label/filter for messages
            max_results: Maximum number of messages to return

        Returns:
            List of message objects

        """
        try:
            messages = list(self.mail_client.get_messages(max_results=max_results))
            return messages
        except Exception:
            logger.exception("Error getting messages from mail client")
            return []


class KanbanClientTicketAdapter(TicketAPI):
    """Adapter to use kanban client as ticket API.

    This adapter wraps a kanban client to provide the ticket API interface.
    """

    def __init__(self, kanban_client: Any) -> None:
        """Initialize with a kanban client instance."""
        self.kanban_client = kanban_client

    async def create_card(self, list_id: str, name: str, description: str | None = None) -> Any:
        """Create a new card."""
        return await self.kanban_client.create_card(list_id, name, description)

    async def get_card(self, card_id: str) -> Any:
        """Get a card by ID."""
        return await self.kanban_client.get_card(card_id)

    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        description: str | None = None,
        list_id: str | None = None,
    ) -> Any:
        """Update a card."""
        return await self.kanban_client.update_card(card_id, name=name, description=description, list_id=list_id)

    async def delete_card(self, card_id: str) -> bool:
        """Delete a card."""
        return await self.kanban_client.delete_card(card_id)

    async def get_cards(self, list_id: str) -> list[Any]:
        """Get all cards in a list."""
        return await self.kanban_client.get_cards(list_id)

    async def get_lists(self, board_id: str) -> list[Any]:
        """Get all lists in a board."""
        return await self.kanban_client.get_lists(board_id)


async def main() -> None:
    """Main integration example."""
    # Configuration from environment variables
    channel_id = os.getenv("CHAT_CHANNEL_ID", "default-channel")
    board_id = os.getenv("TICKET_BOARD_ID", "default-board")
    poll_interval = float(os.getenv("POLL_INTERVAL", "1.0"))

    logger.info("Starting chat-ticket integration example")
    logger.info("Channel ID: %s", channel_id)
    logger.info("Board ID: %s", board_id)
    logger.info("Poll interval: %s seconds", poll_interval)

    # Example: Import and instantiate other teams' implementations
    # Uncomment and modify based on actual available implementations:

    # Option 1: Using Ivan's implementation (example)
    # try:
    #     from gmail_client_impl import get_client as get_gmail_client
    #     from kanban_client_adapter import get_client as get_kanban_client
    #
    #     mail_client = get_gmail_client(interactive=False)
    #     kanban_client = get_kanban_client()
    #
    #     chat_api = MailClientChatAdapter(mail_client)
    #     ticket_api = KanbanClientTicketAdapter(kanban_client)
    # except ImportError:
    #     logger.error("Failed to import required clients")
    #     return

    # For demonstration, we'll use a simple mock setup
    logger.warning("Using mock implementations - replace with actual clients")

    # Create mock implementations for demo purposes

    # Note: In production, you would:
    # 1. Import the actual implementations from other teams
    # 2. Instantiate them with proper credentials
    # 3. Wrap them with adapters if needed
    # 4. Pass them to the integration

    logger.info("Integration setup complete")
    logger.info("To use actual implementations:")
    logger.info("1. Install team packages via uv.sources in pyproject.toml")
    logger.info("2. Import their client factories")
    logger.info("3. Create adapter classes if API signatures differ")
    logger.info("4. Run the integration with: integration.start()")


if __name__ == "__main__":
    asyncio.run(main())
