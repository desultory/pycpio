"""
CPIO entry definition. Starts as just the header and then takes additional data.
"""

from zenlib.logging import loggify

from pycpio.modes import CPIOModes
from pycpio.permissions import Permissions, print_permissions
from pycpio.magic import CPIOMagic
from .common import pad_cpio


@loggify
class CPIOHeader:
    """
    CPIO entry, can be initialized from a segment of header data with or without a structure definition.
    from_path can be used to create a new CPIO header from a path on the host system.
    """
    _ignore_mode_permissions = [CPIOModes.CharDev]

    def __init__(self, header_structure, *args, **kwargs):
        self.structure = header_structure
        self.permissions = set()

        header_data = kwargs.pop('header_data', None)
        if header_data:
            self.logger.debug("Creating CPIOEntry from header data: %s", header_data)
            self.from_bytes(header_data)
        elif kwargs.get('name'):
            self.logger.info("Creating CPIO entry from name: %s", kwargs['name'])
            self.from_args(*args, **kwargs)
        else:
            raise NotImplementedError("CPIOEntry must be initialized with header data")

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

        for name, parameter in self.structure.__members__.items():
            if name in ['magic', 'namesize']:
                continue
            value = kwargs.pop(name, parameter.value * b'0')
            if not isinstance(value, bytes):
                self.logger.debug("Converting %s to bytes: %s" % (name, value))
                value = format(int(value), '08x').encode('ascii')
            setattr(self, name, value)

        self.magic, _ = CPIOMagic[self.structure.__name__.split('_')[1]].value
        self.namesize = format(len(self.name) + 1, '08x').encode('ascii')
        self.resolve_mode()
        self.resolve_permissions()

    def from_bytes(self, data: bytes) -> None:
        if hasattr(self, 'data'):
            raise ValueError("CPIOEntry already initialized")

        if len(data) != 110:
            raise ValueError("CPIO header must be 110 bytes, got length: %s" % len(data))

        self.data = data
        self.offset = 0  # Current offset in the data

        # Header processing
        self.parse_header()  # Parse the header
        # Don't process modes/permissions for the trailer
        if self.mode == b'0' * 8:
            self.entry_mode = None
        else:
            self.resolve_mode()
            self.resolve_permissions()

    def parse_header(self):
        """
        Parse the data according to the structure.
        Sets attributes on the object.
        """
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

    def resolve_mode(self):
        """
        Resolve the mode field.
        """
        if self.mode == b'0' * 8:
            self.entry_mode = None
            return

        for mode_type in CPIOModes:
            if (mode_type.value & int(self.mode, 16)) == mode_type.value:
                self.entry_mode = mode_type
                break
        else:
            raise ValueError("Unable to resolve mode: %s" % self.mode)

        if not self.filesize and self.entry_mode not in [CPIOModes.Dir, CPIOModes.Symlink, CPIOModes.CharDev]:
            raise ValueError("Mode cannot have filesize of 0: %s" % self.entry_mode)

    def resolve_permissions(self):
        """
        Resolve the permissions field.
        """
        # check if any of the ignored modes are i self.modes
        if self.entry_mode in self._ignore_mode_permissions:
            self.logger.debug("Ignoring permissions for mode: %s", self.entry_mode)
            return

        for perm_type in Permissions:
            if (perm_type.value & int(self.mode, 16)) == perm_type.value:
                self.permissions.add(perm_type)

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
            if attr in ['ino', 'mode', 'uid', 'gid', 'nlink', 'devmajor', 'devminor',
                        'rdevmajor', 'rdevminor', 'namesize', 'filesize', 'check']:
                continue
            elif attr == 'mtime':
                out_str += f"    {attr}: {datetime.fromtimestamp(int(self.mtime, 16))}\n"
            else:
                out_str += f"    {attr}: {getattr(self, attr)}\n"

        out_str += f"    Owner, Group: {self.uid} {self.gid}\n"
        out_str += f"    Permissions: {print_permissions(self.permissions)}\n"

        return out_str

