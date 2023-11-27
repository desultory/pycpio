"""
CPIO entry definition. Starts as just the header and then takes additional data.
"""


from zenlib.logging import loggify

from pycpio.masks import resolve_mode_bytes, print_permissions, resolve_permissions
from .header_funcs import get_header_from_magic, get_magic_from_header
from .headers import HEADER_NEW
from pycpio.cpio import pad_cpio


@loggify
class CPIOHeader:
    """
    CPIO entry, can be initialized from a segment of header data with or without a structure definition.
    from_path can be used to create a new CPIO header from a path on the host system.
    """
    def __init__(self, *args, **kwargs):
        header_data = kwargs.pop('header_data', None)
        if header_data:
            self.logger.debug("Creating CPIOEntry from header data: %s", header_data)
            self.from_bytes(header_data)
        elif kwargs.get('name'):
            self.logger.info("Creating CPIO entry from name: %s", kwargs['name'])
            self.from_args(*args, **kwargs)
        else:
            raise NotImplementedError("CPIOEntry must be initialized with header data")

    def __setattr__(self, key, value):
        """
        If the key is in the structure, set the value to the bytes representation.
        """
        if hasattr(self, 'structure') and key in self.structure.__members__ and not isinstance(value, bytes):
            length = self.structure.__members__[key].value
            self.logger.debug("Converting %s to bytes: %s" % (key, value))
            if isinstance(value, str):
                value = format(int(value, 16), f'0{length}x')
            elif isinstance(value, float):
                value = format(int(value), f'0{length}x')
            elif isinstance(value, int):
                value = format(value, f'0{length}x')
            else:
                raise ValueError("Unable to convert %s to bytes: %s" % (key, value))
            value = value.encode('ascii')
            self.logger.debug("[%s] %d bytes: %s" % (key, length, value))

        super().__setattr__(key, value)

        if key == 'mode':
            self.mode_type = resolve_mode_bytes(self.mode)
            self.permissions = resolve_permissions(self.mode)

        if key == 'name':
            self.namesize = len(value) + 1

    def _read_bytes(self, num_bytes: int) -> bytes:
        """
        Read the specified number of bytes from the data.
        Increments the offset.
        """
        data = self.data[self.offset:self.offset + num_bytes]
        self.logger.log(5, "Read %s bytes: %s", num_bytes, data)
        self.offset += num_bytes
        return data

    def add_data(self, additional_data: bytes) -> None:
        """
        Add the file data to the object.
        """
        self.logger.debug("Adding data: %s", additional_data)
        self.data += additional_data

    def from_args(self, *args, **kwargs) -> None:
        """
        Initialize the object from the arguments.
        """
        self.name = kwargs.pop('name')

        self.structure = kwargs.pop('structure', HEADER_NEW)

        for name, parameter in self.structure.__members__.items():
            if name in ['magic', 'namesize']:
                continue
            value = kwargs.pop(name, parameter.value * b'0')
            setattr(self, name, value)

        self.magic = get_magic_from_header(self.structure)

    def from_bytes(self, data: bytes) -> None:
        if hasattr(self, 'data'):
            raise ValueError("CPIOEntry already initialized")

        if len(data) != 110:
            raise ValueError("CPIO header must be 110 bytes, got length: %s" % len(data))

        self.data = data
        self.offset = 0  # Current offset in the data

        # Header processing
        self.parse_header()  # Parse the header

    def parse_header(self):
        """
        Parse the data according to the structure.
        Sets attributes on the object.
        """
        self.structure = get_header_from_magic(self.data[:6])
        for key, length_val in self.structure.__members__.items():
            length = length_val.value
            self.logger.log(5, "Offset: %s, Length: %s", self.offset, length)

            # Read the data, convert to int
            data = self._read_bytes(length)

            if key == 'check' and data != b'0' * 8:
                raise ValueError("Invalid check: %s" % data)
            else:
                setattr(self, key, data)
                self.logger.debug("Parsed %s: %s", key, data)

    def get_name(self):
        """
        Get the name of the file.
        """
        name = self._read_bytes(int(self.namesize, 16)).decode('ascii').strip('\0')

        if not name:
            raise ValueError("Empty name")
        self.name = name

    def __bytes__(self):
        """
        Returns the bytes representation of the object.
        """
        out_bytes = b''
        # Get the bytes for each attribute
        for attr, value in self.structure.__members__.items():
            out_bytes += getattr(self, attr)
        # Output the name as bytes
        out_bytes += self.name.encode('ascii')
        # Calculate padding based on total length, and add the null terminator
        padding = pad_cpio(len(out_bytes) + 1)
        out_bytes += b'\0' * padding + b'\0'

        return out_bytes

    def __str__(self):
        """
        Returns a string representation of the object.
        """
        from datetime import datetime

        out_str = f"[{int(self.ino, 16)}] "
        out_str += "Header:\n" if not hasattr(self, 'name') else f"{self.name}:\n"

        for attr in self.structure.__members__:
            if attr in ['ino', 'mode', 'nlink', 'devmajor', 'devminor',
                        'rdevmajor', 'rdevminor', 'namesize', 'filesize', 'check']:
                continue
            elif attr == 'magic':
                out_str += f"    {attr}: {self.magic}\n"
            elif attr == 'mtime':
                out_str += f"    {attr}: {datetime.fromtimestamp(int(self.mtime, 16))}\n"
            else:
                out_str += f"    {attr}: {int(getattr(self, attr), 16)}\n"

        out_str += f"    Permissions: {print_permissions(self.permissions)}\n"

        return out_str

