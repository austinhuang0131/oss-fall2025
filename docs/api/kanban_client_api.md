# Kanban Client API Reference

`kanban_client_api` provides the abstract base class `KanbanClient` and the `get_client` factory function. This package defines the contract for all kanban/board management implementations.

## Overview

The Kanban Client API is a contract-first design that defines the interface for managing kanban boards, lists, cards, and users. It uses Python's Abstract Base Classes (ABC) to enforce a consistent interface across different implementations.

## Core Components

### KanbanClient (Abstract Base Class)
The main interface defining all operations for kanban board management:
- **Board Operations**: `get_boards()`, `get_board()`, `create_board()`, `update_board()`, `delete_board()`
- **List Operations**: `get_lists()`, `get_list()`, `create_list()`, `update_list()`, `delete_list()`
- **Card Operations**: `get_cards()`, `get_card()`, `create_card()`, `update_card()`, `delete_card()`
- **User Operations**: `get_current_user()`
- **OAuth Operations**: `get_authorization_url()`, `exchange_token()`

### Data Models
- `KanbanBoard`: Represents a board with id, name, description, closed status, url, and created_at
- `KanbanList`: Represents a list with id, name, board_id, closed status, and position
- `KanbanCard`: Represents a card with id, name, description, list_id, board_id, due_date, and position
- `KanbanUser`: Represents a user with id, username, and full_name

### Factory Function
```python
get_client(token: str) -> KanbanClient
```
Returns a client instance bound to the provided authentication token. The actual implementation is injected at runtime.

## Usage Pattern

```python
import kanban_client_api

# Get a client instance
client = kanban_client_api.get_client(token="your-api-token")

# Fetch boards
boards = await client.get_boards()

# Create a list on a board
new_list = await client.create_list(
    board_id="board-123",
    name="To Do"
)

# Create a card in the list
new_card = await client.create_card(
    list_id=new_list.id,
    name="Task Title",
    description="Task description"
)
```

## API Reference

::: kanban_client_api

