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
- TEST_OPENAI_API_KEY: openai API key
"""

from __future__ import annotations

import asyncio
import contextlib
import os

import pytest
from discord_client_impl.discord_impl import DiscordClient
from dotenv import load_dotenv
from openai_impl import OpenAIClient  # type: ignore[import-untyped]
from tickets_api.src.tickets_api import TicketStatus
from trello_ticket_impl.trello_ticket_impl import TrelloTicketClientImpl

from ai_chat_ticket_integration import AiChatTicketIntegration

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
def openai_client() -> OpenAIClient:
    """Create a openai client with credentials from environment."""
    api_key = os.getenv("TEST_OPENAI_API_KEY")
    if not api_key:
        pytest.skip("TEST_OPENAI_API_KEY not set")

    return OpenAIClient(api_key=api_key)


@pytest.fixture
def integration(
    discord_client: DiscordClient,
    trello_client: TrelloTicketClientImpl,
    openai_client: OpenAIClient,
    discord_channel_id: str,
) -> AiChatTicketIntegration:
    """Create a chat-ticket integration instance."""
    return AiChatTicketIntegration(
        chat_api=discord_client,  # type: ignore[arg-type]
        ticket_api=trello_client,
        ai_api=openai_client,  # type: ignore[arg-type]
        channel_id=discord_channel_id,
        poll_interval=1.0,
    )


@pytest.mark.e2e
@pytest.mark.local_credentials
@pytest.mark.asyncio
async def test_e2e_create_ticket_from_discord(
    discord_client: DiscordClient,
    trello_client: TrelloTicketClientImpl,
    integration: AiChatTicketIntegration,
) -> None:
    """Test creating a Trello ticket from a Discord message."""
    # Send a create command in Discord using natural language
    _ = discord_client.send_message(
        integration.channel_id,
        'Create a ticket named "E2E Test Ticket" with description "This is an end-to-end test ticket".',
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
    integration: AiChatTicketIntegration,
) -> None:
    """Test the full lifecycle of a ticket: create, update, get, delete."""
    channel_id = integration.channel_id

    # Step 1: Create ticket using natural language
    _ = discord_client.send_message(
        channel_id,
        "Create a ticket called 'E2E Lifecycle Test' with description 'Testing full ticket lifecycle'",
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
        # Step 2: Update ticket name using natural language
        _ = discord_client.send_message(
            channel_id,
            f"Update ticket {ticket_id} and rename it to 'E2E Lifecycle Test Updated'",
        )
        await asyncio.sleep(2)
        await integration._poll_and_process()
        await asyncio.sleep(2)

        updated_ticket = trello_client.get_ticket(ticket_id)
        assert updated_ticket is not None
        assert "E2E Lifecycle Test Updated" in updated_ticket.title

        # Step 3: Update ticket status using natural language
        _ = discord_client.send_message(
            channel_id,
            f"Change ticket {ticket_id} status to in progress",
        )
        await asyncio.sleep(2)
        await integration._poll_and_process()
        await asyncio.sleep(2)

        updated_ticket = trello_client.get_ticket(ticket_id)
        assert updated_ticket is not None
        assert updated_ticket.status == TicketStatus.IN_PROGRESS

        # Step 4: Get ticket details using natural language (should send a message back)
        initial_messages = len(discord_client.get_messages(channel_id, limit=50))
        _ = discord_client.send_message(channel_id, f"Show me the details for ticket {ticket_id}")
        await asyncio.sleep(2)
        await integration._poll_and_process()
        await asyncio.sleep(2)

        # Verify a response message was sent (increased message count)
        final_messages = len(discord_client.get_messages(channel_id, limit=50))
        assert final_messages > initial_messages, "No response message was sent"

        # Step 5: Close ticket using natural language
        _ = discord_client.send_message(
            channel_id,
            f"Close ticket {ticket_id}",
        )
        await asyncio.sleep(2)
        await integration._poll_and_process()
        await asyncio.sleep(2)

        updated_ticket = trello_client.get_ticket(ticket_id)
        assert updated_ticket is not None
        assert updated_ticket.status == TicketStatus.CLOSED

        # Step 6: Delete ticket using natural language
        _ = discord_client.send_message(channel_id, f"Delete ticket {ticket_id}")
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
    integration: AiChatTicketIntegration,
) -> None:
    """Test that help command executes without errors."""
    # Send help request using natural language
    _ = discord_client.send_message(integration.channel_id, "help")
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
    integration: AiChatTicketIntegration,
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
    integration: AiChatTicketIntegration,
) -> None:
    """Test that duplicate messages are not processed twice."""
    # Send a create command using natural language
    _ = discord_client.send_message(
        integration.channel_id,
        "Create a ticket called 'E2E Duplicate Test' with description 'Testing duplicate prevention'",
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
