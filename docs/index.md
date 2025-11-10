# Welcome to the Mail Client Template

This project is a professional-grade template for a modern Python application, built using a component-based architecture with a clear separation between interface and implementation.

This documentation site provides an overview of the project's architecture, API contracts, and usage guidelines.

## Project Components

### Mail Client System
The mail subsystem provides email functionality:
- **mail_client_api**: Abstract interface for email clients
- **gmail_client_impl**: Gmail implementation
- **mail_client_adapter**: HTTP adapter for mail operations
- **mail_client_service**: FastAPI REST service for email

### Kanban/Board Management System
The kanban subsystem provides board management functionality:
- **kanban_client_api**: Abstract interface for board clients
- **trello_client_impl**: Trello implementation
- **kanban_client_adapter**: Wrapper around generated Trello client
- **kanban_generated_client**: Auto-generated OpenAPI client for Trello
- **kanban_client_service**: FastAPI REST service for boards

## Architecture Principles

This project follows these key architectural principles:

1. **Contract-First Design**: Abstract interfaces define contracts before implementations
2. **Dependency Injection**: Implementations are injected at runtime
3. **Adapter Pattern**: Low-level clients are wrapped in adapters for consistency
4. **Async/Await**: All I/O operations are async for performance
5. **Comprehensive Testing**: Unit tests, integration tests, and end-to-end tests
6. **OpenAPI First**: Generated clients from API specifications

## Getting Started

1. **Read the Architecture guide** to understand the component structure
2. **Browse API References** for specific package documentation
3. **Check integration tests** for usage examples


