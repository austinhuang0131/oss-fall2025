"""Service implementation of the mail client API.

This module provides a concrete implementation of the Client protocol
that uses the REST API service to perform mail client operations.
"""

from typing import Iterator
from mail_client_api import Client
from mail_client_service_client import Client as ServiceClient
from mail_client_service_client.models import MessageResponse
from message import Message


class ServiceMessage(Message):
    """Message implementation wrapping a service response."""

    def __init__(self, response: MessageResponse):
        """Initialize message with service response data."""
        self._response = response

    @property
    def id(self) -> str:
        """Return message ID."""
        return self._response.id

    @property
    def from_(self) -> str:
        """Return sender's email."""
        return self._response.from_  # type: ignore

    @property
    def to(self) -> str:
        """Return recipient's email."""
        return self._response.to

    @property
    def date(self) -> str:
        """Return message date."""
        return self._response.date

    @property
    def subject(self) -> str:
        """Return message subject."""
        return self._response.subject

    @property
    def body(self) -> str:
        """Return message body."""
        return self._response.body


class MailClientServiceImpl(Client):
    """A Client implementation that uses the REST API service."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        """Initialize the client with the service URL."""
        self._client = ServiceClient(base_url=base_url)

    def get_message(self, message_id: str) -> Message:
        """Get a message by ID."""
        response = self._client.messages.get_message.sync(message_id=message_id)
        return ServiceMessage(response)

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID."""
        try:
            response = self._client.messages.delete_message.sync(message_id=message_id)
            return response.success
        except Exception:
            return False

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        try:
            response = self._client.messages.mark_as_read.sync(message_id=message_id)
            return response.success
        except Exception:
            return False

    def get_messages(self, max_results: int = 10) -> Iterator[Message]:
        """Get multiple messages."""
        response = self._client.messages.list_messages.sync(max_results=max_results)
        for message in response:
            yield ServiceMessage(message)


def get_client_impl(interactive: bool = False) -> Client:
    """Create a new service client instance.
    
    Args:
        interactive: Ignored since we don't need auth.
        
    Returns:
        A mail client service implementation.
    """
    return MailClientServiceImpl()
