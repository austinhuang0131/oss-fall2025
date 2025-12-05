"""Trello Ticket Implementation - Concrete implementation of Ticket API for Trello."""

from __future__ import annotations

from .models import TrelloTicket
from .trello_ticket_impl import TrelloTicketClientImpl, get_client_impl, register

__all__ = [
    "TrelloTicket",
    "TrelloTicketClientImpl",
    "get_client_impl",
    "register",
]

# Auto-register when imported
register()
