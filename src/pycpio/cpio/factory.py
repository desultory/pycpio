"""
CPIO entry factory.
"""

from pycpio.header import CPIOHeader
from .data import CPIOData


def create_entry(name: str, structure: dict, *args, **kwargs) -> CPIOData:
    """
    Creates a CPIO entry using the passed data
    """
    from time import time
    kwargs['mtime'] = kwargs.get('mtime', int(time()))
    header = get_header(name, structure, *args, **kwargs)
    data = get_data(header, *args, **kwargs)
    return data


def get_data(header: CPIOHeader, *args, **kwargs) -> CPIOData:
    """
    Get CPIO data using the passed header
    """
    data = kwargs.pop("data", b'')
    match header.mode_type.name:
        case "File":
            raise ValueError("File type not supported, use the CPIOReader")
        case "Dir":
            from .dir import CPIO_Dir
            return CPIO_Dir(data=data, header=header, *args, **kwargs)
        case "Symlink":
            from .symlink import CPIO_Symlink
            return CPIO_Symlink(data=data, header=header, *args, **kwargs)
        case "CharDev":
            from .chardev import CPIO_CharDev
            return CPIO_CharDev(data=data, header=header, *args, **kwargs)

    raise NotImplementedError("Unknown CPIO type: %s" % header.mode_type.name)


def get_header(name: str, structure: dict, *args, **kwargs) -> CPIOHeader:
    """
    Creates a CPIO header using the passed data
    """
    return CPIOHeader(structure=structure, name=name, *args, **kwargs)



