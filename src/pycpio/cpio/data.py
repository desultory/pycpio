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
    def from_dir(path: Path, parent=None, relative=None, *args, **kwargs):
        """
        Returns a list of CPIOData objects from a directory
        """
        path = Path(path).resolve()
        if not path.is_dir():
            raise ValueError("Path is not a directory: %s" % path)

        if relative is True:
            relative = path
        elif relative:
            relative = Path(relative).resolve()

        if relative:
            kwargs['name'] = str(path.relative_to(relative))
        else:
            kwargs['name'] = str(path)

        data = []
        data.append(CPIOData.from_path(path=path, relative=relative, *args, **kwargs))
        for child in path.iterdir():
            if parent:
                child_path = parent / child
            else:
                child_path = child

            if relative:
                kwargs['name'] = str(child_path.relative_to(relative))
            else:
                kwargs['name'] = str(child_path)

            if child.is_dir():
                data.extend(CPIOData.from_dir(path=child_path, parent=parent, relative=relative, *args, **kwargs))
            else:
                data.append(CPIOData.from_path(path=child_path, relative=relative, *args, **kwargs))
        return data

    @staticmethod
    def from_path(path: Path, relative: None, *args, **kwargs):
        """
        Create a CPIOData object from a path.
        If a name is provided, it will be used instead of the resolved path.

        If recursive is True, directories will be recursed into and all files will be added to the return list.
        """
        from pycpio.header import CPIOHeader

        path = Path(path)
        if logger := kwargs.get('logger'):
            logger.debug(f"Creating CPIO entry from path: {path}")

        relative = Path(relative).resolve() if relative else None
        if logger := kwargs.get('logger'):
            logger.debug("Creating CPIO entry relative to path: %s", relative)

        if not path.is_symlink():
            path = path.resolve()
            if not path.exists():
                raise ValueError("Path does not exist: %s" % path)

        kwargs['path'] = path
        if name := kwargs.pop('name', None):
            kwargs['name'] = name
        else:
            if relative:
                kwargs['name'] = str(path.relative_to(relative))
            else:
                kwargs['name'] = str(path)

        kwargs['mode'] = mode_bytes_from_path(path)

        data = b''

        header = CPIOHeader(*args, **kwargs)
        data = CPIOData.get_subtype(data, header, *args, **kwargs)

        if logger := kwargs.get('logger'):
            logger.debug(f"Created CPIO entry from path: {data}")

        return data

    @staticmethod
    def create_entry(name: str, *args, **kwargs):
        """
        Create a CPIOData object from a path
        """
        from time import time
        from pycpio.header import CPIOHeader

        if logger := kwargs.get('logger'):
            logger.debug(f"Creating CPIO entry: {name}")

        kwargs['mtime'] = kwargs.pop('mtime', time())
        kwargs['header'] = kwargs.pop('header', CPIOHeader(name=name, *args, **kwargs))
        kwargs['data'] = kwargs.pop('data', b'')
        data = CPIOData.get_subtype(*args, **kwargs)

        if logger := kwargs.get('logger'):
            logger.info(f"Created CPIO entry: {data}")

        return data

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
        kwargs.pop('logger', None)

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

