"""Adapter for TrelloClient using trello_generated_client."""

from trello_client_api import exceptions as api_exceptions
from trello_client_api.client import TrelloClient
from trello_client_api.models import TrelloBoard, TrelloCard, TrelloList, TrelloUser

# Import generated API functions
from trello_generated_client.api.default import (
    create_board_boards_post,
    create_card_lists_list_id_cards_post,
    create_list_boards_board_id_lists_post,
    delete_board_boards_board_id_delete,
    delete_card_cards_card_id_delete,
    get_board_boards_board_id_get,
    get_boards_boards_get,
    get_card_cards_card_id_get,
    get_cards_lists_list_id_cards_get,
    get_current_user_users_me_get,
    get_lists_boards_board_id_lists_get,
    update_board_boards_board_id_put,
    update_card_cards_card_id_put,
    update_list_lists_list_id_put,
)
from trello_generated_client.client import Client as GeneratedTrelloClient


class TrelloClientAdapter(TrelloClient):
    """Adapter implementation of TrelloClient using trello_generated_client."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """Initialize the adapter with the generated Trello client."""
        self._client: GeneratedTrelloClient = GeneratedTrelloClient(base_url=base_url)

    async def get_current_user(self) -> TrelloUser:
        """Get the current authenticated user."""
        user = await get_current_user_users_me_get.asyncio(client=self._client)
        if user is None or hasattr(user, "detail"):
            msg = "Failed to authenticate user."
            raise api_exceptions.TrelloAuthenticationError(msg)
        return TrelloUser.from_generated(user)

    async def get_boards(self) -> list[TrelloBoard]:
        """Get all boards accessible to the current user."""
        boards = await get_boards_boards_get.asyncio(client=self._client)
        if not isinstance(boards, list):
            msg = "API did not return a list of boards."
            raise api_exceptions.TrelloAPIError(msg)
        return [TrelloBoard.from_generated(board) for board in boards]

    async def get_board(self, board_id: str) -> TrelloBoard:
        """Get a specific board by ID."""
        board = await get_board_boards_board_id_get.asyncio(client=self._client, board_id=board_id)
        if board is None:
            msg = f"Board {board_id} not found."
            raise api_exceptions.TrelloNotFoundError(msg)
        if hasattr(board, "detail"):
            msg = f"Failed to fetch board {board_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return TrelloBoard.from_generated(board)

    async def create_board(self, name: str, description: str | None = None) -> TrelloBoard:
        """Create a new board."""
        board = await create_board_boards_post.asyncio(client=self._client, name=name, description=description)
        if board is None or hasattr(board, "detail"):
            msg = "Failed to create board."
            raise api_exceptions.TrelloAPIError(msg)
        return TrelloBoard.from_generated(board)

    async def update_board(
        self,
        board_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> TrelloBoard:
        """Update an existing board."""
        board = await update_board_boards_board_id_put.asyncio(
            client=self._client,
            board_id=board_id,
            name=name,
            description=description,
        )
        if board is None:
            msg = f"Board {board_id} not found."
            raise api_exceptions.TrelloNotFoundError(msg)
        if hasattr(board, "detail"):
            msg = f"Failed to update board {board_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return TrelloBoard.from_generated(board)

    async def delete_board(self, board_id: str) -> bool:
        """Delete a board."""
        result = await delete_board_boards_board_id_delete.asyncio(client=self._client, board_id=board_id)
        if result is None:
            msg = f"Board {board_id} not found."
            raise api_exceptions.TrelloNotFoundError(msg)
        if hasattr(result, "detail"):
            msg = f"Failed to delete board {board_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return bool(result)

    async def get_lists(self, board_id: str) -> list[TrelloList]:
        """Get all lists in a board."""
        lists = await get_lists_boards_board_id_lists_get.asyncio(client=self._client, board_id=board_id)
        if not isinstance(lists, list):
            msg = f"API did not return a list for board {board_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return [TrelloList.from_generated(lst) for lst in lists]

    async def create_list(self, board_id: str, name: str) -> TrelloList:
        """Create a new list in a board."""
        trello_list = await create_list_boards_board_id_lists_post.asyncio(client=self._client, board_id=board_id, name=name)
        if trello_list is None or hasattr(trello_list, "detail"):
            msg = f"Failed to create list in board {board_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return TrelloList.from_generated(trello_list)

    async def update_list(self, list_id: str, name: str | None = None) -> TrelloList:
        """Update an existing list."""
        trello_list = await update_list_lists_list_id_put.asyncio(client=self._client, list_id=list_id, name=name)
        if trello_list is None:
            msg = f"List {list_id} not found."
            raise api_exceptions.TrelloNotFoundError(msg)
        if hasattr(trello_list, "detail"):
            msg = f"Failed to update list {list_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return TrelloList.from_generated(trello_list)

    async def get_cards(self, list_id: str) -> list[TrelloCard]:
        """Get all cards in a list."""
        cards = await get_cards_lists_list_id_cards_get.asyncio(client=self._client, list_id=list_id)
        if not isinstance(cards, list):
            msg = f"API did not return a list for list {list_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return [TrelloCard.from_generated(card) for card in cards]

    async def get_card(self, card_id: str) -> TrelloCard:
        """Get a specific card by ID."""
        card = await get_card_cards_card_id_get.asyncio(client=self._client, card_id=card_id)
        if card is None:
            msg = f"Card {card_id} not found."
            raise api_exceptions.TrelloNotFoundError(msg)
        if hasattr(card, "detail"):
            msg = f"Failed to fetch card {card_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return TrelloCard.from_generated(card)

    async def create_card(
        self,
        list_id: str,
        name: str,
        description: str | None = None,
    ) -> TrelloCard:
        """Create a new card in a list."""
        card = await create_card_lists_list_id_cards_post.asyncio(
            client=self._client,
            list_id=list_id,
            name=name,
            description=description,
        )
        if card is None or hasattr(card, "detail"):
            msg = f"Failed to create card in list {list_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return TrelloCard.from_generated(card)

    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        description: str | None = None,
        list_id: str | None = None,
    ) -> TrelloCard:
        """Update an existing card."""
        card = await update_card_cards_card_id_put.asyncio(
            client=self._client,
            card_id=card_id,
            name=name,
            description=description,
            list_id=list_id,
        )
        if card is None:
            msg = f"Card {card_id} not found."
            raise api_exceptions.TrelloNotFoundError(msg)
        if hasattr(card, "detail"):
            msg = f"Failed to update card {card_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return TrelloCard.from_generated(card)

    async def delete_card(self, card_id: str) -> bool:
        """Delete a card."""
        result = await delete_card_cards_card_id_delete.asyncio(client=self._client, card_id=card_id)
        if result is None:
            msg = f"Card {card_id} not found."
            raise api_exceptions.TrelloNotFoundError(msg)
        if hasattr(result, "detail"):
            msg = f"Failed to delete card {card_id}."
            raise api_exceptions.TrelloAPIError(msg)
        return bool(result)
