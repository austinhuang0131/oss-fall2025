"""Data models for Ticket entities."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Ticket(ABC):
    """Abstract base class for a Ticket."""

    @property
    @abstractmethod
    def id(self) -> str:
        """The unique identifier for the ticket."""

    @property
    @abstractmethod
    def title(self) -> str:
        """The title of the ticket."""

    @property
    @abstractmethod
    def description(self) -> str:
        """The description of the ticket."""

    @property
    @abstractmethod
    def status(self) -> bool:
        """The status of the ticket.

        False = Open / To Do
        True = Done / Completed
        """
