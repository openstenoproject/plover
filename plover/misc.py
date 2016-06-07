# Copyright (c) 2016 Open Steno Project
# See LICENSE.txt for details.


def popcount32(v):
    """Population count for a 32bits integer."""
    v -= ((v >> 1) & 0x55555555)
    v = (v & 0x33333333) + ((v >> 2) & 0x33333333)
    return ((v + (v >> 4) & 0xF0F0F0F) * 0x1010101) >> 24
