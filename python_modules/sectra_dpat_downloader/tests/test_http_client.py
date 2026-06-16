import json as jsonlib
from http import HTTPStatus
from typing import Callable, List

import httpx

from sectra_dpat_downloader.http_client import HttpClient

TOKEN_PATH = "/token"


def _token_response() -> httpx.Response:
    return httpx.Response(
        HTTPStatus.OK,
        json={
            "access_token": "test-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )


def _make_client(handler: Callable[[httpx.Request], httpx.Response]) -> HttpClient:
    """Build an HttpClient backed by a mock transport using the given handler."""
    transport = httpx.MockTransport(handler)
    httpx_client = httpx.Client(transport=transport)
    return HttpClient(
        "http://test.example.com", "user", "pass", "app-id", client=httpx_client
    )


class TestPost:
    def test_post_sends_json_body(self):
        # Arrange
        captured: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == TOKEN_PATH:
                return _token_response()
            captured.append(request)
            return httpx.Response(HTTPStatus.CREATED, json={})

        client = _make_client(handler)

        # Act
        result = client.post("/test", json={"key": "value"})

        # Assert
        assert len(captured) == 1
        assert captured[0].method == "POST"
        assert str(captured[0].url) == "http://test.example.com/test"
        assert jsonlib.loads(captured[0].content) == {"key": "value"}
        assert result.status_code == HTTPStatus.CREATED

    def test_post_sends_bearer_token(self):
        # Arrange
        captured: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == TOKEN_PATH:
                return _token_response()
            captured.append(request)
            return httpx.Response(HTTPStatus.CREATED, json={})

        client = _make_client(handler)

        # Act
        client.post("/test", json={})

        # Assert
        assert captured[0].headers["Authorization"] == "Bearer test-token"

    def test_post_refreshes_token_on_401(self):
        # Arrange
        token_calls = 0
        test_calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal token_calls, test_calls
            if request.url.path == TOKEN_PATH:
                token_calls += 1
                return _token_response()
            test_calls += 1
            if test_calls == 1:
                return httpx.Response(HTTPStatus.UNAUTHORIZED)
            return httpx.Response(HTTPStatus.CREATED, json={})

        client = _make_client(handler)

        # Act
        result = client.post("/test", json={})

        # Assert
        assert test_calls == 2
        assert token_calls == 2  # initial fetch + refresh after 401
        assert result.status_code == HTTPStatus.CREATED


class TestPut:
    def test_put_sends_json_body(self):
        # Arrange
        captured: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == TOKEN_PATH:
                return _token_response()
            captured.append(request)
            return httpx.Response(HTTPStatus.OK, json={})

        client = _make_client(handler)

        # Act
        result = client.put("/test", json={"key": "value"})

        # Assert
        assert len(captured) == 1
        assert captured[0].method == "PUT"
        assert str(captured[0].url) == "http://test.example.com/test"
        assert jsonlib.loads(captured[0].content) == {"key": "value"}
        assert result.status_code == HTTPStatus.OK

    def test_put_refreshes_token_on_403(self):
        # Arrange
        token_calls = 0
        test_calls = 0

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal token_calls, test_calls
            if request.url.path == TOKEN_PATH:
                token_calls += 1
                return _token_response()
            test_calls += 1
            if test_calls == 1:
                return httpx.Response(HTTPStatus.FORBIDDEN)
            return httpx.Response(HTTPStatus.OK, json={})

        client = _make_client(handler)

        # Act
        result = client.put("/test", json={})

        # Assert
        assert test_calls == 2
        assert token_calls == 2  # initial fetch + refresh after 403
        assert result.status_code == HTTPStatus.OK


class TestToken:
    def test_token_request_uses_basic_auth(self):
        # Arrange
        token_requests: List[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == TOKEN_PATH:
                token_requests.append(request)
                return _token_response()
            return httpx.Response(HTTPStatus.OK, json={})

        client = _make_client(handler)

        # Act
        client.get("/test")

        # Assert
        # "user:pass" base64-encoded is dXNlcjpwYXNz.
        assert token_requests[0].headers["Authorization"] == "Basic dXNlcjpwYXNz"
        assert "applicationId=app-id" in str(token_requests[0].url)
