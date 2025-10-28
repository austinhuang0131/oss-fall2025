"""Data models for Trello entities."""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class TrelloBoard:
    """Represents a Trello board."""
    
    id: str
    name: str
    description: Optional[str] = None
    closed: bool = False
    url: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class TrelloList:
    """Represents a Trello list within a board."""
    
    id: str
    name: str
    board_id: str
    position: float
    closed: bool = False


@dataclass(frozen=True)
class TrelloCard:
    """Represents a Trello card within a list."""
    
    id: str
    name: str
    list_id: str
    board_id: str
    description: Optional[str] = None
    position: float = 0.0
    closed: bool = False
    due_date: Optional[datetime] = None
    url: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class TrelloUser:
    """Represents a Trello user."""
    
    id: str
    username: str
    full_name: Optional[str] = None
    email: Optional[str] = None
