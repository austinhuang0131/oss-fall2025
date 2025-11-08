# Kanban Client API

Abstract interface for Kanban client functionality.

This package defines the abstract contracts for interacting with Kanban boards, lists, and cards. It provides a clean interface that can be implemented by different concrete implementations.

## Core Concepts

- **Board**: A Kanban board represents a project or workflow
- **List**: A column within a board (e.g., "To Do", "In Progress", "Done")  
- **Card**: An individual task or item within a list

## Installation

```bash
uv add kanban-client-api
```

## Usage

```python
from kanban_client_api import KanbanClient

# Implementation will be provided by concrete implementations
client: KanbanClient = get_kanban_client()

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
```
