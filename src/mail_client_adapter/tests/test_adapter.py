"""Tests for the MailClientAdapter."""

from unittest.mock import MagicMock, patch

from mail_client_adapter.mail_client_adapter import MailClientAdapter


@patch("httpx.Client.request")
def test_get_messages_remote(mock_request: MagicMock) -> None:
    """Test fetching a message via the remote service."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {"id": "1", "from": "a", "to": "b", "date": "2023", "subject": "Test"},
    ]
    mock_request.return_value = mock_response
    client = MailClientAdapter(base_url="http://localhost:8000")
    messages = list(client.get_messages(max_results=1))
    assert len(messages) == 1
    assert messages[0].id == "1"
    assert messages[0].from_ == "a"
    assert messages[0].to == "b"
    assert messages[0].date == "2023"
    assert messages[0].subject == "Test"

@patch("httpx.Client.request")
def test_get_message_remote(mock_request: MagicMock) -> None:
    """Test fetching a single message via the remote service."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "1", "from": "a", "to": "b", "date": "2023", "subject": "Test", "body": "Body",
    }
    mock_request.return_value = mock_response
    client = MailClientAdapter(base_url="http://localhost:8000")
    msg = client.get_message("1")
    assert msg.id == "1"
    assert msg.body == "Body"

@patch("httpx.Client.request")
def test_delete_message_remote(mock_request: MagicMock) -> None:
    """Test deleting a message via the remote service."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_request.return_value = mock_response
    client = MailClientAdapter(base_url="http://localhost:8000")
    assert client.delete_message("1") is True

@patch("httpx.Client.request")
def test_mark_as_read_remote(mock_request: MagicMock) -> None:
    """Test marking a message as read via the remote service."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_request.return_value = mock_response
    client = MailClientAdapter(base_url="http://localhost:8000")
    assert client.mark_as_read("1") is True
