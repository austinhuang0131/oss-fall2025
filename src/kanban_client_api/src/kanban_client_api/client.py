"""Abstract Kanban client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import KanbanBoard, KanbanCard, KanbanList, KanbanUser


class KanbanClient(ABC):
    """Abstract interface for Kanban client operations."""

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
