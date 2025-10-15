"""Test implementation of the mail client for testing."""

from collections.abc import Iterator

import mail_client_api
from mail_client_api import Client
from mail_client_api.message import Message as AbstractMessage


class Message(AbstractMessage):
    """A simple implementation of the Message class for testing purposes."""

    def __init__(self, _id: str, from_: str, to: str, date: str, subject: str, body: str) -> None:
        """Initialize a new message."""
        self._id = _id
        self._from_ = from_
        self._to = to
        self._date = date
        self._subject = subject
        self._body = body

    @property
    def id(self) -> str:
        """Return the unique identifier of the message."""
        return self._id

    @property
    def from_(self) -> str:
        """Return the sender's email address."""
        return self._from_

    @property
    def to(self) -> str:
        """Return the recipient's email address."""
        return self._to

    @property
    def date(self) -> str:
        """Return the date the message was sent."""
        return self._date

    @property
    def subject(self) -> str:
        """Return the subject line of the message."""
        return self._subject

    @property
    def body(self) -> str:
        """Return the plain text content of the message."""
        return self._body

class TestClient(Client):
    """A test implementation of the mail client for testing.

    This implementation stores messages in memory and provides basic operations
    for testing purposes.
    """

    def __init__(self) -> None:
        """Initialize a new test client with some sample messages."""
        self._messages: dict[str, Message] = {
            "1": Message("1", "sender1@example.com", "recipient@example.com", "2025-10-03", "Test Message 1", "Body 1"),
            "2": Message("2", "sender2@example.com", "recipient@example.com", "2025-10-03", "Test Message 2", "Body 2"),
            "3": Message("3", "sender3@example.com", "recipient@example.com", "2025-10-03", "Test Message 3", "Body 3"),
        }

    def get_message(self, message_id: str) -> Message:
        """Get a message by ID."""
        if message_id not in self._messages:
            msg = f"Message {message_id} not found"
            raise ValueError(msg)
        return self._messages[message_id]

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID."""
        if message_id not in self._messages:
            return False
        del self._messages[message_id]
        return True

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read by ID."""
        return message_id in self._messages

    def get_messages(self, max_results: int = 10) -> Iterator[Message]:
        """Get an iterator of messages."""
        messages = sorted(self._messages.values(), key=lambda m: m.id)
        return iter(messages[:max_results])

_singleton_client = TestClient()
def get_client_impl(*, interactive: bool = False) -> mail_client_api.Client:
    """Return a singleton :class:`TestClient` instance."""
    return _singleton_client

def register() -> None:
    """Register the Gmail client implementation with the mail client API."""
    mail_client_api.get_client = get_client_impl
