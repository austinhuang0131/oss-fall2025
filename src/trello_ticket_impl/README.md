# `trello_ticket_impl`

Trello implementation of the Ticket API interface for managing tickets across projects. This package provides a concrete implementation of the `TicketInterface` abstraction, allowing teams to interact with Trello as a backend for ticket management.

## Overview

This package implements the Ticket API using Trello as the backend storage. It maps:
- **Trello cards** → **Tickets** (individual tasks/issues)
- **Trello lists** → **Ticket statuses** (workflow states)
- **Trello board** → **Project** (passed as parameter or auto-created)

## Core Concepts

### Status-to-List Mapping

The implementation uses three dedicated Trello lists to represent ticket statuses:

| Ticket Status | Trello List | Purpose |
|---|---|---|
| `OPEN` | "To Do" | Tasks ready to be started |
| `IN_PROGRESS` | "In Progress" | Tasks currently being worked on |
| `CLOSED` | "Done" | Completed tasks |

These lists are automatically created on first use if they don't already exist on your board. If no board is provided, a new board is automatically created during the first ticket operation.

## Usage

### Basic Setup

```python
from trello_ticket_impl import TrelloTicketClientImpl

# Create a client instance with explicit board ID
client = TrelloTicketClientImpl(
    token="your_trello_token",
    board_id="your_board_id"  # Optional: ID from https://trello.com/b/{BOARD_ID}/...
)

# Or let it auto-create a board
client = TrelloTicketClientImpl(
    token="your_trello_token"
    # board_id will be auto-created on first ticket operation
)
```

### Board Configuration

The board can be configured in two ways:

1. **Explicit Board ID** (recommended for existing boards):
   - Pass `board_id` parameter to the constructor
   - Found in the Trello board URL: `https://trello.com/b/{BOARD_ID}/...`

2. **Auto-Creation**:
   - If `board_id` is not provided, a new "Ticket Board" is automatically created on first use
   - The board ID is stored for future operations

### Authentication

Tokens can be provided in three ways:

1. **Direct Token Passing**:
```python
client = TrelloTicketClientImpl(token="your_api_token", board_id="board_id")
```

2. **OAuth Handler** (recommended for production):
```python
from trello_client_impl.oauth import TrelloOAuthHandler

oauth_handler = TrelloOAuthHandler()
client = TrelloTicketClientImpl(oauth_handler=oauth_handler, board_id="board_id")
```

3. **Environment Variables** (if no token/handler provided):
```python
client = TrelloTicketClientImpl(board_id="board_id")
# Will use TRELLO_API_KEY and TRELLO_TOKEN from environment
```

The OAuth handler or token will automatically be sourced from environment variables if not explicitly provided.

## Core Operations

### Creating Tickets

```python
ticket = client.create_ticket(
    title="Fix login bug",
    description="Users report 404 on login endpoint",
    assignee="user_id"  # Optional
)
# Returns: Ticket with status=OPEN, placed in "To Do" list
```

### Retrieving Tickets

```python
ticket = client.get_ticket("trello_card_id")
# Returns: Ticket with current status based on list membership
```

### Updating Tickets

```python
updated_ticket = client.update_ticket(
    "card_id",
    title="Updated title",           # Optional
    description="New description",   # Optional
    status=TicketStatus.IN_PROGRESS, # Optional
    assignee="new_user_id"          # Optional
)
# Moving a ticket to a different status moves its card to the corresponding list
```

### Deleting Tickets

```python
success = client.delete_ticket("card_id")
# Returns: True on successful deletion
```

### Searching Tickets

```python
# Search by query
tickets = client.search_tickets(query="bug fix")

# Filter by status
tickets = client.search_tickets(status=TicketStatus.CLOSED)

# Retrieve all tickets
all_tickets = client.search_tickets()

# Combined search with query and status
tickets = client.search_tickets(query="urgent", status=TicketStatus.OPEN)
```

## Data Model

### Ticket Properties

Each ticket has the following properties:

- **`id`**: Unique identifier (Trello card ID)
- **`title`**: Ticket title (from card name)
- **`description`**: Ticket description (from card description)
- **`status`**: Current status (`OPEN`, `IN_PROGRESS`, or `CLOSED`)
- **`assignee`**: User ID of assigned person (optional, only first assignee if multiple)

## Integration with Shared Vertical Interface

This package implements the `TicketInterface` contract defined in the `tickets_api` package. Other teams depending on the Ticket API can use this implementation without needing to know implementation details:

```python
from tickets_api import get_client

# Teams use the interface, not the implementation
client = get_client()  # Returns TrelloTicketClientImpl when this package is imported
ticket = client.create_ticket("Task", "Description")
```

This design follows the **Interface-Implementation Separation** pattern, allowing easy swapping of implementations.

## Error Handling

The package raises specific exceptions for different scenarios:

- **`TrelloAuthenticationError`**: Authentication failure (missing/invalid token)
- **`TrelloNotFoundError`**: Resource not found (card doesn't exist)
- **`TrelloAPIError`**: General API errors (network issues, invalid state)

```python
from trello_ticket_impl.exceptions import TrelloAuthenticationError, TrelloAPIError

try:
    ticket = client.create_ticket("Task", "Description")
except TrelloAuthenticationError:
    print("Invalid or missing Trello token")
except TrelloAPIError as e:
    print(f"API error: {e}")
```

## Implementation Notes

- **Assignees**: Trello supports multiple assignees per card, but this implementation returns only the first assignee for simplicity and interface compatibility
- **List Initialization**: Lists are lazily initialized on first operation. This requires board write permissions
- **Status Updates**: Moving a ticket to a different status updates its Trello list membership

## Development

Run tests with coverage:

```bash
pytest src/trello_ticket_impl/tests/test_trello_ticket_impl.py -v
```

## See Also

- `trello_client_impl`: Low-level Trello board/list/card management
- `tickets_api`: The abstract Ticket API interface