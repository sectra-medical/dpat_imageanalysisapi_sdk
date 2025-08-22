import logging
from typing import Optional, cast

import requests

from sectra_dpat_client.errors import DPATRequestError
from sectra_dpat_client.helpers import JSONPayload, connection_retry


from .schemas import (
    ApplicationInfo,
    ImageInfo,
    Result,
    ResultResponse,
    QualityControl,
    CaseImageInfo,
)

logger = logging.getLogger(__name__)


class DPATAIClient:
    """Class managing connection and requests to DPAT server AI API.

    Args:
        url (str): URL of the DPAT server
        token (str): Callback token
        app_id (str): Registered application id

    Attributes:
        dpat_version (ApplicationInfo): Versions of the DPAT server
    """

    __slots__ = ("_url", "_token", "dpat_version", "_headers", "_app_id")

    def __init__(self, url: str, token: str, app_id: str) -> None:
        self._url = url
        self._token = token
        self._app_id = app_id
        self._headers = {"Authorization": f"Bearer {token}"}
        self.dpat_version = self._retrieve_dpat_versions()

    def _retrieve_dpat_versions(self) -> ApplicationInfo:
        """Retrieves the versions of DPAT from the server."""

        versions = ApplicationInfo(**cast(dict, self._get("/info")))
        self._headers.update(
            {
                "X-Sectra-ApiVersion": versions.apiVersion,
                "X-Sectra-SoftwareVersion": versions.softwareVersion,
            }
        )
        return versions

    @connection_retry()
    def _get(self, path: str, **kwargs) -> JSONPayload:
        """Runs a GET request to DPAT. Named args are query parameters."""

        url = f"{self._url}{path}"
        resp = requests.get(url, params=kwargs, headers=self._headers)
        if resp.status_code != 200:
            raise DPATRequestError(resp.status_code, resp.text, path)
        return resp.json()

    @connection_retry()
    def _post(
        self, path: str, payload: JSONPayload, parse_response: bool = True
    ) -> Optional[JSONPayload]:
        """Runs a POST request to DPAT.

        Args:
            path (str): Request path
            payload (JSONPayload): Body
            parse_response (bool): Whether the response should be parsed as JSON or not.
                Defaults to True.

        Returns:
            Optional[JSONPayload]: Response, if parse_response is True.
        """
        url = f"{self._url}{path}"
        resp = requests.post(url, json=payload, headers=self._headers)
        if resp.status_code != 201:
            raise DPATRequestError(resp.status_code, resp.text, path)
        if parse_response:
            return resp.json()
        return None

    @connection_retry()
    def _put(
        self, path: str, values: JSONPayload, parse_response: bool = True
    ) -> Optional[JSONPayload]:
        """Runs a PUT request to DPAT.

        Args:
            path (str): Request path
            payload (JSONPayload): Body
            parse_response (bool): Whether the response should be parsed as JSON or not.
                Defaults to True.

        Returns:
            Optional[JSONPayload]: Response, if parse_response is True.
        """
        url = f"{self._url}{path}"
        resp = requests.put(url, json=values, headers=self._headers)
        if resp.status_code != 200:
            raise DPATRequestError(resp.status_code, resp.text, path)
        if parse_response:
            return resp.json()
        return None

    def get_image_infos_in_case(
        self,
        accession_number: str,
        phi: bool = False,
        accession_number_issuer_id: Optional[str] = None,
    ) -> list[CaseImageInfo]:
        """Retrieves all slides in a case. Available from IA-API 1.9 (DPAT 4.1).

        Args:
            accession_number (str): Accession number of the case
            phi (bool): Whether Protected Health Information should be included or not.
                Defaults to False.
            accession_number_issuer_id (Optional[str]): Issuer ID of the accession number.
                Defaults to None.
        Returns:
            list[CaseImageInfo]: List of slides in the case

        """
        path = f"/requests/{accession_number}/images/info"
        params: dict[str, str] = {}
        if phi:
            params["includePHI"] = "true"
        if accession_number_issuer_id:
            params["accessionNumberIssuerId"] = accession_number_issuer_id
        return [
            CaseImageInfo(**img) for img in cast(list[dict], self._get(path, **params))
        ]

    def get_image_infos_in_case_by_slide_id(
        self,
        slide_id: str,
        phi: bool = False,
        accession_number_issuer_id: Optional[str] = None,
    ) -> list[CaseImageInfo]:
        """Retrieves all slides in the case a slide belongs to. Available from IA-API 1.9 (DPAT 4.1).

        Args:
            slide_id (str): Id of the slide
            phi (bool): Whether Protected Health Information should be included or not.
                Defaults to False.
            accession_number_issuer_id (Optional[str]): Issuer ID of the accession number.
                Defaults to None.
        Returns:
            list[CaseImageInfo]: List of slides in the case

        """
        path = f"/slides/{slide_id}/request/images/info"
        params: dict[str, str] = {}
        if phi:
            params["includePHI"] = "true"
        if accession_number_issuer_id:
            params["accessionNumberIssuerId"] = accession_number_issuer_id
        return [
            CaseImageInfo(**img) for img in cast(list[dict], self._get(path, **params))
        ]

    def get_image_info(
        self, slide_id: str, extended: bool = False, phi: bool = False
    ) -> ImageInfo:
        """Retrieves a slide info from its id.

        Args:
            slide_id (str): Id of the slide to retrieve info from
            extended (bool): Whether extended info should be included or not.
                Defaults to False.
            phi (bool): Whether Protected Health Information should be included or not.
                Defaults to False.

        Returns:
            ImageInfo: Requested slide info
        """
        path = f"/slides/{slide_id}/info"
        params: dict[str, str] = {}
        if extended:
            params["scope"] = "extended"
        if phi:
            params["includePHI"] = "true"
        return ImageInfo(**cast(dict, self._get(path, **params)))

    def create_results(self, results: Result) -> ResultResponse:
        """Creates a result in DPAT.

        Args:
            results (Result): Results payload

        Returns:
            ResultResponse: Parsed DPAT response.
        """
        path = f"/applications/{self._app_id}/results"
        resp = self._post(path, results.model_dump())
        return ResultResponse(**cast(dict, resp))

    def get_results(self, id: str) -> ResultResponse:
        """Retrieves results.

        Args:
            id (str): Results id

        Returns:
            ResultResponse: Retrieved results.
        """
        path = f"/application/{self._app_id}/results/{id}"
        return ResultResponse(**self._get(path))  # type: ignore

    def update_results(self, id: str, results: Result) -> ResultResponse:
        """Update existing results.

        Args:
            id (str): Results id
            results (Result): Updated values

        Returns:
            ResultResponse: Updated results
        """
        path = f"/application/{self._app_id}/results/{id}"
        resp = self._put(path, results.model_dump())
        return ResultResponse(**cast(dict, resp))

    def set_quality_control(
        self, slide_id: str, quality_control: QualityControl
    ) -> None:
        """Sets quality control for a slide. Available from IA-API 1.10 (DPAT 4.2).

        Args:
            slide_id (str): Id of the slide to set quality control for
            quality_control (QualityControl): Quality control data to set

        Raises:
            DPATRequestError: If the request fails
        """
        path = f"/slides/{slide_id}/qualityControl"
        self._put(path, quality_control.model_dump(), parse_response=False)
