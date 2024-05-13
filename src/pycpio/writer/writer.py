
from zenlib.logging import loggify
from pycpio.header import CPIOHeader, HEADER_NEW

from pathlib import Path
from os import fsync


@loggify
class CPIOWriter:
    """
    Takes a list of CPIOData objects, gets their bytes representation, then appends a trailer before writing them to a file.
    Compresses the data if compression is specified.
    """
    def __init__(self, cpio_entries: list, output_file: Path, compression=None, structure=None, *args, **kwargs):
        self.cpio_entries = cpio_entries
        self.output_file = Path(output_file)

        self.structure = structure if structure is not None else HEADER_NEW
        self.compression = compression

    def __bytes__(self):
        """ Creates a bytes representation of the CPIOData objects. """
        cpio_bytes = bytes(self.cpio_entries)
        trailer = CPIOHeader(structure=self.structure, name="TRAILER!!!", logger=self.logger, _log_init=False)
        self.logger.debug("Building trailer: %s" % trailer)
        cpio_bytes += bytes(trailer)
        return cpio_bytes

    def compress(self, data):
        """ Attempts to compress the data using the specified compression type. """
        if self.compression == 'xz':
            import lzma
            self.logger.info("Compressing data with xz, original size: %d" % len(data))
            data = lzma.compress(data)
        elif self.compression is not None:
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

        self.logger.info("Wrote %d bytes to: %s" % (len(data), self.output_file))

