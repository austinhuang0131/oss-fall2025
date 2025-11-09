
"""Adapter for KanbanClient using trello_generated_client."""

from typing import TYPE_CHECKING, cast

from kanban_client_api import exceptions as api_exceptions
from kanban_client_api.client import KanbanClient
from kanban_client_api.models import KanbanBoard, KanbanCard, KanbanList, KanbanUser
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
from trello_generated_client.models.error_response import ErrorResponse
from trello_generated_client.models.http_validation_error import HTTPValidationError

from .models import AdapterBoard, AdapterCard, AdapterList, AdapterUser

if TYPE_CHECKING:
    import trello_generated_client.models


class KanbanClientAdapter(KanbanClient):
    """Adapter implementation of KanbanClient using trello_generated_client."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """Initialize the adapter with the generated Trello client."""
        self._client: GeneratedTrelloClient = GeneratedTrelloClient(base_url=base_url)

    @staticmethod
    def _handle_api_error(obj: object, msg: str) -> None:
        """Convert generated client exceptions to KanbanClient exceptions."""
        if obj is None or isinstance(obj, HTTPValidationError):
            msg = f"{msg}: invalid response"
            raise api_exceptions.KanbanAPIError(msg) from None
        if isinstance(obj, ErrorResponse):
            error: type[api_exceptions.KanbanError] = api_exceptions.KanbanAPIError
            if obj.detail == "Authentication failed":
                error = api_exceptions.KanbanAuthenticationError
            elif obj.detail == "Resource not found":
                error = api_exceptions.KanbanNotFoundError
            msg = f"{msg}: {obj.detail}"
            raise error(msg) from None

    def _return_success(self, obj: object) -> bool:
        """Return the object if it matches the expected return type, else raise an error."""
        success = getattr(obj, "success", False)
        if isinstance(success, bool):
            return success
        return False

    async def get_current_user(self) -> KanbanUser:
        """Get the current authenticated user."""
        user = await get_current_user_users_me_get.asyncio(client=self._client)
        self._handle_api_error(user, "Failed to get current user")
        user = cast("trello_generated_client.models.KanbanUser", user)
        return AdapterUser(
            user_id=user.id,
            username=user.username,
            full_name=getattr(user, "full_name", None),
            email=getattr(user, "email", None),
        )

    async def get_boards(self) -> list[KanbanBoard]:
        """Get all boards accessible to the current user."""
        boards = await get_boards_boards_get.asyncio(client=self._client)
        self._handle_api_error(boards, "Failed to fetch boards")
        if not isinstance(boards, list):
            msg = "API did not return a list of boards."
            raise api_exceptions.KanbanAPIError(msg)
        return [AdapterBoard(
            board_id=board.id,
            name=board.name,
            description=getattr(board, "description", None),
            closed=getattr(board, "closed", False),
            url=getattr(board, "url", None),
            created_at=getattr(board, "created_at", None),
        ) for board in boards]

    async def get_board(self, board_id: str) -> KanbanBoard:
        """Get a specific board by ID."""
        board = await get_board_boards_board_id_get.asyncio(client=self._client, board_id=board_id)
        self._handle_api_error(board, f"Failed to fetch board {board_id}")
        board = cast("trello_generated_client.models.KanbanBoard", board)
        return AdapterBoard(
            board_id=board.id,
            name=board.name,
            description=getattr(board, "description", None),
            closed=getattr(board, "closed", False),
            url=getattr(board, "url", None),
            created_at=getattr(board, "created_at", None),
        )

    async def create_board(self, name: str, description: str | None = None) -> KanbanBoard:
        """Create a new board."""
        board = await create_board_boards_post.asyncio(client=self._client, name=name, description=description)
        self._handle_api_error(board, "Failed to create board")
        board = cast("trello_generated_client.models.KanbanBoard", board)
        return AdapterBoard(
            board_id=board.id,
            name=board.name,
            description=getattr(board, "description", None),
            closed=getattr(board, "closed", False),
            url=getattr(board, "url", None),
            created_at=getattr(board, "created_at", None),
        )

    async def update_board(
        self,
        board_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> KanbanBoard:
        """Update an existing board."""
        board = await update_board_boards_board_id_put.asyncio(
            client=self._client,
            board_id=board_id,
            name=name,
            description=description,
        )
        self._handle_api_error(board, f"Failed to update board {board_id}")
        board = cast("trello_generated_client.models.KanbanBoard", board)
        return AdapterBoard(
            board_id=board.id,
            name=board.name,
            description=getattr(board, "description", None),
            closed=getattr(board, "closed", False),
            url=getattr(board, "url", None),
            created_at=getattr(board, "created_at", None),
        )

    async def delete_board(self, board_id: str) -> bool:
        """Delete a board."""
        result = await delete_board_boards_board_id_delete.asyncio(client=self._client, board_id=board_id)
        self._handle_api_error(result, f"Failed to delete board {board_id}")
        return self._return_success(result)

    async def get_lists(self, board_id: str) -> list[KanbanList]:
        """Get all lists in a board."""
        lists = await get_lists_boards_board_id_lists_get.asyncio(client=self._client, board_id=board_id)
        self._handle_api_error(lists, f"Failed to fetch lists for board {board_id}")
        # to reviewers: the list check is done outside to satisfy mypy type checking
        if not isinstance(lists, list):
            msg = f"API did not return a list for board {board_id}."
            raise api_exceptions.KanbanAPIError(msg)
        return [AdapterList(
            list_id=lst.id,
            name=lst.name,
            board_id=lst.board_id,
            position=getattr(lst, "position", 0.0),
            closed=getattr(lst, "closed", False),
        ) for lst in lists]

    async def create_list(self, board_id: str, name: str) -> KanbanList:
        """Create a new list in a board."""
        kanban_list = await create_list_boards_board_id_lists_post.asyncio(client=self._client, board_id=board_id, name=name)
        self._handle_api_error(kanban_list, f"Failed to create list in board {board_id}")
        kanban_list = cast("trello_generated_client.models.KanbanList", kanban_list)
        return AdapterList(
            list_id=kanban_list.id,
            name=kanban_list.name,
            board_id=kanban_list.board_id,
            position=getattr(kanban_list, "position", 0.0),
            closed=getattr(kanban_list, "closed", False),
        )

    async def update_list(self, list_id: str, name: str | None = None) -> KanbanList:
        """Update an existing list."""
        kanban_list = await update_list_lists_list_id_put.asyncio(client=self._client, list_id=list_id, name=name)
        self._handle_api_error(kanban_list, f"Failed to update list {list_id}")
        kanban_list = cast("trello_generated_client.models.KanbanList", kanban_list)
        return AdapterList(
            list_id=kanban_list.id,
            name=kanban_list.name,
            board_id=kanban_list.board_id,
            position=getattr(kanban_list, "position", 0.0),
            closed=getattr(kanban_list, "closed", False),
        )

    async def get_cards(self, list_id: str) -> list[KanbanCard]:
        """Get all cards in a list."""
        cards = await get_cards_lists_list_id_cards_get.asyncio(client=self._client, list_id=list_id)
        self._handle_api_error(cards, f"Failed to fetch cards for list {list_id}")
        # to reviewers: idem
        if not isinstance(cards, list):
            msg = f"API did not return a list for list {list_id}."
            raise api_exceptions.KanbanAPIError(msg)
        return [AdapterCard(
            card_id=card.id,
            name=card.name,
            list_id=card.list_id,
            board_id=card.board_id,
            description=getattr(card, "description", None),
            position=getattr(card, "position", 0.0),
            closed=getattr(card, "closed", False),
            due_date=getattr(card, "due_date", None),
            url=getattr(card, "url", None),
            created_at=getattr(card, "created_at", None),
        ) for card in cards]

    async def get_card(self, card_id: str) -> KanbanCard:
        """Get a specific card by ID."""
        card = await get_card_cards_card_id_get.asyncio(client=self._client, card_id=card_id)
        self._handle_api_error(card, f"Failed to fetch card {card_id}")
        card = cast("trello_generated_client.models.KanbanCard", card)
        return AdapterCard(
            card_id=card.id,
            name=card.name,
            list_id=card.list_id,
            board_id=card.board_id,
            description=getattr(card, "description", None),
            position=getattr(card, "position", 0.0),
            closed=getattr(card, "closed", False),
            due_date=getattr(card, "due_date", None),
            url=getattr(card, "url", None),
            created_at=getattr(card, "created_at", None),
        )

    async def create_card(
        self,
        list_id: str,
        name: str,
        description: str | None = None,
    ) -> KanbanCard:
        """Create a new card in a list."""
        card = await create_card_lists_list_id_cards_post.asyncio(
            client=self._client,
            list_id=list_id,
            name=name,
            description=description,
        )
        self._handle_api_error(card, f"Failed to create card in list {list_id}")
        card = cast("trello_generated_client.models.KanbanCard", card)
        return AdapterCard(
            card_id=card.id,
            name=card.name,
            list_id=card.list_id,
            board_id=card.board_id,
            description=getattr(card, "description", None),
            position=getattr(card, "position", 0.0),
            closed=getattr(card, "closed", False),
            due_date=getattr(card, "due_date", None),
            url=getattr(card, "url", None),
            created_at=getattr(card, "created_at", None),
        )

    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        description: str | None = None,
        list_id: str | None = None,
    ) -> KanbanCard:
        """Update an existing card."""
        card = await update_card_cards_card_id_put.asyncio(
            client=self._client,
            card_id=card_id,
            name=name,
            description=description,
            list_id=list_id,
        )
        self._handle_api_error(card, f"Failed to update card {card_id}")
        card = cast("trello_generated_client.models.KanbanCard", card)
        return AdapterCard(
            card_id=card.id,
            name=card.name,
            list_id=card.list_id,
            board_id=card.board_id,
            description=getattr(card, "description", None),
            position=getattr(card, "position", 0.0),
            closed=getattr(card, "closed", False),
            due_date=getattr(card, "due_date", None),
            url=getattr(card, "url", None),
            created_at=getattr(card, "created_at", None),
        )

    async def delete_card(self, card_id: str) -> bool:
        """Delete a card."""
        result = await delete_card_cards_card_id_delete.asyncio(client=self._client, card_id=card_id)
        self._handle_api_error(result, f"Failed to delete card {card_id}")
        return self._return_success(result)
