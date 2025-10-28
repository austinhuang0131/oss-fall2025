# Trello Client Service

FastAPI service that exposes Trello client operations over HTTP endpoints.

## Features

- RESTful API for Trello operations
- OAuth 2.0 authentication flow
- Comprehensive error handling
- OpenAPI/Swagger documentation 
- Health check endpoint

## Quick Start

1. Set environment variables:
```bash
export TRELLO_API_KEY="your_api_key"
export TRELLO_API_SECRET="your_api_secret"
export DATABASE_URL="postgresql://user:pass@host:port/db"
export REDIRECT_URI="http://localhost:8000/auth/callback"
```

2. Run the service:
```bash
uvicorn trello_client_service.main:app --reload
```

3. Visit http://localhost:8000/docs for API documentation

## Authentication Flow

1. GET `/auth/login` - Get authorization URL
2. User authorizes with Trello
3. GET `/auth/callback` - Handle callback and store credentials
4. Use `user_id` query parameter in subsequent requests

## API Endpoints

### Authentication
- `GET /auth/login` - Start OAuth flow
- `GET /auth/callback` - Handle OAuth callback

### Users
- `GET /users/me` - Get current user

### Boards
- `GET /boards` - List all boards
- `GET /boards/{board_id}` - Get specific board
- `POST /boards` - Create new board
- `PUT /boards/{board_id}` - Update board
- `DELETE /boards/{board_id}` - Delete board

### Lists
- `GET /boards/{board_id}/lists` - Get lists in board
- `POST /boards/{board_id}/lists` - Create list
- `PUT /lists/{list_id}` - Update list

### Cards
- `GET /lists/{list_id}/cards` - Get cards in list
- `GET /cards/{card_id}` - Get specific card
- `POST /lists/{list_id}/cards` - Create card
- `PUT /cards/{card_id}` - Update card
- `DELETE /cards/{card_id}` - Delete card

## Health Check

- `GET /health` - Service health status
