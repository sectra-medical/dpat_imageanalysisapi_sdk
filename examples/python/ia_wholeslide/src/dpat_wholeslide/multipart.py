import logging
from typing import Iterable, Iterator, Tuple


class MultipartParser:
    """Parser for multipart/related response message.

    Requires (but does not check):
        - Chunk size must be equal or larger than the boundary length.
        - Parts are files with a filename in the header.
    """

    HEADER_DELIMITER = b"\r\n\r\n"
    END_DELIMITER = b"--\r\n"
    END_DELIMITER_LENGTH = len(END_DELIMITER)

    def __init__(self, chunks: Iterator[bytes], boundary: str):
        """Initialize the MultipartParser with the given chunks and boundary.

        Parameters
        ----------
        chunks : Iterator[bytes]
            Iterator of byte chunks from the response stream.
        boundary : str
            Boundary string used to separate parts in the multipart response.
        """
        self._chunks = chunks
        self._start_boundary = f"--{boundary}".encode("utf-8")
        self._boundary = "\r\n".encode("utf-8") + self._start_boundary
        self._boundary_length = len(self._boundary)

    def parts(self) -> Iterable[Tuple[str, Iterable[bytes]]]:
        """Parse the multipart response and yield parts with their filenames and chunks."""
        self._buffer = self._read_first_boundary_start()
        end_of_stream = self._check_for_end_of_stream()
        part_index = 0
        while not end_of_stream:
            filename = self._parse_part_header()
            logging.debug(f"Parsing part {part_index} with filename {filename}")
            chunks = self._parse_part_chunks()
            yield filename, chunks
            end_of_stream = self._check_for_end_of_stream()
            part_index += 1

    def _read_first_boundary_start(self) -> bytes:
        """Read the first chunk from stream and return the part after the boundary
        delimiter.

        Raises RuntimeError if the first chunk does not start with the boundary.

        Returns
        -------
        bytes
            Part of first chunk after boundary delimiter.
        """
        chunk = self._read_next_chunk_from_stream()
        if not chunk.startswith(self._start_boundary):
            raise RuntimeError(
                f"First chunk does not start with boundary {self._boundary}"
            )
        return chunk[self._boundary_length :]

    def _check_for_end_of_stream(self) -> bool:
        """Check if the end delimiter is in the buffer and if the stream has ended.

        Expect that a boundary has just been read from straem. Raises RuntimeError if
        end delimiter found but not end of stream.

        Stores any data for the next part in buffer.

        Returns
        -------
        bool
            True if end of stream.
        """
        if len(self._buffer) < self.END_DELIMITER_LENGTH:
            next_chunk = self._read_next_chunk_from_stream()
            self._buffer += next_chunk
        if self._buffer.startswith(self.END_DELIMITER):
            if (
                len(self._buffer) != self.END_DELIMITER_LENGTH
                or next(self._chunks, None) is not None
            ):
                # End delimiter found, but not the end of stream
                raise RuntimeError(
                    "End delimiter found, but the stream did not terminate as expected"
                )
            return True
        return False

    def _parse_part_header(self) -> str:
        """Parse the part header from the stream and return the filename of the part.

        Stores any data for the next part in buffer.
        Expects that the buffer is after the boundary delimiter.

        Returns
        -------
        str
            Filename of the part.
        """
        header_end_index = self._buffer.find(self.HEADER_DELIMITER)
        while header_end_index == -1:
            next_chunk = self._read_next_chunk_from_stream()
            self._buffer += next_chunk
            header_end_index = self._buffer.find(self.HEADER_DELIMITER)
        header = self._buffer[:header_end_index].decode("utf-8")
        # Set the buffer to the remaining data after the header
        self._buffer = self._buffer[header_end_index + len(self.HEADER_DELIMITER) :]
        return self._parse_filename_from_header(header)

    def _parse_filename_from_header(self, header: str) -> str:
        """Parse the filename from the header.

        Parameters
        ----------
        header : str
            Header string to parse.

        Returns
        -------
        str
            Filename extracted from the header.
        """
        for line in header.split("\r\n"):
            if line.lower().startswith("content-disposition"):
                _, *params = line.split(";")
                for param in params:
                    key, _, value = param.strip().partition("=")
                    if key.lower() == "filename":
                        filename = value.strip('"')
                        return filename

        raise ValueError("Filename not found in header")

    def _parse_part_chunks(self) -> Iterator[bytes]:
        """Read chunks from stream until boundary delimiter.

        Stores any data for the next part in buffer.

        Returns
        -------
        Iterator[bytes]
            Chunks of the part.
        """
        # Check if given chunk contains the Boundary
        end_index = self._buffer.find(self._boundary)
        while end_index == -1:
            # Boundary not found, read in next chunk
            next_chunk = self._read_next_chunk_from_stream()
            # Check if boundary between chunks. Need at most boundary length - 1 from
            # each chunk.
            first_chunk_boundary = self._buffer[-self._boundary_length + 1 :]
            second_chunk_boundary = next_chunk[: self._boundary_length - 1]
            chunk_boundary = first_chunk_boundary + second_chunk_boundary
            end_index_in_chunk_boundary = chunk_boundary.find(self._boundary)
            if end_index_in_chunk_boundary > 0:
                logging.debug("Boundary found between chunks")
                # Boundary found between chunks
                # Yield the buffer up to the Boundary
                yield self._buffer[
                    : -self._boundary_length + 1 + end_index_in_chunk_boundary
                ]
                # Set the buffer to the remaining data
                self._buffer = next_chunk[
                    : self._boundary_length - 1 + end_index_in_chunk_boundary
                ]
                return
            # Boundary not in between chunks, so yield the buffer and continue
            yield self._buffer
            self._buffer = next_chunk
            end_index = self._buffer.find(self._boundary)

        # Boundary found in the chunk, yield the chunk up to the boundary
        yield self._buffer[:end_index]
        # Set the buffer to the remaining data after the boundary
        self._buffer = self._buffer[end_index + self._boundary_length :]

    def _read_next_chunk_from_stream(self) -> bytes:
        """Read the next chunk from the stream.

        Returns
        -------
        bytes
            Next chunk from the stream.
        """
        try:
            return next(self._chunks)
        except StopIteration:
            raise RuntimeError("End of stream reached")
