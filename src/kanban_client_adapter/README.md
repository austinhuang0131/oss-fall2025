# kanban_client_adapter

Adapter package for KanbanClient API, delegating calls to the generated Kanban client.

## Structure
- `src/kanban_client_adapter/`: Main adapter implementation
- `tests/`: (Optional) Unit tests for adapter

## Usage
Import `KanbanClientAdapter` from `adapter` and use as a drop-in replacement for the abstract `KanbanClient` interface.

## Development
- Ruff configuration is inherited from the repository root.
- Requires Python 3.10 or newer.
