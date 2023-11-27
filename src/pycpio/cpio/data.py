"""
CPIO data objects
"""

from pathlib import Path

from zenlib.logging import loggify

from pycpio.modes import mode_bytes_from_path


@loggify
class CPIOData:
    """
    Generic object for CPIO data
    """
    @staticmethod
    def from_path(path: Path, header_structure, *args, **kwargs):
        """
        Create a CPIOData object from a path
        """
        from pycpio.cpio import CPIOHeader

        path = Path(path)
        kwargs['path'] = path
        kwargs['name'] = str(path)
        kwargs['mode'] = mode_bytes_from_path(path)

        header = CPIOHeader(header_structure, logger=kwargs.pop('logger'), *args, **kwargs)
        return CPIOData.get_subtype(b'', header, *args, **kwargs)

    @staticmethod
    def get_subtype(data: bytes, header, *args, **kwargs):
        """
        Get the data type from the header
        """
        mode = header.mode_type
        logger = header.logger
        # Just attempt to get the data type from the mode name
        data_type = globals()[f'CPIO_{mode.name}']
        return data_type(data, header, logger=logger, *args, **kwargs)

    def __init__(self, data: bytes, header, *args, **kwargs):
        self.data = data
        self.header = header

    def __str__(self):
        out_str = f"\n{self.header}"
        out_str += f"{self.__class__.__name__} "
        return out_str

    def __bytes__(self):
        """
        Convert the data to bytes
        """
        return bytes(self.header) + self.data


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
            if path.is_absolute():
                self.header.name = str(path.relative_to(path.anchor))


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


class CPIO_Dir(CPIOData):
    """
    Directory object
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if path := kwargs.pop('path', None):
            path = path.resolve()
            self.header.mode = int(self.header.mode, 16) | (path.stat().st_mode & 0o777)
            self.header.mtime = path.resolve().stat().st_mtime
            if path.is_absolute():
                self.header.name = str(path.relative_to(path.anchor))


class CPIO_CharDev(CPIOData):
    """
    Character device object
    """
    def __str__(self):
        return f"{super().__str__()}({int(self.header.rdevmajor)}, {int(self.header.rdevminor)})"



