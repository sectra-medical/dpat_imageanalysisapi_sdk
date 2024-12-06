from enum import Enum, unique
from typing import List, Optional

from pydantic import BaseModel


class CallbackInfo(BaseModel):
    """Model for callbacks info."""

    url: str
    token: str


class Context(BaseModel):
    """Model for analysis context."""

    useGPU: Optional[str] = None
    seedValue: int = 666


@unique
class InputType(str, Enum):
    """Enum for input template types."""

    MULTI_AREA = "multiArea"
    TAGGED_POLYGON = "taggedPolygon"
    WHOLE_SLIDE = "wholeSlide"


class Point(BaseModel):
    """Model for points."""

    x: float
    y: float


class Polygon(BaseModel):
    """Model for polygons."""

    points: List[Point]


class Size(BaseModel):
    """Model for size."""

    width: int
    height: int


class DisplayedName(BaseModel):
    """Model for displayed names."""

    displayName: str
