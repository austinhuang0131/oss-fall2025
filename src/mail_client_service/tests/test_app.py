from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.mail_client_service.app import app
import pytest

client = TestClient(app)

@pytest.fixture
def mock_mail_client():
    with patch('src.mail_client_service.app.get_mail_client') as mock:
        mock_instance = MagicMock()
        mock.return_value = mock_instance
        yield mock_instance

def test_list_messages(mock_mail_client):
    mock_mail_client.list_messages.return_value = [{"id": "1", "snippet": "Hello"}]
    response = client.get("/messages")
    assert response.status_code == 200
    assert response.json() == [{"id": "1", "snippet": "Hello"}]

def test_get_message_found(mock_mail_client):
    mock_mail_client.get_message.return_value = {"id": "1", "snippet": "Hello"}
    response = client.get("/messages/1")
    assert response.status_code == 200
    assert response.json() == {"id": "1", "snippet": "Hello"}

def test_get_message_not_found(mock_mail_client):
    mock_mail_client.get_message.return_value = None
    response = client.get("/messages/999")
    assert response.status_code == 404

def test_mark_as_read_success(mock_mail_client):
    mock_mail_client.mark_as_read.return_value = True
    response = client.post("/messages/1/mark-as-read")
    assert response.status_code == 200
    assert response.json() == {"success": True}

def test_mark_as_read_not_found(mock_mail_client):
    mock_mail_client.mark_as_read.return_value = False
    response = client.post("/messages/999/mark-as-read")
    assert response.status_code == 404

def test_delete_message_success(mock_mail_client):
    mock_mail_client.delete_message.return_value = True
    response = client.delete("/messages/1")
    assert response.status_code == 200
    assert response.json() == {"success": True}

def test_delete_message_not_found(mock_mail_client):
    mock_mail_client.delete_message.return_value = False
    response = client.delete("/messages/999")
    assert response.status_code == 404
