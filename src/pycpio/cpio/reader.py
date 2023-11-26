
from pathlib import Path
from typing import Union

from .header import CPIOHeader
from .data import CPIOData
from zenlib.logging import loggify


@loggify
class CPIOReader:
    """
    A class for reading CPIO archives.
    Takes a file path as input, and reads it into self.raw_cpio.

    Once processed, the files are stored in self.files, which is a list of CPIOEntry objects.
    """
    def __init__(self, input_file: Union[Path, str], *args, **kwargs):
        self.file_path = Path(input_file)
        self.files = []

        self.read_cpio_file()
        self.process_cpio_file()

    def _read_bytes(self, num_bytes: int, pad=False):
        """
        Reads num_bytes from self.raw_cpio, starting at self.offset.
        """
        if not num_bytes:
            return b''

        data = self.raw_cpio[self.offset:self.offset + num_bytes]
        self.logger.debug("Read %s bytes: %s" % (num_bytes, data))
        self.offset += num_bytes

        if pad and self.offset % 4:
            pad_size = 4 - (self.offset % 4)
            self.logger.debug("Padding offset by %s bytes" % pad_size)
            self.offset += pad_size
        return data

    def read_cpio_file(self):
        """
        Reads a CPIO archive.
        """
        self.logger.info("Reading CPIO archive: %s" % self.file_path)
        with open(self.file_path, 'rb') as f:
            self.raw_cpio = f.read()
            self.logger.info("[%s] Read bytes: %s" % (self.file_path, len(self.raw_cpio)))

        self.logger.debug("Setting offset to 0")
        self.offset = 0

    def process_cpio_header(self) -> CPIOHeader:
        """
        Processes a single CPIO header from self.raw_cpio.
        """
        header_data = self._read_bytes(110)
        header = CPIOHeader(header_data=header_data, logger=self.logger, _log_init=False)

        # Get the filename now that we know the size
        filename_data = self._read_bytes(header.namesize, pad=True)
        header.add_data(filename_data)
        header.get_name()

        # If it's the trailer, break
        if header.name == 'TRAILER!!!' and not header.entry_mode:
            self.logger.info("Trailer detected at offset: %s" % self.offset)
            return
        return header

    def process_cpio_contents(self, header: CPIOHeader):
        """
        Attempts to read the contents of a CPIO entry.
        """
        return CPIOData.get_subtype(data=self._read_bytes(header.filesize, pad=True), header=header, _log_init=False)

    def process_cpio_data(self):
        """
        Processes a single CPIO entry.
        """
        while self.offset < len(self.raw_cpio):
            self.logger.debug("At offset: %s" % self.offset)

            if header := self.process_cpio_header():
                data = self.process_cpio_contents(header)
                yield data
            else:
                self.logger.info("Reached end of CPIO archive")
                break
        else:
            self.logger.warning("Reached end of file without finding trailer")

    def process_cpio_file(self):
        """
        Processes a CPIO archive.
        """
        for cpio_entry in self.process_cpio_data():
            self.files.append(cpio_entry)
