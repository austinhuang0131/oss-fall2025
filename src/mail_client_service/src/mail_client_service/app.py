from fastapi import FastAPI, Depends, HTTPException
from mail_client_api import get_client, Client

app = FastAPI()

# Dependency injection for the mail client
def get_mail_client() -> Client:
    return get_client()

@app.get("/messages")
def list_messages(client: Client = Depends(get_mail_client)):
    return client.list_messages()

@app.get("/messages/{message_id}")
def get_message(message_id: str, client: Client = Depends(get_mail_client)):
    message = client.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@app.post("/messages/{message_id}/mark-as-read")
def mark_as_read(message_id: str, client: Client = Depends(get_mail_client)):
    result = client.mark_as_read(message_id)
    if not result:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"success": True}

@app.delete("/messages/{message_id}")
def delete_message(message_id: str, client: Client = Depends(get_mail_client)):
    result = client.delete_message(message_id)
    if not result:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"success": True}
