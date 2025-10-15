import datetime
from http import HTTPStatus
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth

from sectra_dpat_downloader.models import Token


class HttpClient:
    """Http client that handles token authentication and refreshing."""

    def __init__(
        self, base_url: str, username: str, password: str, application_id: str
    ):
        """Create a http client.

        Parameters
        ----------
        base_url: str
            Base url for client requests.
        username: str
            Username to use for requesting token.
        password: str
            Passwort to use for requesting token.
        application_id:
            Application id to use for requesting token.
        """
        self._base_url = base_url
        self._username = username
        self._password = password
        self._application_id = application_id
        client = requests.session()
        self._client = client
        self._token_valid_until: Optional[datetime.datetime] = None

    def get(self, url: str, stream: bool = False) -> requests.Response:
        """Get response from url.

        Parameters
        ----------
        url: str
            Url to get response from.
        stream: bool = False
            If to stream the response.

        Returns
        -------
        requests.Response
            Response with 2xx-status.

        """
        if (
            self._token_valid_until is None
            or datetime.datetime.now() > self._token_valid_until
        ):
            self._refresh_token()
        response = self._get_with_retry(self._base_url + url, 1, stream)
        response.raise_for_status()
        return response

    def _refresh_token(self):
        """Refresh the token and update the client headers."""
        fetch_time = datetime.datetime.now()
        token = self._get_token(self._username, self._password, self._application_id)
        self._token_valid_until = (
            fetch_time
            + datetime.timedelta(seconds=token.expires_in)
            - datetime.timedelta(seconds=60)
        )
        self._client.headers.update({"Authorization": f"Bearer {token.access_token}"})

    def _get_token(self, username: str, password: str, application_id: str) -> Token:
        """Get a valid token."""
        client = requests.session()
        client.auth = HTTPBasicAuth(username, password)
        response = client.post(
            self._base_url + f"/token?applicationId={application_id}",
            {"grant_type": "client_credentials"},
        )
        response.raise_for_status()
        return Token.model_validate(response.json())

    def _get_with_retry(
        self, url: str, retries: int, stream: bool
    ) -> requests.Response:
        """Perform a GET request with token refresh on 401/403 responses."""
        response = self._client.get(url, stream=stream)
        if (
            response.status_code not in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN)
            or retries <= 0
        ):
            return response
        self._refresh_token()
        return self._get_with_retry(url, retries - 1, stream)
