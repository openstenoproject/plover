# Copyright (c) 2016 Open Steno Project
# See LICENSE.txt for details.

import os
import sys

# Python 2/3 compatibility.
from six import PY3

from plover.oslayer.config import CONFIG_DIR


if PY3:

    from types import SimpleNamespace

else:

    class SimpleNamespace(object):

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

        def __repr__(self):
            keys = sorted(self.__dict__)
            items = ("{}={!r}".format(k, self.__dict__[k]) for k in keys)
            return "{}({})".format(type(self).__name__, ", ".join(items))

        def __eq__(self, other):
            return self.__dict__ == other.__dict__


def popcount_8(v):
    """Population count for an 8 bit integer"""
    assert 0 <= v <= 255
    v -= ((v >> 1) & 0x55555555)
    v = (v & 0x33333333) + ((v >> 2) & 0x33333333)
    return ((v + (v >> 4) & 0xF0F0F0F) * 0x1010101) >> 24


if sys.maxunicode == 65535:

    def characters(string):
        """Python 2.7 has narrow Unicode on Mac OS X and Windows"""
        encoded = string.encode('utf-32-be')  # 4 bytes per character
        for char_start in range(0, len(encoded), 4):
            end = char_start + 4
            character = encoded[char_start:end].decode('utf-32-be')
            yield character

else:

    def characters(string):
        return iter(string)


def expand_path(path):
    ''' Expand path.

        - if starting with "~/", it is substituted with the user home directory
        - if relative, it is resolved relative to CONFIG_DIR
    '''
    path = os.path.expanduser(path)
    path = os.path.realpath(os.path.join(CONFIG_DIR, path))
    return path

def shorten_path(path):
    ''' Shorten path.

        - if the path is below CONFIG_DIR, a relative path to it is returned
        - if path is below the user home directory, "~/" is substituted to it

        Note: relative path are automatically assumed to be relative to CONFIG_DIR.
    '''
    path = os.path.realpath(os.path.join(CONFIG_DIR, path))
    config_dir = os.path.realpath(CONFIG_DIR)
    if not config_dir.endswith(os.sep):
        config_dir += os.sep
    if path.startswith(config_dir):
        return path[len(config_dir):]
    home_dir = os.path.expanduser('~')
    if not home_dir.endswith(os.sep):
        home_dir += os.sep
    if path.startswith(home_dir):
        return os.path.join('~', path[len(home_dir):])
    return path
