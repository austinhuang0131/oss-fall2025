
"""Defines common response schemas and models for Trello Client Service API endpoints."""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Basic error response."""

    detail: str


common_error_responses = {
    401: {
        "description": "Authentication error",
        "model": ErrorResponse,
        "content": {"application/json": {"example": "Authentication failed"}},
    },
    400: {
        "description": "API error",
        "model": ErrorResponse,
        "content": {"application/json": {"example": "API error"}},
    },
}

notfound_resource_response = {
    404: {
        "description": "Board not found",
        "model": ErrorResponse,
        "content": {"application/json": {"example": "Resource not found"}},
    },
}
