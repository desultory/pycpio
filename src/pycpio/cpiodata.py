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
    def __new__(cls, *args, **kwargs):
        if data_mode := kwargs.pop('data_mode', None):
            if data_mode in CPIOModes:
                # Get the data type by removing the "S_" prefix
                data_type = globals()[f'CPIO_{data_mode.name[2:]}']
                return data_type(*args, **kwargs)
        return super().__new__(cls)

    def __init__(self, data: bytes, *args, **kwargs):
        self.data = data

    def __str__(self):
        return f"{self.__class__.__name__}: ({len(self.data)})"


class CPIO_IFREG(CPIOData):
    """
    Standard file object
    """
    pass


class CPIO_IFLNK(CPIOData):
    """
    Symbolic link object
    """
    pass

