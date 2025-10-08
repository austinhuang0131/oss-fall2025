# CONTRIBUTING.md

## Architecture Overview

### Components
This repository is organized into several components, each encapsulated in its own directory under `src/`. The main components are:
- **gmail_client_impl**: Implements Gmail-specific client logic and message handling.
- **gmail_message_impl**: Contains Gmail message abstractions.
- **mail_client_api**: Defines the core mail client interface and message abstraction.
- **message**: Provides shared message utilities.

These components interact via well-defined interfaces, allowing for modularity and easy extension or replacement of implementations.

### Interface Design
The primary interface is defined in `mail_client_api/src/mail_client_api/client.py` and `mail_client_api/src/mail_client_api/message.py`. These interfaces abstract mail client and message operations, enabling different implementations (e.g., Gmail) to be plugged in. The design enforces method signatures and expected behaviors, ensuring consistency across implementations.

### Implementation Details
Interfaces are implemented using Python's `abc` module, which allows for the definition of abstract base classes. Implementations in `gmail_client_impl` and `gmail_message_impl` inherit from these ABCs and provide concrete logic. This approach ensures that all required methods are implemented and enables type checking.

Unlike `Protocol` from the `typing` module, which allows for structural subtyping (duck typing), ABCs enforce nominal subtyping, requiring explicit inheritance. Protocols are more flexible for static type checking, but ABCs provide runtime enforcement and can include abstract methods.

### Dependency Injection
The project uses dependency injection to decouple interface definitions from their implementations. In `main.py` (root), line 8, the injection occurs:

```python
import gmail_client_impl  # gmail takes priority
import mail_client_api
```

This pattern allows contributors to swap out implementations (e.g., for testing or extending functionality) without modifying the code that depends on the interface. It enables easier testing, extensibility, and adherence to SOLID principles.

## Repository Structure

### Project Organization
- `src/`: Contains all source code, organized by component.
- `tests/`: Contains test suites, organized into `e2e/` (end-to-end), `integration/`, and component-level test directories.
- `docs/`: Contains documentation, including API docs and guides.
- `pyproject.toml`, `uv.lock`: Root configuration and workspace management files.

### Configuration Files
- **Root `pyproject.toml`**: Manages workspace-wide dependencies, tool configuration, and uv workspace settings.
- **Component `pyproject.toml`**: Manages dependencies and settings specific to each component, allowing for isolated development and testing.

### Package Structure
`__init__.py` files exist in every Python package directory (e.g., `src/gmail_client_impl/gmail_client_impl/`). They mark directories as Python packages and can be used to expose public APIs. Keeping `__init__.py` slim means minimizing logic in these files—preferably only imports or package-level constants. Contributors should follow this convention to avoid side effects and maintain clarity.

### Import Guidelines
Absolute imports should be used throughout the repository. Relative imports (e.g., `from . import ...`) are not used and should be avoided for consistency and clarity. Always use absolute imports to reference modules and packages.

## Testing Strategy

### Testing Philosophy
Tests should follow these principles:

- Test via the Public API: Write tests that interact with the code as users would, through its public interfaces.
- Test State not method invocation: Focus on verifying the resulting state or output, not on whether specific methods were called.
- Write Complete and Concise Tests: Ensure each test contains all necessary information for understanding, without unnecessary details.
- Test behaviors not methods: Test distinct behaviors independently, even if they are implemented in the same method.
- Don’t put logic in tests: Avoid adding logic or computation in tests; tests should be obviously correct and easy to verify.
- Write clear failure message: Make sure test failures provide helpful clues about what went wrong and why.

### Test Organization
- **Unit tests**: Located in each component's `tests/` directory.
- **Integration tests**: Located in `tests/integration/`.
- **E2E tests**: Located in `tests/e2e/`.

`__init__.py` files are generally omitted in test directories to prevent them from being treated as packages, simplifying test discovery and execution by avoiding import issues.

### Test Abstraction Levels
Tests operate at multiple abstraction levels:
- Unit: Individual functions/classes
- Integration: Interactions between components
- E2E: Full application workflows

### Code Coverage
- **Tool**: `coverage.py` is used for coverage analysis.
- **Thresholds**: Minimum acceptable coverage is 85% (in CircleCI).
- **Instructions**:
  1. Install coverage: `uv pip install coverage`
  2. Run tests with coverage: `uv pip install -e . && coverage run -m pytest`
  3. Generate report: `coverage report -m` or `coverage html`

## Development Tools

### Workspace Management
The project uses a `uv` workspace to manage multiple components. Essential commands:
- Set up everything: `uv sync --all-packages --extra dev --verbose`

The root `pyproject.toml` manages shared dependencies and workspace settings, while component-level `pyproject.toml` files manage per-component dependencies and settings.

### Static Analysis and Code Formatting
**Tools**: `ruff` for static analysis and code formatting
**Instructions**:
  - Run static analysis: `uv pip install ruff && ruff check .`
  - Run formatting: `uv pip install ruff && ruff format .`
Ruff is run separately from uv, but can be installed via uv for consistency. Importance: Ensures code quality, consistency, and reduces bugs. Ruff enforces style and formatting rules automatically, so no separate formatter is needed.

### Documentation Generation
- **Tool**: `mkdocs` is used for documentation generation.
- **Instructions**:
  - Install: `uv pip install mkdocs`
  - Build docs: `mkdocs build`
  - Serve docs locally: `mkdocs serve`

### CI
The CI pipeline in `.circleci/` directory includes jobs for:
- Linting and formatting
- Running tests and checking coverage
- Building documentation

Jobs are triggered on pull requests and pushes to main branches, ensuring code quality and up-to-date documentation.

---

Please refer to this guide before contributing. For questions, open an issue or contact a maintainer.