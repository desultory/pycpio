"""
CPIO data objects
"""

from .data import CPIOData


class CPIO_Symlink(CPIOData):
    """
    Symbolic link object
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if path := kwargs.pop('path', None):
            self.data = str(path.readlink()).encode('ascii')
            kwargs['filesize'] = format(len(self.data), '08x').encode('ascii')

    def __str__(self):
        target = self.data.decode('ascii').rstrip('\0')
        return f"{super().__str__()}({target})"
