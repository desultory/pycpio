#!/usr/bin/env python3

from pathlib import Path

from pycpio import PyCPIO
from zenlib.util import get_kwargs


def main():
    arguments = [{'flags': ['-i', '--input'], 'help': 'input file'},
                 {'flags': ['-a', '--append'], 'help': 'append to archive'},
                 {'flags': ['--recursive'], 'action': 'store', 'help': 'append to archive recursively'},
                 {'flags': ['--relative'], 'action': 'store', 'help': 'append to archive relative to this path'},
                 {'flags': ['--absolute'], 'action': 'store_true', 'help': 'allow absolute paths'},
                 {'flags': ['--reproducible'], 'action': 'store_true', 'help': 'Set mtime to 0, start inodes at 0'},
                 {'flags': ['--rm', '--delete'], 'action': 'store', 'help': 'delete from archive'},
                 {'flags': ['-n', '--name'], 'action': 'store', 'help': 'Name/path override for append'},
                 {'flags': ['-s', '--symlink'], 'action': 'store', 'help': 'create symlink'},
                 {'flags': ['-c', '--chardev'], 'action': 'store', 'help': 'create character device'},
                 {'flags': ['--major'], 'action': 'store', 'help': 'major number for character/block device', 'type': int},
                 {'flags': ['--minor'], 'action': 'store', 'help': 'minor number for character/block device', 'type': int},
                 {'flags': ['-u', '--set-owner'], 'action': 'store', 'help': 'set UID on all files', 'type': int, 'dest': 'uid'},
                 {'flags': ['-g', '--set-group'], 'action': 'store', 'help': 'set GID on all files', 'type': int, 'dest': 'gid'},
                 {'flags': ['-m', '--set-mode'], 'action': 'store', 'help': 'set mode on all files', 'type': int, 'dest': 'mode'},
                 {'flags': ['-o', '--output'], 'help': 'output file'},
                 {'flags': ['-l', '--list'], 'action': 'store_true', 'help': 'list CPIO contents'},
                 {'flags': ['-p', '--print'], 'action': 'store_true', 'help': 'print CPIO contents'}]

    kwargs = get_kwargs(package=__package__, description='PyCPIO', arguments=arguments, drop_default=True)

    c = PyCPIO(**kwargs)
    if input_file := kwargs.get('input'):
        c.read_cpio_file(Path(input_file))

    if rm_args := kwargs.get('rm'):
        c.remove_cpio(rm_args)

    if symlink_dest := kwargs.get('symlink'):
        if name := kwargs.get('name'):
            c.add_symlink(name, symlink_dest)
        else:
            raise ValueError('Symlink requires a name')

    if chardev_path := kwargs.get('chardev'):
        major = kwargs.get('major')
        minor = kwargs.get('minor')
        if not major:
            raise ValueError('Character device requires major number')
        if not minor:
            raise ValueError('Character device requires minor number')
        c.add_chardev(chardev_path, major, minor)

    if append_file := kwargs.get('append'):
        relative = kwargs.get('relative')
        cmdargs = {'relative': relative,
                   'path': Path(append_file),
                   'name': kwargs.get('name'),
                   'absolute': kwargs.get('absolute')}

        c.append_cpio(**cmdargs)

    if recursive_path := kwargs.get('recursive'):
        relative = kwargs.get('relative')
        cmdargs = {'relative': relative, 'path': Path(recursive_path)}
        c.append_recursive(**cmdargs)

    if output_file := kwargs.get('output'):
        c.write_cpio_file(Path(output_file))

    if kwargs.get('list'):
        print(c.list_files())

    if kwargs.get('print'):
        print(c)


if __name__ == '__main__':
    main()
