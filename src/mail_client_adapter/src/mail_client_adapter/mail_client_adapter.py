"""Adapter for mail_client_api.Client to proxy calls to a running mail_client_service server."""

from collections.abc import Iterator

from mail_client_api.client import Client
from mail_client_api.message import Message
from mail_client_service_client.api.default.delete_message_messages_message_id_delete import (
    sync as delete_message_sync,
)
from mail_client_service_client.api.default.get_message_messages_message_id_get import (
    sync as get_message_sync,
)
from mail_client_service_client.api.default.get_messages_messages_get import (
    sync as get_messages_sync,
)
from mail_client_service_client.api.default.mark_as_read_messages_message_id_mark_as_read_post import (
    sync as mark_as_read_sync,
)
from mail_client_service_client.client import Client as ServiceClient


class MailClientAdapter(Client):
    """Adapter that proxies mail_client_api.Client calls to a FastAPI service."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """Initialize RemoteMailClient with the FastAPI service base URL.

        Args:
            base_url: The base URL of the FastAPI service.

        """
        self.client = ServiceClient(base_url=base_url)

    def get_message(self, message_id: str) -> Message:
        """Fetch a message by ID from the remote service using OpenAPI client."""
        result = get_message_sync(message_id=message_id, client=self.client)
        if result is None:
            msg = "Failed to fetch message"
            raise ValueError(msg)
        if hasattr(result, "additional_properties"):
            return ServiceMessage(result.additional_properties)
        if isinstance(result, dict):
            return ServiceMessage(result)
        msg = "Failed to fetch message"
        raise ValueError(msg)

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID via the remote service using OpenAPI client."""
        result = delete_message_sync(message_id=message_id, client=self.client)
        return result is not None

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read by ID via the remote service using OpenAPI client."""
        result = mark_as_read_sync(message_id=message_id, client=self.client)
        return result is not None

    def get_messages(self, max_results: int = 10) -> Iterator[Message]:
        """Return an iterator of message summaries from the remote service using OpenAPI client."""
        results = get_messages_sync(client=self.client, max_results=max_results)
        if isinstance(results, list):
            for item in results:
                if hasattr(item, "additional_properties"):
                    yield ServiceMessage(item.additional_properties)
                elif isinstance(item, dict):
                    yield ServiceMessage(item)


class ServiceMessage(Message):
    """Proxy for Message objects returned by the remote service."""

    def __init__(self, data: dict[str, str]) -> None:
        """Initialize ServiceMessage with message data.

        Args:
            data: Dictionary containing message fields.

        """
        self._data: dict[str, str] = data

    @property
    def id(self) -> str:
        """Return the message ID."""
        return self._data["id"]

    @property
    def from_(self) -> str:
        """Return the sender's email address."""
        return self._data["from"]

    @property
    def to(self) -> str:
        """Return the recipient's email address."""
        return self._data["to"]

    @property
    def date(self) -> str:
        """Return the date the message was sent."""
        return self._data["date"]

    @property
    def subject(self) -> str:
        """Return the subject line of the message."""
        return self._data["subject"]

    @property
    def body(self) -> str:
        """Return the body of the message."""
        return self._data.get("body", "")
