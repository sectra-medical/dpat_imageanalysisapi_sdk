import logging
from typing import Any, Dict, List, cast

import requests
from requests.auth import HTTPBasicAuth

from sectra_dpat_client.errors import DPATRequestError
from sectra_dpat_client.helpers import JSONPayload, connection_retry

from .schemas import NAMES_TO_DICOM_CODES, DicomObject

logger = logging.getLogger(__name__)


def _make_query_params(**kwargs) -> Dict[str, Any]:
    """Builds a query params with dicom codes from names."""

    params: Dict[str, Any] = {}
    for k, v in kwargs.items():
        code = NAMES_TO_DICOM_CODES.get(k)
        if code is None:
            logger.warning(
                "No dicom code found for key %s, skipping it in query params", k
            )
            continue
        params[code] = v
    return params


class DPATQidoClient:
    """Class managing connection and requests to DPAT server.

    Args:
        url (str): URL of the DPAT Qido API
        username (str): API username
        password (str): API password
    """

    __slots__ = (
        "_url",
        "_auth",
    )

    def __init__(self, url: str, username: str, password: str) -> None:
        self._url = url
        self._auth = HTTPBasicAuth(username, password)

    @connection_retry()
    def _get(self, path: str, **kwargs) -> JSONPayload:
        """Runs a GET request to DPAT. Named args are query parameters."""

        resp = requests.get(path, params=kwargs, auth=self._auth)
        if resp.status_code != 200:
            raise DPATRequestError(resp.status_code, resp.text, path)
        return resp.json()

    def find_all_studies(self, **kwargs) -> List[DicomObject]:
        """Finds all studies matchings query."""

        params = _make_query_params(**kwargs)
        path = f"{self._url}/studies"
        res = self._get(path, **params)
        return [DicomObject(obj) for obj in cast(list, res)]

    def find_one_study(self, **kwargs) -> DicomObject:
        """Finds one study matching query.

        Raises:
            DPATRequestError: If no study was found.
        """
        studies = self.find_all_studies(**kwargs)
        if not studies:
            raise DPATRequestError(404, "No study found", "")
        return studies[0]
