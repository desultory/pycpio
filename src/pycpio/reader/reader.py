
from pathlib import Path
from typing import Union

from pycpio.cpio import CPIOArchive, pad_cpio, CPIOData
from pycpio.header import CPIOHeader
from zenlib.logging import loggify


@loggify
class CPIOReader:
    """
    A class for reading CPIO archives.
    Takes a file path as input, and reads it into self.raw_cpio.

    Once processed, the files are stored in self.entries, which is a dictionary of CPIO entries.
    """
    def __init__(self, input_file: Union[Path, str], overrides={}, *args, **kwargs):
        self.file_path = Path(input_file)
        assert self.file_path.exists(), "File does not exist: %s" % self.file_path

        self.overrides = overrides
        self.entries = CPIOArchive(logger=self.logger, _log_init=False)

        self.read_cpio_file()
        self.process_cpio_file()

    def _read_bytes(self, num_bytes: int, pad=False):
        """ Reads num_bytes from self.raw_cpio, starting at self.offset. """
        if not num_bytes:
            return b''

        data = self.cpio_file[self.offset:self.offset + num_bytes]
        if len(data) > 256:
            self.logger.debug("Read %s bytes: %s...%s" % (num_bytes, data[:128], data[-128:]))
        else:
            self.logger.debug("Read %s bytes: %s" % (num_bytes, data))
        self.offset += num_bytes

        if pad:
            pad_size = pad_cpio(self.offset)
            self.logger.debug("Padding offset by %s bytes" % pad_size)
            self.offset += pad_size
        return data

    def read_cpio_file(self):
        """ Reads a CPIO archive. """
        self.logger.debug("Reading file: %s" % self.file_path)
        with open(self.file_path, 'rb') as cpio_file:
            self.cpio_file = cpio_file.read()
            self.logger.info("[%s] Read bytes: %s" % (self.file_path, len(self.cpio_file)))

        self.logger.debug("Setting offset to 0")
        self.offset = 0

    def process_cpio_header(self) -> CPIOHeader:
        """ Processes a single CPIO header from self.raw_cpio. """
        header_data = self._read_bytes(110)

        # Start using the class kwargs, as they may contain overrides
        kwargs = {'header_data': header_data, 'overrides': self.overrides, 'logger': self.logger, '_log_init': False}

        try:
            header = CPIOHeader(**kwargs)
        except ValueError as e:
            self.logger.error("Failed to process header: %s" % e)
            self.logger.info("[%s] Header data at offset %d: %s" % (self.file_path, self.offset, header_data))
            return

        # Get the filename now that we know the size
        filename_data = self._read_bytes(int(header.namesize, 16), pad=True)
        header.add_data(filename_data)
        header.get_name()

        # If it's the trailer, break
        if not header.mode_type:
            self.logger.info("Trailer detected at offset: %s" % self.offset)
            return
        return header

    def process_cpio_data(self):
        """ Processes the file object self.cpio_file, yielding CPIOData objects. """
        while self.offset < len(self.cpio_file):
            self.logger.debug("At offset: %s" % self.offset)

            if header := self.process_cpio_header():
                kwargs = {'data': self._read_bytes(int(header.filesize, 16), pad=True),
                          'header': header, '_log_init': False}
                yield CPIOData.get_subtype(**kwargs)
            else:
                break
        else:
            self.logger.warning("Reached end of file without finding trailer")

    def process_cpio_file(self):
        """ Processes a CPIO archive."""
        for cpio_entry in self.process_cpio_data():
            self.entries.add_entry(cpio_entry)
