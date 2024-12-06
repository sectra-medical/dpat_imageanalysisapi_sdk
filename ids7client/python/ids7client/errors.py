class IDS7RequestError(Exception):
    """Exception raised when a request to IDS7 has failed."""

    __slots__ = ("status_code", "text", "path")

    def __init__(self, status_code: int, text: str, path: str) -> None:
        self.status_code = status_code
        self.text = text
        self.path = path
        super().__init__(
            f"Request {path} has failed with status code {status_code}: {text}"
        )
