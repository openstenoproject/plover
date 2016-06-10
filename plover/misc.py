# Copyright (c) 2016 Open Steno Project
# See LICENSE.txt for details.


def popcount_8(v):
    """Population count for an 8 bit integer"""
    assert 0 <= v <= 255
    v -= ((v >> 1) & 0x55555555)
    v = (v & 0x33333333) + ((v >> 2) & 0x33333333)
    return ((v + (v >> 4) & 0xF0F0F0F) * 0x1010101) >> 24


def characters(string):
    """Python 2.7 has narrow Unicode on Mac OS X and Windows"""

    encoded = string.encode('utf-32-be')  # 4 bytes per character
    for char_start in xrange(0, len(encoded), 4):
        end = char_start + 4
        character = encoded[char_start:end].decode('utf-32-be')
        yield character
