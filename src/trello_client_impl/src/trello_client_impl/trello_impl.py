"""Concrete implementation of the Trello client API."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from http import HTTPStatus
from typing import Any

import aiohttp
import asyncpg
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

from .database import CREATE_CREDENTIALS_TABLE
from .oauth import TrelloOAuthHandler


class TrelloClientImpl(TrelloClient):
    """Concrete implementation of the Trello client API."""

    def __init__(
        self,
        db_url: str,
        oauth_handler: TrelloOAuthHandler | None = None,
        user_id: str | None = None,
    ) -> None:
        """Initialize Trello client implementation.

        Args:
            db_url: PostgreSQL database connection URL
            oauth_handler: OAuth handler for authentication
            user_id: User ID for credential lookup

        """
        self.db_url = db_url
        self.oauth_handler = oauth_handler or TrelloOAuthHandler.from_env()
        self.user_id = user_id
        self._db_pool: asyncpg.Pool | None = None
        self.base_url = "https://api.trello.com/1"

    async def _ensure_db_pool(self) -> asyncpg.Pool:
        """Ensure database connection pool is initialized."""
        if self._db_pool is None:
            self._db_pool = await asyncpg.create_pool(self.db_url)
            # Create tables if they don't exist
            async with self._db_pool.acquire() as conn:
                await conn.execute(CREATE_CREDENTIALS_TABLE)
        return self._db_pool

    async def _get_credentials(self) -> tuple[str, str]:
        """Get user credentials from database.

        Returns:
            Tuple[str, str]: Access token and token secret

        Raises:
            TrelloAuthenticationError: If no credentials found

        """
        if not self.user_id:
            msg = "No user ID provided"
            raise TrelloAuthenticationError(msg)

        pool = await self._ensure_db_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT access_token, token_secret FROM user_credentials WHERE user_id = $1",
                self.user_id,
            )

            if not row:
                msg = f"No credentials found for user {self.user_id}"
                raise TrelloAuthenticationError(msg)

            return row["access_token"], row["token_secret"]

    async def store_credentials(
        self,
        user_id: str,
        access_token: str,
        token_secret: str,
    ) -> None:
        """Store user credentials in database.

        Args:
            user_id: User identifier
            access_token: OAuth access token
            token_secret: OAuth token secret

        """
        pool = await self._ensure_db_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_credentials (user_id, access_token, token_secret, updated_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    access_token = EXCLUDED.access_token,
                    token_secret = EXCLUDED.token_secret,
                    updated_at = EXCLUDED.updated_at
                """,
                user_id, access_token, token_secret, datetime.now(UTC),
            )

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, str] | None = None, #SJ
        json_data: dict[str, Any] | None = None,
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
        access_token, _ = await self._get_credentials()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Add authentication parameters
        if params is None:
            params = {}
        params.update({
            "key": self.oauth_handler.api_key,
            "token": access_token,
        })

        async with aiohttp.ClientSession() as session:

            '''#SJ
            kwargs = {"params": params}
            if json_data:
                kwargs["json"] = json_data
            '''

            async with session.request(method, url, params=params, json=json_data) as response: #SJ 
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

                result = await response.json()
                assert isinstance(result, (dict, list)), "Expected dict or list from API"
                return result

    # User operations
    async def get_current_user(self) -> TrelloUser:
        """Get the current authenticated user."""
        data = await self._make_request("GET", "/members/me")
        assert isinstance(data, dict), "Expected dict response from user endpoint" #SJ

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
        assert isinstance(data, list), "Expected list response from boards endpoint" #SJ

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
        assert isinstance(data, dict), "Expected dict response from board endpoint" #SJ

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
        assert isinstance(data, dict), "Expected dict response from board endpoint" #SJ

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
        assert isinstance(data, dict), "Expected dict response from board endpoint" #SJ

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
        assert isinstance(data, list), "Expected list response from lists endpoint" #SJ

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
        assert isinstance(data, dict), "Expected dict response from list endpoint" #SJ

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
        assert isinstance(data, dict), "Expected dict response from list endpoint" #SJ

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
        assert isinstance(data, list), "Expected list response from cards endpoint" #SJ

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
        assert isinstance(data, dict), "Expected dict response from card endpoint" #SJ

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
        assert isinstance(data, dict), "Expected dict response from card endpoint" #SJ

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
        assert isinstance(data, dict), "Expected dict response from card endpoint" #SJ

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
        """Close database connections."""
        if self._db_pool:
            await self._db_pool.close()

    @classmethod
    def from_env(cls, user_id: str | None = None) -> TrelloClientImpl:
        """Create client from environment variables.

        Args:
            user_id: User ID for credential lookup

        Returns:
            TrelloClientImpl: Configured client instance

        """
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            msg = "DATABASE_URL environment variable is required"
            raise ValueError(msg)

        return cls(db_url=db_url, user_id=user_id)
