# Component Definition

Every workspace component lives under `src/<component_name>/` and represents either an abstract contract implemented as an ABC or a concrete implementation.

## Directory Layout
```
<component_name>/
├── pyproject.toml
├── README.md
├── src/<component_name>/
│   ├── __init__.py
│   └── _impl.py        # only for implementations
└── tests/              # optional component-scoped tests
```

## `pyproject.toml` Checklist
- `[project]`: align `name` with the folder, set `version`, `description`, `readme = "README.md"`, `requires-python = ">=3.11"`, and list direct dependencies.
- `[build-system]`: keep `hatchling` as the backend.
- `[tool.uv.sources]`: declare workspace dependencies when another component is required.

## README Expectations
Document, at minimum: overview, scope, exposed interfaces, usage pattern, and component dependencies. Keep examples using absolute imports.

## Implementation Notes (`_impl.py`)
Place concrete classes here so `__init__.py` can focus on exports and dependency injection wiring.

## Package Initialisation (`__init__.py`)
- Contract packages: define the ABC and `get_*` factory that raises `NotImplementedError`.
- Implementation packages: import the contract, expose factories like `get_*_impl`, and rebind the factory (e.g., `contract.get_* = get_*_impl`). Use `__all__` for any public symbols.

## Testing
Component-level tests belong in `tests/`. Target the public interface, use mocks to isolate external services, and keep fixtures local to the component.

---

# Kanban Components

The kanban subsystem follows the same architectural principles as the mail subsystem, providing board management functionality through a layered architecture.

## Component Map

### Contract Layer
- **kanban_client_api**: Abstract interface for board clients
  - Exports: `KanbanClient` ABC, data models, exceptions, `get_client()` factory
  - No implementation - pure interface definition

### Implementation Layer
- **trello_client_impl**: Concrete Trello implementation
  - Exports: `TrelloClientImpl`, `TrelloOAuthHandler`
  - Registers with `kanban_client_api` at import time
  - Depends on: `kanban_client_api`, `kanban_client_adapter`

### Adapter Layer
- **kanban_client_adapter**: Wraps auto-generated client
  - Exports: `KanbanClientAdapter`
  - Exception translation (generated errors → contract exceptions)
  - Model conversion (generated models → contract models)
  - Depends on: `kanban_client_api`, `kanban_generated_client`

### Generated Layer
- **kanban_generated_client**: Auto-generated OpenAPI client
  - Auto-generated from Trello OpenAPI spec
  - Strongly-typed models and endpoints
  - Low-level HTTP communication
  - Excluded from coverage metrics (auto-generated)

### Service Layer
- **kanban_client_service**: FastAPI REST API
  - Exports: FastAPI application with kanban endpoints
  - HTTP endpoints for all CRUD operations
  - OAuth callback handling
  - Depends on: all other kanban components

## Kanban Architecture vs Mail Architecture

| Aspect | Mail | Kanban |
|--------|------|--------|
| **Contract** | `mail_client_api.Client` | `kanban_client_api.KanbanClient` |
| **Implementation** | `gmail_client_impl.GmailClientImpl` | `trello_client_impl.TrelloClientImpl` |
| **Adapter** | `mail_client_adapter` | `kanban_client_adapter` |
| **Generated** | None | `kanban_generated_client` |
| **Service** | `mail_client_service` | `kanban_client_service` |

## Key Differences

### Generated Client
The kanban system includes `kanban_generated_client` - an auto-generated OpenAPI client for Trello. This is excluded from coverage metrics since it's machine-generated.

The mail system doesn't have a generated client; it uses direct HTTP communication.

### OAuth Handling
- **Mail**: OAuth handled by Gmail's server-side flow
- **Kanban**: OAuth handled by `TrelloOAuthHandler` with explicit code exchange

### Data Models
- **Mail**: Message-centric (emails, threads)
- **Kanban**: Board-centric (boards, lists, cards)

## Integration Points

Both subsystems coexist in the same project:

```
┌─────────────────────────────────────┐
│   Main Application (main.py)        │
└─────┬──────────────────────┬────────┘
      │                      │
      ▼                      ▼
┌──────────────────┐  ┌──────────────────┐
│  mail_client_    │  │  kanban_client_  │
│  service         │  │  service         │
└──────────────────┘  └──────────────────┘
```

Both services can be:
- Run independently on different ports
- Composed into a single application
- Deployed in separate containers

## Development Guidelines

When adding new functionality to kanban:

1. **Update Contract First**: Modify `kanban_client_api`
2. **Implement**: Update `trello_client_impl`
3. **Adapt**: Update `kanban_client_adapter` 
4. **Expose**: Add endpoint in `kanban_client_service`
5. **Test**: Add tests at each layer + integration tests

For more details, see [Kanban Integration Guide](kanban-integration.md).


