from zenlib.logging import loggify
from pycpio.header import CPIOHeader, HEADER_NEW

from pathlib import Path
from os import fsync
from lzma import CHECK_CRC32


@loggify
class CPIOWriter:
    """
    Takes a list of CPIOData objects, gets their bytes representation, then appends a trailer before writing them to a file.
    Compresses the data if compression is specified.
    """
    def __init__(self, cpio_entries: list, output_file: Path, structure=None, compression=False, xz_crc=CHECK_CRC32, *args, **kwargs):
        self.cpio_entries = cpio_entries
        self.output_file = Path(output_file)

        self.structure = structure if structure is not None else HEADER_NEW

        if compression is True:
            self.compression = True
        elif compression is False:
            self.compression = False
        elif isinstance(compression, str):
            compression = compression.lower()
            if compression == 'true':
                compression = True
            elif compression == 'false':
                compression = False
            self.compression = compression
        self.xz_crc = xz_crc

    def __bytes__(self):
        """ Creates a bytes representation of the CPIOData objects. """
        cpio_bytes = bytes(self.cpio_entries)
        trailer = CPIOHeader(structure=self.structure, name="TRAILER!!!", logger=self.logger, _log_init=False)
        self.logger.debug("Building trailer: %s" % trailer)
        cpio_bytes += bytes(trailer)
        return cpio_bytes

    def compress(self, data):
        """ Attempts to compress the data using the specified compression type. """
        if self.compression == 'xz' or self.compression is True:
            import lzma
            self.logger.info("XZ compressing the CPIO data, original size: %.2f MiB" % (len(data) / (2 ** 20)))
            data = lzma.compress(data, check=self.xz_crc)
        elif self.compression is not False:
            raise NotImplementedError("Compression type not supported: %s" % self.compression)
        return data

    def write(self, safe_write=True):
        """ Writes the CPIOData objects to the output file. """
        self.logger.debug("Writing to: %s" % self.output_file)
        data = self.compress(bytes(self))
        with open(self.output_file, "wb") as f:
            f.write(data)
            if safe_write:
                # Flush the file to ensure all data is written, then fsync to ensure it's written to disk.
                f.flush()
                fsync(f.fileno())
            else:
                self.logger.warning("File not fsynced, data may not be written to disk: %s" % self.output_file)

        self.logger.info("Wrote %.2f MiB to: %s" % (len(data) / (2 ** 20), self.output_file))

