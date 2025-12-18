# AI Chat Ticket Integration - Natural Language Interface

This document explains the natural language processing capabilities added to the chat ticket integration system.

## Overview

The `AiChatTicketIntegration` class now uses an AI interface to parse natural language chat messages and convert them into structured ticket operations. Users can interact with the system using conversational language instead of rigid command syntax.

## Architecture

### System Prompt

The `SYSTEM_PROMPT` constant defines the AI's role as a ticket management assistant. It instructs the AI to:
- Identify the user's intent (CREATE, UPDATE, DELETE, GET, HELP, or UNKNOWN)
- Extract relevant parameters from natural language
- Return structured data matching the response schema

### Response Schema

The `RESPONSE_SCHEMA` is a JSON schema that defines the expected structure of AI responses:

```python
{
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "enum": ["CREATE", "UPDATE", "DELETE", "GET", "HELP", "UNKNOWN"],
        },
        "parameters": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "enum": ["open", "in_progress", "closed"]},
            },
        },
    },
    "required": ["action", "parameters"],
}
```

### AI Response Parser

The `_parse_ai_response()` method processes the AI's output:
- Accepts either structured dict responses (when using response_schema) or strings
- Returns a parsed dict with action and parameters, or None if parsing fails

### Natural Language Handlers

Four new handler methods process the parsed AI responses:

#### `_handle_create_nl(parameters)`
Creates a new ticket from natural language input.

**Example inputs:**
- "Create a ticket called 'Fix login bug'"
- "Make a new task for implementing user authentication"
- "Add a ticket to track the homepage redesign with description: update the UI"

**Parameters:**
- `title` (required): The ticket title
- `description` (optional): The ticket description

#### `_handle_update_nl(parameters)`
Updates an existing ticket.

**Example inputs:**
- "Update ticket ABC123 to in progress"
- "Change ticket DEF456 status to closed"
- "Rename ticket GHI789 to 'New feature request'"

**Parameters:**
- `ticket_id` (required): The ticket to update
- `title` (optional): New title
- `status` (optional): New status (open, in_progress, or closed)

#### `_handle_delete_nl(parameters)`
Deletes a ticket.

**Example inputs:**
- "Delete ticket ABC123"
- "Remove ticket DEF456"

**Parameters:**
- `ticket_id` (required): The ticket to delete

#### `_handle_get_nl(parameters)`
Retrieves ticket details.

**Example inputs:**
- "Show me ticket ABC123"
- "Get details for ticket DEF456"
- "What's in ticket GHI789?"

**Parameters:**
- `ticket_id` (required): The ticket to retrieve

#### `_handle_search(parameters)`
Searches for tickets based on query and/or status.

**Example inputs:**
- "Search for tickets about login"
- "Find all open tickets"
- "List closed tickets"
- "Show me in progress tickets with bug in the title"

**Parameters:**
- `query` (optional): Search text to filter by title or description
- `status` (optional): Filter by status (open, in_progress, or closed)

## Usage Example

```python
from ai_api.src.ai_api import AIInterface
from chat_api.src.chat_api import ChatInterface
from tickets_api.src.tickets_api import TicketInterface
from ai_chat_ticket_integration.src.ai_chat_ticket_integration.integration import AiChatTicketIntegration

# Initialize your API implementations
chat_api: ChatInterface = ...  # Your chat API
ticket_api: TicketInterface = ...  # Your ticket API
ai_api: AIInterface = ...  # Your AI API

# Create the integration
integration = AiChatTicketIntegration(
    chat_api=chat_api,
    ticket_api=ticket_api,
    ai_api=ai_api,
    channel_id="my-channel",
    poll_interval=1.0,
)

# Start the integration
await integration.start()
```

## Testing

The unit tests in `tests/test_integration.py` verify:

1. **System prompt and schema validation**: Ensures the prompt and schema are correctly defined
2. **AI response parsing**: Tests structured and unstructured response handling
3. **Natural language handlers**: Tests each CRUD operation handler
4. **End-to-end command processing**: Tests the full flow from natural language to ticket operations

Run tests with:
```bash
pytest src/ai_chat_ticket_integration/tests/test_integration.py -v
```

## Error Handling

The integration handles various error conditions:
- Missing required parameters (e.g., no ticket_id for update)
- Invalid status values
- AI parsing failures
- Ticket API exceptions
- Unstructured AI responses

Each error condition results in a helpful error message being sent to the chat channel.

## Migration from Command-Based System

The old command-based handlers (`_handle_create`, `_handle_update`, etc.) remain in the codebase for backward compatibility, but the new natural language processing in `_process_command()` now uses the AI interface to parse messages instead of regex pattern matching.

To fully migrate, you can remove the old handlers once all users are comfortable with the natural language interface.
