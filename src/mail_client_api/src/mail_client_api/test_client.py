"""Test implementation of the mail client for testing."""

from collections.abc import Iterator
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Message:
    """A message class for testing."""
    id: str
    from_: str
    to: str
    date: str
    subject: str
    body: str

class TestClient:
    """A test implementation of the mail client for testing.
    
    This implementation stores messages in memory and provides basic operations
    for testing purposes.
    """

    def __init__(self):
        """Initialize a new test client with some sample messages."""
        self._messages = {
            "1": Message("1", "sender1@example.com", "recipient@example.com", "2025-10-03", "Test Message 1", "Body 1"),
            "2": Message("2", "sender2@example.com", "recipient@example.com", "2025-10-03", "Test Message 2", "Body 2"),
            "3": Message("3", "sender3@example.com", "recipient@example.com", "2025-10-03", "Test Message 3", "Body 3"),
        }

    def get_message(self, message_id: str) -> Message:
        """Get a message by ID."""
        if message_id not in self._messages:
            raise ValueError(f"Message {message_id} not found")
        return self._messages[message_id]

    def delete_message(self, message_id: str) -> bool:
        """Delete a message by ID."""
        if message_id not in self._messages:
            return False
        del self._messages[message_id]
        return True

    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read by ID."""
        if message_id not in self._messages:
            return False
        return True

    def get_messages(self, max_results: int = 10) -> Iterator[Message]:
        """Get an iterator of messages."""
        messages = sorted(self._messages.values(), key=lambda m: m.id)
        return iter(messages[:max_results])
