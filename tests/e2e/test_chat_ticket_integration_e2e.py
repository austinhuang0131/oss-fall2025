"""End-to-end tests for chat-ticket integration using Discord and Trello.

These tests verify that the entire integration system works with real implementations:
- Discord client (from koitu/oss-taapp)
- Trello ticket client (local implementation)

Required environment variables:
- DISCORD_ACCESS_TOKEN: Discord bot token
- TRELLO_API_KEY: Trello API key
- TRELLO_API_SECRET: Trello API secret
- TRELLO_TOKEN: Trello OAuth token (or will be generated)
- TEST_DISCORD_CHANNEL_ID: Discord channel ID for testing
- TEST_TRELLO_BOARD_ID: Trello board ID for testing (optional, will create if not provided)
"""

from __future__ import annotations

import asyncio
import contextlib
import os

import pytest
from discord_client_impl.discord_impl import DiscordClient
from dotenv import load_dotenv
from tickets_api.src.tickets_api import TicketStatus
from trello_ticket_impl.trello_ticket_impl import TrelloTicketClientImpl

from chat_ticket_integration import ChatTicketIntegration

# Load environment variables from .env file
_ = load_dotenv()


@pytest.fixture
def discord_client() -> DiscordClient:
    """Create a Discord client with credentials from environment."""
    access_token = os.getenv("DISCORD_ACCESS_TOKEN")
    if not access_token:
        pytest.skip("DISCORD_ACCESS_TOKEN not set")

    return DiscordClient(access_token=access_token)


@pytest.fixture
def discord_channel_id() -> str:
    """Get the Discord channel ID for testing."""
    channel_id = os.getenv("TEST_DISCORD_CHANNEL_ID")
    if not channel_id:
        pytest.skip("TEST_DISCORD_CHANNEL_ID not set")
    return channel_id


@pytest.fixture
def trello_client() -> TrelloTicketClientImpl:
    """Create a Trello ticket client with credentials from environment."""
    token = os.getenv("TRELLO_TOKEN")
    if not token:
        pytest.skip("TRELLO_TOKEN not set")

    board_id = os.getenv("TEST_TRELLO_BOARD_ID")

    return TrelloTicketClientImpl(token=token, board_id=board_id)


@pytest.fixture
def integration(
    discord_client: DiscordClient,
    trello_client: TrelloTicketClientImpl,
    discord_channel_id: str,
) -> ChatTicketIntegration:
    """Create a chat-ticket integration instance."""
    return ChatTicketIntegration(
        chat_api=discord_client,  # type: ignore[arg-type]
        ticket_api=trello_client,
        channel_id=discord_channel_id,
        poll_interval=1.0,
    )


@pytest.mark.e2e
@pytest.mark.local_credentials
@pytest.mark.asyncio
async def test_e2e_create_ticket_from_discord(
    discord_client: DiscordClient,
    trello_client: TrelloTicketClientImpl,
    integration: ChatTicketIntegration,
) -> None:
    """Test creating a Trello ticket from a Discord message."""
    # Send a create command in Discord
    _ = discord_client.send_message(
        integration.channel_id,
        "!create E2E Test Ticket --desc This is an end-to-end test ticket",
    )

    # Wait a bit for the message to be sent
    await asyncio.sleep(2)

    # Process messages
    await integration._poll_and_process()

    # Wait for ticket creation
    await asyncio.sleep(2)

    # Search for the created ticket
    tickets = trello_client.search_tickets(query="E2E Test Ticket")
    assert len(tickets) > 0, "Ticket was not created"

    ticket = tickets[0]
    assert "E2E Test Ticket" in ticket.title
    assert ticket.description == "This is an end-to-end test ticket"
    assert ticket.status == TicketStatus.OPEN

    # Cleanup: delete the test ticket
    _ = trello_client.delete_ticket(ticket.id)


@pytest.mark.e2e
@pytest.mark.local_credentials
@pytest.mark.asyncio
async def test_e2e_full_ticket_lifecycle(
    discord_client: DiscordClient,
    trello_client: TrelloTicketClientImpl,
    integration: ChatTicketIntegration,
) -> None:
    """Test the full lifecycle of a ticket: create, update, get, delete."""
    channel_id = integration.channel_id

    # Step 1: Create ticket
    _ = discord_client.send_message(
        channel_id,
        "!create E2E Lifecycle Test --desc Testing full ticket lifecycle",
    )
    await asyncio.sleep(2)
    await integration._poll_and_process()
    await asyncio.sleep(2)

    # Find the created ticket
    tickets = trello_client.search_tickets(query="E2E Lifecycle Test")
    assert len(tickets) > 0, "Ticket was not created"
    ticket = tickets[0]
    ticket_id = ticket.id

    try:
        # Step 2: Update ticket name
        _ = discord_client.send_message(
            channel_id,
            f"!update {ticket_id} --name E2E Lifecycle Test Updated",
        )
        await asyncio.sleep(2)
        await integration._poll_and_process()
        await asyncio.sleep(2)

        updated_ticket = trello_client.get_ticket(ticket_id)
        assert updated_ticket is not None
        assert "E2E Lifecycle Test Updated" in updated_ticket.title

        # Step 3: Update ticket status
        _ = discord_client.send_message(
            channel_id,
            f"!update {ticket_id} --status in progress",
        )
        await asyncio.sleep(2)
        await integration._poll_and_process()
        await asyncio.sleep(2)

        updated_ticket = trello_client.get_ticket(ticket_id)
        assert updated_ticket is not None
        assert updated_ticket.status == TicketStatus.IN_PROGRESS

        # Step 4: Get ticket details (should send a message back)
        initial_messages = len(discord_client.get_messages(channel_id, limit=50))
        _ = discord_client.send_message(channel_id, f"!get {ticket_id}")
        await asyncio.sleep(2)
        await integration._poll_and_process()
        await asyncio.sleep(2)

        # Verify a response message was sent (increased message count)
        final_messages = len(discord_client.get_messages(channel_id, limit=50))
        assert final_messages > initial_messages, "No response message was sent"

        # Step 5: Close ticket
        _ = discord_client.send_message(
            channel_id,
            f"!update {ticket_id} --status closed",
        )
        await asyncio.sleep(2)
        await integration._poll_and_process()
        await asyncio.sleep(2)

        updated_ticket = trello_client.get_ticket(ticket_id)
        assert updated_ticket is not None
        assert updated_ticket.status == TicketStatus.CLOSED

        # Step 6: Delete ticket
        _ = discord_client.send_message(channel_id, f"!delete {ticket_id}")
        await asyncio.sleep(2)
        await integration._poll_and_process()
        await asyncio.sleep(2)

        # Verify ticket was deleted
        deleted_ticket = trello_client.get_ticket(ticket_id)
        assert deleted_ticket is None, "Ticket was not deleted"

    except Exception:
        # Cleanup on error
        with contextlib.suppress(Exception):
            _ = trello_client.delete_ticket(ticket_id)
        raise


@pytest.mark.e2e
@pytest.mark.local_credentials
@pytest.mark.asyncio
async def test_e2e_help_command(
    discord_client: DiscordClient,
    integration: ChatTicketIntegration,
) -> None:
    """Test that help command executes without errors."""
    # Send help command
    _ = discord_client.send_message(integration.channel_id, "!help")
    await asyncio.sleep(2)

    # Process messages
    await integration._poll_and_process()

    # If we get here without exception, the test passes


@pytest.mark.e2e
@pytest.mark.local_credentials
@pytest.mark.asyncio
async def test_e2e_invalid_command_ignored(
    discord_client: DiscordClient,
    trello_client: TrelloTicketClientImpl,
    integration: ChatTicketIntegration,
) -> None:
    """Test that invalid commands are ignored."""
    # Count existing tickets
    initial_tickets = len(trello_client.search_tickets())

    # Send invalid command
    _ = discord_client.send_message(
        integration.channel_id,
        "This is not a command, just a regular message",
    )
    await asyncio.sleep(2)

    # Process messages
    await integration._poll_and_process()
    await asyncio.sleep(2)

    # Verify no new tickets were created
    final_tickets = len(trello_client.search_tickets())
    assert final_tickets == initial_tickets, "Invalid command created a ticket"


@pytest.mark.e2e
@pytest.mark.local_credentials
@pytest.mark.asyncio
async def test_e2e_duplicate_message_not_processed(
    discord_client: DiscordClient,
    trello_client: TrelloTicketClientImpl,
    integration: ChatTicketIntegration,
) -> None:
    """Test that duplicate messages are not processed twice."""
    # Send a create command
    _ = discord_client.send_message(
        integration.channel_id,
        "!create E2E Duplicate Test --desc Testing duplicate prevention",
    )
    await asyncio.sleep(2)

    # Process the same messages twice
    await integration._poll_and_process()
    await asyncio.sleep(2)
    await integration._poll_and_process()
    await asyncio.sleep(2)

    # Should only create one ticket
    tickets = trello_client.search_tickets(query="E2E Duplicate Test")
    assert len(tickets) == 1, f"Expected 1 ticket, found {len(tickets)}"

    # Cleanup
    _ = trello_client.delete_ticket(tickets[0].id)
