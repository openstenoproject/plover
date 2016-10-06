# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: unit test this file

"""Generic stenography data models.

This module contains the following class:

Stroke -- A data model class that encapsulates a sequence of steno keys.

"""

import re

from plover import system


STROKE_DELIMITER = '/'

_NUMBERS = set('0123456789')
_IMPLICIT_NUMBER_RX = re.compile('(^|[1-4])([6-9])')

def normalize_stroke(stroke):
    letters = set(stroke)
    if letters & _NUMBERS:
        if system.NUMBER_KEY in letters:
            stroke = stroke.replace(system.NUMBER_KEY, '')
        # Insert dash when dealing with 'explicit' numbers
        m = _IMPLICIT_NUMBER_RX.search(stroke)
        if m is not None:
            start = m.start(2)
            return stroke[:start] + '-' + stroke[start:]
    if '-' in letters:
        if stroke.endswith('-'):
             stroke = stroke[:-1]
        elif letters & system.IMPLICIT_HYPHENS:
            stroke = stroke.replace('-', '')
    return stroke

def normalize_steno(strokes_string):
    """Convert steno strings to one common form."""
    return tuple(normalize_stroke(stroke) for stroke
                 in strokes_string.split(STROKE_DELIMITER))

def sort_steno_keys(steno_keys):
    return sorted(steno_keys, key=lambda x: system.KEY_ORDER.get(x, -1))


class Stroke(object):
    """A standardized data model for stenotype machine strokes.

    This class standardizes the representation of a stenotype chord. A stenotype
    chord can be any sequence of stenotype keys that can be simultaneously
    pressed. Nearly all stenotype machines offer the same set of keys that can
    be combined into a chord, though some variation exists due to duplicate
    keys. This class accounts for such duplication, imposes the standard
    stenographic ordering on the keys, and combines the keys into a single
    string (called RTFCRE for historical reasons).

    """

    def __init__(self, steno_keys) :
        """Create a steno stroke by formatting steno keys.

        Arguments:

        steno_keys -- A sequence of pressed keys.

        """
        # Remove duplicate keys and save local versions of the input 
        # parameters.
        steno_keys_set = set(steno_keys)
        # Order the steno keys so comparisons can be made.
        steno_keys = list(sort_steno_keys(steno_keys_set))

        # Convert strokes involving the number bar to numbers.
        if system.NUMBER_KEY in steno_keys:
            numeral = False
            for i, e in enumerate(steno_keys):
                if e in system.NUMBERS:
                    steno_keys[i] = system.NUMBERS[e]
                    numeral = True
            if numeral:
                steno_keys.remove(system.NUMBER_KEY)
        
        if steno_keys_set & system.IMPLICIT_HYPHEN_KEYS:
            self.rtfcre = ''.join(key.strip('-') for key in steno_keys)
        else:
            pre = ''.join(k.strip('-') for k in steno_keys if k[-1] == '-' or 
                          k == system.NUMBER_KEY)
            post = ''.join(k.strip('-') for k in steno_keys if k[0] == '-')
            self.rtfcre = '-'.join([pre, post]) if post else pre

        self.steno_keys = steno_keys

        # Determine if this stroke is a correction stroke.
        self.is_correction = (self.rtfcre == system.UNDO_STROKE_STENO)

    def __str__(self):
        if self.is_correction:
            prefix = '*'
        else:
            prefix = ''
        return '%sStroke(%s : %s)' % (prefix, self.rtfcre, self.steno_keys)

    def __eq__(self, other):
        return (isinstance(other, Stroke)
                and self.steno_keys == other.steno_keys)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return str(self)

