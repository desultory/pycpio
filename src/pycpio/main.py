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
    parser.add_argument('--rm', '--delete', action='store', help='delete from archive')

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

    c = PyCPIO(logger=logger)
    if args.input:
        c.read_cpio_file(Path(args.input))

    if args.rm:
        c.remove_cpio(args.rm)

    if args.append:
        c.append_cpio(Path(args.append))

    if args.output:
        c.write_cpio_file(Path(args.output))

    if args.list:
        print(c.list_files())

    if args.print:
        print(c)


if __name__ == '__main__':
    main()
