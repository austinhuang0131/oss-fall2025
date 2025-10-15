# mail-client-service

FastAPI service for mail client abstraction. Wraps `mail_client_api.Client` and exposes RESTful endpoints for message operations.

## Endpoints
- `GET /messages`: List message summaries
- `GET /messages/{message_id}`: Get message details
- `POST /messages/{message_id}/mark-as-read`: Mark message as read
- `DELETE /messages/{message_id}`: Delete message
