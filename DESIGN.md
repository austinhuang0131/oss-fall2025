# Design Document: Service-Based Email Client

This document describes the architecture and design of the service-based email client implementation, which transforms the original direct email library into a REST API service with an adapter that maintains backward compatibility.

## Executive Summary

The service-based email client implements a REST API wrapper around the existing Gmail client implementation, enabling remote access to email functionality via HTTP. The solution maintains 100% backward compatibility with existing client code through an adapter pattern while introducing scalability, testability, and deployment flexibility benefits.

## Architecture Overview

### Components

The service-based implementation introduces three new core components that work together to provide a scalable, service-oriented architecture:

* **FastAPI Service** (`src/mail_client_service/src/mail_client_service/app.py`): A production-ready REST API service built on FastAPI that exposes the original email functionality via HTTP endpoints. It includes comprehensive error handling, input validation via Pydantic models, automatic OpenAPI documentation generation, and dependency injection for the underlying email client.

* **Auto-Generated Client** (`src/mail_client_service/mail-client-service-client/mail_client_service_client/`): A type-safe HTTP client automatically generated from the FastAPI service's OpenAPI specification using openapi-python-client. This client provides strongly-typed models (`MessageResponse`, `SuccessResponse`), comprehensive error handling, and both synchronous and asynchronous operation support.

* **Adapter (ServiceImpl)** (`src/mail_client_service_impl/src/mail_client_service_impl/__init__.py`): A seamless adapter that implements the original `Client` protocol while internally delegating to the auto-generated HTTP client. The adapter includes the `ServiceMessage` wrapper class that ensures complete interface compatibility and handles all HTTP-to-domain model transformations.

### Request Flow

The request flow demonstrates how a user's method call travels through the system with full observability and error handling at each layer:

1. **User Code**: Calls a method on what appears to be the original email client interface (e.g., `client.get_messages(max_results=5)`)
2. **Service Adapter**: Receives the call, validates parameters, and translates it into an HTTP request using the auto-generated client
3. **Auto-Generated HTTP Client**: Serializes the request, handles HTTP transport (including retries and timeouts), and manages the connection to the FastAPI service
4. **FastAPI Service**: Receives and validates the HTTP request, applies rate limiting and authentication if configured, then delegates to the original email implementation
5. **Original Email Library**: Performs the actual email operation (Gmail API calls, OAuth token management, etc.)
6. **Response Path**: Results flow back through the same components with proper error mapping, response transformation, and type safety at each layer

**Service Boundaries**: Each component can be deployed independently, scaled horizontally, and monitored separately for production environments.

### Sample API Responses

**List Messages Response** (`GET /messages?max_results=2`):
```json
[
  {
    "id": "msg_123",
    "from": "sender@example.com", 
    "to": "recipient@example.com",
    "date": "2025-10-03",
    "subject": "Test Message",
    "body": "This is a test message body"
  },
  {
    "id": "msg_456",
    "from": "another@example.com",
    "to": "recipient@example.com", 
    "date": "2025-10-02",
    "subject": "Another Message",
    "body": "Another message body"
  }
]
```

**Success Response** (`POST /messages/{message_id}/read`, `DELETE /messages/{message_id}`):
```json
{
  "success": true
}
```

**Error Response** (404 Not Found):
```json
{
  "detail": "Message not found"
}
```

## API Design

### Endpoints

The FastAPI service exposes the following REST endpoints with full OpenAPI documentation available at `/docs`:

* **GET /messages**: Lists messages from the inbox
  - Query parameters:
    - `max_results` (integer, default: 10, minimum: 1): Maximum number of messages to return
  - Returns: `200 OK` with Array of `MessageResponse` objects
  - Error responses: `500 Internal Server Error` for email service failures

* **GET /messages/{message_id}**: Retrieves a specific message by ID
  - Path parameters:
    - `message_id` (string, required): Unique identifier of the message
  - Returns: `200 OK` with Single `MessageResponse` object
  - Error responses: `404 Not Found` if message doesn't exist, `500 Internal Server Error` for service failures

* **POST /messages/{message_id}/read**: Marks a message as read
  - Path parameters:
    - `message_id` (string, required): Unique identifier of the message
  - Returns: `200 OK` with `SuccessResponse` containing boolean success field
  - Error responses: `404 Not Found` if message doesn't exist

* **DELETE /messages/{message_id}**: Deletes a specific message
  - Path parameters:
    - `message_id` (string, required): Unique identifier of the message
  - Returns: `200 OK` with `SuccessResponse` containing boolean success field
  - Error responses: `404 Not Found` if message doesn't exist

**Base URL**: Service runs on `http://127.0.0.1:8000` by default (configurable via environment variables)

### Error Handling

The service implements comprehensive error handling with proper HTTP status code mapping:

**HTTP Status Codes**:
* **200 OK**: Successful operations with valid responses
* **404 Not Found**: When a requested message ID doesn't exist or operations fail due to invalid message references
* **422 Unprocessable Entity**: When request parameters are invalid (automatically handled by FastAPI/Pydantic validation)
* **500 Internal Server Error**: When underlying email operations fail (connection issues, authentication failures, Gmail API errors)

**Error Response Format**:
All errors return a consistent JSON structure with a `detail` field containing the error message:
```json
{
  "detail": "Descriptive error message"
}
```

**Error Propagation**: The service gracefully catches exceptions from the underlying email library and maps them to appropriate HTTP responses, ensuring that sensitive internal details are not exposed to clients while providing meaningful error information.

## The Adapter Pattern

### Why It's Needed

The auto-generated HTTP client provides excellent type safety and HTTP handling but operates at a different abstraction level than the original domain-specific `Client` interface. Key compatibility gaps include:

* **Return Types**: The HTTP client returns `MessageResponse` DTOs while the original interface expects `Message` domain objects
* **Error Handling**: HTTP exceptions need to be translated to domain-appropriate error handling
* **Method Signatures**: HTTP client methods include additional parameters (headers, timeouts) not present in the original interface
* **Async vs Sync**: The generated client supports both sync and async operations, while the original interface is purely synchronous

The adapter pattern solves these incompatibilities by implementing the exact same `Client` abstract base class that users expect, ensuring zero code changes are required when switching between implementations.

### How It Works

The adapter (`MailClientAdapter`) provides seamless integration through several key mechanisms:

**Interface Implementation**:
```python
class MailClientAdapter(Client):

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.client = ServiceClient(base_url=base_url)

    def get_message(self, message_id: str) -> Message:
        result = get_message_sync(message_id=message_id, client=self.client)
        if hasattr(result, "additional_properties"):
            return ServiceMessage(result.additional_properties)
        if isinstance(result, dict):
            return ServiceMessage(result)
        msg = "Failed to fetch message"
        raise ValueError(msg)
```

**User Code Compatibility**:
```python
# This code works identically with both implementations:
client = mail_client_api.get_client(interactive=False)  # Returns adapter when service impl is active
messages = list(client.get_messages(max_results=3))      # Same interface, different backend
message = client.get_message(message_id)                 # Same return types
success = client.mark_as_read(message_id)                # Same error handling
success = client.delete_message(message_id)              # Same behavior
```

**Message Wrapping**: The `ServiceMessage` class implements all `Message` interface properties (`id`, `from_`, `to`, `date`, `subject`, `body`), ensuring complete behavioral compatibility.

**Dependency Injection Integration**: The adapter integrates with the existing dependency injection system, allowing transparent switching between local and service-based implementations through configuration.

## Deployment & Operations

### Service Deployment

**Development Mode**:
```bash
# Start the FastAPI service
cd src/mail_client_service
python -m mail_client_service.main
# Service runs on http://127.0.0.1:8000 with auto-reload
```

**Production Considerations**:
* **Process Management**: Use a production ASGI server like Gunicorn with Uvicorn workers
* **Reverse Proxy**: Deploy behind nginx or similar for SSL termination and load balancing
* **Environment Variables**: Configure base URLs, authentication, and service discovery through environment variables
* **Health Checks**: The service exposes standard FastAPI health endpoints for container orchestration
* **Monitoring**: Built-in OpenAPI documentation at `/docs` and `/redoc` for service introspection

### Configuration Management

**Service Discovery**: The adapter accepts a configurable `base_url` parameter, enabling dynamic service discovery in containerized environments.

**Workspace Integration**: The service is integrated into the uv workspace (`pyproject.toml`) as a separate package, enabling independent versioning and deployment.

### Scalability

* **Horizontal Scaling**: Multiple service instances can be deployed behind a load balancer
* **Stateless Design**: The service maintains no internal state, making it suitable for container orchestration
* **Resource Isolation**: Email processing can be scaled independently from client applications

## Testing Strategy

### What You Tested

The comprehensive testing strategy covers all architectural layers and integration points:

* **FastAPI Service Layer**: Direct testing of REST endpoints, request/response serialization, error handling, and dependency injection
* **Auto-Generated Client**: Validation of HTTP client functionality, error propagation, and type safety
* **Service Adapter**: Verification that `MailClientAdapter` correctly implements the `Client` interface with proper domain object wrapping
* **End-to-End Integration**: Complete request flow testing from user code through all service layers to email operations
* **Interface Compliance**: Behavioral verification that the service-based implementation produces identical results to the original direct implementation

### Test Types

The test suite follows a pyramid structure with comprehensive coverage at each level:

* **Unit Tests**: Individual component testing with mocked dependencies, focusing on business logic and error handling
* **Integration Tests** (`tests/integration/test_mail_client_service.py`): Service-to-service testing with a running FastAPI service process, using mocked Gmail operations to ensure HTTP layer functionality
* **End-to-End Tests** (`tests/e2e/`): Full system testing that verifies the complete flow from user code through all components, including actual service startup and teardown
* **Contract Tests**: Verification that the adapter maintains strict behavioral compatibility with the original interface

**Test Isolation**: Each test type uses appropriate isolation techniques to ensure fast, reliable, and independent test execution.

### Mocking Strategy

The testing approach uses layered mocking to provide comprehensive coverage while maintaining test performance:

**Layer-Specific Mocking**:
* **Integration Tests**: Mock the underlying Gmail client (`mail_client_api.get_client`) while preserving real HTTP communication, ensuring network serialization and transport layer functionality
* **Service Process Isolation**: Run the FastAPI service in a separate multiprocessing.Process during integration tests (port 8001) to ensure realistic HTTP client-server interaction
* **Gmail API Mocking**: Use `unittest.mock.patch` to provide controlled, predictable responses from the Gmail service layer
* **Fixture Management**: Pytest fixtures provide consistent mock configurations across test suites with proper setup and teardown

**Mock Data Management**: Standardized mock message creation (`create_mock_message()`) ensures consistent test data across all test types.

**Real vs Mock Boundaries**: Clear separation between what's mocked (external APIs) and what's real (internal HTTP communication, serialization, type conversion) ensures confidence in the service layer implementation.

### Interface Compliance

Interface compliance is rigorously verified through multiple validation approaches:

**Static Analysis**:
* **Type Checking**: The adapter implements the abstract `Client` protocol with full mypy strict mode compliance, ensuring compile-time interface correctness
* **Protocol Validation**: All method signatures, return types, and exception behaviors match the original interface specification

**Dynamic Verification**:
* **Behavioral Testing**: Integration tests verify that all methods return the expected types (`Message` objects, boolean results) and handle errors appropriately
* **Response Transformation**: Tests validate that `ServiceMessage` wrapper objects properly implement all `Message` interface properties
* **Error Handling Compliance**: Verification that adapter error handling matches original implementation behavior

**Compatibility Testing**:
* **Drop-in Replacement**: End-to-end tests demonstrate that existing user code works identically with both implementations
* **Dependency Injection Integration**: Tests verify that the adapter correctly integrates with the existing factory function mechanism
* **Mock Verification**: Detailed verification that the adapter makes correct HTTP client calls with proper parameter mapping and response handling

**Continuous Validation**: The test suite runs in CI/CD to ensure interface compliance is maintained across code changes and refactoring.