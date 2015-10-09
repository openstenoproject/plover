# Copyright (c) 2010-2011 Joshua Harlan Lifton.
# See LICENSE.txt for details.

# TODO: unit test this file

"""Generic stenography data models.

This module contains the following class:

Stroke -- A data model class that encapsulates a sequence of steno keys.

"""

import re

STROKE_DELIMITER = '/'
IMPLICIT_HYPHENS = set('AOEU*50')


def normalize_steno(strokes_string):
    """Convert steno strings to one common form."""
    strokes = strokes_string.split(STROKE_DELIMITER)
    normalized_strokes = []
    for stroke in strokes:
        if '#' in stroke:
            stroke = stroke.replace('#', '')
            if not re.search('[0-9]', stroke):
                stroke = '#' + stroke
        # Insert dash when dealing with 'explicit' numbers
        if re.search('[1-4][6-9]', stroke):
            start = re.search('[6-9]', stroke).start()
            stroke = stroke[:start] + '-' + stroke[start:]
        has_implicit_dash = bool(set(stroke) & IMPLICIT_HYPHENS)
        if has_implicit_dash:
            stroke = stroke.replace('-', '')
        if stroke.endswith('-'):
            stroke = stroke[:-1]
        normalized_strokes.append(stroke)
    return tuple(normalized_strokes)

STENO_KEY_NUMBERS = {'S-': '1-',
                     'T-': '2-',
                     'P-': '3-',
                     'H-': '4-',
                     'A-': '5-',
                     'O-': '0-',
                     '-F': '-6',
                     '-P': '-7',
                     '-L': '-8',
                     '-T': '-9'}

STENO_KEY_ORDER = {"#": 0,
                   "S-": 1,
                   "T-": 2,
                   "K-": 3,
                   "P-": 4,
                   "W-": 5,
                   "H-": 6,
                   "R-": 7,
                   "A-": 8,
                   "O-": 9,
                   "*": 10,
                   "-E": 11,
                   "-U": 12,
                   "-F": 13,
                   "-R": 14,
                   "-P": 15,
                   "-B": 16,
                   "-L": 17,
                   "-G": 18,
                   "-T": 19,
                   "-S": 20,
                   "-D": 21,
                   "-Z": 22}


class Stroke:
    """A standardized data model for stenotype machine strokes.

    This class standardizes the representation of a stenotype chord. A stenotype
    chord can be any sequence of stenotype keys that can be simultaneously
    pressed. Nearly all stenotype machines offer the same set of keys that can
    be combined into a chord, though some variation exists due to duplicate
    keys. This class accounts for such duplication, imposes the standard
    stenographic ordering on the keys, and combines the keys into a single
    string (called RTFCRE for historical reasons).

    """

    IMPLICIT_HYPHEN = set(('A-', 'O-', '5-', '0-', '-E', '-U', '*'))

    def __init__(self, steno_keys) :
        """Create a steno stroke by formatting steno keys.

        Arguments:

        steno_keys -- A sequence of pressed keys.

        """
        # Remove duplicate keys and save local versions of the input 
        # parameters.
        steno_keys_set = set(steno_keys)
        steno_keys = list(steno_keys_set)

        # Order the steno keys so comparisons can be made.
        steno_keys.sort(key=lambda x: STENO_KEY_ORDER.get(x, -1))
         
        # Convert strokes involving the number bar to numbers.
        if '#' in steno_keys:
            numeral = False
            for i, e in enumerate(steno_keys):
                if e in STENO_KEY_NUMBERS:
                    steno_keys[i] = STENO_KEY_NUMBERS[e]
                    numeral = True
            if numeral:
                steno_keys.remove('#')
        
        if steno_keys_set & self.IMPLICIT_HYPHEN:
            self.rtfcre = ''.join(key.strip('-') for key in steno_keys)
        else:
            pre = ''.join(k.strip('-') for k in steno_keys if k[-1] == '-' or 
                          k == '#')
            post = ''.join(k.strip('-') for k in steno_keys if k[0] == '-')
            self.rtfcre = '-'.join([pre, post]) if post else pre

        self.steno_keys = steno_keys

        # Determine if this stroke is a correction stroke.
        self.is_correction = (self.rtfcre == '*')

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

