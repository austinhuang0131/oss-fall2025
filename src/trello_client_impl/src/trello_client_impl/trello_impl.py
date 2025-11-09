"""Concrete implementation of the Trello client API."""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import aiohttp
from kanban_client_api.client import KanbanClient
from kanban_client_api.exceptions import (
    KanbanAPIError,
    KanbanAuthenticationError,
    KanbanNotFoundError,
)

from .models import TrelloBoard, TrelloCard, TrelloList, TrelloUser
from .oauth import TrelloOAuthHandler

if TYPE_CHECKING:
    from kanban_client_api.models import KanbanBoard, KanbanCard, KanbanList


class TrelloClientImpl(KanbanClient):
    """Concrete implementation of the Kanban client API for Trello."""

    def __init__(
        self,
        token: str | None = None,
        oauth_handler: TrelloOAuthHandler | None = None,
        db_url: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """Initialize Trello client implementation.

        Backward-compatibility: older callers passed ``db_url`` and ``user_id``
        when credentials were stored in a database. The current implementation
        no longer uses a database, but we still accept and store these optional
        parameters so existing code and tests keep working without modification.

        Args:
            token: Trello API token. Optional in tests where requests are mocked.
            oauth_handler: OAuth handler for authentication
            db_url: Deprecated, retained for compatibility only
            user_id: Optional identifier of the current user for callers that
                track user context externally

        """
        self.token = token or ""
        self.oauth_handler = oauth_handler or TrelloOAuthHandler.from_env()
        self.base_url = "https://api.trello.com/1"
        # Compatibility attributes (not used by runtime logic)
        self.db_url = db_url
        self.user_id = user_id


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
            dict: API response data

        Raises:
            KanbanAPIError: If the API request fails
            KanbanAuthenticationError: If authentication fails

        """
        if not self.token:
            msg = "No token provided"
            raise KanbanAuthenticationError(msg)

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
                raise KanbanAuthenticationError(msg)
            if response.status == HTTPStatus.NOT_FOUND:
                msg = "Resource not found"
                raise KanbanNotFoundError(msg)
            if response.status >= HTTPStatus.BAD_REQUEST:
                text = await response.text()
                msg = f"API error: {text}"
                raise KanbanAPIError(msg, response.status)

            return await response.json() # type: ignore[no-any-return]

    # User operations
    async def get_current_user(self) -> TrelloUser:
        """Get the current authenticated user."""
        data = await self._make_request("GET", "/members/me")
        if (not isinstance(data, dict)):
            msg = "API did not return a dict for current user."
            raise KanbanAPIError(msg)

        return TrelloUser(
            user_id=data["id"],
            username=data["username"],
            full_name=data.get("fullName"),
            email=data.get("email"),
        )

    # Board operations
    async def get_boards(self) -> list[KanbanBoard]:
        """Get all boards accessible to the current user."""
        data = await self._make_request("GET", "/members/me/boards")

        boards = []
        if (not isinstance(data, list)):
            msg = "API did not return a list of boards."
            raise KanbanAPIError(msg)
        for board_data in data:
            board: KanbanBoard = TrelloBoard(
                board_id=board_data["id"],
                name=board_data["name"],
                description=board_data.get("desc"),
                closed=board_data.get("closed", False),
                url=board_data.get("url"),
            )
            boards.append(board)

        return boards

    async def get_board(self, board_id: str) -> TrelloBoard:
        """Get a specific board by ID."""
        data = await self._make_request("GET", f"/boards/{board_id}")
        if (not isinstance(data, dict)):
            msg = f"API did not return a dict for board {board_id}."
            raise KanbanAPIError(msg)

        return TrelloBoard(
            board_id=data["id"],
            name=data["name"],
            description=data.get("desc"),
            closed=data.get("closed", False),
            url=data.get("url"),
        )

    async def create_board(
        self,
        name: str,
        description: str | None = None,
    ) -> TrelloBoard:
        """Create a new board."""
        params = {"name": name}
        if description:
            params["desc"] = description

        data = await self._make_request("POST", "/boards", params=params)
        if (not isinstance(data, dict)):
            msg = "API did not return a dict for new board."
            raise KanbanAPIError(msg)

        return TrelloBoard(
            board_id=data["id"],
            name=data["name"],
            description=data.get("desc"),
            closed=data.get("closed", False),
            url=data.get("url"),
        )

    async def update_board(
        self,
        board_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> TrelloBoard:
        """Update an existing board."""
        params = {}
        if name:
            params["name"] = name
        if description is not None:
            params["desc"] = description

        data = await self._make_request("PUT", f"/boards/{board_id}", params=params)
        if (not isinstance(data, dict)):
            msg = f"API did not return a dict for board {board_id}."
            raise KanbanAPIError(msg)

        return TrelloBoard(
            board_id=data["id"],
            name=data["name"],
            description=data.get("desc"),
            closed=data.get("closed", False),
            url=data.get("url"),
        )

    async def delete_board(self, board_id: str) -> bool:
        """Delete a board."""
        await self._make_request("DELETE", f"/boards/{board_id}")
        return True

    # List operations
    async def get_lists(self, board_id: str) -> list[KanbanList]:
        """Get all lists in a board."""
        data = await self._make_request("GET", f"/boards/{board_id}/lists")

        lists = []
        if (not isinstance(data, list)):
            msg = f"API did not return a dict for lists of board {board_id}."
            raise KanbanAPIError(msg)
        for list_data in data:
            trello_list: KanbanList = TrelloList(
                list_id=list_data["id"],
                name=list_data["name"],
                board_id=board_id,
                position=list_data.get("pos", 0.0),
                closed=list_data.get("closed", False),
            )
            lists.append(trello_list)

        return lists

    async def create_list(self, board_id: str, name: str) -> TrelloList:
        """Create a new list in a board."""
        params = {"name": name, "idBoard": board_id}
        data = await self._make_request("POST", "/lists", params=params)
        if (not isinstance(data, dict)):
            msg = "API did not return a dict for the new list."
            raise KanbanAPIError(msg)

        return TrelloList(
            list_id=data["id"],
            name=data["name"],
            board_id=board_id,
            position=data.get("pos", 0.0),
            closed=data.get("closed", False),
        )

    async def update_list(
        self,
        list_id: str,
        name: str | None = None,
    ) -> TrelloList:
        """Update an existing list."""
        params = {}
        if name:
            params["name"] = name

        data = await self._make_request("PUT", f"/lists/{list_id}", params=params)
        if (not isinstance(data, dict)):
            msg = f"API did not return a dict for list {list_id}."
            raise KanbanAPIError(msg)

        return TrelloList(
            list_id=data["id"],
            name=data["name"],
            board_id=data["idBoard"],
            position=data.get("pos", 0.0),
            closed=data.get("closed", False),
        )

    # Card operations
    async def get_cards(self, list_id: str) -> list[KanbanCard]:
        """Get all cards in a list."""
        data = await self._make_request("GET", f"/lists/{list_id}/cards")

        cards = []
        if (not isinstance(data, list)):
            msg = f"API did not return a list for cards of list {list_id}."
            raise KanbanAPIError(msg)

        for card_data in data:
            card: KanbanCard = TrelloCard(
                card_id=card_data["id"],
                name=card_data["name"],
                list_id=list_id,
                board_id=card_data["idBoard"],
                description=card_data.get("desc"),
                position=card_data.get("pos", 0.0),
                closed=card_data.get("closed", False),
                url=card_data.get("url"),
            )
            cards.append(card)

        return cards

    async def get_card(self, card_id: str) -> TrelloCard:
        """Get a specific card by ID."""
        data = await self._make_request("GET", f"/cards/{card_id}")
        if (not isinstance(data, dict)):
            msg = f"API did not return a dict for card {card_id}."
            raise KanbanAPIError(msg)

        return TrelloCard(
            card_id=data["id"],
            name=data["name"],
            list_id=data["idList"],
            board_id=data["idBoard"],
            description=data.get("desc"),
            position=data.get("pos", 0.0),
            closed=data.get("closed", False),
            url=data.get("url"),
        )

    async def create_card(
        self,
        list_id: str,
        name: str,
        description: str | None = None,
    ) -> TrelloCard:
        """Create a new card in a list."""
        params = {"name": name, "idList": list_id}
        if description:
            params["desc"] = description

        data = await self._make_request("POST", "/cards", params=params)
        if (not isinstance(data, dict)):
            msg = "API did not return a dict for the new card."
            raise KanbanAPIError(msg)

        return TrelloCard(
            card_id=data["id"],
            name=data["name"],
            list_id=list_id,
            board_id=data["idBoard"],
            description=data.get("desc"),
            position=data.get("pos", 0.0),
            closed=data.get("closed", False),
            url=data.get("url"),
        )

    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        description: str | None = None,
        list_id: str | None = None,
    ) -> TrelloCard:
        """Update an existing card."""
        params = {}
        if name:
            params["name"] = name
        if description is not None:
            params["desc"] = description
        if list_id:
            params["idList"] = list_id

        data = await self._make_request("PUT", f"/cards/{card_id}", params=params)
        if (not isinstance(data, dict)):
            msg = f"API did not return a dict for card {card_id}."
            raise KanbanAPIError(msg)

        return TrelloCard(
            card_id=data["id"],
            name=data["name"],
            list_id=data["idList"],
            board_id=data["idBoard"],
            description=data.get("desc"),
            position=data.get("pos", 0.0),
            closed=data.get("closed", False),
            url=data.get("url"),
        )

    async def delete_card(self, card_id: str) -> bool:
        """Delete a card."""
        await self._make_request("DELETE", f"/cards/{card_id}")
        return True

    async def close(self) -> None:
        """Close client (no-op)."""

    @classmethod
    def from_env(cls, token: str) -> TrelloClientImpl:
        """Create client from environment variables and token.

        Args:
            token: Trello API token

        Returns:
            TrelloClientImpl: Configured client instance

        """
        return cls(token=token)
