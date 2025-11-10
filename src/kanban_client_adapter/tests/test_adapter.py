"""Tests for the KanbanClientAdapter."""

from unittest.mock import MagicMock, patch

import pytest
from kanban_client_api.exceptions import (
    KanbanAPIError,
    KanbanAuthenticationError,
    KanbanNotFoundError,
)
from kanban_generated_client.models.error_response import ErrorResponse
from kanban_generated_client.models.http_validation_error import HTTPValidationError

from kanban_client_adapter.adapter import KanbanClientAdapter


class TestAdapterInitialization:
    """Tests for adapter initialization."""

    def test_adapter_initialization(self) -> None:
        """Test adapter initialization with base URL."""
        client = KanbanClientAdapter(base_url="http://localhost:9000")
        assert client is not None

    def test_adapter_default_base_url(self) -> None:
        """Test adapter initialization with default base URL."""
        client = KanbanClientAdapter()
        assert client is not None

    def test_adapter_with_custom_url(self) -> None:
        """Test adapter initialization with custom base URL."""
        custom_url = "http://custom.example.com:3000"
        client = KanbanClientAdapter(base_url=custom_url)
        assert client is not None
        # Verify internal client is created
        assert hasattr(client, "_client")

    def test_adapter_has_required_methods(self) -> None:
        """Test that adapter has all required Kanban client methods."""
        client = KanbanClientAdapter()
        # Verify the adapter has all the required methods
        assert hasattr(client, "get_boards")
        assert hasattr(client, "get_board")
        assert hasattr(client, "create_board")
        assert hasattr(client, "update_board")
        assert hasattr(client, "delete_board")
        assert hasattr(client, "get_lists")
        assert hasattr(client, "create_list")
        assert hasattr(client, "update_list")
        assert hasattr(client, "get_cards")
        assert hasattr(client, "get_card")
        assert hasattr(client, "create_card")
        assert hasattr(client, "update_card")
        assert hasattr(client, "delete_card")
        assert hasattr(client, "get_current_user")


class TestAdapterErrorHandling:
    """Tests for adapter error handling."""

    def test_handle_api_error_with_none(self) -> None:
        """Test _handle_api_error raises KanbanAPIError for None response."""
        with pytest.raises(KanbanAPIError, match="invalid response"):
            KanbanClientAdapter._handle_api_error(None, "Test error")

    def test_handle_api_error_with_http_validation_error(self) -> None:
        """Test _handle_api_error raises KanbanAPIError for HTTPValidationError."""
        error = HTTPValidationError()
        with pytest.raises(KanbanAPIError, match="invalid response"):
            KanbanClientAdapter._handle_api_error(error, "Validation failed")

    def test_handle_api_error_with_authentication_failed(self) -> None:
        """Test _handle_api_error raises KanbanAuthenticationError for auth failure."""
        error = ErrorResponse(detail="Authentication failed")
        with pytest.raises(KanbanAuthenticationError, match="Authentication failed"):
            KanbanClientAdapter._handle_api_error(error, "Auth error")

    def test_handle_api_error_with_resource_not_found(self) -> None:
        """Test _handle_api_error raises KanbanNotFoundError for not found."""
        error = ErrorResponse(detail="Resource not found")
        with pytest.raises(KanbanNotFoundError, match="Resource not found"):
            KanbanClientAdapter._handle_api_error(error, "Not found")

    def test_handle_api_error_with_generic_error(self) -> None:
        """Test _handle_api_error raises KanbanAPIError for generic error."""
        error = ErrorResponse(detail="Some API error")
        with pytest.raises(KanbanAPIError, match="Some API error"):
            KanbanClientAdapter._handle_api_error(error, "API error")

    def test_return_success_true(self) -> None:
        """Test _return_success returns True when success attribute is True."""
        client = KanbanClientAdapter()
        mock_obj = MagicMock()
        mock_obj.success = True
        assert client._return_success(mock_obj) is True

    def test_return_success_false(self) -> None:
        """Test _return_success returns False when success attribute is False."""
        client = KanbanClientAdapter()
        mock_obj = MagicMock()
        mock_obj.success = False
        assert client._return_success(mock_obj) is False

    def test_return_success_missing_attribute(self) -> None:
        """Test _return_success returns False when success attribute is missing."""
        client = KanbanClientAdapter()
        mock_obj = MagicMock(spec=[])
        assert client._return_success(mock_obj) is False

    def test_return_success_non_bool_value(self) -> None:
        """Test _return_success returns False when success is not boolean."""
        client = KanbanClientAdapter()
        mock_obj = MagicMock()
        mock_obj.success = "true"
        assert client._return_success(mock_obj) is False


class TestAdapterBoards:
    """Tests for board-related adapter methods."""

    @pytest.mark.asyncio
    async def test_get_boards_success(self) -> None:
        """Test successful get_boards call."""
        mock_board = MagicMock()
        mock_board.id = "b1"
        mock_board.name = "Test Board"
        mock_board.description = "Test Description"
        mock_board.closed = False
        mock_board.url = "http://example.com/b1"
        mock_board.created_at = "2024-01-01"

        with patch("kanban_client_adapter.adapter.get_boards_boards_get.asyncio") as mock_get:
            mock_get.return_value = [mock_board]
            client = KanbanClientAdapter()
            boards = await client.get_boards()

            assert len(boards) == 1
            assert boards[0].id == "b1"
            assert boards[0].name == "Test Board"
            assert boards[0].description == "Test Description"
            assert boards[0].closed is False

    @pytest.mark.asyncio
    async def test_get_boards_empty(self) -> None:
        """Test get_boards with empty list."""
        with patch("kanban_client_adapter.adapter.get_boards_boards_get.asyncio") as mock_get:
            mock_get.return_value = []
            client = KanbanClientAdapter()
            boards = await client.get_boards()

            assert boards == []

    @pytest.mark.asyncio
    async def test_get_boards_error(self) -> None:
        """Test get_boards with error response."""
        with patch("kanban_client_adapter.adapter.get_boards_boards_get.asyncio") as mock_get:
            error = ErrorResponse(detail="API error")
            mock_get.return_value = error
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError):
                await client.get_boards()

    @pytest.mark.asyncio
    async def test_get_boards_invalid_response(self) -> None:
        """Test get_boards when response is not a list."""
        with patch("kanban_client_adapter.adapter.get_boards_boards_get.asyncio") as mock_get:
            mock_get.return_value = {"id": "b1"}  # Dict instead of list
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError, match="did not return a list"):
                await client.get_boards()

    @pytest.mark.asyncio
    async def test_get_board_success(self) -> None:
        """Test successful get_board call."""
        mock_board = MagicMock()
        mock_board.id = "b1"
        mock_board.name = "Test Board"
        mock_board.description = "Test Description"
        mock_board.closed = False
        mock_board.url = "http://example.com/b1"
        mock_board.created_at = "2024-01-01"

        with patch("kanban_client_adapter.adapter.get_board_boards_board_id_get.asyncio") as mock_get:
            mock_get.return_value = mock_board
            client = KanbanClientAdapter()
            board = await client.get_board("b1")

            assert board.id == "b1"
            assert board.name == "Test Board"
            mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_board_not_found(self) -> None:
        """Test get_board with not found error."""
        with patch("kanban_client_adapter.adapter.get_board_boards_board_id_get.asyncio") as mock_get:
            error = ErrorResponse(detail="Resource not found")
            mock_get.return_value = error
            client = KanbanClientAdapter()

            with pytest.raises(KanbanNotFoundError):
                await client.get_board("b1")

    @pytest.mark.asyncio
    async def test_create_board_success(self) -> None:
        """Test successful create_board call."""
        mock_board = MagicMock()
        mock_board.id = "b2"
        mock_board.name = "New Board"
        mock_board.description = "New Description"
        mock_board.closed = False
        mock_board.url = "http://example.com/b2"
        mock_board.created_at = "2024-01-02"

        with patch("kanban_client_adapter.adapter.create_board_boards_post.asyncio") as mock_create:
            mock_create.return_value = mock_board
            client = KanbanClientAdapter()
            board = await client.create_board("New Board", "New Description")

            assert board.id == "b2"
            assert board.name == "New Board"
            assert board.description == "New Description"
            mock_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_board_error(self) -> None:
        """Test create_board with API error."""
        with patch("kanban_client_adapter.adapter.create_board_boards_post.asyncio") as mock_create:
            error = ErrorResponse(detail="Invalid input")
            mock_create.return_value = error
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError):
                await client.create_board("New Board")

    @pytest.mark.asyncio
    async def test_update_board_success(self) -> None:
        """Test successful update_board call."""
        mock_board = MagicMock()
        mock_board.id = "b1"
        mock_board.name = "Updated Board"
        mock_board.description = "Updated Description"
        mock_board.closed = False
        mock_board.url = "http://example.com/b1"
        mock_board.created_at = "2024-01-01"

        with patch("kanban_client_adapter.adapter.update_board_boards_board_id_put.asyncio") as mock_update:
            mock_update.return_value = mock_board
            client = KanbanClientAdapter()
            board = await client.update_board("b1", "Updated Board", "Updated Description")

            assert board.id == "b1"
            assert board.name == "Updated Board"
            assert board.description == "Updated Description"
            mock_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_board_success(self) -> None:
        """Test successful delete_board call."""
        mock_result = MagicMock()
        mock_result.success = True

        with patch("kanban_client_adapter.adapter.delete_board_boards_board_id_delete.asyncio") as mock_delete:
            mock_delete.return_value = mock_result
            client = KanbanClientAdapter()
            result = await client.delete_board("b1")

            assert result is True
            mock_delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_board_failure(self) -> None:
        """Test delete_board with error."""
        with patch("kanban_client_adapter.adapter.delete_board_boards_board_id_delete.asyncio") as mock_delete:
            error = ErrorResponse(detail="Cannot delete board")
            mock_delete.return_value = error
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError):
                await client.delete_board("b1")


class TestAdapterLists:
    """Tests for list-related adapter methods."""

    @pytest.mark.asyncio
    async def test_get_lists_success(self) -> None:
        """Test successful get_lists call."""
        mock_list = MagicMock()
        mock_list.id = "l1"
        mock_list.name = "Test List"
        mock_list.board_id = "b1"
        mock_list.position = 0.0
        mock_list.closed = False

        with patch("kanban_client_adapter.adapter.get_lists_boards_board_id_lists_get.asyncio") as mock_get:
            mock_get.return_value = [mock_list]
            client = KanbanClientAdapter()
            lists = await client.get_lists("b1")

            assert len(lists) == 1
            assert lists[0].id == "l1"
            assert lists[0].name == "Test List"
            assert lists[0].board_id == "b1"

    @pytest.mark.asyncio
    async def test_get_lists_invalid_response(self) -> None:
        """Test get_lists when response is not a list."""
        with patch("kanban_client_adapter.adapter.get_lists_boards_board_id_lists_get.asyncio") as mock_get:
            mock_get.return_value = {"id": "l1"}
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError, match="did not return a list"):
                await client.get_lists("b1")

    @pytest.mark.asyncio
    async def test_create_list_success(self) -> None:
        """Test successful create_list call."""
        mock_list = MagicMock()
        mock_list.id = "l2"
        mock_list.name = "New List"
        mock_list.board_id = "b1"
        mock_list.position = 1.0
        mock_list.closed = False

        with patch("kanban_client_adapter.adapter.create_list_boards_board_id_lists_post.asyncio") as mock_create:
            mock_create.return_value = mock_list
            client = KanbanClientAdapter()
            kanban_list = await client.create_list("b1", "New List")

            assert kanban_list.id == "l2"
            assert kanban_list.name == "New List"

    @pytest.mark.asyncio
    async def test_update_list_success(self) -> None:
        """Test successful update_list call."""
        mock_list = MagicMock()
        mock_list.id = "l1"
        mock_list.name = "Updated List"
        mock_list.board_id = "b1"
        mock_list.position = 0.0
        mock_list.closed = False

        with patch("kanban_client_adapter.adapter.update_list_lists_list_id_put.asyncio") as mock_update:
            mock_update.return_value = mock_list
            client = KanbanClientAdapter()
            kanban_list = await client.update_list("l1", "Updated List")

            assert kanban_list.id == "l1"
            assert kanban_list.name == "Updated List"


class TestAdapterCards:
    """Tests for card-related adapter methods."""

    @pytest.mark.asyncio
    async def test_get_cards_success(self) -> None:
        """Test successful get_cards call."""
        mock_card = MagicMock()
        mock_card.id = "c1"
        mock_card.name = "Test Card"
        mock_card.list_id = "l1"
        mock_card.board_id = "b1"
        mock_card.description = "Test Description"
        mock_card.position = 0.0
        mock_card.closed = False
        mock_card.due_date = None
        mock_card.url = "http://example.com/c1"
        mock_card.created_at = "2024-01-01"

        with patch("kanban_client_adapter.adapter.get_cards_lists_list_id_cards_get.asyncio") as mock_get:
            mock_get.return_value = [mock_card]
            client = KanbanClientAdapter()
            cards = await client.get_cards("l1")

            assert len(cards) == 1
            assert cards[0].id == "c1"
            assert cards[0].name == "Test Card"

    @pytest.mark.asyncio
    async def test_get_cards_invalid_response(self) -> None:
        """Test get_cards when response is not a list."""
        with patch("kanban_client_adapter.adapter.get_cards_lists_list_id_cards_get.asyncio") as mock_get:
            mock_get.return_value = {"id": "c1"}
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError, match="did not return a list"):
                await client.get_cards("l1")

    @pytest.mark.asyncio
    async def test_get_card_success(self) -> None:
        """Test successful get_card call."""
        mock_card = MagicMock()
        mock_card.id = "c1"
        mock_card.name = "Test Card"
        mock_card.list_id = "l1"
        mock_card.board_id = "b1"
        mock_card.description = "Test Description"
        mock_card.position = 0.0
        mock_card.closed = False
        mock_card.due_date = None
        mock_card.url = "http://example.com/c1"
        mock_card.created_at = "2024-01-01"

        with patch("kanban_client_adapter.adapter.get_card_cards_card_id_get.asyncio") as mock_get:
            mock_get.return_value = mock_card
            client = KanbanClientAdapter()
            card = await client.get_card("c1")

            assert card.id == "c1"
            assert card.name == "Test Card"

    @pytest.mark.asyncio
    async def test_create_card_success(self) -> None:
        """Test successful create_card call."""
        mock_card = MagicMock()
        mock_card.id = "c2"
        mock_card.name = "New Card"
        mock_card.list_id = "l1"
        mock_card.board_id = "b1"
        mock_card.description = "New Description"
        mock_card.position = 1.0
        mock_card.closed = False
        mock_card.due_date = None
        mock_card.url = "http://example.com/c2"
        mock_card.created_at = "2024-01-02"

        with patch("kanban_client_adapter.adapter.create_card_lists_list_id_cards_post.asyncio") as mock_create:
            mock_create.return_value = mock_card
            client = KanbanClientAdapter()
            card = await client.create_card("l1", "New Card", "New Description")

            assert card.id == "c2"
            assert card.name == "New Card"
            assert card.description == "New Description"

    @pytest.mark.asyncio
    async def test_update_card_success(self) -> None:
        """Test successful update_card call."""
        mock_card = MagicMock()
        mock_card.id = "c1"
        mock_card.name = "Updated Card"
        mock_card.list_id = "l2"
        mock_card.board_id = "b1"
        mock_card.description = "Updated Description"
        mock_card.position = 0.0
        mock_card.closed = False
        mock_card.due_date = None
        mock_card.url = "http://example.com/c1"
        mock_card.created_at = "2024-01-01"

        with patch("kanban_client_adapter.adapter.update_card_cards_card_id_put.asyncio") as mock_update:
            mock_update.return_value = mock_card
            client = KanbanClientAdapter()
            card = await client.update_card("c1", "Updated Card", "Updated Description", "l2")

            assert card.id == "c1"
            assert card.name == "Updated Card"
            assert card.list_id == "l2"

    @pytest.mark.asyncio
    async def test_delete_card_success(self) -> None:
        """Test successful delete_card call."""
        mock_result = MagicMock()
        mock_result.success = True

        with patch("kanban_client_adapter.adapter.delete_card_cards_card_id_delete.asyncio") as mock_delete:
            mock_delete.return_value = mock_result
            client = KanbanClientAdapter()
            result = await client.delete_card("c1")

            assert result is True


class TestAdapterUser:
    """Tests for user-related adapter methods."""

    @pytest.mark.asyncio
    async def test_get_current_user_success(self) -> None:
        """Test successful get_current_user call."""
        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.username = "testuser"
        mock_user.full_name = "Test User"
        mock_user.email = "test@example.com"

        with patch("kanban_client_adapter.adapter.get_current_user_users_me_get.asyncio") as mock_get:
            mock_get.return_value = mock_user
            client = KanbanClientAdapter()
            user = await client.get_current_user()

            assert user.id == "u1"
            assert user.username == "testuser"
            assert user.full_name == "Test User"
            assert user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_current_user_auth_error(self) -> None:
        """Test get_current_user with authentication error."""
        with patch("kanban_client_adapter.adapter.get_current_user_users_me_get.asyncio") as mock_get:
            error = ErrorResponse(detail="Authentication failed")
            mock_get.return_value = error
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAuthenticationError):
                await client.get_current_user()


class TestAdapterOAuth:
    """Tests for OAuth-related adapter methods."""

    @pytest.mark.asyncio
    async def test_get_authorization_url_success(self) -> None:
        """Test successful get_authorization_url call."""
        mock_response = MagicMock()
        mock_response.additional_properties = {"authorization_url": "https://auth.example.com/authorize"}

        with patch("kanban_client_adapter.adapter.login_auth_login_get.asyncio") as mock_login:
            mock_login.return_value = mock_response
            client = KanbanClientAdapter()
            url = await client.get_authorization_url()

            assert url == "https://auth.example.com/authorize"

    @pytest.mark.asyncio
    async def test_get_authorization_url_dict_response(self) -> None:
        """Test get_authorization_url when response is a dict."""
        mock_response = {"authorization_url": "https://auth.example.com/authorize"}

        with patch("kanban_client_adapter.adapter.login_auth_login_get.asyncio") as mock_login:
            mock_login.return_value = mock_response
            client = KanbanClientAdapter()
            url = await client.get_authorization_url()

            assert url == "https://auth.example.com/authorize"

    @pytest.mark.asyncio
    async def test_get_authorization_url_missing(self) -> None:
        """Test get_authorization_url when URL is missing from response."""
        mock_response = MagicMock()
        mock_response.additional_properties = {}

        with patch("kanban_client_adapter.adapter.login_auth_login_get.asyncio") as mock_login:
            mock_login.return_value = mock_response
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError, match="Authorization URL not found"):
                await client.get_authorization_url()

    @pytest.mark.asyncio
    async def test_get_authorization_url_error(self) -> None:
        """Test get_authorization_url with API error."""
        with patch("kanban_client_adapter.adapter.login_auth_login_get.asyncio") as mock_login:
            error = ErrorResponse(detail="OAuth error")
            mock_login.return_value = error
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError):
                await client.get_authorization_url()

    @pytest.mark.asyncio
    async def test_exchange_token_success(self) -> None:
        """Test successful exchange_token call (validates by getting user)."""
        mock_user = MagicMock()
        mock_user.id = "u1"
        mock_user.username = "testuser"

        with patch("kanban_client_adapter.adapter.get_current_user_users_me_get.asyncio") as mock_get:
            mock_get.return_value = mock_user
            client = KanbanClientAdapter()
            token = await client.exchange_token()

            # Should return empty string as placeholder
            assert token == ""

    @pytest.mark.asyncio
    async def test_exchange_token_auth_error(self) -> None:
        """Test exchange_token with authentication error."""
        with patch("kanban_client_adapter.adapter.get_current_user_users_me_get.asyncio") as mock_get:
            error = ErrorResponse(detail="Authentication failed")
            mock_get.return_value = error
            client = KanbanClientAdapter()

            with pytest.raises(KanbanAuthenticationError, match="Token exchange failed"):
                await client.exchange_token()
