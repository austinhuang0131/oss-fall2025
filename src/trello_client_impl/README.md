# Trello Client Implementation

This package provides a concrete implementation of the Trello client API that wraps the Trello REST API.

## Features

- OAuth utilities like URL generation
- Async/await support
- Comprehensive error handling
- Type-safe operations

## Authentication

The implementation uses OAuth 2.0 with Trello's API. Users are redirected to Trello for authentication, and tokens are returned to the user.

## Usage

```python
from trello_client_impl import TrelloClientImpl, TrelloOAuthHandler

# get oauth login url
oauth_handler = TrelloOAuthHandler.from_env()
auth_url = oauth_handler.get_authorization_url()
print(f"Login at: {auth_url}")

# Create client with existing user token
client = TrelloClientImpl(token="abcdefg...")

# Use the client (OAuth flow handled automatically)
boards = await client.get_boards()
```

## Environment Variables

- `TRELLO_API_KEY`: Your Trello API key
- `TRELLO_API_SECRET`: Your Trello API secret  
- `REDIRECT_URI`: OAuth callback URL
