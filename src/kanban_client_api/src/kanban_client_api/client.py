"""Abstract Kanban client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import KanbanBoard, KanbanCard, KanbanList, KanbanUser


class KanbanClient(ABC):
    """Abstract interface for Kanban client operations."""

    # List operations
    @abstractmethod
    async def get_lists(self, board_id: str) -> list[KanbanList]:
        """Get all lists in a board.

        Args:
            board_id: The ID of the board to retrieve lists from.

        Returns:
            List[KanbanList]: List of lists in the board.

        Raises:
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def create_list(self, board_id: str, name: str) -> KanbanList:
        """Create a new list in a board.

        Args:
            board_id: The ID of the board to add the list to.
            name: The name of the new list.

        Returns:
            KanbanList: The created list.

        Raises:
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def update_list(
        self,
        list_id: str,
        name: str | None = None,
    ) -> KanbanList:
        """Update an existing list.

        Args:
            list_id: The ID of the list to update.
            name: New name for the list (optional).

        Returns:
            KanbanList: The updated list.

        Raises:
            KanbanNotFoundError: If the list doesn't exist.
            KanbanAPIError: If the API request fails.

        """

    # Card operations
    @abstractmethod
    async def get_cards(self, list_id: str) -> list[KanbanCard]:
        """Get all cards in a list.

        Args:
            list_id: The ID of the list to retrieve cards from.

        Returns:
            List[KanbanCard]: List of cards in the list.

        Raises:
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def get_card(self, card_id: str) -> KanbanCard:
        """Get a specific card by ID.

        Args:
            card_id: The ID of the card to retrieve.

        Returns:
            KanbanCard: The requested card.

        Raises:
            KanbanNotFoundError: If the card doesn't exist.
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def create_card(
        self,
        list_id: str,
        name: str,
        description: str | None = None,
    ) -> KanbanCard:
        """Create a new card in a list.

        Args:
            list_id: The ID of the list to add the card to.
            name: The name of the new card.
            description: Optional description for the card.

        Returns:
            KanbanCard: The created card.

        Raises:
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def update_card(
        self,
        card_id: str,
        name: str | None = None,
        description: str | None = None,
        list_id: str | None = None,
    ) -> KanbanCard:
        """Update an existing card.

        Args:
            card_id: The ID of the card to update.
            name: New name for the card (optional).
            description: New description for the card (optional).
            list_id: Move card to another list (optional).

        Returns:
            KanbanCard: The updated card.

        Raises:
            KanbanNotFoundError: If the card doesn't exist.
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def delete_card(self, card_id: str) -> bool:
        """Delete a card.

        Args:
            card_id: The ID of the card to delete.

        Returns:
            bool: True if deletion was successful.

        Raises:
            KanbanNotFoundError: If the card doesn't exist.
            KanbanAPIError: If the API request fails.

        """

    # User operations
    @abstractmethod
    async def get_current_user(self) -> KanbanUser:
        """Get the current authenticated user.

        Returns:
            KanbanUser: The current user information.

        Raises:
            KanbanAuthenticationError: If authentication fails.
            KanbanAPIError: If the API request fails.

        """

    # Board operations
    @abstractmethod
    async def get_boards(self) -> list[KanbanBoard]:
        """Get all boards accessible to the current user.

        Returns:
            List[KanbanBoard]: List of user's boards.

        Raises:
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def get_board(self, board_id: str) -> KanbanBoard:
        """Get a specific board by ID.

        Args:
            board_id: The ID of the board to retrieve.

        Returns:
            KanbanBoard: The requested board.

        Raises:
            KanbanNotFoundError: If the board doesn't exist.
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def create_board(
        self,
        name: str,
        description: str | None = None,
    ) -> KanbanBoard:
        """Create a new board.

        Args:
            name: The name of the board.
            description: Optional description for the board.

        Returns:
            KanbanBoard: The created board.

        Raises:
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def update_board(
        self,
        board_id: str,
        name: str | None = None,
        description: str | None = None,
    ) -> KanbanBoard:
        """Update an existing board.

        Args:
            board_id: The ID of the board to update.
            name: New name for the board (optional).
            description: New description for the board (optional).

        Returns:
            KanbanBoard: The updated board.

        Raises:
            KanbanNotFoundError: If the board doesn't exist.
            KanbanAPIError: If the API request fails.

        """

    @abstractmethod
    async def delete_board(self, board_id: str) -> bool:
        """Delete a board.

        Args:
            board_id: The ID of the board to delete.

        Returns:
            bool: True if deletion was successful.

        Raises:
            KanbanNotFoundError: If the board doesn't exist.
            KanbanAPIError: If the API request fails.

        """
