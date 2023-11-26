"""
CPIO header permissions
"""

from enum import Enum


class Permissions(Enum):
    """
    Enum for CPIO file permissions.
    """
    S_ISUID = 0o004000  # Set UID bit
    S_ISGID = 0o002000  # Set GID
    S_ISVTX = 0o001000  # Sticky bit
    S_IRWXU = 0o000700  # User permissions
    S_IRUSR = 0o000400  # User read
    S_IWUSR = 0o000200  # User write
    S_IXUSR = 0o000100  # User execute
    S_IRWXG = 0o000070  # Group permissions
    S_IRGRP = 0o000040  # Group read
    S_IWGRP = 0o000020  # Group write
    S_IXGRP = 0o000010  # Group execute
    S_IRWXO = 0o000007  # Other permissions
    S_IROTH = 0o000004  # Other read
    S_IWOTH = 0o000002  # Other write
    S_IXOTH = 0o000001  # Other execute
