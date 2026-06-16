from enum import Enum, unique
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from sectra_dpat_downloader.models import CamelCaseBaseModel


class Point(BaseModel):
    x: float
    y: float


class Polygon(BaseModel):
    points: List[Point]


class Polyline(BaseModel):
    points: List[Point]


class Style(CamelCaseBaseModel):
    stroke_style: Optional[str] = None
    fill_style: Optional[str] = None
    size: Optional[int] = None


class Label(BaseModel):
    location: Point
    label: str


class PrimitiveItem(BaseModel):
    style: Optional[Style] = None
    polygons: Optional[List[Polygon]] = None
    polylines: Optional[List[Polyline]] = None
    labels: Optional[List[Label]] = None


class Patch(CamelCaseBaseModel):
    tag: int
    position: Point
    sort_key_value: float


class Status(BaseModel):
    value: Optional[bool] = True
    message: Optional[str] = None


class PatchContent(CamelCaseBaseModel):
    description: str
    polygons: List[Polygon]
    patches: List[Patch]
    tags: List[str]
    patch_size: int
    magnification: float
    statuses: Dict[str, Status] = {"allowVerify": Status()}


@unique
class ResultType(str, Enum):
    PATCHES = "patchCollection"
    PRIMITIVES = "primitive"


class ResultContent(BaseModel):
    type: ResultType
    content: Union[PatchContent, List[PrimitiveItem]]


DisplayProperties = Dict[str, Union[str, int, float]]


class ResultData(BaseModel):
    context: Dict[str, Any] = {}
    result: ResultContent


@unique
class AttachmentState(str, Enum):
    NEW = "new"
    UPLOAD_IN_PROGRESS = "upload-in-progress"
    STORED = "stored"


class Attachment(BaseModel):
    name: str
    state: AttachmentState


class Result(CamelCaseBaseModel):
    slide_id: str
    display_result: str
    display_properties: DisplayProperties = {}
    application_version: str
    attachments: Optional[List[Attachment]] = None
    data: Union[ResultData, Dict[str, Any]] = {}


class ResultResponse(Result):
    id: int
    version_id: str


@unique
class QualityControlStatus(str, Enum):
    NOT_SET = "NotSet"
    QUALITY_OK = "QualityOk"
    REJECTED = "Rejected"


class QualityControlData(CamelCaseBaseModel):
    status: QualityControlStatus
    version_id: str


class QualityControl(CamelCaseBaseModel):
    application_version: str
    quality_control: QualityControlData
