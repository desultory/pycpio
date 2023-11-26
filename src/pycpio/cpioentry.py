"""
CPIO entry definition. Starts as just the header and then takes additional data.
"""

from zenlib.logging import loggify

from .cpiodata import CPIOData
from .header import CPIOMagic, CPIOModes
from .permissions import Permissions


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
    CPIO header
    """
    def __init__(self, header_data: bytes, total_offset: int, *args, **kwargs):
        if len(header_data) != 110:
            raise ValueError("Invalid header length: %s" % len(header_data))

        self.data = header_data
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
            self.logger.debug("Checking magic: %s", magic_type.value)
            magic, structure = magic_type.value
            if magic == magic_bytes:
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
            data = self.read_bytes(length)
            self.logger.log(5, "Data: %s", data)
            self.logger.log(5, "Parsed %s: %s", key, data)

            # Convert to int
            data = int(data, 16)

            if key == 'check' and data != 0:
                raise ValueError("Invalid check: %s" % data)
            else:
                setattr(self, key, data)

    def resolve_mode(self):
        """
        Resolve the mode field.
        """
        # Nothing to process for the trailer
        if self.mode == 0:
            return

        for mode_type in CPIOModes:
            if (mode_type.value & self.mode) == mode_type.value:
                self.data_mode = mode_type
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
        if self.data_mode in ignored_modes:
            self.logger.debug("Ignoring permissions for mode: %s", self.data_mode)
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
        content_data = self.read_bytes(self.filesize, pad=True)
        self.cpio_data = CPIOData(content_data, data_mode=self.data_mode, logger=self.logger, _log_init=False)

    def __str__(self):
        """
        Returns a string representation of the object.
        """
        out_str = "Header:\n" if not hasattr(self, 'name') else f"{self.name}:\n"

        for attr in self.structure.__members__:
            if attr == 'check':
                continue
            elif attr == 'mode':
                out_str += f"    {attr}: {oct(self.mode)}\n"
            else:
                out_str += f"    {attr}: {getattr(self, attr)}\n"

        if hasattr(self, 'cpio_data'):
            out_str += f"    Data: {self.cpio_data}\n"

        if hasattr(self, 'permissions'):
            out_str += f"    Permissions: {self.permissions}\n"

        return out_str

