from http import HTTPStatus
from pathlib import Path

import httpx
import pytest

from sectra_dpat_downloader.client import SectraDpatDownloader
from tests.conftest import APPLICATION_ID, FakeServer

ATTACHMENTS_PATH = f"/applications/{APPLICATION_ID}/results/42/attachments"


class TestGetResultsForSlide:
    def test_results_of_the_application_for_the_slide_are_read(
        self, client: SectraDpatDownloader, server: FakeServer
    ):
        # Arrange
        server.respond_with(
            json=[
                {
                    "id": 42,
                    "versionId": "1",
                    "slideId": "slide-1",
                    "displayResult": "Test result",
                    "displayProperties": {},
                    "applicationVersion": "1.0.0",
                    "data": {},
                }
            ]
        )

        # Act
        results = client.get_results_for_slide("slide-1")

        # Assert
        assert server.requests[0].url.path == (
            f"/applications/{APPLICATION_ID}/results/slide/slide-1"
        )
        assert [result.id for result in results] == [42]
        assert results[0].version_id == "1"


class TestUploadResultAttachment:
    @pytest.fixture()
    def content(self) -> bytes:
        return b"0123456789"

    @pytest.fixture()
    def file(self, tmp_path: Path, content: bytes) -> Path:
        file = tmp_path.joinpath("a.bin")
        file.write_bytes(content)
        return file

    def test_small_attachment_is_uploaded_in_one_request(
        self, client: SectraDpatDownloader, server: FakeServer, content: bytes
    ):
        # Act
        client.upload_result_attachment("42", "example file.txt", content)

        # Assert
        assert len(server.requests) == 1
        request = server.requests[0]
        assert request.method == "PUT"
        assert request.url.path == ATTACHMENTS_PATH
        assert request.url.params["name"] == "example file.txt"
        assert request.headers["Content-Range"] == "bytes 0-9/10"
        assert request.headers["Content-Type"] == "application/octet-stream"
        assert request.content == content

    def test_large_attachment_is_uploaded_in_consecutive_chunks(
        self, client: SectraDpatDownloader, server: FakeServer, content: bytes
    ):
        # Arrange
        server.respond_with(HTTPStatus.ACCEPTED)

        # Act
        client.upload_result_attachment("42", "a.bin", content, chunk_size=4)

        # Assert
        assert [request.headers["Content-Range"] for request in server.requests] == [
            "bytes 0-3/10",
            "bytes 4-7/10",
            "bytes 8-9/10",
        ]
        assert b"".join(request.content for request in server.requests) == content

    @pytest.mark.parametrize("chunk_size", [6])
    def test_file_is_uploaded_in_chunks_of_the_client(
        self,
        client: SectraDpatDownloader,
        server: FakeServer,
        file: Path,
        content: bytes,
    ):
        # Arrange
        server.respond_with(HTTPStatus.ACCEPTED)

        # Act
        client.upload_result_attachment("42", "a.bin", file)

        # Assert
        assert [request.headers["Content-Range"] for request in server.requests] == [
            "bytes 0-5/10",
            "bytes 6-9/10",
        ]
        assert b"".join(request.content for request in server.requests) == content

    def test_out_of_order_chunk_raises(
        self, client: SectraDpatDownloader, server: FakeServer, content: bytes
    ):
        # Arrange
        server.respond_with(
            HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, json={"storedBytes": 4}
        )

        # Act & Assert
        with pytest.raises(httpx.HTTPStatusError):
            client.upload_result_attachment("42", "a.bin", content)

    def test_empty_attachment_is_not_uploaded(
        self, client: SectraDpatDownloader, server: FakeServer
    ):
        # Act & Assert
        with pytest.raises(ValueError):
            client.upload_result_attachment("42", "a.bin", b"")
        assert server.requests == []

    def test_chunk_larger_than_the_server_takes_is_refused(
        self, client: SectraDpatDownloader, server: FakeServer, content: bytes
    ):
        # Act & Assert
        with pytest.raises(ValueError):
            client.upload_result_attachment(
                "42", "a.bin", content, chunk_size=512 * 1024 * 1024 + 1
            )
        assert server.requests == []


class TestDownloadResultAttachment:
    @pytest.fixture()
    def server(self, server: FakeServer) -> FakeServer:
        server.respond_with(content=b"payload")
        return server

    def test_attachment_is_written_to_the_folder(
        self, client: SectraDpatDownloader, server: FakeServer, tmp_path: Path
    ):
        # Act
        path = client.download_result_attachment("42", "example file.txt", tmp_path)

        # Assert
        assert server.requests[0].url.path == ATTACHMENTS_PATH
        assert server.requests[0].url.params["name"] == "example file.txt"
        assert path == tmp_path.joinpath("example file.txt")
        assert path.read_bytes() == b"payload"

    def test_attachment_name_cannot_leave_the_folder(
        self, client: SectraDpatDownloader, tmp_path: Path
    ):
        # Act
        path = client.download_result_attachment("42", "../outside.txt", tmp_path)

        # Assert
        assert path == tmp_path.joinpath("outside.txt")
