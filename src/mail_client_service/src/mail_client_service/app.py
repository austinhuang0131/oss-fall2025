"""FastAPI service implementation for the mail client.

This module provides a REST API service that implements the mail client operations.
"""

from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query, Path
from pydantic import BaseModel, Field
from mail_client_api.test_client import TestClient as Client

app = FastAPI(
    title="Mail Client Service",
    description="A REST API service that implements mail client operations",
    version="1.0.0",
)

def get_client():
    """Return an instance of the mail client."""
    return Client()

class MessageResponse(BaseModel):
    """Represents an email message response."""
    id: str = Field(..., description="Unique identifier of the message")
    from_: str = Field(..., description="Sender's email address", alias="from")
    to: str = Field(..., description="Recipient's email address")
    date: str = Field(..., description="Date the message was sent")
    subject: str = Field(..., description="Subject line of the message")
    body: str = Field("", description="Body content of the message")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "id": "msg_123",
                "from": "sender@example.com",
                "to": "recipient@example.com",
                "date": "2025-10-03",
                "subject": "Test Message",
                "body": "This is a test message body"
            }
        }

class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = Field(..., description="Whether the operation was successful")

# Dependency injection for the mail client
def get_mail_client() -> Client:
    """Dependency to get a mail client instance."""
    return Client()

@app.get("/messages", response_model=List[MessageResponse], tags=["messages"])
def list_messages(
    max_results: int = Query(10, description="Maximum number of messages to return", ge=1),
    client: Client = Depends(get_mail_client)
):
    """List messages from the mail client.
    
    Returns a list of messages with their details.
    """
    try:
        messages = list(client.get_messages(max_results=max_results))
        return [
            {
                "id": msg.id,
                "from": msg.from_,
                "to": msg.to,
                "date": msg.date,
                "subject": msg.subject,
                "body": msg.body
            }
            for msg in messages
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error") from e

@app.get("/messages/{message_id}", response_model=MessageResponse, tags=["messages"])
def get_message(
    message_id: str = Path(..., description="ID of the message to retrieve"),
    client: Client = Depends(get_mail_client)
):
    """Get a specific message by its ID.
    
    Returns the message details if found, otherwise raises a 404 error.
    """
    try:
        message = client.get_message(message_id)
        return {
            "id": message.id,
            "from": message.from_,
            "to": message.to,
            "date": message.date,
            "subject": message.subject,
            "body": message.body
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail="Message not found") from e

@app.post("/messages/{message_id}/read", response_model=SuccessResponse, tags=["messages"])
def mark_as_read(
    message_id: str = Path(..., description="ID of the message to mark as read"),
    client: Client = Depends(get_mail_client)
):
    """Mark a message as read.
    
    Returns success response if marked as read, otherwise raises a 404 error.
    """
    success = client.mark_as_read(message_id=message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"success": True}

@app.delete("/messages/{message_id}", response_model=SuccessResponse, tags=["messages"])
def delete_message(
    message_id: str = Path(..., description="ID of the message to delete"),
    client: Client = Depends(get_mail_client)
):
    """Delete a specific message.
    
    Returns success status. Raises 404 if message is not found.
    """
    success = client.delete_message(message_id=message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"success": True}
