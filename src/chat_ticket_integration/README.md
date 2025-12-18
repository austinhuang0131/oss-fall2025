# Chat Ticket Integration

Integration layer that connects chat APIs with ticket APIs to enable command-based ticket management through chat messages.

## Overview

This package provides a bridge between chat systems and ticket systems, allowing users to manage tickets through chat commands. It follows the adapter pattern and dependency injection to work with any chat or ticket implementation.

## Architecture

- Accepts any chat API implementation and any ticket API implementation via dependency injection
- Polls chat messages at configurable intervals (default: 1 second)
- Parses commands from messages using regex patterns
- Executes corresponding ticket operations
- Tracks processed messages to avoid duplicates

## Supported Commands

- `!create <name> [--desc <description>]` - Create a new ticket
- `!update <card_id> [--name <name>] [--desc <description>] [--list <list_id>]` - Update a ticket
- `!delete <card_id>` - Delete a ticket
- `!get <card_id>` - Get ticket details
- `!list [<list_id>]` - List all lists in the board or all cards in a specific list
- `!help` - Show available commands

## Usage

### Basic Setup

```python
from chat_ticket_integration import ChatTicketIntegration
from chat_ticket_integration.integration import ChatAPI, TicketAPI

# Initialize your chat and ticket API clients
chat_client = YourChatClient()
ticket_client = YourTicketClient()

# Create the integration
integration = ChatTicketIntegration(
    chat_api=chat_client,
    ticket_api=ticket_client,
    channel_id="your-channel-id",
    board_id="your-board-id",
    poll_interval=1.0  # Optional, defaults to 1 second
)

# Start polling (runs indefinitely)
await integration.start()

# Stop polling (call from another coroutine/handler)
integration.stop()
```

### Using with Adapters

If your existing implementations don't match the expected interface, create adapters:

```python
from chat_ticket_integration.integration import ChatAPI, TicketAPI

class MailClientChatAdapter(ChatAPI):
    """Adapter to use mail client as chat API."""
    
    def __init__(self, mail_client):
        self.mail_client = mail_client
    
    def get_messages(self, channel_id: str, max_results: int = 10):
        return list(self.mail_client.get_messages(max_results=max_results))

# Use the adapter
mail_client = get_mail_client()
chat_api = MailClientChatAdapter(mail_client)
```

## Integration with Other Teams

This project is configured to import implementations from other teams as packages. See `pyproject.toml` for the configured git sources:

```toml
[tool.uv.sources]
ta-assignment-ivan = { git = "https://github.com/ivanearisty/oss-taapp", branch = "root" }
ta-assignment-gsiri = { git = "https://github.com/gsiri-code/oss-taapp", branch = "root" }
# ... etc
```

To use another team's implementation, add it as a dependency in your workspace and import it.

## Testing

Run tests:

```bash
uv run pytest src/chat_ticket_integration/tests/ -v
```

## Configuration

- `channel_id`: Fixed channel ID for chat operations
- `board_id`: Fixed board ID for ticket operations  
- `poll_interval`: Time in seconds between polling cycles (default: 1.0)

## Design Principles

- **Dependency Injection**: Clients are injected at runtime, not hardcoded
- **Interface Segregation**: Uses abstract base classes for clear contracts
- **Single Responsibility**: Integration focuses only on bridging chat and tickets
- **Open/Closed**: Open for extension via adapters, closed for modification
