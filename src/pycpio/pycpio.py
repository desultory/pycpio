
from pathlib import Path
from typing import Union
from importlib.metadata import version

from pycpio.cpio import CPIOReader
from zenlib.logging import loggify

__version__ = version(__package__)


@loggify
class PyCPIO:
    """
    A class for reading CPIO archives.
    """
    def __init__(self, *args, **kwargs):
        self.files = []

    def read_cpio_file(self, file_path: Union[Path, str]):
        """
        Creates a CPIOReader object and reads the file.
        """
        reader = CPIOReader(file_path, logger=self.logger)
        self.files.extend(reader.files)

    def list_files(self):
        """
        Returns a list of files in the CPIO archive.
        """
        return '\n'.join([f.name for f in self.files])

    def __str__(self):
        return "\n".join([str(f) for f in self.files])
