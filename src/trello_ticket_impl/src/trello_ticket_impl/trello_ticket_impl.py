"""Concrete implementation of the Ticket API for Trello backend."""

from __future__ import annotations

import asyncio
import concurrent.futures
from http import HTTPStatus
from typing import TYPE_CHECKING, Any, TypeVar

import aiohttp
from tickets_api.src.tickets_api import TicketInterface, TicketStatus
from trello_client_impl.oauth import TrelloOAuthHandler

from .exceptions import (
    TrelloAPIError,
    TrelloAuthenticationError,
    TrelloNotFoundError,
)
from .models import TrelloTicket

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from tickets_api.src.tickets_api import Ticket

T = TypeVar("T")


def _run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine, using existing loop if available."""
    try:
        _ = asyncio.get_running_loop()
    except RuntimeError:
        # No loop running, use asyncio.run
        return asyncio.run(coro)
    else:
        # Loop is running, create a task and wait for it
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()


class TrelloTicketClientImpl(TicketInterface):
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
        board_id: str | None = None,
    ) -> None:
        """Initialize Trello Ticket client implementation.

        Args:
            token: Trello API token
            oauth_handler: OAuth handler for authentication
            board_id: Trello board ID to use for tickets. If not provided, a new board will be created.

        """
        self.token = token or ""
        self.oauth_handler = oauth_handler or TrelloOAuthHandler.from_env()
        self.base_url = "https://api.trello.com/1"

        # Internal configuration - these are NOT exposed in the public API
        self._board_id: str | None = board_id
        self._todo_list_id: str | None = None  # Lazily initialized
        self._in_progress_list_id: str | None = None  # Lazily initialized
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
            raise TrelloAuthenticationError(msg)

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
                raise TrelloAuthenticationError(msg)
            if response.status == HTTPStatus.NOT_FOUND:
                msg = "Resource not found"
                raise TrelloNotFoundError(msg)
            if response.status >= HTTPStatus.BAD_REQUEST:
                text = await response.text()
                msg = f"API error: {text}"
                raise TrelloAPIError(msg, response.status)

            return await response.json()  # type: ignore[no-any-return]

    async def _ensure_lists_initialized(self) -> None:
        """Ensure the To Do and Done lists are initialized.

        This method is called internally before any ticket operations.
        It finds or creates the required lists on the configured board.
        If no board is configured, creates a new board first.

        Raises:
            TicketAPIError: If lists cannot be created

        """
        if self._board_id and self._todo_list_id and self._done_list_id and self._in_progress_list_id:
            return  # Already initialized

        # Create a new board if one wasn't provided
        if not self._board_id:
            board_data = await self._make_request("POST", "/boards", {"name": "Ticket Board"})
            if not isinstance(board_data, dict):
                msg = "Failed to create new board"
                raise TrelloAPIError(msg)
            self._board_id = board_data["id"]

        # Get all lists on the board
        data = await self._make_request("GET", f"/boards/{self._board_id}/lists")

        if not isinstance(data, list):
            msg = "API did not return a list of lists."
            raise TrelloAPIError(msg)

        initial_lists = zip(
            ["_todo_list_id", "_done_list_id", "_in_progress_list_id"],
            ["To Do", "Done", "In Progress"], strict=True,
        )

        # Create To Do list if it doesn't exist
        for list_id_attr, list_name in initial_lists:
            for existing_list in data:
                if existing_list["name"] == list_name:
                    setattr(self, list_id_attr, existing_list["id"])
            if not getattr(self, list_id_attr):
                params: dict[str, str] = {"name": list_name, "idBoard": self._board_id}
                list_data = await self._make_request("POST", "/lists", params=params)
                if not isinstance(list_data, dict):
                    msg = f"Failed to create {list_name} list"
                    raise TrelloAPIError(msg)
                setattr(self, list_id_attr, list_data["id"])

    def _status_to_list(self, status: TicketStatus) -> str:
        """Map ticket status to Trello list ID."""
        to_return: str | None = None
        match status:
            case TicketStatus.OPEN:
                to_return = self._todo_list_id
            case TicketStatus.IN_PROGRESS:
                to_return = self._in_progress_list_id
            case TicketStatus.CLOSED:
                to_return = self._done_list_id
        if to_return is None:
            msg = "Trello lists are not initialized."
            raise ValueError(msg)
        return to_return

    def _list_to_status(self, list_id: str) -> TicketStatus | None:
        """Map Trello list ID to ticket status."""
        if list_id == self._todo_list_id:
            return TicketStatus.OPEN
        if list_id == self._in_progress_list_id:
            return TicketStatus.IN_PROGRESS
        if list_id == self._done_list_id:
            return TicketStatus.CLOSED
        return None

    def create_ticket(self, title: str, description: str, assignee: str | None = None) -> Ticket:
        """Create a new ticket.

        Args:
            title: The title of the ticket
            description: The description of the ticket
            assignee: The assignee of the ticket

        Returns:
            Ticket: The created ticket

        Raises:
            TicketAPIError: If the API request fails
            TicketAuthenticationError: If authentication fails

        """
        return _run_async(self._create_ticket_async(title, description, assignee))

    async def _create_ticket_async(self, title: str, description: str, assignee: str | None) -> Ticket:
        """Async implementation of create_ticket."""
        await self._ensure_lists_initialized()

        # Create card in the To Do list (status = False)
        params: dict[str, str] = {
            "name": title,
            "desc": description,
            "idList": self._todo_list_id or "",
            "idMembers": assignee or "",
        }

        data = await self._make_request("POST", "/cards", params=params)
        if not isinstance(data, dict):
            msg = "API did not return a dict for the new card."
            raise TrelloAPIError(msg)

        return TrelloTicket(
            ticket_id=data["id"],
            title=data["name"],
            description=data.get("desc", ""),
            status=TicketStatus.OPEN,  # New tickets are always open
            assignee=data.get("idMembers", [])[0] if data.get("idMembers") else None, # only FIRST assignee
        )

    def update_ticket(
        self,
        ticket_id: str,
        status: TicketStatus | None = None,
        title: str | None = None,
        description: str | None = None,
        assignee: str | None = None,
    ) -> Ticket:
        """Update an existing ticket.

        Args:
            ticket_id: The ID of the ticket to update
            title: New title for the ticket
            status: New status for the ticket
            description: New description for the ticket
            assignee: New assignee for the ticket (OVERRIDES existing, since only ONE assignee per ticket)

        Returns:
            Ticket: The updated ticket

        Raises:
            TicketNotFoundError: If the ticket doesn't exist
            TicketAPIError: If the API request fails
            TicketAuthenticationError: If authentication fails

        """
        return _run_async(
            self._update_ticket_async(ticket_id, title, description, status, assignee),
        )

    async def _update_ticket_async(
        self,
        ticket_id: str,
        title: str | None,
        description: str | None,
        status: TicketStatus | None,
        assignee: str | None = None,
    ) -> Ticket:
        """Actual async implementation of update_ticket."""
        await self._ensure_lists_initialized()

        params: dict[str, str] = {}

        if title:
            params["name"] = title
        if description:
            params["desc"] = description
        if assignee is not None:
            params["idMembers"] = assignee
        if status:
            target_list_id = self._status_to_list(status)
            params["idList"] = target_list_id

        if params == {}:
            msg = "No fields to update were provided."
            raise TrelloAPIError(msg)

        data = await self._make_request("PUT", f"/cards/{ticket_id}", params=params)
        if not isinstance(data, dict):
            msg = f"API did not return a dict for card {ticket_id}."
            raise TrelloAPIError(msg)

        current_status = self._list_to_status(data["idList"])
        if current_status is None:
            msg = f"Card {ticket_id} has been edited, but it is in another list and thus its status cannot be determined."
            raise TrelloAPIError(msg)

        return TrelloTicket(
            ticket_id=data["id"],
            title=data["name"],
            description=data.get("desc", ""),
            status=current_status,
            assignee=data.get("idMembers", [])[0] if data.get("idMembers") else None, # only FIRST assignee
        )

    def delete_ticket(self, ticket_id: str) -> bool:
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
        async def _delete_async() -> bool:
            try:
                _ = await self._make_request("DELETE", f"/cards/{ticket_id}")
            except TrelloAPIError:
                return False
            else:
                return True

        return _run_async(_delete_async())

    def get_ticket(self, ticket_id: str) -> Ticket:
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
        return _run_async(self._get_ticket_async(ticket_id))

    async def _get_ticket_async(self, ticket_id: str) -> Ticket:
        """Actual async implementation of get_ticket."""
        await self._ensure_lists_initialized()

        data = await self._make_request("GET", f"/cards/{ticket_id}")
        if not isinstance(data, dict):
            msg = f"API did not return a dict for card {ticket_id}."
            raise TrelloAPIError(msg)

        # Determine status based on which list the card is in
        card_list_id = data["idList"]
        status = self._list_to_status(card_list_id)

        if status is None:
            msg = f"Card {ticket_id} is in another list and thus its status cannot be determined."
            raise TrelloAPIError(msg)

        return TrelloTicket(
            ticket_id=data["id"],
            title=data["name"],
            description=data.get("desc", ""),
            status=status,
            assignee=data.get("idMembers", [])[0] if data.get("idMembers") else None, # only FIRST assignee
        )

    def search_tickets(self, query: str | None = None, status: TicketStatus | None = None) -> list[Ticket]:
        """Search for tickets based on query and/or status.

        Args:
            query: Search query to filter tickets by title or description
            status: Filter by ticket status (False = Open, True = Done)

        Returns:
            list[Ticket]: List of tickets matching the search criteria

        Raises:
            TicketAPIError: If the API request fails
            TicketAuthenticationError: If authentication fails

        """
        if query:
            return _run_async(self._search_tickets_async(query, status))
        return _run_async(self._list_all_cards_async(status))

    async def _search_tickets_async(self, query: str, status: TicketStatus | None = None) -> list[Ticket]:
        """Async implementation of search_tickets."""
        await self._ensure_lists_initialized()

        params = {
            "query": query,
            "id_boards": self._board_id or "",
            "model_types": "cards",
            "cards_limit": "1000",
        }

        # Get all cards on the board
        data = await self._make_request("GET", "/search", params)

        if not isinstance(data, dict):
            msg = "API did not return a dict for search."
            raise TrelloAPIError(msg)

        cards = data.get("cards", [])
        if not isinstance(cards, list):
            msg = "API did not return a list of cards."
            raise TrelloAPIError(msg)

        tickets: list[Ticket] = []
        list_id = self._status_to_list(status) if status else None
        for card_data in cards:

            # Apply status filter
            if list_id is not None and card_data["idList"] != list_id:
                continue

            card_status = self._list_to_status(card_data["idList"])
            if card_status is None:
                continue

            tickets.append(
                TrelloTicket(
                    ticket_id=card_data["id"],
                    title=card_data["name"],
                    description=card_data.get("desc", ""),
                    status=card_status,
                    assignee=card_data.get("idMembers", [])[0] if card_data.get("idMembers") else None, # only FIRST assignee
                ),
            )
        return tickets

    async def _list_all_cards_async(self, status: TicketStatus | None = None) -> list[Ticket]:
        """Async implementation to list all cards, optionally filtered by status."""
        await self._ensure_lists_initialized()

        data = await self._make_request(
            "GET",
            f"/lists/{self._status_to_list(status)}/cards" if status else f"/boards/{self._board_id}/cards",
        )

        if not isinstance(data, list):
            msg = "API did not return a list of cards."
            raise TrelloAPIError(msg)
        tickets: list[Ticket] = []
        for card_data in data:
            card_status = self._list_to_status(card_data["idList"])
            if card_status is None:
                continue

            tickets.append(
                TrelloTicket(
                    ticket_id=card_data["id"],
                    title=card_data["name"],
                    description=card_data.get("desc", ""),
                    status=card_status,
                    assignee=card_data.get("idMembers", [])[0] if card_data.get("idMembers") else None, # only FIRST assignee
                ),
            )
        return tickets
