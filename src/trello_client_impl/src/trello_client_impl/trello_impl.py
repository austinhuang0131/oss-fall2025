"""Concrete implementation of the Trello client API."""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

import aiohttp
from trello_client_api import (
    TrelloAPIError,
    TrelloAuthenticationError,
    TrelloBoard,
    TrelloCard,
    TrelloClient,
    TrelloList,
    TrelloNotFoundError,
    TrelloUser,
)

from .oauth import TrelloOAuthHandler


class TrelloClientImpl(TrelloClient):
    """Concrete implementation of the Trello client API."""

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
        json_data: dict | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make authenticated request to Trello API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON request body

        Returns:
            dict: API response data

        Raises:
            TrelloAPIError: If the API request fails
            TrelloAuthenticationError: If authentication fails

        """
        if not self.token:
            raise TrelloAuthenticationError("No token provided")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Add authentication parameters
        if params is None:
            params = {}
        params.update({
            "key": self.oauth_handler.api_key,
            "token": self.token,
        })

        async with aiohttp.ClientSession() as session:
            kwargs = {"params": params}
            if json_data:
                kwargs["json"] = json_data

            async with session.request(method, url, **kwargs) as response:
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

                return await response.json()

    # User operations
    async def get_current_user(self) -> TrelloUser:
        """Get the current authenticated user."""
        data = await self._make_request("GET", "/members/me")
        return TrelloUser(
            id=data["id"],
            username=data["username"],
            full_name=data.get("fullName"),
            email=data.get("email"),
        )

    # Board operations
    async def get_boards(self) -> list[TrelloBoard]:
        """Get all boards accessible to the current user."""
        data = await self._make_request("GET", "/members/me/boards")

        boards = []
        for board_data in data:
            board = TrelloBoard(
                id=board_data["id"],
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

        return TrelloBoard(
            id=data["id"],
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

        return TrelloBoard(
            id=data["id"],
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

        return TrelloBoard(
            id=data["id"],
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
    async def get_lists(self, board_id: str) -> list[TrelloList]:
        """Get all lists in a board."""
        data = await self._make_request("GET", f"/boards/{board_id}/lists")

        lists = []
        for list_data in data:
            trello_list = TrelloList(
                id=list_data["id"],
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

        return TrelloList(
            id=data["id"],
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

        return TrelloList(
            id=data["id"],
            name=data["name"],
            board_id=data["idBoard"],
            position=data.get("pos", 0.0),
            closed=data.get("closed", False),
        )

    # Card operations
    async def get_cards(self, list_id: str) -> list[TrelloCard]:
        """Get all cards in a list."""
        data = await self._make_request("GET", f"/lists/{list_id}/cards")

        cards = []
        for card_data in data:
            card = TrelloCard(
                id=card_data["id"],
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

        return TrelloCard(
            id=data["id"],
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

        return TrelloCard(
            id=data["id"],
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

        return TrelloCard(
            id=data["id"],
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
