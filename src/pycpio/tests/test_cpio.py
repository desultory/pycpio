from unittest import TestCase, main

from pathlib import Path
from hashlib import sha256
from uuid import uuid4

from pycpio import PyCPIO
from zenlib.logging import loggify


@loggify
class TestCpio(TestCase):
    def setUp(self):
        self.cpio = PyCPIO(logger=self.logger, _log_init=False)
        self.make_workdir()

    def tearDown(self):
        for file in self.test_files:
            self.logger.debug("Removing test file: " + str(file))
            file.unlink()
        self.logger.debug("Removing workdir: " + str(self.workdir))
        self.workdir.rmdir()
        del self.cpio

    def make_workdir(self):
        """
        Create a temporary directory for testing.
        Uses a UUID under /tmp/pycpio-test-<uuid>
        sets self.workdir to the Path object of the directory
        initializes self.test_files as an empty list
        """
        from os import mkdir
        workdir = Path('/tmp/pycpio-test-' + str(uuid4()))
        if not workdir.exists():
            mkdir(workdir)

        self.workdir = workdir
        self.test_files = []

    def make_test_file(self):
        """ Creates a test file in the workdir """
        file = self.workdir / str(uuid4())
        with open(file, 'w') as f:
            f.write("This is a test file\n")
        self.test_files.append(file)
        return file

    def make_test_files(self, count):
        """ Creates count test files in the workdir """
        for _ in range(count):
            self.make_test_file()

    def check_file(self, file, relative=False):
        """
        Checks that the file is in the CPIO archive.
        If relative is True, the file is checked relative to the workdir.
        Otherwise, the leading '/' is stripped from the file path.
        """
        filepath = str(file.relative_to(self.workdir)) if relative else str(file).lstrip('/')

        if filepath not in self.cpio.entries:
            self.fail("File not found in CPIO: " + filepath)

        if self.cpio.entries[filepath].header.name != filepath:
            self.fail("Name mismatch: " + self.cpio.entries[filepath].header.name + " != " + filepath)

        if self.cpio.entries[filepath].hash != sha256(file.read_bytes()).hexdigest():
            self.fail("SHA256 mismatch: " + self.cpio.entries[filepath].hash + " != " + sha256(file.read_bytes()).hexdigest())

    def check_all_files(self, relative=False):
        for file in self.test_files:
            self.check_file(file, relative)

    def test_relative_recursive(self):
        self.make_test_files(10)
        self.cpio.append_recursive(self.workdir, relative=True)
        self.check_all_files(relative=True)

    def test_recursive(self):
        self.make_test_files(10)
        self.cpio.append_recursive(self.workdir)
        self.check_all_files()

    def test_pack(self):
        test_file = self.make_test_file()
        self.cpio.append_cpio(test_file)
        self.check_file(test_file)

    def test_relative_pack(self):
        test_file = self.make_test_file()
        self.cpio.append_cpio(test_file, relative=self.workdir)
        self.check_file(test_file, relative=True)


if __name__ == '__main__':
    main()
