"""
CPIO entry definition. Starts as just the header and then takes additional data.
"""

from zenlib.logging import loggify

from .cpiodata import CPIOData
from .header import CPIOMagic, CPIOModes
from .permissions import Permissions, print_permissions


def return_offset(func):
    """
    Decorator to return the offset to the next header.
    """
    def wrapper(self, *args, **kwargs):
        offset = self.offset
        func(self, *args, **kwargs)
        return self.offset - offset
    return wrapper


@loggify
class CPIOEntry:
    """
    CPIO entry, can be initialized from a segment of header data with the total offset, for padding.
    """
    def __init__(self, *args, **kwargs):
        header_data = kwargs.pop('header_data', None)
        total_offset = kwargs.pop('total_offset', None)
        if header_data and total_offset is not None:
            self.logger.debug("Creating CPIOEntry from header data")
            self.from_bytes(header_data, total_offset)
        else:
            raise NotImplementedError("CPIOEntry must be initialized with header data and total offset")

    def from_bytes(self, data: bytes, total_offset: int) -> None:
        if hasattr(self, 'data'):
            raise ValueError("CPIOEntry already initialized")

        if len(data) != 110:
            raise ValueError("CPIO header must be 110 bytes, got length: %s" % len(data))

        self.data = data
        self.total_offset = total_offset  # Total offset in the data
        self.offset = 0  # Current offset in the data

        # Header processing
        self.read_magic()  # Read the magic number and set the appropriate structure
        self.parse_header()  # Parse the header
        self.resolve_mode()  # Resolve the mode
        self.resolve_permissions()  # Resolve the permissions

    def read_bytes(self, length: int, pad=False) -> bytes:
        """
        Read the next length bytes from the data.
        """
        data = self.data[self.offset:self.offset + length]
        self.logger.debug("Read bytes: %s", data)
        self.offset += length
        if pad:
            self.pad_offset()
        return data

    def read_magic(self) -> None:
        """
        Read the magic number and set the appropriate structure.
        """
        magic_bytes = self.read_bytes(6)

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
            data = int(self.read_bytes(length), 16)
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

    def resolve_permissions(self):
        """
        Resolve the permissions field.
        """
        self.permissions = set()

        # Nothing to process for the trailer
        if self.mode == 0:
            return

        ignored_modes = [CPIOModes.S_IFCHR]

        # check if any of the ignored modes are i self.modes
        if self.entry_mode in ignored_modes:
            self.logger.debug("Ignoring permissions for mode: %s", self.entry_mode)
            return

        for perm_type in Permissions:
            if (perm_type.value & self.mode) == perm_type.value:
                self.permissions.add(perm_type)

        if not self.permissions:
            raise ValueError("Unable to resolve permissions: %s" % self.mode)

    @return_offset
    def get_name(self) -> int:
        """
        Get the name of the file.
        """
        name = self.read_bytes(self.namesize, pad=True).decode('ascii').strip('\0')

        if not name:
            raise ValueError("Empty name")
        self.name = name

    def pad_offset(self) -> int:
        """
        Pad the offset to the next 4-byte boundary.
        """
        current_offset = self.offset
        self.logger.debug("Calculating pad offset using total offset: %s, offset: %s", self.total_offset, current_offset)
        if pad := (current_offset + self.total_offset) % 4:
            self.logger.debug("Pad size: %d", 4 - pad)
            self.offset += 4 - pad

    def add_data(self, additional_data: bytes) -> None:
        """
        Add the file data to the object.
        """
        self.logger.debug("Adding data: %s", additional_data)
        self.data += additional_data

    @return_offset
    def read_contents(self) -> int:
        """
        Read the contents of the cpio data to content_data.

        Returns the offset to the next header.
        """
        if self.entry_mode is None:
            self.logger.debug("No data to read")
            return
        content_data = self.read_bytes(self.filesize, pad=True)
        self.cpio_data = CPIOData.from_bytes(content_data, self, _log_init=False)

    def __str__(self):
        """
        Returns a string representation of the object.
        """
        out_str = "Header:\n" if not hasattr(self, 'name') else f"{self.name}:\n"

        for attr in self.structure.__members__:
            if attr in ['mode', 'uid', 'gid', 'nlink', 'devmajor', 'devminor', 'rdevmajor', 'rdevminor', 'namesize', 'filesize', 'check']:
                continue
            elif attr == 'mode':
                out_str += f"    {attr}: {oct(self.mode)}\n"
            else:
                out_str += f"    {attr}: {getattr(self, attr)}\n"

        if hasattr(self, 'cpio_data'):
            out_str += f"    Data: {self.cpio_data}\n"

        out_str += f"    Owner, Group: {self.uid} {self.gid}\n"
        out_str += f"    Permissions: {print_permissions(self.permissions)}\n"

        return out_str

