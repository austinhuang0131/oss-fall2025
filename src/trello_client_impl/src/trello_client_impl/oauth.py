"""OAuth 2.0 authentication handler for Trello API."""

from __future__ import annotations

import os
import urllib.parse
from http import HTTPStatus

import aiohttp
from kanban_client_api.exceptions import KanbanAuthenticationError


class TrelloOAuthHandler:
    """Handles OAuth 2.0 flow for Trello API authentication."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        redirect_uri: str,
    ) -> None:
        """Initialize OAuth handler.

        Args:
            api_key: Trello API key
            api_secret: Trello API secret
            redirect_uri: OAuth callback URL

        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_uri = redirect_uri
        self.base_url = "https://trello.com/1"

    def get_authorization_url(self, state: str | None = None) -> str:
        """Get the authorization URL for OAuth flow with CSRF protection.

        Returns:
            str: Authorization URL to redirect user to

        """
        params = {
            "key": self.api_key,
            "name": "Trello Client Service",
            "expiration": "never",
            "response_type": "token",
            "scope": "read,write",
            "return_url": f"{self.redirect_uri}?state={state}",
            "state": state,
        }

        query_string = urllib.parse.urlencode(params)
        return f"https://trello.com/1/authorize?{query_string}"

    async def exchange_token(self, token: str) -> str:
        """Exchange authorization token for access credentials.

        Args:
            token: Authorization token from callback

        Returns:
            str: Access token

        Raises:
            TrelloAuthenticationError: If token exchange fails

        """
        # For Trello, the token from the callback IS the access token
        # Trello uses a simpler OAuth 1.0a-like flow
        if not token:
            msg = "No token provided"
            raise KanbanAuthenticationError(msg)

        # Validate the token by making a test API call
        async with aiohttp.ClientSession() as session:
            test_url = f"{self.base_url}/members/me"
            params = {"key": self.api_key, "token": token}

            async with session.get(test_url, params=params) as response:
                if response.status != HTTPStatus.OK:
                    msg = f"Token validation failed: {response.status}"
                    raise KanbanAuthenticationError(
                        msg,
                    )

        # For Trello, we use the token as both access_token and token_secret
        return token

    @classmethod
    def from_env(cls) -> TrelloOAuthHandler:
        """Create OAuth handler from environment variables.

        Returns:
            TrelloOAuthHandler: Configured OAuth handler

        Raises:
            ValueError: If required environment variables are missing

        """
        api_key = os.getenv("TRELLO_API_KEY")
        api_secret = os.getenv("TRELLO_API_SECRET")
        redirect_uri = os.getenv("REDIRECT_URI")

        if not api_key:
            msg = "TRELLO_API_KEY environment variable is required"
            raise ValueError(msg)
        if not api_secret:
            msg = "TRELLO_API_SECRET environment variable is required"
            raise ValueError(msg)
        if not redirect_uri:
            msg = "REDIRECT_URI environment variable is required"
            raise ValueError(msg)

        return cls(api_key, api_secret, redirect_uri)
