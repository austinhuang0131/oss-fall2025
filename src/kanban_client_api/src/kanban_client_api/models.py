"""Data models for Kanban entities."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime  # noqa: TC003


class KanbanBoard(ABC):
    """Abstract base class for Kanban board."""

    @property
    @abstractmethod
    def id(self) -> str:
        """The unique identifier for the board."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the board."""

    @property
    @abstractmethod
    def description(self) -> str | None:
        """The description of the board."""

    @property
    @abstractmethod
    def closed(self) -> bool:
        """Whether the board is closed."""

    @property
    @abstractmethod
    def url(self) -> str | None:
        """The URL of the board."""

    @property
    @abstractmethod
    def created_at(self) -> datetime | None:
        """The creation time of the board."""


class KanbanList(ABC):
    """Abstract base class for Kanban list within a board."""

    @property
    @abstractmethod
    def id(self) -> str:
        """The unique identifier for the list."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the list."""

    @property
    @abstractmethod
    def board_id(self) -> str:
        """The ID of the board this list belongs to."""

    @property
    @abstractmethod
    def position(self) -> float:
        """The position of the list in the board."""

    @property
    @abstractmethod
    def closed(self) -> bool:
        """Whether the list is closed."""


class KanbanCard(ABC):
    """Abstract base class for Kanban card within a list."""

    @property
    @abstractmethod
    def id(self) -> str:
        """The unique identifier for the card."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the card."""

    @property
    @abstractmethod
    def list_id(self) -> str:
        """The ID of the list this card belongs to."""

    @property
    @abstractmethod
    def board_id(self) -> str:
        """The ID of the board this card belongs to."""

    @property
    @abstractmethod
    def description(self) -> str | None:
        """The description of the card."""

    @property
    @abstractmethod
    def position(self) -> float:
        """The position of the card in the list."""

    @property
    @abstractmethod
    def closed(self) -> bool:
        """Whether the card is closed."""

    @property
    @abstractmethod
    def due_date(self) -> datetime | None:
        """The due date of the card."""

    @property
    @abstractmethod
    def url(self) -> str | None:
        """The URL of the card."""

    @property
    @abstractmethod
    def created_at(self) -> datetime | None:
        """The creation time of the card."""


class KanbanUser(ABC):
    """Abstract base class for Kanban user."""

    @property
    @abstractmethod
    def id(self) -> str:
        """The unique identifier for the user."""

    @property
    @abstractmethod
    def username(self) -> str:
        """The username of the user."""

    @property
    @abstractmethod
    def full_name(self) -> str | None:
        """The full name of the user."""

    @property
    @abstractmethod
    def email(self) -> str | None:
        """The email address of the user."""
