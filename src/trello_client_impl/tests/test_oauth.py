"""Tests for TrelloOAuthHandler."""

import pytest
from kanban_client_api.exceptions import KanbanAuthenticationError

from trello_client_impl.oauth import TrelloOAuthHandler


class TestTrelloOAuthHandler:
    """Unit tests for OAuth handler."""

    def test_generate_state_returns_non_empty_string(self) -> None:
        """Generate state should return a non-empty random string."""
        state = TrelloOAuthHandler.generate_state()
        assert isinstance(state, str)
        assert len(state) > 0

    def test_generate_state_returns_different_values(self) -> None:
        """Each call to generate_state should return a different value."""
        state1 = TrelloOAuthHandler.generate_state()
        state2 = TrelloOAuthHandler.generate_state()
        assert state1 != state2

    def test_get_authorization_url_contains_required_params(self) -> None:
        """Authorization URL should include key, response_type and return_url."""
        handler = TrelloOAuthHandler(api_key="k", api_secret="s", redirect_uri="http://localhost/callback")
        url = handler.get_authorization_url()
        assert "key=k" in url
        assert "response_type=token" in url
        assert "return_url=http%3A%2F%2Flocalhost%2Fcallback" in url

    async def test_exchange_token_without_token_raises(self) -> None:
        """Calling exchange_token with empty token should raise auth error."""
        handler = TrelloOAuthHandler(api_key="k", api_secret="s", redirect_uri="http://localhost/callback")
        with pytest.raises(KanbanAuthenticationError, match="No token provided"):
            await handler.exchange_token("")

    async def test_exchange_token_success_path_is_validated(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Successful token validation should return the token itself."""
        handler = TrelloOAuthHandler(api_key="k", api_secret="s", redirect_uri="http://localhost/callback")

        class DummyResp:
            status = 200

            async def __aenter__(self) -> "DummyResp":
                return self

            async def __aexit__(self, *args: object, **kwargs: object) -> None:
                return None

        class DummySession:
            async def __aenter__(self) -> "DummySession":
                return self

            async def __aexit__(self, *args: object, **kwargs: object) -> None:
                return None

            def get(self, *_args: object, **_kwargs: object) -> DummyResp:
                return DummyResp()

        import trello_client_impl.oauth as oauth_mod

        monkeypatch.setattr(oauth_mod, "aiohttp", type("X", (), {"ClientSession": DummySession}))
        out = await handler.exchange_token("abc")
        assert out == "abc"

    async def test_exchange_token_status_error_raises(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Non-OK validation status should raise authentication error."""
        handler = TrelloOAuthHandler(api_key="k", api_secret="s", redirect_uri="http://localhost/callback")

        class DummyResp:
            status = 401

            async def __aenter__(self) -> "DummyResp":
                return self

            async def __aexit__(self, *args: object, **kwargs: object) -> None:
                return None

        class DummySession:
            async def __aenter__(self) -> "DummySession":
                return self

            async def __aexit__(self, *args: object, **kwargs: object) -> None:
                return None

            def get(self, *_args: object, **_kwargs: object) -> DummyResp:
                return DummyResp()

        import trello_client_impl.oauth as oauth_mod

        monkeypatch.setattr(oauth_mod, "aiohttp", type("X", (), {"ClientSession": DummySession}))
        with pytest.raises(KanbanAuthenticationError, match="Token validation failed"):
            await handler.exchange_token("bad")

    def test_from_env_validates_presence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """from_env should validate environment variables and construct on success."""
        # Ensure clean env
        for key in ("TRELLO_API_KEY", "TRELLO_API_SECRET", "REDIRECT_URI"):
            monkeypatch.delenv(key, raising=False)
        # Missing vars -> ValueError
        with pytest.raises(ValueError, match="TRELLO_API_KEY environment variable is required"):
            TrelloOAuthHandler.from_env()

        monkeypatch.setenv("TRELLO_API_KEY", "k")
        with pytest.raises(ValueError, match="TRELLO_API_SECRET environment variable is required"):
            TrelloOAuthHandler.from_env()

        monkeypatch.setenv("TRELLO_API_SECRET", "s")
        with pytest.raises(ValueError, match="REDIRECT_URI environment variable is required"):
            TrelloOAuthHandler.from_env()

        monkeypatch.setenv("REDIRECT_URI", "http://localhost/callback")
        h = TrelloOAuthHandler.from_env()
        assert isinstance(h, TrelloOAuthHandler)
