"""
CPIO header permissions
"""

from enum import Enum


class Permissions(Enum):
    """
    Enum for CPIO file permissions.
    """
    SUID = 0o004000  # Set UID bit
    SGID = 0o002000  # Set GID
    SVTX = 0o001000  # Sticky bit
    RUSR = 0o000400  # User read
    WUSR = 0o000200  # User write
    XUSR = 0o000100  # User execute
    RGRP = 0o000040  # Group read
    WGRP = 0o000020  # Group write
    XGRP = 0o000010  # Group execute
    ROTH = 0o000004  # Other read
    WOTH = 0o000002  # Other write
    XOTH = 0o000001  # Other execute


def resolve_permissions(mode: bytes) -> set:
    """
    Resolves the permissions from the mode bytes.
    """
    perms = set()
    for perm in Permissions:
        if int(mode, 16) & perm.value == perm.value:
            perms.add(perm)
    return perms


def print_permissions(passed_perms: set, extended=False) -> str:
    """
    Prints the permissions in a human readable format.
    """
    out = ""
    for permission in Permissions:
        # Skip the setuid, setgid, and sticky bit
        if permission.value >= 0o001000:
            if extended:
                out += f"{permission.name.upper()}-"
            else:
                continue
        # Check if the permission is in the set, if so add it to the output
        if permission in passed_perms:
            out += permission.name[0].lower()
        else:
            out += "-"

        if permission.name[0].lower() == 'x':
            out += " "

    return out.rstrip()

