"""
CPIO data objects
"""

from .data import CPIOData


class CPIO_Symlink(CPIOData):
    """
    Symbolic link object
    """
    def __setattr__(self, key, value):
        if key == 'data':
            if isinstance(value, str):
                value = value.encode('ascii')
            elif isinstance(value, bytes):
                pass
            else:
                raise ValueError("data must be a string or bytes")

            if value and value[-1] != b'\0':
                value += b'\0'
            self.header.filesize = format(len(value), '08x').encode('ascii')

        super().__setattr__(key, value)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if path := kwargs.pop('path', None):
            self.data = str(path.readlink()).encode('ascii')
            self.header.mtime = path.stat().st_mtime
        elif self.data is None:
            raise ValueError("path must be specified for symlinks")

        self.header.mode = 0o120777  # symlink mode

    def __str__(self):
        target = self.data.decode('ascii').rstrip('\0')
        return f"{super().__str__()}({target})"
