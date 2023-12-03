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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not getattr(self.header, "rdevmajor", None):
            raise ValueError("rdevmajor must be set")
        if not getattr(self.header, "rdevminor", None):
            raise ValueError("rdevminor must be set")
        if int(self.header.mode, 16) & 0o777 == 0:
            self.logger.debug("Setting mode to 644")
            self.header.mode = (int(self.header.mode, 16) & 0o7777000) | (0o644)

    def __bytes__(self):
        """ Just return the header """
        return bytes(self.header)
