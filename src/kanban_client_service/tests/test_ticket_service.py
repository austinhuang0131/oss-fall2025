"""Tests for Ticket API endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from ticket_api.client import TicketClient
from ticket_api.exceptions import (
    TicketAPIError,
    TicketAuthenticationError,
    TicketNotFoundError,
)
from ticket_api.models import Ticket

from kanban_client_service.main import app, get_ticket_client


class MockTicket(Ticket):
    """Mock Ticket implementation for testing."""

    def __init__(
        self,
        ticket_id: str,
        title: str,
        description: str,
        status: bool,
    ) -> None:
        """Initialize mock ticket."""
        self._id = ticket_id
        self._title = title
        self._description = description
        self._status = status

    @property
    def id(self) -> str:
        """Get ticket ID."""
        return self._id

    @property
    def title(self) -> str:
        """Get ticket title."""
        return self._title

    @property
    def description(self) -> str:
        """Get ticket description."""
        return self._description

    @property
    def status(self) -> bool:
        """Get ticket status."""
        return self._status


@pytest.fixture
def mock_ticket_client() -> AsyncMock:
    """Create a mock Ticket client."""
    return AsyncMock(spec=TicketClient)


@pytest.fixture
def test_client(mock_ticket_client: AsyncMock) -> TestClient:
    """Create a test client with mocked dependencies."""

    def override_get_ticket_client() -> TicketClient:
        return mock_ticket_client  # type: ignore[return-value]

    app.dependency_overrides[get_ticket_client] = override_get_ticket_client
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_create_ticket(test_client: TestClient, mock_ticket_client: AsyncMock) -> None:
    """Test creating a new ticket."""
    mock_ticket = MockTicket(
        ticket_id="ticket123",
        title="Test Ticket",
        description="Test Description",
        status=False,
    )
    mock_ticket_client.create_ticket.return_value = mock_ticket

    response = test_client.post(
        "/tickets",
        json={"title": "Test Ticket", "description": "Test Description"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ticket123"
    assert data["title"] == "Test Ticket"
    assert data["description"] == "Test Description"
    assert data["status"] is False
    mock_ticket_client.create_ticket.assert_called_once_with(
        "Test Ticket",
        "Test Description",
    )


def test_create_ticket_authentication_error(
    test_client: TestClient,
    mock_ticket_client: AsyncMock,
) -> None:
    """Test creating a ticket with authentication error."""
    mock_ticket_client.create_ticket.side_effect = TicketAuthenticationError(
        "Invalid token",
    )

    response = test_client.post(
        "/tickets",
        json={"title": "Test Ticket", "description": "Test Description"},
    )

    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


def test_create_ticket_api_error(
    test_client: TestClient,
    mock_ticket_client: AsyncMock,
) -> None:
    """Test creating a ticket with API error."""
    mock_ticket_client.create_ticket.side_effect = TicketAPIError("API error")

    response = test_client.post(
        "/tickets",
        json={"title": "Test Ticket", "description": "Test Description"},
    )

    assert response.status_code == 400
    assert "API error" in response.json()["detail"]


def test_get_ticket(test_client: TestClient, mock_ticket_client: AsyncMock) -> None:
    """Test getting a specific ticket."""
    mock_ticket = MockTicket(
        ticket_id="ticket123",
        title="Test Ticket",
        description="Test Description",
        status=True,
    )
    mock_ticket_client.get_ticket.return_value = mock_ticket

    response = test_client.get("/tickets/ticket123")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ticket123"
    assert data["title"] == "Test Ticket"
    assert data["description"] == "Test Description"
    assert data["status"] is True
    mock_ticket_client.get_ticket.assert_called_once_with("ticket123")


def test_get_ticket_not_found(
    test_client: TestClient,
    mock_ticket_client: AsyncMock,
) -> None:
    """Test getting a non-existent ticket."""
    mock_ticket_client.get_ticket.side_effect = TicketNotFoundError(
        "Ticket not found",
    )

    response = test_client.get("/tickets/nonexistent")

    assert response.status_code == 404
    assert "Ticket not found" in response.json()["detail"]


def test_update_ticket(test_client: TestClient, mock_ticket_client: AsyncMock) -> None:
    """Test updating a ticket."""
    mock_ticket = MockTicket(
        ticket_id="ticket123",
        title="Updated Title",
        description="Updated Description",
        status=True,
    )
    mock_ticket_client.update_ticket.return_value = mock_ticket

    response = test_client.put(
        "/tickets/ticket123",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "status": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "ticket123"
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Description"
    assert data["status"] is True
    mock_ticket_client.update_ticket.assert_called_once_with(
        "ticket123",
        "Updated Title",
        "Updated Description",
        True,
    )


def test_update_ticket_not_found(
    test_client: TestClient,
    mock_ticket_client: AsyncMock,
) -> None:
    """Test updating a non-existent ticket."""
    mock_ticket_client.update_ticket.side_effect = TicketNotFoundError(
        "Ticket not found",
    )

    response = test_client.put(
        "/tickets/nonexistent",
        json={
            "title": "Updated Title",
            "description": "Updated Description",
            "status": True,
        },
    )

    assert response.status_code == 404
    assert "Ticket not found" in response.json()["detail"]


def test_delete_ticket(test_client: TestClient, mock_ticket_client: AsyncMock) -> None:
    """Test deleting a ticket."""
    mock_ticket_client.delete_ticket.return_value = True

    response = test_client.delete("/tickets/ticket123")

    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_ticket_client.delete_ticket.assert_called_once_with("ticket123")


def test_delete_ticket_not_found(
    test_client: TestClient,
    mock_ticket_client: AsyncMock,
) -> None:
    """Test deleting a non-existent ticket."""
    mock_ticket_client.delete_ticket.side_effect = TicketNotFoundError(
        "Ticket not found",
    )

    response = test_client.delete("/tickets/nonexistent")

    assert response.status_code == 404
    assert "Ticket not found" in response.json()["detail"]


def test_delete_ticket_authentication_error(
    test_client: TestClient,
    mock_ticket_client: AsyncMock,
) -> None:
    """Test deleting a ticket with authentication error."""
    mock_ticket_client.delete_ticket.side_effect = TicketAuthenticationError(
        "Invalid token",
    )

    response = test_client.delete("/tickets/ticket123")

    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]
