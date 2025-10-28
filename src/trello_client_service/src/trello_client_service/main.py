"""FastAPI service for Trello client operations."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
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
from trello_client_impl import TrelloClientImpl, TrelloOAuthHandler, UserCredential


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
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


def get_trello_client(user_id: Optional[str] = Query(None)) -> TrelloClient:
    """Dependency to get Trello client instance.
    
    Args:
        user_id: User ID for authentication
        
    Returns:
        TrelloClient: Configured client instance
        
    Raises:
        HTTPException: If client creation fails
    """
    try:
        return TrelloClientImpl.from_env(user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create client: {e}")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# OAuth endpoints
@app.get("/auth/login")
async def login(user_id: Optional[str] = Query(None)) -> dict[str, str]:
    """Start OAuth login flow.
    
    Args:
        user_id: Optional user ID, will generate if not provided
        
    Returns:
        dict: Authorization URL and user ID
    """
    try:
        oauth_handler = TrelloOAuthHandler.from_env()
        
        if not user_id:
            user_id = UserCredential.generate_user_id()
            
        auth_url = oauth_handler.get_authorization_url(user_id)
        
        return {
            "authorization_url": auth_url,
            "user_id": user_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {e}")


@app.get("/auth/callback")
async def auth_callback(
    token: str = Query(..., description="OAuth token from Trello"),
    user_id: str = Query(..., description="User ID from login flow"),
) -> dict[str, str]:
    """Handle OAuth callback.
    
    Args:
        token: OAuth token from Trello
        user_id: User ID from login flow
        
    Returns:
        dict: Success message
    """
    try:
        oauth_handler = TrelloOAuthHandler.from_env()
        client = TrelloClientImpl.from_env()
        
        # Exchange token for credentials
        access_token, token_secret = await oauth_handler.exchange_token(token)
        
        # Store credentials
        await client.store_credentials(user_id, access_token, token_secret)
        
        return {"message": "Authentication successful", "user_id": user_id}
        
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Callback failed: {e}")


# User endpoints
@app.get("/users/me", response_model=TrelloUser)
async def get_current_user(
    client: TrelloClient = Depends(get_trello_client),
) -> TrelloUser:
    """Get current authenticated user."""
    try:
        return await client.get_current_user()
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Board endpoints
@app.get("/boards", response_model=List[TrelloBoard])
async def get_boards(
    client: TrelloClient = Depends(get_trello_client),
) -> List[TrelloBoard]:
    """Get all boards accessible to the current user."""
    try:
        return await client.get_boards()
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/boards/{board_id}", response_model=TrelloBoard)
async def get_board(
    board_id: str,
    client: TrelloClient = Depends(get_trello_client),
) -> TrelloBoard:
    """Get a specific board by ID."""
    try:
        return await client.get_board(board_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/boards", response_model=TrelloBoard)
async def create_board(
    name: str,
    description: Optional[str] = None,
    client: TrelloClient = Depends(get_trello_client),
) -> TrelloBoard:
    """Create a new board."""
    try:
        return await client.create_board(name, description)
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/boards/{board_id}", response_model=TrelloBoard)
async def update_board(
    board_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    client: TrelloClient = Depends(get_trello_client),
) -> TrelloBoard:
    """Update an existing board."""
    try:
        return await client.update_board(board_id, name, description)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/boards/{board_id}")
async def delete_board(
    board_id: str,
    client: TrelloClient = Depends(get_trello_client),
) -> dict[str, bool]:
    """Delete a board."""
    try:
        success = await client.delete_board(board_id)
        return {"success": success}
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


# List endpoints
@app.get("/boards/{board_id}/lists", response_model=List[TrelloList])
async def get_lists(
    board_id: str,
    client: TrelloClient = Depends(get_trello_client),
) -> List[TrelloList]:
    """Get all lists in a board."""
    try:
        return await client.get_lists(board_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/boards/{board_id}/lists", response_model=TrelloList)
async def create_list(
    board_id: str,
    name: str,
    client: TrelloClient = Depends(get_trello_client),
) -> TrelloList:
    """Create a new list in a board."""
    try:
        return await client.create_list(board_id, name)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/lists/{list_id}", response_model=TrelloList)
async def update_list(
    list_id: str,
    name: Optional[str] = None,
    client: TrelloClient = Depends(get_trello_client),
) -> TrelloList:
    """Update an existing list."""
    try:
        return await client.update_list(list_id, name)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Card endpoints
@app.get("/lists/{list_id}/cards", response_model=List[TrelloCard])
async def get_cards(
    list_id: str,
    client: TrelloClient = Depends(get_trello_client),
) -> List[TrelloCard]:
    """Get all cards in a list."""
    try:
        return await client.get_cards(list_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/cards/{card_id}", response_model=TrelloCard)
async def get_card(
    card_id: str,
    client: TrelloClient = Depends(get_trello_client),
) -> TrelloCard:
    """Get a specific card by ID."""
    try:
        return await client.get_card(card_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/lists/{list_id}/cards", response_model=TrelloCard)
async def create_card(
    list_id: str,
    name: str,
    description: Optional[str] = None,
    client: TrelloClient = Depends(get_trello_client),
) -> TrelloCard:
    """Create a new card in a list."""
    try:
        return await client.create_card(list_id, name, description)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/cards/{card_id}", response_model=TrelloCard)
async def update_card(
    card_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    list_id: Optional[str] = None,
    client: TrelloClient = Depends(get_trello_client),
) -> TrelloCard:
    """Update an existing card."""
    try:
        return await client.update_card(card_id, name, description, list_id)
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/cards/{card_id}")
async def delete_card(
    card_id: str,
    client: TrelloClient = Depends(get_trello_client),
) -> dict[str, bool]:
    """Delete a card."""
    try:
        success = await client.delete_card(card_id)
        return {"success": success}
    except TrelloNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TrelloAuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except TrelloAPIError as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
