
"""Unit tests for the FastAPI mail client service.

These tests verify that the FastAPI endpoints handle requests and responses correctly,
using a mocked mail client to isolate the tests from the actual implementation.
"""

from collections.abc import Generator
from http import HTTPStatus
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from mail_client_service import app

client = TestClient(app)

@pytest.fixture
def mock_mail_client() -> Generator[MagicMock, Any, None]:
    """Create a mock mail client for testing."""
    with patch("mail_client_service.main.get_client") as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

def create_mock_message(msg_id: str, subject: str = "Test Subject") -> MagicMock:
    """Return a mock message object."""
    mock_msg = MagicMock()
    mock_msg.id = msg_id
    mock_msg.from_ = "sender@example.com"
    mock_msg.to = "recipient@example.com"
    mock_msg.date = "2025-10-03"
    mock_msg.subject = subject
    mock_msg.body = f"Test body for message {msg_id}"
    return mock_msg

def test_list_messages(mock_mail_client: MagicMock) -> None:
    """Test listing messages returns correct format and status code."""
    mock_messages = [
        create_mock_message("1", "First Message"),
        create_mock_message("2", "Second Message"),
    ]
    mock_mail_client.get_messages.return_value = iter(mock_messages)

    # Make request
    response = client.get("/messages")

    # Verify response
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == len(mock_messages)
    assert data[0] == {
        "id": "1",
        "from": "sender@example.com",
        "to": "recipient@example.com",
        "date": "2025-10-03",
        "subject": "First Message",
        "body": "Test body for message 1",
    }

def test_list_messages_with_max_results(mock_mail_client: MagicMock) -> None:
    """Test that max_results parameter is respected."""
    mock_messages = [create_mock_message(str(i)) for i in range(5)]
    mock_mail_client.get_messages.return_value = iter(mock_messages[:3])

    response = client.get("/messages?max_results=3")
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data) == len(mock_messages[:3])

def test_get_message_found(mock_mail_client: MagicMock) -> None:
    """Test retrieving a specific message that exists."""
    mock_message = create_mock_message("123", "Test Message")
    mock_mail_client.get_message.side_effect = lambda i: mock_message if i == "123" else ValueError("Message not found")

    response = client.get("/messages/123")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {
        "id": "123",
        "from": "sender@example.com",
        "to": "recipient@example.com",
        "date": "2025-10-03",
        "subject": "Test Message",
        "body": "Test body for message 123",
    }

def test_get_message_not_found(mock_mail_client: MagicMock) -> None:
    """Test retrieving a non-existent message."""
    mock_mail_client.get_message.side_effect = Exception("Message not found")
    response = client.get("/messages/999")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["detail"] == "Message not found"

def test_mark_as_read_success(mock_mail_client: MagicMock) -> None:
    """Test marking a message as read successfully."""
    mock_mail_client.mark_as_read.return_value = True
    response = client.post("/messages/123/mark-as-read")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"success": True}
    mock_mail_client.mark_as_read.assert_called_once_with("123")

def test_mark_as_read_not_found(mock_mail_client: MagicMock) -> None:
    """Test marking a non-existent message as read."""
    mock_mail_client.mark_as_read.return_value = False
    response = client.post("/messages/999/mark-as-read")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["detail"] == "Message not found"

def test_delete_message_success(mock_mail_client: MagicMock) -> None:
    """Test deleting a message successfully."""
    mock_mail_client.delete_message.return_value = True
    response = client.delete("/messages/123")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"success": True}
    mock_mail_client.delete_message.assert_called_once_with("123")

def test_delete_message_not_found(mock_mail_client: MagicMock) -> None:
    """Test deleting a non-existent message."""
    mock_mail_client.delete_message.return_value = False
    response = client.delete("/messages/999")
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["detail"] == "Message not found"

def test_invalid_max_results(mock_mail_client: MagicMock) -> None:
    """Test that invalid max_results parameter returns 400."""
    response = client.get("/messages?max_results=0")
    assert response.status_code == HTTPStatus.BAD_REQUEST

def test_messages_error_handling(mock_mail_client: MagicMock) -> None:
    """Test error handling when client throws an error."""
    mock_mail_client.get_messages.side_effect = Exception("Internal error")
    response = client.get("/messages")
    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
