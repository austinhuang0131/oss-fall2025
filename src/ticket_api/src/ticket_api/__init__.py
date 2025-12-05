"""Ticket API - Abstract interface for ticket management systems."""

from __future__ import annotations

from .client import TicketClient, get_client
from .exceptions import TicketAPIError, TicketAuthenticationError, TicketNotFoundError
from .models import Ticket

__all__ = [
    "Ticket",
    "TicketAPIError",
    "TicketAuthenticationError",
    "TicketClient",
    "TicketNotFoundError",
    "get_client",
]
