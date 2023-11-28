"""
CPIO file object
"""

from .data import CPIOData


class CPIO_File(CPIOData):
    """
    Standard file object
    """
    def __str__(self):
        return f"{super().__str__()}({len(self.data)} bytes)"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if path := kwargs.pop('path', None):
            path = path.resolve()
            with path.open('rb') as f:
                self.data = f.read()
            self.header.filesize = format(len(self.data), '08x').encode('ascii')
            self.header.mtime = path.resolve().stat().st_mtime
            self.header.mode = int(self.header.mode, 16) | (path.stat().st_mode & 0o777)
            if not kwargs.get('name') and path.is_absolute():
                self.header.name = str(path.relative_to(path.anchor))


