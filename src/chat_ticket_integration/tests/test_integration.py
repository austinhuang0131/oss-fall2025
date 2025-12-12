"""Tests for chat ticket integration."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from chat_ticket_integration.integration import ChatAPI, TicketAPI

from chat_ticket_integration import ChatTicketIntegration


class MockChatAPI(ChatAPI):
    """Mock chat API for testing."""

    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    def get_messages(self, channel_id: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Return mock messages."""
        return self.messages[:max_results]

    def add_message(self, message_id: str, content: str) -> None:
        """Add a mock message."""
        self.messages.append({"id": message_id, "content": content})


class MockTicketAPI(TicketAPI):
    """Mock ticket API for testing."""

    def __init__(self) -> None:
        self.cards: dict[str, dict[str, Any]] = {}
        self.lists: dict[str, dict[str, Any]] = {
            "list1": {"id": "list1", "name": "To Do", "board_id": "board1"},
        }
        self.next_card_id = 1

    async def create_card(self, list_id: str, name: str, description: str | None = None) -> dict[str, Any]:
        """Create a mock card."""
        card_id = f"card{self.next_card_id}"
        self.next_card_id += 1
        card = {"id": card_id, "name": name, "description": description, "list_id": list_id}
        self.cards[card_id] = card
        return card

    async def get_card(self, card_id: str) -> dict[str, Any]:
        """Get a mock card."""
        if card_id not in self.cards:
            raise ValueError(f"Card {card_id} not found")
        return self.cards[card_id]

    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        description: str | None = None,
        list_id: str | None = None,
    ) -> dict[str, Any]:
        """Update a mock card."""
        if card_id not in self.cards:
            raise ValueError(f"Card {card_id} not found")

        card = self.cards[card_id]
        if name is not None:
            card["name"] = name
        if description is not None:
            card["description"] = description
        if list_id is not None:
            card["list_id"] = list_id

        return card

    async def delete_card(self, card_id: str) -> bool:
        """Delete a mock card."""
        if card_id in self.cards:
            del self.cards[card_id]
            return True
        return False

    async def get_cards(self, list_id: str) -> list[dict[str, Any]]:
        """Get all cards in a list."""
        return [card for card in self.cards.values() if card["list_id"] == list_id]

    async def get_lists(self, board_id: str) -> list[dict[str, Any]]:
        """Get all lists in a board."""
        return [lst for lst in self.lists.values() if lst["board_id"] == board_id]


@pytest.mark.asyncio
async def test_create_card_command() -> None:
    """Test creating a card via chat command."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "!create Test Card")

    await integration._poll_and_process()

    assert len(ticket_api.cards) == 1
    card = list(ticket_api.cards.values())[0]
    assert card["name"] == "Test Card"
    assert card["description"] is None


@pytest.mark.asyncio
async def test_create_card_with_description() -> None:
    """Test creating a card with description."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "!create Test Card --desc This is a test description")

    await integration._poll_and_process()

    assert len(ticket_api.cards) == 1
    card = list(ticket_api.cards.values())[0]
    assert card["name"] == "Test Card"
    assert card["description"] == "This is a test description"


@pytest.mark.asyncio
async def test_update_card_command() -> None:
    """Test updating a card via chat command."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    # Create a card first
    card = await ticket_api.create_card("list1", "Original Name")
    card_id = card["id"]

    # Update the card
    chat_api.add_message("msg1", f"!update {card_id} --name Updated Name")

    await integration._poll_and_process()

    updated_card = await ticket_api.get_card(card_id)
    assert updated_card["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_card_command() -> None:
    """Test deleting a card via chat command."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    # Create a card first
    card = await ticket_api.create_card("list1", "Test Card")
    card_id = card["id"]

    # Delete the card
    chat_api.add_message("msg1", f"!delete {card_id}")

    await integration._poll_and_process()

    assert card_id not in ticket_api.cards


@pytest.mark.asyncio
async def test_get_card_command() -> None:
    """Test getting a card via chat command."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    # Create a card first
    card = await ticket_api.create_card("list1", "Test Card")
    card_id = card["id"]

    # Get the card
    chat_api.add_message("msg1", f"!get {card_id}")

    await integration._poll_and_process()

    # Command should execute without error


@pytest.mark.asyncio
async def test_list_command() -> None:
    """Test listing via chat command."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    # List all lists
    chat_api.add_message("msg1", "!list")

    await integration._poll_and_process()

    # Command should execute without error


@pytest.mark.asyncio
async def test_duplicate_message_not_processed() -> None:
    """Test that duplicate messages are not processed."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "!create Test Card")

    # Process the same message twice
    await integration._poll_and_process()
    await integration._poll_and_process()

    # Should only create one card
    assert len(ticket_api.cards) == 1


@pytest.mark.asyncio
async def test_invalid_command_ignored() -> None:
    """Test that invalid commands are ignored."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "This is not a command")

    await integration._poll_and_process()

    # Should not create any cards
    assert len(ticket_api.cards) == 0


@pytest.mark.asyncio
async def test_help_command() -> None:
    """Test help command."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "!help")

    await integration._poll_and_process()


@pytest.mark.asyncio
async def test_list_cards_in_specific_list() -> None:
    """Test listing cards in a specific list."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    # Create cards
    await ticket_api.create_card("list1", "Card 1")
    await ticket_api.create_card("list1", "Card 2")

    # List cards in specific list
    chat_api.add_message("msg1", "!list list1")

    await integration._poll_and_process()


@pytest.mark.asyncio
async def test_update_card_multiple_fields() -> None:
    """Test updating multiple fields of a card."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    # Create a card
    card = await ticket_api.create_card("list1", "Original Name", "Original Description")
    card_id = card["id"]

    # Update multiple fields
    chat_api.add_message("msg1", f"!update {card_id} --name New Name --desc New Description")

    await integration._poll_and_process()

    updated_card = await ticket_api.get_card(card_id)
    assert updated_card["name"] == "New Name"
    assert updated_card["description"] == "New Description"


@pytest.mark.asyncio
async def test_start_stop() -> None:
    """Test starting and stopping the integration."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.01,
    )

    # Start in background
    task = asyncio.create_task(integration.start())

    # Let it run briefly
    await asyncio.sleep(0.05)

    # Stop it
    integration.stop()

    # Wait for task to complete
    try:
        await asyncio.wait_for(task, timeout=1.0)
    except TimeoutError:
        pass


@pytest.mark.asyncio
async def test_message_with_object_attributes() -> None:
    """Test processing messages with object attributes."""
    chat_api = MockChatAPI()
    ticket_api = MockTicketAPI()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        board_id="board1",
        poll_interval=0.1,
    )

    # Create a message with attributes
    class Message:
        def __init__(self, id: str, content: str):
            self.id = id
            self.content = content

    msg = Message("msg1", "!create Test Card")
    chat_api.messages = [msg]

    await integration._poll_and_process()

    assert len(ticket_api.cards) == 1
