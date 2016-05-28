# Copyright (c) 2016 Open Steno Project
# See LICENSE.txt for details.

# Python 2/3 compatibility.
from six import PY3


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


def characters(string):
    """Python 2.7 has narrow Unicode on Mac OS X and Windows"""

    encoded = string.encode('utf-32-be')  # 4 bytes per character
    for char_start in range(0, len(encoded), 4):
        end = char_start + 4
        character = encoded[char_start:end].decode('utf-32-be')
        yield character
