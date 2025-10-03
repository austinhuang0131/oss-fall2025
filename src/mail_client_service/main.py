"""Entry point for the FastAPI application."""

import uvicorn

def main():
    """Start the FastAPI application."""
    uvicorn.run(
        "mail_client_service.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()
