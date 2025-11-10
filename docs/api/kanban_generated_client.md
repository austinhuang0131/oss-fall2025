# Kanban Generated Client Reference

`kanban_generated_client` is an auto-generated OpenAPI client for the Trello API. This package is generated from the Trello OpenAPI specification and provides low-level HTTP communication with the Trello backend.

## Overview

This is an auto-generated client created from the OpenAPI specification. It handles:
- Raw HTTP communication with Trello API endpoints
- Request/response serialization
- Error handling for HTTP status codes
- Model validation using attrs-based data classes

## Purpose

While this package provides direct access to Trello API endpoints, it should typically be used through the `KanbanClientAdapter` which wraps it and translates responses to the contract-defined models.

## Key Components

### Generated Models
- `ErrorResponse`: Standard error response from Trello API
- `Board`: Raw board data from Trello
- `List`: Raw list data from Trello
- `Card`: Raw card data from Trello
- `User`: Raw user data from Trello

### Client Class
The auto-generated client provides methods for each Trello API endpoint. Each method:
- Maps to a specific HTTP endpoint
- Handles authentication parameters
- Serializes/deserializes JSON payloads
- Returns strongly-typed response objects

## Usage Pattern

Typically, you should NOT use this package directly. Instead, use `kanban_client_api.get_client()`:

```python
import kanban_client_api

# Recommended approach
client = kanban_client_api.get_client(token="your-token")
boards = await client.get_boards()
```

If you need low-level access to the generated client:

```python
from kanban_generated_client import client as generated_client
from kanban_client_adapter.adapter import KanbanClientAdapter

# Create adapter which wraps the generated client
adapter = KanbanClientAdapter(generated_client)
```

## Notes

- This package is **excluded from coverage metrics** since it is auto-generated
- It serves as an implementation detail for the adapter layer
- Breaking changes in this package require regeneration from the OpenAPI spec
- For application logic, always use the contract layer (`kanban_client_api`)

## API Reference

::: kanban_generated_client

