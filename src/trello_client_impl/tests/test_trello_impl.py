"""Tests for Trello client implementation."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from trello_client_api import TrelloBoard, TrelloUser

from trello_client_impl import TrelloClientImpl, TrelloOAuthHandler


class TestTrelloClientImpl:
    """Test cases for TrelloClientImpl."""

    @pytest.fixture
    def mock_oauth_handler(self) -> MagicMock:
        """Create mock OAuth handler."""
        handler = MagicMock(spec=TrelloOAuthHandler)
        handler.api_key = "test_key"
        return handler

    @pytest.fixture
    def client(self, mock_oauth_handler: TrelloOAuthHandler) -> TrelloClientImpl:
        """Create test client."""
        return TrelloClientImpl(
            db_url="postgresql://test:test@localhost/test",
            oauth_handler=mock_oauth_handler,
            user_id="test_user_id",
        )

    async def test_client_initialization(self, client: TrelloClientImpl) -> None:
        """Test client initializes correctly."""
        assert client.db_url == "postgresql://test:test@localhost/test"
        assert client.user_id == "test_user_id"
        assert client.base_url == "https://api.trello.com/1"

    async def test_get_current_user_success(self, client: TrelloClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful user retrieval."""
        # Mock the _make_request method
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return {
                "id": "user123",
                "username": "testuser",
                "fullName": "Test User",
                "email": "test@example.com",
            }

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        user = await client.get_current_user()

        assert isinstance(user, TrelloUser)
        assert user.id == "user123"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.email == "test@example.com"

    async def test_get_boards_success(self, client: TrelloClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful board retrieval."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return [
                {
                    "id": "board123",
                    "name": "Test Board",
                    "desc": "Test Description",
                    "closed": False,
                    "url": "https://trello.com/b/board123",
                },
            ]

        monkeypatch.setattr(client, "_make_request", mock_make_request)

        boards = await client.get_boards()

        assert len(boards) == 1
        board = boards[0]
        assert isinstance(board, TrelloBoard)
        assert board.id == "board123"
        assert board.name == "Test Board"
        assert board.description == "Test Description"
        assert not board.closed
        assert board.url == "https://trello.com/b/board123"

    async def test_get_board_success(self, client: TrelloClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test fetching a single board."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return {
                "id": "b1",
                "name": "Board 1",
                "desc": "Desc",
                "closed": False,
                "url": "https://trello.com/b/b1",
            }
        monkeypatch.setattr(client, "_make_request", mock_make_request)
        board = await client.get_board("b1")
        assert board.id == "b1"
        assert board.name == "Board 1"

    async def test_create_board_success(self, client: TrelloClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test creating a board."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            assert method == "POST"
            return {
                "id": "b2",
                "name": params["name"],
                "desc": params.get("desc"),
                "closed": False,
                "url": "url",
            }
        monkeypatch.setattr(client, "_make_request", mock_make_request)
        board = await client.create_board("New", description="D")
        assert board.name == "New"
        assert board.description == "D"

    async def test_update_board_success(self, client: TrelloClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test updating a board."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            assert method == "PUT"
            return {
                "id": "b2",
                "name": params.get("name", "Board 2"),
                "desc": params.get("desc"),
                "closed": False,
                "url": "url",
            }
        monkeypatch.setattr(client, "_make_request", mock_make_request)
        board = await client.update_board("b2", name="Renamed")
        assert board.name == "Renamed"

    async def test_delete_board_success(self, client: TrelloClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test deleting a board."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            assert method == "DELETE"
            return {}
        monkeypatch.setattr(client, "_make_request", mock_make_request)
        assert await client.delete_board("b2") is True

    async def test_lists_and_cards_crud(self, client: TrelloClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Cover list and card CRUD paths with mocked requests."""
        # get_lists
        async def mock_get_lists(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return [
                {"id": "l1", "name": "List1", "pos": 1.0, "closed": False},
            ]
        monkeypatch.setattr(client, "_make_request", mock_get_lists)
        lists = await client.get_lists("b1")
        assert lists[0].id == "l1"

        # create_list
        async def mock_create_list(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return {"id": "l2", "name": params["name"], "pos": 1.0, "closed": False}
        monkeypatch.setattr(client, "_make_request", mock_create_list)
        new_list = await client.create_list("b1", "NewList")
        assert new_list.name == "NewList"

        # update_list
        async def mock_update_list(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return {"id": "l2", "name": params.get("name", "List2"), "idBoard": "b1", "pos": 1.0, "closed": False}
        monkeypatch.setattr(client, "_make_request", mock_update_list)
        updated_list = await client.update_list("l2", name="RenamedList")
        assert updated_list.name == "RenamedList"

        # get_cards
        async def mock_get_cards(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return [
                {"id": "c1", "name": "Card1", "idBoard": "b1", "pos": 0.0, "closed": False, "url": None},
            ]
        monkeypatch.setattr(client, "_make_request", mock_get_cards)
        cards = await client.get_cards("l1")
        assert cards[0].id == "c1"

        # get_card
        async def mock_get_card(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return {"id": "c1", "name": "Card1", "idList": "l1", "idBoard": "b1", "pos": 0.0, "closed": False, "url": None, "desc": None}
        monkeypatch.setattr(client, "_make_request", mock_get_card)
        card = await client.get_card("c1")
        assert card.id == "c1"

        # create_card
        async def mock_create_card(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return {"id": "c2", "name": params["name"], "idBoard": "b1", "pos": 0.0, "closed": False, "url": None, "desc": params.get("desc")}
        monkeypatch.setattr(client, "_make_request", mock_create_card)
        new_card = await client.create_card("l1", "Card2", description="D")
        assert new_card.name == "Card2"
        assert new_card.description == "D"

        # update_card
        async def mock_update_card(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return {"id": "c2", "name": params.get("name", "Card2"), "idList": params.get("idList", "l1"), "idBoard": "b1", "pos": 0.0, "closed": False, "url": None, "desc": params.get("desc")}
        monkeypatch.setattr(client, "_make_request", mock_update_card)
        updated_card = await client.update_card("c2", name="Renamed", description=None)
        assert updated_card.name == "Renamed"

        # delete_card
        async def mock_delete_card(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            return {}
        monkeypatch.setattr(client, "_make_request", mock_delete_card)
        assert await client.delete_card("c2") is True

    async def test_update_board_with_description(self, client: TrelloClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ensure description parameter is forwarded when provided."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            assert params is not None
            assert params.get("desc") == "D2"
            return {"id": "b2", "name": params.get("name", "B"), "desc": params.get("desc"), "closed": False, "url": "u"}
        monkeypatch.setattr(client, "_make_request", mock_make_request)
        out = await client.update_board("b2", name="B", description="D2")
        assert out.description == "D2"

    async def test_update_card_with_description_and_list(self, client: TrelloClientImpl, monkeypatch: pytest.MonkeyPatch) -> None:
        """Ensure update_card forwards description and list_id when provided."""
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict | None=None) -> Any:
            assert params is not None
            assert params.get("desc") == "dd"
            assert params.get("idList") == "l9"
            return {"id": "c9", "name": params.get("name", "C"), "idList": "l9", "idBoard": "b1", "desc": params.get("desc"), "pos": 0.0, "closed": False, "url": None}
        monkeypatch.setattr(client, "_make_request", mock_make_request)
        card = await client.update_card("c9", name="C", description="dd", list_id="l9")
        assert card.description == "dd"
        assert card.list_id == "l9"