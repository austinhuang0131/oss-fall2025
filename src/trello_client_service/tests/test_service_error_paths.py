"""Error-path and dependency-path coverage for ``trello_client_service.main``."""

from http import HTTPStatus
from unittest.mock import patch

from fastapi.testclient import TestClient
from trello_client_api import (
    TrelloAPIError,
    TrelloAuthenticationError,
    TrelloBoard,
    TrelloNotFoundError,
)

from trello_client_service.main import app


client = TestClient(app)


def test_authorization_header_is_used() -> None:
    """Calling with Bearer token should succeed without cookie."""
    with patch("trello_client_service.main.TrelloClientImpl.get_boards", autospec=True) as mock_get:
        mock_get.return_value = [TrelloBoard(id="b1", name="N", description=None, closed=False, url=None)]
        resp = client.get("/boards", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.OK
        assert isinstance(resp.json(), list)


def test_query_param_token_is_used() -> None:
    """Supplying token as query param should also work."""
    with patch("trello_client_service.main.TrelloClientImpl.get_boards", autospec=True) as mock_get:
        mock_get.return_value = [TrelloBoard(id="b1", name="N", description=None, closed=False, url=None)]
        resp = client.get("/boards?token=T")
        assert resp.status_code == HTTPStatus.OK


def test_users_me_auth_error_returns_401() -> None:
    """User endpoint surfaces authentication errors as 401."""
    with patch("trello_client_service.main.TrelloClientImpl.get_current_user", autospec=True) as mock_get:
        mock_get.side_effect = TrelloAuthenticationError()
        resp = client.get("/users/me", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.UNAUTHORIZED


def test_boards_api_error_returns_400() -> None:
    """Boards endpoint surfaces API errors as 400."""
    with patch("trello_client_service.main.TrelloClientImpl.get_boards", autospec=True) as mock_get:
        mock_get.side_effect = TrelloAPIError("bad", 400)
        resp = client.get("/boards", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_board_not_found_returns_404() -> None:
    """Board endpoint returns 404 when underlying call raises not-found."""
    with patch("trello_client_service.main.TrelloClientImpl.get_board", autospec=True) as mock_get:
        mock_get.side_effect = TrelloNotFoundError("missing")
        resp = client.get("/boards/bx", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.NOT_FOUND


def test_delete_board_api_error_returns_400() -> None:
    """Delete board surfaces API error as 400."""
    with patch("trello_client_service.main.TrelloClientImpl.delete_board", autospec=True) as mock_del:
        mock_del.side_effect = TrelloAPIError("bad", 400)
        resp = client.delete("/boards/bx", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_lists_not_found_returns_404() -> None:
    """Lists retrieval returns 404 when not found."""
    with patch("trello_client_service.main.TrelloClientImpl.get_lists", autospec=True) as mock_get:
        mock_get.side_effect = TrelloNotFoundError("no lists")
        resp = client.get("/boards/bx/lists", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.NOT_FOUND


def test_create_list_api_error_returns_400() -> None:
    """Create list surfaces API error as 400."""
    with patch("trello_client_service.main.TrelloClientImpl.create_list", autospec=True) as mock_create:
        mock_create.side_effect = TrelloAPIError("bad", 400)
        resp = client.post("/boards/bx/lists", params={"name": "L"}, headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_update_list_api_error_returns_400() -> None:
    """Update list surfaces API error as 400."""
    with patch("trello_client_service.main.TrelloClientImpl.update_list", autospec=True) as mock_upd:
        mock_upd.side_effect = TrelloAPIError("bad", 400)
        resp = client.put("/lists/ly", params={"name": "L"}, headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_get_cards_api_error_returns_400() -> None:
    """Get cards surfaces API error as 400."""
    with patch("trello_client_service.main.TrelloClientImpl.get_cards", autospec=True) as mock_get:
        mock_get.side_effect = TrelloAPIError("bad", 400)
        resp = client.get("/lists/ly/cards", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_get_card_not_found_returns_404() -> None:
    """Get card returns 404 when not found."""
    with patch("trello_client_service.main.TrelloClientImpl.get_card", autospec=True) as mock_get:
        mock_get.side_effect = TrelloNotFoundError("missing")
        resp = client.get("/cards/cx", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.NOT_FOUND


def test_create_card_api_error_returns_400() -> None:
    """Create card surfaces API error as 400."""
    with patch("trello_client_service.main.TrelloClientImpl.create_card", autospec=True) as mock_create:
        mock_create.side_effect = TrelloAPIError("bad", 400)
        resp = client.post(
            "/lists/ly/cards",
            params={"name": "C", "description": "d"},
            headers={"Authorization": "Bearer T"},
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_update_card_api_error_returns_400() -> None:
    """Update card surfaces API error as 400."""
    with patch("trello_client_service.main.TrelloClientImpl.update_card", autospec=True) as mock_update:
        mock_update.side_effect = TrelloAPIError("bad", 400)
        resp = client.put(
            "/cards/cx",
            params={"name": "C"},
            headers={"Authorization": "Bearer T"},
        )
        assert resp.status_code == HTTPStatus.BAD_REQUEST


def test_delete_card_api_error_returns_400() -> None:
    """Delete card surfaces API error as 400."""
    with patch("trello_client_service.main.TrelloClientImpl.delete_card", autospec=True) as mock_del:
        mock_del.side_effect = TrelloAPIError("bad", 400)
        resp = client.delete("/cards/cx", headers={"Authorization": "Bearer T"})
        assert resp.status_code == HTTPStatus.BAD_REQUEST
