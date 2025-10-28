"""Exception classes for Trello client API."""


class TrelloError(Exception):
    """Base exception for Trello client errors."""


class TrelloAPIError(TrelloError):
    """Exception raised when the Trello API returns an error."""
    
    def __init__(self, message: str, status_code: int | None = None) -> None:
        """Initialize TrelloAPIError.
        
        Args:
            message: Error message.
            status_code: HTTP status code if available.
        """
        super().__init__(message)
        self.status_code = status_code


class TrelloAuthenticationError(TrelloError):
    """Exception raised when authentication fails."""


class TrelloNotFoundError(TrelloAPIError):
    """Exception raised when a requested resource is not found."""
    
    def __init__(self, message: str) -> None:
        """Initialize TrelloNotFoundError.
        
        Args:
            message: Error message.
        """
        super().__init__(message, 404)


class TrelloRateLimitError(TrelloAPIError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, message: str) -> None:
        """Initialize TrelloRateLimitError.
        
        Args:
            message: Error message.
        """
        super().__init__(message, 429)
