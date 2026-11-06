from typing import Any, Dict, List

import pytest

from sectra_dpat_downloader.client import SectraDpatDownloader
from tests.conftest import FakeServer

SLIDE_ID = "ce4f4b9e-ca50-4378-a51b-0753c9b96668"


class TestGetApiInfo:
    def test_versions_are_read(self, client: SectraDpatDownloader, server: FakeServer):
        # Arrange
        server.respond_with(
            json={"apiVersion": "1.11", "softwareVersion": "5.1.0.24128"}
        )

        # Act
        info = client.get_api_info()

        # Assert
        assert server.requests[0].url.path == "/info"
        assert info.api_version == "1.11"
        assert info.software_version == "5.1.0.24128"


class TestGetImagesInCaseOfSlide:
    @pytest.fixture()
    def case_images(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": SLIDE_ID,
                "staining": {"displayName": "HE"},
                "block": {"displayName": "1A"},
                "specimen": {"anatomy": "Breast", "description": "Biopsy"},
                "seriesInstanceUid": "1.2.752.24.16.2.71523.97219.433934.56251",
                "lisSlideId": "CASE-24-999-1-H-A",
            },
            {
                "id": "5a078daa-78c3-4891-9fd5-b635649fc679",
                "staining": {"displayName": "KI67"},
                "block": {"displayName": "B"},
                "specimen": {},
                "seriesInstanceUid": "1.2.752.24.16.2.98523.46219.373931.2259",
                "lisSlideId": "CASE-24-999-1-K-B",
            },
        ]

    @pytest.fixture()
    def server(self, server: FakeServer, case_images: List[Dict[str, Any]]):
        server.respond_with(json=case_images)
        return server

    def test_images_in_the_case_are_read(
        self, client: SectraDpatDownloader, case_images: List[Dict[str, Any]]
    ):
        # Act
        images = list(client.get_images_in_case_of_slide(SLIDE_ID))

        # Assert
        assert [image.id for image in images] == [item["id"] for item in case_images]
        assert images[1].specimen.anatomy is None

    def test_request_is_for_the_case_of_the_slide_with_phi(
        self, client: SectraDpatDownloader, server: FakeServer
    ):
        # Act
        client.get_images_in_case_of_slide(SLIDE_ID)

        # Assert
        request = server.requests[0]
        assert request.url.path == f"/slides/{SLIDE_ID}/request/images/info"
        assert request.url.params["includePHI"] == "True"
        assert request.headers["Authorization"] == "Bearer test-token"
