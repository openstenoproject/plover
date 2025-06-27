# Copyright (c) 2016 Open Steno Project
# See LICENSE.txt for details.

import os

from plover.oslayer.config import CONFIG_DIR
from plover.resource import ASSET_SCHEME


def popcount_8(v):
    """Population count for an 8 bit integer"""
    assert 0 <= v <= 255
    v -= ((v >> 1) & 0x55555555)
    v = (v & 0x33333333) + ((v >> 2) & 0x33333333)
    return ((v + (v >> 4) & 0xF0F0F0F) * 0x1010101) >> 24

def expand_path(path):
    ''' Expand path.

        - if starting with "~/", it is substituted with the user home directory
        - if relative, it is resolved relative to CONFIG_DIR
    '''
    if path.startswith(ASSET_SCHEME):
        return path
    path = os.path.expanduser(path)
    path = normalize_path(os.path.join(CONFIG_DIR, path))
    return path

def shorten_path(path):
    ''' Shorten path.

        - if the path is below CONFIG_DIR, a relative path to it is returned
        - if path is below the user home directory, "~/" is substituted to it

        Note: relative path are automatically assumed to be relative to CONFIG_DIR.
    '''
    if path.startswith(ASSET_SCHEME):
        return path
    path = normalize_path(os.path.join(CONFIG_DIR, path))
    config_dir = normalize_path(CONFIG_DIR)
    if not config_dir.endswith(os.sep):
        config_dir += os.sep
    if path.startswith(config_dir):
        return path[len(config_dir):]
    home_dir = normalize_path(os.path.expanduser('~'))
    if not home_dir.endswith(os.sep):
        home_dir += os.sep
    if path.startswith(home_dir):
        return os.path.join('~', path[len(home_dir):])
    return path

def normalize_path(path):
    ''' Normalize path: return canonical path, normalizing case on Windows.
    '''
    if path.startswith(ASSET_SCHEME):
        return path
    return os.path.normcase(os.path.realpath(path))

def boolean(value):
    if isinstance(value, str):
        v = value.lower()
        if v in ('1', 'yes', 'true', 'on'):
            return True
        if v in ('0', 'no', 'false', 'off'):
            return False
        raise ValueError(value)
    return bool(value)

def to_surrogate_pair(char):
    pairs = []
    for code in char:
        code_point = ord(code)
        if code_point >= 0x10000:
            high_part = (code_point - 0x10000) // 0x400 + 0xD800
            low_part = (code_point - 0x10000) % 0x400 + 0xDC00
            pairs += (high_part, low_part)
        else:
            pairs.append(code_point)
    return pairs
