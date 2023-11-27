"""
CPIO header definitions and parsing.
"""

from enum import Enum


class HEADER_NEW(Enum):
    magic = 6
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


class Magic(Enum):
    """
    Enum for CPIO magic numbers.
    """
    NEW = (b'070701', HEADER_NEW)
