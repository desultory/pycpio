"""
Common functions for CPIO objects.
"""

MAX_INODES = 0xFFFFFFFF


def pad_cpio(size, align=4):
    """Pad size to align bytes."""
    return ((size + align - 1) & ~(align - 1)) - size


def get_new_inode(existing_inodes):
    """Get a new inode number."""
    if not existing_inodes:
        return 1

    if len(existing_inodes) < MAX_INODES:
        return int(max(existing_inodes), 16) + 1

    raise ValueError("No more inodes available")
