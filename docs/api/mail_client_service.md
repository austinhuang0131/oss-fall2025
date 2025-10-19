# Mail Client Adapter Implementation

`mail_client_service` implements a FastAPI application to expose any `mail_client_api` clients (like `gmail_client_impl`) as a REST API. It also includes a REST API client to interact with it, which is in turn used by `mail_client_adapter`. The package will import the active `gmail_client_impl` if exists.