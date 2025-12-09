"""Concrete models for Trello implementation of Ticket ABC."""

from tickets_api.src.tickets_api import Ticket, TicketStatus


class TrelloTicket(Ticket):
    """Concrete implementation of Ticket for Trello."""

    def __init__(
        self,
        ticket_id: str,
        title: str,
        description: str,
        status: TicketStatus,
        assignee: str | None,
    ) -> None:
        """Initialize TrelloTicket.

        Args:
            ticket_id: Unique identifier for the ticket (Trello card ID).
            title: Title of the ticket.
            description: Description of the ticket.
            status: Status of the ticket (False = Open/To Do, True = Done).
            assignee: ID of the user assigned to the ticket, if any.

        """
        self._id: str = ticket_id
        self._title: str = title
        self._description: str = description
        self._status: TicketStatus = status
        self._assignee: str | None = assignee

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
    def status(self) -> TicketStatus:
        """The status of the ticket."""
        return self._status

    @property
    def assignee(self) -> str | None:
        """The assignee of the ticket."""
        return self._assignee
