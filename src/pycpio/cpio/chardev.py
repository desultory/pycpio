"""
CPIO character device
"""

from .data import CPIOData


class CPIO_CharDev(CPIOData):
    """
    Character device object
    """
    def __str__(self):
        return f"{super().__str__()}({int(self.header.rdevmajor)}, {int(self.header.rdevminor)})"



