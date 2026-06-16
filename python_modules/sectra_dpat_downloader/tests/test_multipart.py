from typing import Dict, Iterator, List, Tuple

import pytest

from sectra_dpat_downloader.multipart import MultipartParser

BOUNDARY = "boundary-1234567890"
# Smallest chunk size the parser supports: the full "\r\n--<boundary>" delimiter.
MIN_CHUNK_SIZE = len(f"\r\n--{BOUNDARY}".encode("utf-8"))


def _build_body(parts: List[Tuple[str, bytes]]) -> bytes:
    """Build a multipart/related body for the given (filename, content) parts."""
    body = b""
    for filename, content in parts:
        body += f"--{BOUNDARY}\r\n".encode("utf-8")
        body += (
            f'Content-Disposition: attachment; filename="{filename}"\r\n'.encode(
                "utf-8"
            )
        )
        body += b"Content-Type: application/octet-stream\r\n\r\n"
        body += content
        body += b"\r\n"
    body += f"--{BOUNDARY}--\r\n".encode("utf-8")
    return body


def _chunked(data: bytes, chunk_size: int) -> Iterator[bytes]:
    """Yield the data in fixed-size chunks."""
    for index in range(0, len(data), chunk_size):
        yield data[index : index + chunk_size]


def _parse(data: bytes, chunk_size: int) -> Dict[str, bytes]:
    """Parse a body fed in chunks of the given size into a {filename: content} dict."""
    parser = MultipartParser(_chunked(data, chunk_size), BOUNDARY)
    return {filename: b"".join(chunks) for filename, chunks in parser.parts()}


class TestParts:
    def test_single_part(self):
        # Arrange
        body = _build_body([("a.bin", b"hello world")])

        # Act
        result = _parse(body, chunk_size=len(body))

        # Assert
        assert result == {"a.bin": b"hello world"}

    def test_multiple_parts(self):
        # Arrange
        body = _build_body(
            [("a.bin", b"AAAA"), ("b.bin", b"BBBBBB"), ("c.bin", b"C")]
        )

        # Act
        result = _parse(body, chunk_size=len(body))

        # Assert
        assert result == {"a.bin": b"AAAA", "b.bin": b"BBBBBB", "c.bin": b"C"}

    @pytest.mark.parametrize("chunk_size", list(range(MIN_CHUNK_SIZE, 64)))
    def test_boundary_straddling_chunks_at_every_size(self, chunk_size):
        # Arrange
        # Two parts so a boundary appears mid-stream; sweeping chunk sizes forces
        # the inter-part boundary to straddle a chunk edge at different offsets.
        contents = {"first.bin": b"0123456789" * 5, "second.bin": b"abcdef" * 7}
        body = _build_body(list(contents.items()))

        # Act
        result = _parse(body, chunk_size=chunk_size)

        # Assert
        assert result == contents

    def test_chunk_size_equal_to_boundary_length(self):
        # Arrange
        # The smallest documented supported chunk size is the boundary length.
        body = _build_body([("a.bin", b"some content here"), ("b.bin", b"more")])

        # Act
        result = _parse(body, chunk_size=MIN_CHUNK_SIZE)

        # Assert
        assert result == {"a.bin": b"some content here", "b.bin": b"more"}

    @pytest.mark.parametrize("chunk_size", list(range(MIN_CHUNK_SIZE, 90)))
    def test_mixed_part_sizes_at_every_chunk_size(self, chunk_size):
        # Arrange
        # Mix tiny and larger parts so boundaries land at many offsets relative
        # to the chunk edges regardless of chunk size.
        contents = {
            "tiny.bin": b"x",
            "medium.bin": b"0123456789" * 4,
            "another.bin": b"y",
            "last.bin": b"abcdefghij" * 3,
        }
        body = _build_body(list(contents.items()))

        # Act
        result = _parse(body, chunk_size=chunk_size)

        # Assert
        assert result == contents

    def test_binary_content_with_embedded_crlf(self):
        # Arrange
        # Content that contains bytes resembling delimiters must not be split.
        tricky = b"\r\n--not-the-boundary\r\ndata\r\n"
        body = _build_body([("a.bin", tricky)])

        # Act
        result = _parse(body, chunk_size=MIN_CHUNK_SIZE)

        # Assert
        assert result == {"a.bin": tricky}

    def test_part_smaller_than_boundary(self):
        # Arrange
        # A part whose content is shorter than the boundary still parses.
        body = _build_body([("tiny.bin", b"x"), ("b.bin", b"data")])

        # Act
        result = _parse(body, chunk_size=MIN_CHUNK_SIZE)

        # Assert
        assert result == {"tiny.bin": b"x", "b.bin": b"data"}

    def test_empty_part(self):
        # Arrange
        body = _build_body([("empty.bin", b""), ("b.bin", b"data")])

        # Act
        result = _parse(body, chunk_size=MIN_CHUNK_SIZE)

        # Assert
        assert result == {"empty.bin": b"", "b.bin": b"data"}


class TestErrors:
    def test_first_chunk_not_boundary_raises(self):
        # Arrange
        body = b"garbage that does not start with a boundary at all"

        # Act / Assert
        with pytest.raises(RuntimeError, match="does not start with boundary"):
            _parse(body, chunk_size=len(body))

    def test_missing_filename_raises(self):
        # Arrange
        body = (
            f"--{BOUNDARY}\r\n".encode("utf-8")
            + b"Content-Disposition: attachment\r\n\r\n"
            + b"content"
            + b"\r\n"
            + f"--{BOUNDARY}--\r\n".encode("utf-8")
        )

        # Act / Assert
        with pytest.raises(ValueError, match="Filename not found"):
            _parse(body, chunk_size=len(body))

    def test_truncated_stream_raises(self):
        # Arrange
        # A body that never sends the terminating end delimiter.
        body = (
            f"--{BOUNDARY}\r\n".encode("utf-8")
            + b'Content-Disposition: attachment; filename="a.bin"\r\n\r\n'
            + b"content with no closing boundary"
        )

        # Act / Assert
        with pytest.raises(RuntimeError, match="End of stream reached"):
            _parse(body, chunk_size=MIN_CHUNK_SIZE)
