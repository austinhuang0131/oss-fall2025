"""FastAPI application with OpenTelemetry instrumentation that runs AiChatTicketIntegration."""

from __future__ import annotations

import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai_chat_ticket_integration import AiChatTicketIntegration
from discord_client_impl.discord_impl import DiscordClient
from dotenv import load_dotenv
from fastapi import FastAPI
from openai_impl import OpenAIClient  # type: ignore[import-untyped]
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pydantic import BaseModel
from trello_ticket_impl.trello_ticket_impl import TrelloTicketClientImpl

# Load environment variables
_ = load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Pydantic models for API responses
class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    timestamp: float


# Initialize OpenTelemetry
def setup_telemetry() -> tuple[trace.Tracer, metrics.Meter]:
    """Set up OpenTelemetry tracing and metrics.

    For Cloud Run, this uses the default OTLP exporters which automatically
    send telemetry to Google Cloud Operations when GOOGLE_APPLICATION_CREDENTIALS
    is set and the service account has the required permissions.
    """
    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": "ai-ticket-api-service",
            "service.version": "0.1.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        },
    )

    # Set up OpenTelemetry Python SDK with OTLP exporters
    # Cloud Run automatically sets OTEL_EXPORTER_OTLP_ENDPOINT to route to Google Cloud Operations
    # For local development, set OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 if needed
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(tracer_provider)

    # Metrics are exported every 60 seconds by default
    reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    meter_provider = MeterProvider(metric_readers=[reader], resource=resource)
    metrics.set_meter_provider(meter_provider)

    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)

    logger.info("OpenTelemetry configured for Cloud Run with OTLP exporters")
    logger.info("Service: %s, Environment: %s",
                resource.attributes.get("service.name"),
                resource.attributes.get("deployment.environment"))

    return tracer, meter


# Initialize telemetry
tracer, meter = setup_telemetry()



# Global integration instance
integration_instance: AiChatTicketIntegration | None = None
integration_task: asyncio.Task[None] | None = None


def load_configuration() -> dict[str, str]:
    """Load configuration from environment variables.

    Returns:
        Dictionary with configuration values

    Raises:
        ValueError: If required environment variables are missing

    """
    config = {
        "discord_token": os.getenv("DISCORD_ACCESS_TOKEN", ""),
        "channel_id": os.getenv("TEST_DISCORD_CHANNEL_ID", ""),
        "trello_token": os.getenv("TRELLO_TOKEN", ""),
        "trello_board_id": os.getenv("TEST_TRELLO_BOARD_ID", ""),
        "openai_api_key": os.getenv("TEST_OPENAI_API_KEY", ""),
        "poll_interval": os.getenv("POLL_INTERVAL", "1.0"),
        "user_id": os.getenv("BOT_USER_ID", ""),
    }

    # Validate required fields
    missing = [k for k, v in config.items() if not v and k != "trello_board_id" and k != "user_id"]
    if missing:
        msg = f"Missing required environment variables: {', '.join(missing)}"
        raise ValueError(msg)
    if config["user_id"] == "":
        print("Warning: BOT_USER_ID not set, bot may respond to its own messages.")

    return config


def create_integration() -> AiChatTicketIntegration:
    """Create an AiChatTicketIntegration instance from environment configuration.

    Returns:
        Configured integration instance

    """
    config = load_configuration()

    # Create client instances
    discord_client = DiscordClient(access_token=config["discord_token"])
    trello_client = TrelloTicketClientImpl(
        token=config["trello_token"],
        board_id=config["trello_board_id"] or None,
    )
    openai_client = OpenAIClient(api_key=config["openai_api_key"])

    # Create integration
    integration = AiChatTicketIntegration(
        chat_api=discord_client,  # type: ignore[arg-type]
        ticket_api=trello_client,
        ai_api=openai_client,  # type: ignore[arg-type]
        channel_id=config["channel_id"],
        bot_user_id=config["user_id"] if "user_id" in config else None,
        poll_interval=float(config["poll_interval"]),
    )

    logger.info("Created integration with channel_id=%s", config["channel_id"])
    return integration


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for startup and shutdown."""
    global integration_instance, integration_task

    # Startup
    logger.info("Starting AI Ticket API Service")
    logger.info("OpenTelemetry endpoint: %s", os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))

    try:
        # Create and start integration
        integration_instance = create_integration()
        integration_task = asyncio.create_task(integration_instance.start())
        logger.info("Integration started successfully")

    except Exception:
        logger.exception("Failed to start integration")
        raise

    yield

    # Shutdown
    logger.info("Shutting down AI Ticket API Service")
    if integration_instance:
        integration_instance.stop()
    if integration_task:
        _ = integration_task.cancel()
        try:
            await integration_task
        except asyncio.CancelledError:
            pass


# Create FastAPI app
app = FastAPI(
    title="AI Ticket API Service",
    description="Runs AI-powered ticket management integration with OpenTelemetry monitoring",
    version="0.1.0",
    lifespan=lifespan,
)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)


@app.get("/", response_model=dict[str, str])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": "AI Ticket API Service",
        "version": "0.1.0",
        "description": "Running AI chat ticket integration with OpenTelemetry monitoring",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    status = "healthy"
    if integration_instance is None or not getattr(integration_instance, "_running", False):
        status = "unhealthy"

    return HealthResponse(
        status=status,
        version="0.1.0",
        timestamp=time.time(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ai_ticket_api_service.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=True,
    )
