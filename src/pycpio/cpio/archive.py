"""
Collection of CPIOData objects.
Handles duplicate inodes and hashes.
Handles hardlinks and symlinks.
Normalizes names to be relative to the archive root without changing the header.
"""

from zenlib.logging import loggify
from zenlib.util import handle_plural
from .symlink import CPIO_Symlink


@loggify
class CPIOArchive(dict):
    from .data import CPIOData
    from pycpio.header import HEADER_NEW

    def __setitem__(self, name, value):
        if name in self:
            raise AttributeError("Entry already exists: %s" % name)
        # Check if the inode already exists
        # Ignore symlinks, they can have the same inode
        # Remove data from hardlinks, to save space
        if value.header.ino in self.inodes:
            if isinstance(value, CPIO_Symlink):
                self.logger.debug("[%s] Symlink inode already exists: %s" % (value.header.name, value.header.ino))
            elif self[self.inodes[value.header.ino][0]].data == value.data:
                self.logger.info("[%s] New hardlink detected, removing data." % value.header.name)
                # Remove the data from the current entry
                value.data = b''
            elif value.data == b'':
                self.logger.debug("[%s] Hardlink detected." % value.header.name)
            else:
                from .common import get_new_inode
                self.logger.warning("[%s] Inode already exists: %s" % (value.header.name, value.header.ino))
                value.header.ino = get_new_inode(self.inodes)
                self.logger.info("New inode: %s", value.header.ino)
            self.inodes[value.header.ino].append(name)
        else:
            # Create an inode entry with the name
            self.inodes[value.header.ino] = [name]

        # Check if the hash already exists and the data is not empty
        if value.hash in self.hashes and value.data != b'' and not isinstance(value, CPIO_Symlink):
            match = self[self.hashes[value.hash]]
            self.logger.warning("[%s] Hash matches existing entry: %s" % (value.header.name, match.header.name))
            value.header.ino = match.header.ino
            # run setitem again to handle the duplicate inode as a hardlink
            self[name] = value
        else:
            # Add the name to the hash table
            self.hashes[value.hash] = name

        super().__setitem__(name, value)
        self._update_nlinks(value.header.ino)

    def _update_nlinks(self, inode):
        """ Update nlinks for all entries with the same inode """
        # Get the number of links based on the number of entries with that inode
        nlink = len(self.inodes[inode])
        # Update the nlink value for all entries with that inode
        for name in self.inodes[inode]:
            self[name].header.nlink = nlink

    def __contains__(self, name):
        """ Check if an entry exists in the archive """
        return super().__contains__(self._normalize_name(name))

    def __init__(self, structure=HEADER_NEW, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.structure = structure
        self.inodes = {}
        self.hashes = {}

    def update(self, other):
        """ Update the archive with the values from another archive. """
        self.add_entry(other.values())

    def pop(self, name):
        """ Remove an entry from the archive """
        normalized_name = self._normalize_name(name)
        if normalized_name not in self:
            raise KeyError("Entry does not exist: %s" % name)

        siblings = self.inodes[self[normalized_name].header.ino]
        if len(siblings) > 1 and self[normalized_name].data != b'':
            # Get the data associated with this inode
            for sibling_name in siblings:
                if self[sibling_name].data:
                    data = self[sibling_name].data
                    break
            else:
                raise RuntimeError("No data found for inode: %s" % self[normalized_name].header.ino)

            # Remove the name from the inode list
            siblings.remove(normalized_name)
            self[siblings[0]].data = data
            self.logger.info("[%s] Moved entry data to: %s" % (normalized_name, siblings[0]))
            # Remove the name from the hash list
            del self.hashes[self[normalized_name].hash]
            # Update the nlink value for all entries with that inode
            self._update_nlinks(self[normalized_name].header.ino)

        return super().pop(normalized_name)

    def _normalize_name(self, name):
        """ Make all names relative to the archive root """
        return name.lstrip("/")

    @handle_plural
    def add_entry(self, data: CPIOData):
        """ Add a new entry to the archive """
        entry_name = self._normalize_name(data.header.name)
        self[entry_name] = data
        self.logger.debug("Added entry: %s", entry_name)
