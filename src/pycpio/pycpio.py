
from pathlib import Path
from typing import Union
from importlib.metadata import version

from pycpio.cpio import CPIOData, create_entry
from pycpio.masks import CPIOModes
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
    def __init__(self, structure=HEADER_NEW, name=None, *args, **kwargs):
        self.structure = structure
        self.overrides = {}
        self.entries = {}

        self.name = name

        for attr in self.structure:
            if value := kwargs.pop(attr, None):
                self.logger.info("[%s] Setting override: %s" % (attr, value))
                self.overrides[attr] = value

    def append_cpio(self, path: Path):
        """
        Appends a file or directory to the CPIO archive.
        """
        kwargs = {'name': self.name, 'logger': self.logger, '_log_init': False, 'overrides': self.overrides}
        entry = CPIOData.from_path(path, self.structure, **kwargs)

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

    def add_symlink(self, name: str, target: str):
        """
        Adds a symlink to the CPIO archive.
        """
        if name in self.entries:
            raise ValueError("Duplicate entry: %s" % name)

        symlink = self._build_cpio_entry(name=name, entry_type=CPIOModes['Symlink'].value, data=target)
        self.logger.info("Created symlink entry: %s" % symlink)
        self.entries[name] = symlink

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

    def _build_cpio_entry(self, name: str, entry_type: CPIOModes, data=None):
        """
        Creates a CPIOData object and adds it to the CPIO archive.
        """
        kwargs = {'name': name, 'structure': self.structure, 'mode': entry_type, 'data': data,
                  'overrides': self.overrides, 'logger': self.logger, '_log_init': False}

        self.logger.debug("Building CPIO entry: %s" % kwargs)
        return create_entry(**kwargs)

    def __str__(self):
        return "\n".join([str(f) for f in self.entries.values()])
