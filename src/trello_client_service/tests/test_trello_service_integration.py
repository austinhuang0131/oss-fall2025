"""More detailed tests for Trello service integration."""

import os
from http import HTTPStatus
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient
from trello_client_api import TrelloBoard, TrelloCard, TrelloList, TrelloUser

from trello_client_service import app

os.environ["TRELLO_API_KEY"] = "dummy_key"
os.environ["TRELLO_API_SECRET"] = "dummy_secret"
os.environ["REDIRECT_URI"] = "http://localhost:8000/auth/callback"

client = TestClient(app)

MOCK_TOKEN = "mocked_token_123"
MOCK_AUTH_URL = "https://trello.com/authorize?token=mocked"

@pytest.fixture(autouse=True)
def patch_oauth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch TrelloOAuthHandler with a mock for testing."""
    class MockOAuthHandler:
        """Mock TrelloOAuthHandler for testing."""

        api_key: str = "dummy_key"
        api_secret: str = "dummy_secret"
        redirect_uri: str = "http://localhost:8000/auth/callback"

        @staticmethod
        def from_env() -> "MockOAuthHandler":
            """Return mock handler."""
            return MockOAuthHandler()

        def get_authorization_url(self) -> str:
            """Return mock authorization URL."""
            return MOCK_AUTH_URL

        async def exchange_token(self, token: str) -> str:
            """Return mock token if input matches."""
            assert token == "oauth_token"
            return MOCK_TOKEN

    monkeypatch.setattr("trello_client_service.main.TrelloOAuthHandler", MockOAuthHandler)

# Test /auth/login
def test_auth_login() -> None:
    """Test /auth/login endpoint returns authorization URL."""
    response = client.get("/auth/login")
    assert response.status_code == HTTPStatus.OK
    assert "authorization_url" in response.json()

# Test /auth/callback
def test_auth_callback_sets_cookie() -> None:
    """Test /auth/callback sets token cookie and returns token."""
    response = client.post("/auth/callback", json={"token": "oauth_token"})
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["token"] == MOCK_TOKEN
    # Cookie should be set
    assert "trello_token" in response.cookies
    assert response.cookies["trello_token"] == MOCK_TOKEN

# Helper to set token cookie for authenticated requests
def auth_client() -> TestClient:
    """Return test client with token cookie set."""
    client.cookies.set("trello_token", MOCK_TOKEN)
    return client

# Test /users/me
@patch("trello_client_service.main.TrelloClientImpl.get_current_user", autospec=True)
def test_get_current_user(mock_get_user: Mock) -> None:
    """Test /users/me returns user info."""
    mock_get_user.return_value = TrelloUser(
        id="u1", username="test", full_name="Test User", email="test@example.com",
    )
    response = auth_client().get("/users/me")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["username"] == "test"

# Test /boards endpoints
@patch("trello_client_service.main.TrelloClientImpl.get_boards", autospec=True)
def test_get_boards(mock_get_boards: Mock) -> None:
    """Test /boards returns list of boards."""
    mock_get_boards.return_value = [
        TrelloBoard(id="b1", name="Board1", description=None, closed=False, url="url1"),
    ]
    response = auth_client().get("/boards")
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json(), list)

@patch("trello_client_service.main.TrelloClientImpl.get_board", autospec=True)
def test_get_board(mock_get_board: Mock) -> None:
    """Test /boards/{board_id} returns board info."""
    mock_get_board.return_value = TrelloBoard(id="b1", name="Board1", description=None, closed=False, url="url1")
    response = auth_client().get("/boards/b1")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["id"] == "b1"

@patch("trello_client_service.main.TrelloClientImpl.create_board", autospec=True)
def test_create_board(mock_create_board: Mock) -> None:
    """Test /boards POST creates a board."""
    mock_create_board.return_value = TrelloBoard(id="b2", name="Board2", description="desc", closed=False, url="url2")
    response = auth_client().post("/boards", params={"name": "Board2", "description": "desc"})
    assert response.status_code == HTTPStatus.OK
    assert response.json()["name"] == "Board2"

@patch("trello_client_service.main.TrelloClientImpl.update_board", autospec=True)
def test_update_board(mock_update_board: Mock) -> None:
    """Test /boards/{board_id} PUT updates a board."""
    mock_update_board.return_value = TrelloBoard(id="b2", name="Board2-updated", description=None, closed=False, url="url2")
    response = auth_client().put("/boards/b2", params={"name": "Board2-updated"})
    assert response.status_code == HTTPStatus.OK
    assert response.json()["name"] == "Board2-updated"

@patch("trello_client_service.main.TrelloClientImpl.delete_board", autospec=True)
def test_delete_board(mock_delete_board: Mock) -> None:
    """Test /boards/{board_id} DELETE deletes a board."""
    mock_delete_board.return_value = True
    response = auth_client().delete("/boards/b2")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["success"] is True

# Test /lists endpoints
@patch("trello_client_service.main.TrelloClientImpl.get_lists", autospec=True)
def test_get_lists(mock_get_lists: Mock) -> None:
    """Test /boards/{board_id}/lists returns lists."""
    mock_get_lists.return_value = [
        TrelloList(id="l1", name="List1", board_id="b1", position=0.0, closed=False),
    ]
    response = auth_client().get("/boards/b1/lists")
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json(), list)

@patch("trello_client_service.main.TrelloClientImpl.create_list", autospec=True)
def test_create_list(mock_create_list: Mock) -> None:
    """Test /boards/{board_id}/lists POST creates a list."""
    mock_create_list.return_value = TrelloList(id="l2", name="List2", board_id="b1", position=0.0, closed=False)
    response = auth_client().post("/boards/b1/lists", params={"name": "List2"})
    assert response.status_code == HTTPStatus.OK
    assert response.json()["name"] == "List2"

@patch("trello_client_service.main.TrelloClientImpl.update_list", autospec=True)
def test_update_list(mock_update_list: Mock) -> None:
    """Test /lists/{list_id} PUT updates a list."""
    mock_update_list.return_value = TrelloList(id="l2", name="List2-updated", board_id="b1", position=0.0, closed=False)
    response = auth_client().put("/lists/l2", params={"name": "List2-updated"})
    assert response.status_code == HTTPStatus.OK
    assert response.json()["name"] == "List2-updated"

# Test /cards endpoints
@patch("trello_client_service.main.TrelloClientImpl.get_cards", autospec=True)
def test_get_cards(mock_get_cards: Mock) -> None:
    """Test /lists/{list_id}/cards returns cards."""
    mock_get_cards.return_value = [
        TrelloCard(id="c1", name="Card1", list_id="l1", board_id="b1", description=None, position=0.0, closed=False, url=None),
    ]
    response = auth_client().get("/lists/l1/cards")
    assert response.status_code == HTTPStatus.OK
    assert isinstance(response.json(), list)

@patch("trello_client_service.main.TrelloClientImpl.get_card", autospec=True)
def test_get_card(mock_get_card: Mock) -> None:
    """Test /cards/{card_id} returns card info."""
    mock_get_card.return_value = TrelloCard(id="c1", name="Card1", list_id="l1", board_id="b1", description=None, position=0.0, closed=False, url=None)
    response = auth_client().get("/cards/c1")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["id"] == "c1"

@patch("trello_client_service.main.TrelloClientImpl.create_card", autospec=True)
def test_create_card(mock_create_card: Mock) -> None:
    """Test /lists/{list_id}/cards POST creates a card."""
    mock_create_card.return_value = TrelloCard(id="c2", name="Card2", list_id="l1", board_id="b1", description="desc", position=0.0, closed=False, url=None)
    response = auth_client().post("/lists/l1/cards", params={"name": "Card2", "description": "desc"})
    assert response.status_code == HTTPStatus.OK
    assert response.json()["name"] == "Card2"

@patch("trello_client_service.main.TrelloClientImpl.update_card", autospec=True)
def test_update_card(mock_update_card: Mock) -> None:
    """Test /cards/{card_id} PUT updates a card."""
    mock_update_card.return_value = TrelloCard(id="c2", name="Card2-updated", list_id="l1", board_id="b1", description=None, position=0.0, closed=False, url=None)
    response = auth_client().put("/cards/c2", params={"name": "Card2-updated"})
    assert response.status_code == HTTPStatus.OK
    assert response.json()["name"] == "Card2-updated"

@patch("trello_client_service.main.TrelloClientImpl.delete_card", autospec=True)
def test_delete_card(mock_delete_card: Mock) -> None:
    """Test /cards/{card_id} DELETE deletes a card."""
    mock_delete_card.return_value = True
    response = auth_client().delete("/cards/c2")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["success"] is True

# Test /health endpoint
def test_health() -> None:
    """Test /health endpoint returns healthy status."""
    response = client.get("/health")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["status"] == "healthy"
