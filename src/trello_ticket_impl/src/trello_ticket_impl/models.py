"""Concrete models for Trello implementation of Ticket ABC."""

from ticket_api.models import Ticket


class TrelloTicket(Ticket):
    """Concrete implementation of Ticket for Trello."""

    def __init__(
        self,
        ticket_id: str,
        title: str,
        description: str,
        status: bool,
    ) -> None:
        """Initialize TrelloTicket.

        Args:
            ticket_id: Unique identifier for the ticket (Trello card ID).
            title: Title of the ticket.
            description: Description of the ticket.
            status: Status of the ticket (False = Open/To Do, True = Done).

        """
        self._id: str = ticket_id
        self._title: str = title
        self._description: str = description
        self._status: bool = status

    @property
    def id(self) -> str:
        """The unique identifier for the ticket."""
        return self._id

    @property
    def title(self) -> str:
        """The title of the ticket."""
        return self._title

    @property
    def description(self) -> str:
        """The description of the ticket."""
        return self._description

    @property
    def status(self) -> bool:
        """The status of the ticket.

        False = Open / To Do
        True = Done / Completed
        """
        return self._status
