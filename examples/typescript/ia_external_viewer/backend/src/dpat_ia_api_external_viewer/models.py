from typing import List, Any, Dict, Optional, Union
from enum import Enum, unique

from pydantic import BaseModel, ConfigDict

from pydantic.alias_generators import to_camel


class CamelCaseBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


class Point(CamelCaseBaseModel):
    """Model for points."""

    x: float
    y: float


class Polygon(CamelCaseBaseModel):
    """Model for polygons."""

    points: List[Point]


class Style(CamelCaseBaseModel):
    """Model for style."""

    stroke_style: Optional[str] = None
    fill_style: Optional[str] = None
    size: Optional[int] = None


class Polyline(CamelCaseBaseModel):
    """Model for polylines."""

    points: List[Point]


class Label(CamelCaseBaseModel):
    """Model for label."""

    location: Point
    label: str


class PrimitiveItem(CamelCaseBaseModel):
    """Model for polygon primitive content item."""

    style: Optional[Style] = None
    polygons: Optional[List[Polygon]] = None
    polylines: Optional[List[Polyline]] = None
    labels: Optional[List[Label]] = None


class Patch(CamelCaseBaseModel):
    """Model for patches."""

    tag: int
    position: Point
    sort_key_value: float


class Status(CamelCaseBaseModel):
    """Model for statuses."""

    value: Optional[bool] = True
    message: Optional[str] = None


class PatchContent(CamelCaseBaseModel):
    """Model for sectra patch content."""

    description: str
    polygons: List[Polygon]
    patches: List[Patch]
    tags: List[str]
    patch_size: int
    magnification: float
    statuses: Dict[str, Status] = {"allowVerify": Status()}


@unique
class ResultType(str, Enum):
    """Enum for result types."""

    PATCHES = "patchCollection"
    PRIMITIVES = "primitive"


class ResultContent(CamelCaseBaseModel):
    """Schema for results content."""

    type: ResultType
    content: Union[PatchContent, List[PrimitiveItem]]


DisplayProperties = Dict[str, Union[str, int, float]]


class ResultData(CamelCaseBaseModel):
    """Schema for data field in results."""

    context: Dict[str, Any] = {}
    result: ResultContent


@unique
class AttachmentState(str, Enum):
    """Enum for attachment states."""

    NEW = "new"
    UPLOAD_IN_PROGRESS = "upload-in-progress"
    STORED = "stored"


class Attachment(CamelCaseBaseModel):
    """Model for result attachments."""

    name: str
    state: AttachmentState


class Result(CamelCaseBaseModel):
    """Schema for result posting in DPAT server."""

    slideId: str
    display_result: str
    display_properties: DisplayProperties = {}
    application_version: str
    attachments: Optional[List[Attachment]] = None
    data: Union[ResultData, Dict[str, Any]] = {}


class ResultResponse(Result):
    """Schema for result retrieval from DPAT server."""

    id: int
    version_id: str


class LaunchResponseSlide(CamelCaseBaseModel):
    """A Slide available in the launch."""

    id: str
    description: str


class LaunchResponseBlock(CamelCaseBaseModel):
    """A block available in the launch."""

    name: str
    slides: List[LaunchResponseSlide]


class CallbackInfo(CamelCaseBaseModel):
    """Callback information from Pathology Image Analysis API."""

    token: str
    url: str


class Exam(CamelCaseBaseModel):
    """The response sent to client on launch."""

    request_id: str
    blocks: List[LaunchResponseBlock]


class LaunchResponse(CamelCaseBaseModel):
    """The response received from Pathology Image Analysis API on launch."""

    callback_info: CallbackInfo
    blocks: List[LaunchResponseBlock]


class LaunchRequest(BaseModel):
    appId: str
    launchUrl: str
