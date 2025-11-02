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
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict[str, Any] | None=None) -> Any: #SJ
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
        async def mock_make_request(method: str, endpoint: str, params: dict[str, str] | None=None, json_data: dict[str, Any] | None=None) -> Any: #SJ
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
