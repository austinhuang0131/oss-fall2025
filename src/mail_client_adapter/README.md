# mail-client-adapter

Adapter for `mail_client_api.Client` that proxies calls to a running FastAPI mail_client_service. Consumers use this as a drop-in replacement for the local client, with all network complexity hidden.

## Usage

```python
from mail_client_adapter import RemoteMailClient
client = RemoteMailClient(base_url="http://localhost:8000")
messages = list(client.get_messages())
```
