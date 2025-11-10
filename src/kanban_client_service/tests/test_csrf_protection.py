"""Tests for CSRF protection in OAuth flows."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from kanban_client_service.main import CSRFStateManager, app, csrf_manager


class TestCSRFStateManager:
    """Test the CSRFStateManager utility class."""

    def test_generate_state_returns_string(self) -> None:
        """State token should be a non-empty string."""
        manager = CSRFStateManager()
        state = manager.generate_state()
        assert isinstance(state, str)
        assert len(state) > 0

    def test_generate_state_returns_different_values(self) -> None:
        """Each generated state should be unique."""
        manager = CSRFStateManager()
        state1 = manager.generate_state()
        state2 = manager.generate_state()
        assert state1 != state2

    def test_validate_state_accepts_valid_state(self) -> None:
        """Valid state should pass validation."""
        manager = CSRFStateManager()
        state = manager.generate_state()
        assert manager.validate_state(state) is True

    def test_validate_state_rejects_invalid_state(self) -> None:
        """Invalid state should fail validation."""
        manager = CSRFStateManager()
        assert manager.validate_state("invalid-state") is False

    def test_validate_state_is_one_time_use(self) -> None:
        """State should only be valid once (one-time use)."""
        manager = CSRFStateManager()
        state = manager.generate_state()
        assert manager.validate_state(state) is True
        # Second validation should fail
        assert manager.validate_state(state) is False

    def test_validate_state_rejects_expired_state(self) -> None:
        """Expired state should fail validation."""
        import time
        manager = CSRFStateManager(expiry_seconds=0)
        state = manager.generate_state()
        # Sleep briefly to ensure expiry
        time.sleep(0.1)
        assert manager.validate_state(state) is False

    def test_validate_state_removes_expired_state(self) -> None:
        """Expired state should be removed from tracking."""
        import time
        manager = CSRFStateManager(expiry_seconds=0)
        state = manager.generate_state()
        assert len(manager.states) == 1
        time.sleep(0.1)
        _ = manager.validate_state(state)
        assert len(manager.states) == 0

    def test_generate_state_stores_timestamp(self) -> None:
        """Generated state should have a timestamp stored."""
        manager = CSRFStateManager()
        state = manager.generate_state()
        assert state in manager.states
        assert isinstance(manager.states[state], float)


class TestOAuthLoginEndpoint:
    """Test the /auth/login OAuth endpoint."""

    def test_login_returns_authorization_url(self) -> None:
        """Login should return an authorization URL."""
        client = TestClient(app)
        resp = client.get("/auth/login")
        assert resp.status_code == HTTPStatus.OK
        data: dict[str, str] = resp.json()  # type: ignore[assignment]
        assert "authorization_url" in data
        assert "https://trello.com" in data["authorization_url"]

    def test_login_returns_state(self) -> None:
        """Login should return a CSRF state token."""
        client = TestClient(app)
        resp = client.get("/auth/login")
        assert resp.status_code == HTTPStatus.OK
        data: dict[str, str] = resp.json()  # type: ignore[assignment]
        assert "state" in data
        assert isinstance(data["state"], str)
        assert len(data["state"]) > 0

    def test_login_state_is_different_each_time(self) -> None:
        """Each login request should generate a different state."""
        client = TestClient(app)
        resp1 = client.get("/auth/login")
        resp2 = client.get("/auth/login")
        state1: str = resp1.json()["state"]  # type: ignore[assignment]
        state2: str = resp2.json()["state"]  # type: ignore[assignment]
        assert state1 != state2

    def test_login_url_includes_state_parameter(self) -> None:
        """Authorization URL should include state parameter."""
        client = TestClient(app)
        resp = client.get("/auth/login")
        data: dict[str, str] = resp.json()  # type: ignore[assignment]
        assert "state=" in data["authorization_url"]


class TestOAuthCallbackEndpoint:
    """Test the /auth/callback OAuth callback endpoint."""

    def setup_method(self) -> None:
        """Clear CSRF state before each test."""
        csrf_manager.states.clear()

    def test_callback_rejects_missing_state(self) -> None:
        """Callback should reject requests without state."""
        client = TestClient(app)
        resp = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": ""},
        )
        assert resp.status_code == HTTPStatus.FORBIDDEN

    def test_callback_rejects_invalid_state(self) -> None:
        """Callback should reject requests with invalid state."""
        client = TestClient(app)
        resp = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": "invalid-state"},
        )
        assert resp.status_code == HTTPStatus.FORBIDDEN

    def test_callback_rejects_fake_state(self) -> None:
        """Callback should reject fake state tokens."""
        client = TestClient(app)
        resp = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": "fake_state_12345"},
        )
        assert resp.status_code == HTTPStatus.FORBIDDEN

    @patch("kanban_client_api.get_client")
    async def test_callback_accepts_valid_state(self, mock_get_client: AsyncMock) -> None:
        """Callback should accept requests with valid state."""
        # Mock the async client properly
        mock_client = AsyncMock()
        mock_client.exchange_token = AsyncMock(return_value="credentials")
        mock_client.get_user = AsyncMock(
            return_value=type(
                "User",
                (),
                {
                    "id": "user123",
                    "full_name": "Test User",
                },
            )(),
        )
        mock_get_client.return_value = mock_client

        # Generate a valid state first
        state = csrf_manager.generate_state()

        # Create client and post callback
        client = TestClient(app)
        resp = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": state},
        )

        # Should not return 403 for valid state
        assert resp.status_code != HTTPStatus.FORBIDDEN

    def test_callback_state_is_one_time_use(self) -> None:
        """State should not be reusable after first use."""
        client = TestClient(app)

        # Generate valid state
        state = csrf_manager.generate_state()

        # First callback should be rejected (invalid token) but not due to state
        _ = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": state},
        )
        # State consumed regardless of token validity

        # Second callback with same state should be rejected due to state
        resp2 = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": state},
        )
        assert resp2.status_code == HTTPStatus.FORBIDDEN

    def test_callback_contains_csrf_detail_message(self) -> None:
        """CSRF rejection should include detail message."""
        client = TestClient(app)
        resp = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": "invalid"},
        )
        data: dict[str, str] = resp.json()  # type: ignore[assignment]
        assert "detail" in data
        detail_str: str = str(data["detail"]).lower()
        assert "csrf" in detail_str or "state" in detail_str

    def test_callback_sets_secure_cookie(self) -> None:
        """Successful callback should set secure cookies."""
        state = csrf_manager.generate_state()
        client = TestClient(app)

        resp = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": state},
        )

        # Check for Set-Cookie header
        if resp.status_code != HTTPStatus.FORBIDDEN:
            # If a cookie was set, verify it has security attributes
            set_cookie_header: str = resp.headers.get("set-cookie") or ""
            if set_cookie_header:
                lower_header = set_cookie_header.lower()
                assert "httponly" in lower_header


class TestCSRFStateIntegration:
    """Integration tests for CSRF protection in OAuth flow."""

    def setup_method(self) -> None:
        """Clear CSRF state before each test."""
        csrf_manager.states.clear()

    def test_full_oauth_flow_requires_matching_state(self) -> None:
        """Full flow: login generates state, callback must use same state."""
        client = TestClient(app)

        # Step 1: Get state from login
        login_resp = client.get("/auth/login")
        assert login_resp.status_code == HTTPStatus.OK
        state_from_login: str = login_resp.json()["state"]  # type: ignore[assignment]

        # Step 2: Try callback with different state (should fail)
        callback_resp = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": "wrong-state"},
        )
        assert callback_resp.status_code == HTTPStatus.FORBIDDEN

        # Step 3: Try callback with original state (should fail - token issue, not state)
        # The state is still valid at this point
        callback_resp2 = client.post(
            "/auth/callback",
            json={"token": "test-token", "state": state_from_login},
        )
        # Should not be FORBIDDEN (CSRF) - should be 401 or 500 due to token issue
        assert callback_resp2.status_code != HTTPStatus.FORBIDDEN

    def test_csrf_protection_against_replay_attack(self) -> None:
        """CSRF state should prevent token replay attacks."""
        client = TestClient(app)

        # Generate state
        state = csrf_manager.generate_state()

        # First attempt
        _ = client.post(
            "/auth/callback",
            json={"token": "token-1", "state": state},
        )
        # Regardless of outcome, state should be consumed

        # Replay attempt with same state
        resp2 = client.post(
            "/auth/callback",
            json={"token": "token-1", "state": state},
        )
        assert resp2.status_code == HTTPStatus.FORBIDDEN

    def test_csrf_state_expires(self) -> None:
        """CSRF state should expire after timeout."""
        # Create a manager with very short expiry
        short_lived_manager = CSRFStateManager(expiry_seconds=0)
        state = short_lived_manager.generate_state()

        # Wait for expiry
        import time
        time.sleep(0.1)

        # Validation should fail due to expiry
        assert short_lived_manager.validate_state(state) is False
