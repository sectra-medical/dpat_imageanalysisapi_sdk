from http import HTTPStatus
from typing import Any, List, Optional

import httpx
import pytest

from sectra_dpat_downloader.client import SectraDpatDownloader
from sectra_dpat_downloader.http_client import HttpClient

BASE_URL = "http://test.example.com"
APPLICATION_ID = "app-1"
TOKEN_PATH = "/token"


class FakeServer:
    """An IA-API behind an httpx mock transport. Token requests are granted;
    the other requests are recorded and answered with the response set."""

    def __init__(self):
        self.requests: List[httpx.Request] = []
        self._status = HTTPStatus.OK
        self._json: Any = None
        self._content: Optional[bytes] = None

    def respond_with(
        self,
        status: HTTPStatus = HTTPStatus.OK,
        json: Any = None,
        content: Optional[bytes] = None,
    ) -> None:
        self._status = status
        self._json = json
        self._content = content

    def handle(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == TOKEN_PATH:
            return httpx.Response(
                HTTPStatus.OK,
                json={
                    "access_token": "test-token",
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
            )
        request.read()
        self.requests.append(request)
        if self._json is not None:
            return httpx.Response(self._status, json=self._json)
        return httpx.Response(self._status, content=self._content)


@pytest.fixture()
def server() -> FakeServer:
    return FakeServer()


@pytest.fixture()
def chunk_size() -> int:
    return 64 * 1024 * 1024


@pytest.fixture()
def client(server: FakeServer, chunk_size: int) -> SectraDpatDownloader:
    httpx_client = httpx.Client(transport=httpx.MockTransport(server.handle))
    http_client = HttpClient(
        BASE_URL, "user", "pass", APPLICATION_ID, client=httpx_client
    )
    return SectraDpatDownloader(http_client, APPLICATION_ID, chunk_size)
