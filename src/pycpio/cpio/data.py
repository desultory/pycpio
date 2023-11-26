"""
CPIO data objects
"""

from zenlib.logging import loggify

from pycpio.modes import CPIOModes


@loggify
class CPIOData:
    """
    Generic object for CPIO data
    """
    @staticmethod
    def get_subtype(data: bytes, header, *args, **kwargs):
        """
        Get the data type from the header
        """
        mode = header.entry_mode
        if mode in CPIOModes:
            # Get the data type by removing the "S_" prefix
            data_type = globals()[f'CPIO_{mode.name}']
            logger = header.logger
            return data_type(data, header, logger=logger, *args, **kwargs)
        raise ValueError(f"Unknown CPIO entry mode: {mode}")

    def __init__(self, data: bytes, header, *args, **kwargs):
        self.data = data
        self.header = header

    def __str__(self):
        out_str = f"\n{self.header.name}: {self.header}"
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



