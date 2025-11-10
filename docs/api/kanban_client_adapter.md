# Kanban Client Adapter Reference

`kanban_client_adapter` provides the `KanbanClientAdapter` class that wraps the auto-generated Trello API client and translates it to the contract-defined `KanbanClient` interface.

## Overview

The adapter pattern allows the low-level, auto-generated `kanban_generated_client` to be wrapped in a high-level interface that conforms to the `KanbanClient` abstract base class. This provides:

- **Contract Adherence**: All methods return contract-defined models (`KanbanBoard`, `KanbanCard`, etc.)
- **Exception Translation**: Converts low-level API errors to contract-defined exceptions
- **Abstraction**: Hides implementation details of the generated client
- **Testability**: Mock-friendly design for unit and integration tests

## Architecture

```
┌─────────────────────────────────┐
│   kanban_client_api             │
│   (Abstract Interface)          │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   KanbanClientAdapter           │
│   (Adapter Implementation)      │
│   - Exception Translation       │
│   - Model Conversion            │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│   kanban_generated_client       │
│   (OpenAPI-Generated)           │
│   - Raw HTTP Communication      │
└─────────────────────────────────┘
```

## Key Features

### Exception Translation
The adapter converts low-level `ErrorResponse` objects to contract-defined exceptions:

| API Error | Adapter Exception |
|-----------|-------------------|
| 401 Unauthorized | `KanbanAuthenticationError` |
| 404 Not Found | `KanbanNotFoundError` |
| 4xx/5xx Other | `KanbanAPIError` |

### Model Conversion
Converts raw generated models to contract models:
- `generated.Board` → `KanbanBoard`
- `generated.List` → `KanbanList`
- `generated.Card` → `KanbanCard`
- `generated.User` → `KanbanUser`

## Usage Pattern

```python
from kanban_client_adapter.adapter import KanbanClientAdapter
import kanban_client_api

# Create adapter instance
adapter = KanbanClientAdapter(token="your-trello-token")

# Use through contract interface
boards = await adapter.get_boards()
board = await adapter.get_board("board-id")

# Create resources
new_list = await adapter.create_list(
    board_id="board-id",
    name="To Do"
)

# Error handling - exceptions from adapter are contract-defined
try:
    await adapter.get_board("invalid-id")
except kanban_client_api.KanbanNotFoundError:
    print("Board not found")
except kanban_client_api.KanbanAuthenticationError:
    print("Invalid token")
except kanban_client_api.KanbanAPIError as e:
    print(f"API error: {e}")
```

## Integration with Trello Implementation

The `trello_client_impl` package uses this adapter internally:

```python
from trello_client_impl import TrelloClientImpl

client = TrelloClientImpl(token="your-token")
# Internally uses KanbanClientAdapter
boards = await client.get_boards()
```

## API Reference

::: kanban_client_adapter

