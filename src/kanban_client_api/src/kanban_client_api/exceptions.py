"""Exception classes for Kanban client API."""


class KanbanError(Exception):
    """Base exception for Kanban client errors."""


class KanbanAPIError(KanbanError):
    """Exception raised when the Kanban API returns an error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize KanbanAPIError.

        Args:
            message: Error message.
            status_code: HTTP status code if available.

        """
        self.status_code: int | None
        super().__init__(message)
        self.status_code = status_code


class KanbanAuthenticationError(KanbanError):
    """Exception raised when authentication fails."""


class KanbanNotFoundError(KanbanAPIError):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str) -> None:
        """Initialize KanbanNotFoundError.

        Args:
            message: Error message.

        """
        super().__init__(message, 404)


class KanbanRateLimitError(KanbanAPIError):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str) -> None:
        """Initialize KanbanRateLimitError.

        Args:
            message: Error message.

        """
        super().__init__(message, 429)
