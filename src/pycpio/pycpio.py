
from pathlib import Path
from typing import Union
from importlib.metadata import version

from pycpio.cpio import CPIOReader, CPIOWriter, CPIOData
from pycpio.magic import CPIOMagic
from zenlib.logging import loggify

__version__ = version(__package__)


@loggify
class PyCPIO:
    """
    A class for reading CPIO archives.
    """
    def __init__(self, *args, **kwargs):
        self.entries = []

    def read_cpio_file(self, file_path: Path):
        """
        Creates a CPIOReader object and reads the file.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"{file_path} does not exist")

        reader = CPIOReader(file_path, logger=self.logger, _log_init=False)
        if structure := getattr(self, 'structure', None):
            if structure != reader.structure:
                raise ValueError(f"Structure of {file_path} does not match structure of {self.file_path}")
        else:
            self.structure = reader.structure

        self.entries.extend(reader.entries)

    def append_cpio(self, path: Path):
        """
        Appends a file or directory to the CPIO archive.
        """
        if not getattr(self, 'structure', None):
            self.structure, _ = CPIOMagic['NEW'].value
            self.logger.warning("No structure specified, using HEADER_NEW")

        if entry := CPIOData.from_path(path, self.structure, logger=self.logger, _log_init=False):
            self.logger.info("Created CPIO entry: %s", entry)
            self.entries.append(entry)
        else:
            raise ValueError(f"Could not create header for {path}")

    def write_cpio_file(self, file_path: Union[Path, str]):
        """
        Writes a CPIO archive to file.
        """
        writer = CPIOWriter(self.entries, file_path, logger=self.logger, _log_init=False)
        writer.write()

    def list_files(self):
        """
        Returns a list of files in the CPIO archive.
        """
        return '\n'.join([f.header.name for f in self.entries])

    def __str__(self):
        return "\n".join([str(f) for f in self.entries])
