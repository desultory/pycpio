"""
CPIO header definitions and parsing.
"""

from .headers import HEADER_NEW

lookup_table = {b'070701': HEADER_NEW}


def get_header_from_magic(magic: bytes) -> dict:
    """
    Return the header format for the given magic number.
    """
    for magic, header_type in lookup_table.items():
        if magic == magic:
            return header_type
    raise ValueError("Unknown magic number: %s" % magic)


def get_magic_from_header(header: dict) -> dict:
    """
    Return the magic number for the given header format.
    """
    for magic, header_type in lookup_table.items():
        if header_type == header:
            return magic
    raise ValueError("Unknown header type: %s" % header)
