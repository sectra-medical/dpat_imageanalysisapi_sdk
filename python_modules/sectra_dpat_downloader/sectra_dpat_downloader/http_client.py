import datetime
import threading
from http import HTTPStatus
from typing import Optional

import httpx

from sectra_dpat_downloader.models import Token


class HttpClient:
    """Http client that handles token authentication and refreshing."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        application_id: str,
        client: Optional[httpx.Client] = None,
    ):
        """Create a http client.

        Parameters
        ----------
        base_url: str
            Base url for client requests.
        username: str
            Username to use for requesting token.
        password: str
            Password to use for requesting token.
        application_id:
            Application id to use for requesting token.
        client: Optional[httpx.Client]
            HTTP client to use. Provide a configured client to control timeouts,
            TLS verification or proxies, e.g. when managed by a dependency
            injection container. Defaults to a client with a 30 second timeout.
        """
        self._base_url = base_url
        self._username = username
        self._password = password
        self._application_id = application_id
        self._owns_client = client is None
        self._client = client if client is not None else httpx.Client(timeout=30.0)
        self._token_valid_until: Optional[datetime.datetime] = None
        self._token_lock = threading.Lock()
        self._token_generation = 0

    def close(self) -> None:
        """Close the underlying HTTP client and release pooled connections.

        Only closes the client if it was created by this instance. An
        externally supplied client is left for its owner to close.
        """
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "HttpClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def get(self, url: str, stream: bool = False) -> httpx.Response:
        """Get response from url.

        Parameters
        ----------
        url: str
            Url to get response from.
        stream: bool = False
            If to stream the response. A streamed response must be closed by the
            caller once consumed.

        Returns
        -------
        httpx.Response
            Response with 2xx-status.

        """
        generation = self._ensure_token()
        response = self._request_with_retry(
            "GET", self._base_url + url, 1, generation, stream=stream
        )
        return self._raise_for_status(response)

    def _ensure_token(self) -> int:
        """Ensure a non-expired token is set, refreshing it if needed.

        Returns
        -------
        int
            The token generation that is now in effect, so callers can detect
            whether a concurrent refresh has happened since.
        """
        with self._token_lock:
            if (
                self._token_valid_until is None
                or datetime.datetime.now() > self._token_valid_until
            ):
                self._refresh_token_locked()
            return self._token_generation

    def _force_refresh(self, seen_generation: int) -> None:
        """Force a token refresh after an auth failure.

        Parameters
        ----------
        seen_generation: int
            Token generation observed before the failing request. If the
            current generation differs, another thread already refreshed the
            token and this call is a no-op.
        """
        with self._token_lock:
            if seen_generation != self._token_generation:
                return
            self._refresh_token_locked()

    def _refresh_token_locked(self):
        """Refresh the token and update the client headers.

        The caller must hold ``self._token_lock``.
        """
        fetch_time = datetime.datetime.now()
        token = self._get_token(self._username, self._password, self._application_id)
        buffer_seconds = min(60, token.expires_in // 2)
        self._token_valid_until = (
            fetch_time
            + datetime.timedelta(seconds=token.expires_in)
            - datetime.timedelta(seconds=buffer_seconds)
        )
        self._client.headers["Authorization"] = f"Bearer {token.access_token}"
        self._token_generation += 1

    def _get_token(self, username: str, password: str, application_id: str) -> Token:
        """Get a valid token."""
        response = self._client.post(
            self._base_url + f"/token?applicationId={application_id}",
            data={"grant_type": "client_credentials"},
            auth=httpx.BasicAuth(username, password),
        )
        response.raise_for_status()
        return Token.model_validate(response.json())

    def post(self, url: str, json: object = None) -> httpx.Response:
        """Post json to url.

        Parameters
        ----------
        url: str
            Url to post to.
        json: object
            JSON-serializable body.

        Returns
        -------
        httpx.Response
            Response with 2xx-status.

        """
        generation = self._ensure_token()
        response = self._request_with_retry(
            "POST", self._base_url + url, 1, generation, json=json
        )
        return self._raise_for_status(response)

    def put(self, url: str, json: object = None) -> httpx.Response:
        """Put json to url.

        Parameters
        ----------
        url: str
            Url to put to.
        json: object
            JSON-serializable body.

        Returns
        -------
        httpx.Response
            Response with 2xx-status.

        """
        generation = self._ensure_token()
        response = self._request_with_retry(
            "PUT", self._base_url + url, 1, generation, json=json
        )
        return self._raise_for_status(response)

    def _request_with_retry(
        self,
        method: str,
        url: str,
        retries: int,
        generation: int,
        stream: bool = False,
        json: object = None,
    ) -> httpx.Response:
        """Perform a request with token refresh on 401/403 responses."""
        if stream:
            request = self._client.build_request(method, url)
            response = self._client.send(request, stream=True)
        else:
            response = self._client.request(method, url, json=json)
        if (
            response.status_code not in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)
            or retries <= 0
        ):
            return response
        # Release the failed (possibly streamed) response before retrying so the
        # connection is returned to the pool instead of leaking.
        response.close()
        self._force_refresh(generation)
        return self._request_with_retry(
            method,
            url,
            retries - 1,
            self._token_generation,
            stream=stream,
            json=json,
        )

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> httpx.Response:
        """Raise for non-2xx status, closing the response first to avoid leaks."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError:
            response.close()
            raise
        return response
