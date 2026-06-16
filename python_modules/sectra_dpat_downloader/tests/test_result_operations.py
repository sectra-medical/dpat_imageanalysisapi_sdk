import pytest
from decoy import Decoy, matchers
from httpx import Response

from sectra_dpat_downloader.client import SectraDpatDownloader
from sectra_dpat_downloader.http_client import HttpClient
from sectra_dpat_downloader.result_models import (
    QualityControl,
    QualityControlData,
    QualityControlStatus,
    Result,
    ResultResponse,
)


@pytest.fixture
def mock_http(decoy: Decoy) -> HttpClient:
    return decoy.mock(cls=HttpClient)


@pytest.fixture
def downloader(mock_http: HttpClient) -> SectraDpatDownloader:
    # Inject the mocked HttpClient directly.
    return SectraDpatDownloader(mock_http, "app-1")


def _make_result() -> Result:
    return Result(
        slide_id="slide-1",
        display_result="Test result",
        application_version="1.0.0",
        data={},
    )


def _make_result_response_json() -> dict:
    return {
        "slideId": "slide-1",
        "displayResult": "Test result",
        "displayProperties": {},
        "applicationVersion": "1.0.0",
        "attachments": None,
        "data": {},
        "id": 42,
        "versionId": "v1",
    }


def _stub_response(decoy: Decoy) -> Response:
    response = decoy.mock(cls=Response)
    decoy.when(response.json()).then_return(_make_result_response_json())
    return response


class TestCreateResult:
    def test_posts_to_correct_url(self, decoy: Decoy, downloader, mock_http):
        # Arrange
        # Stubbing the exact URL means a call with any other URL returns the
        # default (None) and the assertion below fails.
        decoy.when(
            mock_http.post("/applications/app-1/results", json=matchers.Anything())
        ).then_return(_stub_response(decoy))

        # Act
        result = downloader.create_result(_make_result())

        # Assert
        assert isinstance(result, ResultResponse)

    def test_returns_result_response(self, decoy: Decoy, downloader, mock_http):
        # Arrange
        decoy.when(
            mock_http.post(matchers.Anything(), json=matchers.Anything())
        ).then_return(_stub_response(decoy))

        # Act
        result = downloader.create_result(_make_result())

        # Assert
        assert isinstance(result, ResultResponse)
        assert result.id == 42
        assert result.version_id == "v1"
        assert result.slide_id == "slide-1"

    def test_serializes_with_camel_case(self, decoy: Decoy, downloader, mock_http):
        # Arrange
        # Stubbing on a camelCase-keyed payload means a snake_case body would
        # not match, so the call would not return the response.
        decoy.when(
            mock_http.post(
                matchers.Anything(),
                json=matchers.DictMatching(
                    {
                        "slideId": "slide-1",
                        "displayResult": "Test result",
                        "applicationVersion": "1.0.0",
                    }
                ),
            )
        ).then_return(_stub_response(decoy))

        # Act
        result = downloader.create_result(_make_result())

        # Assert
        assert isinstance(result, ResultResponse)


class TestGetResult:
    def test_gets_from_correct_url(self, decoy: Decoy, downloader, mock_http):
        # Arrange
        decoy.when(
            mock_http.get("/applications/app-1/results/42")
        ).then_return(_stub_response(decoy))

        # Act
        result = downloader.get_result("42")

        # Assert
        assert isinstance(result, ResultResponse)

    def test_returns_result_response(self, decoy: Decoy, downloader, mock_http):
        # Arrange
        decoy.when(mock_http.get(matchers.Anything())).then_return(
            _stub_response(decoy)
        )

        # Act
        result = downloader.get_result("42")

        # Assert
        assert isinstance(result, ResultResponse)
        assert result.id == 42


class TestUpdateResult:
    def test_puts_to_correct_url(self, decoy: Decoy, downloader, mock_http):
        # Arrange
        decoy.when(
            mock_http.put(
                "/applications/app-1/results/42", json=matchers.Anything()
            )
        ).then_return(_stub_response(decoy))

        # Act
        result = downloader.update_result("42", _make_result())

        # Assert
        assert isinstance(result, ResultResponse)

    def test_returns_result_response(self, decoy: Decoy, downloader, mock_http):
        # Arrange
        decoy.when(
            mock_http.put(matchers.Anything(), json=matchers.Anything())
        ).then_return(_stub_response(decoy))

        # Act
        result = downloader.update_result("42", _make_result())

        # Assert
        assert isinstance(result, ResultResponse)
        assert result.id == 42
        assert result.version_id == "v1"


class TestSetQualityControl:
    def _make_quality_control(self) -> QualityControl:
        return QualityControl(
            application_version="1.0.0",
            quality_control=QualityControlData(
                status=QualityControlStatus.QUALITY_OK,
                version_id="v1",
            ),
        )

    def test_puts_to_correct_url(self, decoy: Decoy, downloader, mock_http):
        # Arrange
        quality_control = self._make_quality_control()

        # Act
        downloader.set_quality_control("slide-1", quality_control)

        # Assert
        # The return value is ignored by the client, so verify the command.
        decoy.verify(
            mock_http.put(
                "/slides/slide-1/qualityControl", json=matchers.Anything()
            ),
            times=1,
        )

    def test_serializes_with_camel_case(self, decoy: Decoy, downloader, mock_http):
        # Arrange
        quality_control = self._make_quality_control()
        payload_captor = matchers.Captor()

        # Act
        downloader.set_quality_control("slide-1", quality_control)

        # Assert
        decoy.verify(mock_http.put(matchers.Anything(), json=payload_captor))
        payload = payload_captor.value
        assert "applicationVersion" in payload
        assert "qualityControl" in payload
        assert "versionId" in payload["qualityControl"]
