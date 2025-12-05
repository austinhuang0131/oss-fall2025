"""Concrete implementation of the Ticket API for Trello backend."""

from __future__ import annotations

import os
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp
from ticket_api.client import TicketClient
from ticket_api.exceptions import (
    TicketAPIError,
    TicketAuthenticationError,
    TicketNotFoundError,
)
from trello_client_impl.oauth import TrelloOAuthHandler

import ticket_api

from .models import TrelloTicket

if TYPE_CHECKING:
    from ticket_api.models import Ticket


class TrelloTicketClientImpl(TicketClient):
    """Concrete implementation of the Ticket API using Trello as backend.

    This implementation uses:
    - ONE Trello board (configured via environment)
    - TWO Trello lists: "To Do" (for open tickets) and "Done" (for completed tickets)
    - Trello cards map to tickets
    - Card movement between lists represents status changes
    """

    def __init__(
        self,
        token: str | None = None,
        oauth_handler: TrelloOAuthHandler | None = None,
    ) -> None:
        """Initialize Trello Ticket client implementation.

        Args:
            token: Trello API token
            oauth_handler: OAuth handler for authentication

        """
        self.token = token or ""
        self.oauth_handler = oauth_handler or TrelloOAuthHandler.from_env()
        self.base_url = "https://api.trello.com/1"

        # Internal configuration - these are NOT exposed in the public API
        self._board_id: str | None = os.getenv("TRELLO_BOARD_ID")
        self._todo_list_id: str | None = None  # Lazily initialized
        self._done_list_id: str | None = None  # Lazily initialized

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[dict[str, Any]]:
        """Make authenticated request to Trello API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters

        Returns:
            API response data

        Raises:
            TicketAPIError: If the API request fails
            TicketAuthenticationError: If authentication fails

        """
        if not self.token:
            msg = "No token provided"
            raise TicketAuthenticationError(msg)

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Add authentication parameters
        if params is None:
            params = {}
        params.update({
            "key": self.oauth_handler.api_key,
            "token": self.token,
        })

        async with aiohttp.ClientSession() as session, session.request(method, url, params=params) as response:
            if response.status == HTTPStatus.UNAUTHORIZED:
                msg = "Authentication failed"
                raise TicketAuthenticationError(msg)
            if response.status == HTTPStatus.NOT_FOUND:
                msg = "Resource not found"
                raise TicketNotFoundError(msg)
            if response.status >= HTTPStatus.BAD_REQUEST:
                text = await response.text()
                msg = f"API error: {text}"
                raise TicketAPIError(msg, response.status)

            return await response.json()  # type: ignore[no-any-return]

    async def _ensure_lists_initialized(self) -> None:
        """Ensure the To Do and Done lists are initialized.

        This method is called internally before any ticket operations.
        It finds or creates the required lists on the configured board.

        Raises:
            TicketAPIError: If board is not configured or lists cannot be created

        """
        if self._todo_list_id and self._done_list_id:
            return  # Already initialized

        if not self._board_id:
            msg = "TRELLO_BOARD_ID environment variable is required"
            raise TicketAPIError(msg)

        # Get all lists on the board
        data = await self._make_request("GET", f"/boards/{self._board_id}/lists")

        if not isinstance(data, list):
            msg = "API did not return a list of lists."
            raise TicketAPIError(msg)

        # Find or create To Do and Done lists
        for list_data in data:
            if list_data["name"] == "To Do":
                self._todo_list_id = list_data["id"]
            elif list_data["name"] == "Done":
                self._done_list_id = list_data["id"]

        # Create To Do list if it doesn't exist
        if not self._todo_list_id:
            params = {"name": "To Do", "idBoard": self._board_id}
            data = await self._make_request("POST", "/lists", params=params)
            if not isinstance(data, dict):
                msg = "Failed to create To Do list"
                raise TicketAPIError(msg)
            self._todo_list_id = data["id"]

        # Create Done list if it doesn't exist
        if not self._done_list_id:
            params = {"name": "Done", "idBoard": self._board_id}
            data = await self._make_request("POST", "/lists", params=params)
            if not isinstance(data, dict):
                msg = "Failed to create Done list"
                raise TicketAPIError(msg)
            self._done_list_id = data["id"]

    async def create_ticket(self, title: str, description: str) -> Ticket:
        """Create a new ticket.

        Args:
            title: The title of the ticket
            description: The description of the ticket

        Returns:
            Ticket: The created ticket (status = False / Open by default)

        Raises:
            TicketAPIError: If the API request fails
            TicketAuthenticationError: If authentication fails

        """
        await self._ensure_lists_initialized()

        # Create card in the To Do list (status = False)
        params: dict[str, str] = {
            "name": title,
            "desc": description,
            "idList": self._todo_list_id or "",
        }

        data = await self._make_request("POST", "/cards", params=params)
        if not isinstance(data, dict):
            msg = "API did not return a dict for the new card."
            raise TicketAPIError(msg)

        return TrelloTicket(
            ticket_id=data["id"],
            title=data["name"],
            description=data.get("desc", ""),
            status=False,  # New tickets are always open
        )

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
        await self._ensure_lists_initialized()

        # Determine which list the card should be in based on status
        target_list_id = self._done_list_id if status else self._todo_list_id

        params: dict[str, str] = {
            "name": title,
            "desc": description,
            "idList": target_list_id or "",
        }

        data = await self._make_request("PUT", f"/cards/{ticket_id}", params=params)
        if not isinstance(data, dict):
            msg = f"API did not return a dict for card {ticket_id}."
            raise TicketAPIError(msg)

        return TrelloTicket(
            ticket_id=data["id"],
            title=data["name"],
            description=data.get("desc", ""),
            status=status,
        )

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
        await self._make_request("DELETE", f"/cards/{ticket_id}")
        return True

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
        await self._ensure_lists_initialized()

        data = await self._make_request("GET", f"/cards/{ticket_id}")
        if not isinstance(data, dict):
            msg = f"API did not return a dict for card {ticket_id}."
            raise TicketAPIError(msg)

        # Determine status based on which list the card is in
        card_list_id = data["idList"]
        status = card_list_id == self._done_list_id

        return TrelloTicket(
            ticket_id=data["id"],
            title=data["name"],
            description=data.get("desc", ""),
            status=status,
        )


def get_client_impl(*, token: str | None = None) -> TicketClient:
    """Return a configured :class:`TrelloTicketClientImpl` instance."""
    return TrelloTicketClientImpl(token)


def register() -> None:
    """Register the Trello ticket implementation with the Ticket API."""
    ticket_api.get_client = get_client_impl
