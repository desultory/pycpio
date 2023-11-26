"""
CPIO header mode masks.
"""

from enum import Enum


class Modes(Enum):
    """
    Enum for CPIO mode masks.
    """
    Socket = 0o140000  # Socket
    Symlink = 0o120000  # Symbolic link
    File = 0o100000  # Regular file
    BlkDev = 0o060000  # Block device
    Dir = 0o040000  # Directory
    CharDev = 0o020000  # Character device
    FIFO = 0o010000  # FIFO
