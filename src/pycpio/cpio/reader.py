
from pathlib import Path
from typing import Union

from .common import pad_cpio
from .header import CPIOHeader
from .data import CPIOData
from pycpio.magic import CPIOMagic
from zenlib.logging import loggify


@loggify
class CPIOReader:
    """
    A class for reading CPIO archives.
    Takes a file path as input, and reads it into self.raw_cpio.

    Once processed, the files are stored in self.entries, which is a list of CPIOData objects.
    """
    def __init__(self, input_file: Union[Path, str], *args, **kwargs):
        self.file_path = Path(input_file)
        self.entries = []

        self.read_cpio_file()
        self.process_cpio_file()

    def _read_bytes(self, num_bytes: int, pad=False):
        """ Reads num_bytes from self.raw_cpio, starting at self.offset. """
        if not num_bytes:
            return b''

        data = self.cpio_file[self.offset:self.offset + num_bytes]
        if len(data) > 128:
            self.logger.debug("Read %s bytes: %s..." % (num_bytes, data[:128]))
        else:
            self.logger.debug("Read %s bytes: %s" % (num_bytes, data))
        self.offset += num_bytes

        if pad:
            pad_size = pad_cpio(self.offset)
            self.logger.debug("Padding offset by %s bytes" % pad_size)
            self.offset += pad_size
        return data

    def process_magic(self):
        """ Processes the magic number at the beginning of the CPIO archive. """
        magic_bytes = self._read_bytes(6)

        if hasattr(self, 'structure'):
            if magic_bytes != self.magic:
                self.logger.debug(self.cpio_file[self.offset - 32:self.offset + 32])
                raise ValueError("Magic number mismatch: %s != %s" % (magic_bytes, self.magic))
            return

        for magic_type in CPIOMagic:
            magic, structure = magic_type.value
            if magic == magic_bytes:
                self.logger.debug("Using structure: %s" % structure)
                self.structure = structure
                self.magic = magic
                break
        else:
            raise ValueError("Magic number not found in CPIOMagic: %s" % magic_bytes)

    def read_cpio_file(self):
        """ Reads a CPIO archive. """
        self.logger.info("Reading CPIO archive: %s" % self.file_path)
        with open(self.file_path, 'rb') as cpio_file:
            self.cpio_file = cpio_file.read()
            self.logger.info("[%s] Read bytes: %s" % (self.file_path, len(self.cpio_file)))

        self.logger.debug("Setting offset to 0")
        self.offset = 0

    def process_cpio_header(self) -> CPIOHeader:
        """ Processes a single CPIO header from self.raw_cpio. """
        self.process_magic()
        # The magic number was already read, so we need to read the rest of the header
        header_data = self.magic + self._read_bytes(104)
        kwargs = {'header_structure': self.structure, 'header_data': header_data,
                  'logger': self.logger, '_log_init': False}
        header = CPIOHeader(**kwargs)

        # Get the filename now that we know the size
        filename_data = self._read_bytes(int(header.namesize, 16), pad=True)
        header.add_data(filename_data)
        header.get_name()

        # If it's the trailer, break
        if header.name == 'TRAILER!!!' and not header.entry_mode:
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
                self.logger.info("Reached end of CPIO archive")
                break
        else:
            self.logger.warning("Reached end of file without finding trailer")

    def process_cpio_file(self):
        """ Processes a CPIO archive."""
        for cpio_entry in self.process_cpio_data():
            self.entries.append(cpio_entry)
