from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_board_boards_board_id_delete_response_delete_board_boards_board_id_delete import (
    DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete,
)
from ...models.error_response import ErrorResponse
from ...models.http_validation_error import HTTPValidationError
from ...types import Response


def _get_kwargs(
    board_id: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/boards/{board_id}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError | None:
    if response.status_code == 200:
        response_200 = DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete.from_dict(response.json())

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
) -> Response[
    DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError
]:
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
) -> Response[
    DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError
]:
    """Delete Board

     Delete a board.

    Args:
        board_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        board_id=board_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError | None:
    """Delete Board

     Delete a board.

    Args:
        board_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError
    """

    return sync_detailed(
        board_id=board_id,
        client=client,
    ).parsed


async def asyncio_detailed(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> Response[
    DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError
]:
    """Delete Board

     Delete a board.

    Args:
        board_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError]
    """

    kwargs = _get_kwargs(
        board_id=board_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    board_id: str,
    *,
    client: AuthenticatedClient | Client,
) -> DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError | None:
    """Delete Board

     Delete a board.

    Args:
        board_id (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeleteBoardBoardsBoardIdDeleteResponseDeleteBoardBoardsBoardIdDelete | ErrorResponse | HTTPValidationError
    """

    return (
        await asyncio_detailed(
            board_id=board_id,
            client=client,
        )
    ).parsed
