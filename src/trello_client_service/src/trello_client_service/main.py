"""FastAPI service for Trello client operations."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Body, Depends, FastAPI, HTTPException, Request, Response
from trello_client_api import (
    TrelloAPIError,
    TrelloAuthenticationError,
    TrelloBoard,
    TrelloCard,
    TrelloClient,
    TrelloList,
    TrelloNotFoundError,
    TrelloUser,
)
from trello_client_impl import TrelloClientImpl, TrelloOAuthHandler

# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # If python-dotenv is not available, check if .env file exists
    # and manually load it
    env_path = Path(".env")
    if env_path.exists():
        with env_path.open() as f:
            for raw_line in f:
                line = raw_line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    """Handle application startup and shutdown."""
    # Startup
    yield
    # Shutdown - could close database connections here


app = FastAPI(
    title="Trello Client Service",
    description="A service for interacting with Trello boards, lists, and cards",
    version="0.1.0",
    lifespan=lifespan,
)


def get_trello_client(request: Request) -> TrelloClient:
    """Dependency to get Trello client instance from cookie or Authorization header."""
    token = None
    # Prefer Authorization header (Bearer)
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header[7:]
    elif "trello_token" in request.cookies:
        token = request.cookies["trello_token"]
    else:
        # Try query param for backward compatibility
        token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing Trello token")
    return TrelloClientImpl.from_env(token=token)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# OAuth endpoints
@app.get("/auth/login")
async def login() -> dict[str, str]:
    """Start OAuth login flow.

    Returns:
        dict: Authorization URL

    """
    try:
        oauth_handler = TrelloOAuthHandler.from_env()
        auth_url = oauth_handler.get_authorization_url()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}") from e
    else:
        return {
            "authorization_url": auth_url,
        }


# Serve the OAuth callback page that parses the fragment and POSTs to /auth/callback
@app.get("/auth/callback_page")
async def auth_callback_page() -> Response:
    """Serve a page that parses the token from the fragment and POSTs to /auth/callback."""
    html = """
    <!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <title>Trello OAuth Callback</title>
        <style>
            body { font-family: sans-serif; margin: 2em; }
            #status { margin-top: 1em; }
        </style>
    </head>
    <body>
        <h2>Authenticating with Trello...</h2>
        <div id='status'>Waiting for token...</div>
        <script>
        function getFragmentParams() {
            const hash = window.location.hash.substring(1);
            const params = {};
            hash.split('&').forEach(pair => {
                const [key, value] = pair.split('=');
                if (key) params[key] = decodeURIComponent(value || '');
            });
            return params;
        }
        async function sendToken(token) {
            const res = await fetch('/auth/callback', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token })
            });
            if (res.ok) {
                document.getElementById('status').textContent = 'Authentication successful!';
            } else {
                const err = await res.text();
                document.getElementById('status').textContent = 'Error: ' + err;
            }
        }
        window.onload = function() {
            const params = getFragmentParams();
            if (params.token) {
                document.getElementById('status').textContent = 'Token found, sending to server...';
                sendToken(params.token);
            } else {
                document.getElementById('status').textContent = 'No token found in fragment.';
            }
        };
        </script>
    </body>
    </html>
    """
    return Response(content=html, media_type="text/html")

# Change /auth/callback to POST and accept token in body
@app.post("/auth/callback")
async def auth_callback(
    response: Response,
    token: Annotated[str, Body(embed=True)],
) -> dict[str, str]:
    """Handle OAuth callback via POST from JS page.

    Args:
        response: FastAPI response object
        token: OAuth token from Trello

    Returns:
        dict: Success message and token

    """
    try:
        oauth_handler = TrelloOAuthHandler.from_env()
        # Exchange token for credentials
        access_token = await oauth_handler.exchange_token(token)
        # Set token in cookie
        response.set_cookie(key="trello_token", value=access_token, httponly=True, secure=True)
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    return {"message": "Authentication successful", "token": access_token}


# User endpoints
@app.get("/users/me")
async def get_current_user(
    client: Annotated[TrelloClient, Depends(get_trello_client)],
) -> TrelloUser:
    """Get current authenticated user."""
    try:
        return await client.get_current_user()
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


# Board endpoints
@app.get("/boards")
async def get_boards(
    client: Annotated[TrelloClient, Depends(get_trello_client)],
) -> list[TrelloBoard]:
    """Get all boards accessible to the current user."""
    try:
        return await client.get_boards()
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.get("/boards/{board_id}")
async def get_board(
    board_id: str,
    client: Annotated[TrelloClient, Depends(get_trello_client)],
) -> TrelloBoard:
    """Get a specific board by ID."""
    try:
        return await client.get_board(board_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.post("/boards")
async def create_board(
    client: Annotated[TrelloClient, Depends(get_trello_client)],
    name: str,
    description: str | None = None,
) -> TrelloBoard:
    """Create a new board."""
    try:
        return await client.create_board(name, description)
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.put("/boards/{board_id}")
async def update_board(
    client: Annotated[TrelloClient, Depends(get_trello_client)],
    board_id: str,
    name: str | None = None,
    description: str | None = None,
) -> TrelloBoard:
    """Update an existing board."""
    try:
        return await client.update_board(board_id, name, description)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.delete("/boards/{board_id}")
async def delete_board(
    board_id: str,
    client: Annotated[TrelloClient, Depends(get_trello_client)],
) -> dict[str, bool]:
    """Delete a board."""
    try:
        success = await client.delete_board(board_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    else:
        return {"success": success}


# List endpoints
@app.get("/boards/{board_id}/lists")
async def get_lists(
    board_id: str,
    client: Annotated[TrelloClient, Depends(get_trello_client)],
) -> list[TrelloList]:
    """Get all lists in a board."""
    try:
        return await client.get_lists(board_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.post("/boards/{board_id}/lists")
async def create_list(
    board_id: str,
    name: str,
    client: Annotated[TrelloClient, Depends(get_trello_client)],
) -> TrelloList:
    """Create a new list in a board."""
    try:
        return await client.create_list(board_id, name)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.put("/lists/{list_id}")
async def update_list(
    client: Annotated[TrelloClient, Depends(get_trello_client)],
    list_id: str,
    name: str | None = None,
) -> TrelloList:
    """Update an existing list."""
    try:
        return await client.update_list(list_id, name)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


# Card endpoints
@app.get("/lists/{list_id}/cards")
async def get_cards(
    list_id: str,
    client: Annotated[TrelloClient, Depends(get_trello_client)],
) -> list[TrelloCard]:
    """Get all cards in a list."""
    try:
        return await client.get_cards(list_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.get("/cards/{card_id}")
async def get_card(
    card_id: str,
    client: Annotated[TrelloClient, Depends(get_trello_client)],
) -> TrelloCard:
    """Get a specific card by ID."""
    try:
        return await client.get_card(card_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.post("/lists/{list_id}/cards")
async def create_card(
    client: Annotated[TrelloClient, Depends(get_trello_client)],
    list_id: str,
    name: str,
    description: str | None = None,
) -> TrelloCard:
    """Create a new card in a list."""
    try:
        return await client.create_card(list_id, name, description)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.put("/cards/{card_id}")
async def update_card(
    client: Annotated[TrelloClient, Depends(get_trello_client)],
    card_id: str,
    name: str | None = None,
    description: str | None = None,
    list_id: str | None = None,
) -> TrelloCard:
    """Update an existing card."""
    try:
        return await client.update_card(card_id, name, description, list_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None


@app.delete("/cards/{card_id}")
async def delete_card(
    card_id: str,
    client: Annotated[TrelloClient, Depends(get_trello_client)],
) -> dict[str, bool]:
    """Delete a card."""
    try:
        success = await client.delete_card(card_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from None
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e)) from None
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e)) from None
    else:
        return {"success": success}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
