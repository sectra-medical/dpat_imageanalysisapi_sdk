from typing import Dict, List, Optional

from pydantic import BaseModel

from .quality_control import QualityControlData
from .common import DisplayedName, Size


class FocalPlane(BaseModel):
    """Model for focal planes."""

    id: str
    offsetUm: float


class OpticalPath(BaseModel):
    """Model for optical paths."""

    id: str
    description: str


class TileFormat(BaseModel):
    """Model for tiles format."""

    mimeType: str
    extension: str


class SlideFormat(BaseModel):
    """Model for slide format."""

    mimeType: str


class Specimen(BaseModel):
    """Model for specimen fields."""

    anatomy: Optional[str] = None
    description: Optional[str] = None


class ImageInfo(BaseModel):
    """Model for images information."""

    id: str
    isStreamable: bool
    imageSize: Size
    tileSize: Size
    micronsPerPixel: float
    focalPlanes: List[FocalPlane]
    opticalPaths: List[OpticalPath]
    storedTileFormat: TileFormat
    availableTileFormats: List[TileFormat]
    fileFormat: SlideFormat
    staining: DisplayedName
    block: DisplayedName
    specimen: Optional[Specimen] = None
    bodyPart: Optional[str] = None
    examCode: Optional[str] = None
    examDescription: Optional[str] = None
    stationName: Optional[str] = None
    priority: Optional[int] = None
    qualityControl: Optional[QualityControlData] = None
    seriesInstanceUid: Optional[str] = None
    lisSlideId: Optional[str] = None
    accessionNumberIssuer: Optional[str] = None
    accessionNumber: Optional[str] = None
    studyInstanceUid: Optional[str] = None
    examId: Optional[str] = None
    examDateTime: Optional[str] = None
    examFreeFields: Optional[List[Dict[str, str]]] = None


class CaseImageInfo(BaseModel):
    id: str
    staining: DisplayedName
    block: DisplayedName
    specimen: Optional[Specimen] = None
    seriesInstanceUid: Optional[str] = None
    lisSlideId: Optional[str] = None
