"""Additional tests to increase coverage for kanban_client_service.main."""

from http import HTTPStatus

from fastapi.testclient import TestClient

from kanban_client_service.main import app


def test_auth_callback_page_served() -> None:
    """GET /auth/callback_page should return an HTML page."""
    client = TestClient(app)
    resp = client.get("/auth/callback_page")
    assert resp.status_code == HTTPStatus.OK
    assert "<html" in resp.text.lower()
    assert "trello oauth callback" in resp.text.lower()


def test_users_me_missing_token_returns_401() -> None:
    """Requests without token should be unauthorized by dependency."""
    client = TestClient(app)
    resp = client.get("/users/me")
    assert resp.status_code == HTTPStatus.UNAUTHORIZED
    assert resp.json()["detail"].lower().find("missing trello token") != -1
