"""End-to-end tests for the mail client service.

These tests verify that the entire system works with real Gmail API.
They require proper Gmail API credentials to be configured.
"""

import multiprocessing
import time
from collections.abc import Generator
from multiprocessing.context import Process
from typing import Any

import pytest
import uvicorn
from mail_client_adapter.mail_client_adapter import MailClientAdapter
from mail_client_api.message import Message

import gmail_client_impl  # Register Gmail implementation  # noqa: F401

# Constants
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8002  # Use different port than development/integration
SERVICE_URL = f"http://{SERVICE_HOST}:{SERVICE_PORT}"

def _run_service() -> None:
    uvicorn.run(
        "mail_client_service:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        log_level="error",
    )

@pytest.fixture(scope="session")
def service_process() -> Generator[Process, Any, None]:
    """Start the FastAPI service in a separate process."""
    # Start service in a separate process
    process = multiprocessing.Process(target=_run_service)
    process.start()

    # Wait for service to start
    time.sleep(2)

    yield process

    # Cleanup
    process.terminate()
    process.join()

@pytest.fixture
def service_client(service_process: Process) -> MailClientAdapter:
    """Create a service client connected to the test service."""
    return MailClientAdapter(base_url=SERVICE_URL)

@pytest.mark.e2e
@pytest.mark.gmail
def test_list_messages_e2e(service_client: MailClientAdapter) -> None:
    """Test listing messages from real Gmail."""
    # Get messages from Gmail
    max_results = 3
    messages = list(service_client.get_messages(max_results=max_results))

    # Basic validation
    assert len(messages) <= max_results
    if messages:
        assert isinstance(messages[0], Message)
        assert messages[0].id
        assert messages[0].subject
        assert messages[0].from_
        assert messages[0].to
        assert messages[0].date

@pytest.mark.e2e
@pytest.mark.gmail
def test_get_message_e2e(service_client: MailClientAdapter) -> None:
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

@pytest.mark.e2e
@pytest.mark.gmail
def test_mark_as_read_e2e(service_client: MailClientAdapter) -> None:
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

@pytest.mark.e2e
@pytest.mark.gmail
def test_full_message_lifecycle_e2e(service_client: MailClientAdapter) -> None:
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

    # Get specific message
    message = service_client.get_message(message_id)
    assert message.id == message_id

    # Mark as read
    result = service_client.mark_as_read(message_id)
    assert result is True

    # Delete message - Commented out for safety
    # Uncomment these lines if you want to test deletion
    # result = service_client.delete_message(message_id)  # noqa: ERA001
    # assert result is True
    # print(f"Successfully deleted message")  # noqa: ERA001
