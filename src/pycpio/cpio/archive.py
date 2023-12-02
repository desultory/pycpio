"""
Collection of CPIOData objects
"""

from zenlib.logging import loggify
from zenlib.util import handle_plural


@loggify
class CPIOArchive(dict):
    from .data import CPIOData
    from pycpio.header import HEADER_NEW

    def __setitem__(self, name, value):
        if name in self:
            raise AttributeError("Entry already exists: %s" % name)
        super().__setitem__(name, value)

    def __contains__(self, name):
        """ Check if an entry exists in the archive """
        return super().__contains__(self._normalize_name(name))

    def __init__(self, structure=HEADER_NEW, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.structure = structure

    def pop(self, name):
        """ Remove an entry from the archive """
        try:
            return super().pop(self._normalize_name(name))
        except KeyError:
            raise KeyError("Entry does not exist: %s" % name)

    def _normalize_name(self, name):
        """ Make all names relative to the archive root """
        return name.lstrip("/")

    @handle_plural
    def add_entry(self, data: CPIOData):
        """ Add a new entry to the archive """
        entry_name = self._normalize_name(data.header.name)
        self[entry_name] = data
        self.logger.debug("Added entry: %s", entry_name)
