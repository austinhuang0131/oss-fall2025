"""Exceptions for the Ticket API."""


class TicketAPIError(Exception):
    """Base exception for Ticket API errors."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize TicketAPIError.

        Args:
            message: Error message
            status_code: HTTP status code if applicable

        """
        super().__init__(message)
        self.status_code = status_code


class TicketNotFoundError(TicketAPIError):
    """Exception raised when a ticket is not found."""


class TicketAuthenticationError(TicketAPIError):
    """Exception raised when authentication fails."""
