from zenlib.logging import loggify

from pathlib import Path
from typing import Union
from importlib.metadata import version

from .cpioentry import CPIOEntry

__version__ = version(__package__)


@loggify
class PyCPIO:
    """
    A class for reading CPIO archives.
    """
    def __init__(self, *args, **kwargs):
        self.files = []

    def read_cpio(self, file_path: Union[str, Path]):
        """
        Reads a CPIO archive.
        """
        file_path = Path(file_path)

        self.logger.info("Reading CPIO archive: %s" % file_path)
        with open(file_path, 'rb') as f:
            self.raw_cpio = f.read()

        self.logger.info("[%s] Read bytes: %s" % (file_path, len(self.raw_cpio)))

        offset = 0
        while offset < len(self.raw_cpio):
            # Start by reading one header at a time
            self.logger.debug("At offset: %s" % offset)
            header_data = self.raw_cpio[offset:offset + 110]
            entry = CPIOEntry(header_data=header_data, total_offset=offset, logger=self.logger, _log_init=False)
            offset += 110

            # Using header info, get the filename
            filename_data = self.raw_cpio[offset:offset + entry.namesize]
            entry.add_data(filename_data)
            offset += entry.get_name()

            # If it's the trailer, break
            if entry.name == 'TRAILER!!!' and not entry.entry_mode:
                self.logger.info("Trailer detected at offset: %s" % offset)
                break

            # If there's a filesize, read the file data
            if filesize := entry.filesize:
                file_data = self.raw_cpio[offset:offset + filesize]
                entry.add_data(file_data)

            # Attempt to read file contents, otherwise just set the data type
            offset += entry.read_contents()
            self.files.append(entry)
        else:
            self.logger.warning("Reached end of file without finding trailer, offset: %s" % offset)
            self.logger.debug("Trailing contents: %s" % self.raw_cpio[offset:])

    def list_files(self):
        """
        Returns a list of files in the CPIO archive.
        """
        return '\n'.join([f.name for f in self.files])

    def __str__(self):
        return "\n".join([str(f) for f in self.files])
