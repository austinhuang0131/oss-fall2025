"""Unit tests for AI-powered natural language ticket integration."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock

import pytest
from tickets_api.src.tickets_api import TicketStatus

from ai_chat_ticket_integration import AiChatTicketIntegration


@pytest.fixture
def mock_chat_api() -> Mock:
    """Create a mock chat API."""
    chat_api = Mock()
    chat_api.get_messages = Mock(return_value=[])
    chat_api.send_message = Mock()
    return chat_api


@pytest.fixture
def mock_ticket_api() -> Mock:
    """Create a mock ticket API."""
    return Mock()


@pytest.fixture
def mock_ai_api() -> Mock:
    """Create a mock AI API."""
    return Mock()


@pytest.fixture
def integration(mock_chat_api: Mock, mock_ticket_api: Mock, mock_ai_api: Mock) -> AiChatTicketIntegration:
    """Create an integration instance with mocked dependencies."""
    return AiChatTicketIntegration(
        chat_api=mock_chat_api,
        ticket_api=mock_ticket_api,
        ai_api=mock_ai_api,
        channel_id="test-channel",
        poll_interval=0.1,
    )


class TestParseAiResponse:
    """Tests for AI response parsing."""

    def test_parse_structured_response(self, integration: AiChatTicketIntegration) -> None:
        """Test parsing a structured dict response."""
        ai_response: dict[str, Any] = {
            "action": "CREATE",
            "parameters": {"title": "Test ticket", "description": "Test description"},
        }

        result = integration._parse_ai_response(ai_response)

        assert result is not None
        assert result["action"] == "CREATE"
        assert result["parameters"]["title"] == "Test ticket"

    def test_parse_string_response_returns_none(self, integration: AiChatTicketIntegration) -> None:
        """Test that string responses return None."""
        ai_response = "This is a plain text response"

        result = integration._parse_ai_response(ai_response)

        assert result is None


class TestHandleCreateNl:
    """Tests for natural language create handler."""

    @pytest.mark.asyncio
    async def test_create_with_title_only(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test creating a ticket with only a title."""
        mock_ticket = Mock()
        mock_ticket.id = "ticket-123"
        mock_ticket.title = "Test ticket"
        mock_ticket.description = ""
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket_api.create_ticket = Mock(return_value=mock_ticket)

        await integration._handle_create({"title": "Test ticket"})

        mock_ticket_api.create_ticket.assert_called_once_with("Test ticket", "", None)
        assert mock_chat_api.send_message.called

    @pytest.mark.asyncio
    async def test_create_with_title_and_description(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test creating a ticket with title and description."""
        mock_ticket = Mock()
        mock_ticket.id = "ticket-456"
        mock_ticket.title = "Fix bug"
        mock_ticket.description = "Bug description"
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket_api.create_ticket = Mock(return_value=mock_ticket)

        await integration._handle_create({"title": "Fix bug", "description": "Bug description"})

        mock_ticket_api.create_ticket.assert_called_once_with("Fix bug", "Bug description", None)
        assert mock_chat_api.send_message.called

    @pytest.mark.asyncio
    async def test_create_without_title(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test that create without title sends error message."""
        await integration._handle_create({})

        mock_ticket_api.create_ticket.assert_not_called()
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "need a title" in call_args[1].lower()


class TestHandleUpdateNl:
    """Tests for natural language update handler."""

    @pytest.mark.asyncio
    async def test_update_status(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test updating ticket status."""
        mock_ticket = Mock()
        mock_ticket.id = "ticket-123"
        mock_ticket.title = "Test ticket"
        mock_ticket.description = "Test"
        mock_ticket.status = TicketStatus.IN_PROGRESS
        mock_ticket_api.update_ticket = Mock(return_value=mock_ticket)

        await integration._handle_update({"ticket_id": "ticket-123", "status": "in_progress"})

        mock_ticket_api.update_ticket.assert_called_once_with("ticket-123", TicketStatus.IN_PROGRESS, None)
        assert mock_chat_api.send_message.called

    @pytest.mark.asyncio
    async def test_update_title(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test updating ticket title."""
        mock_ticket = Mock()
        mock_ticket.id = "ticket-123"
        mock_ticket.title = "New title"
        mock_ticket.description = "Test"
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket_api.update_ticket = Mock(return_value=mock_ticket)

        await integration._handle_update({"ticket_id": "ticket-123", "title": "New title"})

        mock_ticket_api.update_ticket.assert_called_once_with("ticket-123", None, "New title")
        assert mock_chat_api.send_message.called

    @pytest.mark.asyncio
    async def test_update_without_ticket_id(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test that update without ticket ID sends error message."""
        await integration._handle_update({"status": "open"})

        mock_ticket_api.update_ticket.assert_not_called()
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "need a ticket id" in call_args[1].lower()

    @pytest.mark.asyncio
    async def test_update_with_invalid_status(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test that invalid status sends error message."""
        await integration._handle_update({"ticket_id": "ticket-123", "status": "invalid_status"})

        mock_ticket_api.update_ticket.assert_not_called()
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "invalid status" in call_args[1].lower()


class TestHandleDeleteNl:
    """Tests for natural language delete handler."""

    @pytest.mark.asyncio
    async def test_delete_success(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test deleting a ticket successfully."""
        mock_ticket_api.delete_ticket = Mock(return_value=True)

        await integration._handle_delete({"ticket_id": "ticket-123"})

        mock_ticket_api.delete_ticket.assert_called_once_with("ticket-123")
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "deleted" in call_args[1].lower()

    @pytest.mark.asyncio
    async def test_delete_not_found(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test deleting a non-existent ticket."""
        mock_ticket_api.delete_ticket = Mock(return_value=False)

        await integration._handle_delete({"ticket_id": "ticket-999"})

        mock_ticket_api.delete_ticket.assert_called_once_with("ticket-999")
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "not found" in call_args[1].lower()

    @pytest.mark.asyncio
    async def test_delete_without_ticket_id(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test that delete without ticket ID sends error message."""
        await integration._handle_delete({})

        mock_ticket_api.delete_ticket.assert_not_called()
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "need a ticket id" in call_args[1].lower()


class TestHandleGetNl:
    """Tests for natural language get handler."""

    @pytest.mark.asyncio
    async def test_get_success(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test getting a ticket successfully."""
        mock_ticket = Mock()
        mock_ticket.id = "ticket-123"
        mock_ticket.title = "Test ticket"
        mock_ticket.description = "Test description"
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket_api.get_ticket = Mock(return_value=mock_ticket)

        await integration._handle_get({"ticket_id": "ticket-123"})

        mock_ticket_api.get_ticket.assert_called_once_with("ticket-123")
        assert mock_chat_api.send_message.called

    @pytest.mark.asyncio
    async def test_get_not_found(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test getting a non-existent ticket."""
        mock_ticket_api.get_ticket = Mock(return_value=None)

        await integration._handle_get({"ticket_id": "ticket-999"})

        mock_ticket_api.get_ticket.assert_called_once_with("ticket-999")
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "not found" in call_args[1].lower()

    @pytest.mark.asyncio
    async def test_get_without_ticket_id(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test that get without ticket ID sends error message."""
        await integration._handle_get({})

        mock_ticket_api.get_ticket.assert_not_called()
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "need a ticket id" in call_args[1].lower()


class TestProcessCommand:
    """Tests for natural language command processing."""

    @pytest.mark.asyncio
    async def test_system_prompt_enables_correct_parsing(
        self, integration: AiChatTicketIntegration, mock_ai_api: Mock, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test that the system prompt enables AI to correctly parse commands."""
        # Create a mock AI that validates the system prompt content
        def mock_generate_response(user_input: str, system_prompt: str, response_schema: dict[str, Any]) -> dict[str, Any]:
            # Verify the prompt contains essential instructions
            assert "CREATE" in system_prompt
            assert "UPDATE" in system_prompt
            assert "DELETE" in system_prompt
            assert "GET" in system_prompt
            assert "ticket" in system_prompt.lower()

            # Verify schema is provided
            assert "action" in response_schema["properties"]
            assert "parameters" in response_schema["properties"]

            # Return appropriate response based on user input
            if "create" in user_input.lower():
                return {"action": "CREATE", "parameters": {"title": "Test ticket", "description": "Test"}}
            if "update" in user_input.lower():
                return {"action": "UPDATE", "parameters": {"ticket_id": "123", "status": "closed"}}
            if "delete" in user_input.lower():
                return {"action": "DELETE", "parameters": {"ticket_id": "123"}}
            if "show" in user_input.lower() or "get" in user_input.lower():
                return {"action": "GET", "parameters": {"ticket_id": "123"}}
            return {"action": "UNKNOWN", "parameters": {}}

        mock_ai_api.generate_response = Mock(side_effect=mock_generate_response)

        # Test CREATE
        mock_ticket = Mock()
        mock_ticket.id = "ticket-123"
        mock_ticket.title = "Test ticket"
        mock_ticket.description = "Test"
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket_api.create_ticket = Mock(return_value=mock_ticket)

        mock_message = Mock()
        await integration._process_command("Create a new ticket for testing", mock_message)

        mock_ticket_api.create_ticket.assert_called_once()
        mock_ai_api.generate_response.assert_called()

    @pytest.mark.asyncio
    async def test_process_create_command(
        self, integration: AiChatTicketIntegration, mock_ai_api: Mock, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test processing a create command via AI."""
        mock_ai_api.generate_response = Mock(
            return_value={"action": "CREATE", "parameters": {"title": "New ticket", "description": "Description"}},
        )
        mock_ticket = Mock()
        mock_ticket.id = "ticket-123"
        mock_ticket.title = "New ticket"
        mock_ticket.description = "Description"
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket_api.create_ticket = Mock(return_value=mock_ticket)

        mock_message = Mock()
        await integration._process_command("Create a new ticket called 'New ticket'", mock_message)

        mock_ai_api.generate_response.assert_called_once()
        # Verify system_prompt and response_schema were passed (but don't check exact values)
        call_kwargs = mock_ai_api.generate_response.call_args[1]
        assert "system_prompt" in call_kwargs
        assert "response_schema" in call_kwargs
        assert isinstance(call_kwargs["system_prompt"], str)
        assert isinstance(call_kwargs["response_schema"], dict)
        mock_ticket_api.create_ticket.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_update_command(
        self, integration: AiChatTicketIntegration, mock_ai_api: Mock, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test processing an update command via AI."""
        mock_ai_api.generate_response = Mock(
            return_value={"action": "UPDATE", "parameters": {"ticket_id": "ticket-123", "status": "closed"}},
        )
        mock_ticket = Mock()
        mock_ticket.id = "ticket-123"
        mock_ticket.title = "Test"
        mock_ticket.description = "Test"
        mock_ticket.status = TicketStatus.CLOSED
        mock_ticket_api.update_ticket = Mock(return_value=mock_ticket)

        mock_message = Mock()
        await integration._process_command("Close ticket ticket-123", mock_message)

        mock_ai_api.generate_response.assert_called_once()
        mock_ticket_api.update_ticket.assert_called_once_with("ticket-123", TicketStatus.CLOSED, None)

    @pytest.mark.asyncio
    async def test_process_unknown_command(
        self, integration: AiChatTicketIntegration, mock_ai_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test processing an unknown command."""
        mock_ai_api.generate_response = Mock(return_value={"action": "UNKNOWN", "parameters": {}})

        mock_message = Mock()
        await integration._process_command("What is the weather today?", mock_message)

        mock_ai_api.generate_response.assert_called_once()
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "not sure" in call_args[1].lower()

    @pytest.mark.asyncio
    async def test_process_help_command(
        self, integration: AiChatTicketIntegration, mock_ai_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test processing a help command."""
        mock_ai_api.generate_response = Mock(return_value={"action": "HELP", "parameters": {}})

        mock_message = Mock()
        await integration._process_command("help", mock_message)

        mock_ai_api.generate_response.assert_called_once()
        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "natural language" in call_args[1].lower()

    @pytest.mark.asyncio
    async def test_process_command_ai_error(
        self, integration: AiChatTicketIntegration, mock_ai_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test handling AI errors during command processing."""
        mock_ai_api.generate_response = Mock(side_effect=Exception("AI error"))

        mock_message = Mock()
        await integration._process_command("Create a ticket", mock_message)

        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "error" in call_args[1].lower()

    @pytest.mark.asyncio
    async def test_process_command_unstructured_response(
        self, integration: AiChatTicketIntegration, mock_ai_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test handling unstructured AI response."""
        mock_ai_api.generate_response = Mock(return_value="This is an unstructured string response")

        mock_message = Mock()
        await integration._process_command("Do something", mock_message)

        mock_chat_api.send_message.assert_called_once()
        call_args = mock_chat_api.send_message.call_args[0]
        assert "couldn't understand" in call_args[1].lower()


class TestHandleSearchNl:
    """Tests for natural language search handler."""

    @pytest.mark.asyncio
    async def test_search_with_query_and_status(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test searching tickets with query and status."""
        mock_ticket1 = Mock()
        mock_ticket1.id = "ticket-1"
        mock_ticket1.title = "Login bug"
        mock_ticket1.description = "Users can't login"
        mock_ticket1.status = TicketStatus.OPEN

        mock_ticket2 = Mock()
        mock_ticket2.id = "ticket-2"
        mock_ticket2.title = "Login issue"
        mock_ticket2.description = "Password reset broken"
        mock_ticket2.status = TicketStatus.OPEN

        mock_ticket_api.search_tickets = Mock(return_value=[mock_ticket1, mock_ticket2])

        await integration._handle_search({"query": "login", "status": "open"})

        mock_ticket_api.search_tickets.assert_called_once_with(
            query="login",
            status=TicketStatus.OPEN,
        )
        assert mock_chat_api.send_message.called
        call_args = mock_chat_api.send_message.call_args[0]
        assert "Found 2 ticket(s)" in call_args[1]

    @pytest.mark.asyncio
    async def test_search_with_query_only(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test searching tickets with only a query."""
        mock_ticket = Mock()
        mock_ticket.id = "ticket-1"
        mock_ticket.title = "Test ticket"
        mock_ticket.description = "Test description"
        mock_ticket.status = TicketStatus.OPEN

        mock_ticket_api.search_tickets = Mock(return_value=[mock_ticket])

        await integration._handle_search({"query": "test"})

        mock_ticket_api.search_tickets.assert_called_once_with(query="test", status=None)
        assert mock_chat_api.send_message.called

    @pytest.mark.asyncio
    async def test_search_no_results(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test searching with no results."""
        mock_ticket_api.search_tickets = Mock(return_value=[])

        await integration._handle_search({"query": "nonexistent"})

        mock_ticket_api.search_tickets.assert_called_once()
        assert mock_chat_api.send_message.called
        call_args = mock_chat_api.send_message.call_args[0]
        assert "No tickets found" in call_args[1]

    @pytest.mark.asyncio
    async def test_search_invalid_status(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test searching with invalid status."""
        await integration._handle_search({"status": "invalid"})

        assert mock_chat_api.send_message.called
        call_args = mock_chat_api.send_message.call_args[0]
        assert "Invalid status" in call_args[1]

    @pytest.mark.asyncio
    async def test_search_not_supported(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test search when ticket API doesn't support it."""
        delattr(mock_ticket_api, "search_tickets")

        await integration._handle_search({"query": "test"})

        assert mock_chat_api.send_message.called
        call_args = mock_chat_api.send_message.call_args[0]
        assert "not available" in call_args[1]

    @pytest.mark.asyncio
    async def test_search_with_many_results(
        self, integration: AiChatTicketIntegration, mock_ticket_api: Mock, mock_chat_api: Mock,
    ) -> None:
        """Test searching returns more than 10 tickets."""
        mock_tickets = []
        for i in range(15):
            mock_ticket = Mock()
            mock_ticket.id = f"ticket-{i}"
            mock_ticket.title = f"Ticket {i}"
            mock_ticket.description = "Description"
            mock_ticket.status = TicketStatus.OPEN
            mock_tickets.append(mock_ticket)

        mock_ticket_api.search_tickets = Mock(return_value=mock_tickets)

        await integration._handle_search({"query": "test"})

        assert mock_chat_api.send_message.called
        call_args = mock_chat_api.send_message.call_args[0]
        assert "Found 15 ticket(s)" in call_args[1]
        assert "5 more tickets" in call_args[1]


class TestHelperMethods:
    """Tests for helper methods."""

    def test_parse_ticket_status_valid(self, integration: AiChatTicketIntegration) -> None:
        """Test parsing valid status strings."""
        assert integration._parse_ticket_status("open") == TicketStatus.OPEN
        assert integration._parse_ticket_status("OPEN") == TicketStatus.OPEN
        assert integration._parse_ticket_status("in progress") == TicketStatus.IN_PROGRESS
        assert integration._parse_ticket_status("in_progress") == TicketStatus.IN_PROGRESS
        assert integration._parse_ticket_status("closed") == TicketStatus.CLOSED

    def test_parse_ticket_status_invalid(self, integration: AiChatTicketIntegration) -> None:
        """Test parsing invalid status strings."""
        assert integration._parse_ticket_status("invalid") is None
        assert integration._parse_ticket_status("") is None
        assert integration._parse_ticket_status(None) is None

    def test_format_search_results(self, integration: AiChatTicketIntegration) -> None:
        """Test formatting search results."""
        mock_ticket1 = Mock()
        mock_ticket1.id = "1"
        mock_ticket1.title = "Ticket 1"
        mock_ticket1.description = "Short desc"
        mock_ticket1.status = TicketStatus.OPEN

        mock_ticket2 = Mock()
        mock_ticket2.id = "2"
        mock_ticket2.title = "Ticket 2"
        mock_ticket2.description = "A" * 100  # Long description
        mock_ticket2.status = TicketStatus.CLOSED

        result = integration._format_search_results([mock_ticket1, mock_ticket2])

        assert "Found 2 ticket(s)" in result
        assert "Ticket 1" in result
        assert "Ticket 2" in result
        assert "Short desc" in result
        assert "..." in result  # Long description truncated
