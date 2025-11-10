# Kanban Client Service Reference

`kanban_client_service` is the FastAPI-based REST API service that exposes the kanban functionality as HTTP endpoints.

## Overview

The Kanban Client Service provides a production-ready REST API for managing kanban boards, lists, and cards. It:

- Exposes all `KanbanClient` operations as HTTP endpoints
- Uses FastAPI for high performance and async support
- Handles OAuth authentication flow with callback endpoints
- Provides automatic API documentation (Swagger/OpenAPI)
- Implements proper error handling and response serialization

## API Endpoints

### Authentication
- `GET /auth/login` - Initiates OAuth login flow, redirects to Trello authorization
- `GET /auth/callback` - OAuth callback endpoint, exchanges code for token

### Board Operations
- `GET /boards` - List all boards
- `GET /boards/{board_id}` - Get specific board
- `POST /boards` - Create new board
- `PUT /boards/{board_id}` - Update board
- `DELETE /boards/{board_id}` - Delete board

### List Operations
- `GET /boards/{board_id}/lists` - Get lists for a board
- `GET /lists/{list_id}` - Get specific list
- `POST /boards/{board_id}/lists` - Create list
- `PUT /lists/{list_id}` - Update list
- `DELETE /lists/{list_id}` - Delete list

### Card Operations
- `GET /boards/{board_id}/cards` - Get cards for a board
- `GET /lists/{list_id}/cards` - Get cards for a list
- `GET /cards/{card_id}` - Get specific card
- `POST /lists/{list_id}/cards` - Create card
- `PUT /cards/{card_id}` - Update card
- `DELETE /cards/{card_id}` - Delete card

### User Operations
- `GET /users/me` - Get current authenticated user

## Running the Service

### Prerequisites

Set required environment variables:

```bash
export TRELLO_API_KEY=your-api-key
export TRELLO_API_SECRET=your-api-secret
export REDIRECT_URI=http://localhost:8000/auth/callback
```

### Start the Server

```bash
python -m kanban_client_service.main
```

The service will start on `http://localhost:8000`.

## Usage Examples

### Retrieve All Boards

```bash
curl "http://localhost:8000/boards?token=your-token"
```

Response:
```json
[
  {
    "id": "board1",
    "name": "Project Alpha",
    "description": "Main development board",
    "closed": false,
    "url": "https://trello.com/b/...",
    "created_at": "2025-01-01T00:00:00Z"
  }
]
```

### Create a New Board

```bash
curl -X POST "http://localhost:8000/boards" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your-token",
    "name": "New Project",
    "description": "Description here"
  }'
```

### Get Board Details

```bash
curl "http://localhost:8000/boards/board1?token=your-token"
```

### Create a List

```bash
curl -X POST "http://localhost:8000/boards/board1/lists" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your-token",
    "name": "To Do"
  }'
```

### Create a Card

```bash
curl -X POST "http://localhost:8000/lists/list1/cards" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "your-token",
    "name": "Task Title",
    "description": "Task description"
  }'
```

### OAuth Login Flow

1. Redirect user to `/auth/login`
2. User authorizes with Trello
3. Redirected back to `/auth/callback?code=...&state=...`
4. Service exchanges code for token
5. Token stored in session/cookie

```bash
# Initiate login
curl "http://localhost:8000/auth/login"

# Will redirect to Trello authorization URL
# After authorization, redirects back with token
```

## Error Responses

All errors follow a standard format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

- `401` - Authentication failed (invalid token)
- `404` - Resource not found (board, list, or card)
- `422` - Validation error (invalid request data)
- `500` - Internal server error

## Dependency Injection

The service uses dependency injection to provide clients:

```python
from kanban_client_service.main import app

# The app is configured with:
# - FastAPI with async support
# - TrelloClientImpl injected as the KanbanClient implementation
# - All endpoints async for performance
```

## API Documentation

When running locally, access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Testing

Tests verify:
- All endpoints work correctly with mocked clients
- Error responses are properly formatted
- OAuth flow works end-to-end
- Token handling is secure

```bash
pytest tests/service/
```

## API Reference

::: kanban_client_service

