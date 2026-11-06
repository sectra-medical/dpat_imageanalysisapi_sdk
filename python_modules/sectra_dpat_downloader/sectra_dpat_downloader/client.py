from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union
import urllib.parse

from httpx import Response

from sectra_dpat_downloader.http_client import HttpClient
from sectra_dpat_downloader.models import ApiInfo, CaseImage, Image
from sectra_dpat_downloader.multipart import MultipartParser
from sectra_dpat_downloader.result_models import (
    QualityControl,
    Result,
    ResultResponse,
)

MAX_ATTACHMENT_CHUNK_SIZE = 512 * 1024 * 1024
"""The most bytes of an attachment the server takes in one request."""


class SectraDpatDownloader:
    """Client for fetching metadata and images from Sectra pathology server using
    image analysis api. Requires DPAT >= 4.1.
    """

    def __init__(
        self,
        http_client: HttpClient,
        application_id: str,
        chunk_size: int = 64 * 1024 * 1024,
        *,
        owns_client: bool = False,
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
        owns_client: bool = False
            Whether this instance owns the HTTP client and should close it when
            ``close()`` is called. Defaults to False, so an injected client is
            left for its owner to close.
        """
        self._client = http_client
        self._application_id = application_id
        self._chunk_size = chunk_size
        self._owns_client = owns_client

    def close(self) -> None:
        """Close the client and release its connections.

        Only closes the underlying HTTP client when this instance created it
        (i.e. via ``from_credentials``). An HTTP client passed to ``__init__``
        is assumed to be managed elsewhere and is left untouched.
        """
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "SectraDpatDownloader":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

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
            owns_client=True,
        )

    def get_api_info(self) -> ApiInfo:
        """Get the version of the API and of the pathology server.

        Returns
        -------
        ApiInfo
            The API version, as ``<major>.<minor>``, and the software version of
            the server.
        """
        response = self._client.get("/info")
        return ApiInfo.model_validate(response.json())

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

    def get_images_in_case_of_slide(self, slide_id: str) -> Iterable[CaseImage]:
        """Get basic metadata for all images in the case a given slide is in.

        Use this when only the id of one slide in the case is known, for example
        from an image notification.

        Parameters
        ----------
        slide_id : str
            The id of a slide in the case.

        Returns
        -------
        Iterable[CaseImage]
            Basic metadata for all images in the case, the given slide included.
        """
        params = {"includePHI": True}
        url = f"/slides/{slide_id}/request/images/info?{urllib.parse.urlencode(params)}"
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

    def get_tile(
        self,
        slide_id: str,
        level: int,
        x: int,
        y: int,
        extension: str,
        focal_plane: Optional[str] = None,
        optical_path: Optional[str] = None,
    ) -> bytes:
        """Get a tile of a whole-slide image.

        The tile is addressed as in the Deep Zoom (DZI) format: level 0 is the
        image scaled down to a single pixel, and each level doubles the size of
        the one before. The base level, the full resolution, is
        ``ceil(log2(max(width, height)))`` of the ``image_size`` in the image
        metadata.

        Parameters
        ----------
        slide_id : str
            The slide ID to get a tile of.
        level : int
            The zoom level of the tile.
        x : int
            The column of the tile, 0-based.
        y : int
            The row of the tile, 0-based.
        extension : str
            The extension of the tile format, one of the ``available_tile_formats``
            in the image metadata, such as ``jpg``.
        focal_plane : Optional[str] = None
            The id of the focal plane, one of the ``focal_planes`` in the image
            metadata. The default (middle) plane if None.
        optical_path : Optional[str] = None
            The id of the optical path, one of the ``optical_paths`` in the image
            metadata. Required for slides scanned with several optical paths.

        Returns
        -------
        bytes
            The tile, encoded in the format of the extension.
        """
        name = f"{x}_{y}" if focal_plane is None else f"{x}_{y}_{focal_plane}"
        url = f"/images/{slide_id}_files/{level}/{name}.{extension.lstrip('.')}"
        if optical_path is not None:
            url += "?" + urllib.parse.urlencode({"opticalPath": optical_path})
        response = self._client.get(url)
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

    def get_results_for_slide(self, slide_id: str) -> List[ResultResponse]:
        """Get all results created by the application for a slide.

        Parameters
        ----------
        slide_id : str
            The slide id to get results for.

        Returns
        -------
        List[ResultResponse]
            The results of the application for the slide.
        """
        url = f"/applications/{self._application_id}/results/slide/{slide_id}"
        response = self._client.get(url)
        return [ResultResponse.model_validate(item) for item in response.json()]

    def upload_result_attachment(
        self,
        result_id: str,
        name: str,
        content: Union[bytes, str, Path],
        chunk_size: Optional[int] = None,
    ) -> None:
        """Upload an attachment of a result.

        The attachment must first be declared, with state ``new``, in the
        ``attachments`` of the result when it is created or updated. The content
        is uploaded in consecutive chunks, as the server takes at most 512 MiB in
        one request.

        Parameters
        ----------
        result_id : str
            The id of the result the attachment belongs to.
        name : str
            The name the attachment is declared with.
        content : Union[bytes, str, Path]
            The content to upload, or the path of a file to upload.
        chunk_size : Optional[int] = None
            The most bytes to upload in one request. Defaults to the chunk size
            of the client. At most 512 MiB.
        """
        chunk_size = chunk_size or self._chunk_size
        if not 0 < chunk_size <= MAX_ATTACHMENT_CHUNK_SIZE:
            raise ValueError(
                f"Chunk size must be between 1 and {MAX_ATTACHMENT_CHUNK_SIZE} bytes."
            )
        url = (
            f"/applications/{self._application_id}/results/{result_id}/attachments?"
            + urllib.parse.urlencode({"name": name})
        )
        if isinstance(content, bytes):
            total = len(content)
            chunks: Iterable[bytes] = (
                content[start : start + chunk_size]
                for start in range(0, total, chunk_size)
            )
            self._upload_chunks(url, chunks, total)
            return
        path = Path(content)
        total = path.stat().st_size
        with open(path, "rb") as file:
            chunks = iter(lambda: file.read(chunk_size), b"")
            self._upload_chunks(url, chunks, total)

    def _upload_chunks(self, url: str, chunks: Iterable[bytes], total: int) -> None:
        """Upload the chunks of an attachment in order, each with its range."""
        if total == 0:
            raise ValueError("An attachment cannot be empty.")
        start = 0
        for chunk in chunks:
            end = start + len(chunk) - 1
            self._client.put(
                url,
                content=chunk,
                headers={
                    "Content-Range": f"bytes {start}-{end}/{total}",
                    "Content-Type": "application/octet-stream",
                },
            )
            start = end + 1

    def download_result_attachment(
        self,
        result_id: str,
        name: str,
        output_folder: Union[str, Path],
    ) -> Path:
        """Download an attachment of a result.

        Parameters
        ----------
        result_id : str
            The id of the result the attachment belongs to.
        name : str
            The name of the attachment.
        output_folder : Union[str, Path]
            Folder path to write the attachment to, named as the attachment.

        Returns
        -------
        Path
            Path to the downloaded attachment.
        """
        output_folder = Path(output_folder)
        if not output_folder.is_dir():
            raise ValueError(f"Path {output_folder} is not a directory")
        url = (
            f"/applications/{self._application_id}/results/{result_id}/attachments?"
            + urllib.parse.urlencode({"name": name})
        )
        response = self._client.get(url, stream=True)
        try:
            chunks = response.iter_bytes(self._chunk_size)
            return self._write_chunks_to_file(chunks, output_folder, name)
        finally:
            response.close()

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
        url = f"/slides/{slide_id}/qualitycontrol"
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
