"""
CPIO data objects
"""

from pathlib import Path

from zenlib.logging import loggify

from pycpio.modes import CPIOModes


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

        path = Path(path)  # First get the mode from the file type
        if path.is_symlink():
            mode = CPIOModes.Symlink.value
        elif path.is_dir():
            mode = CPIOModes.Dir.value
        elif path.is_file():
            mode = CPIOModes.File.value
        elif path.is_block_device():
            mode = CPIOModes.BlockDev.value
        elif path.is_dir():
            mode = CPIOModes.Dir.value
        elif path.is_char_device():
            mode = CPIOModes.CharDev.value
        elif path.is_fifo():
            mode = CPIOModes.Fifo.value
        else:
            raise ValueError("Unknown file type: %s" % path)

        # Then add the permissions from the actual file
        if mode == CPIOModes.File.value:
            mode |= path.stat().st_mode & 0o777
            with open(path, 'rb') as f:
                data = f.read()
            kwargs['filesize'] = len(data)

        else:
            data = b''

        if mode in [CPIOModes.File.value, CPIOModes.Dir.value]:
            path = path.resolve()
            kwargs['mtime'] = path.stat().st_mtime

        if mode == CPIOModes.Symlink.value:
            data = str(path.readlink()).encode('ascii')
            kwargs['filesize'] = format(len(data), '08x').encode('ascii')

        kwargs['name'] = str(path)
        kwargs['mode'] = mode

        header = CPIOHeader(header_structure, logger=kwargs.pop('logger'), *args, **kwargs)
        return CPIOData.get_subtype(data, header, *args, **kwargs)

    @staticmethod
    def get_subtype(data: bytes, header, *args, **kwargs):
        """
        Get the data type from the header
        """
        mode = header.entry_mode
        if mode in CPIOModes:
            data_type = globals()[f'CPIO_{mode.name}']
            logger = header.logger
            return data_type(data, header, logger=logger, *args, **kwargs)
        raise ValueError(f"Unknown CPIO entry mode: {mode}")

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


class CPIO_Symlink(CPIOData):
    """
    Symbolic link object
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = self.data.decode('ascii').rstrip('\0')

    def __str__(self):
        return f"{super().__str__()}({self.target})"


class CPIO_Dir(CPIOData):
    """
    Directory object
    """
    pass


class CPIO_CharDev(CPIOData):
    """
    Character device object
    """
    def __str__(self):
        return f"{super().__str__()}({self.header.rdevmajor}, {self.header.rdevminor})"



