# Kanban System Integration Guide

## Overview

The Kanban subsystem provides board management functionality through a layered architecture. This guide explains how the components work together and how to use them effectively.

## Architecture Overview

### Layer Model

The kanban system follows a clean architecture with multiple possible implementation paths:

```
┌────────────────────────────────────────────┐
│         User Code (End Script)             │
│          or kanban_client_service          │
└─────────┬──────────────────────┬───────────┘
          │                      │
          │ can use directly     │ or use adapter
          │ (any KanbanClient)   │
          ▼                      ▼
    ┌──────────────┐      ┌──────────────────────────┐
    │Implementation│      │ kanban_client_adapter    │
    │   Options    │      │ (Adapter Pattern Layer)  │
    └──────────────┘      │ - Exception translation  │
            ▲             │ - Model conversion       │
            │             └────────┬─────────────────┘
      ┌─────┴──────┬────────┐      │
      │            │        │      │
      ▼            ▼        ▼      │
  ┌──────────┐ ┌──────────┐ ┌──────────────┐
  │ Trello   │ │ Adapter  │ │ Other Impls  │
  │ Impl     │ │ Impl     │ │(Jira, Asana) │
  ├──────────┤ ├──────────┤ ├──────────────┤
  │Implements│ │Implements│ │Implements    │
  │KanbanCli │ │KanbanCli │ │KanbanCli     │
  │- Direct  │ │- Wraps   │ │- Own         │
  │  Trello  │ │  service │ │  backends    │
  │- OAuth   │ │- Translate│ │              │
  │  support │ │  errors   │ │              │
  └──────────┘ └──────────┘ └──────────────┘
       │            │              │
       └────────────┼──────────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ kanban_client_api    │
         │ (Abstract Contract)  │
         ├──────────────────────┤
         │ - KanbanClient ABC   │
         │ - Models             │
         │ - Exceptions         │
         │ - get_client()       │
         └──────────────────────┘
                    ▲
                    │
    ┌───────────────┴───────────────┐
    │                               │
    ▼                               ▼
┌──────────────────────┐    ┌──────────────────────┐
│ kanban_generated_    │    │ Other service APIs   │
│ client (OpenAPI)     │    │ (if using adapter)   │
│ - Raw HTTP methods   │    │                      │
│ - Trello API calls   │    │                      │
└──────────────────────┘    └──────────────────────┘
```

## Package Relationships

### kanban_client_api
**Purpose**: Define the contract

- Exports `KanbanClient` abstract base class
- Defines data models: `KanbanBoard`, `KanbanList`, `KanbanCard`, `KanbanUser`
- Defines exceptions: `KanbanAPIError`, `KanbanAuthenticationError`, `KanbanNotFoundError`
- Provides `get_client(token: str) -> KanbanClient` factory function
- **No implementation** - pure interface that other packages can implement

### trello_client_impl
**Purpose**: Direct Trello implementation of the contract

- Implements `KanbanClient` as `TrelloClientImpl`
- Handles Trello OAuth authentication
- **Two modes of operation**:
  1. **Direct**: Use `TrelloClientImpl` directly for native Trello API
  2. **Registered**: Registers itself with `kanban_client_api.get_client()` at import time
- **Optionally delegates** to `KanbanClientAdapter` (not required)
- Registers itself automatically when imported

### kanban_client_adapter
**Purpose**: Optional adapter pattern layer for exception/model translation

- Implements `KanbanClient` interface
- **Wraps** `kanban_generated_client` 
- Translates low-level API errors to contract-defined exceptions
- Converts generated models to contract models
- **Optional**: Clients can use adapter directly OR use `TrelloClientImpl` directly
- Enables wrapping of other service implementations

### kanban_generated_client
**Purpose**: Communicate with Trello API at HTTP level

- Auto-generated from OpenAPI specification
- Provides low-level HTTP methods
- Strongly-typed request/response models
- **Excluded from coverage** - it's auto-generated
- Used internally by `KanbanClientAdapter`

### kanban_client_service
**Purpose**: Expose functionality via REST API

- FastAPI application
- HTTP endpoints for all kanban operations
- OAuth callback handling
- Uses `kanban_client_api.get_client()` - receives whatever implementation is registered
- Depends on all other packages

## Dependency Injection Pattern

The system uses a custom dependency injection pattern where any `KanbanClient` implementation can be registered:

### Registration

```python
# In trello_client_impl/__init__.py
from . import trello_impl
trello_impl.register()

# In trello_impl.py
def register() -> None:
    """Register TrelloClientImpl as the kanban_client_api implementation."""
    import kanban_client_api
    kanban_client_api.get_client = get_client_impl

def get_client_impl(token: str) -> TrelloClientImpl:
    """Create a TrelloClientImpl instance."""
    return TrelloClientImpl(token=token)
```

Any other `KanbanClient` implementation could register itself the same way.

### Usage

```python
import kanban_client_api
import trello_client_impl  # Registration happens at import

# Now get_client returns TrelloClientImpl instances
# But you could also register a different implementation
client = kanban_client_api.get_client(token="token")
```

### Direct Use (Without Registration)

You can also use implementations directly without going through `get_client()`:

```python
from trello_client_impl import TrelloClientImpl

# Use directly
client = TrelloClientImpl(token="your-token")
boards = await client.get_boards()
```

Or use the adapter directly:

```python
from kanban_client_adapter.adapter import KanbanClientAdapter

# Use adapter directly
adapter = KanbanClientAdapter(token="your-token")
boards = await adapter.get_boards()
```

Both `TrelloClientImpl` and `KanbanClientAdapter` implement the same `KanbanClient` interface, so they're interchangeable.

## Exception Handling Flow

When an error occurs in Trello API:

```
Trello API returns HTTP error
         │
         ▼
kanban_generated_client receives response
         │
         ▼
Raises ErrorResponse (generated model)
         │
         ▼
kanban_client_adapter catches it
         │
         ▼
Translates to contract exception
         │
         ▼
User code receives KanbanAuthenticationError, KanbanNotFoundError, etc.
```

### Exception Mapping

| HTTP Status | Generated Response | Adapter Exception | Meaning |
|-------------|-------------------|-------------------|---------|
| 401 | ErrorResponse | `KanbanAuthenticationError` | Invalid/expired token |
| 404 | ErrorResponse | `KanbanNotFoundError` | Resource doesn't exist |
| 4xx/5xx | ErrorResponse | `KanbanAPIError` | Other API error |

## Model Conversion Flow

When fetching data from Trello:

```
Trello API returns JSON
         │
         ▼
kanban_generated_client parses to generated models
         │
         ▼
kanban_client_adapter converts to contract models
         │
         ▼
User receives KanbanBoard, KanbanCard, etc.
```

### Model Mapping

| Generated | Contract |
|-----------|----------|
| `generated.Board` | `KanbanBoard` |
| `generated.List` | `KanbanList` |
| `generated.Card` | `KanbanCard` |
| `generated.User` | `KanbanUser` |

## Usage Scenarios

### Scenario 1: Simple Board Fetch

```python
import kanban_client_api
import trello_client_impl  # Enables Trello

# Get client
client = kanban_client_api.get_client(token="your-token")

# Fetch boards
async def list_boards():
    boards = await client.get_boards()
    for board in boards:
        print(f"- {board.name}")
```

**Flow**:
1. `get_client()` returns `TrelloClientImpl`
2. `get_boards()` calls `TrelloClientImpl.get_boards()`
3. Which calls `KanbanClientAdapter.get_boards()`
4. Which calls generated client API
5. Generated client makes HTTP request
6. Response converted to `KanbanBoard` models
7. Returned to caller

### Scenario 2: Error Handling

```python
try:
    board = await client.get_board("invalid-id")
except kanban_client_api.KanbanNotFoundError:
    print("Board not found")
```

**Flow**:
1. `get_board()` makes request via adapter
2. Generated client gets 404 response
3. Raises `ErrorResponse` exception
4. Adapter catches it, translates to `KanbanNotFoundError`
5. User code catches contract exception

### Scenario 3: Testing

```python
from unittest.mock import patch, MagicMock

# Mock the generated client
with patch("kanban_client_adapter.adapter.get_boards_boards_get") as mock:
    mock.return_value = [MagicMock(id="b1", name="Board")]
    
    client = kanban_client_api.get_client(token="test")
    boards = await client.get_boards()
    assert len(boards) == 1
```

## Integration Points

### With mail_client_service

Both mail and kanban services can run together:

```python
from kanban_client_service import kanban_app
from mail_client_service import mail_app

# Can compose into larger application
# or run separately on different ports
```

### With FastAPI

The kanban service integrates seamlessly:

```python
from fastapi import FastAPI
from kanban_client_service.main import app as kanban_app

# Can use as sub-application
# app.include_router(kanban_app.routes)
```

## Testing Strategy

### Unit Tests (by package)

Each package has unit tests:
- `src/kanban_client_api/tests/` - ABC validation
- `src/trello_client_impl/tests/` - Implementation tests
- `src/kanban_client_adapter/tests/` - 42 comprehensive tests
- `src/kanban_client_service/tests/` - Endpoint tests

### Integration Tests

- `tests/integration/test_kanban_integration.py` - Multi-package interaction
- Tests dependency injection
- Tests exception translation
- Tests model conversion
- 18 comprehensive tests, all passing

### Coverage

- **Target**: 85%
- **Current**: 87% (after excluding generated client)
- **Excluded**: `kanban_generated_client/*` (auto-generated)

## Development Workflow

### Adding a New Feature

1. **Update contract** (`kanban_client_api`)
   - Add method to `KanbanClient` ABC
   - Add/update models if needed

2. **Implement** (`trello_client_impl`)
   - Implement new method in `TrelloClientImpl`
   - Use adapter internally

3. **Adapter** (`kanban_client_adapter`)
   - Add adapter method wrapping generated client
   - Add exception translation if needed

4. **Service** (`kanban_client_service`)
   - Add REST endpoint
   - Add tests

5. **Test**
   - Unit tests for each layer
   - Integration tests for cross-layer interaction

### Adding a New Implementation

To add support for another board system (e.g., Jira):

1. Create `jira_client_impl` package
2. Implement `KanbanClient` as `JiraClientImpl`
3. Create `jira_client_adapter` if needed
4. Register via dependency injection
5. Service automatically uses new implementation

## Best Practices

### Do's ✓

- Always import `kanban_client_api` before using
- Always import implementation (`trello_client_impl`) before calling `get_client()`
- Use async/await for all I/O operations
- Catch contract-defined exceptions
- Use mocks for testing, not real API keys
- Handle all possible exceptions

### Don'ts ✗

- Don't use `kanban_generated_client` directly in application code
- Don't catch generated exceptions
- Don't skip error handling
- Don't expose implementation details to callers
- Don't create clients without tokens
- Don't mock at wrong layer in tests

## Debugging

### Check Current Implementation

```python
import kanban_client_api
import trello_client_impl

client = kanban_client_api.get_client(token="t")
print(type(client))  # <class 'trello_client_impl.TrelloClientImpl'>
```

### Trace Execution

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now see all async operations logged
boards = await client.get_boards()
```

### Test a Single Layer

```python
# Test just the adapter
from kanban_client_adapter import KanbanClientAdapter
adapter = KanbanClientAdapter(token="t")
boards = await adapter.get_boards()

# Test just the generated client
from kanban_generated_client import client as gen_client
# Use directly if needed
```

## Performance Considerations

- All operations are async - use `await` for proper concurrency
- Multiple clients can be created for different tokens
- No caching - each call hits the API
- Connection pooling handled by async HTTP client
- Adapter adds minimal overhead

## Security

- Tokens are passed explicitly, never stored
- OAuth handled by `TrelloOAuthHandler`
- No credentials logged
- All HTTP communication uses HTTPS to Trello
- Set environment variables for OAuth configuration

