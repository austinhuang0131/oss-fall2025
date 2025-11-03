"""Data models for Trello entities."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003

from pydantic import BaseModel


class TrelloBoard(BaseModel):
    """Represents a Trello board."""

    id: str
    name: str
    description: str | None = None
    closed: bool = False
    url: str | None = None
    created_at: datetime | None = None


class TrelloList(BaseModel):
    """Represents a Trello list within a board."""

    id: str
    name: str
    board_id: str
    position: float
    closed: bool = False


class TrelloCard(BaseModel):
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
    """Represents a Trello user."""

    id: str
    username: str
    full_name: str | None = None
    email: str | None = None
