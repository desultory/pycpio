"""
CPIO data objects
"""

from pathlib import Path

from zenlib.logging import loggify

from pycpio.masks import mode_bytes_from_path


@loggify
class CPIOData:
    """
    Generic object for CPIO data
    """
    @staticmethod
    def from_path(path: Path, header_structure, *args, **kwargs):
        """
        Create a CPIOData object from a path
        """
        from pycpio.header import CPIOHeader

        path = Path(path)
        kwargs['path'] = path
        kwargs['name'] = kwargs.pop('name', str(path))
        kwargs['mode'] = mode_bytes_from_path(path)
        kwargs['structure'] = header_structure

        header = CPIOHeader(logger=kwargs.pop('logger'), *args, **kwargs)
        return CPIOData.get_subtype(b'', header, *args, **kwargs)

    @staticmethod
    def get_subtype(data: bytes, header, *args, **kwargs):
        """
        Get the data type from the header
        """
        # Imports must be here so the module can be imported
        from .file import CPIO_File
        from .symlink import CPIO_Symlink
        from .chardev import CPIO_CharDev
        from .dir import CPIO_Dir

        mode = header.mode_type
        logger = header.logger

        args = (data, header, *args)
        kwargs = {'logger': logger, **kwargs}

        if mode is None:
            # Return the base type for the trailer
            return CPIOData(*args, **kwargs)

        match mode.name:
            case 'File':
                return CPIO_File(*args, **kwargs)
            case 'Symlink':
                return CPIO_Symlink(*args, **kwargs)
            case 'CharDev':
                return CPIO_CharDev(*args, **kwargs)
            case 'Dir':
                return CPIO_Dir(*args, **kwargs)
            case _:
                raise NotImplementedError(f"Unknown mode type: {mode.name}")

    def __init__(self, data: bytes, header, *args, **kwargs):
        self.header = header
        self.data = data

    def __str__(self):
        out_str = f"\n{self.header}"
        out_str += f"{self.__class__.__name__} "
        return out_str

    def __bytes__(self):
        """
        Convert the data to bytes
        """
        return bytes(self.header) + self.data

