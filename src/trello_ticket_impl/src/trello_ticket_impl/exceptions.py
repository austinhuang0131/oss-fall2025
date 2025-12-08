"""Exceptions for the Ticket API."""


class TrelloAPIError(Exception):
    """Base exception for Ticket API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize TicketAPIError.

        Args:
            message: Error message
            status_code: HTTP status code if applicable

        """
        super().__init__(message)
        self.status_code = status_code


class TrelloNotFoundError(TrelloAPIError):
    """Exception raised when a ticket is not found."""


class TrelloAuthenticationError(TrelloAPIError):
    """Exception raised when authentication fails."""
