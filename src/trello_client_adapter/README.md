# trello_client_adapter

Adapter package for TrelloClient API, delegating calls to the generated Trello client.

## Structure
- `src/trello_client_adapter/`: Main adapter implementation
- `tests/`: (Optional) Unit tests for adapter

## Usage
Import `TrelloClientAdapter` from `trello_client_adapter` and use as a drop-in replacement for the abstract `TrelloClient` interface.

## Development
- Ruff configuration is inherited from the repository root.
- Requires Python 3.10 or newer.
