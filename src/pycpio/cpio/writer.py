
from zenlib.logging import loggify

from .common import pad_cpio, get_new_inode
from .header import CPIOHeader
from pycpio.magic import CPIOMagic

from pathlib import Path


@loggify
class CPIOWriter:
    """
    Takes a list of CPIOData objects,
    writes them to the file specified by output_file.
    """
    def __init__(self, cpio_entries: list, output_file: Path, structure=None, *args, **kwargs):
        self.cpio_entries = cpio_entries
        self.output_file = Path(output_file)

        if structure is None:
            magic, strucutre = CPIOMagic['NEW'].value

        self.structure = structure

    def write(self):
        """
        Writes the CPIOData objects to the output file.
        """
        inodes = set()
        self.logger.info(f"Writing CPIO archive to {self.output_file}")
        offset = 0
        with open(self.output_file, "wb") as f:
            for entry in self.cpio_entries.values():
                # IDK if i want to do hardlink stuff here or in the PyCpio class
                # That class manages the CPIOData objects, as well as duplicate detection
                # If data is passed to the writer, it should try to write it
                if entry.header.ino in inodes:
                    self.logger.warning(f"Duplicate inode: {entry.header.ino}")
                    entry.header.ino = get_new_inode(inodes)
                    self.logger.info(f"New inode: {entry.header.ino}")
                inodes.add(entry.header.ino)
                entry_bytes = bytes(entry)
                padding = pad_cpio(len(entry_bytes))
                output_bytes = entry_bytes + b'\x00' * padding
                f.write(output_bytes)
                self.logger.debug("[%d] Wrote '%d' bytes for: %s" % (offset, len(output_bytes), entry.header.name))
                offset += len(output_bytes)
            trailer = CPIOHeader(self.structure, name="TRAILER!!!")
            self.logger.debug("Writing trailer: %s" % trailer)
            f.write(bytes(trailer))

        self.logger.info("Finished writing CPIO archive")
