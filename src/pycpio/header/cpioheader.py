from pycpio.masks import print_permissions, resolve_mode_bytes, resolve_permissions
from zenlib.logging import loggify


@loggify
class CPIOHeader:
    """CPIO HEADER, can be initialized from a segment of header data with or without a structure definition."""

    def __init__(self, header_data=b"", overrides={}, *args, **kwargs):
        self.overrides = overrides
        if header_data:
            self.logger.debug("Creating CPIOEntry from header data: %s", header_data)
            self.from_bytes(header_data)
        elif kwargs.get("name"):
            self.logger.debug("Creating CPIO Header with name: %s", kwargs["name"])
            self.from_args(*args, **kwargs)
        else:
            raise NotImplementedError("CPIOEntry must be initialized with header data or a name")

        self.process_overrides()
        # Set nlink to 1, additions are made in the CPIOArchive class
        self.nlink = b"00000001"

    def from_args(self, *args, **kwargs) -> None:
        """Initialize the object from the arguments."""
        from .header_funcs import get_magic_from_header
        from .headers import HEADER_NEW

        self.structure = kwargs.pop("structure", HEADER_NEW)
        self.name = kwargs.pop("name")

        for name, length in self.structure.items():
            if name in ["magic", "namesize"]:
                continue
            elif name != "mode" and name in self.overrides:
                continue  # they are processed later
            value = kwargs.pop(name, length * b"0")
            setattr(self, name, value)

        self.magic = get_magic_from_header(self.structure)

    def from_bytes(self, data: bytes) -> None:
        if hasattr(self, "data"):
            raise ValueError("CPIOEntry already initialized")

        if len(data) != 110:
            raise ValueError("CPIO header must be 110 bytes, got length: %s" % len(data))

        self.data = data
        self.offset = 0  # Current offset in the data

        # Header processing
        self.parse_header()  # Parse the header

    def __setattr__(self, key, value):
        """
        For uid/gid definitions, try to resolve the user/group.

        If the key is in the structure, set the value to the bytes representation
        if it is not already bytes.

        If the filesize changes, log a warning.

        Check the mode and set the mode_type and permissions attributes accordingly.
        Check that the inode is < 0xFFFFFFFF, if not, set to 0 and log a warning.
            When used in an archive, the inode will be set to a unique value.
        If setting the name, add a null byte to the end and set the namesize attribute.
        """
        if key in ["uid", "gid"] and not isinstance(value, bytes):
            try:
                value = int(value)
            except ValueError:
                from grp import getgrnam
                from pwd import getpwnam

                if key == "uid":
                    value = getpwnam(value).pw_uid
                elif key == "gid":
                    value = getgrnam(value).gr_gid
                self.logger.debug("Resolved %s: %s" % (key, repr(value)))

        if hasattr(self, "structure") and key in self.structure and not isinstance(value, bytes):
            length = self.structure[key]
            self.logger.debug("Converting %s to bytes: %s" % (key, repr(value)))
            if isinstance(value, str):
                value = format(int(value, 16), f"0{length}x")
            elif isinstance(value, float):
                value = format(int(value), f"0{length}x")
            elif isinstance(value, int):
                value = format(value, f"0{length}x")
            else:
                raise ValueError("Unable to convert %s to bytes: %s" % (key, value))
            value = value.encode("ascii")
            self.logger.debug("[%s] %d bytes: %s" % (key, length, value))

        if key == "filesize" and value != b"00000000":
            if getattr(self, "filesize", b"00000000").lower() not in [value, b"00000000"]:
                self.logger.warning("[%s] Changed filesize: %s -> %s" % (self.name, self.filesize, value))
        elif key == "filesize" and value == b"00000000":
            if getattr(self, "filesize", b"00000000") != b"00000000":
                self.logger.warning("[%s] Setting filesize to 0" % self.name)
        elif key == "ino":
            if int(value, 16) > 0xFFFFFFFF:
                self.logger.warning("Inode too large, setting to 0: %s" % value)
                value = b"00000000"

        super().__setattr__(key, value)

        if key == "mode":
            try:
                self.mode_type = resolve_mode_bytes(self.mode)
            except ValueError:
                raise ValueError("Invalid mode: %s", self.mode)
            self.permissions = resolve_permissions(self.mode)

        if key == "name":
            if isinstance(value, bytes):
                self.logger.debug("Name is bytes, converting to string")
                value = value.decode("ascii")

            super().__setattr__(key, value)

            # Add space for the null byte
            namesize = len(value) + 1
            if hasattr(self, "namesize") and namesize != int(self.namesize, 16):
                self.logger.debug("Name size changed: %s -> %s" % (int(self.namesize, 16), namesize))
            self.namesize = namesize

    def process_overrides(self) -> None:
        """Process the overrides dictionary and set the attributes on the object."""
        for attribute in self.structure:
            if attribute in self.overrides:
                if hasattr(self, attribute):
                    self.logger.log(5, "[%s] Pre-override: %s" % (attribute, getattr(self, attribute)))
                if attribute == "mode":
                    # Mask the mode, then add the override
                    value = (int(self.mode, 16) & 0o7777000) | (self.overrides[attribute] & 0o777)
                else:
                    value = self.overrides[attribute]
                self.logger.debug("[%s] Setting override: %s" % (attribute, value))
                setattr(self, attribute, value)

    def _read_bytes(self, num_bytes: int) -> bytes:
        """Read the specified number of bytes from the data, incrementing the offset, then returning the data."""
        data = self.data[self.offset : self.offset + num_bytes]
        self.logger.log(5, "Read %d bytes: %s" % (num_bytes, data))
        self.offset += num_bytes
        return data

    def add_data(self, data: bytes) -> None:
        """Add the file data to the object."""
        self.logger.debug("Adding data: %s" % data)
        self.data += data

    def parse_header(self):
        """
        Parse the data according to the structure.
        Sets attributes on the object.
        """
        from .header_funcs import get_header_from_magic

        self.structure = get_header_from_magic(self.data[:6])
        for key, length in self.structure.items():
            # Read the data, convert to int
            data = self._read_bytes(length)

            if key == "check" and data != b"0" * 8:
                raise ValueError("Invalid check: %s" % data)
            elif key in self.overrides:
                self.logger.debug("Delaying overridden parameter processing: %s" % key)
            else:
                setattr(self, key, data)
                self.logger.debug("Parsed %s: %s", key, data)

    def get_name(self):
        """Get the name of the file."""
        name = self._read_bytes(int(self.namesize, 16)).decode("ascii").rstrip("\0")

        if not name:
            raise ValueError("Empty name")
        self.name = name

    def __bytes__(self):
        """Returns the bytes representation of the object."""
        from pycpio.cpio import pad_cpio

        out_bytes = b""
        # Get the bytes for each attribute
        for attr, value in self.structure.items():
            out_bytes += getattr(self, attr)
        # Output the name as bytes, with a null byte
        out_bytes += self.name.encode("ascii") + b"\0"
        # Calculate padding based on total length
        out_bytes += b"\0" * pad_cpio(len(out_bytes))

        return out_bytes

    def __str__(self):
        """Returns a string representation of the object."""
        from datetime import datetime

        out_str = f"[{int(self.ino, 16)}] "
        out_str += "Header:\n" if not hasattr(self, "name") else f"{self.name}:\n"

        for attr in self.structure:
            if attr in [
                "ino",
                "mode",
                "devmajor",
                "devminor",
                "uid",
                "gid",
                "rdevmajor",
                "rdevminor",
                "namesize",
                "filesize",
                "check",
            ]:
                continue
            elif attr == "nlink":
                if int(self.nlink, 16) > 1:
                    out_str += f"    {attr}: {int(self.nlink, 16)}\n"
            elif attr == "magic":
                if self.logger.level < 20:
                    out_str += f"    {attr}: {self.magic}\n"
                else:
                    continue
            elif attr == "mtime":
                if self.logger.level < 20:
                    out_str += f"    {attr}: {datetime.fromtimestamp(int(self.mtime, 16))}\n"
                else:
                    continue
            else:
                out_str += f"    {attr}: {int(getattr(self, attr), 16)}"

        out_str += f"    Permissions: {print_permissions(self.permissions)} {int(self.uid, 16)} {int(self.gid, 16)}"
        return out_str
