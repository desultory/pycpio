"""
CPIO entry definition. Starts as just the header and then takes additional data.
"""

from zenlib.logging import loggify

from pycpio.magic import CPIOMagic
from pycpio.modes import CPIOModes
from pycpio.permissions import Permissions, print_permissions


@loggify
class CPIOHeader:
    """
    CPIO entry, can be initialized from a segment of header data with the total offset, for padding.
    """
    def __init__(self, *args, **kwargs):
        header_data = kwargs.pop('header_data', None)
        if header_data:
            self.logger.debug("Creating CPIOEntry from header data")
            self.from_bytes(header_data)
        else:
            raise NotImplementedError("CPIOEntry must be initialized with header data")

    def _read_bytes(self, num_bytes: int) -> bytes:
        """
        Read the specified number of bytes from the data.
        Increments the offset.
        """
        data = self.data[self.offset:self.offset + num_bytes]
        self.logger.debug("Read %s bytes: %s", num_bytes, data)
        self.offset += num_bytes
        return data

    def add_data(self, additional_data: bytes) -> None:
        """
        Add the file data to the object.
        """
        self.logger.debug("Adding data: %s", additional_data)
        self.data += additional_data

    def from_bytes(self, data: bytes) -> None:
        if hasattr(self, 'data'):
            raise ValueError("CPIOEntry already initialized")

        if len(data) != 110:
            raise ValueError("CPIO header must be 110 bytes, got length: %s" % len(data))

        self.data = data
        self.offset = 0  # Current offset in the data

        # Header processing
        self.read_magic()  # Read the magic number and set the appropriate structure
        self.parse_header()  # Parse the header
        self.resolve_mode()  # Resolve the mode
        self.resolve_permissions()  # Resolve the permissions

    def read_magic(self) -> None:
        """
        Read the magic number and set the appropriate structure.
        """
        magic_bytes = self._read_bytes(6)

        for magic_type in CPIOMagic:
            magic, structure = magic_type.value
            if magic == magic_bytes:
                self.logger.debug("Using structure: %s", structure)
                self.structure = structure
                break
        else:
            raise ValueError("Invalid magic: %s" % magic_bytes)

    def parse_header(self):
        """
        Parse the data according to the structure.
        Sets attributes on the object.
        """
        for key, length_val in self.structure.__members__.items():
            length = length_val.value
            self.logger.log(5, "Offset: %s, Length: %s", self.offset, length)

            # Read the data, convert to int
            data = int(self._read_bytes(length), 16)
            self.logger.log(5, "Data: %s", data)

            if key == 'check' and data != 0:
                raise ValueError("Invalid check: %s" % data)
            else:
                setattr(self, key, data)
                self.logger.debug("Parsed %s: %s", key, data)

    def resolve_mode(self):
        """
        Resolve the mode field.
        """
        # Nothing to process for the trailer
        if self.mode == 0:
            self.entry_mode = None
            return

        for mode_type in CPIOModes:
            if (mode_type.value & self.mode) == mode_type.value:
                self.entry_mode = mode_type
                break
        else:
            raise ValueError("Unable to resolve mode: %s" % self.mode)

        if not self.filesize and self.entry_mode not in [CPIOModes.Dir, CPIOModes.Symlink, CPIOModes.CharDev]:
            raise ValueError("Mode cannot hav filesize of 0: %s" % self.entry_mode)

    def resolve_permissions(self):
        """
        Resolve the permissions field.
        """
        self.permissions = set()

        # Nothing to process for the trailer
        if self.mode == 0:
            return

        ignored_modes = [CPIOModes.CharDev]
        # check if any of the ignored modes are i self.modes
        if self.entry_mode in ignored_modes:
            self.logger.debug("Ignoring permissions for mode: %s", self.entry_mode)
            return

        for perm_type in Permissions:
            if (perm_type.value & self.mode) == perm_type.value:
                self.permissions.add(perm_type)

        if not self.permissions:
            raise ValueError("Unable to resolve permissions: %s" % self.mode)

    def get_name(self) -> int:
        """
        Get the name of the file.
        """
        name = self._read_bytes(self.namesize).decode('ascii').strip('\0')

        if not name:
            raise ValueError("Empty name")
        self.name = name

    def __str__(self):
        """
        Returns a string representation of the object.
        """
        from datetime import datetime

        out_str = f"[{self.ino}] "
        out_str += "Header:\n" if not hasattr(self, 'name') else f"{self.name}:\n"

        for attr in self.structure.__members__:
            if attr in ['ino', 'mode', 'uid', 'gid', 'nlink', 'devmajor', 'devminor',
                        'rdevmajor', 'rdevminor', 'namesize', 'filesize', 'check']:
                continue
            elif attr == 'mtime':
                out_str += f"    {attr}: {datetime.fromtimestamp(self.mtime)}\n"
            elif attr == 'mode':
                out_str += f"    {attr}: {oct(self.mode)}\n"
            else:
                out_str += f"    {attr}: {getattr(self, attr)}\n"

        out_str += f"    Owner, Group: {self.uid} {self.gid}\n"
        out_str += f"    Permissions: {print_permissions(self.permissions)}\n"

        return out_str

