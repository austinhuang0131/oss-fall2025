"""Abstract Trello client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import TrelloBoard, TrelloCard, TrelloList, TrelloUser


class TrelloClient(ABC):
    """Abstract interface for Trello client operations."""

    # User operations
    @abstractmethod
    async def get_current_user(self) -> TrelloUser:
        """Get the current authenticated user.
        
        Returns:
            TrelloUser: The current user information.
            
        Raises:
            TrelloAuthenticationError: If authentication fails.
            TrelloAPIError: If the API request fails.
        """

    # Board operations
    @abstractmethod
    async def get_boards(self) -> List[TrelloBoard]:
        """Get all boards accessible to the current user.
        
        Returns:
            List[TrelloBoard]: List of user's boards.
            
        Raises:
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def get_board(self, board_id: str) -> TrelloBoard:
        """Get a specific board by ID.
        
        Args:
            board_id: The ID of the board to retrieve.
            
        Returns:
            TrelloBoard: The requested board.
            
        Raises:
            TrelloNotFoundError: If the board doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def create_board(
        self, 
        name: str, 
        description: Optional[str] = None
    ) -> TrelloBoard:
        """Create a new board.
        
        Args:
            name: The name of the board.
            description: Optional description for the board.
            
        Returns:
            TrelloBoard: The created board.
            
        Raises:
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def update_board(
        self, 
        board_id: str, 
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> TrelloBoard:
        """Update an existing board.
        
        Args:
            board_id: The ID of the board to update.
            name: New name for the board (optional).
            description: New description for the board (optional).
            
        Returns:
            TrelloBoard: The updated board.
            
        Raises:
            TrelloNotFoundError: If the board doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def delete_board(self, board_id: str) -> bool:
        """Delete a board.
        
        Args:
            board_id: The ID of the board to delete.
            
        Returns:
            bool: True if deletion was successful.
            
        Raises:
            TrelloNotFoundError: If the board doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    # List operations
    @abstractmethod
    async def get_lists(self, board_id: str) -> List[TrelloList]:
        """Get all lists in a board.
        
        Args:
            board_id: The ID of the board.
            
        Returns:
            List[TrelloList]: List of lists in the board.
            
        Raises:
            TrelloNotFoundError: If the board doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def create_list(self, board_id: str, name: str) -> TrelloList:
        """Create a new list in a board.
        
        Args:
            board_id: The ID of the board.
            name: The name of the list.
            
        Returns:
            TrelloList: The created list.
            
        Raises:
            TrelloNotFoundError: If the board doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def update_list(
        self, 
        list_id: str, 
        name: Optional[str] = None
    ) -> TrelloList:
        """Update an existing list.
        
        Args:
            list_id: The ID of the list to update.
            name: New name for the list (optional).
            
        Returns:
            TrelloList: The updated list.
            
        Raises:
            TrelloNotFoundError: If the list doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    # Card operations
    @abstractmethod
    async def get_cards(self, list_id: str) -> List[TrelloCard]:
        """Get all cards in a list.
        
        Args:
            list_id: The ID of the list.
            
        Returns:
            List[TrelloCard]: List of cards in the list.
            
        Raises:
            TrelloNotFoundError: If the list doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def get_card(self, card_id: str) -> TrelloCard:
        """Get a specific card by ID.
        
        Args:
            card_id: The ID of the card to retrieve.
            
        Returns:
            TrelloCard: The requested card.
            
        Raises:
            TrelloNotFoundError: If the card doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def create_card(
        self,
        list_id: str,
        name: str,
        description: Optional[str] = None
    ) -> TrelloCard:
        """Create a new card in a list.
        
        Args:
            list_id: The ID of the list.
            name: The name of the card.
            description: Optional description for the card.
            
        Returns:
            TrelloCard: The created card.
            
        Raises:
            TrelloNotFoundError: If the list doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def update_card(
        self,
        card_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        list_id: Optional[str] = None
    ) -> TrelloCard:
        """Update an existing card.
        
        Args:
            card_id: The ID of the card to update.
            name: New name for the card (optional).
            description: New description for the card (optional).
            list_id: Move card to different list (optional).
            
        Returns:
            TrelloCard: The updated card.
            
        Raises:
            TrelloNotFoundError: If the card doesn't exist.
            TrelloAPIError: If the API request fails.
        """

    @abstractmethod
    async def delete_card(self, card_id: str) -> bool:
        """Delete a card.
        
        Args:
            card_id: The ID of the card to delete.
            
        Returns:
            bool: True if deletion was successful.
            
        Raises:
            TrelloNotFoundError: If the card doesn't exist.
            TrelloAPIError: If the API request fails.
        """
