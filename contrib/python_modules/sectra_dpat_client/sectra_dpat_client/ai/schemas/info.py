from pydantic import BaseModel


class ApplicationInfo(BaseModel):
    """Model for applications info."""

    apiVersion: str
    softwareVersion: str
