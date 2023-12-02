
from pathlib import Path
from typing import Union

from pycpio.cpio import CPIOArchive, CPIOData
from pycpio.masks import CPIOModes
from pycpio.header import HEADER_NEW
from pycpio.writer import CPIOWriter
from pycpio.reader import CPIOReader
from zenlib.logging import loggify


@loggify
class PyCPIO:
    """
    A class for reading CPIO archives.
    """
    def __init__(self, structure=HEADER_NEW, *args, **kwargs):
        self.structure = structure
        self.overrides = {}
        self.entries = CPIOArchive(self.structure, logger=self.logger, _log_init=False)

        for attr in self.structure:
            if value := kwargs.pop(attr, None):
                self.logger.info("[%s] Setting override: %s" % (attr, value))
                self.overrides[attr] = value

    def append_cpio(self, path: Path, name: str = None):
        """
        Appends a file or directory to the CPIO archive.
        """
        kwargs = {'path': path, 'structure': self.structure, 'logger': self.logger, '_log_init': False, 'overrides': self.overrides}
        if name:
            kwargs['name'] = name
        self.entries.add_entry(CPIOData.from_path(**kwargs))

    def remove_cpio(self, name: str):
        """
        Removes an entry from the CPIO archive.
        """
        self.logger.info("Removed entry: %s" % self.entries.pop(name))

    def add_symlink(self, name: str, target: str):
        """
        Adds a symlink to the CPIO archive.
        """
        self._build_cpio_entry(name=name, entry_type=CPIOModes['Symlink'].value, data=target)

    def add_chardev(self, name: str, major: int, minor: int):
        """
        Adds a character device to the CPIO archive.
        """
        self._build_cpio_entry(name=name, entry_type=CPIOModes['CharDev'].value, rdevmajor=major, rdevminor=minor)

    def read_cpio_file(self, file_path: Path):
        """
        Creates a CPIOReader object and reads the file.
        """
        kwargs = {'input_file': file_path, 'overrides': self.overrides, 'logger': self.logger, '_log_init': False}
        reader = CPIOReader(**kwargs)
        self.entries.add_entry(reader.entries.values())

    def write_cpio_file(self, file_path: Union[Path, str]):
        """
        Writes a CPIO archive to file.
        """
        kwargs = {'logger': self.logger, 'structure': self.structure, '_log_init': False}
        writer = CPIOWriter(self.entries, file_path, **kwargs)
        writer.write()

    def list_files(self):
        """
        Returns a list of files in the CPIO archive.
        """
        return '\n'.join([name for name in self.entries.keys()])

    def _build_cpio_entry(self, name: str, entry_type: CPIOModes, data=None, **kwargs):
        """
        Creates a CPIOData object and adds it to the CPIO archive.
        """
        kwargs = {'name': name, 'structure': self.structure, 'mode': entry_type, 'data': data,
                  'overrides': self.overrides, 'logger': self.logger, '_log_init': False, **kwargs}

        self.entries.add_entry(CPIOData.create_entry(**kwargs))

    def __str__(self):
        return "\n".join([str(f) for f in self.entries.values()])
