import os
from typing import Any
from unittest.mock import Mock, patch

import pytest
from googleapiclient.errors import HttpError

from gmail_client_impl.gmail_impl import GmailClient


pytestmark = pytest.mark.circleci


def _mock_chain_for(service: Mock) -> tuple[Mock, Mock]:
    mock_users = Mock()
    mock_messages = Mock()
    service.users.return_value = mock_users
    mock_users.messages.return_value = mock_messages
    return mock_users, mock_messages


@patch("gmail_client_impl.gmail_impl.build")
def test_init_with_provided_service_skips_auth(mock_build: Any) -> None:
    mock_service = Mock()
    client = GmailClient(service=mock_service)
    assert client.service is mock_service
    mock_build.assert_not_called()


@patch("gmail_client_impl.gmail_impl.build")
@patch("gmail_client_impl.gmail_impl.Credentials")
@patch("gmail_client_impl.gmail_impl.Request")
@patch.dict(
    os.environ,
    {
        "GMAIL_CLIENT_ID": "cid",
        "GMAIL_CLIENT_SECRET": "csec",
        "GMAIL_REFRESH_TOKEN": "rtok",
    },
)
def test_env_auth_success_saves_token(mock_request: Any, mock_creds_cls: Any, mock_build: Any) -> None:
    mock_creds = Mock()
    mock_creds.valid = True
    mock_creds.refresh_token = "rtok"
    mock_creds_cls.return_value = mock_creds
    mock_build.return_value = Mock()

    with patch("gmail_client_impl.gmail_impl.Path") as mock_path, patch.object(
        GmailClient, "_save_token"
    ) as mock_save:
        mock_path.return_value.exists.return_value = False
        client = GmailClient()
        assert client.service is mock_build.return_value
        mock_creds.refresh.assert_called_once()
        mock_save.assert_called_once()


def test_interactive_flow_returns_invalid_creds_raises_failure_message() -> None:
    with patch.object(GmailClient, "_run_interactive_flow") as mock_flow, patch(
        "gmail_client_impl.gmail_impl.build"
    ) as mock_build:
        creds = Mock()
        creds.valid = False
        creds.refresh_token = "rtok"
        mock_flow.return_value = creds
        mock_build.return_value = Mock()

        with pytest.raises(RuntimeError, match="Failed to obtain credentials"):
            GmailClient(interactive=True)


@patch("gmail_client_impl.gmail_impl.build")
@patch("gmail_client_impl.gmail_impl.Path")
@patch("gmail_client_impl.gmail_impl.Credentials")
def test_token_file_not_found_then_error(mock_creds_cls: Any, mock_path: Any, mock_build: Any) -> None:
    with patch.dict(os.environ, {}, clear=True):
        mock_path.return_value.exists.return_value = False
        with pytest.raises(RuntimeError, match="No valid credentials found"):
            GmailClient()


def test_run_interactive_flow_missing_credentials_file() -> None:
    client = GmailClient(service=Mock())
    with patch("gmail_client_impl.gmail_impl.Path") as mock_path:
        mock_path.return_value.exists.return_value = False
        with pytest.raises(FileNotFoundError):
            client._run_interactive_flow("credentials.json")


def test_delete_message_success_and_failure_paths() -> None:
    service = Mock()
    client = GmailClient(service=service)
    _, msgs = _mock_chain_for(service)

    # Deletion succeeds even if pre-fetch fails
    with patch.object(client, "get_message", side_effect=ValueError("boom")):
        delete_call = Mock()
        msgs.delete.return_value = delete_call
        delete_call.execute.return_value = None
        assert client.delete_message("mid") is True

    # Deletion failure returns False
    delete_call = Mock()
    msgs.delete.return_value = delete_call
    error_response = Mock(status=500, reason="fail")
    delete_call.execute.side_effect = HttpError(error_response, b"err")
    assert client.delete_message("mid") is False


def test_mark_as_read_success_and_failure_paths() -> None:
    service = Mock()
    client = GmailClient(service=service)
    _, msgs = _mock_chain_for(service)

    mod = Mock()
    msgs.modify.return_value = mod
    mod.execute.return_value = None
    assert client.mark_as_read("mid") is True

    error_response = Mock(status=500, reason="fail")
    mod.execute.side_effect = HttpError(error_response, b"err")
    assert client.mark_as_read("mid") is False


def test_get_message_and_get_messages_iter() -> None:
    service = Mock()
    client = GmailClient(service=service)
    users, msgs = _mock_chain_for(service)

    # get_message
    get_call = Mock()
    msgs.get.return_value = get_call
    get_call.execute.return_value = {"raw": "abc"}
    with patch("gmail_client_impl.gmail_impl.message.get_message") as factory:
        m = Mock()
        factory.return_value = m
        assert client.get_message("id1") is m

    # get_messages iterator with mix of good/bad entries
    list_call = Mock()
    msgs.list.return_value = list_call
    list_call.execute.return_value = {"messages": [{"id": "a"}, {"x": 1}, {"id": "b"}]}

    get_call.execute.side_effect = [{"raw": "r1"}, {"raw": "r2"}]
    with patch("gmail_client_impl.gmail_impl.message.get_message") as factory2:
        m1, m2 = Mock(), Mock()
        factory2.side_effect = [m1, m2]
        out = list(client.get_messages(3))
        assert out == [m1, m2]


