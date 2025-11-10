"""Concrete models for Trello implementation of Kanban ABCs."""

from datetime import datetime

from kanban_client_api.models import KanbanBoard, KanbanCard, KanbanList, KanbanUser


class TrelloBoard(KanbanBoard):
    """Concrete implementation of KanbanBoard for Trello."""

    def __init__(
        self,
        board_id: str,
        name: str,
        description: str | None = None,
        *,
        closed: bool = False,
        url: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """Initialize TrelloBoard.

        Args:
            board_id: Unique identifier for the board.
            name: Name of the board.
            description: Board description.
            closed: Whether the board is closed.
            url: Board URL.
            created_at: Creation time.

        """
        self._id: str = board_id
        self._name: str = name
        self._description: str | None = description
        self._closed: bool = closed
        self._url: str | None = url
        self._created_at: datetime | None = created_at

    @property
    def id(self) -> str:
        """The unique identifier for the board."""
        return self._id

    @property
    def name(self) -> str:
        """The name of the board."""
        return self._name

    @property
    def description(self) -> str | None:
        """The description of the board."""
        return self._description

    @property
    def closed(self) -> bool:
        """Whether the board is closed."""
        return self._closed

    @property
    def url(self) -> str | None:
        """The URL of the board."""
        return self._url

    @property
    def created_at(self) -> datetime | None:
        """The creation time of the board."""
        return self._created_at

class TrelloList(KanbanList):
    """Concrete implementation of KanbanList for Trello."""

    def __init__(
        self,
        list_id: str,
        name: str,
        board_id: str,
        position: float,
        *,
        closed: bool = False,
    ) -> None:
        """Initialize TrelloList.

        Args:
            list_id: Unique identifier for the list.
            name: Name of the list.
            board_id: Board ID.
            position: List position.
            closed: Whether the list is closed.

        """
        self._id: str = list_id
        self._name: str = name
        self._board_id: str = board_id
        self._position: float = position
        self._closed: bool = closed

    @property
    def id(self) -> str:
        """The unique identifier for the list."""
        return self._id

    @property
    def name(self) -> str:
        """The name of the list."""
        return self._name

    @property
    def board_id(self) -> str:
        """The ID of the board this list belongs to."""
        return self._board_id

    @property
    def position(self) -> float:
        """The position of the list in the board."""
        return self._position

    @property
    def closed(self) -> bool:
        """Whether the list is closed."""
        return self._closed

class TrelloCard(KanbanCard):
    """Concrete implementation of KanbanCard for Trello."""

    def __init__(
        self,
        card_id: str,
        name: str,
        list_id: str,
        board_id: str,
        description: str | None = None,
        position: float = 0.0,
        *,
        closed: bool = False,
        due_date: datetime | None = None,
        url: str | None = None,
        created_at: datetime | None = None,
    ) -> None:
        """Initialize TrelloCard.

        Args:
            card_id: Unique identifier for the card.
            name: Name of the card.
            list_id: List ID.
            board_id: Board ID.
            description: Card description.
            position: Card position.
            closed: Whether the card is closed.
            due_date: Due date.
            url: Card URL.
            created_at: Creation time.

        """
        self._id: str = card_id
        self._name: str = name
        self._list_id: str = list_id
        self._board_id: str = board_id
        self._description: str | None = description
        self._position: float = position
        self._closed: bool = closed
        self._due_date: datetime | None = due_date
        self._url: str | None = url
        self._created_at: datetime | None = created_at

    @property
    def id(self) -> str:
        """The unique identifier for the card."""
        return self._id

    @property
    def name(self) -> str:
        """The name of the card."""
        return self._name

    @property
    def list_id(self) -> str:
        """The ID of the list this card belongs to."""
        return self._list_id

    @property
    def board_id(self) -> str:
        """The ID of the board this card belongs to."""
        return self._board_id

    @property
    def description(self) -> str | None:
        """The description of the card."""
        return self._description

    @property
    def position(self) -> float:
        """The position of the card in the list."""
        return self._position

    @property
    def closed(self) -> bool:
        """Whether the card is closed."""
        return self._closed

    @property
    def due_date(self) -> datetime | None:
        """The due date of the card."""
        return self._due_date

    @property
    def url(self) -> str | None:
        """The URL of the card."""
        return self._url

    @property
    def created_at(self) -> datetime | None:
        """The creation time of the card."""
        return self._created_at

class TrelloUser(KanbanUser):
    """Concrete implementation of KanbanUser for Trello."""

    def __init__(
        self,
        user_id: str,
        username: str,
        full_name: str | None = None,
        email: str | None = None,
    ) -> None:
        """Initialize TrelloUser.

        Args:
            user_id: Unique identifier for the user.
            username: Username.
            full_name: Full name.
            email: Email address.

        """
        self._id: str = user_id
        self._username: str = username
        self._full_name: str | None = full_name
        self._email: str | None = email

    @property
    def id(self) -> str:
        """The unique identifier for the user."""
        return self._id

    @property
    def username(self) -> str:
        """The username of the user."""
        return self._username

    @property
    def full_name(self) -> str | None:
        """The full name of the user."""
        return self._full_name

    @property
    def email(self) -> str | None:
        """The email address of the user."""
        return self._email
