from enum import Enum, unique

from pydantic import BaseModel


@unique
class QualityControlStatus(str, Enum):
    """Enum for quality control status."""

    NOT_SET = "NotSet"
    QUALITY_OK = "QualityOk"
    REJECTED = "Rejected"


class QualityControlData(BaseModel):
    """Quality control data. Available from IA-API 1.10 (DPAT 4.2)"""

    status: QualityControlStatus
    versionId: str


class QualityControl(BaseModel):
    """Model for updating quality control data."""

    applicationVersion: str
    qualityControl: QualityControlData
