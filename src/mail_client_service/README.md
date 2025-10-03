# mail-client-service

A FastAPI microservice that exposes a RESTful API for your mail client, wrapping the logic from the `mail-client-api` package. This service provides endpoints to fetch, read, and delete messages using your existing mail client implementation.

## Features
- List message summaries
- Fetch full message details
- Mark messages as read
- Delete messages

## Endpoints

### GET `/messages`
- **Description:** List message summaries
- **Response:**
  - `200 OK`: List of message summaries (JSON array)

### GET `/messages/{message_id}`
- **Description:** Get full details of a message
- **Response:**
  - `200 OK`: Message details (JSON object)
  - `404 Not Found`: Message does not exist

### POST `/messages/{message_id}/mark-as-read`
- **Description:** Mark a message as read
- **Response:**
  - `200 OK`: `{ "success": true }` if successful
  - `404 Not Found`: Message does not exist

### DELETE `/messages/{message_id}`
- **Description:** Delete a message
- **Response:**
  - `200 OK`: `{ "success": true }` if successful
  - `404 Not Found`: Message does not exist

## Usage

### Install dependencies
This package uses PEP 621/pyproject.toml. Install dependencies from the project root:

```sh
uv sync --all-packages --extra dev
```

### Run the service
From the package directory:

```sh
uvicorn src.mail_client_service.app:app --reload
```

### Run tests
From the package directory:

```sh
pytest
```

## Development
- The FastAPI app is in `src/mail_client_service/app.py`.
- Unit tests are in `src/mail_client_service/tests/` and use mocks for the mail client.
- All business logic is delegated to the `mail-client-api` package; this service is a thin HTTP wrapper.

## Requirements
- Python 3.11+
- `mail-client-api` and its dependencies
- FastAPI, Uvicorn, pytest (see `pyproject.toml`)
