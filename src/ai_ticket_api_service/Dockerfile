# Multi-stage build for AI Ticket API Service
FROM python:3.11-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Install git for dependency management or source control
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy workspace configuration
COPY pyproject-docker.toml ./pyproject.toml

# Copy all source packages needed for the service
COPY src/ai_ticket_api_service ./src/ai_ticket_api_service
COPY src/ai_chat_ticket_integration ./src/ai_chat_ticket_integration
COPY src/trello_ticket_impl ./src/trello_ticket_impl
COPY src/trello_client_impl ./src/trello_client_impl
COPY src/kanban_client_api ./src/kanban_client_api

# Install dependencies
RUN uv sync --all-packages --no-dev --extra telemetry
RUN uv pip install uvicorn[standard]

# Final runtime stage
FROM python:3.11-slim

# Install ca-certificates for HTTPS requests
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copy installed dependencies from builder
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv
COPY --from=builder --chown=appuser:appuser /app/src ./src

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# Set PYTHONPATH and run the application
ENV PYTHONPATH="/app/src:/app/src/ai_chat_ticket_integration/src:/app/src/trello_ticket_impl/src:/app/src/ai_ticket_api_service/src:/app/src/trello_client_impl/src:/app/src/kanban_client_api/src"
CMD ["python", "-m", "uvicorn", "ai_ticket_api_service.app:app", "--host", "0.0.0.0", "--port", "8080"]
