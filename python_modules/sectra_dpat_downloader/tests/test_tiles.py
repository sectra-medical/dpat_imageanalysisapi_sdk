from http import HTTPStatus

import httpx
import pytest

from sectra_dpat_downloader.client import SectraDpatDownloader
from tests.conftest import BASE_URL, FakeServer

SLIDE_ID = "1.2.752.24.16.123.456"


class TestGetTile:
    def test_tile_in_the_default_focal_plane(
        self, client: SectraDpatDownloader, server: FakeServer
    ):
        # Arrange
        server.respond_with(content=b"tile")

        # Act
        tile = client.get_tile(SLIDE_ID, 10, 2, 1, "jpg")

        # Assert
        assert tile == b"tile"
        assert str(server.requests[0].url) == (
            f"{BASE_URL}/images/{SLIDE_ID}_files/10/2_1.jpg"
        )

    def test_tile_in_a_focal_plane(
        self, client: SectraDpatDownloader, server: FakeServer
    ):
        # Act
        client.get_tile(SLIDE_ID, 10, 2, 1, "png", focal_plane="-1.2")

        # Assert
        assert server.requests[0].url.path == (
            f"/images/{SLIDE_ID}_files/10/2_1_-1.2.png"
        )

    def test_tile_of_an_optical_path(
        self, client: SectraDpatDownloader, server: FakeServer
    ):
        # Act
        client.get_tile(SLIDE_ID, 10, 3, 4, "jpg", optical_path="1")

        # Assert
        assert server.requests[0].url.path == f"/images/{SLIDE_ID}_files/10/3_4.jpg"
        assert server.requests[0].url.params["opticalPath"] == "1"

    def test_tile_sends_bearer_token(
        self, client: SectraDpatDownloader, server: FakeServer
    ):
        # Act
        client.get_tile(SLIDE_ID, 10, 0, 0, ".jpg")

        # Assert
        assert server.requests[0].headers["Authorization"] == "Bearer test-token"
        assert server.requests[0].url.path.endswith("0_0.jpg")

    def test_tile_outside_the_image_raises(
        self, client: SectraDpatDownloader, server: FakeServer
    ):
        # Arrange
        server.respond_with(HTTPStatus.BAD_REQUEST)

        # Act & Assert
        with pytest.raises(httpx.HTTPStatusError):
            client.get_tile(SLIDE_ID, 10, 99, 99, "jpg")
