"""Mail Client API - Core protocols and contracts.

This module defines the core protocols (interfaces) for the mail client system.
It provides abstract contracts that concrete implementations must follow to
enable email retrieval, message management, and client operations.

Usage:
    from mail_client_api import get_client, Client

    # Get a client instance from an implementation
    client = get_client()  # Returns concrete implementation

    # Use the client to fetch messages
    messages = client.get_messages()
    for message in messages:
        print(f"Subject: {message.subject}")
"""

from collections.abc import Iterator
from typing import Protocol, runtime_checkable

from message import Message


@runtime_checkable
class Client(Protocol):
    """A protocol representing a mail client for email operations.

    This protocol defines the interface for mail client implementations
    that can retrieve, delete, and manage email messages from a mail server.
    """

    def get_message(self, message_id: str) -> Message:
        """Return a message by its ID.

        Args:
            message_id (str): The ID of the message to retrieve.

        Returns:
            Message: The message object corresponding to the given ID.

        """
        raise NotImplementedError

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by its ID.

        Args:
            message_id (str): The ID of the message to delete.

        Returns:
            bool: True if the message was successfully deleted, False otherwise.

        """
        raise NotImplementedError

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read by its ID.

        Args:
            message_id (str): The ID of the message to mark as read.

        Returns:
            bool: True if the message was successfully marked as read, False otherwise.

        """
        raise NotImplementedError

    def get_messages(self, max_results: int = 10) -> Iterator[Message]:
        """Return an iterator of all messages in the inbox.

        Args:
            max_results (int, optional): The maximum number of messages to return. Defaults to 10.

        Returns:
            Iterator[Message]: An iterator yielding Message objects from the inbox.

        """
        raise NotImplementedError


def get_client(interactive: bool = False) -> Client:
    """Return an instance of a Mail Client.

    This is a factory function that returns a concrete implementation
    of the Client protocol. The actual implementation is injected
    by implementation packages.

    Args:
        interactive (bool): If True, the client may prompt for user input
        during initialization (e.g., for OAuth2 flow). If False, it will
        use environment variables or other non-interactive methods.

    Returns:
        Client: A concrete mail client instance.
    """
    from mail_client_api.test_client import TestClient
    return TestClient()
