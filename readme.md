 ![Tests](https://github.com/desultory/pycpio/actions/workflows/unit_tests.yml/badge.svg)

# PyCPIO

A library for creating CPIO files in Python.

Currently, the library only supports the New ASCII format, and xz compression

This library is primary designed for use in [ugrd](https://github.com/desultory/ugrd) to create CPIO archives for use in initramfs.

## Usage

```
  -h, --help            show this help message and exit
  -d, --debug           enable debug mode (level 10)
  -dd, --trace          enable trace debug mode (level 5)
  -v, --version         print the version and exit
  --log-file LOG_FILE   set the path to the log file
  --log-level LOG_LEVEL
                        set the log level
  --log-time            enable log timestamps
  --no-log-color        disable log color
  -i INPUT, --input INPUT
                        input file
  -a APPEND, --append APPEND
                        append to archive
  --recursive RECURSIVE
                        append to archive recursively
  --relative RELATIVE   append to archive relative to this path
  --absolute            allow absolute paths
  --reproducible        Set mtime to 0, start inodes at 0
  --rm RM, --delete RM  delete from archive
  -n NAME, --name NAME  Name/path override for append
  -s SYMLINK, --symlink SYMLINK
                        create symlink
  -c CHARDEV, --chardev CHARDEV
                        create character device
  --major MAJOR         major number for character/block device
  --minor MINOR         minor number for character/block device
  -u UID, --set-owner UID
                        set UID on all files
  -g GID, --set-group GID
                        set GID on all files
  -m MODE, --set-mode MODE
                        set mode on all files
  -z COMPRESS, --compress COMPRESS
                        compression type
  -o OUTPUT, --output OUTPUT
                        output file
  -l, --list            list CPIO contents
  -p, --print           print CPIO contents
  ```

# Structure

- `pycpio.header.cpioheader`: The class which represents a CPIO header
  * Can be initialized from args for header fields, or bytes representing a header
  * header types are defined in `pycpio.header.headers` (only the new ascii format is supported)
- `pycpio.cpio.data`: The class which represents a CPIO data block
  * Each CPIO object must have a header.
  * Currently the follwing subtypes are supported:
    - `file` : A regular file, or hardlink.
    - `dir` : A directory
    - `symlink` : A symbolic link
    - `chardev` : A character device
  * CPIO objects are collected in a `pycpio.cpio.archive` object
    - The archive handles duplication, inode generation, name normalization, and other collection related tasks
  * All CPIO object types can be initialized from args, bytes, or a file path
