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


class MetricsResponse(BaseModel):
    """Metrics response."""

    total_requests: int
    successful_requests: int
    failed_requests: int
    success_rate: float
    failure_rate: float
    avg_latency_ms: float


# Initialize OpenTelemetry
def setup_telemetry() -> tuple[trace.Tracer, metrics.Meter]:
    """Set up OpenTelemetry tracing and metrics."""
    # Create resource with service information
    resource = Resource.create(
        {
            "service.name": "ai-ticket-api-service",
            "service.version": "0.1.0",
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        },
    )

    # Set up tracing
    trace_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
        insecure=True,
    )
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)

    # Set up metrics
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
            insecure=True,
        ),
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    tracer = trace.get_tracer(__name__)
    meter = metrics.get_meter(__name__)

    return tracer, meter


# Initialize telemetry
tracer, meter = setup_telemetry()


# In-memory metrics storage (for /metrics endpoint)
class MetricsStorage:
    """Simple in-memory storage for aggregated metrics from integration."""

    def __init__(self) -> None:
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_latency_ms = 0.0

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests


metrics_storage = MetricsStorage()

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
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
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
        integration_task.cancel()
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
        "description": "Running AI chat ticket integration",
        "health": "/health",
        "metrics": "/metrics",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    status = "healthy"
    if integration_instance is None or not integration_instance._running:
        status = "unhealthy"

    return HealthResponse(
        status=status,
        version="0.1.0",
        timestamp=time.time(),
    )


@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Get current metrics.

    Note: These are read from OpenTelemetry metrics exported by the integration.
    The integration class emits metrics for message processing.
    """
    return MetricsResponse(
        total_requests=metrics_storage.total_requests,
        successful_requests=metrics_storage.successful_requests,
        failed_requests=metrics_storage.failed_requests,
        success_rate=metrics_storage.success_rate,
        failure_rate=metrics_storage.failure_rate,
        avg_latency_ms=metrics_storage.avg_latency_ms,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ai_ticket_api_service.app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        reload=True,
    )
