"""Message model for the mail client API."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class Message(Protocol):
    """A protocol representing an email message.

    This protocol defines the interface for message objects that represent
    email messages in the system.
    """

    @property
    def id(self) -> str:
        """Return the message ID."""
        raise NotImplementedError

    @property
    def from_(self) -> str:
        """Return the sender's email address."""
        raise NotImplementedError

    @property
    def to(self) -> str:
        """Return the recipient's email address."""
        raise NotImplementedError

    @property
    def date(self) -> str:
        """Return the message date."""
        raise NotImplementedError

    @property
    def subject(self) -> str:
        """Return the message subject."""
        raise NotImplementedError

    @property
    def body(self) -> str:
        """Return the message body."""
        raise NotImplementedError
