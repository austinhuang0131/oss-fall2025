# Trello Client Implementation Reference

`trello_client_impl` provides the concrete implementation of the `KanbanClient` interface for Trello. It is the primary implementation used in the kanban project.

## Overview

`TrelloClientImpl` is a complete implementation of the `KanbanClient` contract that:

- Connects to the Trello API using OAuth authentication
- Manages boards, lists, cards, and users
- Handles OAuth login flow for token acquisition
- Delegates all HTTP operations to `KanbanClientAdapter`

## Architecture

```
┌─────────────────────────────────┐
│   kanban_client_api             │
│   (Abstract Interface)          │
└────────────────▲────────────────┘
                 │
                 │ implements
                 │
┌─────────────────────────────────┐
│   TrelloClientImpl               │
│   - OAuth Handling              │
│   - Async Operations            │
│   - Token Management            │
└────────────────▲────────────────┘
                 │
                 │ uses
                 │
┌─────────────────────────────────┐
│   KanbanClientAdapter           │
│   - Exception Translation       │
│   - Model Conversion            │
└─────────────────────────────────┘
```

## Key Components

### TrelloClientImpl Class
The main implementation class providing all `KanbanClient` methods:
- All board, list, card operations are async
- Authenticates requests using Trello API key and token
- Supports OAuth token acquisition

### TrelloOAuthHandler
Manages OAuth authentication:
- Generates authorization URLs for login flow
- Exchanges authorization codes for tokens
- Loads credentials from environment variables

## Authentication

### Environment Variables

The Trello implementation requires these environment variables:

```bash
TRELLO_API_KEY=your-api-key
TRELLO_API_SECRET=your-api-secret
REDIRECT_URI=http://localhost:5000/auth/callback
```

### OAuth Flow

```python
from trello_client_impl import TrelloClientImpl

# Step 1: Get authorization URL
client = TrelloClientImpl()
auth_url = await client.get_authorization_url()
# Redirect user to auth_url

# Step 2: Exchange code for token (typically in callback handler)
token = await client.exchange_token(authorization_code)

# Step 3: Use token for subsequent API calls
authenticated_client = TrelloClientImpl(token=token)
boards = await authenticated_client.get_boards()
```

## Usage Pattern

```python
import kanban_client_api

# Get a Trello client (automatically TrelloClientImpl via dependency injection)
client = kanban_client_api.get_client(token="your-trello-token")

# All async operations
async def manage_boards():
    # Get all boards
    boards = await client.get_boards()
    
    # Get specific board
    board = await client.get_board("board-id")
    
    # Create new board
    new_board = await client.create_board(
        name="Project Alpha",
        description="Development board for Project Alpha"
    )
    
    # Get board's lists
    lists = await client.get_lists(board_id=new_board.id)
    
    # Create list
    todo_list = await client.create_list(
        board_id=new_board.id,
        name="To Do"
    )
    
    # Create card
    card = await client.create_card(
        list_id=todo_list.id,
        name="Implement feature X",
        description="Add support for feature X"
    )
    
    # Get current user
    user = await client.get_current_user()
    print(f"Logged in as: {user.full_name}")
```

## Dependency Injection

The `trello_client_impl` package registers itself automatically when imported:

```python
import kanban_client_api
import trello_client_impl  # This registration happens here

# Now get_client returns TrelloClientImpl instances
client = kanban_client_api.get_client(token="token")
assert isinstance(client, trello_client_impl.TrelloClientImpl)
```

## Error Handling

All exceptions raised conform to the `kanban_client_api` contract:

```python
import kanban_client_api

try:
    board = await client.get_board("invalid")
except kanban_client_api.KanbanNotFoundError:
    print("Board not found")
except kanban_client_api.KanbanAuthenticationError:
    print("Invalid token")
except kanban_client_api.KanbanAPIError as e:
    print(f"API error: {e}")
```

## Testing

Mock `TrelloClientImpl` by mocking its internal adapter:

```python
from unittest.mock import MagicMock, patch
from trello_client_impl import TrelloClientImpl

with patch("kanban_client_adapter.adapter.get_boards_boards_get") as mock_get:
    mock_get.return_value = [{"id": "b1", "name": "Board"}]
    
    client = TrelloClientImpl(token="test")
    boards = await client.get_boards()
```

## API Reference

::: trello_client_impl

