"""Tests for TrelloOAuthHandler."""

import os

import pytest

from trello_client_api import TrelloAuthenticationError
from trello_client_impl.oauth import TrelloOAuthHandler


class TestTrelloOAuthHandler:
    """Unit tests for OAuth handler."""

    def test_get_authorization_url_contains_required_params(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Authorization URL should include key, response_type and return_url."""
        handler = TrelloOAuthHandler(api_key="k", api_secret="s", redirect_uri="http://localhost/callback")
        url = handler.get_authorization_url()
        assert "key=k" in url
        assert "response_type=token" in url
        assert "return_url=http%3A%2F%2Flocalhost%2Fcallback" in url

    async def test_exchange_token_without_token_raises(self) -> None:
        """Calling exchange_token with empty token should raise auth error."""
        handler = TrelloOAuthHandler(api_key="k", api_secret="s", redirect_uri="http://localhost/callback")
        with pytest.raises(TrelloAuthenticationError, match="No token provided"):
            await handler.exchange_token("")

    def test_from_env_validates_presence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """from_env should validate environment variables and construct on success."""
        # Ensure clean env
        for key in ("TRELLO_API_KEY", "TRELLO_API_SECRET", "REDIRECT_URI"):
            monkeypatch.delenv(key, raising=False)
        # Missing vars -> ValueError
        with pytest.raises(ValueError):
            TrelloOAuthHandler.from_env()

        monkeypatch.setenv("TRELLO_API_KEY", "k")
        with pytest.raises(ValueError):
            TrelloOAuthHandler.from_env()

        monkeypatch.setenv("TRELLO_API_SECRET", "s")
        with pytest.raises(ValueError):
            TrelloOAuthHandler.from_env()

        monkeypatch.setenv("REDIRECT_URI", "http://localhost/callback")
        h = TrelloOAuthHandler.from_env()
        assert isinstance(h, TrelloOAuthHandler)
