from typing import List, Dict, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelCaseBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        from_attributes=True,
        populate_by_name=True,
    )


class Size(CamelCaseBaseModel):
    width: int
    height: int


class FocalPlane(CamelCaseBaseModel):
    id: str
    offset_um: float


class OpticalPath(CamelCaseBaseModel):
    id: str
    description: str


class FileFormat(CamelCaseBaseModel):
    mime_type: str


class TileFormat(FileFormat):
    extension: str


class Staining(CamelCaseBaseModel):
    display_name: str


class Block(CamelCaseBaseModel):
    display_name: str


class Specimen(CamelCaseBaseModel):
    anatomy: Optional[str] = None
    description: Optional[str] = None


class CaseImage(CamelCaseBaseModel):
    id: str
    staining: Staining
    block: Block
    specimen: Specimen
    series_instance_uid: str
    lis_slide_id: Optional[str] = None


class Image(CamelCaseBaseModel):
    id: str
    staining: Staining
    block: Block
    specimen: Specimen
    is_streamable: bool
    image_size: Size
    tile_size: Size
    microns_per_pixel: float
    focal_planes: List[FocalPlane]
    optical_paths: List[OpticalPath]
    stored_tile_format: TileFormat
    available_tile_formats: List[TileFormat]
    file_format: FileFormat
    accession_number_issuer: str
    accession_number: str
    study_instance_uid: str
    exam_id: str
    exam_free_fields: List[Dict[str, str]]
    series_instance_uid: str
    exam_date_time: Optional[datetime] = None
    lis_slide_id: Optional[str] = None
    body_part: Optional[str] = None
    exam_code: Optional[str] = None
    exam_description: Optional[str] = None
    station_name: Optional[str] = None
    priority: Optional[int] = None


class Token(CamelCaseBaseModel):
    access_token: str
    token_type: str
    expires_in: int
