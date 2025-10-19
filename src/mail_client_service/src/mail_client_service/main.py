"""FastAPI service exposing mail_client_api.Client endpoints."""

import os
from typing import Annotated

if os.environ.get("MOCK_CLIENT") == "1":
    from . import test_client
    test_client.register()
else:
    import gmail_client_impl  # type: ignore[no-redef] # noqa: F401
from fastapi import Depends, FastAPI, HTTPException
from mail_client_api import get_client
from mail_client_api.client import Client

app = FastAPI()

def get_client_dep() -> Client:
    """Dependency to get the mail client instance."""
    client = get_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Mail client initialization failed")
    return client


@app.get("/messages")
def get_messages(
    client: Annotated[Client, Depends(get_client_dep)],
    max_results: int = 10,
) -> list[dict[str, str]]:
    """Return a list of message summaries."""
    if max_results < 1:
        raise HTTPException(status_code=400, detail="max_results must be at least 1")
    try:
        return [
            {
                "id": msg.id,
                "from": msg.from_,
                "to": msg.to,
                "date": msg.date,
                "subject": msg.subject,
                "body": msg.body,
            }
            for msg in client.get_messages(max_results=max_results)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e


@app.get("/messages/{message_id}")
def get_message(
    message_id: str,
    client: Annotated[Client, Depends(get_client_dep)],
) -> dict[str, str]:
    """Return the full detail of a single message."""
    try:
        message = client.get_message(message_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail="Message not found") from e
    else:
        return {
            "id": message.id,
            "from": message.from_,
            "to": message.to,
            "date": message.date,
            "subject": message.subject,
            "body": message.body,
        }


@app.post("/messages/{message_id}/mark-as-read")
def mark_as_read(
    message_id: str,
    client: Annotated[Client, Depends(get_client_dep)],
) -> dict[str, bool]:
    """Mark a message as read."""
    result = client.mark_as_read(message_id)
    if not result:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"success": True}


@app.delete("/messages/{message_id}")
def delete_message(
    message_id: str,
    client: Annotated[Client, Depends(get_client_dep)],
) -> dict[str, bool]:
    """Delete a message."""
    result = client.delete_message(message_id)
    if not result:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"success": True}
