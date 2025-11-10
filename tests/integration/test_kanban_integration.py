"""Integration tests for kanban client packages.

These tests verify that the kanban packages work correctly together:
- kanban_client_api (abstract interface)
- trello_client_impl (Trello implementation)
- kanban_client_adapter (adapter wrapping generated client)
- kanban_client_service (FastAPI service)

Tests use mocking for the generated client but verify real interactions between packages.
"""

import logging
import os
from unittest.mock import MagicMock, patch

import pytest
from kanban_client_adapter.adapter import KanbanClientAdapter
from kanban_client_api.exceptions import (
    KanbanAPIError,
    KanbanAuthenticationError,
    KanbanNotFoundError,
)
from trello_client_impl.trello_impl import TrelloClientImpl

import kanban_client_api

# Mark all tests in this file as integration tests
pytestmark = pytest.mark.integration

logger = logging.getLogger(__name__)

# Environment setup for trello client
os.environ.setdefault("TRELLO_API_KEY", "test_api_key")
os.environ.setdefault("TRELLO_API_SECRET", "test_api_secret")
os.environ.setdefault("REDIRECT_URI", "http://localhost:5000/auth/callback")

# Import after environment is set
import trello_client_impl as _  # noqa: E402,F401


class TestDependencyInjection:
    """Tests for dependency injection between kanban packages."""

    def test_trello_impl_registers_with_kanban_api(self) -> None:
        """Test that importing trello_client_impl registers with kanban_client_api."""
        # The import happens at module level, but we verify the registration worked
        client = kanban_client_api.get_client(token="test_token")

        # Should be a TrelloClientImpl instance
        assert isinstance(client, TrelloClientImpl)

    def test_get_client_function_is_replaced(self) -> None:
        """Test that kanban_client_api.get_client is replaced by trello implementation."""
        # The get_client should be a function that returns TrelloClientImpl
        client = kanban_client_api.get_client(token="test_token")
        assert isinstance(client, TrelloClientImpl)

    def test_multiple_client_instances_are_independent(self) -> None:
        """Test that multiple client instances can be created independently."""
        client1 = kanban_client_api.get_client(token="token1")
        client2 = kanban_client_api.get_client(token="token2")

        # Should be separate instances
        assert client1 is not client2
        assert isinstance(client1, TrelloClientImpl)
        assert isinstance(client2, TrelloClientImpl)
class TestAdapterIntegration:
    """Tests for adapter integration with kanban_client_api."""

    @pytest.mark.asyncio
    async def test_adapter_implements_kanban_client_interface(self) -> None:
        """Test that KanbanClientAdapter properly implements KanbanClient interface."""
        adapter = KanbanClientAdapter(base_url="http://localhost:8000")

        # Should have all required methods from KanbanClient interface
        assert hasattr(adapter, "get_boards")
        assert hasattr(adapter, "get_board")
        assert hasattr(adapter, "create_board")
        assert hasattr(adapter, "update_board")
        assert hasattr(adapter, "delete_board")
        assert hasattr(adapter, "get_lists")
        assert hasattr(adapter, "create_list")
        assert hasattr(adapter, "update_list")
        assert hasattr(adapter, "get_cards")
        assert hasattr(adapter, "get_card")
        assert hasattr(adapter, "create_card")
        assert hasattr(adapter, "update_card")
        assert hasattr(adapter, "delete_card")
        assert hasattr(adapter, "get_current_user")
        assert hasattr(adapter, "get_authorization_url")
        assert hasattr(adapter, "exchange_token")

    @pytest.mark.asyncio
    async def test_adapter_board_operations_return_correct_types(self) -> None:
        """Test that adapter methods return correct types implementing KanbanBoard interface."""
        mock_board = MagicMock()
        mock_board.id = "board1"
        mock_board.name = "Test Board"
        mock_board.description = "Test Description"
        mock_board.closed = False
        mock_board.url = "http://example.com/board1"
        mock_board.created_at = None

        with patch("kanban_client_adapter.adapter.get_boards_boards_get.asyncio") as mock_get:
            mock_get.return_value = [mock_board]
            adapter = KanbanClientAdapter()
            boards = await adapter.get_boards()

            # Verify type is correct
            assert len(boards) == 1
            board = boards[0]

            # Should have all KanbanBoard properties
            assert hasattr(board, "id")
            assert hasattr(board, "name")
            assert hasattr(board, "description")
            assert hasattr(board, "closed")
            assert hasattr(board, "url")
            assert hasattr(board, "created_at")


class TestExceptionConversion:
    """Tests for exception conversion between adapter and API layers."""

    @pytest.mark.asyncio
    async def test_adapter_converts_auth_errors(self) -> None:
        """Test that adapter converts ErrorResponse to KanbanAuthenticationError."""
        from kanban_generated_client.models.error_response import ErrorResponse

        with patch("kanban_client_adapter.adapter.get_current_user_users_me_get.asyncio") as mock_get:
            error = ErrorResponse(detail="Authentication failed")
            mock_get.return_value = error
            adapter = KanbanClientAdapter()

            with pytest.raises(KanbanAuthenticationError):
                await adapter.get_current_user()

    @pytest.mark.asyncio
    async def test_adapter_converts_not_found_errors(self) -> None:
        """Test that adapter converts ErrorResponse to KanbanNotFoundError."""
        from kanban_generated_client.models.error_response import ErrorResponse

        with patch("kanban_client_adapter.adapter.get_board_boards_board_id_get.asyncio") as mock_get:
            error = ErrorResponse(detail="Resource not found")
            mock_get.return_value = error
            adapter = KanbanClientAdapter()

            with pytest.raises(KanbanNotFoundError):
                await adapter.get_board("board1")

    @pytest.mark.asyncio
    async def test_adapter_converts_generic_errors(self) -> None:
        """Test that adapter converts generic ErrorResponse to KanbanAPIError."""
        from kanban_generated_client.models.error_response import ErrorResponse

        with patch("kanban_client_adapter.adapter.get_boards_boards_get.asyncio") as mock_get:
            error = ErrorResponse(detail="API error occurred")
            mock_get.return_value = error
            adapter = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError):
                await adapter.get_boards()


class TestTrelloImplementationIntegration:
    """Tests for TrelloClientImpl integration with kanban_client_api."""

    def test_trello_impl_is_kanban_client_type(self) -> None:
        """Test that TrelloClientImpl is a KanbanClient."""
        client = TrelloClientImpl(token="test_token")

        # Should be KanbanClient instance
        assert hasattr(client, "get_boards")
        assert hasattr(client, "get_current_user")
        assert hasattr(client, "token")
        assert client.token == "test_token"

    def test_trello_impl_from_di_container(self) -> None:
        """Test that TrelloClientImpl is created from DI container."""
        client = kanban_client_api.get_client(token="test_token")

        assert isinstance(client, TrelloClientImpl)
        assert client.token == "test_token"


class TestMultiPackageWorkflow:
    """Integration tests for complete workflows across packages."""

    @pytest.mark.asyncio
    async def test_board_crud_workflow(self) -> None:
        """Test complete board CRUD workflow through adapter."""
        # Setup mocks for all operations
        new_board = MagicMock()
        new_board.id = "b1"
        new_board.name = "My Board"
        new_board.description = "Test board"
        new_board.closed = False
        new_board.url = "http://example.com/b1"
        new_board.created_at = None

        updated_board = MagicMock()
        updated_board.id = "b1"
        updated_board.name = "Updated Board"
        updated_board.description = "Updated description"
        updated_board.closed = False
        updated_board.url = "http://example.com/b1"
        updated_board.created_at = None

        with patch("kanban_client_adapter.adapter.create_board_boards_post.asyncio") as mock_create, \
             patch("kanban_client_adapter.adapter.get_board_boards_board_id_get.asyncio") as mock_get, \
             patch("kanban_client_adapter.adapter.update_board_boards_board_id_put.asyncio") as mock_update, \
             patch("kanban_client_adapter.adapter.delete_board_boards_board_id_delete.asyncio") as mock_delete:

            mock_create.return_value = new_board
            mock_get.return_value = new_board
            mock_update.return_value = updated_board
            mock_result = MagicMock()
            mock_result.success = True
            mock_delete.return_value = mock_result

            adapter = KanbanClientAdapter()

            # Create
            created = await adapter.create_board("My Board", "Test board")
            assert created.name == "My Board"

            # Get
            fetched = await adapter.get_board("b1")
            assert fetched.id == "b1"

            # Update
            updated = await adapter.update_board("b1", "Updated Board", "Updated description")
            assert updated.name == "Updated Board"

            # Delete
            deleted = await adapter.delete_board("b1")
            assert deleted is True

    @pytest.mark.asyncio
    async def test_list_and_card_workflow(self) -> None:
        """Test workflow with lists and cards."""
        mock_list = MagicMock()
        mock_list.id = "l1"
        mock_list.name = "To Do"
        mock_list.board_id = "b1"
        mock_list.position = 0.0
        mock_list.closed = False

        mock_card = MagicMock()
        mock_card.id = "c1"
        mock_card.name = "Task 1"
        mock_card.list_id = "l1"
        mock_card.board_id = "b1"
        mock_card.description = "Do something"
        mock_card.position = 0.0
        mock_card.closed = False
        mock_card.due_date = None
        mock_card.url = None
        mock_card.created_at = None

        with patch("kanban_client_adapter.adapter.get_lists_boards_board_id_lists_get.asyncio") as mock_get_lists, \
             patch("kanban_client_adapter.adapter.create_list_boards_board_id_lists_post.asyncio") as mock_create_list, \
             patch("kanban_client_adapter.adapter.get_cards_lists_list_id_cards_get.asyncio") as mock_get_cards, \
             patch("kanban_client_adapter.adapter.create_card_lists_list_id_cards_post.asyncio") as mock_create_card:

            mock_get_lists.return_value = [mock_list]
            mock_create_list.return_value = mock_list
            mock_get_cards.return_value = [mock_card]
            mock_create_card.return_value = mock_card

            adapter = KanbanClientAdapter()

            # Get lists
            lists = await adapter.get_lists("b1")
            assert len(lists) == 1
            assert lists[0].name == "To Do"

            # Create list
            new_list = await adapter.create_list("b1", "In Progress")
            assert new_list.name == "To Do"

            # Get cards in list
            cards = await adapter.get_cards("l1")
            assert len(cards) == 1
            assert cards[0].name == "Task 1"

            # Create card
            new_card = await adapter.create_card("l1", "New Task", "Task description")
            assert new_card.name == "Task 1"


class TestErrorPropagation:
    """Tests for error propagation through package layers."""

    @pytest.mark.asyncio
    async def test_invalid_response_handling(self) -> None:
        """Test that adapter handles invalid responses correctly."""
        from kanban_generated_client.models.http_validation_error import HTTPValidationError

        with patch("kanban_client_adapter.adapter.get_boards_boards_get.asyncio") as mock_get:
            mock_get.return_value = HTTPValidationError()
            adapter = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError):
                await adapter.get_boards()

    @pytest.mark.asyncio
    async def test_none_response_handling(self) -> None:
        """Test that adapter handles None responses correctly."""
        with patch("kanban_client_adapter.adapter.get_board_boards_board_id_get.asyncio") as mock_get:
            mock_get.return_value = None
            adapter = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError):
                await adapter.get_board("b1")

    @pytest.mark.asyncio
    async def test_non_list_response_for_list_operation(self) -> None:
        """Test that adapter rejects non-list responses for list operations."""
        with patch("kanban_client_adapter.adapter.get_boards_boards_get.asyncio") as mock_get:
            # Return a dict instead of list
            mock_get.return_value = {"id": "b1"}
            adapter = KanbanClientAdapter()

            with pytest.raises(KanbanAPIError, match="did not return a list"):
                await adapter.get_boards()


class TestAbstractInterfaceCompliance:
    """Tests that implementations comply with abstract interfaces."""

    def test_kanban_board_interface_properties(self) -> None:
        """Test that KanbanBoard ABC requires specific properties."""
        from kanban_client_adapter.models import AdapterBoard
        from kanban_client_api.models import KanbanBoard

        board = AdapterBoard(
            board_id="b1",
            name="Test",
            description="Test board",
            closed=False,
            url="http://example.com",
            created_at=None,
        )

        # Should implement KanbanBoard interface
        assert isinstance(board, KanbanBoard)

        # Should have all required properties
        assert board.id == "b1"
        assert board.name == "Test"
        assert board.description == "Test board"
        assert board.closed is False
        assert board.url == "http://example.com"
        assert board.created_at is None

    def test_kanban_card_interface_properties(self) -> None:
        """Test that KanbanCard ABC requires specific properties."""
        from kanban_client_adapter.models import AdapterCard
        from kanban_client_api.models import KanbanCard

        card = AdapterCard(
            card_id="c1",
            name="Task",
            list_id="l1",
            board_id="b1",
            description="Test task",
            position=0.0,
            closed=False,
            due_date=None,
            url="http://example.com",
            created_at=None,
        )

        # Should implement KanbanCard interface
        assert isinstance(card, KanbanCard)

        # Should have all required properties
        assert card.id == "c1"
        assert card.name == "Task"
        assert card.list_id == "l1"
        assert card.board_id == "b1"
        assert card.description == "Test task"

    def test_kanban_user_interface_properties(self) -> None:
        """Test that KanbanUser ABC requires specific properties."""
        from kanban_client_adapter.models import AdapterUser
        from kanban_client_api.models import KanbanUser

        user = AdapterUser(
            user_id="u1",
            username="testuser",
            full_name="Test User",
            email="test@example.com",
        )

        # Should implement KanbanUser interface
        assert isinstance(user, KanbanUser)

        # Should have all required properties
        assert user.id == "u1"
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.email == "test@example.com"
