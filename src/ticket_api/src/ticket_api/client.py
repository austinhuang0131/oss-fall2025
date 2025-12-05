"""Abstract Ticket client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Ticket


class TicketClient(ABC):
    """Abstract interface for Ticket client operations."""

    @abstractmethod
    async def create_ticket(self, title: str, description: str) -> Ticket:
        """Create a new ticket.

        Args:
            title: The title of the ticket
            description: The description of the ticket

        Returns:
            Ticket: The created ticket

        Raises:
            TicketAPIError: If the API request fails
            TicketAuthenticationError: If authentication fails

        """

    @abstractmethod
    async def update_ticket(
        self,
        ticket_id: str,
        title: str,
        description: str,
        status: bool,
    ) -> Ticket:
        """Update an existing ticket.

        Args:
            ticket_id: The ID of the ticket to update
            title: New title for the ticket
            description: New description for the ticket
            status: New status for the ticket (False = Open, True = Done)

        Returns:
            Ticket: The updated ticket

        Raises:
            TicketNotFoundError: If the ticket doesn't exist
            TicketAPIError: If the API request fails
            TicketAuthenticationError: If authentication fails

        """

    @abstractmethod
    async def delete_ticket(self, ticket_id: str) -> bool:
        """Delete a ticket.

        Args:
            ticket_id: The ID of the ticket to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            TicketNotFoundError: If the ticket doesn't exist
            TicketAPIError: If the API request fails
            TicketAuthenticationError: If authentication fails

        """

    @abstractmethod
    async def get_ticket(self, ticket_id: str) -> Ticket:
        """Get a specific ticket by ID.

        Args:
            ticket_id: The ID of the ticket to retrieve

        Returns:
            Ticket: The requested ticket

        Raises:
            TicketNotFoundError: If the ticket doesn't exist
            TicketAPIError: If the API request fails
            TicketAuthenticationError: If authentication fails

        """


def get_client(*, token: str | None = None) -> TicketClient:
    """Return an instance of a Ticket Client."""
    raise NotImplementedError
