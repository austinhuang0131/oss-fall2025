# AI Ticket API Service

FastAPI service that runs an `AiChatTicketIntegration` instance with OpenTelemetry instrumentation.

## Features

- **Automated Integration**: Runs AI chat ticket integration continuously
- **Configuration-Based**: All clients configured via environment variables
- **OpenTelemetry**: Distributed tracing and metrics exported from integration
- **Health Checks**: `/health` and `/metrics` endpoints
- **Auto-generated Documentation**: Swagger UI at `/docs`

## Telemetry

The integration emits the following metrics via OpenTelemetry:

- **Request Latency**: Histogram of message processing duration (`integration_request_duration`)
- **Success Rate**: Counter of successfully processed messages (`integration_requests_success`)
- **Failure Rate**: Counter of failed message processing attempts (`integration_requests_failure`)
- **Total Requests**: Counter of all processed messages (`integration_requests_total`)

Metrics are exported via OTLP (OpenTelemetry Protocol) to a collector endpoint and include `channel_id` labels.

## Installation

```bash
cd src/ai_ticket_api_service
pip install -e ".[dev]"
```

## Configuration

Set the following environment variables (or use a `.env` file):

**Service Configuration:**
- `PORT`: Server port (default: `8080`)
- `ENVIRONMENT`: Deployment environment (default: `development`)
- `OTEL_EXPORTER_OTLP_ENDPOINT`: OpenTelemetry collector endpoint (default unset)

**Integration Configuration:**
- `DISCORD_ACCESS_TOKEN`: Discord bot token (required)
- `TEST_DISCORD_CHANNEL_ID`: Discord channel ID to monitor (required)
- `TRELLO_TOKEN`: Trello OAuth token (required)
- `TEST_TRELLO_BOARD_ID`: Trello board ID (optional, creates if not provided)
- `TEST_OPENAI_API_KEY`: OpenAI API key (required)
- `POLL_INTERVAL`: Message polling interval in seconds (default: `1.0`)

## Running Locally

### Start OpenTelemetry Collector

```bash
# Using Docker
docker run -d \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 55679:55679 \
  otel/opentelemetry-collector:latest
```

### Start the API Service

```bash
uvicorn ai_ticket_api_service.app:app --reload --port 8080
```

Or run directly:

```bash
python -m ai_ticket_api_service.app
```

## API Endpoints

The service runs the integration in the background. It provides monitoring endpoints only:

### Health & Monitoring

- `GET /` - Service information
- `GET /health` - Health check (status: healthy/unhealthy based on integration state)
- `GET /metrics` - Current aggregated metrics from integration

The integration automatically polls the configured Discord channel and processes messages.

## Example Usage

### Check Service Health

```bash
curl http://localhost:8080/health
```

### View Aggregated Metrics

```bash
curl http://localhost:8080/metrics
```

### Interact with the Integration

Send messages in the configured Discord channel:

```
# In Discord channel
Create a ticket called "Fix login bug" with description "Users can't login"

# The service automatically processes the message and creates a ticket
```

## Deployment

See [Terraform Configuration](../../terraform/README.md) for deploying to Google Cloud Run.

## Development

### Run Tests

```bash
pytest
```

### Run Linting

```bash
ruff check .
ruff format .
```

### Type Checking

```bash
mypy src/ai_ticket_api_service
```

## Monitoring Dashboard

When deployed to Google Cloud, metrics are automatically sent to Cloud Monitoring. Create a dashboard with:

1. **Request Latency Chart**: Line chart showing `api_request_duration` over time
2. **Success/Failure Rate**: Pie chart showing ratio of successful vs failed requests
3. **Request Volume**: Bar chart showing `api_requests_total` by endpoint
4. **Error Rate Alert**: Alert when failure rate exceeds 5% for 5 minutes

## Architecture

The service wraps the `AiChatTicketIntegration` class which continuously polls for messages and processes them:

```
┌─────────────────────┐
│  FastAPI Service    │
│  (Health/Metrics)   │
└──────────┬──────────┘
           │
           │ runs
           ▼
┌─────────────────────────────┐      ┌──────────────┐
│ AiChatTicketIntegration     │─────▶│ Discord      │
│ (polls & processes messages)│      │ (Chat API)   │
└─────────────────────────────┘      └──────────────┘
           │                                  
           ├────────────────────┐            
           ▼                    ▼            
    ┌──────────┐         ┌──────────┐       
    │ OpenAI   │         │ Trello   │       
    │ (AI API) │         │ (Tickets)│       
    └──────────┘         └──────────┘       
           │
           │ OTLP
           ▼
    ┌──────────────────┐
    │ OTel Collector   │
    │ (Cloud Monitoring)│
    └──────────────────┘
```

The integration emits OpenTelemetry metrics for all message processing operations.
