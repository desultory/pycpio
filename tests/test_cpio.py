from unittest import TestCase, main, expectedFailure

from pathlib import Path
from tempfile import TemporaryDirectory, NamedTemporaryFile
from hashlib import sha256
from uuid import uuid4

from pycpio import PyCPIO
from pycpio.header import CPIOHeader
from zenlib.logging import loggify

from cpio_test_headers import newc_test_headers, build_newc_header


@loggify
class TestCpio(TestCase):
    def setUp(self):
        self.cpio = PyCPIO(logger=self.logger, _log_init=False)
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
        self.workdir = TemporaryDirectory(prefix='pycpio-test-')
        self.test_files = []
        self.test_dirs = []

    def make_test_file(self, subdir=None, data=None):
        """ Creates a test file in the workdir """
        base_dir = self.workdir.name
        if subdir is True:
            d = TemporaryDirectory(dir=base_dir)
            self.test_dirs.append(d)
            base_dir = d.name
        elif subdir is not None and subdir in self.test_dirs:
            base_dir = subdir.name

        file = NamedTemporaryFile(dir=base_dir)
        file_data = data.encode() if data is not None else bytes(str(uuid4()), 'utf-8')
        file.file.write(file_data)
        file.file.flush()

        self.test_files.append(file)
        return file

    def make_test_files(self, count, subdir=None, data=None):
        """ Creates count test files in the workdir """
        for _ in range(count):
            self.make_test_file(subdir=subdir, data=data)

    def check_file(self, file, relative=False):
        """
        Checks that the file is in the CPIO archive.
        If relative is True, the file is checked relative to the workdir.
        Otherwise, the leading '/' is stripped from the file path.
        """
        filepath = str(Path(file).relative_to(self.workdir.name)) if relative else str(file).lstrip('/')

        if filepath not in self.cpio.entries:
            self.fail("File not found in CPIO: " + filepath)

        if self.cpio.entries[filepath].header.name != filepath:
            self.fail("Name mismatch: " + self.cpio.entries[filepath].header.name + " != " + filepath)

        if self.cpio.entries[filepath].hash != sha256(Path(file).read_bytes()).hexdigest():
            self.fail("SHA256 mismatch: " + self.cpio.entries[filepath].hash + " != " + sha256(Path(file).read_bytes()).hexdigest())

    def check_all_files(self, relative=False):
        for file in self.test_files:
            self.check_file(file.name, relative)

    def test_relative_recursive(self):
        self.make_test_files(10)
        for _ in range(5):
            self.make_test_files(2, subdir=True)
        self.cpio.append_recursive(self.workdir.name, relative=True)
        self.check_all_files(relative=True)

    def test_recursive(self):
        self.make_test_files(10)
        for _ in range(5):
            self.make_test_files(2, subdir=True)
        self.cpio.append_recursive(self.workdir.name)
        self.check_all_files()

    def test_pack(self):
        test_file = self.make_test_file()
        self.cpio.append_cpio(test_file.name)
        self.check_file(Path(test_file.name))

    def test_relative_pack(self):
        test_file = self.make_test_file()
        self.cpio.append_cpio(test_file.name, relative=self.workdir.name)
        self.check_file(Path(test_file.name), relative=True)

    def test_dedup(self):
        self.make_test_files(10, data='test')
        self.cpio.append_recursive(self.workdir.name)
        self.check_all_files()
        filename_lengths = sum([len(x) for x in self.cpio.entries])
        # Length of all headers, length of all filenames,
        # length of all data
        target_length = (110 * 11) + filename_lengths + 4 * 10
        if len(bytes(self.cpio.entries)) > target_length:
            self.fail("Deduplication failed, got " + str(len(bytes(self.cpio.entries))) + " bytes, expected no more than: " + str(target_length))

    @expectedFailure
    def test_dup(self):
        test_file = self.make_test_file()
        self.cpio.append_cpio(test_file.name)
        self.cpio.append_cpio(test_file.name)

    def test_newc_from_data(self):
        for header_data in newc_test_headers:
            header = build_newc_header(header_data)
            test_header = CPIOHeader(header)
            # Here, the build header is passed as data to the CPIOHeader constructor
            # It should populate all data as attributes within the object, equal
            # To the dictionary structure/data in the test_headers list.
            for attr, value in header_data.items():
                self.assertEqual(getattr(test_header, attr), value)

    def test_newc_from_kwargs(self):
        for header_data in newc_test_headers:
            test_header = CPIOHeader(name='.', **header_data)  # A name is required for the namesize
            # Here, the build header is passed as kwargs to the CPIOHeader constructor
            # It should populate all data as attributes within the object, equal
            # To the dictionary structure/data in the test_headers list.
            for attr, value in header_data.items():
                self.assertEqual(getattr(test_header, attr), value)


if __name__ == '__main__':
    main()
