from pathlib import Path
from typing import Generator, Union, Any

from pycpio.cpio import CPIOArchive, CPIOData, pad_cpio
from pycpio.header import CPIOHeader
from zenlib.logging import LoggerMixIn


class CPIOReader(LoggerMixIn):
    """
    A class for reading CPIO archives.
    Takes a file path as input, and reads it into self.raw_cpio.

    Once processed, the files are stored in self.entries, which is a dictionary of CPIO entries.
    """

    def __init__(self, input_file: Union[Path, str], overrides: Union[dict[str, Any], None] = None, *args, **kwargs):
        if overrides is None:
            overrides = {}
        self.init_logger(args, kwargs)

        self.file_path: Union[Path, int] = Path(input_file)
        if self.file_path == Path('-'):
            # opening just '0' indicates stdin
            self.file_path = 0
        else:
            # normal file
            assert self.file_path.exists(), "File does not exist: %s" % self.file_path
        self.data_bytes: bytes = b""

        self.overrides: dict[str, Any] = overrides
        self.entries: CPIOArchive = CPIOArchive(logger=self.logger)
        self.offset: int = 0

        self.read_cpio_file()
        self.process_cpio_file()

    def _read_bytes(self, num_bytes: int, pad: bool = False) -> bytes:
        """Reads num_bytes from self.raw_cpio, starting at self.offset."""
        if not num_bytes:
            return b""

        data = self.data_bytes[self.offset : self.offset + num_bytes]
        if len(data) > 256:
            self.logger.debug("Read %d bytes: %r...%r" % (num_bytes, data[:128], data[-128:]))
        else:
            self.logger.debug("Read %d bytes: %r" % (num_bytes, data))
        self.offset += num_bytes

        if pad:
            pad_size = pad_cpio(self.offset)
            self.logger.debug("Padding offset by %d bytes" % pad_size)
            self.offset += pad_size
        return data

    def read_cpio_file(self) -> None:
        """
        Reads a CPIO archive into self.data_bytes.
        Resets the offset to 0, preparing for processing.
        """
        self.logger.debug("Reading file: %s" % self.file_path)
        with open(self.file_path, "rb") as cpio_file:
            self.data_bytes = cpio_file.read()
            self.logger.info("[%s] Read bytes: %d" % (self.file_path, len(self.data_bytes)))

        if self.offset != 0:
            self.logger.debug("Resetting read offset to 0")
            self.offset = 0

    def process_cpio_header(self) -> Union[CPIOHeader, None]:
        """Processes a single CPIO header from self.raw_cpio."""
        header_data = self._read_bytes(110)

        # Start using the class kwargs, as they may contain overrides
        kwargs = {"header_data": header_data, "overrides": self.overrides, "logger": self.logger}

        try:
            header = CPIOHeader(**kwargs)
        except ValueError as e:
            self.logger.error("Failed to process header: %s" % e)
            return self.logger.info("[%s] Header data at offset %d: %r" % (self.file_path, self.offset, header_data))

        # Get the filename now that we know the size
        filename_data = self._read_bytes(int(header.namesize, 16), pad=True)
        header.add_data(filename_data)
        header.get_name()

        # If it's the trailer, break
        if not header.mode_type:
            return self.logger.info("Trailer detected at offset: %s" % self.offset)
        return header

    def process_cpio_data(self) -> Generator[CPIOData, None, None]:
        """Processes the file object self.data_bytes, yielding CPIOData objects."""
        while self.offset < len(self.data_bytes):
            self.logger.debug("At offset: %s" % self.offset)

            if header := self.process_cpio_header():
                filesize = int(getattr(header, "filesize", "0"), 16)
                data = self._read_bytes(filesize, pad=True)
                yield CPIOData(header=header, data=data, logger=self.logger)
            else:
                break
        else:
            self.logger.warning("Reached end of file without finding trailer")

    def process_cpio_file(self) -> None:
        """
        Processes a CPIO archive.
        Uses reads data from self.data_bytes, and processes it into CPIOData objects.
        When opjects are processed, the internal offset is updated.
        Processed objects are stored in self.entries.
        """
        for cpio_entry in self.process_cpio_data():
            self.entries.add_entry(cpio_entry)
