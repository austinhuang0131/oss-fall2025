"""Tests for Trello ticket implementation."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from tickets_api.src.tickets_api import Ticket, TicketStatus
from trello_client_impl.oauth import TrelloOAuthHandler

from trello_ticket_impl.exceptions import (
    TrelloAPIError,
    TrelloAuthenticationError,
)
from trello_ticket_impl.trello_ticket_impl import TrelloTicketClientImpl


class TestTrelloTicketClientImpl:
    """Test cases for TrelloTicketClientImpl."""

    @pytest.fixture
    def mock_oauth_handler(self) -> MagicMock:
        """Create mock OAuth handler."""
        handler = MagicMock(spec=TrelloOAuthHandler)
        handler.api_key = "test_key"
        return handler

    @pytest.fixture
    def client(self, mock_oauth_handler: TrelloOAuthHandler) -> TrelloTicketClientImpl:
        """Create test client."""
        return TrelloTicketClientImpl(
            token="test_token",
            oauth_handler=mock_oauth_handler,
            board_id="test_board_123",
        )

    def test_client_initialization(self, client: TrelloTicketClientImpl) -> None:
        """Test client initializes correctly."""
        assert client.base_url == "https://api.trello.com/1"
        assert client.token == "test_token"
        assert client._board_id == "test_board_123"

    def test_create_ticket_success(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful ticket creation."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/lists":
                return [
                    {"id": "list_todo", "name": "To Do"},
                    {"id": "list_done", "name": "Done"},
                    {"id": "list_in_progress", "name": "In Progress"},
                ]
            if endpoint == "/cards" and params:
                return {
                    "id": "card123",
                    "name": params["name"],
                    "desc": params["desc"],
                    "idMembers": [params["idMembers"]] if params.get("idMembers") else [],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.create_ticket("Test Ticket", "This is a test ticket", assignee="user123")

        assert isinstance(ticket, Ticket)
        assert ticket.title == "Test Ticket"
        assert ticket.description == "This is a test ticket"
        assert ticket.status == TicketStatus.OPEN
        assert ticket.assignee == "user123"

    def test_create_ticket_without_assignee(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test ticket creation without assignee."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/lists":
                return [
                    {"id": "list_todo", "name": "To Do"},
                    {"id": "list_done", "name": "Done"},
                    {"id": "list_in_progress", "name": "In Progress"},
                ]
            if endpoint == "/cards" and params:
                return {
                    "id": "card123",
                    "name": params["name"],
                    "desc": params["desc"],
                    "idMembers": [],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.create_ticket("Test Ticket", "No assignee")

        assert ticket.assignee is None
        assert ticket.status == TicketStatus.OPEN

    def test_get_ticket_open_status(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fetching a ticket with OPEN status."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/lists":
                return [
                    {"id": "list_todo", "name": "To Do"},
                    {"id": "list_done", "name": "Done"},
                    {"id": "list_in_progress", "name": "In Progress"},
                ]
            if endpoint == "/cards/card123":
                return {
                    "id": "card123",
                    "name": "Test Ticket",
                    "desc": "Test Description",
                    "idList": "list_todo",
                    "idMembers": ["user123"],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.get_ticket("card123")

        assert ticket.id == "card123"
        assert ticket.title == "Test Ticket"
        assert ticket.description == "Test Description"
        assert ticket.status == TicketStatus.OPEN
        assert ticket.assignee == "user123"

    def test_get_ticket_closed_status(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fetching a ticket with CLOSED status."""
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == "/cards/card456":
                return {
                    "id": "card456",
                    "name": "Completed Ticket",
                    "desc": "All done",
                    "idList": "list_done",
                    "idMembers": [],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.get_ticket("card456")

        assert ticket.status == TicketStatus.CLOSED
        assert ticket.assignee is None

    def test_get_ticket_in_progress_status(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fetching a ticket with IN_PROGRESS status."""
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == "/cards/card789":
                return {
                    "id": "card789",
                    "name": "In Progress Ticket",
                    "desc": "Currently working on this",
                    "idList": "list_in_progress",
                    "idMembers": ["user456"],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.get_ticket("card789")

        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.assignee == "user456"

    def test_update_ticket_title(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test updating only the ticket title."""
        # Pre-initialize list IDs to avoid lazy initialization
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == "/cards/card123" and method == "PUT":
                assert params is not None
                assert params.get("name") == "Updated Title"
                return {
                    "id": "card123",
                    "name": params.get("name"),
                    "desc": "Original Description",
                    "idList": "list_todo",
                    "idMembers": [],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.update_ticket("card123", title="Updated Title")

        assert ticket.title == "Updated Title"
        assert ticket.description == "Original Description"
        assert ticket.status == TicketStatus.OPEN

    def test_update_ticket_status(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test updating ticket status (moving between lists)."""
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == "/cards/card123" and method == "PUT":
                assert params is not None
                assert params.get("idList") == "list_done"
                return {
                    "id": "card123",
                    "name": "Test Ticket",
                    "desc": "Test Description",
                    "idList": "list_done",
                    "idMembers": [],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.update_ticket("card123", status=TicketStatus.CLOSED)

        assert ticket.status == TicketStatus.CLOSED

    def test_update_ticket_assignee(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test updating ticket assignee."""
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == "/cards/card123" and method == "PUT":
                assert params is not None
                assert params.get("idMembers") == "new_user_456"
                return {
                    "id": "card123",
                    "name": "Test Ticket",
                    "desc": "Test Description",
                    "idList": "list_todo",
                    "idMembers": ["new_user_456"],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.update_ticket("card123", assignee="new_user_456")

        assert ticket.assignee == "new_user_456"

    def test_update_ticket_multiple_fields(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test updating multiple ticket fields at once."""
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == "/cards/card123" and method == "PUT":
                assert params is not None
                assert params.get("name") == "New Title"
                assert params.get("desc") == "New Description"
                assert params.get("idList") == "list_in_progress"
                assert params.get("idMembers") == "user999"
                return {
                    "id": "card123",
                    "name": "New Title",
                    "desc": "New Description",
                    "idList": "list_in_progress",
                    "idMembers": ["user999"],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.update_ticket(
            "card123",
            title="New Title",
            description="New Description",
            status=TicketStatus.IN_PROGRESS,
            assignee="user999",
        )

        assert ticket.title == "New Title"
        assert ticket.description == "New Description"
        assert ticket.status == TicketStatus.IN_PROGRESS
        assert ticket.assignee == "user999"

    def test_update_ticket_no_fields_raises_error(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that update with no fields raises TrelloAPIError."""
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        with pytest.raises(TrelloAPIError):
            client.update_ticket("card123")

    def test_delete_ticket_success(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful ticket deletion."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/lists":
                return [
                    {"id": "list_todo", "name": "To Do"},
                    {"id": "list_done", "name": "Done"},
                    {"id": "list_in_progress", "name": "In Progress"},
                ]
            if method == "DELETE":
                return {}
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        result = client.delete_ticket("card123")

        assert result is True

    def test_search_tickets_by_query(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test searching tickets by query string."""
        card_list = [
            {
                "id": "card1",
                "name": "Login bug",
                "desc": "Bug in login form",
                "idList": "list_todo",
                "idMembers": [],
            },
            {
                "id": "card2",
                "name": "Database bug",
                "desc": "Slow query bug",
                "idList": "list_in_progress",
                "idMembers": ["user123"],
            },
        ]
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == "/search":
                assert params is not None
                assert params.get("query") == "bug"
                return {"cards": card_list}
            return []

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        tickets = client.search_tickets(query="bug")

        assert len(tickets) == len(card_list)
        assert tickets[0].title == card_list[0]["name"]
        assert tickets[0].status == TicketStatus.OPEN
        assert tickets[1].title == card_list[1]["name"]
        assert tickets[1].status == TicketStatus.IN_PROGRESS

    def test_search_tickets_by_status(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test searching tickets by status only."""
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == "/lists/list_done/cards":
                return [
                    {
                        "id": "card1",
                        "name": "Completed Task",
                        "desc": "Done",
                        "idList": "list_done",
                        "idMembers": [],
                    },
                ]
            return []

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        tickets = client.search_tickets(status=TicketStatus.CLOSED)

        assert len(tickets) == 1
        assert tickets[0].status == TicketStatus.CLOSED

    def test_search_tickets_all_on_board(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test retrieving all tickets on the board."""
        card_list = [
            {
                "id": "card1",
                "name": "Task 1",
                "desc": "Description 1",
                "idList": "list_todo",
                "idMembers": [],
            },
            {
                "id": "card2",
                "name": "Task 2",
                "desc": "Description 2",
                "idList": "list_done",
                "idMembers": ["user1"],
            },
        ]
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/cards":
                return card_list
            return []

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        tickets = client.search_tickets()

        assert len(tickets) == len(card_list)
        assert tickets[0].title == card_list[0]["name"]
        assert tickets[1].title == card_list[1]["name"]

    def test_no_token_raises_authentication_error(self, mock_oauth_handler: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that missing token raises TrelloAuthenticationError."""
        monkeypatch.setenv("TRELLO_BOARD_ID", "test_board")
        client = TrelloTicketClientImpl(token="", oauth_handler=mock_oauth_handler)

        with pytest.raises(TrelloAuthenticationError):
            client.create_ticket("Test", "Test")

    def test_api_error_response(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling of API error responses."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/lists":
                return [
                    {"id": "list_todo", "name": "To Do"},
                    {"id": "list_done", "name": "Done"},
                    {"id": "list_in_progress", "name": "In Progress"},
                ]
            if endpoint == "/cards":
                msg = "Card creation failed"
                raise TrelloAPIError(msg)
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        with pytest.raises(TrelloAPIError):
            client.create_ticket("Test", "Test")

    def test_malformed_api_response_create_card(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling when API returns non-dict for create_ticket."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/lists":
                return [
                    {"id": "list_todo", "name": "To Do"},
                    {"id": "list_done", "name": "Done"},
                    {"id": "list_in_progress", "name": "In Progress"},
                ]
            if endpoint == "/cards":
                return []  # Should be dict, not list
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        with pytest.raises(TrelloAPIError):
            client.create_ticket("Test", "Test")

    def test_malformed_api_response_get_card(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling when API returns non-dict for get_ticket."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/lists":
                return [
                    {"id": "list_todo", "name": "To Do"},
                    {"id": "list_done", "name": "Done"},
                    {"id": "list_in_progress", "name": "In Progress"},
                ]
            if endpoint == "/cards/card123":
                return []  # Should be dict, not list
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        with pytest.raises(TrelloAPIError):
            client.get_ticket("card123")

    def test_status_mapping_consistency(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that status mapping is consistent across operations."""
        # Pre-initialize list IDs
        client._todo_list_id = "list_todo"
        client._done_list_id = "list_done"
        client._in_progress_list_id = "list_in_progress"

        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == "/cards":
                return {
                    "id": "card123",
                    "name": "Test",
                    "desc": "Test",
                    "idList": "list_todo",
                    "idMembers": [],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.create_ticket("Test", "Test")
        # New tickets should be OPEN (in To Do list)
        assert ticket.status == TicketStatus.OPEN

    def test_multiple_assignees_only_first_returned(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that only the first assignee is returned when API returns multiple."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/lists":
                return [
                    {"id": "list_todo", "name": "To Do"},
                    {"id": "list_done", "name": "Done"},
                    {"id": "list_in_progress", "name": "In Progress"},
                ]
            if endpoint == "/cards/card123":
                return {
                    "id": "card123",
                    "name": "Test Ticket",
                    "desc": "Test Description",
                    "idList": "list_todo",
                    "idMembers": ["user1", "user2", "user3"],
                }
            return {}

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        ticket = client.get_ticket("card123")

        assert ticket.assignee == "user1"

    def test_search_with_query_and_status_filter(self, client: TrelloTicketClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test searching with both query and status filter."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None = None) -> Any:
            if endpoint == f"/boards/{client._board_id}/lists":
                return [
                    {"id": "list_todo", "name": "To Do"},
                    {"id": "list_done", "name": "Done"},
                    {"id": "list_in_progress", "name": "In Progress"},
                ]
            if endpoint == "/search":
                return {
                    "cards": [
                        {
                            "id": "card1",
                            "name": "Open bug",
                            "desc": "Not fixed",
                            "idList": "list_todo",
                            "idMembers": [],
                        },
                        {
                            "id": "card2",
                            "name": "Fixed bug",
                            "desc": "Now done",
                            "idList": "list_done",
                            "idMembers": [],
                        },
                    ],
                }
            return []

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        tickets = client.search_tickets(query="bug", status=TicketStatus.OPEN)

        assert len(tickets) == 1
        assert tickets[0].status == TicketStatus.OPEN
