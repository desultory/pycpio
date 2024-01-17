#!/usr/bin/env python3

from pathlib import Path

from pycpio import PyCPIO
from zenlib.util import init_logger, init_argparser, process_args


def main():
    logger = init_logger(__package__)
    argparser = init_argparser(prog=__package__, description='PyCPIO')

    argparser.add_argument('-i', '--input', help='input file')

    argparser.add_argument('-a', '--append', action='store', help='append to archive')
    argparser.add_argument('--recursive', action='store_true', help='append to archive recursively')
    argparser.add_argument('--relative', action='store', help='append to archive relative to this path')
    argparser.add_argument('--absolute', action='store_true', help='allow absolute paths')
    argparser.add_argument('--rm', '--delete', action='store', help='delete from archive')
    argparser.add_argument('-n', '--name', action='store', help='Name/path override for append')

    argparser.add_argument('-s', '--symlink', action='store', help='create symlink')
    argparser.add_argument('-c', '--chardev', action='store', help='create character device')

    argparser.add_argument('--major', action='store', help='major number for character/block device')
    argparser.add_argument('--minor', action='store', help='minor number for character/block device')

    argparser.add_argument('-u', '--set-owner', action='store', help='set UID on all files')
    argparser.add_argument('-g', '--set-group', action='store', help='set GID on all files')
    argparser.add_argument('-m', '--set-mode', action='store', help='set mode on all files')

    argparser.add_argument('-o', '--output', help='output file')

    argparser.add_argument('-l', '--list', action='store_true', help='list CPIO contents')
    argparser.add_argument('-p', '--print', action='store_true', help='print CPIO contents')

    args = process_args(argparser, logger=logger)
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
        cmdargs = {'relative': relative, 'path': Path(args.append)}

        if args.name:
            cmdargs['name'] = args.name

        if args.absolute:
            cmdargs['absolute'] = args.absolute

        if args.recursive:
            c.append_recursive(**cmdargs)
        else:
            c.append_cpio(**cmdargs)

    if args.output:
        c.write_cpio_file(Path(args.output))

    if args.list:
        print(c.list_files())

    if args.print:
        print(c)


if __name__ == '__main__':
    main()
