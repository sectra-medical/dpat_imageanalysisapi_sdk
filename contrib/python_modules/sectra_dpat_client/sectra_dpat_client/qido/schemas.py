from enum import Enum, unique
from typing import Any, Dict, List, Union, cast

from pydantic import BaseModel


@unique
class DicomCodes(str, Enum):
    """Enum for DPAT dicom codes."""

    PATIENT_ID = "00100020"
    EXAM_ID = "00200010"
    REQUEST_ID = "00080050"
    STUDY_ID = "0020000D"


NAMES_TO_DICOM_CODES: Dict[str, DicomCodes] = {"studyInstanceUid": DicomCodes.STUDY_ID}


class DicomValue(BaseModel):
    """Model for a single Dicom field value."""

    vr: str
    Value: List[Union[str, Dict[str, "DicomValue"], Dict[str, str]]]

    def is_string(self) -> bool:
        """Checks if the value is a string. If the list of values is empty,
        returns True."""

        if len(self.Value) == 0:
            return True
        return isinstance(self.Value[0], str)

    def is_values_dict(self) -> bool:
        """Checks if the value is a dict of dicom values.
        If Value is empty, returns True.
        If all dicts are empty, returns True."""

        if len(self.Value) == 0:
            return True
        if not isinstance(self.Value[0], dict):
            return False
        for item in self.Value:
            if len(item) > 0:
                return isinstance(next(iter(item.values())), "DicomValue")  # type: ignore
        # No dict in values with an entry
        return True

    def is_str_dict(self) -> bool:
        """Checks if the value is a dict of strings.
        If Value is empty, returns True.
        If all dicts are empty, returns True."""
        if len(self.Value) == 0:
            return True
        if not isinstance(self.Value[0], dict):
            return False
        for item in self.Value:
            if len(item) > 0:
                return isinstance(next(iter(item.values())), str)  # type: ignore
        # No dict in values with an entry
        return True

    def first_as_string(self) -> str:
        """Returns the first value as a string.

        Raises:
            IndexError: if the Value is empty
        """
        return cast(str, self.Value[0])


class DicomObject:
    """Class for handling dicom objects."""

    __slots__ = ("fields",)

    def __init__(self, fields: Dict[str, Any]) -> None:
        self.fields = {k: DicomValue(**v) for k, v in fields.items()}

    def get_value_as_string(self, key: str) -> str:
        """Returns a field value as string.

        Args:
            key (str): Field key

        Returns:
            str: Field first value as string.

        Raises:
            KeyError: If the field doesn't exist
            IndexError: If the field value is empty
        """
        return self.fields[key].first_as_string()
