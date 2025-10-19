"""Integration tests for the mail client service.

These tests verify that the service client works correctly with the running service.
They use a mock Gmail client but test the real HTTP communication layer.
"""

import multiprocessing
import os
from collections.abc import Generator
from multiprocessing.context import Process
from typing import Any

import pytest
import uvicorn

from mail_client_adapter import MailClientAdapter

pytestmark = pytest.mark.integration

# Constants
SERVICE_HOST = "127.0.0.1"
SERVICE_PORT = 8001  # Use different port than development
SERVICE_URL = f"http://{SERVICE_HOST}:{SERVICE_PORT}"

os.environ["MOCK_CLIENT"] = "1"

def _run_service() -> None:
    uvicorn.run(
        "mail_client_service:app",
        host=SERVICE_HOST,
        port=SERVICE_PORT,
        log_level="error",
    )

@pytest.fixture(scope="session")
def service_process() -> Generator[Process, Any, None]:
    """Fixture to start and stop the mail client service for testing."""
    # Start service in a separate process
    process = multiprocessing.Process(target=_run_service)
    process.start()

    # Wait for service to start
    import time
    time.sleep(2)

    yield process

    # Cleanup
    process.terminate()
    process.join()

@pytest.fixture
def service_client(service_process: Process) -> MailClientAdapter:
    """Create a service client connected to the test service."""
    return MailClientAdapter(base_url=SERVICE_URL)

def test_list_messages(service_client: MailClientAdapter) -> None:
    """Test that listing messages works through the service."""
    # Call through service
    max_results = 2
    messages = list(service_client.get_messages(max_results=max_results))

    # Verify results
    assert len(messages) == max_results
    assert messages[0].id == "1"
    assert messages[0].subject == "Test Message 1"
    assert messages[1].id == "2"
    assert messages[1].subject == "Test Message 2"

def test_get_message(service_client: MailClientAdapter) -> None:
    """Test that getting a specific message works through the service."""
    # Call through service
    message = service_client.get_message("3")

    # Verify result
    assert message.id == "3"
    assert message.subject == "Test Message 3"
    assert message.from_ == "sender3@example.com"
    assert message.to == "recipient@example.com"
    assert message.date == "2025-10-03"
    assert message.body == "Body 3"

def test_mark_as_read(service_client: MailClientAdapter) -> None:
    """Test that marking a message as read works through the service."""
    # Call through service
    result = service_client.mark_as_read("3")

    # Verify result
    assert result is True

def test_delete_message(service_client: MailClientAdapter) -> None:
    """Test that deleting a message works through the service."""
    # Call through service
    result = service_client.delete_message("3")

    # Verify result
    assert result is True

    # check that getting the message now fails
    with pytest.raises(ValueError, match="Failed to fetch message"):
        service_client.get_message("3")

def test_error_handling(service_client: MailClientAdapter) -> None:
    """Test that service errors are handled correctly."""
    # Verify that the error is handled gracefully
    with pytest.raises(ValueError, match="Failed to fetch message"):
        service_client.get_message("999")
