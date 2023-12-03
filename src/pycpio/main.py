#!/usr/bin/env python3


from pycpio import PyCPIO

from logging import getLogger, StreamHandler
from argparse import ArgumentParser
from importlib.metadata import version
from pathlib import Path

from zenlib.logging import ColorLognameFormatter


def main():
    logger = getLogger(__name__)
    handler = StreamHandler()
    handler.setFormatter(ColorLognameFormatter('%(levelname)s | %(name)-42s | %(message)s'))
    logger.addHandler(handler)

    parser = ArgumentParser(prog='cpio')
    parser.add_argument('-i', '--input', help='input file')

    parser.add_argument('-a', '--append', action='store', help='append to archive')
    parser.add_argument('--recursive', action='store_true', help='append to archive recursively')
    parser.add_argument('--relative', action='store', help='append to archive relative to this path')
    parser.add_argument('--rm', '--delete', action='store', help='delete from archive')
    parser.add_argument('-n', '--name', action='store', help='Name/path override for append')

    parser.add_argument('-s', '--symlink', action='store', help='create symlink')
    parser.add_argument('-c', '--chardev', action='store', help='create character device')

    parser.add_argument('--major', action='store', help='major number for character/block device')
    parser.add_argument('--minor', action='store', help='minor number for character/block device')

    parser.add_argument('-u', '--set-owner', action='store', help='set UID on all files')
    parser.add_argument('-g', '--set-group', action='store', help='set GID on all files')
    parser.add_argument('-m', '--set-mode', action='store', help='set mode on all files')

    parser.add_argument('-o', '--output', help='output file')

    parser.add_argument('-l', '--list', action='store_true', help='list CPIO contents')
    parser.add_argument('-p', '--print', action='store_true', help='print CPIO contents')

    parser.add_argument('-d', '--debug', action='store_true', help='Debug output')
    parser.add_argument('-dd', '--verbose', action='store_true', help='Verbose output')

    parser.add_argument('-v', '--version', action='store_true', help='Print version and exit')

    args = parser.parse_args()

    if args.version:
        print(f'PyCPIO {version("pycpio")}')
        return

    if args.debug:
        logger.setLevel(10)
    elif args.verbose:
        logger.setLevel(5)
    else:
        logger.setLevel(20)

    kwargs = {'logger': logger}

    if args.name:
        kwargs['name'] = args.name

    if args.set_owner:
        kwargs['uid'] = int(args.set_owner)

    if args.set_group:
        kwargs['gid'] = int(args.set_group)

    if args.set_mode:
        kwargs['mode'] = int(args.set_mode, 8)

    c = PyCPIO(**kwargs)
    if args.input:
        c.read_cpio_file(Path(args.input))

    if args.rm:
        c.remove_cpio(args.rm)

    if args.symlink:
        if not args.name:
            raise ValueError('Symlink requires a name')
        c.add_symlink(args.name, args.symlink)

    if args.chardev:
        if not args.major or not args.minor:
            raise ValueError('Character device requires major and minor numbers')
        c.add_chardev(args.chardev, int(args.major), int(args.minor))

    if args.append:
        relative = args.relative if args.relative else None
        path = Path(args.append)

        if args.recursive:
            c.append_recursive(path=path, relative=relative)
        elif args.name:
            c.append_cpio(path=path, name=args.name, relative=relative)
        else:
            c.append_cpio(path=path, relative=relative)

    if args.output:
        c.write_cpio_file(Path(args.output))

    if args.list:
        print(c.list_files())

    if args.print:
        print(c)


if __name__ == '__main__':
    main()
