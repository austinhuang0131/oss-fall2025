# Trello Client API

Abstract interface for Trello client functionality.

This package defines the abstract contracts for interacting with Trello boards, lists, and cards. It provides a clean interface that can be implemented by different concrete implementations.

## Core Concepts

- **Board**: A Trello board represents a project or workflow
- **List**: A column within a board (e.g., "To Do", "In Progress", "Done")  
- **Card**: An individual task or item within a list

## Installation

```bash
uv add trello-client-api
```

## Usage

```python
from trello_client_api import TrelloClient

# Implementation will be provided by concrete implementations
client: TrelloClient = get_trello_client()

# Get all boards
boards = await client.get_boards()

# Create a new board
board = await client.create_board("My Project Board")

# Get lists in a board
lists = await client.get_lists(board.id)

# Create a card
card = await client.create_card(
    list_id=lists[0].id,
    name="Implement authentication",
    description="Add OAuth 2.0 flow to the service"
)
```
