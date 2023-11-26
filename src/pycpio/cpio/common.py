"""
Common functions for CPIO objects.
"""


def pad_cpio(size, align=4):
    """Pad size to align bytes."""
    return ((size + align - 1) & ~(align - 1)) - size
