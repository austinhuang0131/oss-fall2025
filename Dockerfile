# Dockerfile for the FastAPI service using uv

FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set work directory
WORKDIR /app

# Copy all source code and workspace config
COPY . /app

# Install all dependencies using uv sync (from uv.lock)
RUN uv sync --all-packages

# Expose port for FastAPI
EXPOSE 8000

# Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Run FastAPI app using uv
CMD ["uv", "run", "uvicorn", "mail_client_service:app", "--host", "0.0.0.0", "--port", "8000"]

# Healthcheck: expects a 404 response from root
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
	CMD wget --spider --server-response http://0.0.0.0:8000 2>&1 | grep '{"detail":"Not Found"}' || exit 1
