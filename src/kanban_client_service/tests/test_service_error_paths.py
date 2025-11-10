"""Error-path and dependency-path coverage for ``kanban_client_service.main``."""

from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from kanban_client_api.exceptions import (
    KanbanAPIError,
    KanbanAuthenticationError,
    KanbanNotFoundError,
)

from kanban_client_service.main import app

client = TestClient(app)


def test_authorization_header_is_used() -> None:
    """Calling with Bearer token should succeed without cookie."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_board = MagicMock()
        mock_board.id = "b1"
        mock_board.name = "N"
        mock_client.get_boards.return_value = [mock_board]
        mock_get_client.return_value = mock_client
        resp = client.get("/boards", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.OK
        assert isinstance(resp.json(), list)


def test_no_boards_without_auth() -> None:
    """Calling without token or cookie should return 401."""
    resp = client.get("/boards")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_query_param_token_is_used() -> None:
    """Supplying token as query param should also work."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = AsyncMock()
        mock_board = MagicMock()
        mock_board.id = "b1"
        mock_board.name = "N"
        mock_client.get_boards.return_value = [mock_board]
        mock_get_client.return_value = mock_client
        resp = client.get("/boards?token=T")
        assert resp.status_code == HTTPStatus.OK


def test_users_me_auth_error_returns_401() -> None:
    """User endpoint surfaces authentication errors as 401."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_current_user.side_effect = KanbanAuthenticationError()
        mock_get_client.return_value = mock_client
        resp = client.get("/users/me", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_boards_api_error_returns_400() -> None:
    """Boards endpoint surfaces API errors as 400."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_boards.side_effect = KanbanAPIError("bad", 400)
        mock_get_client.return_value = mock_client
        resp = client.get("/boards", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_board_not_found_returns_404() -> None:
    """Board endpoint returns 404 when underlying call raises not-found."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_board.side_effect = KanbanNotFoundError("missing")
        mock_get_client.return_value = mock_client
        resp = client.get("/boards/bx", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.NOT_FOUND


def test_delete_board_api_error_returns_400() -> None:
    """Delete board surfaces API error as 400."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.delete_board.side_effect = KanbanAPIError("bad", 400)
        mock_get_client.return_value = mock_client
        resp = client.delete("/boards/bx", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_lists_not_found_returns_404() -> None:
    """Lists retrieval returns 404 when not found."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_lists.side_effect = KanbanNotFoundError("no lists")
        mock_get_client.return_value = mock_client
        resp = client.get("/boards/bx/lists", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.NOT_FOUND


def test_create_list_api_error_returns_400() -> None:
    """Create list surfaces API error as 400."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.create_list.side_effect = KanbanAPIError("bad", 400)
        mock_get_client.return_value = mock_client
        resp = client.post("/boards/bx/lists", params={"name": "L"}, headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_update_list_api_error_returns_400() -> None:
    """Update list surfaces API error as 400."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.update_list.side_effect = KanbanAPIError("bad", 400)
        mock_get_client.return_value = mock_client
        resp = client.put("/lists/ly", params={"name": "L"}, headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_get_cards_api_error_returns_400() -> None:
    """Get cards surfaces API error as 400."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_cards.side_effect = KanbanAPIError("bad", 400)
        mock_get_client.return_value = mock_client
        resp = client.get("/lists/ly/cards", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_get_card_not_found_returns_404() -> None:
    """Get card returns 404 when not found."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.get_card.side_effect = KanbanNotFoundError("missing")
        mock_get_client.return_value = mock_client
        resp = client.get("/cards/cx", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.NOT_FOUND


def test_create_card_api_error_returns_400() -> None:
    """Create card surfaces API error as 400."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.create_card.side_effect = KanbanAPIError("bad", 400)
        mock_get_client.return_value = mock_client
        resp = client.post(
            "/lists/ly/cards",
            params={"name": "C", "description": "d"},
            headers={"Authorization": "Bearer T"},
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_update_card_api_error_returns_400() -> None:
    """Update card surfaces API error as 400."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.update_card.side_effect = KanbanAPIError("bad", 400)
        mock_get_client.return_value = mock_client
        resp = client.put(
            "/cards/cx",
            params={"name": "C"},
            headers={"Authorization": "Bearer T"},
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_delete_card_api_error_returns_400() -> None:
    """Delete card surfaces API error as 400."""
    with patch("kanban_client_api.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.delete_card.side_effect = KanbanAPIError("bad", 400)
        mock_get_client.return_value = mock_client
        resp = client.delete("/cards/cx", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST
