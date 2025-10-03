"""End-to-end tests for the mail client service.

These tests verify that the entire system works with real Gmail API.
They require proper Gmail API credentials to be configured.
"""

import os
import pytest
import uvicorn
import multiprocessing
import time

from mail_client_service_impl import MailClientServiceImpl
from message import Message
import gmail_client_impl  # Register Gmail implementation
import gmail_message_impl  # Register Gmail message implementation

# Constants
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8002  # Use different port than development/integration
SERVICE_URL = f"http://{SERVICE_HOST}:{SERVICE_PORT}"

@pytest.fixture(scope="session")
def service_process():
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
    time.sleep(2)
    
    yield process
    
    # Cleanup
    process.terminate()
    process.join()

@pytest.fixture
def service_client(service_process):
    """Create a service client connected to the test service."""
    return MailClientServiceImpl(base_url=SERVICE_URL)

@pytest.mark.e2e
@pytest.mark.gmail
def test_list_messages_e2e(service_client):
    """Test listing messages from real Gmail."""
    # Get messages from Gmail
    messages = list(service_client.get_messages(max_results=3))

    # Basic validation
    assert len(messages) <= 3
    if messages:
        assert isinstance(messages[0], Message)
        assert messages[0].id
        assert messages[0].subject
        assert messages[0].from_
        assert messages[0].to
        assert messages[0].date
        print(f"Found message: {messages[0].subject}")

@pytest.mark.e2e
@pytest.mark.gmail
def test_get_message_e2e(service_client):
    """Test getting a specific message from real Gmail."""
    # First get a list of messages to get a valid ID
    messages = list(service_client.get_messages(max_results=1))
    if not messages:
        pytest.skip("No messages available in Gmail")

    # Get specific message
    message_id = messages[0].id
    message = service_client.get_message(message_id)

    # Verify message
    assert isinstance(message, Message)
    assert message.id == message_id
    assert message.subject
    assert message.from_
    assert message.to
    assert message.date
    assert message.body is not None
    print(f"Retrieved message: {message.subject}")

@pytest.mark.e2e
@pytest.mark.gmail
def test_mark_as_read_e2e(service_client):
    """Test marking a message as read in real Gmail."""
    # Get a message to mark as read
    messages = list(service_client.get_messages(max_results=1))
    if not messages:
        pytest.skip("No messages available in Gmail")

    # Mark as read
    message_id = messages[0].id
    result = service_client.mark_as_read(message_id)

    # Verify result
    assert result is True
    print(f"Marked message as read: {messages[0].subject}")

@pytest.mark.e2e
@pytest.mark.gmail
def test_full_message_lifecycle_e2e(service_client):
    """Test a complete message lifecycle with real Gmail.
    
    This test demonstrates:
    1. Listing messages
    2. Getting a specific message
    3. Marking it as read
    4. Optional: Deleting it (commented out for safety)
    """
    # List messages
    messages = list(service_client.get_messages(max_results=1))
    if not messages:
        pytest.skip("No messages available in Gmail")

    message_id = messages[0].id
    print(f"\nTesting with message: {messages[0].subject}")

    # Get specific message
    message = service_client.get_message(message_id)
    assert message.id == message_id
    print(f"Successfully retrieved message details")

    # Mark as read
    result = service_client.mark_as_read(message_id)
    assert result is True
    print(f"Successfully marked message as read")

    # Delete message - Commented out for safety
    # Uncomment these lines if you want to test deletion
    # result = service_client.delete_message(message_id)
    # assert result is True
    # print(f"Successfully deleted message")
