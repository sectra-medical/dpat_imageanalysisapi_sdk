# Backend for Sectra DPAT IA-API Example: External Viewer

Simple Python FastApi web application that proxies the requests from the front end client to the Sectra DPAT server.

## Configuration

Configure the app by creating an .env file. Set `WEB_APP_URL` to the URL that the frontend runs on. Optionally set `IGNORE_SSL_ERRORS` to ignore any ssl errors when making requests to the DPAT server.

```env
WEB_APP_URL=http://localhost:5173
IGNORE_SSL_ERRORS=true
```

## Running

Run using uv

```sh
uv run python .\src\dpat_ia_api_external_viewer\app.py
```

The server listens by default on port 8000.