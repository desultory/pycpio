from tempfile import NamedTemporaryFile, TemporaryDirectory
from unittest import TestCase, main
from uuid import uuid4

from pycpio import PyCPIO
from pycpio.errors import UnavailableCompression
from zenlib.logging import loggify


@loggify
class TestCpio(TestCase):
    def setUp(self):
        self.cpio = PyCPIO(logger=self.logger)
        self.make_workdir()

    def tearDown(self):
        for file in self.test_files:
            file.close()
        for directory in self.test_dirs:
            directory.cleanup()
        self.workdir.cleanup()
        del self.cpio

    def make_workdir(self):
        """
        Create a temporary directory for testing.
        sets self.workdir to the Path object of the directory
        initializes self.test_files as an empty list
        """
        self.workdir = TemporaryDirectory(prefix="pycpio-test-")
        self.test_files = []
        self.test_dirs = []

    def make_test_file(self, subdir=None, data=None):
        """Creates a test file in the workdir"""
        base_dir = self.workdir.name
        if subdir is True:
            d = TemporaryDirectory(dir=base_dir)
            self.test_dirs.append(d)
            base_dir = d.name
        elif subdir is not None and subdir in self.test_dirs:
            base_dir = subdir.name

        file = NamedTemporaryFile(dir=base_dir)
        file_data = data.encode() if data is not None else bytes(str(uuid4()), "utf-8")
        file.file.write(file_data)
        file.file.flush()

        self.test_files.append(file)
        return file

    def make_test_files(self, count, subdir=None, data=None):
        """Creates count test files in the workdir"""
        for _ in range(count):
            self.make_test_file(subdir=subdir, data=data)

    def test_write_no_compress(self):
        self.make_test_files(100)
        self.cpio.append_recursive(self.workdir.name)
        out_file = NamedTemporaryFile()  # Out file for the cpio
        self.cpio.write_cpio_file(out_file.file.name)
        out_file.file.flush()

    def test_write_xz_compress(self):
        self.make_test_files(100)
        self.cpio.append_recursive(self.workdir.name)
        out_file = NamedTemporaryFile()
        self.cpio.write_cpio_file(out_file.file.name, compression="xz")
        out_file.file.flush()

    def test_write_zstd_compress(self):
        self.make_test_files(100)
        self.cpio.append_recursive(self.workdir.name)
        out_file = NamedTemporaryFile()
        try:
            self.cpio.write_cpio_file(out_file.file.name, compression="zstd")
        except UnavailableCompression as e:
            self.skipTest(f"Zstandard compression is not available in this environment: {e}")
        out_file.file.flush()


if __name__ == "__main__":
    main()
