"""Unit tests for the FastAPI mail client service.

These tests verify that the FastAPI endpoints handle requests and responses correctly,
using a mocked mail client to isolate the tests from the actual implementation.
"""

from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
import pytest

from mail_client_service.app import app
from mail_client_api.test_client import Message

client = TestClient(app)

@pytest.fixture
def mock_mail_client():
    """Create a mock mail client for testing."""
    with patch('mail_client_service.app.Client') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

def create_mock_message(msg_id: str, subject: str = "Test Subject"):
    """Create a mock message object."""
    return Message(
        id=msg_id,
        from_="sender@example.com",
        to="recipient@example.com",
        date="2025-10-03",
        subject=subject,
        body=f"Test body for message {msg_id}"
    )

def test_list_messages(mock_mail_client):
    """Test listing messages returns correct format and status code."""
    # Setup mock messages
    mock_messages = [
        create_mock_message("1", "First Message"),
        create_mock_message("2", "Second Message")
    ]
    mock_mail_client.get_messages.return_value = iter(mock_messages)

    # Make request
    response = client.get("/messages")

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0] == {
        "id": "1",
        "from": "sender@example.com",
        "to": "recipient@example.com",
        "date": "2025-10-03",
        "subject": "First Message",
        "body": "Test body for message 1"
    }

def test_list_messages_with_max_results(mock_mail_client):
    """Test that max_results parameter is respected."""
    mock_messages = [create_mock_message(str(i)) for i in range(5)]
    mock_mail_client.get_messages.return_value = iter(mock_messages[:3])

    response = client.get("/messages?max_results=3")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

def test_get_message_found(mock_mail_client):
    """Test retrieving a specific message that exists."""
    mock_message = create_mock_message("123", "Test Message")
    mock_mail_client.get_message.side_effect = lambda id: mock_message if id == "123" else ValueError("Message not found")

    response = client.get("/messages/123")
    
    assert response.status_code == 200
    assert response.json() == {
        "id": "123",
        "from": "sender@example.com",
        "to": "recipient@example.com",
        "date": "2025-10-03",
        "subject": "Test Message",
        "body": "Test body for message 123"
    }

def test_get_message_not_found(mock_mail_client):
    """Test retrieving a non-existent message."""
    mock_mail_client.get_message.side_effect = Exception("Message not found")
    
    response = client.get("/messages/999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"

def test_mark_as_read_success(mock_mail_client):
    """Test marking a message as read successfully."""
    mock_mail_client.mark_as_read.return_value = True
    
    response = client.post("/messages/123/read")
    
    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_mail_client.mark_as_read.assert_called_once_with(message_id="123")

def test_mark_as_read_not_found(mock_mail_client):
    """Test marking a non-existent message as read."""
    mock_mail_client.mark_as_read.return_value = False
    
    response = client.post("/messages/999/read")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"

def test_delete_message_success(mock_mail_client):
    """Test deleting a message successfully."""
    mock_mail_client.delete_message.return_value = True
    
    response = client.delete("/messages/123")
    
    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_mail_client.delete_message.assert_called_once_with(message_id="123")

def test_delete_message_not_found(mock_mail_client):
    """Test deleting a non-existent message."""
    mock_mail_client.delete_message.return_value = False
    
    response = client.delete("/messages/999")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Message not found"

def test_invalid_max_results(mock_mail_client):
    """Test that invalid max_results parameter returns 422."""
    response = client.get("/messages?max_results=0")
    assert response.status_code == 422

def test_messages_error_handling(mock_mail_client):
    """Test error handling when client throws an error."""
    mock_mail_client.get_messages.side_effect = Exception("Internal error")
    
    response = client.get("/messages")
    
    assert response.status_code == 500
