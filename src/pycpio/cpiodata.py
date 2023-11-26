"""
CPIO data objects
"""

from zenlib.logging import loggify

from .header import CPIOModes


@loggify
class CPIOData:
    """
    Generic object for CPIO data
    """
    @staticmethod
    def from_bytes(data: bytes, header, *args, **kwargs):
        """
        Get the data type from the header
        """
        mode = header.entry_mode
        if mode in CPIOModes:
            # Get the data type by removing the "S_" prefix
            data_type = globals()[f'CPIO_{mode.name[2:]}']
            logger = header.logger
            return data_type(data, header, logger=logger, *args, **kwargs)
        raise ValueError(f"Unknown CPIO entry mode: {mode}")

    def __init__(self, data: bytes, header, *args, **kwargs):
        self.data = data
        self.header = header

    def __str__(self):
        out_str = f"{self.__class__.__name__}: ({len(self.data)} bytes)"
        return out_str


class CPIO_IFREG(CPIOData):
    """
    Standard file object
    """
    pass


class CPIO_IFLNK(CPIOData):
    """
    Symbolic link object
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target = self.data.decode('ascii').rstrip('\0')

    def __str__(self):
        return f"{self.__class__.__name__}: ({self.target})"


class CPIO_IFDIR(CPIOData):
    """
    Directory object
    """
    pass


class CPIO_IFCHR(CPIOData):
    """
    Character device object
    """
    def __str__(self):
        return f"{self.__class__.__name__}: ({self.header.rdevmajor}, {self.header.rdevminor})"




