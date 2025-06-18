"""
Collection of CPIOData objects.
Handles duplicate inodes and hashes.
Handles hardlinks and symlinks.
Normalizes names to be relative to the archive root without changing the header.
"""

from zenlib.logging import loggify
from zenlib.util import handle_plural

from .file import CPIO_File
from .symlink import CPIO_Symlink


@loggify
class CPIOArchive(dict):
    from pycpio.header import HEADER_NEW

    from .data import CPIOData

    def __setitem__(self, name, value):
        if name in self:
            raise AttributeError("Entry already exists: %s" % name)
        if name != value.header.name:
            self.logger.warning("Name mismatch: %s != %s" % (name, value.header.name))
            name = value.header.name
        # If reproduceable is enabled, set the inode to 0, so it can be recalculated
        if self.reproducible:
            value.header.ino = 0

        # Check if the inode already exists
        self._update_inodes(value)

        # Check if the hash already exists and the data is not empty
        if value.hash in self.hashes and value.data != b"" and not isinstance(value, CPIO_Symlink):
            match = self[self.hashes[value.hash]]
            self.logger.warning("[%s] Hash matches existing entry: %s" % (value.header.name, match.header.name))
            if match.data == value.data:
                self.logger.info("[%s] New hardlink detected by hash match." % value.header.name)
                self.inodes[value.header.ino].remove(value.header.name)  # Remove the name from the inode list
                value.header.ino = match.header.ino
                self._update_inodes(value)  # Update the inode list
            else:
                raise ValueError("[%s] Hash collision detected!" % value.header.name)
        else:
            # Add the name to the hash table
            self.hashes[value.hash] = name

        super().__setitem__(name, value)
        self._update_nlinks(value)

    def _update_inodes(self, entry):
        """ Checks if an entry exists with the same inode.

        If the inode exists and has entries, check if the data matches.
            If it does, it's a hardlink - update the inode list and remove the data.
        If it's a file but has no data, treat it as a hardlink and continue.
        Otherwise, if the inode exists but the data doesn't match, generate a new inode.

        Adds the updated entry to the inode list.
        """
        if entry_inodes := self.inodes.get(entry.header.ino, []):
            self.logger.log(5, "[%s] Inode already exists: %s" % (entry.header.name, entry.header.ino))

            # For regular files, check if the existing entry has the same data, if so, clear it before making a hardlink
            if isinstance(entry, CPIO_File) and self[entry_inodes[0]].data == entry.data:
                self.logger.info("[%s] New hardlink detected, removing data." % entry.header.name)
                # Remove the data from the current entry, as it now links to an existing entry
                entry.data = b""
            # If it's a file, but has no data, it's already a hardlink
            elif isinstance(entry, CPIO_File) and entry.data == b"":
                # No need to do anything, it's already a hardlink and has no data
                self.logger.debug("[%s] Hardlink detected." % entry.header.name)
            else:  # If there is a collision, generate a new inode
                from .common import get_new_inode

                if entry.header.ino == 0 and not self.reproducible:  # Warn for another inode of 0 for non-reproducible archives
                    self.logger.warning("[%s] Inode already exists: %s" % (entry.header.name, entry.header.ino))

                entry.header.ino = get_new_inode(self.inodes)
                if self.reproducible:
                    self.logger.debug("[%s] Inode recalculated: %s" % (entry.header.name, entry.header.ino))
                else:
                    self.logger.info("[%s] New inode: %s" % (entry.header.name, entry.header.ino))

        if entry.header.ino not in self.inodes:
            self.inodes[entry.header.ino] = []

        self.inodes[entry.header.ino].append(entry.header.name)

    def _update_nlinks(self, entry):
        """Update nlinks for all entries with the same inode"""
        inode = entry.header.ino
        # Get the number of links based on the number of entries with that inode
        nlink = len(self.inodes[inode])
        # Update the nlink value for all entries with that inode
        for name in self.inodes[inode]:
            self[name].header.nlink = nlink

    def __contains__(self, name):
        """Check if an entry exists in the archive"""
        return super().__contains__(self._normalize_name(name))

    def __getitem__(self, name):
        """Get an entry from the archive"""
        return super().__getitem__(self._normalize_name(name))

    def __init__(self, structure=HEADER_NEW, reproducible=False, *args, **kwargs):
        self.structure = structure
        self.reproducible = reproducible
        self.inodes = {}
        self.hashes = {}
        super().__init__(*args, **kwargs)

    def update(self, other):
        """Update the archive with the values from another archive."""
        self.add_entry(other.values())

    def pop(self, name):
        """Remove an entry from the archive"""
        normalized_name = self._normalize_name(name)
        if normalized_name not in self:
            raise KeyError("Entry does not exist: %s" % name)

        siblings = self.inodes[self[normalized_name].header.ino]
        if len(siblings) > 1 and self[normalized_name].data != b"":
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
            self._update_nlinks(self[normalized_name])

        return super().pop(normalized_name)

    def _normalize_name(self, name):
        """Make all names relative to the archive root"""
        return name.lstrip("/")

    @handle_plural
    def add_entry(self, data: CPIOData):
        """Add a new entry to the archive"""
        entry_name = self._normalize_name(data.header.name)
        if self.reproducible:
            data.header.mtime = 0
        self[entry_name] = data
        self.logger.debug("Added entry: %s", entry_name)

    def __bytes__(self):
        """Return the archive as a byte string, packed with all the data."""
        return b"".join([bytes(data) for data in self.values()])

    def list(self):
        """Return a list of all the entries in the archive."""
        return "\n".join([name for name in self.keys()])

    def __str__(self):
        """Return a string representation of the archive."""
        return "\n".join([str(data) for data in self.values()])
