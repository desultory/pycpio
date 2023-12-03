"""
CPIO header mode masks.
"""

from enum import Enum
from pathlib import Path


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


def resolve_mode_bytes(mode: bytes) -> CPIOModes:
    """
    Resolve the mode mask from the given bytes.
    """
    mode_int = int(mode.decode('ascii'), 16)
    # Handle the trailer
    if not mode_int:
        return None

    for mode in CPIOModes:
        if mode.value & mode_int == mode.value:
            return mode

    raise ValueError(f"Invalid mode: {mode}")


def mode_bytes_from_path(file_path: Path) -> CPIOModes:
    """
    Gets the mode type bytes from the given path.
    """
    if file_path.is_dir():
        return CPIOModes.Dir.value
    elif file_path.is_symlink():
        return CPIOModes.Symlink.value
    elif file_path.is_block_device():
        return CPIOModes.BlkDev.value
    elif file_path.is_char_device():
        return CPIOModes.CharDev.value
    elif file_path.is_fifo():
        return CPIOModes.FIFO.value
    elif file_path.is_file():
        return CPIOModes.File.value

    raise ValueError(f"Invalid mode: {file_path}")










