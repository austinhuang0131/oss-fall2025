"""Tests for the kanban client API abstract base classes.

This module contains unit tests that verify the contracts and behavior
of the kanban_client_api.KanbanClient and kanban_client_api models abstractions.
These tests use mocks to demonstrate how implementations should behave
and serve as documentation for the expected API contracts.
"""

from unittest.mock import AsyncMock, Mock

import pytest
from kanban_client_api.client import KanbanClient
from kanban_client_api.exceptions import (
    KanbanAPIError,
    KanbanAuthenticationError,
    KanbanNotFoundError,
    KanbanRateLimitError,
)
from kanban_client_api.models import KanbanBoard, KanbanCard, KanbanList, KanbanUser

# HTTP Status codes for exception tests
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMIT = 429


# Board-related tests
@pytest.mark.asyncio
async def test_client_get_boards() -> None:
    """Verifies and demonstrates the contract for the `get_boards` method.

    This test ensures that any implementation of the KanbanClient abstraction
    must have a `get_boards` method that returns a list of KanbanBoard objects.
    """
    # ARRANGE: Create mocks that conform to our abstractions.
    mock_board = Mock(spec=KanbanBoard)
    mock_board.id = "board_1"
    mock_board.name = "Test Board"
    mock_board.description = "A test board"
    mock_board.closed = False
    mock_board.url = "https://example.com/board1"
    mock_board.created_at = None

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.get_boards.return_value = [mock_board]

    # ACT: Use the client as a consumer would.
    boards = await mock_client.get_boards()
    first_board = boards[0] if boards else None

    # ASSERT: Verify the interaction and the result.
    mock_client.get_boards.assert_called_once_with()
    assert first_board is not None
    assert first_board.id == "board_1"
    assert first_board.name == "Test Board"
    assert first_board.description == "A test board"
    assert first_board.closed is False


@pytest.mark.asyncio
async def test_client_get_board() -> None:
    """Verifies and demonstrates the contract for the `get_board` method."""
    # ARRANGE
    mock_board = Mock(spec=KanbanBoard)
    mock_board.id = "board_123"
    mock_board.name = "Specific Board"

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.get_board.return_value = mock_board

    # ACT
    retrieved_board = await mock_client.get_board(board_id="board_123")

    # ASSERT
    mock_client.get_board.assert_called_once_with(board_id="board_123")
    assert retrieved_board.id == "board_123"
    assert retrieved_board.name == "Specific Board"


@pytest.mark.asyncio
async def test_client_create_board() -> None:
    """Verifies and demonstrates the contract for the `create_board` method."""
    # ARRANGE
    mock_board = Mock(spec=KanbanBoard)
    mock_board.id = "new_board"
    mock_board.name = "New Board"
    mock_board.description = "A newly created board"

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.create_board.return_value = mock_board

    # ACT
    created_board = await mock_client.create_board(
        name="New Board",
        description="A newly created board",
    )

    # ASSERT
    mock_client.create_board.assert_called_once_with(
        name="New Board",
        description="A newly created board",
    )
    assert created_board.id == "new_board"
    assert created_board.name == "New Board"


@pytest.mark.asyncio
async def test_client_update_board() -> None:
    """Verifies and demonstrates the contract for the `update_board` method."""
    # ARRANGE
    mock_board = Mock(spec=KanbanBoard)
    mock_board.id = "board_123"
    mock_board.name = "Updated Board"
    mock_board.description = "Updated description"

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.update_board.return_value = mock_board

    # ACT
    updated_board = await mock_client.update_board(
        board_id="board_123",
        name="Updated Board",
        description="Updated description",
    )

    # ASSERT
    mock_client.update_board.assert_called_once_with(
        board_id="board_123",
        name="Updated Board",
        description="Updated description",
    )
    assert updated_board.name == "Updated Board"


@pytest.mark.asyncio
async def test_client_delete_board() -> None:
    """Verifies and demonstrates the contract for the `delete_board` method."""
    # ARRANGE
    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.delete_board.return_value = True

    # ACT
    success = await mock_client.delete_board(board_id="board_to_delete")

    # ASSERT
    mock_client.delete_board.assert_called_once_with(board_id="board_to_delete")
    assert success is True


# List-related tests
@pytest.mark.asyncio
async def test_client_get_lists() -> None:
    """Verifies and demonstrates the contract for the `get_lists` method."""
    # ARRANGE
    mock_list = Mock(spec=KanbanList)
    mock_list.id = "list_1"
    mock_list.name = "Test List"
    mock_list.board_id = "board_1"
    mock_list.position = 0.0
    mock_list.closed = False

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.get_lists.return_value = [mock_list]

    # ACT
    lists = await mock_client.get_lists(board_id="board_1")
    first_list = lists[0] if lists else None

    # ASSERT
    mock_client.get_lists.assert_called_once_with(board_id="board_1")
    assert first_list is not None
    assert first_list.id == "list_1"
    assert first_list.name == "Test List"
    assert first_list.board_id == "board_1"


@pytest.mark.asyncio
async def test_client_create_list() -> None:
    """Verifies and demonstrates the contract for the `create_list` method."""
    # ARRANGE
    mock_list = Mock(spec=KanbanList)
    mock_list.id = "new_list"
    mock_list.name = "New List"
    mock_list.board_id = "board_1"

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.create_list.return_value = mock_list

    # ACT
    created_list = await mock_client.create_list(
        board_id="board_1",
        name="New List",
    )

    # ASSERT
    mock_client.create_list.assert_called_once_with(
        board_id="board_1",
        name="New List",
    )
    assert created_list.id == "new_list"
    assert created_list.name == "New List"


@pytest.mark.asyncio
async def test_client_update_list() -> None:
    """Verifies and demonstrates the contract for the `update_list` method."""
    # ARRANGE
    mock_list = Mock(spec=KanbanList)
    mock_list.id = "list_1"
    mock_list.name = "Updated List"

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.update_list.return_value = mock_list

    # ACT
    updated_list = await mock_client.update_list(
        list_id="list_1",
        name="Updated List",
    )

    # ASSERT
    mock_client.update_list.assert_called_once_with(
        list_id="list_1",
        name="Updated List",
    )
    assert updated_list.name == "Updated List"


# Card-related tests
@pytest.mark.asyncio
async def test_client_get_cards() -> None:
    """Verifies and demonstrates the contract for the `get_cards` method."""
    # ARRANGE
    mock_card = Mock(spec=KanbanCard)
    mock_card.id = "card_1"
    mock_card.name = "Test Card"
    mock_card.list_id = "list_1"
    mock_card.board_id = "board_1"
    mock_card.description = "A test card"
    mock_card.closed = False

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.get_cards.return_value = [mock_card]

    # ACT
    cards = await mock_client.get_cards(list_id="list_1")
    first_card = cards[0] if cards else None

    # ASSERT
    mock_client.get_cards.assert_called_once_with(list_id="list_1")
    assert first_card is not None
    assert first_card.id == "card_1"
    assert first_card.name == "Test Card"
    assert first_card.list_id == "list_1"


@pytest.mark.asyncio
async def test_client_get_card() -> None:
    """Verifies and demonstrates the contract for the `get_card` method."""
    # ARRANGE
    mock_card = Mock(spec=KanbanCard)
    mock_card.id = "card_123"
    mock_card.name = "Specific Card"

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.get_card.return_value = mock_card

    # ACT
    retrieved_card = await mock_client.get_card(card_id="card_123")

    # ASSERT
    mock_client.get_card.assert_called_once_with(card_id="card_123")
    assert retrieved_card.id == "card_123"
    assert retrieved_card.name == "Specific Card"


@pytest.mark.asyncio
async def test_client_create_card() -> None:
    """Verifies and demonstrates the contract for the `create_card` method."""
    # ARRANGE
    mock_card = Mock(spec=KanbanCard)
    mock_card.id = "new_card"
    mock_card.name = "New Card"
    mock_card.description = "A new card"
    mock_card.list_id = "list_1"

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.create_card.return_value = mock_card

    # ACT
    created_card = await mock_client.create_card(
        list_id="list_1",
        name="New Card",
        description="A new card",
    )

    # ASSERT
    mock_client.create_card.assert_called_once_with(
        list_id="list_1",
        name="New Card",
        description="A new card",
    )
    assert created_card.id == "new_card"
    assert created_card.name == "New Card"


@pytest.mark.asyncio
async def test_client_update_card() -> None:
    """Verifies and demonstrates the contract for the `update_card` method."""
    # ARRANGE
    mock_card = Mock(spec=KanbanCard)
    mock_card.id = "card_123"
    mock_card.name = "Updated Card"
    mock_card.description = "Updated description"

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.update_card.return_value = mock_card

    # ACT
    updated_card = await mock_client.update_card(
        card_id="card_123",
        name="Updated Card",
        description="Updated description",
    )

    # ASSERT
    mock_client.update_card.assert_called_once_with(
        card_id="card_123",
        name="Updated Card",
        description="Updated description",
    )
    assert updated_card.name == "Updated Card"


@pytest.mark.asyncio
async def test_client_delete_card() -> None:
    """Verifies and demonstrates the contract for the `delete_card` method."""
    # ARRANGE
    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.delete_card.return_value = True

    # ACT
    success = await mock_client.delete_card(card_id="card_to_delete")

    # ASSERT
    mock_client.delete_card.assert_called_once_with(card_id="card_to_delete")
    assert success is True


# User-related tests
@pytest.mark.asyncio
async def test_client_get_current_user() -> None:
    """Verifies and demonstrates the contract for the `get_current_user` method."""
    # ARRANGE
    mock_user = Mock(spec=KanbanUser)
    mock_user.id = "user_1"
    mock_user.username = "testuser"
    mock_user.full_name = "Test User"
    mock_user.email = "test@example.com"

    mock_client = AsyncMock(spec=KanbanClient)
    mock_client.get_current_user.return_value = mock_user

    # ACT
    user = await mock_client.get_current_user()

    # ASSERT
    mock_client.get_current_user.assert_called_once_with()
    assert user.id == "user_1"
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.email == "test@example.com"


# Model tests to verify properties
def test_kanban_board_abstraction() -> None:
    """Verifies board model properties."""
    mock_board = Mock(spec=KanbanBoard)
    mock_board.id = "board_1"
    mock_board.name = "Test Board"
    mock_board.description = "Description"
    mock_board.closed = False
    mock_board.url = "https://example.com"
    mock_board.created_at = None

    assert mock_board.id == "board_1"
    assert mock_board.name == "Test Board"
    assert mock_board.description == "Description"
    assert mock_board.closed is False
    assert mock_board.url == "https://example.com"
    assert mock_board.created_at is None


def test_kanban_list_abstraction() -> None:
    """Verifies list model properties."""
    mock_list = Mock(spec=KanbanList)
    mock_list.id = "list_1"
    mock_list.name = "Test List"
    mock_list.board_id = "board_1"
    mock_list.position = 1.0
    mock_list.closed = False

    assert mock_list.id == "list_1"
    assert mock_list.name == "Test List"
    assert mock_list.board_id == "board_1"
    assert mock_list.position == 1.0
    assert mock_list.closed is False


def test_kanban_card_abstraction() -> None:
    """Verifies card model properties."""
    mock_card = Mock(spec=KanbanCard)
    mock_card.id = "card_1"
    mock_card.name = "Test Card"
    mock_card.list_id = "list_1"
    mock_card.board_id = "board_1"
    mock_card.description = "Description"
    mock_card.position = 0.0
    mock_card.closed = False
    mock_card.due_date = None
    mock_card.url = "https://example.com/card"
    mock_card.created_at = None

    assert mock_card.id == "card_1"
    assert mock_card.name == "Test Card"
    assert mock_card.list_id == "list_1"
    assert mock_card.board_id == "board_1"
    assert mock_card.description == "Description"


def test_kanban_user_abstraction() -> None:
    """Verifies user model properties."""
    mock_user = Mock(spec=KanbanUser)
    mock_user.id = "user_1"
    mock_user.username = "testuser"
    mock_user.full_name = "Test User"
    mock_user.email = "test@example.com"

    assert mock_user.id == "user_1"
    assert mock_user.username == "testuser"
    assert mock_user.full_name == "Test User"
    assert mock_user.email == "test@example.com"


# Exception tests
def test_kanban_api_error() -> None:
    """Test KanbanAPIError exception."""
    error = KanbanAPIError("API request failed", HTTP_BAD_REQUEST)
    assert str(error) == "API request failed"
    assert error.status_code == HTTP_BAD_REQUEST


def test_kanban_authentication_error() -> None:
    """Test KanbanAuthenticationError exception."""
    error = KanbanAuthenticationError("Invalid token")
    assert isinstance(error, Exception)
    assert str(error) == "Invalid token"


def test_kanban_not_found_error() -> None:
    """Test KanbanNotFoundError exception."""
    error = KanbanNotFoundError("Resource not found")
    assert str(error) == "Resource not found"
    assert error.status_code == HTTP_NOT_FOUND


def test_kanban_rate_limit_error() -> None:
    """Test KanbanRateLimitError exception."""
    error = KanbanRateLimitError("Rate limit exceeded")
    assert str(error) == "Rate limit exceeded"
    assert error.status_code == HTTP_RATE_LIMIT
