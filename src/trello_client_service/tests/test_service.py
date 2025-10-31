"""Tests for Trello client service."""

from http import HTTPStatus

import pytest
from fastapi.testclient import TestClient

from trello_client_service.main import app


@pytest.fixture
def client() -> TestClient:
    """Create test client."""
    return TestClient(app)


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "healthy"}


def test_auth_login_endpoint(client: TestClient) -> None:
    """Test auth login endpoint structure."""
    # This will fail without proper env vars, but we can test the endpoint exists
    response = client.get("/auth/login")
    # Should return 500 due to missing env vars, not 404
    assert response.status_code in [HTTPStatus.OK, HTTPStatus.INTERNAL_SERVER_ERROR]


def test_docs_endpoint(client: TestClient) -> None:
    """Test that documentation is accessible."""
    response = client.get("/docs")
    assert response.status_code == HTTPStatus.OK
