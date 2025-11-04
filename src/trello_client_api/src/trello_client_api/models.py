"""Data models for Trello entities."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel


class TrelloBoard(BaseModel):
    @classmethod
    def from_generated(cls, generated_board: object) -> TrelloBoard:
        """Convert from generated client board model to TrelloBoard."""
        return cls(
            id=getattr(generated_board, "id", ""),
            name=getattr(generated_board, "name", ""),
            description=getattr(generated_board, "description", None),
            closed=getattr(generated_board, "closed", False),
            url=getattr(generated_board, "url", None),
            created_at=getattr(generated_board, "created_at", None),
        )
    """Represents a Trello board."""

    id: str
    name: str
    description: str | None = None
    closed: bool = False
    url: str | None = None
    created_at: datetime | None = None


class TrelloList(BaseModel):
    @classmethod
    def from_generated(cls, generated_list: object) -> TrelloList:
        """Convert from generated client list model to TrelloList."""
        return cls(
            id=getattr(generated_list, "id", ""),
            name=getattr(generated_list, "name", ""),
            board_id=getattr(generated_list, "board_id", ""),
            position=getattr(generated_list, "position", 0.0),
            closed=getattr(generated_list, "closed", False),
        )
    """Represents a Trello list within a board."""

    id: str
    name: str
    board_id: str
    position: float
    closed: bool = False


class TrelloCard(BaseModel):
    @classmethod
    def from_generated(cls, generated_card: object) -> TrelloCard:
        """Convert from generated client card model to TrelloCard."""
        return cls(
            id=getattr(generated_card, "id", ""),
            name=getattr(generated_card, "name", ""),
            list_id=getattr(generated_card, "list_id", ""),
            board_id=getattr(generated_card, "board_id", ""),
            description=getattr(generated_card, "description", None),
            position=getattr(generated_card, "position", 0.0),
            closed=getattr(generated_card, "closed", False),
            due_date=getattr(generated_card, "due_date", None),
            url=getattr(generated_card, "url", None),
            created_at=getattr(generated_card, "created_at", None),
        )
    """Represents a Trello card within a list."""

    id: str
    name: str
    list_id: str
    board_id: str
    description: str | None = None
    position: float = 0.0
    closed: bool = False
    due_date: datetime | None = None
    url: str | None = None
    created_at: datetime | None = None


class TrelloUser(BaseModel):
    @classmethod
    def from_generated(cls, generated_user: object) -> TrelloUser:
        """Convert from generated client user model to TrelloUser."""
        return cls(
            id=getattr(generated_user, "id", ""),
            username=getattr(generated_user, "username", ""),
            full_name=getattr(generated_user, "full_name", None),
            email=getattr(generated_user, "email", None),
        )
    """Represents a Trello user."""

    id: str
    username: str
    full_name: str | None = None
    email: str | None = None
