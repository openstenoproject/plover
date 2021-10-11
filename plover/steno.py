# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Generic stenography data models.

This module contains the following class:

Stroke -- A data model class that encapsulates a sequence of steno keys.

"""

from plover_stroke import BaseStroke, StrokeHelper

from plover import log


def sort_steno_strokes(strokes_list):
    '''Return suggestions, sorted by fewest strokes, then fewest keys.'''
    return sorted(strokes_list, key=lambda x: (len(x), sum(map(len, x))))


stroke_helper = StrokeHelper()


def normalize_stroke(steno, strict=False):
    try:
        return stroke_helper.normalize_stroke(steno)
    except ValueError:
        if strict:
            raise
        log.error(exc_info=True)
        return steno

def normalize_steno(steno, strict=False):
    try:
        return stroke_helper.normalize_steno(steno)
    except ValueError:
        if strict:
            raise
        log.error('', exc_info=True)
        return tuple(steno.split('/'))

def steno_to_sort_key(steno, strict=False):
    try:
        return stroke_helper.steno_to_sort_key(steno)
    except ValueError:
        if strict:
            raise
        log.error('', exc_info=True)
        return b'\x00\x00' + steno.encode('utf-8')


class Stroke(BaseStroke):

    """A standardized data model for stenotype machine strokes.

    This class standardizes the representation of a stenotype chord. A stenotype
    chord can be any sequence of stenotype keys that can be simultaneously
    pressed. Nearly all stenotype machines offer the same set of keys that can
    be combined into a chord, though some variation exists due to duplicate
    keys. This class accounts for such duplication, imposes the standard
    stenographic ordering on the keys, and combines the keys into a single
    string (called RTFCRE for historical reasons).

    """

    _helper = stroke_helper

    PREFIX_STROKE = None
    UNDO_STROKE = None

    @classmethod
    def setup(cls, keys, implicit_hyphen_keys, number_key, numbers, undo_stroke):
        if number_key is None:
            numbers = None
        stroke_helper.setup(keys, implicit_hyphen_keys, number_key, numbers)
        cls.PREFIX_STROKE = cls.from_integer(0)
        cls.UNDO_STROKE = cls.from_steno(undo_stroke)

    @property
    def steno_keys(self):
        return list(self.keys())

    @property
    def rtfcre(self):
        return stroke_helper.stroke_to_steno(self)

    @property
    def is_correction(self):
        return int(self) == int(self.UNDO_STROKE)

    def __str__(self):
        if self.is_correction:
            prefix = '*'
        else:
            prefix = ''
        return '%sStroke(%s : %s)' % (prefix, self.rtfcre, self.steno_keys)

    __repr__ = __str__
