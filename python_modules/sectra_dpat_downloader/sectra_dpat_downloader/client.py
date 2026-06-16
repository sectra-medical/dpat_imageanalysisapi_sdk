from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union
import urllib.parse

from httpx import Response

from sectra_dpat_downloader.http_client import HttpClient
from sectra_dpat_downloader.models import CaseImage, Image
from sectra_dpat_downloader.multipart import MultipartParser
from sectra_dpat_downloader.result_models import (
    QualityControl,
    Result,
    ResultResponse,
)


class SectraDpatDownloader:
    """Client for fetching metadata and images from Sectra pathology server using
    image analysis api. Requires DPAT >= 4.1.
    """

    def __init__(
        self,
        http_client: HttpClient,
        application_id: str,
        chunk_size: int = 64 * 1024 * 1024,
    ):
        """
        Create a client from an existing HTTP client.

        Use this when the HTTP client is managed elsewhere, e.g. as a singleton
        in a dependency injection container, so its session and cached token are
        shared. For simple usage from credentials, see ``from_credentials``.

        Parameters
        ----------
        http_client : HttpClient
            HTTP client handling authentication and requests.
        application_id : str
            ID of the application to identify as. Used for the result endpoints.
        chunk_size: int = 64 * 1024 * 1024
            Chunk size for streaming file from response to disk. Defaults to 64 MB.
        """
        self._client = http_client
        self._application_id = application_id
        self._chunk_size = chunk_size

    @classmethod
    def from_credentials(
        cls,
        base_url: str,
        application_id: str,
        username: str,
        password: str,
        chunk_size: int = 64 * 1024 * 1024,
    ) -> "SectraDpatDownloader":
        """
        Create a client from credentials.

        Parameters
        ----------
        base_url : str
            Base URL of the pathology server. Typically
            http(s)://<host>/SectraPathologyServer/external/imageanalysis/v1.
        application_id : str
            ID of the application to identify as.
        username : str
            Username for authentication.
        password : str
            Password for authentication.
        chunk_size: int = 64 * 1024 * 1024
            Chunk size for streaming file from response to disk. Defaults to 64 MB.

        Returns
        -------
        SectraDpatDownloader
            Client backed by a new HTTP client for the given credentials.
        """
        return cls(
            HttpClient(base_url, username, password, application_id),
            application_id,
            chunk_size,
        )

    def get_images_in_case(
        self,
        accession_number: str,
        accession_number_issuer: Optional[str] = None,
    ) -> Iterable[CaseImage]:
        """Get basic metadata for all images in a given case.

        Parameters
        ----------
        accession_number : str
            The accession number to get images for.
        accession_number_issuer : Optional[str], optional
            The issuer of the accession number, by default None.

        Returns
        -------
        Iterable[CaseImage]
            Basic metadata for all images in the given case.
        """

        params: Dict[str, Any] = {"includePHI": True}
        if accession_number_issuer:
            params["accessionNumberIssuer"] = accession_number_issuer
        url = (
            f"/requests/{accession_number}/images/info?{urllib.parse.urlencode(params)}"
        )
        response = self._client.get(url)
        return [CaseImage.model_validate(item) for item in response.json()]

    def get_image_metadata(self, slide_id: str) -> Image:
        """Get the metadata for a given slide ID.

        Parameters
        ----------
        slide_id : str
            The slide ID to get metadata for.

        Returns
        -------
        Image
            The metadata for the given slide ID.
        """
        params = {
            "scope": "extended",
            "includePHI": True,
        }
        url = f"/slides/{slide_id}/info?{urllib.parse.urlencode(params)}"
        response = self._client.get(url)
        return Image.model_validate(response.json())

    def get_image_label(self, slide_id: str) -> bytes:
        """Get the label for a given slide ID.

        Parameters
        ----------
        slide_id : str
            The slide ID to get label for.

        Returns
        -------
        bytes
            The label for the given slide ID.
        """
        response = self._client.get(f"/slides/{slide_id}/label")
        return response.content

    def download_image_files(
        self,
        slide_id: str,
        output_folder: Union[str, Path],
    ) -> List[Path]:
        """Download the image files for a given slide ID.

        Parameters
        ----------
        slide_id : str
            The slide ID to download image files for.
        output_folder : Union[str, Path]
            Folder path to write downloaded image files to.

        Returns
        -------
        List[Path]
            Paths to the downloaded image files.
        """
        output_folder = Path(output_folder)
        if not output_folder.exists():
            raise ValueError(f"Path {output_folder} does not exist")
        if not output_folder.is_dir():
            raise ValueError(f"Path {output_folder} is not a directory")
        response = self._client.get(f"/slides/{slide_id}/files", stream=True)
        try:
            content_type = response.headers["content-type"]
            if content_type.startswith("multipart/related"):
                return list(
                    self._handle_multipart_file_response(response, output_folder)
                )
            return [self._handle_file_response(response, output_folder)]
        finally:
            response.close()

    def _handle_multipart_file_response(
        self, response: Response, output_folder: Path
    ) -> Iterable[Path]:
        """Write files in multipart response to output.

        Parameters
        ----------
        response: Response
            Multipart response with files.
        output_folder : Path
            Folder path to write files to.

        Returns
        -------
        List[Path]
            Paths to the created files.
        """
        boundary = (
            response.headers["content-type"]
            .split("boundary=")[1]
            .split(";")[0]
            .strip('"')
        )
        parser = MultipartParser(response.iter_bytes(self._chunk_size), boundary)
        for filename, file_chunks in parser.parts():
            yield self._write_chunks_to_file(file_chunks, output_folder, filename)

    def _handle_file_response(self, response: Response, output_folder: Path) -> Path:
        """Write file in response to output.

        Parameters
        ----------
        response: Response
            Response with file.
        output_folder : Path
            Folder path to write file to.

        Returns
        -------
        Path
            Paths to the created file.
        """
        content_disposition = response.headers["content-disposition"]
        filename = content_disposition.split("filename=")[1].strip('"')
        chunks = response.iter_bytes(self._chunk_size)
        return self._write_chunks_to_file(chunks, output_folder, filename)

    def create_result(self, result: Result) -> ResultResponse:
        """Create a result in DPAT.

        Parameters
        ----------
        result : Result
            Result payload to create.

        Returns
        -------
        ResultResponse
            Created result with id and version.
        """
        url = f"/applications/{self._application_id}/results"
        response = self._client.post(url, json=result.model_dump(by_alias=True))
        return ResultResponse.model_validate(response.json())

    def get_result(self, result_id: str) -> ResultResponse:
        """Get a result by id.

        Parameters
        ----------
        result_id : str
            The result id.

        Returns
        -------
        ResultResponse
            The result.
        """
        url = f"/applications/{self._application_id}/results/{result_id}"
        response = self._client.get(url)
        return ResultResponse.model_validate(response.json())

    def update_result(self, result_id: str, result: Result) -> ResultResponse:
        """Update an existing result.

        Parameters
        ----------
        result_id : str
            The result id to update.
        result : Result
            Updated result payload.

        Returns
        -------
        ResultResponse
            Updated result with id and version.
        """
        url = f"/applications/{self._application_id}/results/{result_id}"
        response = self._client.put(url, json=result.model_dump(by_alias=True))
        return ResultResponse.model_validate(response.json())

    def set_quality_control(
        self, slide_id: str, quality_control: QualityControl
    ) -> None:
        """Set quality control for a slide. Available from IA-API 1.10 (DPAT 4.2).

        Parameters
        ----------
        slide_id : str
            The slide id to set quality control for.
        quality_control : QualityControl
            Quality control data to set.
        """
        url = f"/slides/{slide_id}/qualityControl"
        self._client.put(url, json=quality_control.model_dump(by_alias=True))

    @staticmethod
    def _write_chunks_to_file(
        chunks: Iterable[bytes],
        output_folder: Path,
        filename: str,
    ) -> Path:
        """Write chunks of bytes to output file.

        Parameters
        ----------
        chunks: Iterable[bytes]
            Chunks to write.
        output_folder: Path
            Folder path to write to.
        filename: str
            Filename in output folder to write to.

        Returns
        -------
        Path
            Path to the created file.
        """
        safe_name = Path(filename.replace("\\", "/")).name
        if not safe_name or safe_name in (".", ".."):
            raise ValueError(f"Invalid filename in response: {filename!r}")
        filepath = output_folder.joinpath(safe_name)
        with open(filepath, "wb") as file:
            for chunk in chunks:
                file.write(chunk)
        return filepath
