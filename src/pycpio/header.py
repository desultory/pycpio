"""
CPIO header definitions and parsing.
"""

from enum import Enum


class CPIO_HEADER_NEW(Enum):
    ino = 8
    mode = 8
    uid = 8
    gid = 8
    nlink = 8
    mtime = 8
    filesize = 8
    devmajor = 8
    devminor = 8
    rdevmajor = 8
    rdevminor = 8
    namesize = 8
    check = 8


class CPIO_HEADER_OLD(Enum):
    dev = 6
    ino = 6
    mode = 6
    uid = 6
    gid = 6
    nlink = 6
    rdev = 6
    mtime = 11
    namesize = 6
    filesize = 11
    check = 6


class CPIOMagic(Enum):
    """
    Enum for CPIO magic numbers.
    """
    NEW = (b'070701', CPIO_HEADER_NEW)
    OLD = (b'070707', CPIO_HEADER_OLD)


class CPIOModes(Enum):
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

