"""Integration tests for the mail client service.

These tests verify that the service client works correctly with the running service.
They use a mock Gmail client but test the real HTTP communication layer.
"""

import os
import pytest
import uvicorn
import multiprocessing
from unittest.mock import patch, MagicMock

from mail_client_service_impl import MailClientServiceImpl
from message import Message

# Constants
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8001  # Use different port than development
SERVICE_URL = f"http://{SERVICE_HOST}:{SERVICE_PORT}"

@pytest.fixture(scope="session")
def mock_gmail_client():
    """Create a mock Gmail client that will be used by the service."""
    with patch('mail_client_api.get_client') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture(scope="session")
def service_process(mock_gmail_client):
    """Start the FastAPI service in a separate process."""
    def run_service():
        import uvicorn
        uvicorn.run(
            "mail_client_service.app:app",
            host=SERVICE_HOST,
            port=SERVICE_PORT,
            log_level="error"
        )

    # Start service in a separate process
    process = multiprocessing.Process(target=run_service)
    process.start()
    
    # Wait for service to start
    import time
    time.sleep(2)
    
    yield process
    
    # Cleanup
    process.terminate()
    process.join()

@pytest.fixture
def service_client(service_process):
    """Create a service client connected to the test service."""
    return MailClientServiceImpl(base_url=SERVICE_URL)

def create_mock_message(msg_id: str, subject: str = "Test Subject"):
    """Create a mock message object."""
    message = MagicMock()
    message.id = msg_id
    message.from_ = "sender@example.com"
    message.to = "recipient@example.com"
    message.date = "2025-10-03"
    message.subject = subject
    message.body = f"Test body for message {msg_id}"
    return message

def test_list_messages(mock_gmail_client, service_client):
    """Test that listing messages works through the service."""
    # Setup mock response
    mock_messages = [
        create_mock_message("1", "First Message"),
        create_mock_message("2", "Second Message")
    ]
    mock_gmail_client.get_messages.return_value = mock_messages

    # Call through service
    messages = list(service_client.get_messages(max_results=2))

    # Verify results
    assert len(messages) == 2
    assert messages[0].id == "1"
    assert messages[0].subject == "First Message"
    assert messages[1].id == "2"
    assert messages[1].subject == "Second Message"

def test_get_message(mock_gmail_client, service_client):
    """Test that getting a specific message works through the service."""
    # Setup mock response
    mock_message = create_mock_message("123", "Test Message")
    mock_gmail_client.get_message.return_value = mock_message

    # Call through service
    message = service_client.get_message("123")

    # Verify result
    assert isinstance(message, Message)
    assert message.id == "123"
    assert message.subject == "Test Message"
    assert message.from_ == "sender@example.com"
    assert message.to == "recipient@example.com"
    assert message.date == "2025-10-03"
    assert message.body == "Test body for message 123"

def test_mark_as_read(mock_gmail_client, service_client):
    """Test that marking a message as read works through the service."""
    # Setup mock response
    mock_gmail_client.mark_as_read.return_value = True

    # Call through service
    result = service_client.mark_as_read("123")

    # Verify result
    assert result is True
    mock_gmail_client.mark_as_read.assert_called_once_with(message_id="123")

def test_delete_message(mock_gmail_client, service_client):
    """Test that deleting a message works through the service."""
    # Setup mock response
    mock_gmail_client.delete_message.return_value = True

    # Call through service
    result = service_client.delete_message("123")

    # Verify result
    assert result is True
    mock_gmail_client.delete_message.assert_called_once_with(message_id="123")

def test_error_handling(mock_gmail_client, service_client):
    """Test that service errors are handled correctly."""
    # Setup mock to raise an exception
    mock_gmail_client.get_message.side_effect = Exception("Not found")

    # Verify that the error is handled gracefully
    with pytest.raises(Exception):
        service_client.get_message("999")
