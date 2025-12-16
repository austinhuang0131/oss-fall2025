"""Tests for chat ticket integration."""

from __future__ import annotations

import asyncio

import pytest
from chat_api.src.chat_api import ChatInterface, Message
from tickets_api.src.tickets_api import Ticket, TicketInterface, TicketStatus

from chat_ticket_integration import ChatTicketIntegration


class MockMessage(Message):
    """Mock message for testing."""

    def __init__(self, msg_id: str, content: str, sender_id: str = "test_sender") -> None:
        """Initialize the mock message."""
        self._id: str = msg_id
        self._content: str = content
        self._sender_id: str = sender_id

    @property
    def id(self) -> str:
        """Return the ID of the message."""
        return self._id

    @property
    def content(self) -> str:
        """Return the content of the message."""
        return self._content

    @property
    def sender_id(self) -> str:
        """Return the sender ID of the message."""
        return self._sender_id


class MockChatInterface(ChatInterface):
    """Mock chat interface for testing."""

    def __init__(self) -> None:  # noqa: D107
        self.messages: list[MockMessage] = []
        self.sent_messages: list[tuple[str, str]] = []

    def get_messages(self, channel_id: str, limit: int = 20) -> list[Message]:
        """Return mock messages."""
        return list(self.messages[:limit])  # type: ignore[return-value]

    def send_message(self, channel_id: str, content: str) -> bool:
        """Send a mock message."""
        self.sent_messages.append((channel_id, content))
        return True

    def delete_message(self, channel_id: str, message_id: str) -> bool:
        """Delete a specific message. Returns True if successful."""
        self.messages = [m for m in self.messages if m.id != message_id]
        return True

    def add_message(self, message_id: str, content: str) -> None:
        """Add a mock message (helper method for tests)."""
        self.messages.append(MockMessage(message_id, content))


class MockTicket(Ticket):
    """Mock ticket for testing."""

    def __init__(
        self,
        ticket_id: str,
        title: str,
        description: str,
        status: TicketStatus,
        assignee: str | None = None,
    ) -> None:
        """Initialize the mock ticket."""
        self._id: str = ticket_id
        self._title: str = title
        self._description: str = description
        self._status: TicketStatus = status
        self._assignee: str | None = assignee

    @property
    def id(self) -> str:
        """Return the ID of the ticket."""
        return self._id

    @property
    def title(self) -> str:
        """Return the title of the ticket."""
        return self._title

    @property
    def description(self) -> str:
        """Return the description of the ticket."""
        return self._description

    @property
    def status(self) -> TicketStatus:
        """Return the status of the ticket."""
        return self._status

    @property
    def assignee(self) -> str | None:
        """Return the assignee of the ticket."""
        return self._assignee


class MockTicketInterface(TicketInterface):
    """Mock ticket interface for testing."""

    def __init__(self) -> None:  # noqa: D107
        self.tickets: dict[str, MockTicket] = {}
        self.next_ticket_id: int = 1

    def create_ticket(
        self, title: str, description: str, assignee: str | None = None,
    ) -> Ticket:
        """Create a mock ticket."""
        ticket_id = f"ticket{self.next_ticket_id}"
        self.next_ticket_id += 1
        ticket = MockTicket(ticket_id, title, description, TicketStatus.OPEN, assignee)
        self.tickets[ticket_id] = ticket
        return ticket

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Get a mock ticket."""
        return self.tickets.get(ticket_id)

    def search_tickets(
        self, query: str | None = None, status: TicketStatus | None = None,
    ) -> list[Ticket]:
        """Search for mock tickets."""
        results: list[Ticket] = list(self.tickets.values())
        if status is not None:
            results = [t for t in results if t.status == status]
        if query is not None:
            results = [
                t for t in results
                if query.lower() in t.title.lower() or query.lower() in t.description.lower()
            ]
        return results

    def update_ticket(
        self,
        ticket_id: str,
        status: TicketStatus | None = None,
        title: str | None = None,
    ) -> Ticket:
        """Update a mock ticket."""
        ticket = self.tickets.get(ticket_id)
        if ticket is None:
            msg = f"Ticket {ticket_id} not found"
            raise ValueError(msg)

        # Create a new ticket with updated values
        new_title = title if title is not None else ticket.title
        new_status = status if status is not None else ticket.status
        updated_ticket = MockTicket(
            ticket_id, new_title, ticket.description, new_status, ticket.assignee,
        )
        self.tickets[ticket_id] = updated_ticket
        return updated_ticket

    def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a mock ticket."""
        if ticket_id in self.tickets:
            del self.tickets[ticket_id]
            return True
        return False


@pytest.mark.asyncio
async def test_create_card_command() -> None:
    """Test creating a ticket via chat command."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "!create Test Card")

    await integration._poll_and_process()

    assert len(ticket_api.tickets) == 1
    ticket = next(iter(ticket_api.tickets.values()))
    assert ticket.title == "Test Card"
    assert ticket.description == ""


@pytest.mark.asyncio
async def test_create_card_with_description() -> None:
    """Test creating a ticket with description."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "!create Test Card --desc This is a test description")

    await integration._poll_and_process()

    assert len(ticket_api.tickets) == 1
    ticket = next(iter(ticket_api.tickets.values()))
    assert ticket.title == "Test Card"
    assert ticket.description == "This is a test description"


@pytest.mark.asyncio
async def test_update_card_command() -> None:
    """Test updating a ticket via chat command."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    # Create a ticket first
    ticket = ticket_api.create_ticket("Original Name", "Description")
    ticket_id = ticket.id

    # Update the ticket
    chat_api.add_message("msg1", f"!update {ticket_id} --name Updated Name")

    await integration._poll_and_process()

    updated_ticket = ticket_api.get_ticket(ticket_id)
    assert updated_ticket is not None
    assert updated_ticket.title == "Updated Name"


@pytest.mark.asyncio
async def test_delete_card_command() -> None:
    """Test deleting a ticket via chat command."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    # Create a ticket first
    ticket = ticket_api.create_ticket("Test Card", "Description")
    ticket_id = ticket.id

    # Delete the ticket
    chat_api.add_message("msg1", f"!delete {ticket_id}")

    await integration._poll_and_process()

    assert ticket_id not in ticket_api.tickets


@pytest.mark.asyncio
async def test_get_card_command() -> None:
    """Test getting a ticket via chat command."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    # Create a ticket first
    ticket = ticket_api.create_ticket("Test Card", "Description")
    ticket_id = ticket.id

    # Get the ticket
    chat_api.add_message("msg1", f"!get {ticket_id}")

    await integration._poll_and_process()

    # Command should execute without error and send a message
    assert len(chat_api.sent_messages) == 1


@pytest.mark.asyncio
async def test_help_command() -> None:
    """Test help command."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "!help")

    await integration._poll_and_process()


@pytest.mark.asyncio
async def test_duplicate_message_not_processed() -> None:
    """Test that duplicate messages are not processed."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "!create Test Card")

    # Process the same message twice
    await integration._poll_and_process()
    await integration._poll_and_process()

    # Should only create one ticket
    assert len(ticket_api.tickets) == 1


@pytest.mark.asyncio
async def test_invalid_command_ignored() -> None:
    """Test that invalid commands are ignored."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    chat_api.add_message("msg1", "This is not a command")

    await integration._poll_and_process()

    # Should not create any tickets
    assert len(ticket_api.tickets) == 0


@pytest.mark.asyncio
async def test_update_ticket_status() -> None:
    """Test updating ticket status via chat command."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    # Create a ticket first
    ticket = ticket_api.create_ticket("Test Ticket", "Description")
    ticket_id = ticket.id

    # Update the ticket status
    chat_api.add_message("msg1", f"!update {ticket_id} --status closed")

    await integration._poll_and_process()

    updated_ticket = ticket_api.get_ticket(ticket_id)
    assert updated_ticket is not None
    assert updated_ticket.status == TicketStatus.CLOSED


@pytest.mark.asyncio
async def test_get_nonexistent_ticket() -> None:
    """Test getting a nonexistent ticket."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    # Try to get a nonexistent ticket
    chat_api.add_message("msg1", "!get nonexistent")

    await integration._poll_and_process()

    # Should send a not found message
    assert len(chat_api.sent_messages) == 1
    assert "not found" in chat_api.sent_messages[0][1].lower()


@pytest.mark.asyncio
async def test_update_ticket_multiple_fields() -> None:
    """Test updating multiple fields of a ticket."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    # Create a ticket
    ticket = ticket_api.create_ticket("Original Name", "Original Description")
    ticket_id = ticket.id

    # Update multiple fields (name and status)
    chat_api.add_message("msg1", f"!update {ticket_id} --name New Name --status in progress")

    await integration._poll_and_process()

    updated_ticket = ticket_api.get_ticket(ticket_id)
    assert updated_ticket is not None
    assert updated_ticket.title == "New Name"
    assert updated_ticket.status == TicketStatus.IN_PROGRESS


@pytest.mark.asyncio
async def test_start_stop() -> None:
    """Test starting and stopping the integration."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.01,
    )

    # Start in background
    task = asyncio.create_task(integration.start())

    # Let it run briefly
    await asyncio.sleep(0.05)

    # Stop it
    integration.stop()

    # Wait for task to complete
    import contextlib
    with contextlib.suppress(TimeoutError):
        await asyncio.wait_for(task, timeout=1.0)


@pytest.mark.asyncio
async def test_message_with_object_attributes() -> None:
    """Test processing messages with object attributes."""
    chat_api = MockChatInterface()
    ticket_api = MockTicketInterface()

    integration = ChatTicketIntegration(
        chat_api=chat_api,
        ticket_api=ticket_api,
        channel_id="channel1",
        poll_interval=0.1,
    )

    # MockMessage already has the right attributes
    msg = MockMessage(msg_id="msg1", content="!create Test Card")
    chat_api.messages = [msg]

    await integration._poll_and_process()

    assert len(ticket_api.tickets) == 1
