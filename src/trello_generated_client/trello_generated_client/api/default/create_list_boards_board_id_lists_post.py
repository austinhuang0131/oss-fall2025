from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.error_response import ErrorResponse
from ...models.http_validation_error import HTTPValidationError
from ...models.kanban_list import KanbanList
from ...types import UNSET, Response


def _get_kwargs(
    board_id: str,
    *,
    name: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["name"] = name

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/boards/{board_id}/lists",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ErrorResponse | HTTPValidationError | KanbanList | None:
    if response.status_code == 200:
        response_200 = KanbanList.from_dict(response.json())

        return response_200

    if response.status_code == 400:
        response_400 = ErrorResponse.from_dict(response.json())

        return response_400

    if response.status_code == 401:
        response_401 = ErrorResponse.from_dict(response.json())

        return response_401

    if response.status_code == 404:
        response_404 = ErrorResponse.from_dict(response.json())

        return response_404

    if response.status_code == 422:
        response_422 = HTTPValidationError.from_dict(response.json())

        return response_422

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ErrorResponse | HTTPValidationError | KanbanList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    name: str,
) -> Response[ErrorResponse | HTTPValidationError | KanbanList]:
    """Create List

     Create a new list in a board.

    Args:
        board_id (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | HTTPValidationError | KanbanList]
    """

    kwargs = _get_kwargs(
        board_id=board_id,
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    name: str,
) -> ErrorResponse | HTTPValidationError | KanbanList | None:
    """Create List

     Create a new list in a board.

    Args:
        board_id (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | HTTPValidationError | KanbanList
    """

    return sync_detailed(
        board_id=board_id,
        client=client,
        name=name,
    ).parsed


async def asyncio_detailed(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    name: str,
) -> Response[ErrorResponse | HTTPValidationError | KanbanList]:
    """Create List

     Create a new list in a board.

    Args:
        board_id (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ErrorResponse | HTTPValidationError | KanbanList]
    """

    kwargs = _get_kwargs(
        board_id=board_id,
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
    name: str,
) -> ErrorResponse | HTTPValidationError | KanbanList | None:
    """Create List

     Create a new list in a board.

    Args:
        board_id (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ErrorResponse | HTTPValidationError | KanbanList
    """

    return (
        await asyncio_detailed(
            board_id=board_id,
            client=client,
            name=name,
        )
    ).parsed
