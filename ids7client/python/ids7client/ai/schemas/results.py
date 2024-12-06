from enum import Enum, unique
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from .common import Point, Polygon


class Style(BaseModel):
    """Model for style."""

    strokeStyle: Optional[str] = None
    fillStyle: Optional[str] = None
    size: Optional[int] = None


class Polyline(BaseModel):
    """Model for polylines."""

    points: List[Point]


class Label(BaseModel):
    """Model for label."""

    location: Point
    label: str


class PrimitiveItem(BaseModel):
    """Model for polygon primitive content item."""

    style: Optional[Style] = None
    polygons: Optional[List[Polygon]] = None
    polylines: Optional[List[Polyline]] = None
    labels: Optional[List[Label]] = None


class Patch(BaseModel):
    """Model for patches."""

    tag: int
    position: Point
    sortKeyValue: float


class Status(BaseModel):
    """Model for statuses."""

    value: Optional[bool] = True
    message: Optional[str] = None


class PatchContent(BaseModel):
    """Model for sectra patch content."""

    description: str
    polygons: List[Polygon]
    patches: List[Patch]
    tags: List[str]
    patchSize: int
    magnification: float
    statuses: Dict[str, Status] = {"allowVerify": Status()}


@unique
class ResultType(str, Enum):
    """Enum for result types."""

    PATCHES = "patchCollection"
    PRIMITIVES = "primitive"


class ResultContent(BaseModel):
    """Schema for results content."""

    type: ResultType
    content: Union[PatchContent, List[PrimitiveItem]]


DisplayProperties = Dict[str, Union[str, int, float]]


class ResultData(BaseModel):
    """Schema for data field in results."""

    context: Dict[str, Any] = {}
    result: ResultContent


@unique
class AttachmentState(str, Enum):
    """Enum for attachment states."""

    NEW = "new"
    UPLOAD_IN_PROGRESS = "upload-in-progress"
    STORED = "stored"


class Attachment(BaseModel):
    """Model for result attachments."""

    name: str
    state: AttachmentState


class Result(BaseModel):
    """Schema for result posting in IDS7 server."""

    slideId: str
    displayResult: str
    displayProperties: DisplayProperties = {}
    applicationVersion: str
    attachments: Optional[List[Attachment]] = None
    data: Union[ResultData, Dict[str, Any]] = {}


class ResultResponse(Result):
    """Schema for result retrieval from IDS7 server."""

    id: int
    versionId: str
