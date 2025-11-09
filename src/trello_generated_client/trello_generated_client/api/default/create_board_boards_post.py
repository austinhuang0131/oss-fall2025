from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.kanban_board import KanbanBoard
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    name: str,
    description: None | str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["name"] = name

    json_description: None | str | Unset
    if isinstance(description, Unset):
        json_description = UNSET
    else:
        json_description = description
    params["description"] = json_description

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/boards",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | HTTPValidationError | KanbanBoard | None:
    if response.status_code == 200:
        response_200 = KanbanBoard.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | HTTPValidationError | KanbanBoard]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    name: str,
    description: None | str | Unset = UNSET,
) -> Response[ErrorResponse | HTTPValidationError | KanbanBoard]:
    """Create Board

     Create a new board.

    Args:
        name (str):
        description (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | HTTPValidationError | KanbanBoard]
    """

    kwargs = _get_kwargs(
        name=name,
        description=description,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    name: str,
    description: None | str | Unset = UNSET,
) -> ErrorResponse | HTTPValidationError | KanbanBoard | None:
    """Create Board

     Create a new board.

    Args:
        name (str):
        description (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | HTTPValidationError | KanbanBoard
    """

    return sync_detailed(
        client=client,
        name=name,
        description=description,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    name: str,
    description: None | str | Unset = UNSET,
) -> Response[ErrorResponse | HTTPValidationError | KanbanBoard]:
    """Create Board

     Create a new board.

    Args:
        name (str):
        description (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | HTTPValidationError | KanbanBoard]
    """

    kwargs = _get_kwargs(
        name=name,
        description=description,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    name: str,
    description: None | str | Unset = UNSET,
) -> ErrorResponse | HTTPValidationError | KanbanBoard | None:
    """Create Board

     Create a new board.

    Args:
        name (str):
        description (None | str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | HTTPValidationError | KanbanBoard
    """

    return (
        await asyncio_detailed(
            client=client,
            name=name,
            description=description,
        )
    ).parsed
