
from pathlib import Path
from typing import Union
from importlib.metadata import version

from pycpio.cpio import CPIOData
from pycpio.header import HEADER_NEW
from pycpio.writer import CPIOWriter
from pycpio.reader import CPIOReader
from zenlib.logging import loggify

__version__ = version(__package__)


@loggify
class PyCPIO:
    """
    A class for reading CPIO archives.
    """
    def __init__(self, *args, **kwargs):
        self.overrides = {}
        self.entries = {}

        self.structure = kwargs.pop('structure', HEADER_NEW)

        for name in self.structure:
            if value := kwargs.pop(name, None):
                self.logger.info("[%s] Setting override: %s" % (name, value))
                self.overrides[name] = value

    def read_cpio_file(self, file_path: Path):
        """
        Creates a CPIOReader object and reads the file.
        """
        kwargs = {'input_file': file_path, 'overrides': self.overrides, 'logger': self.logger, '_log_init': False}
        reader = CPIOReader(**kwargs)

        for name, entry in reader.entries.items():
            self.logger.debug("[%s]Read CPIO entry: %s" % (file_path.name, entry))
            if name in self.entries:
                raise ValueError("Duplicate entry: %s" % entry.header.name)
            if entry.header.structure != self.structure:
                raise ValueError("Entry structure does not match archive structure: %s" % entry)
            self.entries[name] = entry

    def append_cpio(self, path: Path):
        """
        Appends a file or directory to the CPIO archive.
        """
        entry = CPIOData.from_path(path, self.structure, logger=self.logger, _log_init=False)

        if entry.header.name in self.entries:
            raise ValueError(f"Duplicate entry: {entry.header.name}")

        self.entries[entry.header.name] = entry

    def remove_cpio(self, name: str):
        """
        Removes an entry from the CPIO archive.
        """
        if name not in self.entries:
            if path := Path(name).resolve():
                if path.is_absolute():
                    path = path.relative_to(path.anchor)
                self.logger.debug("Resolved entry path: %s" % path)

                name = str(path)
                if name not in self.entries:
                    self.logger.info("Current entries: %s" % self.entries)
                    raise ValueError(f"Entry not found: {name}")
            else:
                raise ValueError(f"Entry not found: {name}")

        self.logger.info("Removed entry: %s" % self.entries.pop(name))

    def write_cpio_file(self, file_path: Union[Path, str]):
        """
        Writes a CPIO archive to file.
        """
        kwargs = {'logger': self.logger, '_log_init': False}

        if hasattr(self, 'structure'):
            kwargs['structure'] = self.structure

        writer = CPIOWriter(self.entries, file_path, **kwargs)
        writer.write()

    def list_files(self):
        """
        Returns a list of files in the CPIO archive.
        """
        return '\n'.join([name for name in self.entries.keys()])

    def __str__(self):
        return "\n".join([str(f) for f in self.entries.values()])
