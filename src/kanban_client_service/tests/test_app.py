"""Comprehensive tests for kanban_client_service main endpoints.

These tests verify that the FastAPI endpoints handle requests and responses correctly,
using a mocked Kanban client to isolate the tests from the actual Trello implementation.
"""

from collections.abc import Generator
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from kanban_client_api.models import KanbanBoard, KanbanCard, KanbanList, KanbanUser

from kanban_client_service.main import app

client = TestClient(app)

# Constants for test data
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_NOT_FOUND = 404


def create_mock_board(
    board_id: str,
    name: str = "Test Board",
    description: str | None = None,
) -> MagicMock:
    """Return a mock board object."""
    mock_board = MagicMock(spec=KanbanBoard)
    mock_board.id = board_id
    mock_board.name = name
    mock_board.description = description or "A test board"
    mock_board.closed = False
    mock_board.url = f"https://example.com/board/{board_id}"
    mock_board.created_at = None
    return mock_board


def create_mock_list(
    list_id: str,
    name: str = "Test List",
    board_id: str = "b1",
) -> MagicMock:
    """Return a mock list object."""
    mock_list = MagicMock(spec=KanbanList)
    mock_list.id = list_id
    mock_list.name = name
    mock_list.board_id = board_id
    mock_list.position = 0.0
    mock_list.closed = False
    return mock_list


def create_mock_card(
    card_id: str,
    name: str = "Test Card",
    list_id: str = "l1",
    board_id: str = "b1",
    description: str | None = None,
) -> MagicMock:
    """Return a mock card object."""
    mock_card = MagicMock(spec=KanbanCard)
    mock_card.id = card_id
    mock_card.name = name
    mock_card.list_id = list_id
    mock_card.board_id = board_id
    mock_card.description = description or "A test card"
    mock_card.position = 0.0
    mock_card.closed = False
    mock_card.due_date = None
    mock_card.url = f"https://example.com/card/{card_id}"
    mock_card.created_at = None
    return mock_card


def create_mock_user(
    user_id: str = "u1",
    username: str = "testuser",
    full_name: str | None = None,
    email: str | None = None,
) -> MagicMock:
    """Return a mock user object."""
    mock_user = MagicMock(spec=KanbanUser)
    mock_user.id = user_id
    mock_user.username = username
    mock_user.full_name = full_name or "Test User"
    mock_user.email = email or "test@example.com"
    return mock_user


@pytest.fixture
def mock_kanban_client() -> Generator[MagicMock, Any, None]:
    """Create a mock Kanban client for testing."""
    with patch("kanban_client_service.main.TrelloClientImpl") as mock:
        mock_instance = AsyncMock()
        mock.from_env.return_value = mock_instance
        yield mock_instance


# Board endpoint tests
def test_get_boards(mock_kanban_client: MagicMock) -> None:
    """Test listing boards returns correct format and status code."""
    mock_boards = [
        create_mock_board("b1", "Board 1"),
        create_mock_board("b2", "Board 2"),
    ]
    mock_kanban_client.get_boards.return_value = mock_boards

    response = client.get("/boards", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == len(mock_boards)
    assert data[0]["id"] == "b1"
    assert data[0]["name"] == "Board 1"


def test_get_boards_with_max_results(mock_kanban_client: MagicMock) -> None:
    """Test that boards listing works with pagination."""
    mock_boards = [
        create_mock_board("b1", "Board 1"),
        create_mock_board("b2", "Board 2"),
        create_mock_board("b3", "Board 3"),
    ]
    mock_kanban_client.get_boards.return_value = mock_boards

    response = client.get("/boards", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) == len(mock_boards)


def test_get_board_found(mock_kanban_client: MagicMock) -> None:
    """Test retrieving a specific board that exists."""
    mock_board = create_mock_board("b1", "Board 1")
    mock_kanban_client.get_board.return_value = mock_board

    response = client.get("/boards/b1", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == "b1"
    assert data["name"] == "Board 1"
    assert data["description"] == "A test board"


def test_get_board_not_found(mock_kanban_client: MagicMock) -> None:
    """Test retrieving a non-existent board."""
    from kanban_client_api.exceptions import KanbanNotFoundError

    mock_kanban_client.get_board.side_effect = KanbanNotFoundError("Board not found")
    response = client.get("/boards/nonexistent", headers={"Authorization": "Bearer TEST_TOKEN"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_board(mock_kanban_client: MagicMock) -> None:
    """Test creating a new board."""
    mock_board = create_mock_board("new_b", "New Board", "A new board")
    mock_kanban_client.create_board.return_value = mock_board

    response = client.post(
        "/boards?name=New+Board&description=A+new+board",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == "new_b"
    assert data["name"] == "New Board"


def test_update_board(mock_kanban_client: MagicMock) -> None:
    """Test updating a board."""
    mock_board = create_mock_board("b1", "Updated Board", "Updated description")
    mock_kanban_client.update_board.return_value = mock_board

    response = client.put(
        "/boards/b1?name=Updated+Board&description=Updated+description",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == "Updated Board"


def test_delete_board(mock_kanban_client: MagicMock) -> None:
    """Test deleting a board."""
    mock_kanban_client.delete_board.return_value = True

    response = client.delete("/boards/b1", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["success"] is True


# List endpoint tests
def test_get_lists(mock_kanban_client: MagicMock) -> None:
    """Test listing lists in a board."""
    mock_lists = [
        create_mock_list("l1", "To Do"),
        create_mock_list("l2", "In Progress"),
    ]
    mock_kanban_client.get_lists.return_value = mock_lists

    response = client.get("/boards/b1/lists", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == len(mock_lists)
    assert data[0]["name"] == "To Do"


def test_get_lists_not_found(mock_kanban_client: MagicMock) -> None:
    """Test getting lists when board doesn't exist."""
    from kanban_client_api.exceptions import KanbanNotFoundError

    mock_kanban_client.get_lists.side_effect = KanbanNotFoundError("Board not found")
    response = client.get("/boards/nonexistent/lists", headers={"Authorization": "Bearer TEST_TOKEN"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_list(mock_kanban_client: MagicMock) -> None:
    """Test creating a list in a board."""
    mock_list = create_mock_list("l3", "Done", "b1")
    mock_kanban_client.create_list.return_value = mock_list

    response = client.post(
        "/boards/b1/lists?name=Done",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == "Done"
    assert data["board_id"] == "b1"


def test_update_list(mock_kanban_client: MagicMock) -> None:
    """Test updating a list."""
    mock_list = create_mock_list("l1", "Updated List Name")
    mock_kanban_client.update_list.return_value = mock_list

    response = client.put(
        "/lists/l1?name=Updated+List+Name",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == "Updated List Name"


# Card endpoint tests
def test_get_cards(mock_kanban_client: MagicMock) -> None:
    """Test listing cards in a list."""
    mock_cards = [
        create_mock_card("c1", "Task 1"),
        create_mock_card("c2", "Task 2"),
    ]
    mock_kanban_client.get_cards.return_value = mock_cards

    response = client.get("/lists/l1/cards", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == len(mock_cards)
    assert data[0]["name"] == "Task 1"


def test_get_card_found(mock_kanban_client: MagicMock) -> None:
    """Test retrieving a specific card."""
    mock_card = create_mock_card("c1", "Task 1", description="Test task")
    mock_kanban_client.get_card.return_value = mock_card

    response = client.get("/cards/c1", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == "c1"
    assert data["name"] == "Task 1"
    assert data["description"] == "Test task"


def test_get_card_not_found(mock_kanban_client: MagicMock) -> None:
    """Test retrieving a non-existent card."""
    from kanban_client_api.exceptions import KanbanNotFoundError

    mock_kanban_client.get_card.side_effect = KanbanNotFoundError("Card not found")
    response = client.get("/cards/nonexistent", headers={"Authorization": "Bearer TEST_TOKEN"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_create_card(mock_kanban_client: MagicMock) -> None:
    """Test creating a card in a list."""
    mock_card = create_mock_card("c3", "New Task", description="A new task")
    mock_kanban_client.create_card.return_value = mock_card

    response = client.post(
        "/lists/l1/cards?name=New+Task&description=A+new+task",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == "New Task"
    assert data["description"] == "A new task"


def test_update_card(mock_kanban_client: MagicMock) -> None:
    """Test updating a card."""
    mock_card = create_mock_card("c1", "Updated Task", description="Updated description")
    mock_kanban_client.update_card.return_value = mock_card

    response = client.put(
        "/cards/c1?name=Updated+Task&description=Updated+description",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["name"] == "Updated Task"


def test_delete_card(mock_kanban_client: MagicMock) -> None:
    """Test deleting a card."""
    mock_kanban_client.delete_card.return_value = True

    response = client.delete("/cards/c1", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["success"] is True


# User endpoint tests
def test_get_current_user(mock_kanban_client: MagicMock) -> None:
    """Test retrieving current user."""
    mock_user = create_mock_user()
    mock_kanban_client.get_current_user.return_value = mock_user

    response = client.get("/users/me", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["id"] == "u1"
    assert data["username"] == "testuser"
    assert data["full_name"] == "Test User"
    assert data["email"] == "test@example.com"


def test_get_current_user_auth_error(mock_kanban_client: MagicMock) -> None:
    """Test authentication error when getting current user."""
    from kanban_client_api.exceptions import KanbanAuthenticationError

    mock_kanban_client.get_current_user.side_effect = KanbanAuthenticationError("Invalid token")
    response = client.get("/users/me", headers={"Authorization": "Bearer INVALID_TOKEN"})
    assert response.status_code == HTTPStatus.UNAUTHORIZED


# Error handling tests
def test_missing_token_returns_401() -> None:
    """Requests without token should be unauthorized by dependency."""
    response = client.get("/users/me")
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_api_error_handling(mock_kanban_client: MagicMock) -> None:
    """Test API error handling."""
    from kanban_client_api.exceptions import KanbanAPIError

    mock_kanban_client.get_boards.side_effect = KanbanAPIError("API Error", HTTP_BAD_REQUEST)
    response = client.get("/boards", headers={"Authorization": "Bearer TEST_TOKEN"})
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_create_board_api_error(mock_kanban_client: MagicMock) -> None:
    """Test creating board with API error."""
    from kanban_client_api.exceptions import KanbanAPIError

    mock_kanban_client.create_board.side_effect = KanbanAPIError("Bad request", HTTP_BAD_REQUEST)
    response = client.post(
        "/boards?name=Test",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_create_list_not_found(mock_kanban_client: MagicMock) -> None:
    """Test creating list when board doesn't exist."""
    from kanban_client_api.exceptions import KanbanNotFoundError

    mock_kanban_client.create_list.side_effect = KanbanNotFoundError("Board not found")
    response = client.post(
        "/boards/nonexistent/lists?name=Test",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_update_card_not_found(mock_kanban_client: MagicMock) -> None:
    """Test updating a card that doesn't exist."""
    from kanban_client_api.exceptions import KanbanNotFoundError

    mock_kanban_client.update_card.side_effect = KanbanNotFoundError("Card not found")
    response = client.put(
        "/cards/nonexistent?name=Updated",
        headers={"Authorization": "Bearer TEST_TOKEN"},
    )
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_card_not_found(mock_kanban_client: MagicMock) -> None:
    """Test deleting a card that doesn't exist."""
    from kanban_client_api.exceptions import KanbanNotFoundError

    mock_kanban_client.delete_card.side_effect = KanbanNotFoundError("Card not found")
    response = client.delete("/cards/nonexistent", headers={"Authorization": "Bearer TEST_TOKEN"})
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_delete_board_not_found(mock_kanban_client: MagicMock) -> None:
    """Test deleting a board that doesn't exist."""
    from kanban_client_api.exceptions import KanbanNotFoundError

    mock_kanban_client.delete_board.side_effect = KanbanNotFoundError("Board not found")
    response = client.delete("/boards/nonexistent", headers={"Authorization": "Bearer TEST_TOKEN"})
    assert response.status_code == HTTPStatus.NOT_FOUND


# Multiple items with pagination tests
def test_get_cards_pagination(mock_kanban_client: MagicMock) -> None:
    """Test card listing with multiple items."""
    mock_cards = [
        create_mock_card(f"c{i}", f"Task {i}") for i in range(1, 6)
    ]
    mock_kanban_client.get_cards.return_value = mock_cards

    response = client.get("/lists/l1/cards", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == len(mock_cards)


def test_get_lists_pagination(mock_kanban_client: MagicMock) -> None:
    """Test list listing with multiple items."""
    mock_lists = [
        create_mock_list(f"l{i}", f"List {i}") for i in range(1, 4)
    ]
    mock_kanban_client.get_lists.return_value = mock_lists

    response = client.get("/boards/b1/lists", headers={"Authorization": "Bearer TEST_TOKEN"})

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == len(mock_lists)
