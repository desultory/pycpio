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
    S_IRUSR = 0o000400  # User read
    S_IWUSR = 0o000200  # User write
    S_IXUSR = 0o000100  # User execute
    S_IRGRP = 0o000040  # Group read
    S_IWGRP = 0o000020  # Group write
    S_IXGRP = 0o000010  # Group execute
    S_IROTH = 0o000004  # Other read
    S_IWOTH = 0o000002  # Other write
    S_IXOTH = 0o000001  # Other execute


def print_permissions(passed_perms: set) -> str:
    """
    Prints the permissions in a human readable format.
    """
    out = ""
    for permission in Permissions:
        # Skip the setuid, setgid, and sticky bit
        if permission.value >= 0o001000:
            continue
        # Check if the permission is in the set, if so add it to the output
        if permission in passed_perms:
            out += permission.name[3].lower()
        else:
            out += "-"

        if permission.name[3].lower() == 'x':
            out += " "

    return out.rstrip()

