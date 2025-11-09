"""Tests for the KanbanClientAdapter."""

from kanban_client_adapter.adapter import KanbanClientAdapter


def test_adapter_initialization() -> None:
    """Test adapter initialization with base URL."""
    client = KanbanClientAdapter(base_url="http://localhost:9000")
    assert client is not None


def test_adapter_default_base_url() -> None:
    """Test adapter initialization with default base URL."""
    client = KanbanClientAdapter()
    assert client is not None


def test_adapter_has_required_methods() -> None:
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


def test_adapter_with_custom_url() -> None:
    """Test adapter initialization with custom base URL."""
    custom_url = "http://custom.example.com:3000"
    client = KanbanClientAdapter(base_url=custom_url)
    assert client is not None
    # Verify internal client is created
    assert hasattr(client, "_client")
