# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

"""Generic stenography data models.

This module contains the following class:

Stroke -- A data model class that encapsulates a sequence of steno keys.

"""

from plover_stroke import BaseStroke


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

    PREFIX_STROKE = None
    UNDO_STROKE = None

    @classmethod
    def setup(cls, keys, implicit_hyphen_keys, number_key,
              numbers, feral_number_key, undo_stroke):
        if number_key is None:
            assert not numbers
            numbers = None
        super().setup(keys, implicit_hyphen_keys, number_key, numbers, feral_number_key)
        cls._class = type(cls.__name__, (cls,), {'_helper': cls._helper})
        cls._class._class = cls._class
        cls._class.PREFIX_STROKE = cls.PREFIX_STROKE = cls.from_integer(0)
        cls._class.UNDO_STROKE = cls.UNDO_STROKE = cls.from_steno(undo_stroke)

    @classmethod
    def from_steno(cls, steno):
        return int.__new__(cls._class, cls._helper.stroke_from_steno(steno))

    @classmethod
    def from_keys(cls, keys):
        return int.__new__(cls._class, cls._helper.stroke_from_keys(keys))

    @classmethod
    def from_integer(cls, integer):
        return int.__new__(cls._class, cls._helper.stroke_from_int(integer))

    @classmethod
    def normalize_stroke(cls, steno, strict=True):
        try:
            return cls._helper.normalize_stroke(steno)
        except ValueError:
            if strict:
                raise
            return steno

    @classmethod
    def normalize_steno(cls, steno, strict=True):
        try:
            return cls._helper.normalize_steno(steno)
        except ValueError:
            if strict:
                raise
            return tuple(steno.split('/'))

    @classmethod
    def steno_to_sort_key(cls, steno, strict=True):
        try:
            return cls._helper.steno_to_sort_key(steno)
        except ValueError:
            if strict:
                raise
            return b'\x00\x00' + steno.encode('utf-8')

    def __new__(cls, value):
        return int.__new__(cls._class, cls._helper.stroke_from_any(value))

    @property
    def steno_keys(self):
        return list(self.keys())

    @property
    def rtfcre(self):
        return self._helper.stroke_to_steno(self)

    @property
    def is_correction(self):
        return int(self) == int(self.UNDO_STROKE)

    def __str__(self):
        prefix = '*' if self.is_correction else ''
        return f'{prefix}Stroke({self.rtfcre} : {self.steno_keys})'

    __repr__ = __str__


normalize_stroke = Stroke.normalize_stroke
normalize_steno = Stroke.normalize_steno
steno_to_sort_key = Stroke.steno_to_sort_key

def sort_steno_strokes(strokes_list):
    '''Return suggestions, sorted by fewest strokes, then fewest keys.'''
    return sorted(strokes_list, key=lambda x: (len(x), sum(map(len, x))))
